"""Data models for authentication system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class LoginStatus(str, Enum):
    """登录状态"""
    SUCCESS = "success"
    FAILED = "failed"


class LoginType(str, Enum):
    """登录类型"""
    FEISHU_QR = "feishu_qr"
    FEISHU_AUTO = "feishu_auto"
    PASSWORD = "password"


# 权限定义
PERMISSIONS = {
    # 对话相关
    "chat:query": "执行数据查询对话",
    "chat:export": "导出对话内容",
    
    # 报告相关
    "export:report": "导出分析报告",
    "view:dashboard": "查看仪表板",
    
    # 管理相关
    "admin:user": "管理用户",
    "admin:sync": "同步企业数据",
    "admin:config": "系统配置",
}

# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.ADMIN: list(PERMISSIONS.keys()),
    UserRole.ANALYST: [
        "chat:query",
        "chat:export",
        "export:report",
        "view:dashboard",
    ],
    UserRole.VIEWER: [
        "view:dashboard",
    ],
}


@dataclass
class User:
    """用户模型"""
    
    # 主键
    id: str  # UUID
    
    # 飞书信息
    feishu_open_id: str = ""  # 飞书用户唯一标识
    feishu_union_id: str = ""  # 飞书union_id
    feishu_user_id: str = ""  # 飞书user_id
    
    # 基本信息
    name: str = ""  # 用户姓名
    email: str = ""  # 邮箱
    mobile: str = ""  # 手机号（脱敏）
    avatar: str = ""  # 头像URL
    
    # 本地账号信息
    username: str = ""  # 用户名（用于密码登录）
    password_hash: str = ""  # 密码哈希
    
    # 企业信息
    employee_id: str = ""  # 员工工号
    department_id: str = ""  # 部门ID
    department_name: str = ""  # 部门名称
    job_title: str = ""  # 职位
    
    # 权限控制
    role: str = "analyst"  # 角色: admin/analyst/viewer
    is_active: bool = True  # 是否启用
    permissions: List[str] = field(default_factory=list)  # 权限列表
    
    # 时间戳
    created_at: str = ""  # 首次注册时间
    updated_at: str = ""  # 信息更新时间
    last_login_at: str = ""  # 最后登录时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "feishu_open_id": self.feishu_open_id,
            "feishu_union_id": self.feishu_union_id,
            "feishu_user_id": self.feishu_user_id,
            "name": self.name,
            "email": self.email,
            "mobile": self.mobile,
            "avatar": self.avatar,
            "username": self.username,
            "password_hash": self.password_hash,
            "employee_id": self.employee_id,
            "department_id": self.department_id,
            "department_name": self.department_name,
            "job_title": self.job_title,
            "role": self.role,
            "is_active": self.is_active,
            "permissions": self.permissions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login_at": self.last_login_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            feishu_open_id=data.get("feishu_open_id", ""),
            feishu_union_id=data.get("feishu_union_id", ""),
            feishu_user_id=data.get("feishu_user_id", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            mobile=data.get("mobile", ""),
            avatar=data.get("avatar", ""),
            username=data.get("username", ""),
            password_hash=data.get("password_hash", ""),
            employee_id=data.get("employee_id", ""),
            department_id=data.get("department_id", ""),
            department_name=data.get("department_name", ""),
            job_title=data.get("job_title", ""),
            role=data.get("role", "analyst"),
            is_active=data.get("is_active", True),
            permissions=data.get("permissions", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            last_login_at=data.get("last_login_at", ""),
        )
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        if self.role == UserRole.ADMIN:
            return True
        if permission in self.permissions:
            return True
        role_perms = ROLE_PERMISSIONS.get(self.role, [])
        return permission in role_perms


@dataclass
class LoginLog:
    """登录审计日志"""
    
    id: str
    user_id: str
    login_type: str  # feishu_qr / feishu_auto
    ip_address: str
    user_agent: str
    status: str  # success / failed
    error_msg: str = ""  # 失败原因
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "login_type": self.login_type,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_msg": self.error_msg,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoginLog":
        return cls(
            id=data.get("id", ""),
            user_id=data.get("user_id", ""),
            login_type=data.get("login_type", ""),
            ip_address=data.get("ip_address", ""),
            user_agent=data.get("user_agent", ""),
            status=data.get("status", ""),
            error_msg=data.get("error_msg", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass
class SessionState:
    """登录会话状态"""
    
    session_id: str
    user_id: str
    token: str  # JWT token
    expires_at: str  # 过期时间 ISO格式
    created_at: str
    ip_address: str
    user_agent: str
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "token": self.token,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            token=data.get("token", ""),
            expires_at=data.get("expires_at", ""),
            created_at=data.get("created_at", ""),
            ip_address=data.get("ip_address", ""),
            user_agent=data.get("user_agent", ""),
            is_active=data.get("is_active", True),
        )
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        if not self.expires_at:
            return True
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expires
        except:
            return True
