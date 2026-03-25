"""JWT token utilities."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


def generate_jwt_token(
    user_id: str,
    secret: str,
    expires_hours: int = 8,
    extra_claims: Optional[Dict[str, Any]] = None
) -> str:
    """生成JWT token
    
    Args:
        user_id: 用户ID
        secret: JWT密钥
        expires_hours: 过期时间（小时）
        extra_claims: 额外声明
    
    Returns:
        JWT token字符串
    """
    if not JWT_AVAILABLE:
        raise ImportError("PyJWT is required. Install with: pip install PyJWT")
    
    now = datetime.utcnow()
    expires = now + timedelta(hours=expires_hours)
    
    payload = {
        "sub": user_id,  # subject (user_id)
        "jti": str(uuid.uuid4()),  # JWT ID
        "iat": now,  # issued at
        "exp": expires,  # expiration
        "type": "access",
    }
    
    if extra_claims:
        payload.update(extra_claims)
    
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_jwt_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """验证JWT token
    
    Args:
        token: JWT token字符串
        secret: JWT密钥
    
    Returns:
        解码后的payload，验证失败返回None
    """
    if not JWT_AVAILABLE:
        raise ImportError("PyJWT is required. Install with: pip install PyJWT")
    
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_jwt_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """仅解码JWT token（不验证签名）
    
    用于调试或获取token中的信息
    """
    if not JWT_AVAILABLE:
        raise ImportError("PyJWT is required. Install with: pip install PyJWT")
    
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.InvalidTokenError:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """获取token过期时间"""
    payload = decode_jwt_without_verification(token)
    if payload and "exp" in payload:
        exp_timestamp = payload["exp"]
        return datetime.utcfromtimestamp(exp_timestamp)
    return None


def is_token_expired(token: str) -> bool:
    """检查token是否已过期"""
    expiry = get_token_expiry(token)
    if expiry:
        return datetime.utcnow() > expiry
    return True
