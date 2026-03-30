from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from gold_miner.odps_client import OdpsClient, OdpsConfig


def run(
    start_dt: str,
    end_dt: Optional[str] = None,
    output_table: Optional[str] = None,
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    ROAS偏差分析Skill
    计算ROAS模型的预估偏差，对比模型预估LTV与实际变现LTV的差异

    参数:
        start_dt: 开始日期（格式：yyyyMMdd）
        end_dt: 结束日期（格式：yyyyMMdd），默认等于start_dt
        output_table: 输出表名，默认自动生成
        config: ODPS 配置
    """
    config = config or _get_config()
    odps = _create_odps_client(config)

    # 设置日期范围
    if end_dt is None:
        end_dt = start_dt

    # 生成输出表名
    if output_table is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_table = f"roas_bias_{timestamp}"

    print(f"[roas_bias] 分析日期范围: {start_dt} ~ {end_dt}")

    # 计算相关日期
    dates = _get_date_range(start_dt, end_dt)
    
    # 创建临时表和计算偏差
    _create_bias_table(odps, start_dt, end_dt, output_table)
    
    # 获取汇总统计
    summary = _get_summary(odps, output_table)
    
    # 获取明细数据行数
    df_detail = odps.run_sql(f"SELECT COUNT(*) as cnt FROM {output_table}")
    detail_rows = int(df_detail.iloc[0]["cnt"]) if df_detail is not None and not df_detail.empty else 0

    return {
        "status": "success",
        "start_dt": start_dt,
        "end_dt": end_dt,
        "output_table": output_table,
        "detail_rows": detail_rows,
        "summary": summary,
        "message": f"ROAS偏差分析完成。明细表: {output_table}",
    }


def _get_date_range(start_dt: str, end_dt: str) -> List[str]:
    """获取日期范围内的所有日期"""
    dates = []
    current = datetime.strptime(start_dt, "%Y%m%d")
    end = datetime.strptime(end_dt, "%Y%m%d")
    
    while current <= end:
        dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    
    return dates


def _create_bias_table(
    odps: OdpsClient,
    start_dt: str,
    end_dt: str,
    output_table: str,
) -> None:
    """创建ROAS偏差分析表"""
    # 删除旧表
    drop_sql = f"DROP TABLE IF EXISTS {output_table};"
    try:
        odps.run_sql(drop_sql)
    except Exception as e:
        print(f"[roas_bias] Warning: Drop table failed (may not exist): {e}")

    # 计算日期偏移
    start_date = datetime.strptime(start_dt, "%Y%m%d")
    end_date = datetime.strptime(end_dt, "%Y%m%d")
    
    # 响应数据开始日期（往前22天）
    resp_start_date = start_date - timedelta(days=22)
    resp_start_dt = resp_start_date.strftime("%Y%m%d")
    
    # 响应数据结束日期（往后7天）
    resp_end_date = end_date + timedelta(days=7)
    resp_end_dt = resp_end_date.strftime("%Y%m%d")
    
    # 激活数据开始日期（往前11天）
    conv_start_date = start_date - timedelta(days=11)
    conv_start_dt = conv_start_date.strftime("%Y%m%d")
    
    # 激活数据结束日期（往后8天）
    conv_end_date = end_date + timedelta(days=8)
    conv_end_dt = conv_end_date.strftime("%Y%m%d")
    
    # 收入数据结束日期（激活后7天）
    revenue_end_date = end_date + timedelta(days=7)
    revenue_end_dt = revenue_end_date.strftime("%Y%m%d")

    # 创建偏差分析表
    create_sql = f"""
    CREATE TABLE {output_table} AS
    WITH response AS (
        SELECT  request_id,
                roas_ltv_model_name,
                code_seat_id,
                ad_creative_id,
                package_name,
                ltv_raw,
                ltv
        FROM    (
                    SELECT  request_id,
                            roas_ltv_model_name,
                            code_seat_id,
                            ad_creative_id,
                            package_name,
                            IF(ltv_raw IS NULL, ltv, ltv_raw) AS ltv_raw,
                            ltv,
                            ROW_NUMBER() OVER (PARTITION BY request_id, code_seat_id, ad_creative_id ORDER BY resp_ts) AS resp_rn
                    FROM    com_cdm.dwd_log_dsp_adserver_response_hi
                    WHERE   (is_offline_ad IS NULL OR is_offline_ad <> '1')
                    AND     dh >= '{resp_start_dt}00'
                    AND     dh <= '{resp_end_dt}23'
                    AND     gaid <> '00000000-0000-0000-0000-000000000000'
                    AND     cost_type IN ('7')
                    AND     ltv IS NOT NULL
                    AND     roas_ltv_model_name != 'downgrade_roas_ltv'
                    AND     roas_ltv_model_name IS NOT NULL
                    AND     roas_ltv_model_name LIKE '%roas_%'
                ) t2c
        WHERE   resp_rn = 1
    ),
    init_info AS (
        SELECT  *
        FROM    (
                    SELECT  request_id,
                            ad_creative_id,
                            ad_group_id,
                            gaid,
                            billing_actual_deduction_price,
                            CAST(trans_event_ts AS BIGINT) AS init_ts,
                            package_name,
                            SUBSTR(dh, 1, 8) AS dt,
                            ROW_NUMBER() OVER (PARTITION BY request_id, ad_creative_id ORDER BY trans_event_ts) AS rn
                    FROM    com_cdm.dwd_eagllwin_conv_log_hi
                    WHERE   dh BETWEEN '{conv_start_dt}00' AND '{conv_end_dt}23'
                    AND     COALESCE(is_natural, '0') != '1'
                    AND     COALESCE(is_inapp_ad, '0') != '1'
                    AND     request_id IS NOT NULL
                    AND     ad_creative_id IS NOT NULL
                    AND     gaid IS NOT NULL
                    AND     gaid <> '00000000-0000-0000-0000-000000000000'
                    AND     trans_event_type IN ('2', '激活')
                    AND     bid_type IN ('7')
                )
        WHERE   rn = 1
    ),
    init_join_response AS (
        SELECT  response.roas_ltv_model_name,
                init_info.gaid,
                init_info.ad_group_id,
                response.ltv_raw,
                init_info.dt,
                response.ltv AS pltv,
                init_info.billing_actual_deduction_price AS cost,
                response.package_name,
                init_info.package_name AS package_name1
        FROM    response
        JOIN    init_info
        ON      init_info.request_id = response.request_id
        AND     init_info.ad_creative_id = response.ad_creative_id
        WHERE   init_info.dt BETWEEN '{start_dt}' AND '{end_dt}'
    ),
    revenue AS (
        SELECT  gaid,
                package_name,
                100 * SUM(income) AS ltv,
                SUBSTR(dh, 1, 8) AS dt
        FROM    com_cdm.dws_eagllwin_deep_conv_income_hi
        WHERE   dh BETWEEN '{conv_start_dt}00' AND '{revenue_end_dt}23'
        GROUP BY gaid, package_name, SUBSTR(dh, 1, 8)
    )
    SELECT  init_join_response.ad_group_id,
            SUM(init_join_response.ltv_raw) AS pltv_raw,
            SUM(init_join_response.pltv) AS pltv,
            SUM(revenue.ltv) AS ltv,
            SUM(init_join_response.cost) / 1000 / 100 AS cost,
            CASE 
                WHEN SUM(init_join_response.pltv) > 0 
                THEN SUM(revenue.ltv) / SUM(init_join_response.pltv) - 1
                ELSE NULL 
            END AS bias_ltv,
            CASE 
                WHEN SUM(init_join_response.cost) > 0 
                THEN SUM(revenue.ltv) * 1000 / SUM(init_join_response.cost)
                ELSE NULL 
            END AS roi7,
            CASE 
                WHEN SUM(init_join_response.ltv_raw) > 0 
                THEN SUM(revenue.ltv) / SUM(init_join_response.ltv_raw) - 1
                ELSE NULL 
            END AS bias_ltv_raw,
            ABS(SUM(init_join_response.cost) / 1000 / 100 * 
                CASE 
                    WHEN SUM(init_join_response.pltv) > 0 
                    THEN SUM(revenue.ltv) / SUM(init_join_response.pltv) - 1
                    ELSE 0 
                END
            ) AS abs_bias
    FROM    init_join_response
    LEFT JOIN revenue
    ON      init_join_response.gaid = revenue.gaid
    AND     init_join_response.package_name1 = revenue.package_name
    AND     DATEDIFF(
                CAST(CONCAT(SUBSTR(init_join_response.dt, 1, 4), '-', SUBSTR(init_join_response.dt, 5, 2), '-', SUBSTR(init_join_response.dt, 7, 2)) AS DATE),
                CAST(CONCAT(SUBSTR(revenue.dt, 1, 4), '-', SUBSTR(revenue.dt, 5, 2), '-', SUBSTR(revenue.dt, 7, 2)) AS DATE)
            ) BETWEEN -7 AND 0
    GROUP BY init_join_response.ad_group_id
    HAVING  SUM(init_join_response.cost) > 0
    ORDER BY cost DESC
    """
    
    odps.run_sql(create_sql)


def _get_summary(odps: OdpsClient, output_table: str) -> Dict[str, Any]:
    """获取汇总统计"""
    try:
        # 总体汇总
        summary_sql = f"""
        SELECT 
            COUNT(*) AS total_adgroups,
            SUM(cost) AS total_cost,
            SUM(pltv) AS total_pltv,
            SUM(ltv) AS total_ltv,
            CASE 
                WHEN SUM(pltv) > 0 
                THEN SUM(ltv) / SUM(pltv) - 1
                ELSE NULL 
            END AS overall_bias,
            CASE 
                WHEN SUM(cost) > 0 
                THEN SUM(ltv) * 1000 / (SUM(cost) * 1000)
                ELSE NULL 
            END AS overall_roi7,
            SUM(abs_bias) AS total_abs_bias,
            CASE 
                WHEN SUM(cost) > 0 
                THEN SUM(abs_bias) / SUM(cost)
                ELSE NULL 
            END AS weighted_bias
        FROM {output_table}
        """
        df = odps.run_sql(summary_sql)
        
        if df is not None and not df.empty:
            return {
                "total_adgroups": int(df.iloc[0]["total_adgroups"]) if df.iloc[0]["total_adgroups"] else 0,
                "total_cost": float(df.iloc[0]["total_cost"]) if df.iloc[0]["total_cost"] else 0,
                "total_pltv": float(df.iloc[0]["total_pltv"]) if df.iloc[0]["total_pltv"] else 0,
                "total_ltv": float(df.iloc[0]["total_ltv"]) if df.iloc[0]["total_ltv"] else 0,
                "overall_bias": float(df.iloc[0]["overall_bias"]) if df.iloc[0]["overall_bias"] else None,
                "overall_roi7": float(df.iloc[0]["overall_roi7"]) if df.iloc[0]["overall_roi7"] else None,
                "total_abs_bias": float(df.iloc[0]["total_abs_bias"]) if df.iloc[0]["total_abs_bias"] else 0,
                "weighted_bias": float(df.iloc[0]["weighted_bias"]) if df.iloc[0]["weighted_bias"] else None,
            }
    except Exception as e:
        print(f"[roas_bias] Warning: Failed to get summary: {e}")

    return {}


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
    "name": "roas_bias",
    "description": "Calculate ROAS model prediction bias by comparing predicted LTV with actual revenue. Invoke when user needs to analyze ROAS model accuracy or forecast deviation.",
    "inputs": {
        "start_dt": "Start date (yyyyMMdd format)",
        "end_dt": "End date (yyyyMMdd format, optional, defaults to start_dt)",
        "output_table": "Output table name (auto-generated if not provided)",
    },
    "run": run,
}
