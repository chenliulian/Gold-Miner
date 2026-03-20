"""Service layer for GoldMiner - provides business logic abstraction."""

from __future__ import annotations

from typing import Optional

from .agent_pool import AgentPool, get_agent_pool
from .task_queue import TaskQueue, TaskStatus, get_task_queue

__all__ = [
    "AgentPool",
    "get_agent_pool",
    "TaskQueue",
    "TaskStatus",
    "get_task_queue",
]


# Global service instances
_agent_pool: Optional[AgentPool] = None
_task_queue: Optional[TaskQueue] = None


def init_services(
    config,
    skills_dir: str,
    sessions_dir: str,
) -> None:
    """Initialize all services with configuration."""
    global _agent_pool, _task_queue

    # Initialize agent pool with config values
    _agent_pool = AgentPool(
        config=config,
        skills_dir=skills_dir,
        sessions_dir=sessions_dir,
        min_size=config.agent_pool_min_size,
        max_size=config.agent_pool_max_size,
        max_idle_time=config.agent_pool_max_idle_time,
    )

    # Initialize task queue
    _task_queue = TaskQueue(max_workers=4, max_queue_size=100)


def get_agent_pool(
    config=None,
    skills_dir: Optional[str] = None,
    sessions_dir: Optional[str] = None,
) -> AgentPool:
    """Get or create the global agent pool."""
    global _agent_pool
    if _agent_pool is None:
        if config is None or skills_dir is None:
            raise RuntimeError(
                "Agent pool not initialized. Call init_services() first or provide config."
            )
        _agent_pool = AgentPool(
            config=config,
            skills_dir=skills_dir,
            sessions_dir=sessions_dir or "./sessions",
            min_size=getattr(config, 'agent_pool_min_size', 2),
            max_size=getattr(config, 'agent_pool_max_size', 10),
            max_idle_time=getattr(config, 'agent_pool_max_idle_time', 3600),
        )
    return _agent_pool


def get_task_queue() -> TaskQueue:
    """Get or create the global task queue."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(max_workers=4, max_queue_size=100)
    return _task_queue