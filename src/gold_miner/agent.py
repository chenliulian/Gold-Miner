from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd
from tabulate import tabulate

from .auto_improvement import get_auto_improvement_manager
from .business_knowledge import get_knowledge_manager
from .config import Config
from .llm import OpenAICompatibleClient
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


@dataclass
class QueryResult:
    sql: str
    preview: str
    rows: int
    columns: List[str]


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


class SqlAgent:
    def __init__(
        self,
        config: Config,
        skills_dir: str,
        sessions_dir: Optional[str] = None,
        sql_validator: Optional[SQLValidator] = None,
    ):
        self.config = config
        self.llm = OpenAICompatibleClient(
            config.llm_base_url, config.llm_api_key, config.llm_model
        )
        self.odps = OdpsClient(
            OdpsConfig(
                access_id=config.odps_access_id,
                access_key=config.odps_access_key,
                project=config.odps_project,
                endpoint=config.odps_endpoint,
            )
        )
        # 长期记忆 - 只保存用户明确要求记住的内容
        self.memory = MemoryStore(config.memory_path)
        # 会话历史 - 保存每次对话的完整记录
        sessions_dir = sessions_dir or os.path.join(os.path.dirname(config.memory_path), "../sessions")
        self.session = SessionStore(sessions_dir)
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
            action = self._next_action(question, tables)
            note = action.get("notes")
            if note:
                print(f"\n[Agent] {note}")
                if status_cb:
                    status_cb({"type": "note", "content": note})
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
            elif action["action"] == "final":
                if status_cb:
                    status_cb("finalizing")
                report_path = self._finalize(action["report_markdown"], output_path)
                # 只在用户要求时才更新长期记忆
                if should_remember:
                    self._update_structured_memory(question, tables)
                if status_cb:
                    status_cb("done")
                return report_path
            else:
                # Invalid action, log error and continue
                error_msg = f"Invalid action received: {action.get('action', 'None')}. Expected one of: run_sql, use_skill, search_skills, final"
                print(f"\n[Agent Error] {error_msg}")
                self.state.last_error = error_msg
                self.session.add_step("tool", f"Error: {error_msg}", visible=True)
                if status_cb:
                    status_cb({"type": "error", "content": error_msg})
                continue

        report = self._final_report_via_llm(question)
        report_path = self._finalize(report, output_path)
        # 只在用户要求时才更新长期记忆
        if should_remember:
            self._update_structured_memory(question, tables)
        if status_cb:
            status_cb("done")
        return report_path

    def _next_action(self, question: str, tables: Optional[str]) -> Dict[str, Any]:
        # 获取会话上下文（最近对话历史）
        session_context = self.session.get_context()
        # 获取长期记忆上下文
        memory_context = self.memory.get_context()
        
        results_summary = self._results_summary()
        skill_list = self.skills.list()
        
        # 获取业务知识上下文
        business_context = self.knowledge.build_context(question)
        business_knowledge_str = self.knowledge.format_context_for_prompt(business_context)
        
        visible_steps = [s for s in session_context["steps"] if s.get("visible", True)]
        
        # 构建增强的 system prompt
        enhanced_system_prompt = SYSTEM_PROMPT
        if business_knowledge_str:
            enhanced_system_prompt += f"\n\n{business_knowledge_str}"
        
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
                        "recent_steps": visible_steps,
                        "results_summary": results_summary,
                        "last_sql": self.state.last_sql,
                        "last_error": self.state.last_error,
                        "skills": skill_list,
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        content = self.llm.chat(messages, enforce_json=True)
        action = _parse_json(content)
        
        # Validate action
        if not isinstance(action, dict):
            print(f"[Warning] Invalid action format: {action}")
            action = {"action": "final", "report_markdown": f"Error: Invalid response format from LLM", "notes": "Invalid action format"}
        elif "action" not in action:
            print(f"[Warning] Action missing 'action' field: {action}")
            action = {"action": "final", "report_markdown": f"Error: Missing action field", "notes": "Missing action field"}
        elif action["action"] not in ("run_sql", "use_skill", "search_skills", "final"):
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
        try:
            skill_def = self.skills.get(skill)
        except KeyError:
            self.state.last_error = f"Skill '{skill}' not found. Available skills: {list(self.skills.skills.keys())}"
            self.state.notes.append(self.state.last_error)
            self.session.add_step("tool", f"Skill error: {self.state.last_error}", visible=True)
            return
        
        is_invisible = skill_def.invisible_context if skill_def else True
        
        if self.state.last_df is not None and "dataframe" not in skill_args:
            skill_args = dict(skill_args)
            skill_args["dataframe"] = self.state.last_df
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
        results_summary = self._results_summary()
        messages = [
            {"role": "system", "content": FINAL_REPORT_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"question": question, "results_summary": results_summary},
                    ensure_ascii=False,
                ),
            },
        ]
        return self.llm.chat(messages, temperature=0.3)

    def _finalize(self, report_markdown: str, output_path: Optional[str]) -> str:
        # 构建完整报告（包含执行SQL）
        full_report = report_markdown
        
        # 如果有执行的SQL，附加到报告末尾
        if self.state.executed_sqls:
            full_report += "\n\n---\n\n## 执行SQL详情\n\n"
            for i, sql_info in enumerate(self.state.executed_sqls, 1):
                full_report += f"### SQL {i}\n\n"
                full_report += f"```sql\n{sql_info['sql']}\n```\n\n"
                full_report += f"- 返回行数: {sql_info['rows']}\n"
                full_report += f"- Instance ID: {sql_info.get('instance_id', 'N/A')}\n\n"
        
        # 总是保存报告到文件，如果用户指定了 output_path 则使用指定路径，否则使用默认路径
        return write_report(full_report, self.config.reports_dir, output_path)

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
        raw = self.llm.chat(messages, temperature=0.2, enforce_json=True)
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
    
    content = content.strip()
    
    # 如果内容以 ... 结尾，说明可能被截断了，记录警告
    if content.endswith('...'):
        print(f"[Warning] LLM response appears to be truncated: {content[:100]}...")
    
    try:
        return json.loads(content, strict=False)
    except json.JSONDecodeError:
        pass

    try:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1], strict=False)
    except json.JSONDecodeError:
        pass

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

    match = re.search(r'\{[^{}]*\}', content)
    if match:
        try:
            return json.loads(match.group(0), strict=False)
        except json.JSONDecodeError:
            pass

    # 尝试修复常见的 JSON 格式问题
    try:
        # 移除可能的尾部逗号
        fixed_content = re.sub(r',(\s*[}\]])', r'\1', content)
        return json.loads(fixed_content, strict=False)
    except json.JSONDecodeError:
        pass

    # 尝试修复反引号转义问题 (LLM 有时会返回 \` 而不是 `)
    try:
        fixed_content = content.replace(r'\`', '`')
        return json.loads(fixed_content, strict=False)
    except json.JSONDecodeError:
        pass

    # 尝试修复其他常见的无效转义序列
    try:
        # 将无效的转义序列替换为未转义的字符
        fixed_content = re.sub(r'\\([^"\\/bfnrtu])', r'\1', content)
        return json.loads(fixed_content, strict=False)
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not parse JSON from content (length={len(content)}): {content[:500]}...")
