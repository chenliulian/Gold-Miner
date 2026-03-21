"""Message priority for context management"""

from __future__ import annotations

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional
from .context_manager import Message, MessageRole


class PriorityType(IntEnum):
    CRITICAL = 100
    HIGH = 80
    NORMAL = 50
    LOW = 20
    DISCARDABLE = 0


Priority = PriorityType


@dataclass
class MessagePriority:
    """
    消息优先级计算器

    规则：
    1. SYSTEM 消息 = CRITICAL
    2. 用户明确标记重要的 = HIGH
    3. 工具执行结果（包含错误/关键数据）= HIGH
    4. 中间过程 = LOW
    5. 旧消息 = 可丢弃
    """

    @classmethod
    def calculate(cls, message: Message) -> Priority:
        """计算消息优先级"""
        if message.role == MessageRole.SYSTEM:
            return Priority.CRITICAL

        if message.metadata.get("preserve"):
            return Priority.HIGH

        if message.metadata.get("error"):
            return Priority.HIGH

        if message.metadata.get("result"):
            return Priority.HIGH

        if message.role == MessageRole.TOOL:
            tool_name = message.metadata.get("tool_name", "")
            if "error" in tool_name.lower() or "fail" in tool_name.lower():
                return Priority.HIGH
            return Priority.NORMAL

        if message.metadata.get("is_summary"):
            return Priority.LOW

        if message.metadata.get("is_step"):
            return Priority.LOW

        return Priority.NORMAL

    @classmethod
    def sort_messages(cls, messages: list[Message]) -> list[Message]:
        """按优先级排序消息（高优先级在前）"""
        return sorted(messages, key=lambda m: cls.calculate(m), reverse=True)

    @classmethod
    def filter_discardable(cls, messages: list[Message], threshold: Priority = Priority.DISCARDABLE) -> list[Message]:
        """过滤可丢弃的消息"""
        return [m for m in messages if cls.calculate(m) > threshold]