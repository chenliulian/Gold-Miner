from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import os


LEARNINGS_DIR = Path(__file__).parent / "references"
LEARNINGS_FILE = LEARNINGS_DIR / "LEARNINGS.md"
ERRORS_FILE = LEARNINGS_DIR / "ERRORS.md"
FEATURE_REQUESTS_FILE = LEARNINGS_DIR / "FEATURE_REQUESTS.md"


def _ensure_learnings_dir():
    LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)
    if not LEARNINGS_FILE.exists():
        _create_file(LEARNINGS_FILE, _LEARNINGS_TEMPLATE)
    if not ERRORS_FILE.exists():
        _create_file(ERRORS_FILE, _ERRORS_TEMPLATE)
    if not FEATURE_REQUESTS_FILE.exists():
        _create_file(FEATURE_REQUESTS_FILE, _FEATURE_REQUESTS_TEMPLATE)


def _create_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


_LEARNINGS_TEMPLATE = """# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice
**Areas**: frontend | backend | infra | tests | docs | config | odps

---
"""

_ERRORS_TEMPLATE = """# Errors

Command failures, exceptions, and unexpected errors logged for debugging.

**Areas**: frontend | backend | infra | tests | docs | config | odps

---
"""

_FEATURE_REQUESTS_TEMPLATE = """# Feature Requests

User-requested capabilities and feature ideas.

---
"""


def run(
    category: str = "insight",
    summary: str = "",
    details: str = "",
    suggested_action: str = "",
    area: str = "backend",
    source: str = "conversation",
    related_files: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    priority: str = "medium",
    entry_type: str = "learning",
) -> Dict[str, Any]:
    """
    记录学习内容、错误和修正，实现持续改进

    参数:
        category: 学习类别 - correction | insight | knowledge_gap | best_practice
        summary: 一句话描述
        details: 详细上下文
        suggested_action: 建议的修复或改进
        area: 领域 - frontend | backend | infra | tests | docs | config | odps
        source: 来源 - conversation | error | user_feedback
        related_files: 相关文件列表
        tags: 标签列表
        priority: 优先级 - low | medium | high | critical
        entry_type: 条目类型 - learning | error | feature_request
    """
    _ensure_learnings_dir()

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    entry_id = _generate_entry_id(entry_type)

    if entry_type == "error":
        content = _build_error_entry(entry_id, timestamp, summary, details, suggested_action, area, priority, source, related_files)
        file_path = ERRORS_FILE
    elif entry_type == "feature_request":
        content = _build_feature_entry(entry_id, timestamp, summary, details, suggested_action, area, priority)
        file_path = FEATURE_REQUESTS_FILE
    else:
        content = _build_learning_entry(entry_id, timestamp, category, summary, details, suggested_action, area, priority, source, related_files, tags)
        file_path = LEARNINGS_FILE

    with open(file_path, "a", encoding="utf-8") as f:
        f.write("\n" + content)

    return {
        "status": "success",
        "entry_id": entry_id,
        "entry_type": entry_type,
        "file": str(file_path),
        "message": f"Logged {entry_type} to {file_path.name}",
    }


def _generate_entry_id(entry_type: str) -> str:
    prefix = {"learning": "LRN", "error": "ERR", "feature_request": "FRQ"}[entry_type]
    date_str = datetime.now().strftime("%Y%m%d")
    import random
    suffix = str(random.randint(1, 999)).zfill(3)
    return f"{prefix}-{date_str}-{suffix}"


def _build_learning_entry(
    entry_id: str,
    timestamp: str,
    category: str,
    summary: str,
    details: str,
    suggested_action: str,
    area: str,
    priority: str,
    source: str,
    related_files: Optional[List[str]],
    tags: Optional[List[str]],
) -> str:
    files_str = ", ".join(related_files) if related_files else ""
    tags_str = ", ".join(tags) if tags else ""

    return f"""## [{entry_id}] {category}

**Logged**: {timestamp}
**Priority**: {priority}
**Status**: pending
**Area**: {area}

### Summary
{summary}

### Details
{details}

### Suggested Action
{suggested_action}

### Metadata
- Source: {source}
- Related Files: {files_str}
- Tags: {tags_str}

---
"""


def _build_error_entry(
    entry_id: str,
    timestamp: str,
    summary: str,
    details: str,
    suggested_action: str,
    area: str,
    priority: str,
    source: str,
    related_files: Optional[List[str]],
) -> str:
    files_str = ", ".join(related_files) if related_files else ""

    return f"""## [{entry_id}] skill_or_command

**Logged**: {timestamp}
**Priority**: {priority}
**Status**: pending
**Area**: {area}

### Summary
{summary}

### Error
```
{details}
```

### Context
- Source: {source}

### Suggested Fix
{suggested_action}

### Metadata
- Reproducible: unknown
- Related Files: {files_str}

---
"""


def _build_feature_entry(
    entry_id: str,
    timestamp: str,
    summary: str,
    details: str,
    suggested_action: str,
    area: str,
    priority: str,
) -> str:
    return f"""## [{entry_id}]

**Logged**: {timestamp}
**Priority**: {priority}
**Status**: pending
**Area**: {area}

### Summary
{summary}

### Details
{details}

### Suggested Implementation
{suggested_action}

---
"""


def review() -> Dict[str, Any]:
    """查看所有学习记录"""
    _ensure_learnings_dir()

    result = {
        "learnings": _read_file(LEARNINGS_FILE),
        "errors": _read_file(ERRORS_FILE),
        "feature_requests": _read_file(FEATURE_REQUESTS_FILE),
    }
    return result


def _read_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


SKILL = {
    "name": "self_improvement",
    "description": "记录学习内容、错误和修正，实现持续改进。当命令失败、用户纠正你、请求不存在的功能、外部API失败、知识过时或发现更好的方法时使用。",
    "inputs": {
        "entry_type": "str (可选) - 条目类型: 'learning'(默认), 'error', 'feature_request'",
        "category": "str (可选) - 学习类别: correction, insight, knowledge_gap, best_practice",
        "summary": "str (必需) - 一句话描述",
        "details": "str (可选) - 详细上下文",
        "suggested_action": "str (可选) - 建议的修复或改进",
        "area": "str (可选) - 领域: frontend, backend, infra, tests, docs, config, odps",
        "priority": "str (可选) - 优先级: low, medium, high, critical",
        "source": "str (可选) - 来源: conversation, error, user_feedback",
        "related_files": "list (可选) - 相关文件列表",
        "tags": "list (可选) - 标签列表",
    },
    "run": run,
    "review": review,
}
