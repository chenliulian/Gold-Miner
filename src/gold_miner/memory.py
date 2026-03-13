from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MemoryState:
    summary: str = ""
    recent_steps: List[Dict[str, str]] = field(default_factory=list)
    table_schemas: Dict[str, List[str]] = field(default_factory=dict)
    metric_definitions: Dict[str, str] = field(default_factory=dict)
    business_background: List[str] = field(default_factory=list)


class MemoryStore:
    def __init__(self, path: str, max_recent: int = 50, summary_path: str | None = None):
        self.path = path
        self.max_recent = max_recent
        self.summary_path = summary_path or os.path.join(os.path.dirname(path), "summary.md")
        self.total_steps = 0
        self.state = MemoryState()
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.state.summary = raw.get("summary", "")
        self.state.recent_steps = raw.get("recent_steps", [])
        self.state.table_schemas = raw.get("table_schemas", {})
        self.state.metric_definitions = raw.get("metric_definitions", {})
        self.state.business_background = raw.get("business_background", [])

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": self.state.summary,
                    "recent_steps": self.state.recent_steps,
                    "table_schemas": self.state.table_schemas,
                    "metric_definitions": self.state.metric_definitions,
                    "business_background": self.state.business_background,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        self._write_summary_doc()

    def _write_summary_doc(self) -> None:
        lines = []
        lines.append("# Memory Summary\n")
        if self.state.summary:
            lines.append("## Conversation Summary\n")
            lines.append(self.state.summary.strip() + "\n")
        if self.state.table_schemas:
            lines.append("## Table Schemas\n")
            for table, cols in self.state.table_schemas.items():
                cols_text = ", ".join(cols)
                lines.append(f"- `{table}`: {cols_text}\n")
        if self.state.metric_definitions:
            lines.append("## Metric Definitions\n")
            for metric, definition in self.state.metric_definitions.items():
                lines.append(f"- `{metric}`: {definition}\n")
        if self.state.business_background:
            lines.append("## Business Background\n")
            for item in self.state.business_background:
                lines.append(f"- {item}\n")
        os.makedirs(os.path.dirname(self.summary_path), exist_ok=True)
        with open(self.summary_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def add_step(self, role: str, content: str) -> None:
        self.state.recent_steps.append({"role": role, "content": content})
        self.total_steps += 1
        if len(self.state.recent_steps) > self.max_recent:
            self.state.recent_steps = self.state.recent_steps[-self.max_recent :]
        self._save()

    def set_summary(self, summary: str) -> None:
        self.state.summary = summary
        self._save()

    def update_structured(
        self,
        table_schemas: Dict[str, List[str]] | None = None,
        metric_definitions: Dict[str, str] | None = None,
        business_background: List[str] | None = None,
    ) -> None:
        if table_schemas:
            for table, cols in table_schemas.items():
                if not cols:
                    continue
                self.state.table_schemas[table] = cols
        if metric_definitions:
            self.state.metric_definitions.update(metric_definitions)
        if business_background:
            existing = set(self.state.business_background)
            for item in business_background:
                if item not in existing:
                    self.state.business_background.append(item)
                    existing.add(item)
        self._save()

    def clear(self) -> None:
        self.state = MemoryState()
        self._save()

    def get_context(self) -> Dict[str, List[Dict[str, str]] | str]:
        need_summary = self.total_steps > self.max_recent and not self.state.summary
        
        recent_steps = list(self.state.recent_steps)
        has_interrupt = False
        if recent_steps and "[用户插话]" in recent_steps[-1].get("content", ""):
            has_interrupt = True
            recent_steps[-1]["content"] = recent_steps[-1]["content"].replace("[用户插话] ", "")
        
        return {
            "summary": self.state.summary,
            "recent_steps": recent_steps,
            "table_schemas": self.state.table_schemas,
            "metric_definitions": self.state.metric_definitions,
            "business_background": self.state.business_background,
            "total_steps": self.total_steps,
            "need_summary": need_summary,
            "has_interrupt": has_interrupt,
        }
