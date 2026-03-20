"""Rate limiting utilities for API protection."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Callable, Dict, List, Optional, Tuple


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class LimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests: int
    window: int  # in seconds
    strategy: LimitStrategy = LimitStrategy.SLIDING_WINDOW
    burst_size: int = 0  # for token bucket


@dataclass
class RequestRecord:
    """Record of a request for rate limiting."""
    timestamp: float
    count: int = 1


class FixedWindowLimiter:
    """Fixed window rate limiter."""

    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = window
        self.windows: Dict[str, Tuple[int, float]] = {}
        self.lock = Lock()

    def is_allowed(self, key: str) -> Tuple[bool, Dict]:
        """Check if request is allowed."""
        with self.lock:
            current_time = time.time()
            current_window = int(current_time // self.window)

            count, window = self.windows.get(key, (0, 0))

            if window != current_window:
                # New window
                self.windows[key] = (1, current_window)
                return True, {
                    "limit": self.max_requests,
                    "remaining": self.max_requests - 1,
                    "reset": (current_window + 1) * self.window,
                }

            if count >= self.max_requests:
                return False, {
                    "limit": self.max_requests,
                    "remaining": 0,
                    "reset": (current_window + 1) * self.window,
                }

            self.windows[key] = (count + 1, window)
            return True, {
                "limit": self.max_requests,
                "remaining": self.max_requests - count - 1,
                "reset": (current_window + 1) * self.window,
            }


class SlidingWindowLimiter:
    """Sliding window rate limiter."""

    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, key: str) -> Tuple[bool, Dict]:
        """Check if request is allowed."""
        with self.lock:
            current_time = time.time()
            cutoff = current_time - self.window

            # Clean old requests and count recent ones
            self.requests[key] = [
                ts for ts in self.requests[key]
                if ts > cutoff
            ]

            if len(self.requests[key]) >= self.max_requests:
                oldest = min(self.requests[key])
                return False, {
                    "limit": self.max_requests,
                    "remaining": 0,
                    "reset": oldest + self.window,
                }

            self.requests[key].append(current_time)
            return True, {
                "limit": self.max_requests,
                "remaining": self.max_requests - len(self.requests[key]),
                "reset": current_time + self.window,
            }


class TokenBucketLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int, window: int, burst_size: int = 0):
        self.rate = max_requests / window  # tokens per second
        self.burst_size = burst_size or max_requests
        self.buckets: Dict[str, Tuple[float, float]] = {}  # (tokens, last_update)
        self.lock = Lock()

    def is_allowed(self, key: str) -> Tuple[bool, Dict]:
        """Check if request is allowed."""
        with self.lock:
            current_time = time.time()
            tokens, last_update = self.buckets.get(key, (self.burst_size, current_time))

            # Add tokens based on time passed
            time_passed = current_time - last_update
            tokens = min(self.burst_size, tokens + time_passed * self.rate)

            if tokens < 1:
                wait_time = (1 - tokens) / self.rate
                return False, {
                    "limit": int(self.burst_size),
                    "remaining": 0,
                    "reset": current_time + wait_time,
                }

            tokens -= 1
            self.buckets[key] = (tokens, current_time)
            return True, {
                "limit": int(self.burst_size),
                "remaining": int(tokens),
                "reset": current_time + (self.burst_size - tokens) / self.rate,
            }


class RateLimiter:
    """Main rate limiter class."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig(
            requests=100,
            window=60,
            strategy=LimitStrategy.SLIDING_WINDOW,
        )
        self._init_limiter()

    def _init_limiter(self):
        """Initialize the appropriate limiter based on strategy."""
        if self.config.strategy == LimitStrategy.FIXED_WINDOW:
            self.limiter = FixedWindowLimiter(
                self.config.requests,
                self.config.window,
            )
        elif self.config.strategy == LimitStrategy.TOKEN_BUCKET:
            self.limiter = TokenBucketLimiter(
                self.config.requests,
                self.config.window,
                self.config.burst_size,
            )
        else:  # Default to sliding window
            self.limiter = SlidingWindowLimiter(
                self.config.requests,
                self.config.window,
            )

    def is_allowed(self, key: str) -> Tuple[bool, Dict]:
        """Check if request is allowed for the given key."""
        return self.limiter.is_allowed(key)

    def check_rate_limit(self, key: str) -> None:
        """Check rate limit and raise exception if exceeded."""
        allowed, info = self.is_allowed(key)
        if not allowed:
            raise RateLimitExceeded(
                f"Rate limit exceeded. Try again after {info['reset']:.0f}"
            )


def rate_limit(
    requests: int = 100,
    window: int = 60,
    strategy: LimitStrategy = LimitStrategy.SLIDING_WINDOW,
    key_func: Optional[Callable] = None,
):
    """
    Decorator for rate limiting functions.

    Args:
        requests: Maximum number of requests allowed
        window: Time window in seconds
        strategy: Rate limiting strategy
        key_func: Function to extract key from arguments
    """
    limiter = RateLimiter(RateLimitConfig(
        requests=requests,
        window=window,
        strategy=strategy,
    ))

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default to function name
                key = func.__name__

            allowed, info = limiter.is_allowed(key)
            if not allowed:
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {key}. "
                    f"Try again after {info['reset']:.0f} seconds."
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global rate limiter instances
_default_limiter: Optional[RateLimiter] = None
_chat_limiter: Optional[RateLimiter] = None


def get_default_limiter() -> RateLimiter:
    """Get or create default rate limiter."""
    global _default_limiter
    if _default_limiter is None:
        # Try to load from config
        try:
            from .config import Config
            config = Config.from_env()
            _default_limiter = RateLimiter(RateLimitConfig(
                requests=config.rate_limit_default_per_minute,
                window=60,
                strategy=LimitStrategy.SLIDING_WINDOW,
            ))
        except Exception:
            # Fallback to defaults
            _default_limiter = RateLimiter(RateLimitConfig(
                requests=60,
                window=60,
                strategy=LimitStrategy.SLIDING_WINDOW,
            ))
    return _default_limiter


def get_chat_limiter() -> RateLimiter:
    """Get or create chat endpoint rate limiter."""
    global _chat_limiter
    if _chat_limiter is None:
        # Try to load from config
        try:
            from .config import Config
            config = Config.from_env()
            _chat_limiter = RateLimiter(RateLimitConfig(
                requests=config.rate_limit_chat_per_minute,
                window=60,
                strategy=LimitStrategy.SLIDING_WINDOW,
            ))
        except Exception:
            # Fallback to defaults
            _chat_limiter = RateLimiter(RateLimitConfig(
                requests=10,
                window=60,
                strategy=LimitStrategy.SLIDING_WINDOW,
            ))
    return _chat_limiter


def reset_limiters() -> None:
    """Reset all limiters (for testing)."""
    global _default_limiter, _chat_limiter
    _default_limiter = None
    _chat_limiter = None
