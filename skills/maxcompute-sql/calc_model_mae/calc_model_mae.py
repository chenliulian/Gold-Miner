from typing import Any, Dict, Optional

from gold_miner.odps_client import OdpsClient, OdpsConfig


def run(
    ctr_table: str = "adgroup_level_pcoc_stats_ctr",
    cvr_table: str = "adgroup_level_pcoc_stats_cvr",
    output_table: str = "model_pred_mae",
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    计算 CTR/CVR 模型预测的 MAE (Mean Absolute Error) 误差

    参数:
        ctr_table: CTR 偏差分析表
        cvr_table: CVR 偏差分析表
        output_table: 输出表名
        config: ODPS 配置
    """
    config = config or _get_config()
    odps = _create_odps_client(config)

    sql = f"""
    DROP TABLE IF EXISTS {output_table};

    SET odps.instance.priority = 7;

    CREATE TABLE IF NOT EXISTS {output_table} LIFECYCLE 7 AS
    SELECT  'CTR' AS model_type,
            'pkg_buz' AS stats_group,
            COUNT(DISTINCT CONCAT(t1.ad_package_name, t1.business_line_nm)) AS group_cnt,
            SUM(t1.show_num) AS show_num,
            SUM(t1.clk_num) AS clk_num,
            SUM(t1.pctr_sum) AS pctr_sum,
            SUM(t1.show_num / t2.show_num_tt * t1.abs_error) AS mae,
            SUM(t1.show_num / t2.show_num_tt * t1.abs_error) / SUM(t1.clk_num) AS mae_rate
    FROM package_buz_level_pcoc_stats_ctr t1
    JOIN (
        SELECT SUM(show_num) AS show_num_tt
        FROM package_buz_level_pcoc_stats_ctr
    ) t2 ON 1 = 1
    WHERE t1.show_num >= 1000

    UNION ALL

    SELECT  'CTR' AS model_type,
            'adgroup' AS stats_group,
            COUNT(DISTINCT t1.ad_group_id) AS group_cnt,
            SUM(t1.show_num) AS show_num,
            SUM(t1.clk_num) AS clk_num,
            SUM(t1.pctr_sum) AS pctr_sum,
            SUM(t1.show_num / t2.show_num_tt * t1.abs_error) AS mae,
            SUM(t1.show_num / t2.show_num_tt * t1.abs_error) / SUM(t1.clk_num) AS mae_rate
    FROM {ctr_table} t1
    JOIN (
        SELECT SUM(show_num) AS show_num_tt
        FROM {ctr_table}
        WHERE show_num >= 1000
    ) t2 ON 1 = 1
    WHERE t1.show_num >= 1000

    UNION ALL

    SELECT  'CVR' AS model_type,
            'adgroup' AS stats_group,
            COUNT(DISTINCT t1.ad_group_id) AS group_cnt,
            SUM(t1.clk_num) AS clk_num,
            SUM(t1.conv_num) AS conv_num,
            SUM(t1.pcvr_sum) AS pcvr_sum,
            SUM(t1.clk_num / t2.clk_num_tt * t1.abs_error) AS mae,
            SUM(t1.clk_num / t2.clk_num_tt * t1.abs_error) / SUM(t1.conv_num) AS mae_rate
    FROM {cvr_table} t1
    JOIN (
        SELECT SUM(clk_num) AS clk_num_tt
        FROM {cvr_table}
        WHERE clk_num >= 1000
    ) t2 ON 1 = 1
    WHERE t1.clk_num >= 1000

    UNION ALL

    SELECT  'CVR' AS model_type,
            'pkg_buz' AS stats_group,
            COUNT(DISTINCT CONCAT(t1.ad_package_name, t1.business_line_nm)) AS group_cnt,
            SUM(t1.clk_num) AS clk_num,
            SUM(t1.conv_num) AS conv_num,
            SUM(t1.pcvr_sum) AS pcvr_sum,
            SUM(t1.clk_num / t2.clk_num_tt * t1.abs_error) AS mae,
            SUM(t1.clk_num / t2.clk_num_tt * t1.abs_error) / SUM(t1.conv_num) AS mae_rate
    FROM package_buz_level_pcoc_stats_cvr t1
    JOIN (
        SELECT SUM(clk_num) AS clk_num_tt
        FROM package_buz_level_pcoc_stats_cvr
        WHERE clk_num >= 1000
    ) t2 ON 1 = 1
    WHERE t1.clk_num >= 1000
    ;

    SELECT  *
    FROM    {output_table}
    ;
    """

    print(f"[calc_model_mae] Executing MAE calculation...")
    df = odps.run_sql(sql)

    return {
        "status": "success",
        "ctr_table": ctr_table,
        "cvr_table": cvr_table,
        "output_table": output_table,
        "rows": len(df) if df is not None else 0,
        "message": f"Model MAE table {output_table} created",
    }


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
    "name": "calc_model_mae",
    "description": "计算 CTR/CVR 模型预测的 MAE (平均绝对误差)。需要先运行 analyze_ctr_pcoc 和 analyze_cvr_pcoc 生成中间表。",
    "inputs": {
        "ctr_table": "str (可选) - CTR 偏差分析表，默认 'adgroup_level_pcoc_stats_ctr'",
        "cvr_table": "str (可选) - CVR 偏差分析表，默认 'adgroup_level_pcoc_stats_cvr'",
        "output_table": "str (可选) - 输出表名，默认 'model_pred_mae'",
        "config": "dict (可选) - ODPS 配置",
    },
    "run": run,
}
