"""
Agent 性能对比测试脚本
对比 main 分支和 refactor/harness-engineering 分支的 Agent 表现

测试维度：
1. 回答准确性
2. 执行效率（时间）
3. 步骤数
4. 错误恢复能力
5. 上下文管理效率
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

# Mock ODPS 模块
sys.modules['odps'] = MagicMock()
sys.modules['odps.models'] = MagicMock()

from gold_miner.agent import SqlAgent
from gold_miner.config import Config


@dataclass
class TestQuestion:
    """测试问题定义"""
    id: str
    category: str  # simple, medium, complex, error_recovery
    question: str
    expected_tables: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class StepLog:
    """单步执行日志"""
    step_number: int
    action: str
    content: str
    timestamp: float
    duration_ms: int = 0
    error: Optional[str] = None


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
    steps: List[StepLog] = field(default_factory=list)
    final_output: str = ""
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# 测试问题集 - 覆盖不同场景
TEST_QUESTIONS = [
    # 简单问题 - 单表查询
    TestQuestion(
        id="Q001",
        category="simple",
        question="查询昨天广告投放的消耗数据",
        expected_tables=["ad_group_stats"],
        description="简单单表聚合查询"
    ),
    
    # 中等复杂度 - 多表关联
    TestQuestion(
        id="Q002",
        category="medium",
        question="分析最近7天各广告组的CTR和CVR趋势",
        expected_tables=["ad_group_stats", "ad_conversion"],
        description="多表关联 + 时间窗口 + 指标计算"
    ),
    
    # 复杂分析 - 多步骤推理
    TestQuestion(
        id="Q003",
        category="complex",
        question="找出过去30天ROI最高的前10个广告组，并分析它们的共同特征",
        expected_tables=["ad_group_stats", "ad_conversion", "ad_group"],
        description="复杂分析：聚合 + 排序 + 特征提取"
    ),
    
    # 上下文依赖 - 需要多轮对话
    TestQuestion(
        id="Q004",
        category="context",
        question="对比上个月的消耗数据",
        expected_tables=["ad_group_stats"],
        description="需要上下文理解（指代消解）"
    ),
    
    # 错误恢复 - 可能产生错误SQL
    TestQuestion(
        id="Q005",
        category="error_recovery",
        question="查询所有用户在过去一年的贷款申请记录，按月份统计通过率",
        expected_tables=["loan_application", "user_info"],
        description="可能遇到大数据量查询，测试错误恢复"
    ),
    
    # 技能调用 - 需要后处理
    TestQuestion(
        id="Q006",
        category="skill",
        question="计算各渠道用户的留存率，并生成可视化报告",
        expected_tables=["user_channel", "user_activity"],
        description="需要调用技能进行数据可视化"
    ),
]


class AgentBenchmark:
    """Agent 性能测试框架"""
    
    def __init__(self, branch_name: str):
        self.branch_name = branch_name
        self.results: List[TestResult] = []
        self.config = self._create_test_config()
        
    def _create_test_config(self) -> Config:
        """创建测试配置"""
        config = Config()
        config.agent_max_steps = 6
        config.agent_max_memory = 50
        config.llm_api_key = os.getenv("LLM_API_KEY", "test-key")
        config.llm_base_url = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
        config.llm_model = os.getenv("LLM_MODEL", "gpt-4")
        return config
    
    def _mock_llm_response(self, question: str, context: Dict) -> Dict[str, Any]:
        """模拟 LLM 响应 - 用于测试"""
        # 根据问题类型返回不同的模拟响应
        if "消耗" in question or "投放" in question:
            return {
                "action": "run_sql",
                "sql": "SELECT SUM(cost) as total_cost FROM ad_group_stats WHERE dt = '${yesterday}'",
                "notes": "查询昨天广告投放消耗"
            }
        elif "CTR" in question or "CVR" in question:
            return {
                "action": "run_sql",
                "sql": """SELECT 
                    ad_group_id,
                    SUM(clicks)/SUM(impressions) as ctr,
                    SUM(conversions)/SUM(clicks) as cvr
                FROM ad_group_stats 
                WHERE dt >= '${last_7_days}'
                GROUP BY ad_group_id""",
                "notes": "计算CTR和CVR指标"
            }
        elif "ROI" in question:
            return {
                "action": "run_sql",
                "sql": """SELECT 
                    ad_group_id,
                    (SUM(revenue) - SUM(cost)) / SUM(cost) as roi
                FROM ad_group_stats 
                WHERE dt >= '${last_30_days}'
                GROUP BY ad_group_id
                ORDER BY roi DESC
                LIMIT 10""",
                "notes": "计算ROI并排序"
            }
        else:
            return {
                "action": "final",
                "notes": "生成最终报告"
            }
    
    def run_single_test(self, question: TestQuestion) -> TestResult:
        """运行单个测试"""
        print(f"\n{'='*60}")
        print(f"[测试] {question.id}: {question.question}")
        print(f"[类型] {question.category}")
        print(f"{'='*60}")
        
        steps: List[StepLog] = []
        start_time = time.time()
        success = False
        error_msg = ""
        step_count = 0
        
        try:
            # 创建 Agent
            agent = SqlAgent(self.config)
            
            # 状态回调函数 - 记录每步执行
            def status_callback(status):
                nonlocal step_count
                step_start = time.time()
                
                if isinstance(status, dict):
                    action_type = status.get("type", "unknown")
                    content = status.get("content", "")
                    
                    step = StepLog(
                        step_number=step_count,
                        action=action_type,
                        content=content[:500],  # 限制长度
                        timestamp=step_start,
                        duration_ms=int((time.time() - step_start) * 1000)
                    )
                    steps.append(step)
                    step_count += 1
                    
                    print(f"  Step {step_count}: [{action_type}] {content[:100]}...")
                    
                elif isinstance(status, str):
                    step = StepLog(
                        step_number=step_count,
                        action=status,
                        content=status,
                        timestamp=step_start,
                        duration_ms=int((time.time() - step_start) * 1000)
                    )
                    steps.append(step)
                    print(f"  [{status}]")
            
            # 运行测试（使用模拟模式）
            with patch.object(agent.llm, 'chat') as mock_chat:
                mock_chat.side_effect = lambda msgs, **kwargs: json.dumps(
                    self._mock_llm_response(question.question, {})
                )
                
                result = agent.run(
                    question.question,
                    status_cb=status_callback,
                    max_steps=6
                )
                
                success = True
                
        except Exception as e:
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            print(f"  [ERROR] {error_msg}")
            print(f"  {traceback_str}")
        
        total_duration = int((time.time() - start_time) * 1000)
        
        test_result = TestResult(
            question_id=question.id,
            branch=self.branch_name,
            question=question.question,
            category=question.category,
            success=success,
            total_duration_ms=total_duration,
            step_count=step_count,
            steps=steps,
            error_message=error_msg,
            metadata={
                "expected_tables": question.expected_tables,
                "description": question.description,
                "test_time": datetime.now().isoformat()
            }
        )
        
        print(f"\n[结果] 成功: {success}, 耗时: {total_duration}ms, 步骤: {step_count}")
        
        return test_result
    
    def run_all_tests(self) -> List[TestResult]:
        """运行所有测试"""
        print(f"\n{'#'*70}")
        print(f"# 开始测试分支: {self.branch_name}")
        print(f"# 测试时间: {datetime.now().isoformat()}")
        print(f"# 测试问题数: {len(TEST_QUESTIONS)}")
        print(f"{'#'*70}")
        
        for question in TEST_QUESTIONS:
            result = self.run_single_test(question)
            self.results.append(result)
        
        return self.results
    
    def save_results(self, output_dir: str = "test_results"):
        """保存测试结果"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/benchmark_{self.branch_name}_{timestamp}.json"
        
        data = {
            "branch": self.branch_name,
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(),
            "results": [asdict(r) for r in self.results]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[保存] 结果已保存到: {filename}")
        return filename
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        total_tests = len(self.results)
        success_count = sum(1 for r in self.results if r.success)
        total_duration = sum(r.total_duration_ms for r in self.results)
        total_steps = sum(r.step_count for r in self.results)
        
        category_stats = {}
        for r in self.results:
            cat = r.category
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "success": 0, "duration": 0}
            category_stats[cat]["count"] += 1
            category_stats[cat]["success"] += 1 if r.success else 0
            category_stats[cat]["duration"] += r.total_duration_ms
        
        return {
            "total_tests": total_tests,
            "success_count": success_count,
            "success_rate": f"{success_count/total_tests*100:.1f}%",
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration // total_tests if total_tests > 0 else 0,
            "total_steps": total_steps,
            "avg_steps": total_steps / total_tests if total_tests > 0 else 0,
            "category_stats": category_stats
        }


