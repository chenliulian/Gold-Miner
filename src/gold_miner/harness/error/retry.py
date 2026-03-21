"""Retry Policy - 重试策略"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, Type


class RetryStrategy(str, Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


@dataclass
class RetryPolicy:
    """
    重试策略配置

    属性：
    - max_attempts: 最大重试次数
    - initial_delay: 初始延迟（秒）
    - max_delay: 最大延迟（秒）
    - strategy: 重试策略
    - retryable_errors: 可重试的错误类型
    """
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retryable_errors: tuple = field(
        default_factory=lambda: ("timeout", "connection", "rate_limit")
    )

    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (2 ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        else:
            delay = self.initial_delay

        return min(delay, self.max_delay)

    def is_retryable(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_str = str(error).lower()
        for pattern in self.retryable_errors:
            if pattern.lower() in error_str:
                return True
        return False


@dataclass
class RetryAttempt:
    """重试记录"""
    attempt: int
    delay: float
    error: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class RetryManager:
    """
    重试管理器

    使用方式：
    ```python
    policy = RetryPolicy(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
    manager = RetryManager(policy)

    result = manager.execute_with_retry(my_function, arg1, arg2)
    ```
    """

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
        self._attempts: list[RetryAttempt] = []

    @property
    def attempts(self) -> list[RetryAttempt]:
        return self._attempts

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数，支持重试

        返回：(result, success)
        """
        last_error = None

        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                return result, True
            except Exception as e:
                last_error = e

                if attempt >= self.policy.max_attempts:
                    break

                if not self.policy.is_retryable(e):
                    break

                delay = self.policy.calculate_delay(attempt)
                self._attempts.append(RetryAttempt(
                    attempt=attempt,
                    delay=delay,
                    error=str(e)
                ))

                time.sleep(delay)

        return None, False

    def execute_with_retry_callback(
        self,
        func: Callable,
        on_retry: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> Any:
        """执行函数，支持重试和回调"""
        last_error = None

        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                return result, True, None
            except Exception as e:
                last_error = e

                if attempt >= self.policy.max_attempts:
                    break

                if not self.policy.is_retryable(e):
                    break

                delay = self.policy.calculate_delay(attempt)
                self._attempts.append(RetryAttempt(
                    attempt=attempt,
                    delay=delay,
                    error=str(e)
                ))

                if on_retry:
                    on_retry(attempt, delay, str(e))

                time.sleep(delay)

        if on_failure:
            on_failure(last_error)

        return None, False, last_error

    def reset(self) -> None:
        """重置重试记录"""
        self._attempts.clear()

    def get_retry_summary(self) -> str:
        """获取重试摘要"""
        if not self._attempts:
            return "No retries"
        lines = [f"Total retries: {len(self._attempts)}"]
        for attempt in self._attempts:
            lines.append(f"  Attempt {attempt.attempt}: delay={attempt.delay}s, error={attempt.error[:50]}")
        return "\n".join(lines)