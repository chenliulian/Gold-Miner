from typing import Any, Dict, List, Optional

from gold_miner.odps_client import OdpsClient, OdpsConfig


def run(
    input_table: str = "adgroup_show_clk_conv_data",
    level: str = "adgroup",
    cost_types: Optional[List[str]] = None,
    output_table: Optional[str] = None,
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    分析 CTR 模型的预估偏差 (PCOC = Predicted CTR / Actual CTR)

    参数:
        input_table: 输入表名
        level: 分析维度，'adgroup'=广告组维度，'pkg_buz'=包名+业务线维度
        cost_types: 投放类型列表，如 ['2', '3', '6', '7']，默认全部
        output_table: 输出表名，默认自动生成
        config: ODPS 配置
    """
    config = config or _get_config()
    odps = _create_odps_client(config)

    cost_types = cost_types or ["2", "3", "6", "7"]
    cost_types_str = ", ".join([f"'{ct}'" for ct in cost_types])

    if level == "adgroup":
        output_table = output_table or "adgroup_level_pcoc_stats_ctr"
        sql = _build_adgroup_ctr_sql(input_table, cost_types_str, output_table)
    elif level == "pkg_buz":
        output_table = output_table or "package_buz_level_pcoc_stats_ctr"
        sql = _build_pkg_buz_ctr_sql(input_table, cost_types_str, output_table)
    else:
        return {"error": f"Unknown level: {level}. Use 'adgroup' or 'pkg_buz'"}

    print(f"[analyze_ctr_pcoc] Executing CTR PCOC analysis at {level} level...")
    df = odps.run_sql(sql)

    return {
        "status": "success",
        "level": level,
        "cost_types": cost_types,
        "output_table": output_table,
        "rows": len(df) if df is not None else 0,
        "message": f"CTR PCOC analysis table {output_table} created",
    }


def _build_adgroup_ctr_sql(input_table: str, cost_types_str: str, output_table: str) -> str:
    return f"""
    DROP TABLE IF EXISTS {output_table};

    SET odps.instance.priority = 7;

    CREATE TABLE {output_table} AS
    SELECT t.*,
           t.pctr_raw_sum/t.clk_num AS pcoc_raw,
           ABS(t.pctr_raw_sum/t.clk_num - 1) AS abs_error_raw,
           t.pctr_sum/t.clk_num AS pcoc,
           ABS(t.pctr_sum/t.clk_num - 1) AS abs_error
    FROM (
        SELECT cost_type,
               ad_group_id,
               SUM(show_num) AS show_num,
               SUM(clk_num) AS clk_num,
               SUM(pctr_raw_sum) AS pctr_raw_sum,
               SUM(pctr_sum) AS pctr_sum,
               SUM(clk_num) / SUM(show_num) AS ctr,
               SUM(pctr_raw_sum) / SUM(show_num) AS pctr_raw,
               SUM(pctr_sum) / SUM(show_num) AS pctr
        FROM {input_table}
        WHERE cost_type IN ({cost_types_str})
          AND business_line_nm != '分发'
          AND is_offline_ad != '1'
        GROUP BY cost_type, ad_group_id
    ) t
    WHERE t.show_num >= 1000 AND t.ctr > 0.005
    ;
    """


def _build_pkg_buz_ctr_sql(input_table: str, cost_types_str: str, output_table: str) -> str:
    return f"""
    DROP TABLE IF EXISTS {output_table};

    SET odps.instance.priority = 7;

    CREATE TABLE {output_table} AS
    SELECT t.*,
           t.pctr_raw_sum/t.clk_num AS pcoc_raw,
           ABS(t.pctr_raw_sum/t.clk_num - 1) AS abs_error_raw,
           t.pctr_sum/t.clk_num AS pcoc,
           ABS(t.pctr_sum/t.clk_num - 1) AS abs_error
    FROM (
        SELECT cost_type,
               ad_package_name,
               business_line_nm,
               SUM(show_num) AS show_num,
               SUM(clk_num) AS clk_num,
               SUM(pctr_raw_sum) AS pctr_raw_sum,
               SUM(pctr_sum) AS pctr_sum,
               SUM(clk_num) / SUM(show_num) AS ctr,
               SUM(pctr_raw_sum) / SUM(show_num) AS pctr_raw,
               SUM(pctr_sum) / SUM(show_num) AS pctr
        FROM {input_table}
        WHERE cost_type IN ({cost_types_str})
          AND business_line_nm != '分发'
          AND is_offline_ad = '0'
        GROUP BY cost_type, ad_package_name, business_line_nm
    ) t
    WHERE t.show_num >= 1000 AND t.ctr > 0.005
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
    "name": "analyze_ctr_pcoc",
    "description": "分析 CTR 模型的预估偏差(PCOC)，支持 adgroup 和 pkg_buz 维度。计算 pCTR 与实际 CTR 的比值及误差。",
    "inputs": {
        "input_table": "str (可选) - 输入表名，默认 'adgroup_show_clk_conv_data'",
        "level": "str (可选) - 分析维度，'adgroup'=广告组，'pkg_buz'=包名+业务线，默认 'adgroup'",
        "cost_types": "list (可选) - 投放类型，如 ['2','3','6','7']，默认全部",
        "output_table": "str (可选) - 输出表名",
        "config": "dict (可选) - ODPS 配置",
    },
    "run": run,
}
