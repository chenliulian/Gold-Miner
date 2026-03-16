import subprocess
import os
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()

ALLOWED_COMMANDS = {
    "grep": ["grep", "-rn", "--include"],
    "find": ["find", "-name"],
    "ls": ["ls", "-la", "-l", "-R"],
    "cat": ["cat"],
    "pwd": ["pwd"],
    "tree": ["tree", "-L"],
    "head": ["head", "-n"],
    "tail": ["tail", "-n"],
    "wc": ["wc", "-l"],
    "diff": ["diff"],
}

ALLOWED_EXTENSIONS = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh"}

DANGEROUS_PATTERNS = ["rm -rf", "dd", "mkfs", ">:", "| sh", "&& rm", "; rm", "chmod 777", "chown"]


def _is_safe_command(command: str) -> bool:
    cmd_lower = command.lower()
    for dangerous in DANGEROUS_PATTERNS:
        if dangerous in cmd_lower:
            return False
    return True


def run(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    执行系统命令

    参数:
        command: 要执行的命令
        cwd: 工作目录 (默认项目根目录)
    """
    if cwd is None:
        cwd = str(PROJECT_ROOT)

    if not _is_safe_command(command):
        return {
            "success": False,
            "error": "Command contains potentially dangerous patterns",
            "output": "",
        }

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "output": result.stdout[:5000] if result.stdout else "",
            "error": result.stderr[:1000] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out (30s limit)",
            "output": "",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "output": "",
        }


SKILL = {
    "name": "system_command",
    "description": "在项目目录中执行系统命令，支持文件检索、目录操作等",
    "inputs": {
        "command": "str (必需) - 要执行的命令，如 grep -rn 'pattern' .",
        "cwd": "str (可选) - 工作目录，默认项目根目录",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
