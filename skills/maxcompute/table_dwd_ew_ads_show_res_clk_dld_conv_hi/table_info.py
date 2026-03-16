
from typing import Any, Dict

def run(table_name: str = "mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi") -> Dict[str, Any]:
    """
    mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 表的元信息

    更多信息请查看同目录下的 SKILL.md
    """
    return {
        "table_name": "mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi",
        "project": "mi_ads_dmp",
        "columns_count": 116,
        "partitions_count": 1,
    }


SKILL = {
    "name": "table_dwd_ew_ads_show_res_clk_dld_conv_hi",
    "description": "mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 表的元信息和字段说明",
    "inputs": {
        "table_name": "表名 (可选，默认值即为该表)"
    },
    "run": run,
    "invisible_context": True,
    "hooks": [],
}
