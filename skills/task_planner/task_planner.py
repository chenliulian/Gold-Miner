"""
业务数据洞察分析任务规划器

专门用于拆解复杂的业务数据分析需求，生成可执行的任务计划，
并跟踪任务执行状态，支持多步骤数据洞察分析工作流。
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

# 任务状态
class TaskStatus(Enum):
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 已跳过


class Task:
    """单个分析任务"""
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        task_type: str,
        depends_on: List[str] = None,
        parameters: Dict[str, Any] = None,
        expected_output: str = "",
    ):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.task_type = task_type  # sql, analysis, visualization, report
        self.depends_on = depends_on or []
        self.parameters = parameters or {}
        self.expected_output = expected_output
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error_message: str = ""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.execution_logs: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "depends_on": self.depends_on,
            "parameters": self.parameters,
            "expected_output": self.expected_output,
            "status": self.status.value,
            "result": self.result,
            "error_message": self.error_message,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_logs": self.execution_logs,
        }


class AnalysisPlan:
    """分析计划"""
    def __init__(
        self,
        plan_id: str,
        title: str,
        business_goal: str,
        tables_involved: List[str],
        tasks: List[Task],
        created_at: datetime = None,
    ):
        self.plan_id = plan_id
        self.title = title
        self.business_goal = business_goal
        self.tables_involved = tables_involved
        self.tasks = {t.task_id: t for t in tasks}
        self.created_at = created_at or datetime.now()
        self.updated_at = self.created_at
        self.overall_status = TaskStatus.PENDING
        self.summary_report: str = ""

    def get_execution_order(self) -> List[str]:
        """获取任务执行顺序（拓扑排序）"""
        visited = set()
        order = []
        temp_mark = set()

        def visit(task_id: str):
            if task_id in temp_mark:
                raise ValueError(f"任务依赖存在循环: {task_id}")
            if task_id in visited:
                return
            temp_mark.add(task_id)
            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.depends_on:
                    visit(dep_id)
            temp_mark.remove(task_id)
            visited.add(task_id)
            order.append(task_id)

        for task_id in self.tasks:
            if task_id not in visited:
                visit(task_id)

        return order

    def get_ready_tasks(self) -> List[Task]:
        """获取当前可以执行的任务（依赖已完成）"""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            # 检查所有依赖是否已完成
            deps_satisfied = all(
                self.tasks.get(dep_id, Task("", "", "", "")).status == TaskStatus.COMPLETED
                for dep_id in task.depends_on
            )
            if deps_satisfied:
                ready.append(task)
        return ready

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "business_goal": self.business_goal,
            "tables_involved": self.tables_involved,
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "overall_status": self.overall_status.value,
            "summary_report": self.summary_report,
        }


def run(
    business_question: str,
    tables: List[str] = None,
    analysis_depth: str = "standard",  # quick, standard, deep
    output_format: str = "markdown",   # markdown, json, html
    save_plan: bool = True,
) -> Dict[str, Any]:
    """
    创建业务数据洞察分析任务计划

    参数:
        business_question: 业务问题/分析目标
        tables: 涉及的表名列表
        analysis_depth: 分析深度 (quick-快速, standard-标准, deep-深度)
        output_format: 输出格式
        save_plan: 是否保存计划到文件

    返回:
        包含分析计划的任务列表和元信息
    """
    plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    # 根据业务问题类型自动识别分析模式
    analysis_pattern = _identify_analysis_pattern(business_question)

    # 根据分析深度确定任务数量
    task_templates = _get_task_templates(analysis_pattern, analysis_depth)

    # 构建任务列表
    tasks = []
    for i, template in enumerate(task_templates):
        task = Task(
            task_id=f"task_{i+1:03d}",
            name=template["name"],
            description=template["description"],
            task_type=template["task_type"],
            depends_on=template.get("depends_on", []),
            parameters=_fill_parameters(template.get("parameters", {}), business_question, tables),
            expected_output=template.get("expected_output", ""),
        )
        tasks.append(task)

    # 创建分析计划
    plan = AnalysisPlan(
        plan_id=plan_id,
        title=f"分析: {business_question[:50]}...",
        business_goal=business_question,
        tables_involved=tables or [],
        tasks=tasks,
    )

    # 生成执行计划文档
    plan_document = _generate_plan_document(plan, output_format)

    # 保存计划
    plan_file = None
    if save_plan:
        plan_file = _save_plan(plan, output_format)

    return {
        "success": True,
        "plan_id": plan_id,
        "business_goal": business_question,
        "analysis_pattern": analysis_pattern,
        "analysis_depth": analysis_depth,
        "total_tasks": len(tasks),
        "execution_order": plan.get_execution_order(),
        "tasks": [t.to_dict() for t in tasks],
        "plan_document": plan_document,
        "plan_file": plan_file,
        "message": f"分析计划已创建，共 {len(tasks)} 个任务，执行顺序: {' -> '.join(plan.get_execution_order())}",
    }


def execute_plan(
    plan_id: str,
    plan_data: Dict[str, Any] = None,
    execute_callback: Callable[[Task], Any] = None,
    stop_on_error: bool = True,
) -> Dict[str, Any]:
    """
    执行分析计划

    参数:
        plan_id: 计划ID
        plan_data: 计划数据（如果已加载）
        execute_callback: 任务执行回调函数
        stop_on_error: 出错时是否停止

    返回:
        执行结果
    """
    # 这里简化实现，实际应该加载 plan 并执行
    return {
        "success": True,
        "plan_id": plan_id,
        "message": "计划执行功能需要通过 Agent 集成实现",
        "note": "在实际使用中，Agent 会读取任务计划并逐个执行",
    }


def _identify_analysis_pattern(question: str) -> str:
    """识别分析模式"""
    question_lower = question.lower()

    patterns = {
        "trend_analysis": ["趋势", "变化", "走势", "增长", "下降", "同比", "环比"],
        "comparison_analysis": ["对比", "比较", "差异", "vs", "versus", "差距"],
        "root_cause_analysis": ["原因", "为什么", "归因", "根因", "下降原因", "异常"],
        "segmentation_analysis": ["分层", "分群", "细分", "画像", "特征", "群体"],
        "correlation_analysis": ["相关", "关系", "影响", "关联", "因果"],
        "prediction_analysis": ["预测", "预估", "未来", "将会", "趋势预测"],
        "funnel_analysis": ["漏斗", "转化", "流失", "步骤", "流程"],
        "cohort_analysis": ["留存", "cohort", "同期群", "生命周期"],
    }

    scores = {pattern: 0 for pattern in patterns}
    for pattern, keywords in patterns.items():
        for keyword in keywords:
            if keyword in question_lower:
                scores[pattern] += 1

    best_pattern = max(scores, key=scores.get)
    return best_pattern if scores[best_pattern] > 0 else "general_analysis"


def _get_task_templates(pattern: str, depth: str) -> List[Dict[str, Any]]:
    """获取任务模板"""

    # 基础任务：数据探查
    base_tasks = [
        {
            "name": "数据概览探查",
            "description": "了解数据规模、时间范围、关键字段分布",
            "task_type": "sql",
            "parameters": {
                "sql_template": "overview",
                "metrics": ["row_count", "date_range", "distinct_counts"],
            },
            "expected_output": "数据概览统计报告",
        },
    ]

    # 根据分析模式添加特定任务
    pattern_tasks = {
        "trend_analysis": [
            {
                "name": "时间序列分析",
                "description": "按时间维度统计核心指标趋势",
                "task_type": "sql",
                "depends_on": ["task_001"],
                "parameters": {"sql_template": "time_series", "granularity": "daily"},
                "expected_output": "时间序列数据",
            },
            {
                "name": "趋势可视化",
                "description": "生成趋势图表",
                "task_type": "visualization",
                "depends_on": ["task_002"],
                "parameters": {"chart_type": "line", "metrics": []},
                "expected_output": "趋势图表",
            },
        ],
        "comparison_analysis": [
            {
                "name": "分组对比分析",
                "description": "按维度分组对比核心指标",
                "task_type": "sql",
                "depends_on": ["task_001"],
                "parameters": {"sql_template": "group_comparison"},
                "expected_output": "分组对比数据",
            },
            {
                "name": "差异显著性检验",
                "description": "统计检验差异是否显著",
                "task_type": "analysis",
                "depends_on": ["task_002"],
                "parameters": {"test_type": "t_test"},
                "expected_output": "统计检验结果",
            },
        ],
        "root_cause_analysis": [
            {
                "name": "维度下钻分析",
                "description": "按多维度拆解指标变化",
                "task_type": "sql",
                "depends_on": ["task_001"],
                "parameters": {"sql_template": "dimension_drilldown"},
                "expected_output": "维度拆解数据",
            },
            {
                "name": "贡献度计算",
                "description": "计算各维度对变化的贡献度",
                "task_type": "analysis",
                "depends_on": ["task_002"],
                "parameters": {"method": "contribution_analysis"},
                "expected_output": "贡献度分析结果",
            },
        ],
        "funnel_analysis": [
            {
                "name": "漏斗步骤统计",
                "description": "统计各步骤转化数据",
                "task_type": "sql",
                "depends_on": ["task_001"],
                "parameters": {"sql_template": "funnel_steps"},
                "expected_output": "漏斗步骤数据",
            },
            {
                "name": "流失点识别",
                "description": "识别主要流失环节",
                "task_type": "analysis",
                "depends_on": ["task_002"],
                "parameters": {"method": "funnel_analysis"},
                "expected_output": "流失点分析报告",
            },
        ],
        "general_analysis": [
            {
                "name": "核心指标统计",
                "description": "计算核心指标的统计分布",
                "task_type": "sql",
                "depends_on": ["task_001"],
                "parameters": {"sql_template": "metrics_summary"},
                "expected_output": "指标统计数据",
            },
        ],
    }

    # 根据深度添加任务
    depth_tasks = {
        "quick": [],
        "standard": [
            {
                "name": "数据质量检查",
                "description": "检查数据完整性、异常值",
                "task_type": "sql",
                "depends_on": ["task_001"],
                "parameters": {"sql_template": "data_quality"},
                "expected_output": "数据质量报告",
            },
        ],
        "deep": [
            {
                "name": "数据质量检查",
                "description": "检查数据完整性、异常值",
                "task_type": "sql",
                "depends_on": ["task_001"],
                "parameters": {"sql_template": "data_quality"},
                "expected_output": "数据质量报告",
            },
            {
                "name": "深度特征分析",
                "description": "分析关键特征的分布和相关性",
                "task_type": "analysis",
                "parameters": {"method": "feature_analysis"},
                "expected_output": "特征分析报告",
            },
            {
                "name": "生成综合分析报告",
                "description": "汇总所有分析结果生成最终报告",
                "task_type": "report",
                "parameters": {"report_type": "comprehensive"},
                "expected_output": "综合分析报告",
            },
        ],
    }

    # 组合任务
    tasks = base_tasks + pattern_tasks.get(pattern, pattern_tasks["general_analysis"])

    # 更新依赖关系
    if len(tasks) > 1:
        for i, task in enumerate(tasks[1:], start=2):
            task["depends_on"] = [f"task_{i-1:03d}"]

    # 添加深度任务
    deep_task_list = depth_tasks.get(depth, [])
    for task in deep_task_list:
        task["depends_on"] = [f"task_{len(tasks):03d}"]
        tasks.append(task)

    return tasks


def _fill_parameters(params: Dict[str, Any], question: str, tables: List[str]) -> Dict[str, Any]:
    """填充参数"""
    filled = params.copy()
    filled["business_question"] = question
    filled["tables"] = tables or []
    return filled


def _generate_plan_document(plan: AnalysisPlan, format: str) -> str:
    """生成计划文档"""
    if format == "markdown":
        return _generate_markdown_plan(plan)
    elif format == "json":
        return json.dumps(plan.to_dict(), indent=2, ensure_ascii=False)
    else:
        return _generate_markdown_plan(plan)


def _generate_markdown_plan(plan: AnalysisPlan) -> str:
    """生成 Markdown 格式的计划文档"""
    md = f"""# {plan.title}

