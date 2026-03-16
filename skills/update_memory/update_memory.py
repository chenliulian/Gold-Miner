import json
from pathlib import Path
from typing import Any, Dict

MEMORY_STATE_FILE = Path(__file__).parent.parent.parent / "memory" / "state.json"


def _load_state() -> Dict[str, Any]:
    if MEMORY_STATE_FILE.exists():
        try:
            return json.loads(MEMORY_STATE_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {
        "table_schemas": {},
        "metric_definitions": {},
        "business_background": [],
    }


def _save_state(state: Dict[str, Any]) -> None:
    MEMORY_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def run(
    memory_type: str,
    key: str,
    value: str,
) -> Dict[str, Any]:
    """
    更新结构化记忆

    参数:
        memory_type: 记忆类型 (table_schema, metric_definition, business_background)
        key: 键
        value: 值
    """
    if memory_type not in ["table_schema", "metric_definition", "business_background"]:
        return {
            "success": False,
            "error": f"Invalid memory_type: {memory_type}. Must be one of: table_schema, metric_definition, business_background",
        }

    state = _load_state()

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

    _save_state(state)

    return {
        "success": True,
        "memory_type": memory_type,
        "key": key,
        "value": value,
        "message": f"Memory updated: {memory_type}.{key}",
    }


SKILL = {
    "name": "update_memory",
    "description": "自动更新结构化记忆文件，包括表结构、指标定义、业务背景等",
    "inputs": {
        "memory_type": "str (必需) - 记忆类型: table_schema, metric_definition, business_background",
        "key": "str (必需) - 键 (表名/指标名)",
        "value": "str (必需) - 值 (定义/描述)",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
