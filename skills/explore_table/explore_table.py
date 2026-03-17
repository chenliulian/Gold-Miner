import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILLS_DIR = Path(__file__).parent.parent


def run(
    table_name: str,
    project: str = "mi_ads_dmp",
    sample_rows: int = 5,
    sample_date: str = "20260314",
    generate_skill: bool = True,
) -> Dict[str, Any]:
    """
    探索新表的数据结构和业务含义

    参数:
        table_name: 表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)
        project: 项目名 (默认: mi_ads_dmp)
        sample_rows: 采样行数 (默认: 5)
        sample_date: 采样日期 (默认: 20260314)
        generate_skill: 是否自动生成 Skill 文件 (默认: True)

    返回:
        包含表结构、字段信息、样本数据的字典
    """
    from gold_miner.odps_client import OdpsClient, OdpsConfig
    from gold_miner.config import Config

    config = Config.from_env()
    odps_config = OdpsConfig.from_config(config)
    client = OdpsClient(odps_config)

    full_table_name = table_name if "." in table_name else f"{project}.{table_name}"

    result = {
        "table_name": full_table_name,
        "project": project,
        "structure": {},
        "columns": [],
        "partitions": [],
        "sample_data": None,
        "business_notes": [],
    }

    try:
        table = client.odps.get_table(full_table_name)
        table_schema = table.table_schema
        
        for col in table_schema.columns:
            result["columns"].append({
                "name": col.name,
                "type": str(col.type),
            })
        
        for part in table_schema.partitions:
            result["partitions"].append({
                "name": part.name,
                "type": str(part.type),
            })
        
        result["structure"]["total_columns"] = len(result["columns"])
        result["structure"]["total_partitions"] = len(result["partitions"])
    except Exception as e:
        result["error"] = f"获取表结构失败: {str(e)}"

    try:
        partition_where = ""
        if result["partitions"]:
            part_col = result["partitions"][0]["name"]
            partition_where = f"WHERE {part_col} = '{sample_date}'"

        sample_sql = f"SELECT * FROM {full_table_name} {partition_where} LIMIT {sample_rows};"
        print(f"[explore_table] Executing sample query: {sample_sql}")
        sample_df = client.run_sql(sample_sql, enable_log=False)

        if not sample_df.empty:
            result["sample_data"] = {
                "columns": list(sample_df.columns),
                "rows": sample_df.head(sample_rows).to_dict(orient="records"),
            }

            for col in sample_df.columns:
                if col not in [p["name"] for p in result["partitions"]]:
                    col_data = sample_df[col]
                    result["columns"] = [
                        c | {"sample": str(col_data.iloc[0])[:50]} if c["name"] == col else c
                        for c in result["columns"]
                    ]

    except Exception as e:
        result["error"] = result.get("error", "") + f"\n采样失败: {str(e)}"

    result["business_notes"] = _generate_business_notes(result)

    if generate_skill:
        try:
            skill_result = _generate_skill_file(table_name, result)
            result["skill_generation"] = skill_result
        except Exception as e:
            result["skill_generation"] = {"success": False, "error": str(e)}

    return result


def _generate_business_notes(table_info: Dict) -> List[str]:
    notes = []

    if table_info.get("partitions"):
        parts = [f"{p['name']} ({p['type']})" for p in table_info["partitions"]]
        notes.append(f"分区字段: {', '.join(parts)}")

    id_fields = [c["name"] for c in table_info["columns"] if "_id" in c["name"].lower() or c["name"].lower() in ("id", "request_id")]
    if id_fields:
        notes.append(f"ID字段: {', '.join(id_fields)}")

    label_fields = [c["name"] for c in table_info["columns"] if "label" in c["name"].lower()]
    if label_fields:
        notes.append(f"标签字段: {', '.join(label_fields)}")

    price_fields = [c["name"] for c in table_info["columns"] if any(x in c["name"].lower() for x in ["price", "cost", "spend", "ecpm", "ctr", "cvr"])]
    if price_fields:
        notes.append(f"计费/指标字段: {', '.join(price_fields)}")

    date_fields = [c["name"] for c in table_info["columns"] if any(x in c["name"].lower() for x in ["date", "time", "ts", "dh", "dt"])]
    if date_fields:
        notes.append(f"时间字段: {', '.join(date_fields)}")

    return notes


