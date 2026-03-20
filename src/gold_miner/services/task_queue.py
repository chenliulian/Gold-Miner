"""Task queue for asynchronous processing."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A task in the queue."""
    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    progress_message: str = ""


class TaskQueue:
    """Simple in-memory task queue with worker threads."""

    def __init__(self, max_workers: int = 4, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self._queue: List[Task] = []
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.RLock()
        self._workers: List[threading.Thread] = []
        self._shutdown = False
        self._condition = threading.Condition(self._lock)

        # Start worker threads
        self._start_workers()

    def _start_workers(self) -> None:
        """Start worker threads."""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)

    def _worker_loop(self) -> None:
        """Worker thread loop."""
        while True:
            with self._condition:
                if self._shutdown:
                    break

                # Wait for tasks
                while not self._queue and not self._shutdown:
                    self._condition.wait(timeout=1.0)

                if self._shutdown:
                    break

                if not self._queue:
                    continue

                task = self._queue.pop(0)
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()

            # Execute task outside lock
            try:
                result = task.func(*task.args, **task.kwargs)
                with self._lock:
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    task.progress = 1.0
                    task.progress_message = "Completed"
            except Exception as e:
                with self._lock:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    task.progress_message = f"Failed: {e}"

    def submit(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> str:
        """Submit a task to the queue."""
        with self._lock:
            if len(self._queue) >= self.max_queue_size:
                raise RuntimeError(f"Task queue is full (max {self.max_queue_size})")

            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs,
            )
            self._queue.append(task)
            self._tasks[task_id] = task

            # Notify workers
            with self._condition:
                self._condition.notify()

            return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        task = self.get_task(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "progress": task.progress,
            "progress_message": task.progress_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result if task.status == TaskStatus.COMPLETED else None,
            "error": task.error if task.status == TaskStatus.FAILED else None,
        }

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                if task in self._queue:
                    self._queue.remove(task)
                return True

            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            statuses = {}
            for task in self._tasks.values():
                status = task.status.value
                statuses[status] = statuses.get(status, 0) + 1

            return {
                "queue_size": len(self._queue),
                "total_tasks": len(self._tasks),
                "max_workers": self.max_workers,
                "max_queue_size": self.max_queue_size,
                "statuses": statuses,
            }

    def shutdown(self) -> None:
        """Shutdown the task queue."""
        with self._condition:
            self._shutdown = True
            self._condition.notify_all()

        for worker in self._workers:
            worker.join(timeout=5.0)


# Global task queue instance
_task_queue: Optional[TaskQueue] = None
_queue_lock = threading.Lock()


def get_task_queue(max_workers: int = 4) -> TaskQueue:
    """Get or create the global task queue."""
    global _task_queue

    if _task_queue is None:
        with _queue_lock:
            if _task_queue is None:
                _task_queue = TaskQueue(max_workers=max_workers)

    return _task_queue


def reset_task_queue() -> None:
    """Reset the global task queue (for testing)."""
    global _task_queue
    with _queue_lock:
        if _task_queue:
            _task_queue.shutdown()
        _task_queue = None