## 分析目标
{plan.business_goal}

## 涉及数据表
"""
    for table in plan.tables_involved:
        md += f"- {table}\n"

    md += f"""
## 执行计划

**计划ID**: {plan.plan_id}
**创建时间**: {plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**任务总数**: {len(plan.tasks)}

### 任务列表

"""

    execution_order = plan.get_execution_order()
    for i, task_id in enumerate(execution_order, 1):
        task = plan.tasks[task_id]
        md += f"""#### {i}. {task.name} (`{task.task_id}`)

- **类型**: {task.task_type}
- **描述**: {task.description}
- **依赖**: {', '.join(task.depends_on) if task.depends_on else '无'}
- **预期输出**: {task.expected_output}
- **参数**:
"""
        for key, value in task.parameters.items():
            md += f"  - {key}: {value}\n"
        md += "\n"

    md += """## 执行说明

1. 任务按上述顺序依次执行
2. 有依赖的任务需等待前置任务完成
3. 每个任务完成后会更新状态和结果
4. 最终生成综合分析报告

## 状态跟踪

| 任务ID | 任务名称 | 状态 | 结果摘要 |
|--------|----------|------|----------|
"""
    for task_id in execution_order:
        task = plan.tasks[task_id]
        md += f"| {task.task_id} | {task.name} | {task.status.value} | - |\n"

    return md


def _save_plan(plan: AnalysisPlan, format: str) -> str:
    """保存计划到文件"""
    plans_dir = Path(__file__).parent.parent.parent / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    if format == "json":
        file_path = plans_dir / f"{plan.plan_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)
    else:
        file_path = plans_dir / f"{plan.plan_id}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(_generate_markdown_plan(plan))

    return str(file_path)


# Skill 定义
SKILL = {
    "name": "task_planner",
    "description": "业务数据洞察分析任务规划器 - 自动拆解复杂分析需求为可执行的任务计划",
    "inputs": {
        "business_question": "业务问题/分析目标（必填）",
        "tables": "涉及的表名列表（可选）",
        "analysis_depth": "分析深度: quick(快速), standard(标准), deep(深度) - 默认 standard",
        "output_format": "输出格式: markdown, json - 默认 markdown",
        "save_plan": "是否保存计划到文件 - 默认 True",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
