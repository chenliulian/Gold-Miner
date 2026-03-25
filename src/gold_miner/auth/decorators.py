"""Authentication decorators for Flask routes."""

from __future__ import annotations

import functools
from typing import Callable, Optional

from flask import request, jsonify, g

from .service import AuthService


def get_auth_service() -> Optional[AuthService]:
    """获取认证服务实例
    
    从Flask应用上下文中获取
    """
    from flask import current_app
    return getattr(current_app, "auth_service", None)


def get_token_from_request() -> Optional[str]:
    """从请求中提取token
    
    支持:
    - Authorization: Bearer <token>
    - Cookie: session_token=<token>
    - Query param: ?token=<token>
    """
    # 从Header获取
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    # 从Cookie获取
    token = request.cookies.get("session_token")
    if token:
        return token
    
    # 从Query参数获取
    token = request.args.get("token")
    if token:
        return token
    
    return None


def require_auth(f: Callable) -> Callable:
    """要求登录的装饰器
    
    验证JWT token，并将当前用户设置到g.current_user
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_service = get_auth_service()
        if not auth_service:
            return jsonify({
                "success": False,
                "error": "auth_service_not_initialized",
                "message": "Authentication service not initialized",
            }), 500
        
        token = get_token_from_request()
        if not token:
            return jsonify({
                "success": False,
                "error": "missing_token",
                "message": "Authentication token is required",
            }), 401
        
        user, error = auth_service.verify_token(token)
        if not user:
            return jsonify({
                "success": False,
                "error": "invalid_token",
                "message": error or "Invalid token",
            }), 401
        
        # 设置当前用户到Flask全局对象
        g.current_user = user
        g.current_token = token
        
        return f(*args, **kwargs)
    
    return decorated


def require_permission(permission: str) -> Callable:
    """要求特定权限的装饰器
    
    Args:
        permission: 需要的权限代码
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            auth_service = get_auth_service()
            if not auth_service:
                return jsonify({
                    "success": False,
                    "error": "auth_service_not_initialized",
                    "message": "Authentication service not initialized",
                }), 500
            
            token = get_token_from_request()
            if not token:
                return jsonify({
                    "success": False,
                    "error": "missing_token",
                    "message": "Authentication token is required",
                }), 401
            
            user, error = auth_service.verify_token(token)
            if not user:
                return jsonify({
                    "success": False,
                    "error": "invalid_token",
                    "message": error or "Invalid token",
                }), 401
            
            # 检查权限
            if not user.has_permission(permission):
                return jsonify({
                    "success": False,
                    "error": "permission_denied",
                    "message": f"Permission '{permission}' is required",
                }), 403
            
            # 设置当前用户
            g.current_user = user
            g.current_token = token
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def optional_auth(f: Callable) -> Callable:
    """可选认证装饰器
    
    如果提供了token则验证，否则继续执行
    用于一些既支持匿名又支持登录的接口
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_service = get_auth_service()
        if auth_service:
            token = get_token_from_request()
            if token:
                user, _ = auth_service.verify_token(token)
                if user:
                    g.current_user = user
                    g.current_token = token
        
        return f(*args, **kwargs)
    
    return decorated


def get_current_user():
    """获取当前登录用户
    
    需要在require_auth装饰器后使用
    """
    return getattr(g, "current_user", None)


def get_current_token():
    """获取当前token
    
    需要在require_auth装饰器后使用
    """
    return getattr(g, "current_token", None)
