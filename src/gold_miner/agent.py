from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from tabulate import tabulate

from .auto_improvement import get_auto_improvement_manager
from .business_knowledge import get_knowledge_manager
from .config import Config
from .llm import AnthropicClient, OpenAICompatibleClient
from .llm_provider import get_provider_manager
from .memory import MemoryStore
from .odps_client import OdpsClient, OdpsConfig
from .prompts import (
    FINAL_REPORT_PROMPT,
    MEMORY_EXTRACT_PROMPT,
    MEMORY_SUMMARY_PROMPT,
    SYSTEM_PROMPT,
)
from .report import write_report
from .security import SQLValidator, ValidationResult, create_default_validator
from .session import SessionStore
from .skills import SkillRegistry


# 上下文长度管理常量
# Claude 3.5 Sonnet 上下文窗口约 200K tokens
# 按 1 token ≈ 4 字符估算，约 800K 字符
MAX_CONTEXT_CHARS = 200000 * 4  # 800K 字符
# 为输出预留空间
OUTPUT_RESERVE_CHARS = 4096 * 4  # 约 16K 字符
# 可用于输入的最大字符数
MAX_INPUT_CHARS = MAX_CONTEXT_CHARS - OUTPUT_RESERVE_CHARS  # 约 784K 字符


def estimate_tokens(text: str) -> int:
    """估算文本的token数量
    
    使用粗略估算：1 token ≈ 4 个字符（适用于中英文混合）
    """
    return len(text) // 4


def truncate_steps_by_chars(steps: List[Dict], max_chars: int) -> List[Dict]:
    """根据字符数限制截断步骤列表，保留最近的步骤
    
    Args:
        steps: 步骤列表
        max_chars: 最大允许的字符数
        
    Returns:
        截断后的步骤列表
    """
    if not steps:
        return []
    
    # 从最近的步骤开始累加，直到达到字符限制
    selected_steps = []
    current_chars = 0
    
    # 反向遍历，优先保留最近的步骤
    for step in reversed(steps):
        step_text = json.dumps(step, ensure_ascii=False)
        step_chars = len(step_text)
        
        if current_chars + step_chars > max_chars and selected_steps:
            # 如果添加这个步骤会超出限制，且已经有选中步骤，则停止
            break
        
        selected_steps.insert(0, step)
        current_chars += step_chars
    
    return selected_steps


@dataclass
class QueryResult:
    sql: str
    preview: str
    rows: int
    columns: List[str]


# 类变量：跨会话跟踪 self_improvement 调用，防止重复记录
# 注意：这些变量在 dataclass 外部定义，作为真正的类变量
_recent_self_improvements: List[Dict[str, Any]] = []
_SELF_IMPROVEMENT_COOLDOWN: int = 300  # 5分钟冷却时间
_MAX_RECENT_SELF_IMPROVEMENTS: int = 20


@dataclass
class AgentState:
    results: List[QueryResult] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    last_df: Optional[pd.DataFrame] = None
    last_sql: Optional[str] = None
    last_error: Optional[str] = None
    executed_sqls: List[Dict[str, Any]] = field(default_factory=list)  # 记录所有执行的SQL

    # Memory limits
    MAX_RESULTS: int = field(default=100, repr=False)
    MAX_NOTES: int = field(default=500, repr=False)
    MAX_EXECUTED_SQLS: int = field(default=50, repr=False)

    def add_result(self, result: QueryResult) -> None:
        """Add a result with size limit."""
        self.results.append(result)
        if len(self.results) > self.MAX_RESULTS:
            # Keep most recent results
            self.results = self.results[-self.MAX_RESULTS:]

    def add_note(self, note: str) -> None:
        """Add a note with size limit."""
        self.notes.append(note)
        if len(self.notes) > self.MAX_NOTES:
            self.notes = self.notes[-self.MAX_NOTES:]

    def add_executed_sql(self, sql_info: Dict[str, Any]) -> None:
        """Add executed SQL with size limit."""
        self.executed_sqls.append(sql_info)
        if len(self.executed_sqls) > self.MAX_EXECUTED_SQLS:
            self.executed_sqls = self.executed_sqls[-self.MAX_EXECUTED_SQLS:]

    def is_self_improvement_recently_called(self, skill_args: Dict[str, Any]) -> bool:
        """检查 self_improvement 是否最近已经调用过（基于内容相似度）
        
        使用全局变量 _recent_self_improvements 来跨会话跟踪调用记录，
        防止每次用户发送消息都重复记录相同的反馈。
        """
        global _recent_self_improvements, _SELF_IMPROVEMENT_COOLDOWN
        
        if not _recent_self_improvements:
            return False

        new_summary = skill_args.get("summary", "")
        new_details = skill_args.get("details", "")
        
        for call in _recent_self_improvements:
            call_time = call.get("timestamp", 0)
            elapsed = time.time() - call_time

            # 如果在冷却时间内，认为是重复调用
            if elapsed < _SELF_IMPROVEMENT_COOLDOWN:
                existing_summary = call.get("args", {}).get("summary", "")
                existing_details = call.get("args", {}).get("details", "")

                # 如果summary或details内容相似，认为是重复调用
                if existing_summary and new_summary:
                    # 检查summary是否包含相同的关键词（简化匹配）
                    if self._is_similar_content(existing_summary, new_summary):
                        return True
                if existing_details and new_details:
                    if self._is_similar_content(existing_details, new_details):
                        return True

        return False

    def _is_similar_content(self, content1: str, content2: str) -> bool:
        """检查两段内容是否相似（改进版 - 基于核心关键词）"""
        import re

        def extract_keywords(s: str) -> set:
            """提取中文和英文关键词"""
            # 转换为小写
            s = s.lower()
            # 提取中文词汇（2-10个字符）
            chinese_words = set(re.findall(r'[\u4e00-\u9fa5]{2,10}', s))
            # 提取英文单词（3个字符以上）
            english_words = set(re.findall(r'[a-z]{3,}', s))
            # 提取数字（可能是ID或关键数值）
            numbers = set(re.findall(r'\d+', s))
            return chinese_words | english_words | numbers

        keywords1 = extract_keywords(content1)
        keywords2 = extract_keywords(content2)

        if not keywords1 or not keywords2:
            return False

        # 计算关键词交集比例
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        if not union:
            return False

        similarity = len(intersection) / len(union)

        # 如果相似度超过60%，认为是相似内容
        # 或者如果核心关键词（表名、字段名等）完全匹配
        return similarity > 0.6 or len(intersection) >= 3

    def record_self_improvement_call(self, skill_args: Dict[str, Any]) -> None:
        """记录 self_improvement 调用到全局变量"""
        global _recent_self_improvements, _MAX_RECENT_SELF_IMPROVEMENTS
        
        _recent_self_improvements.append({
            "args": skill_args,
            "timestamp": time.time()
        })
        # 限制历史记录数量
        if len(_recent_self_improvements) > _MAX_RECENT_SELF_IMPROVEMENTS:
            _recent_self_improvements[:] = _recent_self_improvements[-_MAX_RECENT_SELF_IMPROVEMENTS:]

    def is_skill_recently_called(self, skill_name: str, skill_args: Dict[str, Any], window: int = 3) -> bool:
        """检查skill是否在最近window次调用中已经调用过（基于内容相似度）"""
        # 对于 self_improvement，使用专门的跨会话跟踪
        if skill_name == "self_improvement":
            return self.is_self_improvement_recently_called(skill_args)
        
        # 其他skill不使用此机制（因为没有recent_skills实例变量了）
        return False


