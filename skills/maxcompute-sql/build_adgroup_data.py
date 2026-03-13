from typing import Any, Dict, Optional
import pandas as pd

from gold_miner.odps_client import OdpsClient, OdpsConfig
from gold_miner.config import Config


def run(
    start_date: str,
    end_date: str,
    output_table: str = "adgroup_show_clk_conv_data",
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    构建 adgroup 维度的中间聚合表，包含展示/点击/下载/转化数据

    参数:
        start_date: 开始日期，格式 YYYYMMDD，如 '20260301'
        end_date: 结束日期，格式 YYYYMMDD，如 '20260310'
        output_table: 输出表名
    """
    config = config or _get_config()
    odps = _create_odps_client(config)

    end_date_pt5 = end_date

    sql = f"""
    DROP TABLE IF EXISTS {output_table};

    SET odps.instance.priority = 7;

    CREATE TABLE IF NOT EXISTS {output_table}
    LIFECYCLE 30 AS
    SELECT  t1.*
            ,t2.app_name
            ,t2.business_line_nm
            ,t3.country_name_zh
    FROM    (
                SELECT  cost_type
                        ,ad_package_name
                        ,ad_group_id
                        ,app_id
                        ,national_id
                        ,is_offline_ad
                        ,SUM(show_label) AS show_num
                        ,COUNT(distinct case when show_label=1 then concat(request_id, ad_creative_id) else null end) as show_cnt
                        ,SUM(click_label) AS clk_num
                        ,COUNT(distinct case when click_label=1 then concat(request_id, ad_creative_id) else null end ) as clk_cnt
                        ,SUM(dld_label) AS dld_num
                        ,COUNT(distinct case when dld_label=1 then concat(request_id, ad_creative_id) else null end) as dld_cnt
                        ,SUM(ctr_raw) AS pctr_raw_sum
                        ,SUM(cast(ctr as double)) AS pctr_sum
                        ,SUM(dbr_raw) AS pdbr_raw_sum
                        ,SUM(dbr) AS pdbr_sum
                        ,SUM(
                            IF(click_label = 1,
                               CASE    WHEN cost_type IN ('6','7') THEN conv_label_active
                                       WHEN transform_target_cn LIKE '%注册%' THEN conv_label_register
                                       WHEN transform_target_cn = '付费' THEN conv_label_pay
                                       WHEN transform_target_cn = '首次付费' THEN conv_label_first_pay
                                       WHEN cost_type = '3' THEN conv_label_pay
                                       ELSE 0
                               END
                            ,0)
                        ) AS conv_num
                        ,SUM(
                            IF(dld_label = 1,
                               CASE    WHEN cost_type IN ('6','7') THEN conv_label_active
                                       WHEN transform_target_cn LIKE '%注册%' THEN conv_label_register
                                       WHEN transform_target_cn = '付费' THEN conv_label_pay
                                       WHEN transform_target_cn = '首次付费' THEN conv_label_first_pay
                                       WHEN cost_type = '3' THEN conv_label_pay
                                       ELSE 0
                               END
                            ,0)
                        ) AS conv_num2
                        ,SUM(CASE    WHEN click_label = 1 THEN cvr_raw ELSE 0 END) AS pcvr_raw_sum
                        ,SUM(CASE    WHEN click_label = 1 THEN cvr ELSE 0 END) AS pcvr_sum
                        ,SUM(CASE    WHEN dld_label = 1 THEN cvr_raw ELSE 0 END) AS pdcvr_raw_sum
                        ,SUM(CASE    WHEN dld_label = 1 THEN cvr ELSE 0 END) AS pdcvr_sum
                        ,SUM(billing_actual_deduction_price) / 1e5 AS cost_sum
                        ,SUM(CASE    WHEN show_label = 1 THEN ecpm_raw ELSE 0 END) / 1e5 AS ecpm_sum
                FROM    mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
                WHERE   dh >= '{start_date}00'
                AND     dh <= '{end_date_pt5}23'
                AND     is_inapp_ad = '0'
                AND     (request_id is not null and ad_creative_id is not null)
                AND     (request_id!='' and ad_creative_id!='')
                AND     (ad_group_id is not null and ad_group_id!='')
                AND     (gaid != '00000000-0000-0000-0000-000000000000' AND gaid IS NOT NULL AND gaid != '')
                AND     show_label=1
                AND     TO_CHAR(FROM_UNIXTIME(CAST(show_ts / 1000 AS BIGINT)),"yyyymmdd") BETWEEN '{start_date}' AND '{end_date}'
                AND     first_price > 0
                GROUP BY cost_type
                         ,ad_package_name
                         ,ad_group_id
                         ,app_id
                         ,national_id
                         ,is_offline_ad
            ) t1
    LEFT JOIN   (
                    SELECT  media_app_id
                            ,MAX(business_line_nm) AS business_line_nm
                            ,MAX(app_name) AS app_name
                    FROM    com_cdm.dim_code_seat_dd
                    WHERE   dt = MAX_PT('com_cdm.dim_code_seat_dd')
                    GROUP BY media_app_id
                ) t2
    ON      t1.app_id = t2.media_app_id
    LEFT JOIN   (
                    SELECT  DISTINCT country_code
                            ,country_name_zh
                    FROM    com_cdm.dim_country_info
                ) t3
    ON      t1.national_id = t3.country_code
    ;
    """

    print(f"[build_adgroup_data] Executing SQL to build {output_table}...")
    odps.run_script(sql)

    return {
        "status": "success",
        "output_table": output_table,
        "date_range": f"{start_date} to {end_date}",
        "message": f"Table {output_table} created successfully",
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
    "name": "build_adgroup_data",
    "description": "构建 adgroup 维度的中间聚合表，包含展示/点击/下载/转化等核心指标。输入日期范围，会在 ODPS 创建临时表。",
    "inputs": {
        "start_date": "str (必需) - 开始日期，格式 YYYYMMDD，如 '20260301'",
        "end_date": "str (必需) - 结束日期，格式 YYYYMMDD，如 '20260310'",
        "output_table": "str (可选) - 输出表名，默认 'adgroup_show_clk_conv_data'",
        "config": "dict (可选) - ODPS 配置，默认从环境变量读取",
    },
    "run": run,
}
