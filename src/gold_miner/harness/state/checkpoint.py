"""Checkpoint Manager - 检查点与恢复"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .session_state import SessionState


@dataclass
class Checkpoint:
    """检查点"""
    id: str
    session_id: str
    step: int
    state: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""

    def save(self, checkpoint_dir: str) -> str:
        """保存检查点到文件"""
        path = Path(checkpoint_dir) / f"{self.session_id}_{self.step}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "id": self.id,
                "session_id": self.session_id,
                "step": self.step,
                "state": self.state,
                "created_at": self.created_at,
                "description": self.description
            }, f, ensure_ascii=False, indent=2)
        return str(path)

    @classmethod
    def load(cls, checkpoint_path: str) -> "Checkpoint":
        """从文件加载检查点"""
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            step=data["step"],
            state=data["state"],
            created_at=data.get("created_at", ""),
            description=data.get("description", "")
        )


class CheckpointManager:
    """
    检查点管理器 - 支持状态快照与恢复

    解决 Lost State on Failure 问题：
    1. 定期保存检查点
    2. 故障后可以从检查点恢复
    3. 支持回溯到任意检查点
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints: Dict[str, List[Checkpoint]] = {}

    def create_checkpoint(
        self,
        session_id: str,
        step: int,
        state: SessionState,
        description: str = ""
    ) -> Checkpoint:
        """创建检查点"""
        checkpoint = Checkpoint(
            id=f"{session_id}_step{step}",
            session_id=session_id,
            step=step,
            state=state.to_dict(),
            description=description
        )
        path = checkpoint.save(str(self.checkpoint_dir))

        if session_id not in self._checkpoints:
            self._checkpoints[session_id] = []
        self._checkpoints[session_id].append(checkpoint)

        return checkpoint

    def get_latest_checkpoint(self, session_id: str) -> Optional[Checkpoint]:
        """获取最新的检查点"""
        checkpoints = self._checkpoints.get(session_id, [])
        if not checkpoints:
            return None
        return checkpoints[-1]

    def get_checkpoint_at_step(self, session_id: str, step: int) -> Optional[Checkpoint]:
        """获取指定步骤的检查点"""
        checkpoints = self._checkpoints.get(session_id, [])
        for cp in checkpoints:
            if cp.step == step:
                return cp
        return None

    def restore_session_state(self, checkpoint: Checkpoint) -> SessionState:
        """从检查点恢复 SessionState"""
        return SessionState.from_dict(checkpoint.state)

    def list_checkpoints(self, session_id: str) -> List[Checkpoint]:
        """列出会话的所有检查点"""
        return self._checkpoints.get(session_id, [])

    def delete_checkpoints(self, session_id: str) -> int:
        """删除会话的所有检查点"""
        count = 0
        for checkpoint in self._checkpoints.get(session_id, []):
            path = self.checkpoint_dir / f"{session_id}_{checkpoint.step}.json"
            if path.exists():
                path.unlink()
                count += 1
        self._checkpoints[session_id] = []
        return count

    def load_checkpoints_from_disk(self) -> None:
        """从磁盘加载检查点"""
        for path in self.checkpoint_dir.glob("*.json"):
            try:
                checkpoint = Checkpoint.load(str(path))
                session_id = checkpoint.session_id
                if session_id not in self._checkpoints:
                    self._checkpoints[session_id] = []
                self._checkpoints[session_id].append(checkpoint)
            except Exception:
                pass

    def auto_cleanup(self, max_checkpoints_per_session: int = 10) -> None:
        """自动清理旧检查点"""
        for session_id, checkpoints in self._checkpoints.items():
            if len(checkpoints) > max_checkpoints_per_session:
                to_delete = checkpoints[:-max_checkpoints_per_session]
                for cp in to_delete:
                    path = self.checkpoint_dir / f"{session_id}_{cp.step}.json"
                    if path.exists():
                        path.unlink()
                self._checkpoints[session_id] = checkpoints[-max_checkpoints_per_session:]