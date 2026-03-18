import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILLS_DIR = Path(__file__).parent.parent

# knowledge/tables 目录路径
KNOWLEDGE_DIR = Path(__file__).parent.parent.parent / "knowledge"
TABLES_DIR = KNOWLEDGE_DIR / "tables"


def run(
    table_name: str,
    project: str = "mi_ads_dmp",
    sample_rows: int = 5,
    sample_date: str = "20260314",
    generate_knowledge: bool = True,
) -> Dict[str, Any]:
    """
    探索新表的数据结构和业务含义

    参数:
        table_name: 表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)
        project: 项目名 (默认: mi_ads_dmp)
        sample_rows: 采样行数 (默认: 5)
        sample_date: 采样日期 (默认: 20260314)
        generate_knowledge: 是否自动生成知识文件到 knowledge/tables (默认: True)

    返回:
        包含表结构、字段信息、样本数据的字典
    """
    from gold_miner.odps_client import OdpsClient, OdpsConfig
    from gold_miner.config import Config
    from odps import ODPS

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

    # 存储字段注释信息
    column_comments = {}

    try:
        # 首先尝试使用 ODPS SDK get_table 获取表结构（包括字段注释）
        try:
            print(f"[explore_table] Getting table schema via ODPS SDK: {full_table_name}")
            o = ODPS(
                odps_config.access_id,
                odps_config.access_key,
                odps_config.project,
                endpoint=odps_config.endpoint
            )
            table_obj = o.get_table(full_table_name)

            # 获取分区信息
            for part in table_obj.table_schema.partitions:
                result["partitions"].append({
                    "name": part.name,
                    "type": str(part.type),
                })
            result["structure"]["total_partitions"] = len(result["partitions"])
            print(f"[explore_table] Found {len(result['partitions'])} partition columns via SDK")

            # 获取字段信息和注释
            for col in table_obj.table_schema.columns:
                col_name = col.name
                col_type = str(col.type)
                col_comment = col.comment if col.comment else ""
                column_comments[col_name] = {
                    "type": col_type,
                    "comment": col_comment,
                }
            print(f"[explore_table] Found {len(column_comments)} columns with comments via SDK")

        except Exception as e:
            print(f"[explore_table] ODPS SDK get_table failed: {e}")
            # 降级到 SHOW PARTITIONS
            try:
                partition_sql = f"SHOW PARTITIONS {full_table_name}"
                print(f"[explore_table] Executing SHOW PARTITIONS: {partition_sql}")
                partition_df = client.run_sql(partition_sql, enable_log=False)
                if not partition_df.empty:
                    first_partition = str(partition_df.iloc[0, 0])
                    if "=" in first_partition:
                        part_col = first_partition.split("=")[0]
                        result["partitions"].append({
                            "name": part_col,
                            "type": "string",
                        })
                        result["structure"]["total_partitions"] = len(partition_df)
                        print(f"[explore_table] Found partition column: {part_col}")
            except Exception as e2:
                print(f"[explore_table] SHOW PARTITIONS also failed: {e2}")

        # 使用样本查询获取样本数据
        partition_where = ""
        if result["partitions"]:
            part_col = result["partitions"][0]["name"]
            # 如果有 SDK 获取的分区信息，使用 sample_date
            partition_where = f"WHERE {part_col} = '{sample_date}'"

        sample_sql = f"SELECT * FROM {full_table_name} {partition_where} LIMIT {sample_rows}"
        print(f"[explore_table] Getting sample data: {sample_sql}")
        sample_df = client.run_sql(sample_sql, enable_log=False)

        if not sample_df.empty:
            # 从 DataFrame 和 SDK 获取的注释构建列信息
            for col_name in sample_df.columns:
                # 检查是否是分区列
                is_partition = any(p["name"] == col_name for p in result["partitions"])

                if is_partition:
                    continue  # 分区列已在上面处理

                # 获取列信息（优先使用 SDK 获取的信息）
                col_info = {
                    "name": col_name,
                    "type": "STRING",
                    "comment": "",
                }

                if col_name in column_comments:
                    col_info["type"] = column_comments[col_name]["type"]
                    col_info["comment"] = column_comments[col_name]["comment"]
                else:
                    # 从 DataFrame 推断类型
                    col_type = str(sample_df[col_name].dtype)
                    type_mapping = {
                        'int64': 'BIGINT',
                        'float64': 'DOUBLE',
                        'object': 'STRING',
                        'bool': 'BOOLEAN',
                        'datetime64[ns]': 'DATETIME',
                    }
                    col_info["type"] = type_mapping.get(col_type, 'STRING')

                # 添加样本值
                col_data = sample_df[col_name]
                col_info["sample"] = str(col_data.iloc[0])[:50] if not col_data.empty else ""
                result["columns"].append(col_info)

            result["structure"]["total_columns"] = len(result["columns"])

            # 保存样本数据
            result["sample_data"] = {
                "columns": list(sample_df.columns),
                "rows": sample_df.head(sample_rows).to_dict(orient="records"),
            }

            print(f"[explore_table] Found {len(result['columns'])} columns with {sum(1 for c in result['columns'] if c.get('comment'))} having comments")
        else:
            print(f"[explore_table] Sample query returned empty result")
            # 使用 SDK 获取的字段信息填充列信息
            if column_comments:
                print(f"[explore_table] Using SDK column info to populate columns")
                for col_name, col_info in column_comments.items():
                    # 检查是否是分区列
                    is_partition = any(p["name"] == col_name for p in result["partitions"])
                    if is_partition:
                        continue

                    result["columns"].append({
                        "name": col_name,
                        "type": col_info["type"],
                        "comment": col_info["comment"],
                        "sample": "",
                    })
                result["structure"]["total_columns"] = len(result["columns"])
                print(f"[explore_table] Populated {len(result['columns'])} columns from SDK")

    except Exception as e:
        result["error"] = f"获取表结构失败: {str(e)}"

    # 样本数据查询已经在上面执行过了，这里只需要保存结果
    # 如果需要更多行数，可以重新查询
    try:
        if result.get("sample_data") is None and result["columns"]:
            # 需要获取更多样本数据
            partition_where = ""
            if result["partitions"]:
                part_col = result["partitions"][0]["name"]
                partition_where = f"WHERE {part_col} = '{sample_date}'"

            sample_sql = f"SELECT * FROM {full_table_name} {partition_where} LIMIT {sample_rows}"
            print(f"[explore_table] Executing sample query: {sample_sql}")
            sample_df = client.run_sql(sample_sql, enable_log=False)

            if not sample_df.empty:
                result["sample_data"] = {
                    "columns": list(sample_df.columns),
                    "rows": sample_df.head(sample_rows).to_dict(orient="records"),
                }

                # 添加样本值到列信息
                for col in sample_df.columns:
                    if col not in [p["name"] for p in result["partitions"]]:
                        col_data = sample_df[col]
                        for c in result["columns"]:
                            if c["name"] == col:
                                c["sample"] = str(col_data.iloc[0])[:50] if not col_data.empty else ""
                                break

    except Exception as e:
        result["error"] = result.get("error", "") + f"\n采样失败: {str(e)}"

    result["business_notes"] = _generate_business_notes(result)

    if generate_knowledge:
        try:
            knowledge_result = _generate_knowledge_file(table_name, result)
            result["knowledge_generation"] = knowledge_result
        except Exception as e:
            result["knowledge_generation"] = {"success": False, "error": str(e)}

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


