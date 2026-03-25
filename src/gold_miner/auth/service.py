"""Authentication service."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from .models import User, LoginLog, SessionState, LoginType, LoginStatus
from .user_store import UserStore
from .jwt_utils import generate_jwt_token, verify_jwt_token


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash


class AuthService:
    """认证服务"""
    
    def __init__(
        self,
        user_store: UserStore,
        jwt_secret: str,
        token_expires_hours: int = 8,
    ):
        self.user_store = user_store
        self.jwt_secret = jwt_secret
        self.token_expires_hours = token_expires_hours
    
    def authenticate_feishu_user(
        self,
        feishu_user_info: Dict[str, Any],
        ip_address: str = "",
        user_agent: str = "",
    ) -> Tuple[Optional[User], Optional[str], Optional[str]]:
        """认证飞书用户
        
        Args:
            feishu_user_info: 飞书用户信息
            ip_address: 登录IP
            user_agent: 用户代理
        
        Returns:
            (user, token, error_message)
        """
        open_id = feishu_user_info.get("open_id")
        union_id = feishu_user_info.get("union_id")
        
        if not open_id and not union_id:
            return None, None, "Invalid Feishu user info"
        
        # 查找已有用户
        user = None
        if open_id:
            user = self.user_store.get_user_by_feishu_open_id(open_id)
        if not user and union_id:
            user = self.user_store.get_user_by_feishu_union_id(union_id)
        
        now = datetime.now().isoformat()
        
        if user:
            # 更新用户信息
            user.name = feishu_user_info.get("name", user.name)
            user.email = feishu_user_info.get("email", user.email)
            user.mobile = feishu_user_info.get("mobile", user.mobile)
            user.avatar = feishu_user_info.get("avatar", user.avatar)
            user.feishu_user_id = feishu_user_info.get("user_id", user.feishu_user_id)
            user.last_login_at = now
            self.user_store.update_user(user)
        else:
            # 创建新用户
            user_data = {
                "feishu_open_id": open_id or "",
                "feishu_union_id": union_id or "",
                "feishu_user_id": feishu_user_info.get("user_id", ""),
                "name": feishu_user_info.get("name", ""),
                "email": feishu_user_info.get("email", ""),
                "mobile": feishu_user_info.get("mobile", ""),
                "avatar": feishu_user_info.get("avatar", ""),
                "employee_id": feishu_user_info.get("employee_id", ""),
                "department_id": feishu_user_info.get("department_id", ""),
                "department_name": feishu_user_info.get("department_name", ""),
                "job_title": feishu_user_info.get("job_title", ""),
                "role": "analyst",  # 默认角色
                "is_active": True,
                "last_login_at": now,
            }
            user = self.user_store.create_user(user_data)
        
        # 检查用户是否被禁用
        if not user.is_active:
            self._log_login(user.id, LoginType.FEISHU_QR, ip_address, user_agent, LoginStatus.FAILED, "User is disabled")
            return None, None, "User account is disabled"
        
        # 生成token
        token = generate_jwt_token(
            user_id=user.id,
            secret=self.jwt_secret,
            expires_hours=self.token_expires_hours,
            extra_claims={
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        )
        
        # 创建会话
        session_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(hours=self.token_expires_hours)).isoformat()
        
        session = SessionState(
            session_id=session_id,
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            created_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )
        self.user_store.create_session(session)
        
        # 记录登录日志
        self._log_login(user.id, LoginType.FEISHU_QR, ip_address, user_agent, LoginStatus.SUCCESS)
        
        return user, token, None
    
    def verify_token(self, token: str) -> Tuple[Optional[User], Optional[str]]:
        """验证token
        
        Args:
            token: JWT token
        
        Returns:
            (user, error_message)
        """
        # 验证JWT
        payload = verify_jwt_token(token, self.jwt_secret)
        if not payload:
            return None, "Invalid or expired token"
        
        user_id = payload.get("sub")
        if not user_id:
            return None, "Invalid token payload"
        
        # 获取用户
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return None, "User not found"
        
        if not user.is_active:
            return None, "User account is disabled"
        
        # 检查会话是否有效
        session = self.user_store.get_session_by_token(token)
        if session and not session.is_active:
            return None, "Session has been revoked"
        
        return user, None
    
    def logout(self, token: str) -> bool:
        """登出
        
        Args:
            token: JWT token
        
        Returns:
            是否成功
        """
        session = self.user_store.get_session_by_token(token)
        if session:
            session.is_active = False
            self.user_store.update_session(session)
            return True
        return False
    
    def refresh_token(self, token: str) -> Tuple[Optional[str], Optional[str]]:
        """刷新token
        
        Args:
            token: 当前token
        
        Returns:
            (new_token, error_message)
        """
        user, error = self.verify_token(token)
        if not user:
            return None, error
        
        # 使旧token失效
        old_session = self.user_store.get_session_by_token(token)
        if old_session:
            old_session.is_active = False
            self.user_store.update_session(old_session)
        
        # 生成新token
        new_token = generate_jwt_token(
            user_id=user.id,
            secret=self.jwt_secret,
            expires_hours=self.token_expires_hours,
            extra_claims={
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        )
        
        # 创建新会话
        session_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(hours=self.token_expires_hours)).isoformat()
        
        session = SessionState(
            session_id=session_id,
            user_id=user.id,
            token=new_token,
            expires_at=expires_at,
            created_at=datetime.now().isoformat(),
            ip_address=old_session.ip_address if old_session else "",
            user_agent=old_session.user_agent if old_session else "",
            is_active=True,
        )
        self.user_store.create_session(session)
        
        return new_token, None
    
    def _log_login(
        self,
        user_id: str,
        login_type: str,
        ip_address: str,
        user_agent: str,
        status: str,
        error_msg: str = "",
    ) -> None:
        """记录登录日志"""
        log = LoginLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            login_type=login_type,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_msg=error_msg,
            created_at=datetime.now().isoformat(),
        )
        self.user_store.create_login_log(log)
    
    def get_current_user(self, token: str) -> Optional[User]:
        """获取当前用户"""
        user, _ = self.verify_token(token)
        return user

    def register_user(
        self,
        username: str,
        password: str,
        name: str = "",
        role: str = "analyst",
    ) -> Tuple[Optional[User], Optional[str]]:
        """注册用户

        Args:
            username: 用户名
            password: 密码
            name: 显示名称
            role: 角色

        Returns:
            (user, error_message)
        """
        # 检查用户名是否已存在
        existing_user = self.user_store.get_user_by_username(username)
        if existing_user:
            return None, "Username already exists"

        # 创建新用户
        now = datetime.now().isoformat()
        user_data = {
            "username": username,
            "password_hash": hash_password(password),
            "name": name or username,
            "role": role,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        user = self.user_store.create_user(user_data)
        return user, None

    def authenticate_by_password(
        self,
        username: str,
        password: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Tuple[Optional[User], Optional[str], Optional[str]]:
        """使用用户名密码认证

        Args:
            username: 用户名
            password: 密码
            ip_address: 登录IP
            user_agent: 用户代理

        Returns:
            (user, token, error_message)
        """
        # 查找用户
        user = self.user_store.get_user_by_username(username)
        if not user:
            self._log_login("", LoginType.PASSWORD, ip_address, user_agent, LoginStatus.FAILED, "User not found")
            return None, None, "Invalid username or password"

        # 验证密码
        if not verify_password(password, user.password_hash):
            self._log_login(user.id, LoginType.PASSWORD, ip_address, user_agent, LoginStatus.FAILED, "Invalid password")
            return None, None, "Invalid username or password"

        # 检查用户是否被禁用
        if not user.is_active:
            self._log_login(user.id, LoginType.PASSWORD, ip_address, user_agent, LoginStatus.FAILED, "User is disabled")
            return None, None, "User account is disabled"

        # 更新登录时间
        now = datetime.now().isoformat()
        user.last_login_at = now
        self.user_store.update_user(user)

        # 生成token
        token = generate_jwt_token(
            user_id=user.id,
            secret=self.jwt_secret,
            expires_hours=self.token_expires_hours,
            extra_claims={
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        )

        # 创建会话
        session_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(hours=self.token_expires_hours)).isoformat()

        session = SessionState(
            session_id=session_id,
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            created_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )
        self.user_store.create_session(session)

        # 记录登录日志
        self._log_login(user.id, LoginType.PASSWORD, ip_address, user_agent, LoginStatus.SUCCESS)

        return user, token, None
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话
        
        Returns:
            清理的会话数量
        """
        count = 0
        # 这里可以遍历所有会话并清理过期的
        # 为了性能考虑，可以定期执行而不是每次请求都执行
        return count
