"""User data storage with file-based implementation."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import User, LoginLog, SessionState


class UserStore:
    """用户数据存储 - 基于文件系统"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.users_dir = os.path.join(data_dir, "users")
        self.sessions_dir = os.path.join(data_dir, "sessions")
        self.logs_dir = os.path.join(data_dir, "logs")
        self.users_index_path = os.path.join(data_dir, "users_index.json")
        
        self._ensure_dirs()
    
    def _ensure_dirs(self) -> None:
        """确保目录存在"""
        os.makedirs(self.users_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def _get_user_path(self, user_id: str) -> str:
        """获取用户文件路径"""
        return os.path.join(self.users_dir, f"{user_id}.json")
    
    def _get_session_path(self, session_id: str) -> str:
        """获取会话文件路径"""
        return os.path.join(self.sessions_dir, f"{session_id}.json")
    
    def _get_log_path(self, log_id: str) -> str:
        """获取日志文件路径"""
        return os.path.join(self.logs_dir, f"{log_id}.json")
    
    def _load_index(self) -> Dict[str, Any]:
        """加载用户索引"""
        if os.path.exists(self.users_index_path):
            with open(self.users_index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "feishu_open_id_map": {},  # feishu_open_id -> user_id
            "feishu_union_id_map": {},  # feishu_union_id -> user_id
            "email_map": {},  # email -> user_id
            "employee_id_map": {},  # employee_id -> user_id
            "username_map": {},  # username -> user_id
        }
    
    def _save_index(self, index: Dict[str, Any]) -> None:
        """保存用户索引"""
        with open(self.users_index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _update_index(self, user: User) -> None:
        """更新用户索引"""
        index = self._load_index()
        
        if user.feishu_open_id:
            index["feishu_open_id_map"][user.feishu_open_id] = user.id
        if user.feishu_union_id:
            index["feishu_union_id_map"][user.feishu_union_id] = user.id
        if user.email:
            index["email_map"][user.email] = user.id
        if user.employee_id:
            index["employee_id_map"][user.employee_id] = user.id
        if user.username:
            index["username_map"][user.username] = user.id
        
        self._save_index(index)
    
    # ========== User Operations ==========
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """创建新用户"""
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # 移除可能重复的字段
        user_data = {k: v for k, v in user_data.items() if k not in ['id', 'created_at', 'updated_at']}

        user = User(
            id=user_id,
            **user_data,
            created_at=now,
            updated_at=now,
        )
        
        # 保存用户数据
        with open(self._get_user_path(user_id), "w", encoding="utf-8") as f:
            json.dump(user.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 更新索引
        self._update_index(user)
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        path = self._get_user_path(user_id)
        if not os.path.exists(path):
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return User.from_dict(data)
    
    def get_user_by_feishu_open_id(self, open_id: str) -> Optional[User]:
        """根据飞书open_id获取用户"""
        index = self._load_index()
        user_id = index["feishu_open_id_map"].get(open_id)
        if user_id:
            return self.get_user_by_id(user_id)
        return None
    
    def get_user_by_feishu_union_id(self, union_id: str) -> Optional[User]:
        """根据飞书union_id获取用户"""
        index = self._load_index()
        user_id = index["feishu_union_id_map"].get(union_id)
        if user_id:
            return self.get_user_by_id(user_id)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        index = self._load_index()
        user_id = index["email_map"].get(email)
        if user_id:
            return self.get_user_by_id(user_id)
        return None
    
    def get_user_by_employee_id(self, employee_id: str) -> Optional[User]:
        """根据员工工号获取用户"""
        index = self._load_index()
        user_id = index["employee_id_map"].get(employee_id)
        if user_id:
            return self.get_user_by_id(user_id)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        index = self._load_index()
        user_id = index["username_map"].get(username)
        if user_id:
            return self.get_user_by_id(user_id)
        return None
    
    def update_user(self, user: User) -> User:
        """更新用户信息"""
        user.updated_at = datetime.now().isoformat()
        
        with open(self._get_user_path(user.id), "w", encoding="utf-8") as f:
            json.dump(user.to_dict(), f, ensure_ascii=False, indent=2)
        
        self._update_index(user)
        
        return user
    
    def list_users(self, active_only: bool = False) -> List[User]:
        """列出所有用户"""
        users = []
        
        for filename in os.listdir(self.users_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.users_dir, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    user = User.from_dict(data)
                    if not active_only or user.is_active:
                        users.append(user)
        
        return users
    
    # ========== Session Operations ==========
    
    def create_session(self, session: SessionState) -> SessionState:
        """创建会话"""
        with open(self._get_session_path(session.session_id), "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """获取会话"""
        path = self._get_session_path(session_id)
        if not os.path.exists(path):
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return SessionState.from_dict(data)
    
    def get_session_by_token(self, token: str) -> Optional[SessionState]:
        """根据token获取会话"""
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.sessions_dir, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("token") == token:
                        return SessionState.from_dict(data)
        return None
    
    def update_session(self, session: SessionState) -> SessionState:
        """更新会话"""
        with open(self._get_session_path(session.session_id), "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        path = self._get_session_path(session_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def list_user_sessions(self, user_id: str, active_only: bool = False) -> List[SessionState]:
        """列出用户的所有会话"""
        sessions = []
        
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.sessions_dir, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("user_id") == user_id:
                        session = SessionState.from_dict(data)
                        if not active_only or session.is_active:
                            sessions.append(session)
        
        return sessions
    
    # ========== Login Log Operations ==========
    
    def create_login_log(self, log: LoginLog) -> LoginLog:
        """创建登录日志"""
        with open(self._get_log_path(log.id), "w", encoding="utf-8") as f:
            json.dump(log.to_dict(), f, ensure_ascii=False, indent=2)
        
        return log
    
    def get_user_login_logs(self, user_id: str, limit: int = 10) -> List[LoginLog]:
        """获取用户登录日志"""
        logs = []
        
        for filename in os.listdir(self.logs_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.logs_dir, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("user_id") == user_id:
                        logs.append(LoginLog.from_dict(data))
        
        # 按时间倒序排列
        logs.sort(key=lambda x: x.created_at, reverse=True)
        
        return logs[:limit]
    
    # ========== User Data Directory ==========
    
    def get_user_data_dir(self, user_id: str) -> str:
        """获取用户数据目录"""
        user_dir = os.path.join(self.data_dir, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        # 创建子目录
        os.makedirs(os.path.join(user_dir, "sessions"), exist_ok=True)
        os.makedirs(os.path.join(user_dir, "memory"), exist_ok=True)
        os.makedirs(os.path.join(user_dir, "learnings"), exist_ok=True)
        os.makedirs(os.path.join(user_dir, "reports"), exist_ok=True)
        
        return user_dir
    
    def get_user_profile_path(self, user_id: str) -> str:
        """获取用户配置文件路径"""
        user_dir = self.get_user_data_dir(user_id)
        return os.path.join(user_dir, "profile.json")
