"""Session summarization scheduler - extracts reusable experiences from conversation history."""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SessionSummary:
    """Summary of a conversation session."""
    session_id: str
    title: str
    start_time: str
    duration_minutes: float
    step_count: int
    key_insights: List[str] = field(default_factory=list)
    reusable_patterns: List[str] = field(default_factory=list)
    sql_queries: List[str] = field(default_factory=list)
    tables_used: List[str] = field(default_factory=list)
    summary_text: str = ""


class SessionSummarizer:
    """Review session histories and extract reusable experiences."""

    def __init__(
        self,
        sessions_dir: str = "./sessions",
        memory_path: str = "./memory/memory.json",
        review_interval_hours: int = 1,
        auto_start: bool = False,
    ):
        self.sessions_dir = Path(sessions_dir)
        self.memory_path = Path(memory_path)
        self.review_interval = timedelta(hours=review_interval_hours)
        self._auto_start = auto_start

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_review: Optional[datetime] = None
        self._callbacks: List[callable] = []
        self._memory_lock = threading.Lock()

        if self._auto_start:
            self.start()

    def start(self) -> None:
        """Start the summarizer in background thread."""
        if self._thread and self._thread.is_alive():
            print("[SessionSummarizer] Already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[SessionSummarizer] Started (interval: {self.review_interval})")

    def stop(self) -> None:
        """Stop the summarizer."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        print("[SessionSummarizer] Stopped")

    def _run(self) -> None:
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            try:
                self._perform_review()
            except Exception as e:
                print(f"[SessionSummarizer] Review failed: {e}")

            self._stop_event.wait(self.review_interval.total_seconds())

    def _perform_review(self) -> None:
        """Review recent sessions and extract insights."""
        print(f"[SessionSummarizer] Starting session review at {datetime.now()}")

        sessions = self._get_recent_sessions()
        if not sessions:
            print("[SessionSummarizer] No sessions to review")
            return

        summaries = []
        for session in sessions:
            summary = self._summarize_session(session)
            if summary:
                summaries.append(summary)

        if summaries:
            self._append_insights_to_memory(summaries)
            self._trigger_callbacks(summaries)

        self._last_review = datetime.now()
        print(f"[SessionSummarizer] Reviewed {len(sessions)} sessions, extracted {len(summaries)} insights")

    def _get_recent_sessions(self) -> List[Dict]:
        """Get sessions from the past review interval."""
        sessions = []
        cutoff = datetime.now() - self.review_interval

        if not self.sessions_dir.exists():
            return sessions

        for filename in sorted(self.sessions_dir.glob("session_*.json"), reverse=True):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    session_data = json.load(f)

                start_time = datetime.fromisoformat(session_data.get("start_time", ""))
                if start_time > cutoff:
                    sessions.append(session_data)
            except Exception:
                continue

        return sessions

    def _summarize_session(self, session: Dict) -> Optional[SessionSummary]:
        """Summarize a single session."""
        steps = session.get("steps", [])
        if not steps:
            return None

        try:
            start_time = datetime.fromisoformat(session.get("start_time", ""))
            end_time = datetime.fromisoformat(session.get("end_time", "")) if session.get("end_time") else datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
        except Exception:
            duration = 0

        key_insights = []
        reusable_patterns = []
        sql_queries = []
        tables_used = []

        for step in steps:
            content = step.get("content", "")
            role = step.get("role", "")

            if role == "user":
                if any(kw in content for kw in ["记住", "保存", "沉淀"]):
                    key_insights.append(content[:200])

            if role == "assistant":
                if "SELECT" in content.upper() or "CREATE TABLE" in content.upper():
                    if len(content) > 50:
                        sql_queries.append(content[:500])

                for kw in ["常用模式", "pattern", "最佳实践", "推荐做法"]:
                    if kw in content:
                        reusable_patterns.append(content[:200])

        summary_text = self._generate_summary_text(session, len(steps), duration)

        return SessionSummary(
            session_id=session.get("session_id", ""),
            title=session.get("title", "未命名"),
            start_time=session.get("start_time", ""),
            duration_minutes=duration,
            step_count=len(steps),
            key_insights=key_insights,
            reusable_patterns=reusable_patterns,
            sql_queries=sql_queries,
            tables_used=tables_used,
            summary_text=summary_text,
        )

    def _generate_summary_text(self, session: Dict, step_count: int, duration: float) -> str:
        """Generate readable summary text."""
        title = session.get("title", "未命名")
        return f"对话「{title}」- {step_count}轮对话，耗时{duration:.1f}分钟"

    def _append_insights_to_memory(self, summaries: List[SessionSummary]) -> None:
        """Append extracted insights to memory document."""
        with self._memory_lock:
            if not self.memory_path.exists():
                return

            memory_md = self.memory_path.with_suffix(".md")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

            lines = [f"\n## 会话回顾沉淀 ({timestamp})\n"]

            for summary in summaries:
                lines.append(f"\n### {summary.title}\n")
                lines.append(f"- 时间: {summary.start_time}\n")
                lines.append(f"- 时长: {summary.duration_minutes:.1f}分钟\n")
                lines.append(f"- 轮数: {summary.step_count}\n")

                if summary.key_insights:
                    lines.append("\n**关键洞察:**\n")
                    for insight in summary.key_insights[:3]:
                        lines.append(f"- {insight}\n")

                if summary.reusable_patterns:
                    lines.append("\n**可复用模式:**\n")
                    for pattern in summary.reusable_patterns[:3]:
                        lines.append(f"- {pattern}\n")

                if summary.sql_queries:
                    lines.append(f"\n**涉及SQL数: {len(summary.sql_queries)}**\n")

            try:
                with open(memory_md, "a", encoding="utf-8") as f:
                    f.writelines(lines)
                print(f"[SessionSummarizer] Appended insights to {memory_md}")
            except Exception as e:
                print(f"[SessionSummarizer] Failed to append insights: {e}")

    def _trigger_callbacks(self, summaries: List[SessionSummary]) -> None:
        """Trigger registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(summaries)
            except Exception as e:
                print(f"[SessionSummarizer] Callback error: {e}")

    def on_review_complete(self, callback: callable) -> None:
        """Register a callback to be called when review completes."""
        self._callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Get summarizer statistics."""
        sessions = self._get_recent_sessions()
        return {
            "last_review": self._last_review.isoformat() if self._last_review else None,
            "next_review_in_seconds": (
                (self.review_interval - (datetime.now() - self._last_review)).total_seconds()
                if self._last_review else self.review_interval.total_seconds()
            ),
            "is_running": self._thread is not None and self._thread.is_alive(),
            "sessions_in_period": len(sessions),
        }


_session_summarizer: Optional[SessionSummarizer] = None


def get_session_summarizer(
    sessions_dir: str = "./sessions",
    memory_path: str = "./memory/memory.json",
    review_interval_hours: int = 1,
    auto_start: bool = False,
) -> SessionSummarizer:
    """Get or create global session summarizer instance."""
    global _session_summarizer
    if _session_summarizer is None:
        _session_summarizer = SessionSummarizer(
            sessions_dir=sessions_dir,
            memory_path=memory_path,
            review_interval_hours=review_interval_hours,
            auto_start=auto_start,
        )
    return _session_summarizer
