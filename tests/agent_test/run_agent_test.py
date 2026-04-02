"""
Agent 测试运行脚本 - 记录详细执行日志和数据分析结果
用于对比 main 分支和 refactor/harness-engineering 分支
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from gold_miner.agent import SqlAgent
from gold_miner.config import Config


@dataclass
class StepLog:
    """单步执行日志"""
    step_number: int
    action: str
    content: str
    timestamp: str
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class SQLExecutionLog:
    """SQL执行记录"""
    sql: str
    execution_time_ms: int
    row_count: int = 0
    column_count: int = 0
    preview_data: List[Dict] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class DataAnalysisResult:
    """数据分析结果"""
    query_summary: str = ""
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    data_preview: List[Dict] = field(default_factory=list)
    total_rows: int = 0
    columns: List[str] = field(default_factory=list)
    analysis_notes: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """测试结果"""
    question_id: str
    branch: str
    question: str
    category: str
    success: bool
    total_duration_ms: int
    step_count: int
    steps: List[Dict] = field(default_factory=list)
    final_output: str = ""
    final_report_content: str = ""
    sql_executions: List[SQLExecutionLog] = field(default_factory=list)
    total_sql_count: int = 0
    successful_sql_count: int = 0
    failed_sql_count: int = 0
    data_analysis: DataAnalysisResult = field(default_factory=DataAnalysisResult)
    error_message: str = ""
    error_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


TEST_QUESTIONS = [
    {
        "id": "Q001",
        "category": "simple",
        "question": "查询广告主2368昨天在com_cdm.dws_tracker_ad_cpc_cost_hi表中的总消耗",
        "description": "简单单表聚合查询",
        "expected_metrics": ["total_cost", "cost_usd"]
    },
    {
        "id": "Q002", 
        "category": "medium",
        "question": "分析广告主2368最近7天在com_cdm.dws_tracker_ad_cpc_cost_hi表中各广告组的CTR和CVR趋势",
        "description": "多维度分析",
        "expected_metrics": ["ctr", "cvr", "click_cnt", "show_cnt"]
    },
    {
        "id": "Q003",
        "category": "complex", 
        "question": "找出广告主2368过去15天在com_cdm.dws_tracker_ad_cpc_cost_hi表中消耗最高的前5个广告组，并分析它们的点击率和转化率",
        "description": "复杂分析",
        "expected_metrics": ["ad_group_id", "cost", "ctr", "cvr"]
    },
    {
        "id": "Q004",
        "category": "context",
        "question": "对比广告主2368上上周和上周在com_cdm.dws_tracker_ad_cpc_cost_hi表中的消耗数据",
        "description": "双周期对比",
        "expected_metrics": ["week_over_week", "cost_comparison"]
    },
    {
        "id": "Q005",
        "category": "error_recovery",
        "question": "统计广告主2368过去15天在com_cdm.dws_tracker_ad_cpc_cost_hi表中每天的分时消耗趋势，并找出消耗峰值时段",
        "description": "时间序列分析",
        "expected_metrics": ["hourly_trend", "peak_hour"]
    },
]


def create_test_config() -> Config:
    return Config.from_env()


def run_test(question_data: Dict, branch: str) -> TestResult:
    qid = question_data["id"]
    question = question_data["question"]
    category = question_data["category"]
    expected_metrics = question_data.get("expected_metrics", [])
    
    print(f"\n{'='*70}")
    print(f"[测试 {qid}] {question}")
    print(f"[分支] {branch}")
    print(f"{'='*70}")
    
    steps = []
    sql_executions = []
    analysis_notes = []
    start_time = time.time()
    success = False
    error_msg = ""
    error_type = ""
    step_counter = [0]
    last_df = None
    last_sql = None
    
    def status_callback(status):
        nonlocal last_df, last_sql
        step_num = step_counter[0]
        
        if isinstance(status, dict):
            action_type = status.get("type", "unknown")
            content = str(status.get("content", ""))[:1000]
            
            # 记录SQL执行
            if action_type == "action" and "执行 SQL:" in content:
                sql = content.split("执行 SQL:")[1].strip()[:500]
                last_sql = sql
                
            # 记录SQL结果
            if action_type == "sql_result":
                row_count = 0
                if "返回" in content and "行" in content:
                    try:
                        row_count = int(content.split("返回")[1].split("行")[0].strip())
                    except:
                        pass
                if last_sql:
                    sql_exec = SQLExecutionLog(
                        sql=last_sql,
                        execution_time_ms=0,
                        row_count=row_count
                    )
                    sql_executions.append(sql_exec)
                    last_sql = None
            
            # 记录错误
            if action_type == "error":
                if sql_executions:
                    sql_executions[-1].error = content[:500]
            
            # 记录笔记
            if action_type == "note":
                analysis_notes.append(content[:300])
            
            step = {
                "step_number": step_num,
                "action": action_type,
                "content": content[:500],
                "timestamp": datetime.now().isoformat(),
                "duration_ms": 0
            }
            steps.append(step)
            step_counter[0] += 1
            
            print(f"  → Step {step_num}: [{action_type}]")
            if len(content) > 100:
                print(f"    {content[:100]}...")
            else:
                print(f"    {content}")
                
        elif isinstance(status, str):
            step = {
                "step_number": step_num,
                "action": status,
                "content": status,
                "timestamp": datetime.now().isoformat(),
                "duration_ms": 0
            }
            steps.append(step)
            print(f"  → [{status}]")
    
    try:
        config = create_test_config()
        skills_dir = os.path.join(os.path.dirname(__file__), '../../skills')
        sessions_dir = os.path.join(os.path.dirname(__file__), '../../sessions')
        agent = SqlAgent(config, skills_dir=skills_dir, sessions_dir=sessions_dir)
        
        result = agent.run(
            question=question,
            status_cb=status_callback,
            max_steps=6,
            clear_memory=True
        )
        
        # 尝试读取最终报告
        final_report_content = ""
        if result and os.path.exists(result):
            try:
                with open(result, 'r', encoding='utf-8') as f:
                    final_report_content = f.read()[:2000]  # 只取前2000字符
            except:
                final_report_content = str(result)[:500]
        else:
            final_report_content = str(result)[:500] if result else ""
        
        success = True
        print(f"\n  ✓ 测试完成")
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        traceback_str = traceback.format_exc()
        print(f"\n  ✗ 测试失败: {error_msg}")
    
    total_duration = int((time.time() - start_time) * 1000)
    
    # 构建数据分析结果
    data_analysis = DataAnalysisResult(
        query_summary=f"测试问题: {question[:100]}",
        analysis_notes=analysis_notes[:10],
        total_rows=sum(s.row_count for s in sql_executions)
    )
    
    return TestResult(
        question_id=qid,
        branch=branch,
        question=question,
        category=category,
        success=success,
        total_duration_ms=total_duration,
        step_count=len(steps),
        steps=steps,
        final_output=result if success else "",
        final_report_content=final_report_content if success else "",
        sql_executions=sql_executions,
        total_sql_count=len(sql_executions),
        successful_sql_count=len([s for s in sql_executions if not s.error]),
        failed_sql_count=len([s for s in sql_executions if s.error]),
        data_analysis=data_analysis,
        error_message=error_msg,
        error_type=error_type,
        metadata={
            "description": question_data["description"],
            "expected_metrics": expected_metrics,
            "test_time": datetime.now().isoformat()
        }
    )


def main():
    branch = os.popen('git branch --show-current').read().strip()
    if not branch:
        branch = "unknown"
    
    print(f"\n{'#'*70}")
    print(f"# Agent 测试 - 分支: {branch}")
    print(f"# 时间: {datetime.now().isoformat()}")
    print(f"{'#'*70}")
    
    results = []
    for q in TEST_QUESTIONS:
        result = run_test(q, branch)
        results.append(asdict(result))
    
    output_dir = "../../test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_branch = branch.replace('/', '_')
    filename = f"{output_dir}/agent_test_{safe_branch}_{timestamp}.json"
    
    output_data = {
        "branch": branch,
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(TEST_QUESTIONS),
        "results": results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"测试完成！结果保存到: {filename}")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results if r["success"])
    total_duration = sum(r["total_duration_ms"] for r in results)
    total_sql = sum(r["total_sql_count"] for r in results)
    
    print(f"\n摘要:")
    print(f"  总测试数: {len(results)}")
    print(f"  成功: {success_count}")
    print(f"  失败: {len(results) - success_count}")
    print(f"  总耗时: {total_duration}ms")
    print(f"  平均耗时: {total_duration // len(results)}ms")
    print(f"  总SQL执行数: {total_sql}")


if __name__ == "__main__":
    main()