def _generate_knowledge_file(
    table_name: str,
    table_info: Dict[str, Any],
) -> Dict[str, Any]:
    """
    根据探索结果生成或更新 knowledge/tables YAML 文件

    参数:
        table_name: 表名
        table_info: 表信息 (来自 explore_table run 的结果)

    返回:
        生成结果
    """
    from datetime import datetime
    import yaml

    table_name_clean = table_name.replace(".", "_").replace("-", "_")
    knowledge_file = TABLES_DIR / f"{table_name_clean}.yaml"

    # 确保目录存在
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    full_table_name = table_info.get('table_name', table_name)
    project = table_info.get('project', 'mi_ads_dmp')
    total_columns = table_info.get('structure', {}).get('total_columns', 0)
    total_partitions = table_info.get('structure', {}).get('total_partitions', 0)

    # 从 ODPS 获取的字段信息（包含注释）
    odps_columns = {}
    for col in table_info.get("columns", []):
        odps_columns[col['name']] = {
            'type': col.get('type', 'UNKNOWN'),
            'comment': col.get('comment', ''),
            'sample': col.get('sample', ''),
        }

    # 如果文件已存在，读取并更新
    if knowledge_file.exists():
        try:
            with open(knowledge_file, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f) or {}

            # 更新基本信息
            existing_data['基本信息'] = existing_data.get('基本信息', {})
            existing_data['基本信息']['表名'] = full_table_name
            existing_data['基本信息']['项目'] = project
            existing_data['基本信息']['列数'] = total_columns
            existing_data['基本信息']['分区数'] = total_partitions

            # 更新或补充核心字段
            existing_fields = existing_data.get('核心字段详解', {})
            updated_fields = {}
            updated_count = 0
            added_count = 0

            for col_name, odps_info in odps_columns.items():
                if col_name in existing_fields:
                    # 更新现有字段
                    field_info = existing_fields[col_name]
                    # 如果业务含义为空，使用 ODPS 注释补充
                    if not field_info.get('业务含义') and odps_info['comment']:
                        field_info['业务含义'] = odps_info['comment']
                        updated_count += 1
                    # 更新数据类型
                    field_info['数据类型'] = odps_info['type']
                    # 更新示例值
                    if odps_info['sample'] and not field_info.get('示例值'):
                        field_info['示例值'] = [odps_info['sample']]
                    updated_fields[col_name] = field_info
                else:
                    # 添加新字段
                    updated_fields[col_name] = {
                        '字段名': col_name,
                        '数据类型': odps_info['type'],
                        '业务含义': odps_info['comment'],
                        '示例值': [odps_info['sample']] if odps_info['sample'] else [],
                        '使用注意': ''
                    }
                    added_count += 1

            existing_data['核心字段详解'] = updated_fields
            existing_data['更新时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 写入更新后的文件
            with open(knowledge_file, "w", encoding="utf-8") as f:
                yaml.dump(existing_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

            return {
                "success": True,
                "knowledge_file": str(knowledge_file),
                "message": f"知识文件已更新: {knowledge_file}",
                "details": {
                    "updated_comments": updated_count,
                    "added_fields": added_count,
                    "total_fields": len(updated_fields),
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"更新知识文件失败: {str(e)}",
            }

    # 文件不存在，创建新文件
    # 构建核心字段
    core_fields = {}
    for col_name, odps_info in odps_columns.items():
        core_fields[col_name] = {
            '字段名': col_name,
            '数据类型': odps_info['type'],
            '业务含义': odps_info['comment'],
            '示例值': [odps_info['sample']] if odps_info['sample'] else [],
            '使用注意': ''
        }

    # 构建分区信息
    partition_info = {}
    if table_info.get("partitions"):
        part = table_info["partitions"][0]
        partition_info = {
            '分区字段': part['name'],
            '分区类型': part['type'],
            '分区说明': '日期/小时分区'
        }

    # 解析业务备注
    business_notes = table_info.get("business_notes", [])
    id_fields = []
    label_fields = []
    metric_fields = []
    time_fields = []

    for note in business_notes:
        if note.startswith("ID字段:"):
            id_fields = [f.strip() for f in note.replace("ID字段:", "").split(",")]
        elif note.startswith("标签字段:"):
            label_fields = [f.strip() for f in note.replace("标签字段:", "").split(",")]
        elif note.startswith("计费/指标字段:"):
            metric_fields = [f.strip() for f in note.replace("计费/指标字段:", "").split(",")]
        elif note.startswith("时间字段:"):
            time_fields = [f.strip() for f in note.replace("时间字段:", "").split(",")]

    # 构建 YAML 结构
    knowledge_data = {
        '基本信息': {
            '表名': full_table_name,
            '业务名称': '',  # 待补充
            '数据粒度': '',  # 待补充
            '更新频率': '未知',
            '保留周期': '未知',
            '项目': project,
            '列数': total_columns,
            '分区数': total_partitions
        },
        '分区信息': partition_info,
        '核心字段详解': core_fields,
        '常用查询场景': {
            '示例查询': {
                '场景名称': '示例查询',
                'SQL模板': f"SELECT * FROM {full_table_name} WHERE dh = '{{{{dh}}}}' LIMIT 100",
                '参数': {
                    'dh': '分区值'
                }
            }
        },
        '数据质量规则': {
            '异常值识别': {}
        },
        '业务备注': {
            'ID字段': id_fields,
            '标签字段': label_fields,
            '计费字段': metric_fields,
            '时间字段': time_fields
        },
        '生成时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 写入 YAML 文件
    with open(knowledge_file, "w", encoding="utf-8") as f:
        yaml.dump(knowledge_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    return {
        "success": True,
        "knowledge_file": str(knowledge_file),
        "message": f"知识文件已生成到: {knowledge_file}",
        "details": {
            "added_fields": len(core_fields),
        }
    }


SKILL = {
    "name": "explore_table",
    "description": "探索新表的数据结构和业务含义，分析字段类型、分区、样本数据，并自动生成 knowledge/tables YAML 文件",
    "inputs": {
        "table_name": "表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)",
        "project": "项目名 (默认: mi_ads_dmp)",
        "sample_rows": "采样行数 (默认: 5)",
        "sample_date": "采样日期 (默认: 20260314)",
        "generate_knowledge": "是否自动生成知识文件到 knowledge/tables (默认: True)",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
