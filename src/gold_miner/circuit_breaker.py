"""Circuit breaker pattern for fault tolerance."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    success_threshold: int = 2
    expected_exception: Type[Exception] = Exception


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        with self._lock:
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call a function with circuit breaker protection."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
                else:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service temporarily unavailable."
                    )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.name}' is HALF_OPEN "
                        f"and max calls reached."
                    )
                self._half_open_calls += 1

        # Execute the function outside the lock
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.config.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._reset()
            else:
                self._failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN

    def _reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "last_failure_time": self._last_failure_time,
            }

    def force_open(self) -> None:
        """Force circuit breaker to open state."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._last_failure_time = time.time()

    def force_close(self) -> None:
        """Force circuit breaker to closed state."""
        with self._lock:
            self._reset()


def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    expected_exception: Type[Exception] = Exception,
):
    """
    Decorator for adding circuit breaker to functions.

    Args:
        name: Circuit breaker name (defaults to function name)
        failure_threshold: Number of failures before opening
        recovery_timeout: Time before attempting recovery
        expected_exception: Exception type to count as failure
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
    )

    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        breaker = CircuitBreaker(breaker_name, config)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        # Attach circuit breaker instance for monitoring
        wrapper._circuit_breaker = breaker
        return wrapper

    return decorator


# Global circuit breakers registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get a circuit breaker by name."""
    with _breakers_lock:
        return _circuit_breakers.get(name)


def register_circuit_breaker(name: str, breaker: CircuitBreaker) -> None:
    """Register a circuit breaker."""
    with _breakers_lock:
        _circuit_breakers[name] = breaker


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    with _breakers_lock:
        return dict(_circuit_breakers)


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers."""
    with _breakers_lock:
        for breaker in _circuit_breakers.values():
            breaker.force_close()
