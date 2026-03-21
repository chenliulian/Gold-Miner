"""Tool Registry - 统一的工具注册与管理"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class ActionType(str, Enum):
    RUN_SQL = "run_sql"
    USE_SKILL = "use_skill"
    SEARCH_SKILLS = "search_skills"
    FINAL = "final"


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)
    handler: Optional[Callable] = None
    invisible_context: bool = False
    hooks: List[str] = field(default_factory=list)

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """验证参数"""
        missing = [p for p in self.required_params if p not in params]
        if missing:
            return False, f"Missing required params: {missing}"
        return True, ""


@dataclass
class ToolCall:
    action: str
    args: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    visible_context: bool = True


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    visible_context: bool = True


class ToolRegistry:
    """
    工具注册表 - 统一管理所有可用工具

    解决 Hallucinated Tool Calls 问题：
    1. 严格定义工具签名
    2. 参数验证
    3. 文档化工具能力
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._actions: Dict[str, str] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """注册默认工具"""
        self.register_tool(Tool(
            name="run_sql",
            description="Execute SQL query against MaxCompute",
            parameters={
                "sql": {"type": "string", "description": "SQL query to execute"}
            },
            required_params=["sql"]
        ))

        self.register_tool(Tool(
            name="use_skill",
            description="Call a named skill with arguments",
            parameters={
                "skill": {"type": "string", "description": "Skill name"},
                "skill_args": {"type": "object", "description": "Skill arguments"}
            },
            required_params=["skill"]
        ))

        self.register_tool(Tool(
            name="search_skills",
            description="Search skills directory for relevant skills",
            parameters={
                "search_keywords": {"type": "string", "description": "Keywords to search"}
            },
            required_params=["search_keywords"]
        ))

        self.register_tool(Tool(
            name="final",
            description="Provide the final report",
            parameters={
                "report_markdown": {"type": "string", "description": "Report content in markdown"}
            },
            required_params=["report_markdown"]
        ))

    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
        self._actions[tool.name] = tool.name

    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self._tools.keys())

    def validate_action(self, action: str, args: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证 Action 是否合法

        返回：(is_valid, error_message)
        """
        tool = self._tools.get(action)
        if not tool:
            return False, f"Unknown action: {action}. Available: {self.list_tools()}"

        return tool.validate_params(args)

    def parse_action_dict(self, action_dict: Dict[str, Any]) -> ToolCall:
        """
        解析 Action 字典

        处理不同的 action 格式，统一返回 ToolCall
        """
        action = action_dict.get("action", "")
        args = {}

        if action == "run_sql":
            args = {"sql": action_dict.get("sql", "")}
        elif action == "use_skill":
            args = {
                "skill": action_dict.get("skill", ""),
                "skill_args": action_dict.get("skill_args", {})
            }
        elif action == "search_skills":
            args = {"search_keywords": action_dict.get("search_keywords", "")}
        elif action == "final":
            args = {"report_markdown": action_dict.get("report_markdown", "")}

        return ToolCall(
            action=action,
            args=args,
            notes=action_dict.get("notes"),
            visible_context=action_dict.get("visible_context", True)
        )

    def get_tools_description(self) -> str:
        """获取工具描述（用于 prompt）"""
        lines = []
        for name, tool in self._tools.items():
            params_str = ", ".join(tool.required_params)
            lines.append(f"- {tool.name}: {tool.description} (params: {params_str})")
        return "\n".join(lines)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取工具 schema（用于 prompt engineering）"""
        schemas = []
        for tool in self._tools.values():
            schema = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": tool.required_params
                }
            }
            schemas.append(schema)
        return schemas