"""Context compressor implementations"""

from __future__ import annotations

from typing import List, Callable, Optional
from .context_manager import Message, MessageRole


class ContextCompressor:
    """
    上下文压缩器 - 提供多种压缩策略
    """

    def __init__(self, llm_caller: Optional[Callable] = None):
        self._llm_caller = llm_caller

    def compress_messages(
        self,
        messages: List[Message],
        max_count: int = 10,
        strategy: str = "drop_old"
    ) -> List[Message]:
        """
        压缩消息列表

        策略：
        - drop_old: 丢弃最旧的消息
        - drop_small: 丢弃最小的消息
        - summarize: 总结压缩（需要 LLM）
        """
        if len(messages) <= max_count:
            return messages

        if strategy == "drop_old":
            return self._drop_old(messages, max_count)
        elif strategy == "drop_small":
            return self._drop_small(messages, max_count)
        elif strategy == "summarize":
            return self._summarize(messages, max_count)
        else:
            return messages[-max_count:]

    def _drop_old(self, messages: List[Message], max_count: int) -> List[Message]:
        """保留最新的消息"""
        return messages[-max_count:]

    def _drop_small(self, messages: List[Message], max_count: int) -> List[Message]:
        """保留最大的消息"""
        preserved = [m for m in messages if m.role == MessageRole.SYSTEM]
        rest = [m for m in messages if m.role != MessageRole.SYSTEM]
        rest.sort(key=lambda m: len(m.content))
        return preserved + rest[-max_count:]

    def _summarize(self, messages: List[Message], max_count: int) -> List[Message]:
        """总结压缩"""
        if not self._llm_caller:
            return self._drop_old(messages, max_count)

        to_summarize = messages[:-max_count]
        summary = self._llm_caller(
            f"总结以下对话要点，保留关键信息（不超过200字）：\n"
            + "\n".join(f"{m.role.value}: {m.content[:100]}" for m in to_summarize)
        )

        result = [Message(MessageRole.SYSTEM, f"[早期对话摘要] {summary}", {"is_summary": True})]
        result.extend(messages[-max_count:])
        return result