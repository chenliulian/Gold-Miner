"""文件存储服务 - 支持本地存储和对象存储.

This module provides file storage capabilities:
- Local file system storage
- Object storage (OSS/S3) support (future)
- File metadata management
- Automatic cleanup of expired files
"""

from __future__ import annotations

import hashlib
import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from pathlib import Path


@dataclass
class FileInfo:
    """文件信息数据结构."""

    file_id: str
    filename: str  # 原始文件名
    stored_filename: str  # 存储文件名
    file_path: str  # 完整存储路径
    download_url: str  # 下载 URL
    size: int  # 文件大小（字节）
    created_at: datetime
    expire_at: datetime
    content_type: str = "application/octet-stream"
    metadata: Dict[str, Any] = field(default_factory=dict)


class StorageBackend(ABC):
    """存储后端抽象基类."""

    @abstractmethod
    def save(self, local_path: str, stored_filename: str) -> str:
        """保存文件.

        Args:
            local_path: 本地文件路径
            stored_filename: 存储文件名

        Returns:
            文件访问 URL
        """
        pass

    @abstractmethod
    def get_url(self, stored_filename: str) -> str:
        """获取文件访问 URL.

        Args:
            stored_filename: 存储文件名

        Returns:
            文件访问 URL
        """
        pass

    @abstractmethod
    def delete(self, stored_filename: str) -> bool:
        """删除文件.

        Args:
            stored_filename: 存储文件名

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def exists(self, stored_filename: str) -> bool:
        """检查文件是否存在.

        Args:
            stored_filename: 存储文件名

        Returns:
            文件是否存在
        """
        pass

    @abstractmethod
    def get_path(self, stored_filename: str) -> str:
        """获取文件的完整路径.

        Args:
            stored_filename: 存储文件名

        Returns:
            文件完整路径
        """
        pass


class LocalStorageBackend(StorageBackend):
    """本地文件存储后端."""

    def __init__(self, base_dir: str, base_url: str = "/api/v2/reports/download"):
        """初始化本地存储后端.

        Args:
            base_dir: 基础存储目录
            base_url: 下载 URL 基础路径
        """
        self.base_dir = Path(base_dir)
        self.base_url = base_url
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, local_path: str, stored_filename: str) -> str:
        """保存文件到本地存储."""
        dest_path = self.base_dir / stored_filename
        local_path_obj = Path(local_path)
        
        # 如果源文件和目标路径相同，跳过复制
        if local_path_obj.resolve() == dest_path.resolve():
            return f"{self.base_url}/{stored_filename}"
        
        shutil.copy2(local_path, dest_path)
        return f"{self.base_url}/{stored_filename}"

    def get_url(self, stored_filename: str) -> str:
        """获取文件下载 URL."""
        return f"{self.base_url}/{stored_filename}"

    def delete(self, stored_filename: str) -> bool:
        """删除文件."""
        file_path = self.base_dir / stored_filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def exists(self, stored_filename: str) -> bool:
        """检查文件是否存在."""
        return (self.base_dir / stored_filename).exists()

    def get_path(self, stored_filename: str) -> str:
        """获取文件完整路径."""
        return str(self.base_dir / stored_filename)


class FileStorageService:
    """文件存储服务."""

    def __init__(
        self,
        backend: StorageBackend,
        default_expire_hours: int = 24,
        cleanup_interval_hours: int = 1,
    ):
        """初始化文件存储服务.

        Args:
            backend: 存储后端
            default_expire_hours: 默认文件过期时间（小时）
            cleanup_interval_hours: 清理任务间隔（小时）
        """
        self.backend = backend
        self.default_expire_hours = default_expire_hours
        self._file_registry: Dict[str, FileInfo] = {}
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(hours=cleanup_interval_hours)

    def store_file(
        self,
        local_path: str,
        original_filename: Optional[str] = None,
        expire_hours: Optional[int] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_original_name: bool = False,
    ) -> FileInfo:
        """存储文件并返回文件信息.

        Args:
            local_path: 本地文件路径
            original_filename: 原始文件名
            expire_hours: 过期时间（小时），默认使用服务默认值
            content_type: 文件 MIME 类型
            metadata: 额外元数据
            use_original_name: 是否使用原始文件名作为存储名（而不是hash）

        Returns:
            文件信息对象
        """
        # 检查并执行清理
        self._maybe_cleanup()

        # 确定文件名
        actual_filename = original_filename or Path(local_path).name
        ext = Path(actual_filename).suffix
        
        if use_original_name:
            # 使用原始文件名作为 file_id 和存储名
            file_id = actual_filename.replace(ext, '')
            stored_filename = actual_filename
        else:
            # 生成基于hash的存储文件名
            file_id = self._calc_file_hash(local_path)
            stored_filename = f"{file_id}{ext}"

        # 如果文件已存在，直接返回已有信息
        if file_id in self._file_registry:
            return self._file_registry[file_id]

        # 保存到后端
        self.backend.save(local_path, stored_filename)
        
        # 生成下载 URL（使用 file_id）
        download_url = f"{self.backend.base_url}/{file_id}"

        # 计算过期时间
        expire = expire_hours or self.default_expire_hours
        now = datetime.now()

        # 创建文件信息
        file_info = FileInfo(
            file_id=file_id,
            filename=actual_filename,
            stored_filename=stored_filename,
            file_path=self.backend.get_path(stored_filename),
            download_url=download_url,
            size=os.path.getsize(local_path),
            created_at=now,
            expire_at=now + timedelta(hours=expire),
            content_type=content_type or self._guess_content_type(actual_filename),
            metadata=metadata or {},
        )

        self._file_registry[file_id] = file_info
        return file_info

    def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """获取文件信息.

        Args:
            file_id: 文件 ID

        Returns:
            文件信息对象，不存在则返回 None
        """
        file_info = self._file_registry.get(file_id)
        if file_info is None:
            return None

        # 检查是否过期
        if datetime.now() > file_info.expire_at:
            self.delete_file(file_id)
            return None

        return file_info

    def get_download_url(self, file_id: str) -> Optional[str]:
        """获取文件下载 URL.

        Args:
            file_id: 文件 ID

        Returns:
            下载 URL，文件不存在或已过期则返回 None
        """
        file_info = self.get_file_info(file_id)
        return file_info.download_url if file_info else None

    def delete_file(self, file_id: str) -> bool:
        """删除文件.

        Args:
            file_id: 文件 ID

        Returns:
            是否删除成功
        """
        file_info = self._file_registry.pop(file_id, None)
        if file_info:
            return self.backend.delete(file_info.stored_filename)
        return False

    def list_files(
        self,
        filter_func: Optional[Callable[[FileInfo], bool]] = None,
    ) -> List[FileInfo]:
        """列出所有文件.

        Args:
            filter_func: 过滤函数

        Returns:
            文件信息列表
        """
        files = list(self._file_registry.values())
        if filter_func:
            files = [f for f in files if filter_func(f)]
        return files

    def cleanup_expired(self) -> int:
        """清理过期文件.

        Returns:
            清理的文件数量
        """
        now = datetime.now()
        expired_ids = [
            file_id
            for file_id, info in self._file_registry.items()
            if info.expire_at < now
        ]

        for file_id in expired_ids:
            self.delete_file(file_id)

        self._last_cleanup = now
        return len(expired_ids)

    def _maybe_cleanup(self) -> None:
        """根据需要执行清理."""
        if datetime.now() - self._last_cleanup > self._cleanup_interval:
            self.cleanup_expired()

    @staticmethod
    def _calc_file_hash(filepath: str) -> str:
        """计算文件哈希.

        Args:
            filepath: 文件路径

        Returns:
            文件哈希值（前16位）
        """
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        """根据文件名猜测 MIME 类型.

        Args:
            filename: 文件名

        Returns:
            MIME 类型
        """
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".csv": "text/csv",
            ".json": "application/json",
            ".md": "text/markdown",
            ".txt": "text/plain",
            ".html": "text/html",
            ".htm": "text/html",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
        }
        return mime_types.get(ext, "application/octet-stream")


def create_user_storage_service(
    user_reports_dir: str,
    base_url: str = "/api/v2/reports/download",
    expire_hours: int = 24,
) -> FileStorageService:
    """创建用户专用的文件存储服务.

    Args:
        user_reports_dir: 用户报告目录
        base_url: 下载 URL 基础路径
        expire_hours: 默认过期时间

    Returns:
        文件存储服务实例
    """
    backend = LocalStorageBackend(user_reports_dir, base_url)
    return FileStorageService(backend, default_expire_hours=expire_hours)
