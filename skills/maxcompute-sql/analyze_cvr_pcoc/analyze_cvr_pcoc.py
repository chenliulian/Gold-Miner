from typing import Any, Dict, List, Optional

from gold_miner.odps_client import OdpsClient, OdpsConfig


def run(
    input_table: str = "adgroup_show_clk_conv_data",
    level: str = "adgroup",
    conv_type: str = "all",
    cost_types: Optional[List[str]] = None,
    output_table: Optional[str] = None,
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    分析 CVR 模型的预估偏差 (PCOC = Predicted CVR / Actual CVR)

    参数:
        input_table: 输入表名
        level: 分析维度，'adgroup'=广告组维度，'pkg_buz'=包名+业务线维度
        conv_type: 转化类型，'all'=全部，'cpi'=CPA(CPI)，'ocpc'=oCPC，'ocpi'=oCPI
        cost_types: 投放类型列表，默认 ['3', '6', '7']
        output_table: 输出表名，默认自动生成
        config: ODPS 配置
    """
    config = config or _get_config()
    odps = _create_odps_client(config)

    if conv_type == "all":
        cost_types = cost_types or ["3", "6", "7"]
    elif conv_type == "cpi":
        cost_types = cost_types or ["6"]
    elif conv_type == "ocpc":
        cost_types = cost_types or ["3"]
    elif conv_type == "ocpi":
        cost_types = cost_types or ["7"]
    else:
        return {"error": f"Unknown conv_type: {conv_type}"}

    cost_types_str = ", ".join([f"'{ct}'" for ct in cost_types])

    if level == "adgroup":
        output_table = output_table or f"adgroup_level_pcoc_stats_cvr_{conv_type}"
        sql = _build_adgroup_cvr_sql(input_table, cost_types_str, output_table)
    elif level == "pkg_buz":
        output_table = output_table or f"package_buz_level_pcoc_stats_cvr_{conv_type}"
        sql = _build_pkg_buz_cvr_sql(input_table, cost_types_str, output_table)
    else:
        return {"error": f"Unknown level: {level}. Use 'adgroup' or 'pkg_buz'"}

    print(f"[analyze_cvr_pcoc] Executing CVR PCOC analysis at {level} level, conv_type={conv_type}...")
    df = odps.run_sql(sql)

    return {
        "status": "success",
        "level": level,
        "conv_type": conv_type,
        "cost_types": cost_types,
        "output_table": output_table,
        "rows": len(df) if df is not None else 0,
        "message": f"CVR PCOC analysis table {output_table} created",
    }


def _build_adgroup_cvr_sql(input_table: str, cost_types_str: str, output_table: str) -> str:
    return f"""
    DROP TABLE IF EXISTS {output_table};

    SET odps.instance.priority = 7;

    CREATE TABLE {output_table} AS
    SELECT t.*,
           t.pcvr_raw_sum/t.conv_num AS pcoc_raw,
           ABS(t.pcvr_raw_sum/t.conv_num - 1) AS abs_error_raw,
           t.pcvr_sum/t.conv_num AS pcoc,
           ABS(t.pcvr_sum/t.conv_num - 1) AS abs_error,
           t.clk_num/t.clk_cnt AS clk_dup_ratio
    FROM (
        SELECT cost_type,
               ad_group_id,
               SUM(clk_num) AS clk_num,
               SUM(clk_cnt) AS clk_cnt,
               SUM(conv_num) AS conv_num,
               SUM(pcvr_raw_sum) AS pcvr_raw_sum,
               SUM(pcvr_sum) AS pcvr_sum,
               SUM(conv_num) / SUM(clk_num) AS cvr,
               SUM(pcvr_raw_sum) / SUM(clk_num) AS pcvr_raw,
               SUM(pcvr_sum) / SUM(clk_num) AS pcvr
        FROM {input_table}
        WHERE cost_type IN ({cost_types_str})
          AND business_line_nm != '分发'
          AND is_offline_ad = '0'
        GROUP BY cost_type, ad_group_id
    ) t
    WHERE t.clk_num >= 2000 AND t.cvr > 0.005
    ;
    """


def _build_pkg_buz_cvr_sql(input_table: str, cost_types_str: str, output_table: str) -> str:
    return f"""
    DROP TABLE IF EXISTS {output_table};

    SET odps.instance.priority = 7;

    CREATE TABLE {output_table} AS
    SELECT t.*,
           t.pcvr_raw_sum/t.conv_num AS pcoc_raw,
           ABS(t.pcvr_raw_sum/t.conv_num - 1) AS abs_error_raw,
           t.pcvr_sum/t.conv_num AS pcoc,
           ABS(t.pcvr_sum/t.conv_num - 1) AS abs_error
    FROM (
        SELECT cost_type,
               ad_package_name,
               business_line_nm,
               SUM(clk_num) AS clk_num,
               SUM(conv_num) AS conv_num,
               SUM(pcvr_raw_sum) AS pcvr_raw_sum,
               SUM(pcvr_sum) AS pcvr_sum,
               SUM(conv_num) / SUM(clk_num) AS cvr,
               SUM(pcvr_raw_sum) / SUM(clk_num) AS pcvr_raw,
               SUM(pcvr_sum) / SUM(clk_num) AS pcvr
        FROM {input_table}
        WHERE cost_type IN ({cost_types_str})
          AND business_line_nm != '分发'
          AND is_offline_ad = '0'
        GROUP BY cost_type, ad_package_name, business_line_nm
    ) t
    WHERE t.clk_num >= 2000 AND t.cvr > 0.005
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
    "name": "analyze_cvr_pcoc",
    "description": "分析 CVR 模型的预估偏差(PCOC)，支持 adgroup 和 pkg_buz 维度。可按转化类型(cpi/ocpc/ocpi)筛选。",
    "inputs": {
        "input_table": "str (可选) - 输入表名，默认 'adgroup_show_clk_conv_data'",
        "level": "str (可选) - 分析维度，'adgroup'=广告组，'pkg_buz'=包名+业务线，默认 'adgroup'",
        "conv_type": "str (可选) - 转化类型，'all'=全部，'cpi'=CPA，'ocpc'=oCPC，'ocpi'=oCPI，默认 'all'",
        "cost_types": "list (可选) - 投放类型，默认根据 conv_type 自动选择",
        "output_table": "str (可选) - 输出表名",
        "config": "dict (可选) - ODPS 配置",
    },
    "run": run,
}
