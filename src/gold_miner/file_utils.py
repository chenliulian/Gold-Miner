"""File utilities with atomic write support."""

from __future__ import annotations

import fcntl
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Union


class FileLock:
    """File-based locking mechanism."""

    def __init__(self, lock_path: Union[str, Path]):
        self.lock_path = Path(lock_path)
        self.lock_file = None

    def acquire(self) -> None:
        """Acquire the lock."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file = open(self.lock_path, "w")
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)

    def release(self) -> None:
        """Release the lock."""
        if self.lock_file:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_file = None

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


def atomic_write(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    mode: int = 0o644,
) -> None:
    """
    Atomically write content to a file.

    Uses write-to-temp + rename pattern for atomicity.

    Args:
        path: Target file path
        content: Content to write
        encoding: File encoding
        mode: File permissions
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory for atomic rename
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )

    try:
        # Write to temp file
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)

        # Set permissions
        os.chmod(temp_path, mode)

        # Atomic rename
        os.replace(temp_path, path)

    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def atomic_write_json(
    path: Union[str, Path],
    data: dict,
    encoding: str = "utf-8",
    indent: int = 2,
) -> None:
    """Atomically write JSON data to a file."""
    import json

    content = json.dumps(data, ensure_ascii=False, indent=indent)
    atomic_write(path, content, encoding)


@contextmanager
def locked_file(
    path: Union[str, Path],
    mode: str = "r",
    encoding: str = "utf-8",
) -> Generator:
    """
    Context manager for file access with locking.

    Args:
        path: File path
        mode: File mode
        encoding: File encoding

    Yields:
        File object
    """
    path = Path(path)
    lock_path = path.parent / f".{path.name}.lock"

    with FileLock(lock_path):
        with open(path, mode, encoding=encoding) as f:
            yield f


def safe_read_json(
    path: Union[str, Path],
    default: dict = None,
    encoding: str = "utf-8",
) -> dict:
    """
    Safely read JSON file with fallback to default.

    Args:
        path: File path
        default: Default value if file doesn't exist or is invalid
        encoding: File encoding

    Returns:
        Parsed JSON data or default
    """
    import json

    path = Path(path)
    if not path.exists():
        return default if default is not None else {}

    try:
        with locked_file(path, "r", encoding) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else {}
