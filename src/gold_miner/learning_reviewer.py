"""Learning record review scheduler with heartbeat mechanism.

This module provides periodic review of .learnings records,
summarizing them and appending to memory.md for human audit.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set


class ReviewStatus(Enum):
    """Status of a learning record review."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    MODIFIED = "modified"


@dataclass
class LearningRecord:
    """Represents a single learning record from .learnings files."""
    id: str
    type: str  # correction | insight | knowledge_gap | best_practice
    area: str  # frontend | backend | infra | tests | docs | config | odps
    priority: str
    status: ReviewStatus
    logged_at: datetime
    summary: str
    details: str
    suggested_action: str
    source: str
    related_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    review_notes: str = ""
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None


@dataclass
class ReviewReport:
    """Report generated from periodic review."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_records: int
    by_type: Dict[str, int]
    by_area: Dict[str, int]
    by_status: Dict[str, int]
    pending_high_priority: List[LearningRecord]
    summary: str
    recommendations: List[str]


class LearningParser:
    """Parser for .learnings markdown files."""

    @staticmethod
    def parse_file(filepath: Path) -> List[LearningRecord]:
        """Parse a learnings markdown file and extract records."""
        filepath = Path(filepath)
        if not filepath.exists():
            return []

        content = filepath.read_text(encoding="utf-8")
        records = []

        # Split by record headers (## [ID-XXXX])
        pattern = r'##\s*\[([A-Z]+-\d{8}-\d{3})\]\s*(\w+)'
        parts = re.split(pattern, content)

        if len(parts) < 2:
            return records

        # parts[0] is header, then id, type, content for each record
        for i in range(1, len(parts), 3):
            if i + 2 >= len(parts):
                break

            record_id = parts[i]
            record_type = parts[i + 1]
            record_content = parts[i + 2]

            record = LearningParser._parse_record(record_id, record_type, record_content)
            if record:
                records.append(record)

        return records

    @staticmethod
    def _parse_record(record_id: str, record_type: str, content: str) -> Optional[LearningRecord]:
        """Parse individual record content."""
        try:
            # Extract fields using regex
            logged_match = re.search(r'\*\*Logged\*\*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', content)
            priority_match = re.search(r'\*\*Priority\*\*:\s*(\w+)', content)
            status_match = re.search(r'\*\*Status\*\*:\s*(\w+)', content)
            area_match = re.search(r'\*\*Area\*\*:\s*(\w+)', content)
            summary_match = re.search(r'### Summary\s*\n([^#]+)', content)
            details_match = re.search(r'### Details\s*\n([^#]+)', content)
            action_match = re.search(r'### Suggested Action\s*\n([^#]+)', content)
            source_match = re.search(r'\* Source:\s*(\w+)', content)

            # Parse tags
            tags_match = re.search(r'\* Tags:\s*([\w,\s]+)', content)
            tags = [t.strip() for t in tags_match.group(1).split(',')] if tags_match else []

            # Parse related files
            files_match = re.search(r'\* Related Files:\s*([^\n]+)', content)
            files = [f.strip() for f in files_match.group(1).split(',') if f.strip()] if files_match else []

            return LearningRecord(
                id=record_id,
                type=record_type.lower(),
                area=area_match.group(1).lower() if area_match else "unknown",
                priority=priority_match.group(1).lower() if priority_match else "medium",
                status=ReviewStatus(status_match.group(1).lower()) if status_match else ReviewStatus.PENDING,
                logged_at=datetime.fromisoformat(logged_match.group(1)) if logged_match else datetime.now(),
                summary=summary_match.group(1).strip() if summary_match else "",
                details=details_match.group(1).strip() if details_match else "",
                suggested_action=action_match.group(1).strip() if action_match else "",
                source=source_match.group(1).lower() if source_match else "unknown",
                related_files=files,
                tags=tags,
            )
        except Exception as e:
            print(f"[LearningParser] Failed to parse record {record_id}: {e}")
            return None


class LearningReviewScheduler:
    """Scheduler for periodic learning record reviews."""

    def __init__(
        self,
        learnings_dir: str = ".learnings",
        memory_path: str = "memory/memory.md",
        review_interval_hours: int = 24,
        auto_start: bool = False,
    ):
        self.learnings_dir = Path(learnings_dir)
        self.memory_path = Path(memory_path)
        self.review_interval = timedelta(hours=review_interval_hours)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_review: Optional[datetime] = None
        self._callbacks: List[Callable[[ReviewReport], None]] = []

        if auto_start:
            self.start()

    def start(self) -> None:
        """Start the review scheduler in background thread."""
        if self._thread and self._thread.is_alive():
            print("[LearningReviewScheduler] Already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[LearningReviewScheduler] Started (interval: {self.review_interval})")

    def stop(self) -> None:
        """Stop the review scheduler."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        print("[LearningReviewScheduler] Stopped")

    def _run(self) -> None:
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            try:
                self._perform_review()
            except Exception as e:
                print(f"[LearningReviewScheduler] Review failed: {e}")

            # Wait for next interval or until stopped
            self._stop_event.wait(self.review_interval.total_seconds())

    def _perform_review(self) -> None:
        """Perform a review cycle."""
        now = datetime.now()
        period_start = self._last_review or now - self.review_interval

        # Load all learning records
        records = self._load_all_records()

        if not records:
            print("[LearningReviewScheduler] No records to review")
            self._last_review = now
            return

        # Generate report
        report = self._generate_report(records, period_start, now)

        # Append to memory.md
        self._append_to_memory(report)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(report)
            except Exception as e:
                print(f"[LearningReviewScheduler] Callback error: {e}")

        self._last_review = now
        print(f"[LearningReviewScheduler] Review completed: {len(records)} records reviewed")

    def _load_all_records(self) -> List[LearningRecord]:
        """Load all learning records from .learnings directory."""
        all_records = []

        if not self.learnings_dir.exists():
            return all_records

        for filepath in self.learnings_dir.glob("*.md"):
            records = LearningParser.parse_file(filepath)
            all_records.extend(records)

        return all_records

    def _generate_report(
        self,
        records: List[LearningRecord],
        period_start: datetime,
        period_end: datetime,
    ) -> ReviewReport:
        """Generate review report from records."""
        by_type: Dict[str, int] = {}
        by_area: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        pending_high_priority: List[LearningRecord] = []

        for record in records:
            by_type[record.type] = by_type.get(record.type, 0) + 1
            by_area[record.area] = by_area.get(record.area, 0) + 1
            by_status[record.status.value] = by_status.get(record.status.value, 0) + 1

            if record.status == ReviewStatus.PENDING and record.priority == "high":
                pending_high_priority.append(record)

        # Sort high priority by logged date
        pending_high_priority.sort(key=lambda r: r.logged_at)

        # Generate summary
        summary_parts = [
            f"共 {len(records)} 条学习记录",
            f"按类型: {', '.join(f'{k}({v})' for k, v in sorted(by_type.items()))}",
            f"按领域: {', '.join(f'{k}({v})' for k, v in sorted(by_area.items()))}",
            f"待审核: {by_status.get('pending', 0)} 条",
        ]
        if pending_high_priority:
            summary_parts.append(f"高优先级待审核: {len(pending_high_priority)} 条")

        # Generate recommendations
        recommendations = []
        if pending_high_priority:
            recommendations.append(
                f"建议优先审核 {len(pending_high_priority)} 条高优先级记录"
            )
        if by_type.get("correction", 0) > 0:
            recommendations.append(
                f"有 {by_type['correction']} 条修正记录，建议确认是否已应用到代码"
            )
        if by_status.get("pending", 0) > 10:
            recommendations.append(
                "待审核记录较多，建议进行批量审核"
            )

        return ReviewReport(
            generated_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            total_records=len(records),
            by_type=by_type,
            by_area=by_area,
            by_status=by_status,
            pending_high_priority=pending_high_priority,
            summary="\n".join(summary_parts),
            recommendations=recommendations,
        )

    def _append_to_memory(self, report: ReviewReport) -> None:
        """Append review report to memory.md."""
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        lines.append("")
        lines.append(f"---")
        lines.append(f"## 学习记录审核报告")
        lines.append(f"")
        lines.append(f"**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**审核周期**: {report.period_start.strftime('%Y-%m-%d %H:%M')} ~ {report.period_end.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"")
        lines.append(f"### 统计概览")
        lines.append(f"- 总记录数: {report.total_records}")
        lines.append(f"- 按类型: {json.dumps(report.by_type, ensure_ascii=False, indent=2)}")
        lines.append(f"- 按领域: {json.dumps(report.by_area, ensure_ascii=False, indent=2)}")
        lines.append(f"- 按状态: {json.dumps(report.by_status, ensure_ascii=False, indent=2)}")
        lines.append(f"")

        if report.pending_high_priority:
            lines.append(f"### 高优先级待审核记录 ({len(report.pending_high_priority)} 条)")
            for record in report.pending_high_priority[:5]:  # Limit to 5
                lines.append(f"")
                lines.append(f"**[{record.id}]** {record.summary}")
                lines.append(f"- 类型: {record.type} | 领域: {record.area} | 优先级: {record.priority}")
                lines.append(f"- 记录时间: {record.logged_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append(f"- 建议操作: {record.suggested_action}")
            if len(report.pending_high_priority) > 5:
                lines.append(f"- ... 还有 {len(report.pending_high_priority) - 5} 条")
            lines.append(f"")

        if report.recommendations:
            lines.append(f"### 审核建议")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append(f"")

        lines.append(f"---")
        lines.append("")

        # Append to file
        with open(self.memory_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"[LearningReviewScheduler] Report appended to {self.memory_path}")

    def trigger_review(self) -> ReviewReport:
        """Manually trigger a review immediately."""
        records = self._load_all_records()
        now = datetime.now()
        period_start = self._last_review or now - self.review_interval
        report = self._generate_report(records, period_start, now)
        self._append_to_memory(report)
        self._last_review = now
        return report

    def get_pending_records(
        self,
        area: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 10,
    ) -> List[LearningRecord]:
        """Get pending learning records with optional filters."""
        records = self._load_all_records()
        filtered = [r for r in records if r.status == ReviewStatus.PENDING]

        if area:
            filtered = [r for r in filtered if r.area == area]
        if priority:
            filtered = [r for r in filtered if r.priority == priority]

        # Sort by priority (high first) then by date
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda r: (priority_order.get(r.priority, 1), r.logged_at))

        return filtered[:limit]

    def update_record_status(
        self,
        record_id: str,
        new_status: ReviewStatus,
        review_notes: str = "",
    ) -> bool:
        """Update the status of a learning record."""
        # Find the file containing this record
        if not self.learnings_dir.exists():
            return False

        for filepath in self.learnings_dir.glob("*.md"):
            content = filepath.read_text(encoding="utf-8")

            if record_id not in content:
                continue

            # Update status in content
            pattern = rf'(\*\*Status\*\*:\s*)\w+'
            replacement = rf'\g<1>{new_status.value}'
            new_content = re.sub(pattern, replacement, content)

            # Add review notes if provided
            if review_notes:
                review_section = f"\n### Review Notes\n{review_notes}\n"
                if "### Suggested Action" in new_content:
                    new_content = new_content.replace(
                        "### Suggested Action",
                        f"{review_section}### Suggested Action"
                    )

            # Write back
            filepath.write_text(new_content, encoding="utf-8")
            print(f"[LearningReviewScheduler] Updated {record_id} status to {new_status.value}")
            return True

        return False

    def on_review_complete(self, callback: Callable[[ReviewReport], None]) -> None:
        """Register a callback to be called when review completes."""
        self._callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        records = self._load_all_records()
        return {
            "total_records": len(records),
            "last_review": self._last_review.isoformat() if self._last_review else None,
            "next_review_in_seconds": (
                (self.review_interval - (datetime.now() - self._last_review)).total_seconds()
                if self._last_review else self.review_interval.total_seconds()
            ),
            "is_running": self._thread is not None and self._thread.is_alive(),
            "by_type": {
                r.type: sum(1 for rec in records if rec.type == r.type)
                for r in records
            },
            "by_status": {
                s.value: sum(1 for rec in records if rec.status == s)
                for s in ReviewStatus
            },
        }


# Global scheduler instance
_scheduler: Optional[LearningReviewScheduler] = None


def get_learning_reviewer(
    learnings_dir: str = ".learnings",
    memory_path: str = "memory/memory.md",
    review_interval_hours: int = 24,
    auto_start: bool = False,
) -> LearningReviewScheduler:
    """Get or create global learning reviewer instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = LearningReviewScheduler(
            learnings_dir=learnings_dir,
            memory_path=memory_path,
            review_interval_hours=review_interval_hours,
            auto_start=auto_start,
        )
    return _scheduler