"""Artifact Manager - 工件管理器（简化版）"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .workspace import Artifact, Workspace


class ArtifactManager:
    """
    工件管理器 - 提供高级工件管理功能

    功能：
    1. 工件分类
    2. 工件搜索
    3. 工件版本控制（简化版）
    4. 工件导出/导入
    """

    def __init__(self, workspace: Optional[Workspace] = None):
        self.workspace = workspace or Workspace()

    def store_data(self, key: str, data: Any, metadata: Optional[Dict] = None) -> Artifact:
        """存储数据工件"""
        return self.workspace.store(key, data, "data", metadata)

    def store_sql(self, key: str, sql: str, metadata: Optional[Dict] = None) -> Artifact:
        """存储 SQL 工件"""
        return self.workspace.store(key, sql, "sql", metadata)

    def store_report(self, key: str, report: str, metadata: Optional[Dict] = None) -> Artifact:
        """存储报告工件"""
        return self.workspace.store(key, report, "report", metadata)

    def store_text(self, key: str, text: str, metadata: Optional[Dict] = None) -> Artifact:
        """存储文本工件"""
        return self.workspace.store(key, text, "text", metadata)

    def store_csv(self, key: str, csv_data: str, metadata: Optional[Dict] = None) -> Artifact:
        """存储 CSV 工件"""
        return self.workspace.store(key, csv_data, "csv", metadata)

    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据工件"""
        return self.workspace.retrieve(key, default)

    def get_sql(self, key: str) -> Optional[str]:
        """获取 SQL 工件"""
        content = self.workspace.retrieve(key)
        return content if isinstance(content, str) else None

    def get_report(self, key: str) -> Optional[str]:
        """获取报告工件"""
        content = self.workspace.retrieve(key)
        return content if isinstance(content, str) else None

    def list_data(self) -> List[Artifact]:
        """列出数据工件"""
        return self.workspace.list_artifacts("data")

    def list_sql(self) -> List[Artifact]:
        """列出 SQL 工件"""
        return self.workspace.list_artifacts("sql")

    def list_reports(self) -> List[Artifact]:
        """列出报告工件"""
        return self.workspace.list_artifacts("report")

    def search(self, query: str) -> List[Artifact]:
        """搜索工件（按 key）"""
        results = []
        query_lower = query.lower()
        for artifact in self.workspace.list_artifacts():
            if query_lower in artifact.key.lower():
                results.append(artifact)
        return results

    def export_artifact(self, key: str, export_path: str) -> bool:
        """导出工件到指定路径"""
        artifact = self.workspace._artifacts.get(key)
        if not artifact:
            return False

        path = Path(export_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(artifact.content, (str, bytes)):
            mode = "wb" if isinstance(artifact.content, bytes) else "w"
            encoding = None if isinstance(artifact.content, bytes) else "utf-8"
            with open(path, mode, encoding=encoding) as f:
                f.write(artifact.content)
            return True

        with open(path, "w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, ensure_ascii=False, indent=2)
        return True

    def import_artifact(self, import_path: str, key: Optional[str] = None) -> Optional[Artifact]:
        """从指定路径导入工件"""
        path = Path(import_path)
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8")
        artifact_key = key or path.stem

        return self.workspace.store(artifact_key, content, "imported", {"source": str(path)})