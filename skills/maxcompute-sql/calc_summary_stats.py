from typing import Any, Dict, Optional
import pandas as pd

from gold_miner.odps_client import OdpsClient, OdpsConfig
from gold_miner.config import Config


def run(
    input_table: str = "adgroup_show_clk_conv_data",
    summary_type: str = "clk",
    output_table: str = "show_clk_conv_summary",
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    计算消耗/CTR/CVR/eCPM 等汇总指标

    参数:
        input_table: 输入表名（build_adgroup_data 输出的表）
        summary_type: 汇总类型，'clk' = 点击维度，'dld' = 下载维度
        output_table: 输出表名
    """
    config = config or _get_config()
    odps = _create_odps_client(config)

    if summary_type == "clk":
        sql = _build_clk_summary_sql(input_table, output_table)
    elif summary_type == "dld":
        sql = _build_dld_summary_sql(input_table, output_table)
    else:
        return {"error": f"Unknown summary_type: {summary_type}. Use 'clk' or 'dld'"}

    print(f"[calc_summary_stats] Executing SQL for {summary_type} summary...")
    df = odps.run_sql(sql)

    return {
        "status": "success",
        "summary_type": summary_type,
        "output_table": output_table,
        "rows": len(df) if df is not None else 0,
        "message": f"Summary table {output_table} created successfully",
    }


def _build_clk_summary_sql(input_table: str, output_table: str) -> str:
    return f"""
    DROP TABLE IF EXISTS {output_table};

    SET odps.instance.priority = 7;

    CREATE TABLE IF NOT EXISTS {output_table}
    LIFECYCLE 30 AS
    SELECT  t.*
            ,round(show_num/show_cnt, 4) as show_dup_ratio
            ,round(clk_num/clk_cnt, 4) as clk_dup_ratio
            ,round(EW消耗 / show_num * 1000,2) AS eCPM
            ,round(CASE    WHEN EW消耗 > 0 THEN ecpm_sum / EW消耗 ELSE NULL END,2) AS pcoc_ecpm
            ,round(CASE    WHEN show_num > 0 THEN clk_num / show_num ELSE NULL END,4) AS ctr
            ,round(CASE    WHEN clk_num > 0 THEN conv_cnt / clk_num ELSE NULL END,4) AS cvr
            ,round(CASE    WHEN clk_num > 0 THEN pred_clk_num / clk_num ELSE NULL END,2) AS pcoc_ctr
            ,round(CASE    WHEN conv_cnt > 0 THEN pred_conv_num / conv_cnt ELSE NULL END,2) AS pcoc_cvr
    FROM    (
                SELECT  cost_type
                        ,round(SUM(ecpm_sum),1) AS ecpm_sum
                        ,round(SUM(cost_sum),1) AS EW消耗
                        ,SUM(show_num) AS show_num
                        ,SUm(show_cnt) as show_cnt
                        ,SUM(clk_num) AS clk_num
                        ,sum(clk_cnt) as clk_cnt
                        ,round(SUM(pctr_sum),0) AS pred_clk_num
                        ,SUM(conv_num) AS conv_cnt
                        ,round(SUM(pcvr_sum),0) AS pred_conv_num
                FROM    {input_table} t1
                WHERE   is_offline_ad = '0'
                AND     business_line_nm != '分发'
                AND     cost_type IN ('2','3','6','7')
                GROUP BY cost_type
            ) t
    ORDER BY t.EW消耗 DESC
    LIMIT   1000
    ;

    SELECT  *
    FROM    {output_table}
    ;
    """


def _build_dld_summary_sql(input_table: str, output_table: str) -> str:
    return f"""
    DROP TABLE IF EXISTS {output_table};

    SET odps.instance.priority = 7;

    CREATE TABLE IF NOT EXISTS {output_table}
    LIFECYCLE 30 AS
    SELECT  t.*
            ,round(EW消耗 / show_num * 1000,2) AS eCPM
            ,round(CASE    WHEN EW消耗 > 0 THEN ecpm_sum / EW消耗 ELSE NULL END,2) AS pcoc_ecpm
            ,round(CASE    WHEN show_num > 0 THEN dld_num / show_num ELSE NULL END,4) AS dctr
            ,round(CASE    WHEN dld_num > 0 THEN conv_cnt / dld_num ELSE NULL END,4) AS dcvr
            ,round(CASE    WHEN dld_num > 0 THEN pred_dld_num / dld_num ELSE NULL END,2) AS pcoc_dctr
            ,round(CASE    WHEN conv_cnt > 0 THEN pred_conv_num / conv_cnt ELSE NULL END,2) AS pcoc_dcvr
    FROM    (
                SELECT  cost_type
                        ,round(SUM(ecpm_sum),1) AS ecpm_sum
                        ,round(SUM(cost_sum),1) AS EW消耗
                        ,SUM(show_num) AS show_num
                        ,SUM(dld_num) AS dld_num
                        ,round(SUM(pdbr_sum),0) AS pred_dld_num
                        ,SUM(conv_num) AS conv_cnt
                        ,round(SUM(pdcvr_sum),0) AS pred_conv_num
                FROM    {input_table} t1
                WHERE   is_offline_ad = '0'
                AND     (
                            (
                                        business_line_nm != '分发'
                                        AND     cost_type IN ('4','5')
                            )
                            OR      (
                                        business_line_nm = '分发'
                                        AND     cost_type IN ('6','7')
                            )
                )
                GROUP BY cost_type
            ) t
    ORDER BY t.EW消耗 DESC
    LIMIT   1000
    ;

    SELECT  *
    FROM    {output_table}
    ;
    """


def _get_config() -> Dict[str, str]:
    from dotenv import load_dotenv
    import os

    load_dotenv()
    return {
        "access_id": os.getenv("ODPS_ACCESS_ID", ""),
        "access_key": os.getenv("ODPS_ACCESS_KEY", ""),
        "project": os.getenv("ODPS_PROJECT", ""),
        "endpoint": os.getenv("ODPS_ENDPOINT", ""),
    }


def _create_odps_client(config: Dict[str, str]) -> OdpsClient:
    odps_config = OdpsConfig(
        access_id=config["access_id"],
        access_key=config["access_key"],
        project=config["project"],
        endpoint=config["endpoint"],
    )
    return OdpsClient(odps_config)


SKILL = {
    "name": "calc_summary_stats",
    "description": "计算消耗/CTR/CVR/eCPM 等汇总指标。输入中间表，自动按 cost_type 汇总并计算核心业务指标。",
    "inputs": {
        "input_table": "str (可选) - 输入表名，默认 'adgroup_show_clk_conv_data'",
        "summary_type": "str (可选) - 汇总类型，'clk'=点击维度，'dld'=下载维度，默认 'clk'",
        "output_table": "str (可选) - 输出表名",
        "config": "dict (可选) - ODPS 配置",
    },
    "run": run,
}
