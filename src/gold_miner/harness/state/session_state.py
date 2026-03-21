"""Session State - 会话状态管理"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Step:
    """执行步骤"""
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    visible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionRecord:
    """执行记录"""
    sql: str
    rows: int
    instance_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionState:
    """
    会话状态 - 解决 Lost State on Failure 问题

    包含：
    1. 当前执行上下文
    2. 执行历史
    3. 状态快照
    """
    session_id: str
    question: str = ""
    current_step: int = 0
    max_steps: int = 6

    results: List[Any] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    last_df: Optional[Any] = None
    last_sql: Optional[str] = None
    last_error: Optional[str] = None
    executed_sqls: List[ExecutionRecord] = field(default_factory=list)

    steps: List[Step] = field(default_factory=list)

    is_cancelled: bool = False
    is_completed: bool = False
    cancel_reason: Optional[str] = None

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def tick(self) -> None:
        """推进一步"""
        self.current_step += 1
        self.updated_at = datetime.now().isoformat()

    def add_step(self, role: str, content: str, visible: bool = True, **metadata) -> None:
        """添加执行步骤"""
        self.steps.append(Step(
            role=role,
            content=content,
            visible=visible,
            metadata=metadata
        ))
        self.updated_at = datetime.now().isoformat()

    def add_result(self, result: Any) -> None:
        """添加结果"""
        self.results.append(result)
        self.updated_at = datetime.now().isoformat()

    def add_note(self, note: str) -> None:
        """添加笔记"""
        self.notes.append(note)
        self.updated_at = datetime.now().isoformat()

    def add_sql(self, record: ExecutionRecord) -> None:
        """添加 SQL 执行记录"""
        self.executed_sqls.append(record)
        self.updated_at = datetime.now().isoformat()

    def cancel(self, reason: Optional[str] = None) -> None:
        """取消执行"""
        self.is_cancelled = True
        self.cancel_reason = reason
        self.updated_at = datetime.now().isoformat()

    def complete(self) -> None:
        """标记完成"""
        self.is_completed = True
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "question": self.question,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "results": self.results,
            "notes": self.notes,
            "last_sql": self.last_sql,
            "last_error": self.last_error,
            "executed_sqls": [
                {
                    "sql": r.sql,
                    "rows": r.rows,
                    "instance_id": r.instance_id,
                    "success": r.success,
                    "error": r.error,
                    "timestamp": r.timestamp
                }
                for r in self.executed_sqls
            ],
            "steps": [
                {
                    "role": s.role,
                    "content": s.content,
                    "timestamp": s.timestamp,
                    "visible": s.visible,
                    "metadata": s.metadata
                }
                for s in self.steps
            ],
            "is_cancelled": self.is_cancelled,
            "is_completed": self.is_completed,
            "cancel_reason": self.cancel_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """从字典恢复"""
        state = cls(
            session_id=data["session_id"],
            question=data.get("question", ""),
            current_step=data.get("current_step", 0),
            max_steps=data.get("max_steps", 6)
        )
        state.results = data.get("results", [])
        state.notes = data.get("notes", [])
        state.last_sql = data.get("last_sql")
        state.last_error = data.get("last_error")
        state.executed_sqls = [
            ExecutionRecord(**r) for r in data.get("executed_sqls", [])
        ]
        state.steps = [Step(**s) for s in data.get("steps", [])]
        state.is_cancelled = data.get("is_cancelled", False)
        state.is_completed = data.get("is_completed", False)
        state.cancel_reason = data.get("cancel_reason")
        state.created_at = data.get("created_at", datetime.now().isoformat())
        state.updated_at = data.get("updated_at", datetime.now().isoformat())
        return state

    def summary(self) -> str:
        """生成状态摘要"""
        return (
            f"Session: {self.session_id}\n"
            f"Step: {self.current_step}/{self.max_steps}\n"
            f"SQLs: {len(self.executed_sqls)}\n"
            f"Results: {len(self.results)}\n"
            f"Status: {'Completed' if self.is_completed else ('Cancelled' if self.is_cancelled else 'Running')}"
        )