def _generate_skill_file(
    table_name: str,
    table_info: Dict[str, Any],
    category: str = "maxcompute",
) -> Dict[str, Any]:
    """
    根据探索结果生成 Skill 文件

    参数:
        table_name: 表名
        table_info: 表信息 (来自 explore_table run 的结果)
        category: 技能分类 (默认: maxcompute)

    返回:
        生成结果
    """
    from datetime import datetime
    import json

    table_name_clean = table_name.replace(".", "_").replace("-", "_")

    skill_dir = SKILLS_DIR / category / f"table_{table_name_clean}"
    if skill_dir.exists():
        return {
            "success": False,
            "error": f"Skill 目录已存在: {skill_dir}",
        }

    skill_dir.mkdir(parents=True, exist_ok=True)

    columns_md = ""
    if table_info.get("columns"):
        for col in table_info["columns"][:30]:
            col_type = col.get("type", "unknown")
            col_sample = col.get("sample", "")
            columns_md += f"- **{col['name']}**: {col_type}"
            if col_sample:
                columns_md += f" (示例: {col_sample})"
            columns_md += "\n"

    partitions_md = ""
    if table_info.get("partitions"):
        for part in table_info["partitions"]:
            partitions_md += f"- **{part['name']}**: {part['type']}\n"

    business_notes_md = ""
    if table_info.get("business_notes"):
        business_notes_md = "\n".join(f"- {note}" for note in table_info["business_notes"])

    full_table_name = table_info.get('table_name', table_name)
    project = table_info.get('project', 'mi_ads_dmp')
    total_columns = table_info.get('structure', {}).get('total_columns', 0)
    total_partitions = table_info.get('structure', {}).get('total_partitions', 0)

    skill_md = f"""# {full_table_name} 表探索

## 概述
- **表名**: {full_table_name}
- **项目**: {project}
- **列数**: {total_columns}
- **分区数**: {total_partitions}

## 分区字段
{partitions_md or '无'}

## 字段说明
{columns_md or '无'}

## 业务备注
{business_notes_md or '无'}

## 使用示例
```sql
SELECT * FROM {full_table_name}
WHERE dh = '2026031400'
LIMIT 100;
```

## 生成时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    with open(skill_dir / "SKILL.md", "w", encoding="utf-8") as f:
        f.write(skill_md)

    skill_py = f'''
from typing import Any, Dict

def run(table_name: str = "{full_table_name}") -> Dict[str, Any]:
    """
    {full_table_name} 表的元信息

    更多信息请查看同目录下的 SKILL.md
    """
    return {{
        "table_name": "{full_table_name}",
        "project": "{project}",
        "columns_count": {total_columns},
        "partitions_count": {total_partitions},
    }}


SKILL = {{
    "name": "table_{table_name_clean}",
    "description": "{full_table_name} 表的元信息和字段说明",
    "inputs": {{
        "table_name": "表名 (可选，默认值即为该表)"
    }},
    "run": run,
    "invisible_context": True,
    "hooks": [],
}}
'''

    with open(skill_dir / "table_info.py", "w", encoding="utf-8") as f:
        f.write(skill_py)

    return {
        "success": True,
        "skill_dir": str(skill_dir),
        "message": f"Skill 已生成到: {skill_dir}",
    }


SKILL = {
    "name": "explore_table",
    "description": "探索新表的数据结构和业务含义，分析字段类型、分区、样本数据，并可自动生成 Skill 文件帮助后续理解",
    "inputs": {
        "table_name": "表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)",
        "project": "项目名 (默认: mi_ads_dmp)",
        "sample_rows": "采样行数 (默认: 5)",
        "sample_date": "采样日期 (默认: 20260314)",
        "generate_skill": "是否自动生成 Skill 文件 (默认: True)",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
