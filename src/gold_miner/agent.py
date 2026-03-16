from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd
from tabulate import tabulate

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


class SqlAgent:
    def __init__(self, config: Config, skills_dir: str):
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
        self.memory = MemoryStore(config.memory_path)
        self.skills = SkillRegistry(skills_dir)
        self.skills.load()
        self.state = AgentState()

    def run(
        self,
        question: str,
        tables: Optional[str] = None,
        max_steps: Optional[int] = None,
        output_path: Optional[str] = None,
        cancel_event: Optional[Any] = None,
        status_cb: Optional[Any] = None,
        heartbeat_cb: Optional[Any] = None,
    ) -> str:
        max_steps = max_steps or self.config.agent_max_steps
        if status_cb:
            status_cb("starting")
        
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
                self._handle_sql(action["sql"])
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
            elif action["action"] == "final":
                if status_cb:
                    status_cb("finalizing")
                report_path = self._finalize(action["report_markdown"], output_path)
                self._update_structured_memory(question, tables)
                if status_cb:
                    status_cb("done")
                return report_path
            else:
                raise ValueError(f"Unknown action: {action}")
            self._maybe_update_memory_summary()

        report = self._final_report_via_llm(question)
        report_path = self._finalize(report, output_path)
        self._update_structured_memory(question, tables)
        if status_cb:
            status_cb("done")
        return report_path

    def _next_action(self, question: str, tables: Optional[str]) -> Dict[str, Any]:
        context = self.memory.get_context()
        results_summary = self._results_summary()
        skill_list = self.skills.list()
        
        visible_steps = [s for s in context["recent_steps"] if s.get("visible", True)]
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": question,
                        "tables": tables,
                        "memory_summary": context["summary"],
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
        
        visible_context = action.get("visible_context", True)
        self.memory.add_step("assistant", content, visible=visible_context)
        
        return action

    def _handle_sql(self, sql: str) -> None:
        self.state.last_sql = sql
        self.state.last_error = None
        try:
            if "SET odps.instance.priority" not in sql:
                sql = "SET odps.instance.priority = 7;\n" + sql
            print("\n[SQL] Executing:\n" + sql)
            df = self.odps.run_script(sql)
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
            self.state.last_error = err
            self.state.notes.append(f"SQL error: {err}")
            self.memory.add_step("tool", f"SQL error: {err}\nSQL: {sql}")
            return
        preview = _df_preview(df)
        self.state.results.append(
            QueryResult(sql=sql, preview=preview, rows=len(df), columns=list(df.columns))
        )
        self.state.last_df = df
        self.memory.add_step("tool", f"SQL executed. Rows={len(df)}\n{preview}")

    def _handle_skill(self, skill: str, skill_args: Dict[str, Any]) -> None:
        skill_def = self.skills.get(skill)
        is_invisible = skill_def.invisible_context if skill_def else True
        
        if self.state.last_df is not None and "dataframe" not in skill_args:
            skill_args = dict(skill_args)
            skill_args["dataframe"] = self.state.last_df
        try:
            result = self.skills.call(skill, **skill_args)
            self.state.notes.append(f"Skill {skill} result: {result}")
            self.memory.add_step("tool", f"Skill {skill} result: {result}", visible=not is_invisible)
            
            if skill_def and skill_def.hooks:
                self._run_hooks(skill, result, skill_def.hooks)
        except Exception as exc:
            err = str(exc)
            self.state.last_error = f"Skill '{skill}' error: {err}"
            self.state.notes.append(f"Skill {skill} error: {err}")
            self.memory.add_step("tool", f"Skill {skill} error: {err}\nSkill args: {skill_args}", visible=True)

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
        return write_report(report_markdown, self.config.reports_dir, output_path)

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

    def _maybe_update_memory_summary(self) -> None:
        context = self.memory.get_context()
        if not context.get("need_summary"):
            return
        messages = [
            {"role": "system", "content": MEMORY_SUMMARY_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "current_summary": self.memory.state.summary,
                        "recent_steps": self.memory.state.recent_steps,
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        summary = self.llm.chat(messages, temperature=0.2)
        self.memory.set_summary(summary)

    def _update_structured_memory(self, question: str, tables: Optional[str]) -> None:
        context = self.memory.get_context()
        messages = [
            {"role": "system", "content": MEMORY_EXTRACT_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": question,
                        "tables": tables,
                        "memory_summary": context["summary"],
                        "recent_steps": context["recent_steps"],
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
        self.memory.update_structured(
            table_schemas=data.get("table_schemas"),
            metric_definitions=data.get("metric_definitions"),
            business_background=data.get("business_background"),
        )

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
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    try:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            return json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        pass

    import re
    match = re.search(r'\{[^{}]*\}', content)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from content: {content[:200]}...")
