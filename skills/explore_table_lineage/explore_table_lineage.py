"""
表血缘关系探索 Skill

通过 DataWorks 数据地图 API 获取 ODPS 表的血缘关系，
帮助理解数据业务结构和上游依赖
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def run(
    table_name: str,
    project: str = "mi_ads_dmp",
    direction: str = "UPSTREAM",
) -> Dict[str, Any]:
    """
    探索 ODPS 表的血缘关系

    参数:
        table_name: 表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)
        project: 项目名 (默认: mi_ads_dmp)
        direction: 查询方向 - UPSTREAM (上游), DOWNSTREAM (下游), BOTH

    返回:
        包含血缘关系的字典
    """
    from gold_miner.dataworks_client import DataWorksClient, DataWorksConfig

    # 解析表名
    if "." in table_name:
        parts = table_name.split(".")
        project = parts[0]
        table_name = parts[1]

    full_table_name = f"{project}.{table_name}"

    print(f"[explore_table_lineage] 探索表血缘: {full_table_name}")
    print(f"[explore_table_lineage] 方向: {direction}")

    try:
        # 初始化 DataWorks 客户端
        config = DataWorksConfig.from_env()
        config.validate()
        client = DataWorksClient(config)

        # 获取血缘关系
        lineage_result = client.get_table_lineage(
            table_name=table_name,
            project_name=project,
            direction=direction,
        )

        if not lineage_result.get("success"):
            error_msg = lineage_result.get("error", "Unknown error")
            print(f"[explore_table_lineage] 获取血缘关系失败: {error_msg}")
            return {
                "success": False,
                "table_name": full_table_name,
                "error": error_msg,
            }

        # 解析血缘数据
        parsed_lineage = client.parse_lineage_data(lineage_result)

        if not parsed_lineage.get("success"):
            return {
                "success": False,
                "table_name": full_table_name,
                "error": parsed_lineage.get("error", "解析失败"),
            }

        # 构建结果
        result = {
            "success": True,
            "table_name": full_table_name,
            "project": project,
            "direction": direction,
            "upstream_count": parsed_lineage.get("upstream_count", 0),
            "downstream_count": parsed_lineage.get("downstream_count", 0),
            "upstream_tables": parsed_lineage.get("upstream_tables", []),
            "downstream_tables": parsed_lineage.get("downstream_tables", []),
            "summary": _generate_summary(full_table_name, parsed_lineage),
        }

        print(f"[explore_table_lineage] 发现 {result['upstream_count']} 个上游表, {result['downstream_count']} 个下游表")

        return result

    except Exception as e:
        error_msg = str(e)
        print(f"[explore_table_lineage] 错误: {error_msg}")
        return {
            "success": False,
            "table_name": full_table_name,
            "error": error_msg,
        }


def _generate_summary(table_name: str, lineage_data: Dict[str, Any]) -> str:
    """生成血缘关系摘要"""
    upstream = lineage_data.get("upstream_tables", [])
    downstream = lineage_data.get("downstream_tables", [])

    lines = [f"## {table_name} 血缘关系分析", ""]

    # 上游表
    if upstream:
        lines.append(f"### 上游依赖表 ({len(upstream)}个)")
        lines.append("")
        for i, table in enumerate(upstream[:10], 1):  # 最多显示10个
            lines.append(f"{i}. **{table['project']}.{table['table_name']}**")
            if table.get("job_name"):
                lines.append(f"   - 生成任务: {table['job_name']}")
        if len(upstream) > 10:
            lines.append(f"   ... 还有 {len(upstream) - 10} 个上游表")
        lines.append("")
    else:
        lines.append("### 上游依赖表")
        lines.append("未找到上游依赖表（可能是数据源表）")
        lines.append("")

    # 下游表
    if downstream:
        lines.append(f"### 下游引用表 ({len(downstream)}个)")
        lines.append("")
        for i, table in enumerate(downstream[:10], 1):  # 最多显示10个
            lines.append(f"{i}. **{table['project']}.{table['table_name']}**")
            if table.get("job_name"):
                lines.append(f"   - 引用任务: {table['job_name']}")
        if len(downstream) > 10:
            lines.append(f"   ... 还有 {len(downstream) - 10} 个下游表")
        lines.append("")
    else:
        lines.append("### 下游引用表")
        lines.append("未找到下游引用表（可能是最终报表）")
        lines.append("")

    return "\n".join(lines)


SKILL = {
    "name": "explore_table_lineage",
    "description": "探索 ODPS 表的血缘关系，通过 DataWorks 数据地图 API 获取上游依赖表和下游引用表，帮助理解数据业务结构",
    "inputs": {
        "table_name": "表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)",
        "project": "项目名 (默认: mi_ads_dmp)",
        "direction": "查询方向 - UPSTREAM (上游), DOWNSTREAM (下游), BOTH (默认: UPSTREAM)",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