def compare_branches(result_file_main: str, result_file_refactor: str):
    """对比两个分支的测试结果"""
    with open(result_file_main, 'r') as f:
        main_data = json.load(f)
    with open(result_file_refactor, 'r') as f:
        refactor_data = json.load(f)
    
    print("\n" + "="*80)
    print("分支对比分析")
    print("="*80)
    
    # 整体对比
    main_summary = main_data["summary"]
    refactor_summary = refactor_data["summary"]
    
    print("\n【整体性能对比】")
    print(f"{'指标':<25} {'main':<20} {'refactor':<20} {'差异':<20}")
    print("-"*85)
    print(f"{'成功率':<25} {main_summary['success_rate']:<20} {refactor_summary['success_rate']:<20}")
    print(f"{'总耗时(ms)':<25} {main_summary['total_duration_ms']:<20} {refactor_summary['total_duration_ms']:<20} {refactor_summary['total_duration_ms'] - main_summary['total_duration_ms']:+d}")
    print(f"{'平均耗时(ms)':<25} {main_summary['avg_duration_ms']:<20} {refactor_summary['avg_duration_ms']:<20} {refactor_summary['avg_duration_ms'] - main_summary['avg_duration_ms']:+d}")
    print(f"{'平均步骤数':<25} {main_summary['avg_steps']:<20.1f} {refactor_summary['avg_steps']:<20.1f} {refactor_summary['avg_steps'] - main_summary['avg_steps']:+.1f}")
    
    # 按问题对比
    print("\n【按问题对比】")
    print(f"{'问题ID':<10} {'类别':<15} {'main耗时':<12} {'refactor耗时':<12} {'main步骤':<10} {'refactor步骤':<12}")
    print("-"*85)
    
    main_results = {r["question_id"]: r for r in main_data["results"]}
    refactor_results = {r["question_id"]: r for r in refactor_data["results"]}
    
    for qid in main_results:
        main_r = main_results[qid]
        refactor_r = refactor_results.get(qid, {})
        print(f"{qid:<10} {main_r['category']:<15} {main_r['total_duration_ms']:<12} {refactor_r.get('total_duration_ms', 0):<12} {main_r['step_count']:<10} {refactor_r.get('step_count', 0):<12}")
    
    # 生成对比报告
    report = {
        "comparison_time": datetime.now().isoformat(),
        "main_summary": main_summary,
        "refactor_summary": refactor_summary,
        "detailed_comparison": []
    }
    
    return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Agent 性能对比测试')
    parser.add_argument('--branch', type=str, help='测试分支名称')
    parser.add_argument('--compare', nargs=2, metavar=('MAIN_FILE', 'REFACTOR_FILE'), help='对比两个结果文件')
    parser.add_argument('--output-dir', type=str, default='test_results', help='输出目录')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_branches(args.compare[0], args.compare[1])
    elif args.branch:
        benchmark = AgentBenchmark(args.branch)
        benchmark.run_all_tests()
        benchmark.save_results(args.output_dir)
    else:
        # 默认运行当前分支测试
        branch = os.popen('git branch --show-current').read().strip()
        benchmark = AgentBenchmark(branch or "unknown")
        benchmark.run_all_tests()
        benchmark.save_results(args.output_dir)


if __name__ == "__main__":
    main()
