from typing import Any, Dict, Optional, List, Union
from datetime import datetime, timedelta

from gold_miner.odps_client import OdpsClient, OdpsConfig


def run(
    ad_group_id: Union[str, int],
    dt: str,
    model_name: str = "roas_v1",
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    OCPI客户ROI异常排查Skill
    针对OCPI客户某日ROI不符合预期的原因进行排查定位

    参数:
        ad_group_id: 广告组ID
        dt: 分析日期（格式：yyyyMMdd）
        model_name: 模型名称，默认'roas_v1'
        config: ODPS 配置
    """
    config = config or _get_config()
    odps = _create_odps_client(config)

    ad_group_id = str(ad_group_id)
    
    print(f"[ocpi_roi_debug] 开始排查广告组: {ad_group_id}, 日期: {dt}")

    # 第一步：从响应表获取app_id维度的消耗分布
    app_analysis = _analyze_app_distribution(odps, ad_group_id, dt)
    
    # 第二步：消耗趋势回溯（按app_id）
    consumption_trend = _analyze_app_consumption_trend(odps, ad_group_id, dt)
    
    # 第三步：获取主要app_id对应的package_name
    package_info = _get_package_info(odps, ad_group_id, dt)
    
    # 第四步：查询模型校准系数
    calibration_data = []
    calibration_trend = []
    
    if package_info and package_info.get("package_name"):
        package_name = package_info["package_name"]
        app_id = package_info.get("app_id", "")
        
        # 查询当前校准系数
        calibration_data = _get_calibration_coefficient(
            odps, ad_group_id, package_name, model_name, dt
        )
        
        # 查询校准系数趋势（近7天）
        calibration_trend = _get_calibration_trend(
            odps, ad_group_id, package_name, model_name, dt
        )
    
    # 生成排查结论
    conclusion = _generate_conclusion(
        app_analysis, 
        consumption_trend, 
        calibration_data, 
        calibration_trend
    )

    return {
        "status": "success",
        "ad_group_id": ad_group_id,
        "dt": dt,
        "model_name": model_name,
        "app_analysis": app_analysis,
        "consumption_trend": consumption_trend,
        "package_info": package_info,
        "calibration_data": calibration_data,
        "calibration_trend": calibration_trend,
        "conclusion": conclusion,
        "message": f"ROI异常排查完成。广告组: {ad_group_id}, 日期: {dt}",
    }


def _analyze_app_distribution(odps: OdpsClient, ad_group_id: str, dt: str) -> Dict[str, Any]:
    """第一步：从响应表分析app_id维度的消耗分布"""
    try:
        sql = f"""
        SELECT 
            app_id,
            MAX(package_name) as package_name,
            SUM(cost) as cost,
            SUM(ecpm) as ecpm,
            COUNT(*) as request_count
        FROM com_cdm.dwd_log_dsp_adserver_response_hi
        WHERE dh >= '{dt}00'
          AND dh <= '{dt}23'
          AND ad_group_id = '{ad_group_id}'
          AND cost_type = '7'
          AND gaid <> '00000000-0000-0000-0000-000000000000'
          AND roas_ltv_model_name IS NOT NULL
          AND roas_ltv_model_name LIKE '%roas_%'
        GROUP BY app_id
        ORDER BY cost DESC
        LIMIT 1000
        """
        
        df = odps.run_sql(sql)
        
        if df is not None and not df.empty:
            total_cost = df["cost"].sum()
            
            app_list = []
            for _, row in df.iterrows():
                cost_ratio = float(row["cost"]) / total_cost if total_cost > 0 else 0
                app_list.append({
                    "app_id": str(row["app_id"]),
                    "package_name": str(row["package_name"]) if row["package_name"] else "",
                    "cost": float(row["cost"]) if row["cost"] else 0,
                    "cost_ratio": cost_ratio,
                    "ecpm": float(row["ecpm"]) if row["ecpm"] else 0,
                    "request_count": int(row["request_count"]) if row["request_count"] else 0,
                })
            
            # 识别主要app（消耗占比>50%）
            dominant_apps = [a for a in app_list if a["cost_ratio"] > 0.5]
            
            return {
                "total_cost": float(total_cost),
                "app_count": len(app_list),
                "app_list": app_list,
                "dominant_apps": dominant_apps,
                "has_dominant_app": len(dominant_apps) > 0,
            }
    except Exception as e:
        print(f"[ocpi_roi_debug] Warning: App analysis failed: {e}")
    
    return {"app_list": [], "dominant_apps": [], "has_dominant_app": False}


def _analyze_app_consumption_trend(odps: OdpsClient, ad_group_id: str, dt: str) -> Dict[str, Any]:
    """第二步：按app_id分析消耗趋势"""
    try:
        # 计算前7天日期
        current_date = datetime.strptime(dt, "%Y%m%d")
        date_list = []
        for i in range(7, -1, -1):
            date = current_date - timedelta(days=i)
            date_list.append(date.strftime("%Y%m%d"))
        
        sql = f"""
        SELECT 
            SUBSTR(dh, 1, 8) as dt,
            app_id,
            SUM(cost) as cost
        FROM com_cdm.dwd_log_dsp_adserver_response_hi
        WHERE dh >= '{date_list[0]}00'
          AND dh <= '{dt}23'
          AND ad_group_id = '{ad_group_id}'
          AND cost_type = '7'
          AND gaid <> '00000000-0000-0000-0000-000000000000'
          AND roas_ltv_model_name IS NOT NULL
          AND roas_ltv_model_name LIKE '%roas_%'
        GROUP BY SUBSTR(dh, 1, 8), app_id
        ORDER BY dt DESC, cost DESC
        LIMIT 10000
        """
        
        df = odps.run_sql(sql)
        
        if df is not None and not df.empty:
            # 分析每个app的消耗趋势
            app_trends = {}
            for app_id in df["app_id"].unique():
                app_df = df[df["app_id"] == app_id].sort_values("dt")
                costs = app_df["cost"].tolist()
                
                # 检查是否近期上涨
                recent_avg = sum(costs[-3:]) / 3 if len(costs) >= 3 else sum(costs) / len(costs)
                early_avg = sum(costs[:3]) / 3 if len(costs) >= 3 else sum(costs) / len(costs)
                
                trend = "stable"
                if early_avg > 0 and recent_avg / early_avg > 1.5:
                    trend = "increasing"
                elif early_avg > 0 and recent_avg / early_avg < 0.7:
                    trend = "decreasing"
                
                app_trends[str(app_id)] = {
                    "trend": trend,
                    "recent_avg_cost": float(recent_avg),
                    "early_avg_cost": float(early_avg),
                    "change_ratio": float(recent_avg / early_avg) if early_avg > 0 else 0,
                }
            
            # 识别消耗明显上涨的app
            increasing_apps = {
                k: v for k, v in app_trends.items() 
                if v["trend"] == "increasing"
            }
            
            return {
                "date_range": date_list,
                "app_trends": app_trends,
                "increasing_apps": increasing_apps,
                "has_increasing_app": len(increasing_apps) > 0,
            }
    except Exception as e:
        print(f"[ocpi_roi_debug] Warning: App consumption trend analysis failed: {e}")
    
    return {"app_trends": {}, "increasing_apps": {}, "has_increasing_app": False}


def _get_package_info(odps: OdpsClient, ad_group_id: str, dt: str) -> Optional[Dict[str, str]]:
    """第三步：获取主要app_id对应的package_name"""
    try:
        sql = f"""
        SELECT 
            app_id,
            package_name,
            SUM(cost) as cost
        FROM com_cdm.dwd_log_dsp_adserver_response_hi
        WHERE dh >= '{dt}00'
          AND dh <= '{dt}23'
          AND ad_group_id = '{ad_group_id}'
          AND cost_type = '7'
          AND package_name IS NOT NULL
        GROUP BY app_id, package_name
        ORDER BY cost DESC
        LIMIT 1
        """
        
        df = odps.run_sql(sql)
        
        if df is not None and not df.empty:
            return {
                "app_id": str(df.iloc[0]["app_id"]),
                "package_name": str(df.iloc[0]["package_name"]),
                "cost": float(df.iloc[0]["cost"]) if df.iloc[0]["cost"] else 0,
            }
        
        return None
        
    except Exception as e:
        print(f"[ocpi_roi_debug] Warning: Package info query failed: {e}")
    
    return None


def _get_calibration_coefficient(
    odps: OdpsClient, 
    ad_group_id: str, 
    package_name: str, 
    model_name: str,
    dt: str
) -> List[Dict[str, Any]]:
    """第四步：查询模型校准系数"""
    try:
        sql = f"""
        SELECT 
            score_start,
            score_end,
            calibrate_factor,
            dh
        FROM ads_strategy.dwd_eagllwin_ad_group_model_package_ltv_calibrate_mysql_dh
        WHERE dh = MAX_PT('ads_strategy.dwd_eagllwin_ad_group_model_package_ltv_calibrate_mysql_dh')
          AND ad_group_id = {ad_group_id}
          AND model_name = '{model_name}'
          AND package_name = '{package_name}'
        ORDER BY score_start
        """
        
        df = odps.run_sql(sql)
        
        if df is not None and not df.empty:
            calibration_list = []
            for _, row in df.iterrows():
                factor = float(row["calibrate_factor"]) if row["calibrate_factor"] else 0
                
                # 风险等级评估
                risk_level = "low"
                if factor > 1.1:
                    risk_level = "high"
                elif factor > 0.8:
                    risk_level = "medium"
                
                calibration_list.append({
                    "score_start": float(row["score_start"]) if row["score_start"] else 0,
                    "score_end": float(row["score_end"]) if row["score_end"] else 0,
                    "calibrate_factor": factor,
                    "risk_level": risk_level,
                    "dh": str(row["dh"]) if row["dh"] else "",
                })
            
            return calibration_list
    except Exception as e:
        print(f"[ocpi_roi_debug] Warning: Calibration coefficient query failed: {e}")
    
    return []


def _get_calibration_trend(
    odps: OdpsClient, 
    ad_group_id: str, 
    package_name: str, 
    model_name: str,
    dt: str
) -> List[Dict[str, Any]]:
    """查询校准系数趋势（近7天）"""
    try:
        # 计算近7天的分区
        current_date = datetime.strptime(dt, "%Y%m%d")
        
        sql = f"""
        SELECT 
            dh,
            AVG(calibrate_factor) as avg_factor,
            COUNT(*) as segment_count
        FROM ads_strategy.dwd_eagllwin_ad_group_model_package_ltv_calibrate_mysql_dh
        WHERE ad_group_id = {ad_group_id}
          AND model_name = '{model_name}'
          AND package_name = '{package_name}'
          AND dh >= '{(current_date - timedelta(days=7)).strftime("%Y%m%d")}'
        GROUP BY dh
        ORDER BY dh
        """
        
        df = odps.run_sql(sql)
        
        if df is not None and not df.empty:
            trend_list = []
            for _, row in df.iterrows():
                trend_list.append({
                    "dh": str(row["dh"]),
                    "avg_calibrate_factor": float(row["avg_factor"]) if row["avg_factor"] else 0,
                    "segment_count": int(row["segment_count"]) if row["segment_count"] else 0,
                })
            
            return trend_list
    except Exception as e:
        print(f"[ocpi_roi_debug] Warning: Calibration trend query failed: {e}")
    
    return []


def _generate_conclusion(
    app_analysis: Dict,
    consumption_trend: Dict,
    calibration_data: List[Dict],
    calibration_trend: List[Dict]
) -> Dict[str, Any]:
    """生成排查结论"""
    conclusion = {
        "primary_cause": "",
        "details": [],
        "recommendations": [],
    }
    
    causes = []
    
    # 检查1：app集中度
    if app_analysis.get("has_dominant_app"):
        dominant = app_analysis["dominant_apps"][0]
        causes.append(f"App集中度过高：{dominant['package_name']}({dominant['app_id']})消耗占比{dominant['cost_ratio']:.1%}")
    
    # 检查2：消耗上涨
    if consumption_trend.get("has_increasing_app"):
        for app_id, trend in consumption_trend["increasing_apps"].items():
            causes.append(f"App消耗上涨：app_id={app_id}近期消耗上涨{trend['change_ratio']:.1f}倍，可能导致打分变高")
    
    # 检查3：校准系数
    high_risk_segments = [c for c in calibration_data if c.get("risk_level") == "high"]
    if high_risk_segments:
        avg_factor = sum(c["calibrate_factor"] for c in high_risk_segments) / len(high_risk_segments)
        causes.append(f"校准系数过高：{len(high_risk_segments)}个分数段校准系数>1.1，平均系数{avg_factor:.2f}，存在打分高估风险")
    
    # 检查4：校准系数趋势
    if len(calibration_trend) >= 2:
        recent_avg = sum(t["avg_calibrate_factor"] for t in calibration_trend[-3:]) / min(3, len(calibration_trend[-3:]))
        early_avg = sum(t["avg_calibrate_factor"] for t in calibration_trend[:3]) / min(3, len(calibration_trend[:3]))
        
        if early_avg > 0 and recent_avg / early_avg > 1.2:
            causes.append(f"校准系数上升：近期校准系数从{early_avg:.2f}上升到{recent_avg:.2f}，涨幅{(recent_avg/early_avg-1):.1%}")
    
    # 确定主要原因
    if causes:
        conclusion["primary_cause"] = causes[0]
        conclusion["details"] = causes
        
        # 生成建议
        if high_risk_segments:
            conclusion["recommendations"].append("建议调整模型校准系数，降低打分高估风险")
        if consumption_trend.get("has_increasing_app"):
            conclusion["recommendations"].append("建议监控消耗上涨App的ROI表现，必要时降低出价")
        if app_analysis.get("has_dominant_app"):
            conclusion["recommendations"].append("建议分散App投放，降低单一App依赖")
    else:
        conclusion["primary_cause"] = "未发现明显异常"
        conclusion["details"].append("App分布、消耗趋势、校准系数均正常")
    
    return conclusion


def _get_config() -> Dict[str, str]:
    """获取ODPS配置"""
    from gold_miner.config import Config
    cfg = Config.from_env()
    return {
        "access_id": cfg.odps_access_id,
        "access_key": cfg.odps_access_key,
        "project": cfg.odps_project,
        "endpoint": cfg.odps_endpoint,
    }


def _create_odps_client(config: Dict[str, str]) -> OdpsClient:
    """创建ODPS客户端"""
    odps_config = OdpsConfig(
        access_id=config["access_id"],
        access_key=config["access_key"],
        project=config["project"],
        endpoint=config["endpoint"],
    )
    return OdpsClient(odps_config)


SKILL = {
    "name": "ocpi_roi_debug",
    "description": "Debug OCPI customer ROI anomalies by analyzing app distribution, consumption trends, and model calibration coefficients. Invoke when user reports unexpected ROI for an OCPI ad group.",
    "inputs": {
        "ad_group_id": "Ad group ID",
        "dt": "Analysis date (yyyyMMdd format)",
        "model_name": "Model name (default: roas_v1)",
    },
    "run": run,
}
