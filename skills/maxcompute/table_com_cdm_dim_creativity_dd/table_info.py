
from typing import Any, Dict

def run(table_name: str = "com_cdm.dim_creativity_dd") -> Dict[str, Any]:
    """
    com_cdm.dim_creativity_dd 表的元信息

    更多信息请查看同目录下的 SKILL.md
    """
    return {
        "table_name": "com_cdm.dim_creativity_dd",
        "project": "com_cdm",
        "columns_count": 47,
        "partitions_count": 1,
    }


SKILL = {
    "name": "table_com_cdm_dim_creativity_dd",
    "description": "com_cdm.dim_creativity_dd 表的元信息和字段说明",
    "inputs": {
        "table_name": "表名 (可选，默认值即为该表)"
    },
    "run": run,
    "invisible_context": True,
    "hooks": [],
}
