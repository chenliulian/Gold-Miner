from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from gold_miner.odps_client import OdpsClient, OdpsConfig


def run(
    dt: str,
    min_cost_threshold: float = 100.0,
    output_table: Optional[str] = None,
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    LTV数据分析Skill
    功能：
    1. 计算固定日期当天全部OCPI账户的总消耗及整体ROI
    2. 输出联运游戏客户（MI_游戏_联运开头）的整体消耗及平均ROI（CPI和OCPI分别统计）
    3. 输出消耗>=100的group明细数据（包括消耗和ROI）

    参数:
        dt: 日期（格式：yyyyMMdd）
        min_cost_threshold: group最小消耗阈值（美元），默认100
        output_table: 输出表名，默认自动生成
        config: ODPS 配置
    """
    config = config or _get_config()
    odps = _create_odps_client(config)

    # 生成输出表名
    if output_table is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_table = f"ltv_roi_analysis_{timestamp}"

    print(f"[monitor_ltv_roi] 分析日期: {dt}")
    print(f"[monitor_ltv_roi] Group最小消耗阈值: ${min_cost_threshold}")

    # 1. 计算全部OCPI账户统计（全部数据，不限制消耗）
    ocpi_overall_stats = _get_ocpi_overall_stats(odps, dt)
    
    # 2. 计算联运游戏客户统计（全部数据，不限制消耗）
    lianyun_game_stats = _get_lianyun_game_stats(odps, dt)
    
    # 3. 创建消耗>=threshold的group明细表
    _create_group_detail_table(odps, dt, min_cost_threshold, output_table)
    
    # 获取明细数据
    df_detail = odps.run_sql(f"SELECT * FROM {output_table} LIMIT 10000")

    return {
        "status": "success",
        "date": dt,
        "min_cost_threshold": min_cost_threshold,
        "output_table": output_table,
        "detail_rows": len(df_detail) if df_detail is not None else 0,
        "ocpi_overall": ocpi_overall_stats,
        "lianyun_game": lianyun_game_stats,
        "message": f"LTV数据分析完成。明细表: {output_table}",
    }


def _get_ocpi_overall_stats(odps: OdpsClient, dt: str) -> Dict[str, Any]:
    """获取全部OCPI账户统计（全部数据，不限制消耗）"""
    try:
        sql = f"""
        SELECT 
            COUNT(DISTINCT ad_group_id) AS adgroup_cnt,
            SUM(cpi_cost) AS total_cost,
            SUM(income) AS total_income,
            CASE 
                WHEN SUM(cpi_cost) > 0 
                THEN SUM(income) / SUM(cpi_cost) 
                ELSE 0 
            END AS overall_roi
        FROM com_cdm.dws_tracker_ad_cpc_cost_hi
        WHERE dh >= '{dt}00'
          AND dh <= '{dt}23'
          AND cost_type = 'ocpi'
          AND ad_group_id IS NOT NULL
          AND ad_group_id != ''
        """
        df = odps.run_sql(sql)
        if df is not None and not df.empty:
            return {
                "adgroup_cnt": int(df.iloc[0]["adgroup_cnt"]) if df.iloc[0]["adgroup_cnt"] else 0,
                "total_cost": float(df.iloc[0]["total_cost"]) if df.iloc[0]["total_cost"] else 0,
                "total_income": float(df.iloc[0]["total_income"]) if df.iloc[0]["total_income"] else 0,
                "overall_roi": float(df.iloc[0]["overall_roi"]) if df.iloc[0]["overall_roi"] else 0,
            }
    except Exception as e:
        print(f"[monitor_ltv_roi] Warning: Failed to get OCPI overall stats: {e}")
    
    return {"adgroup_cnt": 0, "total_cost": 0, "total_income": 0, "overall_roi": 0}


def _get_lianyun_game_stats(odps: OdpsClient, dt: str) -> Dict[str, Any]:
    """获取联运游戏（MI_游戏_联运开头）客户统计（全部数据，不限制消耗）"""
    try:
        # OCPI联运游戏统计
        ocpi_sql = f"""
        SELECT 
            COUNT(DISTINCT ad_group_id) AS adgroup_cnt,
            SUM(cpi_cost) AS total_cost,
            SUM(income) AS total_income,
            CASE 
                WHEN SUM(cpi_cost) > 0 
                THEN SUM(income) / SUM(cpi_cost) 
                ELSE 0 
            END AS avg_roi
        FROM com_cdm.dws_tracker_ad_cpc_cost_hi
        WHERE dh >= '{dt}00'
          AND dh <= '{dt}23'
          AND cost_type = 'ocpi'
          AND LOWER(ad_group_title) LIKE 'mi_游戏_联运%'
          AND ad_group_id IS NOT NULL
          AND ad_group_id != ''
        """
        
        # CPI联运游戏统计
        cpi_sql = f"""
        SELECT 
            COUNT(DISTINCT ad_group_id) AS adgroup_cnt,
            SUM(cpi_cost) AS total_cost,
            SUM(income) AS total_income,
            CASE 
                WHEN SUM(cpi_cost) > 0 
                THEN SUM(income) / SUM(cpi_cost) 
                ELSE 0 
            END AS avg_roi
        FROM com_cdm.dws_tracker_ad_cpc_cost_hi
        WHERE dh >= '{dt}00'
          AND dh <= '{dt}23'
          AND cost_type = 'cpi'
          AND cpi_cost > 0
          AND LOWER(ad_group_title) LIKE 'mi_游戏_联运%'
          AND ad_group_id IS NOT NULL
          AND ad_group_id != ''
        """
        
        ocpi_df = odps.run_sql(ocpi_sql)
        cpi_df = odps.run_sql(cpi_sql)
        
        result = {
            "ocpi": {
                "adgroup_cnt": 0,
                "total_cost": 0,
                "total_income": 0,
                "avg_roi": 0,
            },
            "cpi": {
                "adgroup_cnt": 0,
                "total_cost": 0,
                "total_income": 0,
                "avg_roi": 0,
            }
        }
        
        if ocpi_df is not None and not ocpi_df.empty:
            result["ocpi"] = {
                "adgroup_cnt": int(ocpi_df.iloc[0]["adgroup_cnt"]) if ocpi_df.iloc[0]["adgroup_cnt"] else 0,
                "total_cost": float(ocpi_df.iloc[0]["total_cost"]) if ocpi_df.iloc[0]["total_cost"] else 0,
                "total_income": float(ocpi_df.iloc[0]["total_income"]) if ocpi_df.iloc[0]["total_income"] else 0,
                "avg_roi": float(ocpi_df.iloc[0]["avg_roi"]) if ocpi_df.iloc[0]["avg_roi"] else 0,
            }
        
        if cpi_df is not None and not cpi_df.empty:
            result["cpi"] = {
                "adgroup_cnt": int(cpi_df.iloc[0]["adgroup_cnt"]) if cpi_df.iloc[0]["adgroup_cnt"] else 0,
                "total_cost": float(cpi_df.iloc[0]["total_cost"]) if cpi_df.iloc[0]["total_cost"] else 0,
                "total_income": float(cpi_df.iloc[0]["total_income"]) if cpi_df.iloc[0]["total_income"] else 0,
                "avg_roi": float(cpi_df.iloc[0]["avg_roi"]) if cpi_df.iloc[0]["avg_roi"] else 0,
            }
        
        return result
        
    except Exception as e:
        print(f"[monitor_ltv_roi] Warning: Failed to get lianyun game stats: {e}")
    
    return {
        "ocpi": {"adgroup_cnt": 0, "total_cost": 0, "total_income": 0, "avg_roi": 0},
        "cpi": {"adgroup_cnt": 0, "total_cost": 0, "total_income": 0, "avg_roi": 0},
    }


def _create_group_detail_table(
    odps: OdpsClient,
    dt: str,
    min_cost_threshold: float,
    output_table: str,
) -> None:
    """创建消耗>=threshold的group明细表"""
    # 删除旧表
    drop_sql = f"DROP TABLE IF EXISTS {output_table};"
    try:
        odps.run_sql(drop_sql)
    except Exception as e:
        print(f"[monitor_ltv_roi] Warning: Drop table failed (may not exist): {e}")

    # 创建结果表（仅OCPI类型，消耗>=threshold）
    create_sql = f"""
    CREATE TABLE {output_table} AS
    SELECT 
        ad_group_id,
        MAX(ad_group_title) AS ad_group_title,
        SUM(cpi_cost) AS cost,
        SUM(income) AS income,
        CASE 
            WHEN SUM(cpi_cost) > 0 
            THEN SUM(income) / SUM(cpi_cost) 
            ELSE 0 
        END AS roi,
        SUM(show_num) AS show_num,
        SUM(click_cnt) AS click_cnt,
        '{dt}' AS dt
    FROM com_cdm.dws_tracker_ad_cpc_cost_hi
    WHERE dh >= '{dt}00'
      AND dh <= '{dt}23'
      AND cost_type = 'ocpi'
      AND ad_group_id IS NOT NULL
      AND ad_group_id != ''
    GROUP BY ad_group_id
    HAVING SUM(cpi_cost) >= {min_cost_threshold}
    ORDER BY cost DESC
    LIMIT 1000
    """
    odps.run_sql(create_sql)


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
    "name": "monitor_ltv_roi",
    "description": "LTV数据分析Skill：计算固定日期OCPI账户的总消耗及整体ROI，联运游戏客户的消耗及ROI，并输出高消耗group明细。",
    "inputs": {
        "dt": "Date (yyyyMMdd format)",
        "min_cost_threshold": "Group minimum cost threshold in USD (default: 100)",
        "output_table": "Output table name (auto-generated if not provided)",
    },
    "run": run,
}