class SqlAgent:
    def __init__(
        self,
        config: Config,
        skills_dir: str,
        sessions_dir: Optional[str] = None,
        sql_validator: Optional[SQLValidator] = None,
        user_id: str = "",
    ):
        self.config = config
        self.user_id = user_id  # 当前用户ID
        # 使用新的 Provider Manager 支持多 LLM 故障转移
        self.llm_provider = get_provider_manager()
        self.odps = OdpsClient(
            OdpsConfig(
                access_id=config.odps_access_id,
                access_key=config.odps_access_key,
                project=config.odps_project,
                endpoint=config.odps_endpoint,
            )
        )
        # 长期记忆 - 只保存用户明确要求记住的内容（按用户隔离）
        self.memory = MemoryStore(config.memory_path, user_id=user_id)
        # 会话历史 - 保存每次对话的完整记录
        sessions_dir = sessions_dir or os.path.join(os.path.dirname(config.memory_path), "../sessions")
        self.session = SessionStore(sessions_dir, user_id=user_id)  # 传递用户ID
        self.skills = SkillRegistry(skills_dir)
        self.skills.load()
        self.knowledge = get_knowledge_manager()  # 业务知识管理器
        self.state = AgentState()
        self._cancel_event: Optional[Any] = None
        # SQL验证器 - 防止SQL注入
        self.sql_validator = sql_validator or create_default_validator()

    def start_new_session(self, title: str = "") -> str:
        """开始一个新的对话会话"""
        return self.session.start_session(title)

    def interrupt(self) -> None:
        """中断当前 Agent 的执行"""
        if self._cancel_event is not None:
            self._cancel_event.set()

    def cancel(self) -> None:
        """取消当前 Agent 的执行（interrupt 的别名）"""
        self.interrupt()

    def run(
        self,
        question: str,
        tables: Optional[str] = None,
        max_steps: Optional[int] = None,
        output_path: Optional[str] = None,
        cancel_event: Optional[Any] = None,
        status_cb: Optional[Any] = None,
        heartbeat_cb: Optional[Any] = None,
        clear_memory: bool = True,
    ) -> str:
        max_steps = max_steps or self.config.agent_max_steps
        if status_cb:
            status_cb("starting")

        # Reset agent state for new run
        self.state = AgentState()
        self._cancel_event = cancel_event

        # 设置会话状态为运行中
        self.session.set_result_status("running")

        # 检查用户是否要求记住什么
        should_remember = self.memory.should_remember(question)
        
        step_count = 0
        for step in range(max_steps):
            step_count += 1

            if heartbeat_cb and step_count % 3 == 0:
                heartbeat_cb({
                    "step": step_count,
                    "max_steps": max_steps,
                    "progress": f"{step_count}/{max_steps}",
                })

            if cancel_event is not None and cancel_event.is_set():
                if status_cb:
                    status_cb("cancelled")
                return ""

            try:
                action = self._next_action(question, tables)
            except Exception as e:
                # LLM调用失败（如超时），如果有已执行的结果，则返回已有结果
                error_msg = str(e)
                print(f"\n[Agent] LLM调用失败: {error_msg}")
                if status_cb:
                    status_cb({"type": "error", "content": f"LLM调用失败: {error_msg}"})

                # 如果有已执行的结果，基于已有结果生成报告
                if self.state.results:
                    print("[Agent] 基于已获取的结果生成报告...")
                    if status_cb:
                        status_cb("finalizing")
                    report = self._generate_report_from_results(question)
                    # 保存最终结果到会话
                    self.session.set_final_result(report, status="completed")
                    report_path = self._finalize(report, output_path, question)
                    if status_cb:
                        status_cb("done")
                    return report_path
                else:
                    # 没有结果，记录错误状态
                    self.session.set_final_result(f"Error: {error_msg}", status="failed")
                    # 没有结果，返回错误
                    raise
            note = action.get("notes")
            if note:
                print(f"\n[Agent] {note}")
                if status_cb:
                    status_cb({"type": "note", "content": note})
            # 打印QL分析中间结果（完整action内容）
            print(f"[Agent] Action: {json.dumps(action, ensure_ascii=False, indent=2)}")
            if action["action"] == "run_sql":
                if status_cb:
                    status_cb({"type": "action", "content": f"执行 SQL: {action.get('sql', '')[:200]}..."})
                try:
                    self._handle_sql(action["sql"])
                except InterruptedError:
                    if status_cb:
                        status_cb("cancelled")
                    return ""
                if status_cb:
                    if self.state.last_error:
                        status_cb({"type": "error", "content": self.state.last_error})
                    else:
                        status_cb({"type": "sql_result", "content": f"SQL 执行完成，返回 {len(self.state.last_df) if self.state.last_df is not None else 0} 行"})
                if self.state.last_error:
                    continue
            elif action["action"] == "use_skill":
                skill_name = action["skill"]
                print(f"\n[Agent] Using skill: {skill_name}")
                if status_cb:
                    status_cb({"type": "action", "content": f"调用技能: {skill_name}"})
                self._handle_skill(skill_name, action.get("skill_args", {}))
                if status_cb:
                    if self.state.last_error:
                        status_cb({"type": "error", "content": self.state.last_error})
                    else:
                        status_cb({"type": "skill_result", "content": f"技能 {skill_name} 执行完成"})
                if self.state.last_error:
                    continue
            elif action["action"] == "search_skills":
                keywords = action.get("search_keywords", "")
                print(f"\n[Agent] Searching skills for: {keywords}")
                if status_cb:
                    status_cb({"type": "action", "content": f"搜索技能: {keywords}"})
                self._handle_search_skills(keywords)
                if status_cb:
                    status_cb({"type": "skill_result", "content": f"技能搜索完成"})
            elif action["action"] == "summary":
                if status_cb:
                    status_cb({"type": "action", "content": "生成分析报告..."})
                report_markdown = action.get("report_markdown", "")
                if report_markdown:
                    # Store the draft report in state for review
                    self.state.draft_report = report_markdown
                    print(f"\n[Agent] Summary report generated, awaiting review")
                    # 不将草稿报告添加到会话步骤，避免前端显示
                    # 只通过 status_cb 通知前端报告已生成
                    if status_cb:
                        status_cb({"type": "summary", "content": "分析报告已生成，等待审核"})
                else:
                    error_msg = "Summary action missing report_markdown field"
                    print(f"\n[Agent Error] {error_msg}")
                    self.state.last_error = error_msg
                    self.session.add_step("tool", f"Error: {error_msg}", visible=True)
                    if status_cb:
                        status_cb({"type": "error", "content": error_msg})
            elif action["action"] == "review":
                if status_cb:
                    status_cb({"type": "action", "content": "审核报告..."})
                review_passed = action.get("review_passed", False)
                review_issues = action.get("review_issues", [])
                if review_passed:
                    print(f"\n[Agent] Review passed, proceeding to final")
                    self.session.add_step("assistant", "Review passed: Report is accurate and well-formatted", visible=True)
                    if status_cb:
                        status_cb({"type": "review", "content": "审核通过"})
                    # Continue to next iteration which should trigger final action
                else:
                    print(f"\n[Agent] Review found issues: {review_issues}")
                    self.session.add_step("assistant", f"Review issues found: {review_issues}", visible=True)
                    self.state.last_error = f"Review issues: {review_issues}"
                    if status_cb:
                        status_cb({"type": "review", "content": f"审核发现问题: {review_issues}"})
                    # Continue to next iteration which should fix issues via run_sql/use_skill
            elif action["action"] == "final":
                if status_cb:
                    status_cb("finalizing")

                # 检查是否有简单消息响应（不需要生成完整报告的场景）
                simple_message = action.get("simple_message", "")
                report_markdown = action.get("report_markdown", "")

                if simple_message:
                    # 使用简单消息（如记录规则完成、简单确认等）
                    report = simple_message
                elif report_markdown:
                    # 使用 LLM 提供的报告内容
                    report = report_markdown
                elif getattr(self.state, 'draft_report', None):
                    # 使用 review 通过的 draft report
                    report = self.state.draft_report
                elif self.state.results:
                    # 有数据结果，生成完整报告
                    report = self._final_report_via_llm(question)
                else:
                    # 没有数据结果，使用 notes 或默认消息
                    report = action.get("notes", "任务已完成。")

                # 添加最终报告到会话步骤，使其能在前端显示
                self.session.add_step("assistant", report, visible=True)
                # 保存最终结果到会话，支持会话切换后恢复
                self.session.set_final_result(report, status="completed")
                report_path = self._finalize(report, output_path, question)
                # 只在用户要求时才更新长期记忆
                if should_remember:
                    self._update_structured_memory(question, tables)
                if status_cb:
                    status_cb("done")
                return report_path
            else:
                # Invalid action, log error and continue
                error_msg = f"Invalid action received: {action.get('action', 'None')}. Expected one of: run_sql, use_skill, search_skills, summary, review, final"
                print(f"\n[Agent Error] {error_msg}")
                self.state.last_error = error_msg
                self.session.add_step("tool", f"Error: {error_msg}", visible=True)
                if status_cb:
                    status_cb({"type": "error", "content": error_msg})
                continue

        report = self._final_report_via_llm(question)
        # 添加最终报告到会话步骤，使其能在前端显示
        self.session.add_step("assistant", report, visible=True)
        # 保存最终结果到会话，支持会话切换后恢复
        self.session.set_final_result(report, status="completed")
        report_path = self._finalize(report, output_path, question)
        # 只在用户要求时才更新长期记忆
        if should_remember:
            self._update_structured_memory(question, tables)
        if status_cb:
            status_cb("done")
        return report_path

    def _load_learnings_summary(self) -> str:
        """加载用户learnings总结"""
        try:
            from .user_data import UserDataManager
            user_data_mgr = UserDataManager()
            learnings_path = user_data_mgr.get_user_learnings_path(self.user_id)
            if os.path.exists(learnings_path):
                with open(learnings_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 如果内容太长，只返回前5000字符
                    if len(content) > 5000:
                        return content[:5000] + "\n... (内容已截断)"
                    return content
        except Exception as e:
            print(f"[Warning] 加载learnings失败: {e}")
        return ""

    def _build_context_with_budget(self, question: str, tables: Optional[str]) -> Tuple[str, List[Dict], Dict]:
        """根据字符预算构建上下文
        
        策略：
        1. L0: 系统提示词 + 知识库rules + 相关tables + learnings + memory (必须保留，不截断)
        2. L1 = MAX_INPUT_CHARS - L0: 对话上下文可用预算
        3. 对话上下文按最近L1个字符截断
        
        Returns:
            (enhanced_system_prompt, truncated_steps, memory_context)
        """
        # 获取长期记忆上下文
        memory_context = self.memory.get_context()
        
        # 获取业务知识上下文 (包含rules和tables)
        business_context = self.knowledge.build_context(question)
        business_knowledge_str = self.knowledge.format_context_for_prompt(business_context)
        
        # 获取learnings总结
        learnings_summary = self._load_learnings_summary()
        
        # 构建L0: 系统提示词 + 知识库 + learnings
        enhanced_system_prompt = SYSTEM_PROMPT
        if business_knowledge_str:
            enhanced_system_prompt += f"\n\n{business_knowledge_str}"
        if learnings_summary:
            enhanced_system_prompt += f"\n\n## 历史学习记录\n{learnings_summary}"
        
        # 计算L0长度
        l0_chars = len(enhanced_system_prompt)
        
        # 计算L1: 对话上下文可用预算
        # 预留空间给user message的其他字段（question, tables, memory等）
        other_fields_estimate = 5000  # 估算其他字段的字符数
        l1_budget = MAX_INPUT_CHARS - l0_chars - other_fields_estimate
        
        # 获取会话上下文
        session_context = self.session.get_context()
        visible_steps = [s for s in session_context["steps"] if s.get("visible", True)]
        
        # 根据L1预算截断对话上下文
        if l1_budget < 1000:
            # 如果预算不足，只保留最少量的上下文
            print(f"[Warning] 上下文预算不足 (L1={l1_budget} chars)，只保留最近1步")
            truncated_steps = visible_steps[-1:] if visible_steps else []
        else:
            truncated_steps = truncate_steps_by_chars(visible_steps, int(l1_budget))
        
        # 打印上下文统计信息
        steps_chars = sum(len(json.dumps(s, ensure_ascii=False)) for s in truncated_steps)
        print(f"[Context] L0(系统+知识库+learnings): {l0_chars} chars (~{estimate_tokens(enhanced_system_prompt)} tokens)")
        print(f"[Context] L1(对话上下文预算): {l1_budget} chars, 实际使用: {steps_chars} chars (~{estimate_tokens(str(truncated_steps))} tokens)")
        print(f"[Context] 保留对话步骤: {len(truncated_steps)}/{len(visible_steps)}")
        
        return enhanced_system_prompt, truncated_steps, memory_context

    def _next_action(self, question: str, tables: Optional[str]) -> Dict[str, Any]:
        # 使用新的上下文预算管理方法构建上下文
        enhanced_system_prompt, truncated_steps, memory_context = self._build_context_with_budget(question, tables)
        
        results_summary = self._results_summary()
        skill_list = self.skills.list()
        
        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": question,
                        "tables": tables,
                        "memory_summary": memory_context.get("summary", ""),
                        "table_schemas": memory_context.get("table_schemas", {}),
                        "metric_definitions": memory_context.get("metric_definitions", {}),
                        "recent_steps": truncated_steps,
                        "results_summary": results_summary,
                        "last_sql": self.state.last_sql,
                        "last_error": self.state.last_error,
                        "skills": skill_list,
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        content = self.llm_provider.chat(messages, enforce_json=True)
        action = _parse_json(content)
        
        # Validate action
        if not isinstance(action, dict):
            print(f"[Warning] Invalid action format: {action}")
            action = {"action": "final", "report_markdown": f"Error: Invalid response format from LLM", "notes": "Invalid action format"}
        elif "action" not in action:
            print(f"[Warning] Action missing 'action' field: {action}")
            action = {"action": "final", "report_markdown": f"Error: Missing action field", "notes": "Missing action field"}
        elif action["action"] not in ("run_sql", "use_skill", "search_skills", "summary", "review", "final"):
            print(f"[Warning] Invalid action value: {action['action']}")
            # Try to recover by treating as final
            action = {"action": "final", "report_markdown": f"Error: Invalid action '{action.get('action')}'", "notes": f"Invalid action: {action.get('action')}"}
        
        visible_context = action.get("visible_context", True)
        self.session.add_step("assistant", content, visible=visible_context)
        
        return action

    def _handle_sql(self, sql: str) -> None:
        self.state.last_sql = sql
        self.state.last_error = None

        # SQL安全验证
        validation_result = self.sql_validator.validate(sql)
        if not validation_result.is_valid:
            error_msg = f"SQL validation failed: {'; '.join(validation_result.errors)}"
            print(f"\n[SQL] Validation Error: {error_msg}")
            self.state.last_error = error_msg
            self.state.notes.append(f"SQL validation error: {error_msg}")
            self.session.add_step("tool", f"SQL validation error: {error_msg}\nSQL: {sql}")
            self._auto_log_error(error_msg, "sql_validation", sql)
            return

        # 记录警告
        if validation_result.warnings:
            for warning in validation_result.warnings:
                print(f"\n[SQL] Warning: {warning}")

        try:
            print("\n[SQL] Executing:\n" + sql)
            # 使用 execute_sql_with_priority 替代 run_script_with_progress，默认 priority=5
            df, instance_id = self.odps.execute_sql_with_priority(sql, priority=5, cancel_event=self._cancel_event)
            print(f"[SQL] Instance ID: {instance_id}")
        except InterruptedError:
            # Task was cancelled
            self.state.last_error = "Task cancelled by user"
            self.session.add_step("tool", "SQL execution cancelled by user")
            raise  # Re-raise to stop the agent
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
            self.state.last_error = err
            self.state.add_note(f"SQL error: {err}")
            self.session.add_step("tool", f"SQL error: {err}\nSQL: {sql}")
            # 自动检测并记录错误
            self._auto_log_error(err, "sql_execution", sql)
            return
        preview = _df_preview(df)
        self.state.add_result(
            QueryResult(sql=sql, preview=preview, rows=len(df), columns=list(df.columns))
        )
        self.state.last_df = df
        # 记录执行的SQL
        self.state.add_executed_sql({
            "sql": sql,
            "rows": len(df),
            "instance_id": instance_id,
            "success": True
        })
        self.session.add_step("tool", f"SQL executed. Rows={len(df)}\n{preview}")

    def _handle_skill(self, skill: str, skill_args: Dict[str, Any]) -> None:
        # 检查是否最近已经调用过相同的skill（防止重复调用）
        if self.state.is_skill_recently_called(skill, skill_args):
            print(f"\n[Agent] Skipping duplicate skill call: {skill}")
            self.session.add_step("tool", f"Skipped duplicate skill call: {skill}", visible=False)
            return

        # 对于 self_improvement，使用专门的记录方法（跨会话跟踪）
        if skill == "self_improvement":
            self.state.record_self_improvement_call(skill_args)

        try:
            skill_def = self.skills.get(skill)
        except KeyError:
            self.state.last_error = f"Skill '{skill}' not found. Available skills: {list(self.skills.skills.keys())}"
            self.state.notes.append(self.state.last_error)
            self.session.add_step("tool", f"Skill error: {self.state.last_error}", visible=True)
            return

        is_invisible = skill_def.invisible_context if skill_def else True

        # 准备 skill 参数
        skill_args = dict(skill_args)

        # 只有需要 dataframe 的 skill 才添加 dataframe 参数
        skills_needing_dataframe = {"chart", "export", "analyze", "transform"}  # 明确需要 dataframe 的 skills
        if (self.state.last_df is not None and
            "dataframe" not in skill_args and
            skill in skills_needing_dataframe):
            skill_args["dataframe"] = self.state.last_df

        # 对于需要用户隔离的 skill，传入 user_id
        skills_needing_user_id = {"self_improvement", "update_memory"}  # 需要 user_id 的 skills
        if skill in skills_needing_user_id and self.user_id:
            skill_args["user_id"] = self.user_id

        try:
            result = self.skills.call(skill, **skill_args)
            self.state.add_note(f"Skill {skill} result: {result}")
            self.session.add_step("tool", f"Skill {skill} result: {result}", visible=not is_invisible)

            if skill_def and skill_def.hooks:
                self._run_hooks(skill, result, skill_def.hooks)
        except Exception as exc:
            err = str(exc)
            self.state.last_error = f"Skill '{skill}' error: {err}"
            self.state.add_note(f"Skill {skill} error: {err}")
            self.session.add_step("tool", f"Skill {skill} error: {err}\nSkill args: {skill_args}", visible=True)
            # 自动检测并记录错误
            self._auto_log_error(err, f"skill_execution:{skill}", skill_args=str(skill_args), skill_name=skill)

    def _handle_search_skills(self, keywords: str) -> None:
        import os
        import re
        from pathlib import Path
        
        skills_dir = self.skills.skills_dir
        results = []
        
        pattern = re.compile(keywords, re.IGNORECASE) if keywords else None
        
        for root, dirs, files in os.walk(skills_dir):
            for file in files:
                if file == "SKILL.md":
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if pattern is None or pattern.search(content):
                                rel_path = os.path.relpath(file_path, skills_dir)
                                results.append({
                                    "path": rel_path,
                                    "content": content[:500]
                                })
                    except Exception:
                        pass
        
        result_text = f"搜索关键词: {keywords}\n\n找到 {len(results)} 个相关 skills:\n"
        for r in results:
            result_text += f"- {r['path']}\n"
        
        self.state.notes.append(f"Skill search results: {result_text}")
        self.session.add_step("tool", f"Skill search: {result_text}", visible=True)

    def _final_report_via_llm(self, question: str) -> str:
        """基于会话历史生成最终报告。

        流程：
        1. 从会话历史中提取所有可见的对话内容（用户问题和助手回复）
        2. 将这些内容拼接成原始报告（包含实际数据）
        3. 让 LLM 对原始报告进行润色和格式化
        """
        # 获取会话历史
        context = self.session.get_context()
        steps = context.get("steps", [])

        # 构建原始报告内容（从会话历史中提取）
        raw_report_lines = []
        raw_report_lines.append(f"# 数据分析报告\n")
        raw_report_lines.append(f"**分析主题**: {question}\n")
        raw_report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        raw_report_lines.append("---\n")

        # 提取用户问题和助手回复中的分析内容
        for step in steps:
            role = step.get("role", "")
            content = step.get("content", "")
            visible = step.get("visible", True)

            # 只处理可见的内容
            if not visible:
                continue

            if role == "user":
                # 用户问题
                raw_report_lines.append(f"\n## 用户问题\n")
                raw_report_lines.append(f"{content}\n")
            elif role == "assistant":
                # 助手回复 - 尝试解析 JSON 格式的 action
                assistant_content = self._extract_assistant_content(content)
                if assistant_content:
                    raw_report_lines.append(f"\n## 分析结果\n")
                    raw_report_lines.append(f"{assistant_content}\n")
            elif role == "tool":
                # 工具执行结果（SQL 结果等）
                if "SQL executed" in content or "Rows=" in content:
                    raw_report_lines.append(f"\n### 数据查询结果\n")
                    raw_report_lines.append(f"```\n{content}\n```\n")

        # 添加实际查询结果数据（关键：包含实际数据表格）
        if self.state.results:
            raw_report_lines.append("\n## 实际查询结果数据\n")
            for i, result in enumerate(self.state.results, 1):
                raw_report_lines.append(f"\n### 查询 {i} 结果\n")
                raw_report_lines.append(f"**SQL**: `{result.sql}`\n")
                raw_report_lines.append(f"**返回行数**: {result.rows}\n")
                raw_report_lines.append(f"**数据预览**:\n")
                raw_report_lines.append(f"{result.preview}\n")

        # 添加执行的所有 SQL
        if self.state.executed_sqls:
            raw_report_lines.append("\n## 执行的SQL查询\n")
            for i, sql_info in enumerate(self.state.executed_sqls, 1):
                raw_report_lines.append(f"\n### 查询 {i}\n")
                raw_report_lines.append(f"```sql\n{sql_info['sql']}\n```\n")
                raw_report_lines.append(f"返回行数: {sql_info['rows']}\n")

        raw_report = "\n".join(raw_report_lines)

        # 让 LLM 润色原始报告
        messages = [
            {"role": "system", "content": FINAL_REPORT_PROMPT},
            {
                "role": "user",
                "content": f"请对以下原始数据分析报告进行润色和格式化，使其更加专业、易读。\n\n原始报告内容：\n\n{raw_report}",
            },
        ]
        return self.llm_provider.chat(messages, temperature=0.3)

    def _extract_assistant_content(self, content: str) -> str:
        """从助手回复中提取有用的内容"""
        if not isinstance(content, str):
            return ""

        content = content.strip()

        # 尝试解析 JSON 格式的 action
        if content.startswith("{"):
            try:
                parsed = json.loads(content)
                # 优先提取 report_markdown
                if "report_markdown" in parsed:
                    return parsed["report_markdown"]
                # 提取 notes
                if "notes" in parsed:
                    return parsed["notes"]
                # 提取 answer
                if "answer" in parsed:
                    return parsed["answer"]
            except json.JSONDecodeError:
                pass

        # 如果不是 JSON 或解析失败，返回原始内容
        return content

    def _generate_report_from_results(self, question: str) -> str:
        """基于已获取的结果生成报告（当LLM不可用时使用）"""
        if not self.state.results:
            return f"## 查询结果\n\n未能获取到结果。\n\n**问题**: {question}"

        report_lines = [f"## 查询结果\n", f"**问题**: {question}\n"]

        for i, result in enumerate(self.state.results, 1):
            report_lines.append(f"\n### 查询 {i}")
            report_lines.append(f"```sql\n{result.sql}\n```")
            report_lines.append(f"\n**返回行数**: {result.rows}")
            report_lines.append(f"\n**预览**:\n{result.preview}")

        # 添加说明
        report_lines.append("\n---\n")
        report_lines.append(
            "> **注意**: 由于LLM服务暂时不可用，此报告仅基于已执行的SQL查询结果生成。"
        )

        return "\n".join(report_lines)

    def _finalize(self, report_markdown: str, output_path: Optional[str], question: str = "") -> str:
        # 构建完整报告（包含执行SQL）
        full_report = report_markdown

        # 如果有执行的SQL，附加到报告末尾（紧凑格式）
        if self.state.executed_sqls:
            full_report += "\n\n"
            for i, sql_info in enumerate(self.state.executed_sqls, 1):
                full_report += f"```sql\n{sql_info['sql']}\n```\n\n"

        # 生成会话标题（使用简化逻辑，优先使用用户问题作为标题）
        self._generate_session_title_simple(question)

        # 总是保存报告到文件，如果用户指定了 output_path 则使用指定路径，否则使用默认路径
        return write_report(full_report, self.config.reports_dir, output_path)

    def _generate_session_title_simple(self, question: str = "") -> None:
        """使用LLM生成会话标题，基于用户问题和对话历史"""
        import threading
        
        def _generate_title_async():
            try:
                # 获取对话历史
                context = self.session.get_context()
                steps = context.get("steps", [])
                
                # 构建对话文本
                conversation_text = []
                
                # 添加历史对话（最多3轮）
                user_messages = [s for s in steps if s.get("role") == "user"]
                for msg in user_messages[-3:]:  # 最近3条用户消息
                    content = msg.get("content", "").strip()
                    if content:
                        conversation_text.append(content)
                
                # 添加当前问题
                if question and question.strip():
                    conversation_text.append(question.strip())
                
                if not conversation_text:
                    return
                
                # 构建prompt
                prompt = f"""根据以下用户问题和对话历史，生成一个简洁的会话标题（不超过15个字）。
标题应该准确概括对话的核心主题，使用中文。

用户问题：
{' | '.join(conversation_text)}

请直接返回标题文字，不要加引号或其他格式。"""

                messages = [
                    {"role": "system", "content": "你是一个专业的对话标题生成助手。"},
                    {"role": "user", "content": prompt}
                ]
                
                # 调用LLM生成标题
                title = self.llm_provider.chat(messages, enforce_json=False).strip()
                
                # 清理标题
                title = title.replace('"', '').replace("'", "").replace("「", "").replace("」", "").replace("标题：", "").replace("标题:", "").strip()
                if len(title) > 20:
                    title = title[:20]
                
                if title:
                    self.session.update_title(title)
                    print(f"\n[Session] 生成标题: {title}")
                    
            except Exception as e:
                print(f"\n[Session] 生成标题失败: {e}")
        
        # 异步执行标题生成，不阻塞主流程
        threading.Thread(target=_generate_title_async, daemon=True).start()

    def _generate_session_title(self) -> None:
        """根据对话内容生成合适的会话标题（异步调用LLM版本，用于后续优化）"""
        import threading

        def _generate_title_async():
            try:
                context = self.session.get_context()
                steps = context.get("steps", [])

                if not steps:
                    return

                # 构建对话摘要用于生成标题
                conversation_summary = []
                for step in steps[:10]:  # 只取前10步
                    role = step.get("role", "")
                    content = step.get("content", "")[:200]  # 限制长度
                    if role and content:
                        conversation_summary.append(f"{role}: {content}")

                if not conversation_summary:
                    return

                prompt = f"""根据以下对话内容，生成一个简洁的会话标题（不超过15个字）。
标题应该准确概括对话的核心主题。

对话内容：
{' | '.join(conversation_summary)}

请直接返回标题文字，不要加引号或其他格式。"""

                messages = [
                    {"role": "system", "content": "你是一个专业的对话标题生成助手。"},
                    {"role": "user", "content": prompt}
                ]

                title = self.llm_provider.chat(messages, enforce_json=False).strip()

                # 清理标题
                title = title.replace('"', '').replace("'", "").replace("「", "").replace("」", "")
                if len(title) > 20:
                    title = title[:20]

                if title:
                    self.session.update_title(title)
                    print(f"\n[Session] 生成标题: {title}")

            except Exception as e:
                print(f"\n[Session] 生成标题失败: {e}")

        # 异步执行标题生成，不阻塞主流程
        threading.Thread(target=_generate_title_async, daemon=True).start()

    def _run_hooks(self, skill_name: str, result: Any, hooks: List[str]) -> None:
        print(f"\n[Hooks] Running hooks for skill '{skill_name}': {hooks}")
        for hook in hooks:
            try:
                if hook == "basic_stats":
                    self._handle_skill("basic_stats", {"dataframe": self.state.last_df})
                elif hook == "self_improvement":
                    self._handle_skill("self_improvement", {
                        "content": f"Skill {skill_name} executed successfully",
                        "notes": f"Result: {str(result)[:200]}"
                    })
                elif hook == "feishu_notify":
                    pass
            except Exception as e:
                print(f"[Hooks] Error running hook '{hook}': {e}")

    def _auto_log_error(
        self,
        error_message: str,
        context: str,
        sql: Optional[str] = None,
        skill_args: Optional[str] = None,
        skill_name: Optional[str] = None,
    ) -> None:
        """自动检测并记录错误到 self_improvement"""
        try:
            manager = get_auto_improvement_manager()
            improvement_entry = manager.detect_error(
                error_message=error_message,
                context=context,
                sql=sql,
                skill_name=skill_name,
            )

            if improvement_entry:
                print(f"\n[AutoImprovement] 检测到错误，自动记录到学习日志")
                self._handle_skill("self_improvement", improvement_entry)

                # 检查是否需要触发学习回顾
                if manager.should_trigger_learning_review():
                    stats = manager.get_error_stats()
                    print(f"\n[AutoImprovement] 错误统计: {stats['error_counts']}")
        except Exception as e:
            # 自动改进机制不应影响主流程
            print(f"\n[AutoImprovement] 记录错误时出错: {e}")

    def _update_structured_memory(self, question: str, tables: Optional[str]) -> None:
        """只在用户要求时更新长期记忆"""
        session_context = self.session.get_context()
        messages = [
            {"role": "system", "content": MEMORY_EXTRACT_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": question,
                        "tables": tables,
                        "recent_steps": session_context["steps"],
                        "results_summary": self._results_summary(),
                        "last_sql": self.state.last_sql,
                        "last_error": self.state.last_error,
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        raw = self.llm_provider.chat(messages, temperature=0.2, enforce_json=True)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return
        
        # 保存到长期记忆
        if data.get("table_schemas"):
            for table, cols in data["table_schemas"].items():
                self.memory.save_table_schema(table, cols)
        if data.get("metric_definitions"):
            for metric, definition in data["metric_definitions"].items():
                self.memory.save_metric_definition(metric, definition)
        if data.get("business_background"):
            for item in data["business_background"]:
                self.memory.save_business_background(item)

    def _results_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "sql": r.sql,
                "rows": r.rows,
                "columns": r.columns,
                "preview": r.preview,
            }
            for r in self.state.results
        ]


def _df_preview(df: pd.DataFrame, max_rows: int = 10) -> str:
    if df.empty:
        return "<empty>"
    return tabulate(df.head(max_rows), headers="keys", tablefmt="github", showindex=False)


def _parse_json(content: str) -> Dict[str, Any]:
    import re
    import os
    from datetime import datetime
    
    original_content = content.strip()
    content = original_content
    
    # 如果内容以 ... 结尾，说明可能被截断了，记录警告
    if content.endswith('...'):
        print(f"[Warning] LLM response appears to be truncated: {content[:100]}...")
    
    # 尝试直接解析
    try:
        return json.loads(content, strict=False)
    except json.JSONDecodeError as e:
        first_error = str(e)
        pass

    # 尝试提取 JSON 对象（从第一个 { 到最后一个 }）
    try:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1], strict=False)
    except json.JSONDecodeError:
        pass

    # 尝试通过括号计数找到最外层的 JSON 对象
    brace_count = 0
    start = -1
    for i, c in enumerate(content):
        if c == '{':
            if start == -1:
                start = i
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0 and start != -1:
                try:
                    return json.loads(content[start:i+1], strict=False)
                except json.JSONDecodeError:
                    pass

    # 尝试匹配简单的 JSON 对象
    match = re.search(r'\{[^{}]*\}', content)
    if match:
        try:
            return json.loads(match.group(0), strict=False)
        except json.JSONDecodeError:
            pass

    # 尝试修复常见的 JSON 格式问题
    fixes = [
        # 修复1: 移除尾部逗号
        (lambda c: re.sub(r',(\s*[}\]])', r'\1', c), "remove trailing commas"),
        # 修复2: 修复反引号转义
        (lambda c: c.replace(r'\`', '`'), "fix backtick escape"),
        # 修复3: 修复换行符（将裸换行符转为 \n）
        (lambda c: c.replace('\n', '\\n').replace('\r', '\\r'), "escape newlines"),
        # 修复4: 修复制表符
        (lambda c: c.replace('\t', '\\t'), "escape tabs"),
        # 修复5: 修复无效的转义序列
        (lambda c: re.sub(r'\\([^"\\/bfnrtu])', r'\1', c), "fix invalid escapes"),
        # 修复6: 修复单引号（JSON 标准要求双引号）
        (lambda c: c.replace("'", '"'), "replace single quotes"),
        # 修复7: 修复可能的 Unicode 转义问题
        (lambda c: re.sub(r'\\u([0-9a-fA-F]{0,3})(?![0-9a-fA-F])', r'\\u0000', c), "fix unicode escapes"),
        # 修复8: 修复未转义的双引号（在字符串值中）
        # 这个比较复杂，需要识别哪些双引号是 JSON 结构的一部分，哪些是字符串内容
    ]
    
    for fix_func, fix_name in fixes:
        try:
            fixed_content = fix_func(content)
            result = json.loads(fixed_content, strict=False)
            print(f"[JSON Parse] Fixed with: {fix_name}")
            return result
        except json.JSONDecodeError:
            continue
    
    # 尝试组合修复
    try:
        fixed_content = content
        # 先处理换行符
        fixed_content = fixed_content.replace('\n', '\\n').replace('\r', '\\r')
        # 再处理制表符
        fixed_content = fixed_content.replace('\t', '\\t')
        # 移除尾部逗号
        fixed_content = re.sub(r',(\s*[}\]])', r'\1', fixed_content)
        # 修复无效转义
        fixed_content = re.sub(r'\\([^"\\/bfnrtu])', r'\1', fixed_content)
        return json.loads(fixed_content, strict=False)
    except json.JSONDecodeError:
        pass

    # 尝试修复未转义的双引号问题（在字符串值中）
    # 策略：找到 "report_markdown": 后面的内容，将其中的未转义双引号转义
    try:
        # 匹配 report_markdown 字段的内容
        pattern = r'("report_markdown"\s*:\s*")(.*?)"\s*[,}]'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            prefix = content[:match.start(2)]
            markdown_content = match.group(2)
            suffix = content[match.end(2):]
            
            # 转义 markdown 内容中的双引号
            escaped_markdown = markdown_content.replace('"', '\\"')
            
            fixed_content = prefix + escaped_markdown + suffix
            return json.loads(fixed_content, strict=False)
    except (json.JSONDecodeError, re.error):
        pass

    # 尝试处理内容被截断的情况（补全未闭合的字符串）
    try:
        fixed_content = content
        # 检查是否有未闭合的字符串
        quote_count = fixed_content.count('"') - fixed_content.count('\\"')
        if quote_count % 2 != 0:
            # 奇数个双引号，说明有未闭合的字符串
            fixed_content += '"'
        # 检查括号是否匹配
        if fixed_content.count('{') > fixed_content.count('}'):
            fixed_content += '}' * (fixed_content.count('{') - fixed_content.count('}'))
        if fixed_content.count('[') > fixed_content.count(']'):
            fixed_content += ']' * (fixed_content.count('[') - fixed_content.count(']'))
        return json.loads(fixed_content, strict=False)
    except json.JSONDecodeError:
        pass

    # 如果所有修复都失败，保存错误日志并记录详细的错误信息
    error_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    error_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'logs', f'json_parse_error_{error_timestamp}.log')
    
    try:
        os.makedirs(os.path.dirname(error_log_path), exist_ok=True)
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(f"Error: {first_error}\n")
            f.write(f"Content length: {len(content)}\n")
            f.write(f"Content:\n{content}\n")
        print(f"[JSON Parse Error] Error log saved to: {error_log_path}")
    except Exception as log_e:
        print(f"[JSON Parse Error] Failed to save error log: {log_e}")
    
    print(f"[JSON Parse Error] Could not parse JSON (length={len(content)})")
    print(f"[JSON Parse Error] First error: {first_error}")
    print(f"[JSON Parse Error] Content preview: {content[:200]}...")
    print(f"[JSON Parse Error] Content end: ...{content[-200:]}")
    
    raise ValueError(f"Could not parse JSON from content (length={len(content)}, first_error={first_error[:100]}): {content[:200]}...")
