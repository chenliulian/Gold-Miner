from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import os


# 学习记录保存到项目根目录的 .learnings 目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
LEARNINGS_DIR = PROJECT_ROOT / ".learnings"
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


def _generate_content_fingerprint(summary: str, details: str) -> str:
    """生成内容指纹用于去重"""
    import hashlib
    # 提取关键信息生成指纹
    content = f"{summary}:{details[:200]}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()[:16]


def _is_duplicate(file_path: Path, fingerprint: str) -> bool:
    """检查文件是否已包含相同指纹的记录"""
    if not file_path.exists():
        return False
    
    try:
        content = file_path.read_text(encoding="utf-8")
        # 检查是否已存在相同指纹（存储在Metadata中）
        return f"Fingerprint: {fingerprint}" in content
    except Exception:
        return False


def _get_learnings_paths(user_id: str = "") -> Dict[str, Path]:
    """获取学习记录文件路径，支持用户隔离"""
    if user_id:
        # 使用用户特定目录
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        from gold_miner.user_data import get_user_data_manager

        user_data_manager = get_user_data_manager()
        paths = user_data_manager.get_user_paths(user_id)
        learnings_dir = Path(paths.learnings_dir)
        learnings_dir.mkdir(parents=True, exist_ok=True)

        return {
            "learnings_file": learnings_dir / "LEARNINGS.md",
            "errors_file": learnings_dir / "ERRORS.md",
            "feature_requests_file": learnings_dir / "FEATURE_REQUESTS.md",
        }
    else:
        # 使用默认目录（向后兼容）
        return {
            "learnings_file": LEARNINGS_FILE,
            "errors_file": ERRORS_FILE,
            "feature_requests_file": FEATURE_REQUESTS_FILE,
        }


def _ensure_user_learnings_dir(paths: Dict[str, Path]) -> None:
    """确保用户学习记录目录和文件存在"""
    for file_path in paths.values():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            if "ERRORS" in file_path.name:
                _create_file(file_path, _ERRORS_TEMPLATE)
            elif "FEATURE" in file_path.name:
                _create_file(file_path, _FEATURE_REQUESTS_TEMPLATE)
            else:
                _create_file(file_path, _LEARNINGS_TEMPLATE)


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
    user_id: str = "",
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
        user_id: 用户ID，用于数据隔离
    """
    # 获取学习记录路径（支持用户隔离）
    paths = _get_learnings_paths(user_id)
    _ensure_user_learnings_dir(paths)

    # 生成内容指纹用于去重
    fingerprint = _generate_content_fingerprint(summary, details)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    entry_id = _generate_entry_id(entry_type)

    # 根据 entry_type 选择对应的文件路径
    if entry_type == "error":
        content = _build_error_entry(entry_id, timestamp, summary, details, suggested_action, area, priority, source, related_files, fingerprint)
        file_path = paths["errors_file"]
    elif entry_type == "feature_request":
        content = _build_feature_entry(entry_id, timestamp, summary, details, suggested_action, area, priority)
        file_path = paths["feature_requests_file"]
    else:
        content = _build_learning_entry(entry_id, timestamp, category, summary, details, suggested_action, area, priority, source, related_files, tags, fingerprint)
        file_path = paths["learnings_file"]

    # 检查是否重复
    if _is_duplicate(file_path, fingerprint):
        return {
            "status": "skipped",
            "entry_id": entry_id,
            "entry_type": entry_type,
            "file": str(file_path),
            "message": f"Duplicate entry skipped (same content fingerprint)",
        }

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
    fingerprint: str = "",
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
- Fingerprint: {fingerprint}

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
    fingerprint: str = "",
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
- Fingerprint: {fingerprint}

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
    "invisible_context": False,
}
