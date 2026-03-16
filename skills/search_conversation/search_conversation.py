import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

MEMORY_DIR = Path(__file__).parent.parent.parent / "memory"


def _get_conversation_files() -> List[Path]:
    if not MEMORY_DIR.exists():
        return []
    return sorted(MEMORY_DIR.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def run(query: str = "", limit: int = 5) -> Dict[str, Any]:
    """
    检索历史对话记录

    参数:
        query: 搜索关键词 (可选)
        limit: 返回数量 (默认 5)
    """
    files = _get_conversation_files()
    
    if not files:
        return {
            "success": True,
            "conversations": [],
            "message": "No conversation history found",
        }
    
    results = []
    for file_path in files[:limit]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            content = json.dumps(data, ensure_ascii=False)
            
            if query and query.lower() not in content.lower():
                continue
            
            session_id = file_path.stem.replace("session_", "")
            
            recent_steps = data.get("recent_steps", [])
            first_user_msg = ""
            for step in recent_steps:
                if step.get("role") == "user":
                    first_user_msg = step.get("content", "")[:100]
                    break
            
            results.append({
                "session_id": session_id,
                "file": file_path.name,
                "preview": first_user_msg,
                "steps_count": len(recent_steps),
            })
            
            if len(results) >= limit:
                break
                
        except Exception as e:
            continue
    
    return {
        "success": True,
        "query": query,
        "conversations": results,
        "total_found": len(results),
    }


SKILL = {
    "name": "search_conversation",
    "description": "检索历史对话记录，支持按关键词搜索或查看最近的对话",
    "inputs": {
        "query": "str (可选) - 搜索关键词",
        "limit": "int (可选) - 返回数量，默认 5",
    },
    "run": run,
    "invisible_context": True,
    "hooks": [],
}
