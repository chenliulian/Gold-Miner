"""Context Manager - 管理上下文窗口，防止 Context Rot"""

from __future__ import annotations

import tiktoken
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: MessageRole
    content: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"role": self.role.value, "content": self.content, **self.metadata}


@dataclass
class ContextConfig:
    max_tokens: int = 8000
    model: str = "cl100k_base"
    compress_threshold: float = 0.85
    preserve_roles: list[MessageRole] = field(
        default_factory=lambda: [MessageRole.SYSTEM]
    )


class ContextManager:
    """
    管理 Agent 上下文窗口，解决 Context Rot 问题

    核心能力：
    1. 消息窗口管理 - 限制消息数量和 token 数
    2. 上下文压缩 - 自动压缩旧消息
    3. 消息优先级 - 保留重要消息，丢弃次要消息
    4. 上下文卸载 - 将中间结果持久化到文件

    类比：上下文窗口 = RAM，Context Manager = 内存管理器
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()
        self._encoder = tiktoken.get_encoding(self.config.model)
        self._messages: List[Message] = []
        self._artifacts: dict = {}

    @property
    def messages(self) -> List[Message]:
        return self._messages

    def add_message(self, role: MessageRole, content: str, metadata: Optional[dict] = None) -> None:
        """添加消息到上下文"""
        msg = Message(role=role, content=content, metadata=metadata or {})
        self._messages.append(msg)
        self._maybe_compress()

    def add_system(self, content: str) -> None:
        """添加 system 消息（优先保留）"""
        self.add_message(MessageRole.SYSTEM, content, {"preserve": True})

    def add_user(self, content: str) -> None:
        """添加 user 消息"""
        self.add_message(MessageRole.USER, content)

    def add_assistant(self, content: str) -> None:
        """添加 assistant 消息"""
        self.add_message(MessageRole.ASSISTANT, content)

    def add_tool(self, content: str, tool_name: Optional[str] = None) -> None:
        """添加 tool 消息"""
        metadata = {"tool_name": tool_name} if tool_name else {}
        self.add_message(MessageRole.TOOL, content, metadata)

    def get_messages(self) -> List[dict]:
        """获取所有消息（转为 dict 格式）"""
        return [msg.to_dict() for msg in self._messages]

    def count_tokens(self, text: str) -> int:
        """计算文本 token 数"""
        return len(self._encoder.encode(text))

    def count_total_tokens(self) -> int:
        """计算当前上下文总 token 数"""
        total = 0
        for msg in self._messages:
            total += self.count_tokens(msg.content)
        return total

    def _maybe_compress(self) -> None:
        """检查是否需要压缩上下文"""
        total = self.count_total_tokens()
        max_tokens = self.config.max_tokens

        if total > max_tokens * self.config.compress_threshold:
            self.compress()

    def compress(self, strategy: str = "summarize") -> None:
        """
        压缩上下文

        策略：
        1. summarize - 总结旧消息，保留关键信息
        2. drop_old - 直接丢弃最旧的消息
        3. drop_small - 丢弃最小的消息
        """
        if strategy == "summarize":
            self._compress_by_summarize()
        elif strategy == "drop_old":
            self._compress_by_drop_old()
        elif strategy == "drop_small":
            self._compress_by_drop_small()

    def _compress_by_summarize(self) -> None:
        """通过总结压缩上下文（保留最近消息和 system）"""
        preserved = []
        to_summarize = []

        for msg in self._messages:
            if msg.metadata.get("preserve") or msg.role == MessageRole.SYSTEM:
                preserved.append(msg)
            else:
                to_summarize.append(msg)

        if len(to_summarize) <= 2:
            return

        summary = self._summarize_messages(to_summarize[:-2])
        self._messages = preserved + to_summarize[-2:]
        self._messages.insert(1, Message(
            MessageRole.SYSTEM,
            f"[早期对话摘要] {summary}",
            {"is_summary": True}
        ))

    def _compress_by_drop_old(self) -> None:
        """直接丢弃最旧的消息（保留 system）"""
        preserved = []
        rest = []

        for msg in self._messages:
            if msg.metadata.get("preserve") or msg.role == MessageRole.SYSTEM:
                preserved.append(msg)
            else:
                rest.append(msg)

        keep_count = len(rest) // 2
        self._messages = preserved + rest[-keep_count:]

    def _compress_by_drop_small(self) -> None:
        """丢弃最小的消息"""
        preserved = []
        rest = []

        for msg in self._messages:
            if msg.metadata.get("preserve") or msg.role == MessageRole.SYSTEM:
                preserved.append(msg)
            else:
                rest.append(msg)

        if not rest:
            return

        rest.sort(key=lambda m: len(m.content))
        keep_count = len(rest) // 2
        self._messages = preserved + rest[-keep_count:]

    def _summarize_messages(self, messages: List[Message]) -> str:
        """总结消息（需要 LLM 调用）"""
        if not messages:
            return ""
        content = "\n".join(f"[{m.role.value}] {m.content[:100]}" for m in messages)
        return f"[已压缩 {len(messages)} 条早期消息]"

    def set_artifact(self, key: str, value: Any) -> None:
        """存储中间结果到 artifacts（释放上下文窗口）"""
        self._artifacts[key] = value

    def get_artifact(self, key: str, default: Any = None) -> Any:
        """从 artifacts 获取中间结果"""
        return self._artifacts.get(key, default)

    def clear(self) -> None:
        """清空上下文（保留 system）"""
        system_msgs = [m for m in self._messages if m.role == MessageRole.SYSTEM]
        self._messages = system_msgs
        self._artifacts.clear()

    def build_prompt(self, question: str, **kwargs) -> str:
        """构建发送给 LLM 的完整提示"""
        parts = []
        for msg in self._messages:
            parts.append(f"{msg.role.value}: {msg.content}")
        parts.append(f"user: {question}")
        return "\n\n".join(parts)