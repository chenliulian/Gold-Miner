"""Circuit Breaker - 熔断器模式"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """
    熔断器 - 防止连续失败导致系统崩溃

    状态机：
    1. CLOSED（正常）：请求正常通过
    2. OPEN（熔断）：请求直接失败，快速返回
    3. HALF_OPEN（半开）：尝试恢复

    配置：
    - failure_threshold: 打开熔断的失败次数
    - recovery_timeout: 尝试恢复的等待时间（秒）
    - success_threshold: 半开状态下确认恢复的成功次数
    """

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2

    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _failure_count: int = field(default=0, repr=False)
    _success_count: int = field(default=0, repr=False)
    _last_failure_time: Optional[float] = field(default=None, repr=False)
    _opened_at: Optional[float] = field(default=None, repr=False)

    def call(self, func: Callable, *args, **kwargs):
        """通过熔断器执行函数"""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            else:
                raise CircuitOpenError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """记录成功"""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._reset()
        else:
            self._failure_count = 0

    def _on_failure(self) -> None:
        """记录失败"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._open()

    def _open(self) -> None:
        """打开熔断器"""
        self._state = CircuitState.OPEN
        self._opened_at = time.time()

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试恢复"""
        if self._opened_at is None:
            return True
        return (time.time() - self._opened_at) >= self.recovery_timeout

    def _reset(self) -> None:
        """重置熔断器"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._opened_at = None

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    def is_closed(self) -> bool:
        return self._state == CircuitState.CLOSED

    def is_half_open(self) -> bool:
        return self._state == CircuitState.HALF_OPEN

    def summary(self) -> str:
        return (
            f"CircuitBreaker(state={self._state.value}, "
            f"failures={self._failure_count}/{self.failure_threshold}, "
            f"successes={self._success_count}/{self.success_threshold})"
        )


class CircuitOpenError(Exception):
    """熔断器打开异常"""
    pass