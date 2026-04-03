import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def _get_memory_path(user_id: Optional[str] = None) -> Path:
    """获取记忆文件路径，如果提供了 user_id 则使用用户特定目录"""
    if user_id:
        # 使用用户特定的记忆目录: data/user_{user_id}/memory/state.json
        data_root = Path(__file__).parent.parent.parent / "data"
        return data_root / f"user_{user_id}" / "memory" / "state.json"
    else:
        # 默认使用全局记忆目录
        return Path(__file__).parent.parent.parent / "memory" / "state.json"


def _load_state(user_id: Optional[str] = None) -> Dict[str, Any]:
    memory_path = _get_memory_path(user_id)
    if memory_path.exists():
        try:
            return json.loads(memory_path.read_text(encoding="utf-8"))
        except:
            pass
    return {
        "table_schemas": {},
        "metric_definitions": {},
        "business_background": [],
    }


def _save_state(state: Dict[str, Any], user_id: Optional[str] = None) -> None:
    memory_path = _get_memory_path(user_id)
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def run(
    memory_type: str,
    key: str,
    value: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    更新结构化记忆

    参数:
        memory_type: 记忆类型 (table_schema, metric_definition, business_background)
        key: 键
        value: 值
        user_id: 用户ID (可选，如果提供则保存到用户特定的记忆目录)
    """
    if memory_type not in ["table_schema", "metric_definition", "business_background"]:
        return {
            "success": False,
            "error": f"Invalid memory_type: {memory_type}. Must be one of: table_schema, metric_definition, business_background",
        }

    state = _load_state(user_id)

    if memory_type == "table_schema":
        if "table_schemas" not in state:
            state["table_schemas"] = {}
        state["table_schemas"][key] = value
        
    elif memory_type == "metric_definition":
        if "metric_definitions" not in state:
            state["metric_definitions"] = {}
        state["metric_definitions"][key] = value
        
    elif memory_type == "business_background":
        if "business_background" not in state:
            state["business_background"] = []
        if value not in state["business_background"]:
            state["business_background"].append(value)

    _save_state(state, user_id)

    return {
        "success": True,
        "memory_type": memory_type,
        "key": key,
        "value": value,
        "user_id": user_id,
        "message": f"Memory updated: {memory_type}.{key}",
    }


SKILL = {
    "name": "update_memory",
    "description": "自动更新结构化记忆文件，包括表结构、指标定义、业务背景等。支持用户隔离存储。",
    "inputs": {
        "memory_type": "str (必需) - 记忆类型: table_schema, metric_definition, business_background",
        "key": "str (必需) - 键 (表名/指标名)",
        "value": "str (必需) - 值 (定义/描述)",
        "user_id": "str (可选) - 用户ID，如果提供则保存到用户特定的记忆目录",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
