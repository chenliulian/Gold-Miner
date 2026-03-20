"""Agent pool for managing multiple agent instances."""

from __future__ import annotations

import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..agent import SqlAgent
from ..config import Config


@dataclass
class PooledAgent:
    """An agent instance in the pool."""
    agent: SqlAgent
    agent_id: str
    created_at: datetime
    last_used: datetime
    in_use: bool = False
    use_count: int = 0
    session_id: Optional[str] = None


class AgentPool:
    """Pool of agent instances for handling concurrent requests."""

    def __init__(
        self,
        config: Config,
        skills_dir: str,
        sessions_dir: str,
        min_size: int = 2,
        max_size: int = 10,
        max_idle_time: int = 3600,  # 1 hour
    ):
        self.config = config
        self.skills_dir = skills_dir
        self.sessions_dir = sessions_dir
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time

        self._pool: deque[PooledAgent] = deque()
        self._lock = threading.RLock()
        self._shutdown = False

        # Initialize minimum pool size
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Initialize the pool with minimum agents."""
        for _ in range(self.min_size):
            agent = self._create_agent()
            self._pool.append(agent)

    def _create_agent(self) -> PooledAgent:
        """Create a new agent instance."""
        now = datetime.now()
        return PooledAgent(
            agent=SqlAgent(self.config, self.skills_dir, self.sessions_dir),
            agent_id=str(uuid.uuid4()),
            created_at=now,
            last_used=now,
            in_use=False,
            use_count=0,
        )

    def acquire(self, session_id: Optional[str] = None) -> PooledAgent:
        """Acquire an agent from the pool."""
        with self._lock:
            if self._shutdown:
                raise RuntimeError("Agent pool is shutdown")

            # Try to find an available agent
            for pooled_agent in self._pool:
                if not pooled_agent.in_use:
                    pooled_agent.in_use = True
                    pooled_agent.last_used = datetime.now()
                    pooled_agent.use_count += 1
                    pooled_agent.session_id = session_id
                    return pooled_agent

            # Create new agent if under max size
            if len(self._pool) < self.max_size:
                new_agent = self._create_agent()
                new_agent.in_use = True
                new_agent.use_count = 1
                new_agent.session_id = session_id
                self._pool.append(new_agent)
                return new_agent

            # Pool exhausted
            raise RuntimeError(
                f"Agent pool exhausted. All {self.max_size} agents are in use. "
                "Please try again later."
            )

    def release(self, pooled_agent: PooledAgent) -> None:
        """Release an agent back to the pool."""
        with self._lock:
            if pooled_agent in self._pool:
                pooled_agent.in_use = False
                pooled_agent.session_id = None
                pooled_agent.last_used = datetime.now()

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            total = len(self._pool)
            in_use = sum(1 for a in self._pool if a.in_use)
            available = total - in_use

            return {
                "total_agents": total,
                "in_use": in_use,
                "available": available,
                "min_size": self.min_size,
                "max_size": self.max_size,
                "agents": [
                    {
                        "agent_id": a.agent_id,
                        "in_use": a.in_use,
                        "use_count": a.use_count,
                        "created_at": a.created_at.isoformat(),
                        "last_used": a.last_used.isoformat(),
                        "session_id": a.session_id,
                    }
                    for a in self._pool
                ],
            }

    def cleanup_idle(self) -> int:
        """Remove idle agents beyond minimum size."""
        with self._lock:
            now = datetime.now()
            to_remove = []

            for pooled_agent in self._pool:
                if (
                    not pooled_agent.in_use
                    and len(self._pool) - len(to_remove) > self.min_size
                ):
                    idle_time = (now - pooled_agent.last_used).total_seconds()
                    if idle_time > self.max_idle_time:
                        to_remove.append(pooled_agent)

            for agent in to_remove:
                self._pool.remove(agent)

            return len(to_remove)

    def shutdown(self) -> None:
        """Shutdown the pool and release all agents."""
        with self._lock:
            self._shutdown = True
            self._pool.clear()


# Global agent pool instance
_agent_pool: Optional[AgentPool] = None
_pool_lock = threading.Lock()


def get_agent_pool(
    config: Optional[Config] = None,
    skills_dir: Optional[str] = None,
    sessions_dir: Optional[str] = None,
) -> AgentPool:
    """Get or create the global agent pool."""
    global _agent_pool

    if _agent_pool is None:
        with _pool_lock:
            if _agent_pool is None:
                if config is None or skills_dir is None:
                    raise ValueError(
                        "Config and skills_dir required for initial pool creation"
                    )
                _agent_pool = AgentPool(
                    config=config,
                    skills_dir=skills_dir,
                    sessions_dir=sessions_dir or "./sessions",
                )

    return _agent_pool


def reset_agent_pool() -> None:
    """Reset the global agent pool (for testing)."""
    global _agent_pool
    with _pool_lock:
        if _agent_pool:
            _agent_pool.shutdown()
        _agent_pool = None
