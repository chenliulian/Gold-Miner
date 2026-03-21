"""Tool Executor - 工具执行器"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass

from .registry import ToolCall, ToolResult, ToolRegistry


class ToolExecutor:
    """
    工具执行器 - 统一执行工具调用

    职责：
    1. 验证工具参数
    2. 执行工具
    3. 捕获异常
    4. 返回标准化结果
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self._handlers: Dict[str, Callable] = {}

    def register_handler(self, action: str, handler: Callable) -> None:
        """注册工具处理器"""
        self._handlers[action] = handler

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        执行工具调用

        流程：
        1. 验证参数
        2. 调用处理器
        3. 捕获异常
        4. 返回结果
        """
        is_valid, error = self.registry.validate_action(tool_call.action, tool_call.args)
        if not is_valid:
            return ToolResult(
                success=False,
                error=f"Validation failed: {error}",
                visible_context=tool_call.visible_context
            )

        handler = self._handlers.get(tool_call.action)
        if not handler:
            return ToolResult(
                success=False,
                error=f"No handler registered for action: {tool_call.action}",
                visible_context=tool_call.visible_context
            )

        try:
            result = handler(**tool_call.args)
            return ToolResult(
                success=True,
                data=result,
                visible_context=tool_call.visible_context
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                visible_context=tool_call.visible_context
            )

    def execute_dict(self, action_dict: Dict[str, Any]) -> ToolResult:
        """直接执行 action 字典"""
        tool_call = self.registry.parse_action_dict(action_dict)
        return self.execute(tool_call)