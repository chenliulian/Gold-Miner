"""Workspace - Agent 工作空间管理"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Artifact:
    """
    工件 - 存储中间结果
    """
    key: str
    content: Any
    artifact_type: str = "data"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "content": self.content,
            "artifact_type": self.artifact_type,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Artifact":
        return cls(
            key=data["key"],
            content=data["content"],
            artifact_type=data.get("artifact_type", "data"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


class Workspace:
    """
    工作空间 - Agent 的文件系统抽象

    功能：
    1. 工件存储 - 存储中间结果，释放上下文窗口
    2. 上下文卸载 - 将不常用的数据持久化
    3. 协作共享 - 多个 Agent 可以通过共享工作空间协作

    类比：工作空间 = 文件系统，Artifact = 文件
    """

    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts: Dict[str, Artifact] = {}
        self._load_index()

    def _load_index(self) -> None:
        """加载索引"""
        index_path = self.workspace_dir / ".index.json"
        if index_path.exists():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index = json.load(f)
                    for key, data in index.get("artifacts", {}).items():
                        self._artifacts[key] = Artifact.from_dict(data)
            except Exception:
                pass

    def _save_index(self) -> None:
        """保存索引"""
        index_path = self.workspace_dir / ".index.json"
        index = {
            "artifacts": {k: v.to_dict() for k, v in self._artifacts.items()}
        }
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def store(
        self,
        key: str,
        content: Any,
        artifact_type: str = "data",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Artifact:
        """
        存储工件

        Args:
            key: 工件标识
            content: 内容（可以是任意可序列化对象）
            artifact_type: 类型标记
            metadata: 元数据

        Returns:
            Artifact 对象
        """
        artifact = Artifact(
            key=key,
            content=content,
            artifact_type=artifact_type,
            metadata=metadata or {}
        )

        self._artifacts[key] = artifact

        if isinstance(content, (str, bytes)):
            self._store_file(key, content, artifact_type)

        self._save_index()
        return artifact

    def _store_file(self, key: str, content: Any, artifact_type: str) -> None:
        """存储为文件"""
        ext = self._get_extension(artifact_type)
        file_path = self.workspace_dir / f"{key}{ext}"

        mode = "wb" if isinstance(content, bytes) else "w"
        encoding = None if isinstance(content, bytes) else "utf-8"

        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)

    def _get_extension(self, artifact_type: str) -> str:
        """获取文件扩展名"""
        extensions = {
            "data": ".json",
            "text": ".txt",
            "sql": ".sql",
            "report": ".md",
            "csv": ".csv",
            "code": ".py"
        }
        return extensions.get(artifact_type, ".dat")

    def retrieve(self, key: str, default: Any = None) -> Any:
        """
        获取工件

        Args:
            key: 工件标识
            default: 默认值

        Returns:
            工件内容或默认值
        """
        artifact = self._artifacts.get(key)
        if artifact:
            return artifact.content
        return default

    def exists(self, key: str) -> bool:
        """检查工件是否存在"""
        return key in self._artifacts

    def delete(self, key: str) -> bool:
        """删除工件"""
        if key in self._artifacts:
            del self._artifacts[key]

            file_path = self._find_file(key)
            if file_path and file_path.exists():
                file_path.unlink()

            self._save_index()
            return True
        return False

    def _find_file(self, key: str) -> Optional[Path]:
        """查找工件文件"""
        for ext in [".json", ".txt", ".sql", ".md", ".csv", ".py", ".dat"]:
            path = self.workspace_dir / f"{key}{ext}"
            if path.exists():
                return path
        return None

    def list_artifacts(self, artifact_type: Optional[str] = None) -> List[Artifact]:
        """列出工件"""
        if artifact_type:
            return [a for a in self._artifacts.values() if a.artifact_type == artifact_type]
        return list(self._artifacts.values())

    def clear(self) -> None:
        """清空工作空间"""
        for key in list(self._artifacts.keys()):
            self.delete(key)

    def summary(self) -> str:
        """获取工作空间摘要"""
        types = {}
        for artifact in self._artifacts.values():
            types[artifact.artifact_type] = types.get(artifact.artifact_type, 0) + 1
        lines = [f"Workspace: {self.workspace_dir}", f"Total artifacts: {len(self._artifacts)}"]
        for t, count in types.items():
            lines.append(f"  {t}: {count}")
        return "\n".join(lines)