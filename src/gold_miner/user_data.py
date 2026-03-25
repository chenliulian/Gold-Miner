"""User data isolation manager.

This module provides user-specific data management including:
- Session storage per user
- Memory storage per user
- Learning records per user
- Reports per user
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

from .file_utils import atomic_write_json, safe_read_json


@dataclass
class UserPaths:
    """Paths for user-specific data storage."""
    base_dir: str
    sessions_dir: str
    memory_dir: str
    learnings_dir: str
    reports_dir: str
    profile_path: str


class UserDataManager:
    """Manager for user-specific data isolation.
    
    Each user gets their own directory structure:
    data/user_{user_id}/
        ├── profile.json          # User profile and settings
        ├── sessions/             # User's conversation sessions
        ├── memory/               # User's long-term memory
        ├── learnings/            # User's learning records
        └── reports/              # User's generated reports
    """
    
    def __init__(self, data_root: str = "./data"):
        self.data_root = Path(data_root)
        self._ensure_base_structure()
    
    def _ensure_base_structure(self) -> None:
        """Ensure the base data directory exists."""
        self.data_root.mkdir(parents=True, exist_ok=True)
    
    def get_user_paths(self, user_id: str) -> UserPaths:
        """Get all paths for a specific user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            UserPaths object containing all paths for the user
        """
        user_dir = self.data_root / f"user_{user_id}"
        
        return UserPaths(
            base_dir=str(user_dir),
            sessions_dir=str(user_dir / "sessions"),
            memory_dir=str(user_dir / "memory"),
            learnings_dir=str(user_dir / "learnings"),
            reports_dir=str(user_dir / "reports"),
            profile_path=str(user_dir / "profile.json"),
        )
    
    def create_user_directories(self, user_id: str) -> UserPaths:
        """Create all necessary directories for a new user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            UserPaths object containing all paths for the user
        """
        paths = self.get_user_paths(user_id)
        
        # Create all directories
        Path(paths.base_dir).mkdir(parents=True, exist_ok=True)
        Path(paths.sessions_dir).mkdir(parents=True, exist_ok=True)
        Path(paths.memory_dir).mkdir(parents=True, exist_ok=True)
        Path(paths.learnings_dir).mkdir(parents=True, exist_ok=True)
        Path(paths.reports_dir).mkdir(parents=True, exist_ok=True)
        
        # Create default profile if not exists
        if not os.path.exists(paths.profile_path):
            default_profile = {
                "user_id": user_id,
                "settings": {
                    "theme": "light",
                    "language": "zh-CN",
                    "notifications_enabled": True,
                },
                "created_at": self._now_iso(),
                "updated_at": self._now_iso(),
            }
            atomic_write_json(paths.profile_path, default_profile)
        
        return paths
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User profile dictionary
        """
        paths = self.get_user_paths(user_id)
        return safe_read_json(paths.profile_path, default={})
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile.
        
        Args:
            user_id: The user's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated user profile
        """
        paths = self.get_user_paths(user_id)
        profile = self.get_user_profile(user_id)
        
        # Deep merge updates
        self._deep_merge(profile, updates)
        profile["updated_at"] = self._now_iso()
        
        atomic_write_json(paths.profile_path, profile)
        return profile
    
    def get_user_sessions_dir(self, user_id: str) -> str:
        """Get the sessions directory for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            Path to the user's sessions directory
        """
        paths = self.create_user_directories(user_id)
        return paths.sessions_dir
    
    def get_user_memory_path(self, user_id: str) -> str:
        """Get the memory file path for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            Path to the user's memory file
        """
        paths = self.create_user_directories(user_id)
        return os.path.join(paths.memory_dir, "state.json")
    
    def get_user_memory_summary_path(self, user_id: str) -> str:
        """Get the memory summary file path for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            Path to the user's memory summary file
        """
        paths = self.create_user_directories(user_id)
        return os.path.join(paths.memory_dir, "summary.md")
    
    def get_user_learnings_path(self, user_id: str) -> str:
        """Get the learnings file path for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            Path to the user's learnings file
        """
        paths = self.create_user_directories(user_id)
        return os.path.join(paths.learnings_dir, "learnings.md")
    
    def get_user_reports_dir(self, user_id: str) -> str:
        """Get the reports directory for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            Path to the user's reports directory
        """
        paths = self.create_user_directories(user_id)
        return paths.reports_dir
    
    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of session metadata
        """
        sessions_dir = self.get_user_sessions_dir(user_id)
        sessions = []
        
        if not os.path.exists(sessions_dir):
            return sessions
        
        for filename in os.listdir(sessions_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(sessions_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        sessions.append({
                            "session_id": data.get("session_id", filename[:-5]),
                            "title": data.get("title", "Untitled"),
                            "start_time": data.get("start_time", ""),
                            "end_time": data.get("end_time"),
                            "step_count": len(data.get("steps", [])),
                        })
                except (json.JSONDecodeError, IOError):
                    continue
        
        # Sort by start time descending
        sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        return sessions
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all data for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            True if successful
        """
        import shutil
        
        paths = self.get_user_paths(user_id)
        user_dir = Path(paths.base_dir)
        
        if user_dir.exists():
            shutil.rmtree(user_dir)
            return True
        return False
    
    def user_exists(self, user_id: str) -> bool:
        """Check if a user has data stored.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            True if user data exists
        """
        paths = self.get_user_paths(user_id)
        return os.path.exists(paths.base_dir)
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Deep merge updates into base dictionary."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _now_iso(self) -> str:
        """Get current time in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


# Global instance
_user_data_manager: Optional[UserDataManager] = None


def get_user_data_manager(data_root: str = "./data") -> UserDataManager:
    """Get the global UserDataManager instance.
    
    Args:
        data_root: Root directory for user data
        
    Returns:
        UserDataManager instance
    """
    global _user_data_manager
    if _user_data_manager is None:
        _user_data_manager = UserDataManager(data_root)
    return _user_data_manager


def init_user_data_manager(data_root: str = "./data") -> UserDataManager:
    """Initialize the global UserDataManager instance.
    
    Args:
        data_root: Root directory for user data
        
    Returns:
        UserDataManager instance
    """
    global _user_data_manager
    _user_data_manager = UserDataManager(data_root)
    return _user_data_manager
