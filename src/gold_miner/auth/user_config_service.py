"""User configuration service for LLM, ODPS, and Tavily settings."""

from __future__ import annotations

import os
import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .models import User, UserLLMConfig, UserODPSConfig, UserTavilyConfig
from .user_store import UserStore


@dataclass
class UserConfigInput:
    """用户配置输入"""
    # LLM 配置
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    llm_provider: str = "anthropic"
    # ODPS 配置
    odps_access_id: str = ""
    odps_access_key: str = ""
    odps_project: str = ""
    odps_endpoint: str = ""
    odps_quota: str = ""
    # Tavily 配置
    tavily_api_key: str = ""


@dataclass
class UserConfigResult:
    """用户配置结果"""
    success: bool
    message: str
    error_type: str = ""  # validation_error, connection_failed, auth_failed
    config: Optional[Dict[str, Any]] = None


class UserConfigService:
    """用户配置服务 - 统一管理 LLM、ODPS、Tavily 配置"""
    
    def __init__(self, user_store: UserStore, encryption_key: Optional[str] = None):
        self.user_store = user_store
        self._encryption_key = encryption_key or os.getenv("USER_API_KEY_ENCRYPTION_KEY", "")
        self._fernet = self._init_fernet() if self._encryption_key else None
    
    def _init_fernet(self) -> Optional[Fernet]:
        """初始化 Fernet 加密器"""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"gold_miner_user_api_key_salt",
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self._encryption_key.encode()))
            return Fernet(key)
        except Exception:
            return None
    
    def _encrypt(self, plaintext: str) -> str:
        """加密文本"""
        if not self._fernet:
            return f"plain:{plaintext}"
        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return f"enc:{encrypted.decode()}"
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")
    
    def _decrypt(self, ciphertext: str) -> str:
        """解密文本"""
        if ciphertext.startswith("plain:"):
            return ciphertext[6:]
        if ciphertext.startswith("enc:"):
            if not self._fernet:
                raise ValueError("Encryption key not configured, cannot decrypt")
            try:
                encrypted_data = ciphertext[4:].encode()
                decrypted = self._fernet.decrypt(encrypted_data)
                return decrypted.decode()
            except Exception as e:
                raise ValueError(f"Decryption failed: {e}")
        return ciphertext
    
    def _mask_api_key(self, api_key: str) -> str:
        """脱敏显示 API Key"""
        if len(api_key) <= 8:
            return "****"
        return f"{api_key[:4]}****{api_key[-4:]}"
    
    def get_user_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的完整配置（解密后）"""
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return None
        
        config = {
            "llm": None,
            "odps": None,
            "tavily": None,
        }
        
        # LLM 配置
        if user.llm_config.is_configured():
            try:
                config["llm"] = {
                    "api_key": self._decrypt(user.llm_config.api_key_encrypted),
                    "base_url": user.llm_config.base_url,
                    "model": user.llm_config.model,
                    "provider": user.llm_config.provider,
                }
            except Exception:
                pass
        
        # ODPS 配置
        if user.odps_config.is_configured():
            try:
                config["odps"] = {
                    "access_id": user.odps_config.access_id,
                    "access_key": self._decrypt(user.odps_config.access_key_encrypted),
                    "project": user.odps_config.project,
                    "endpoint": user.odps_config.endpoint,
                    "quota": user.odps_config.quota,
                }
            except Exception:
                pass
        
        # Tavily 配置
        if user.tavily_config.is_configured():
            try:
                config["tavily"] = {
                    "api_key": self._decrypt(user.tavily_config.api_key_encrypted),
                }
            except Exception:
                pass
        
        return config
    
    def get_user_config_masked(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的配置（脱敏显示）"""
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return None
        
        config = {
            "llm": {
                "has_config": user.llm_config.is_configured(),
                "base_url": user.llm_config.base_url,
                "model": user.llm_config.model,
                "provider": user.llm_config.provider,
                "api_key_masked": self._mask_api_key(
                    self._decrypt(user.llm_config.api_key_encrypted)
                ) if user.llm_config.is_configured() else "",
            },
            "odps": {
                "has_config": user.odps_config.is_configured(),
                "access_id": user.odps_config.access_id,
                "project": user.odps_config.project,
                "endpoint": user.odps_config.endpoint,
                "quota": user.odps_config.quota,
                "access_key_masked": self._mask_api_key(
                    self._decrypt(user.odps_config.access_key_encrypted)
                ) if user.odps_config.is_configured() else "",
            },
            "tavily": {
                "has_config": user.tavily_config.is_configured(),
                "api_key_masked": self._mask_api_key(
                    self._decrypt(user.tavily_config.api_key_encrypted)
                ) if user.tavily_config.is_configured() else "",
            },
            "config_status": user.get_config_status(),
        }
        
        return config
    
    def validate_config(self, config: UserConfigInput, user: User = None) -> Tuple[bool, str]:
        """验证配置格式
        
        Args:
            config: 配置输入
            user: 当前用户（用于检查是否已有LLM配置）
        """
        # 验证 ODPS 配置（必填项）
        if not config.odps_access_id:
            return False, "ODPS Access ID 不能为空"
        if not config.odps_access_key:
            return False, "ODPS Access Key 不能为空"
        if not config.odps_project:
            return False, "ODPS Project 不能为空"
        if not config.odps_endpoint:
            return False, "ODPS Endpoint 不能为空"
        
        if not config.odps_endpoint.startswith(("http://", "https://")):
            return False, "ODPS Endpoint 格式不正确，应以 http:// 或 https:// 开头"
        
        # 验证 LLM 配置（仅当用户提供了新配置时才验证）
        # 如果用户已有LLM配置且没有提供新配置，则保留原有配置
        if config.llm_api_key or config.llm_base_url:
            if not config.llm_api_key:
                return False, "LLM API Key 不能为空"
            if not config.llm_base_url:
                return False, "LLM Base URL 不能为空"
            if not config.llm_base_url.startswith(("http://", "https://")):
                return False, "LLM Base URL 格式不正确，应以 http:// 或 https:// 开头"
        
        # Tavily 配置是可选的，不需要验证
        
        return True, ""
    
    def update_user_config(self, user_id: str, config: UserConfigInput) -> UserConfigResult:
        """更新用户配置"""
        # 先获取用户
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return UserConfigResult(
                success=False,
                message="用户不存在",
                error_type="not_found"
            )
        
        # 验证配置（传入用户对象，用于检查已有配置）
        valid, error_msg = self.validate_config(config, user)
        if not valid:
            return UserConfigResult(
                success=False,
                message=error_msg,
                error_type="validation_error"
            )
        
        now = datetime.now().isoformat()
        
        # 更新 LLM 配置（仅当提供了完整的新配置时才更新）
        # 如果用户没有提供 LLM 配置，但已有配置，则保留原有配置
        if config.llm_api_key and config.llm_base_url:
            user.llm_config = UserLLMConfig(
                api_key_encrypted=self._encrypt(config.llm_api_key),
                base_url=config.llm_base_url,
                model=config.llm_model,
                provider=config.llm_provider,
                created_at=user.llm_config.created_at or now,
                updated_at=now,
            )
        
        # 更新 ODPS 配置
        user.odps_config = UserODPSConfig(
            access_id=config.odps_access_id,
            access_key_encrypted=self._encrypt(config.odps_access_key),
            project=config.odps_project,
            endpoint=config.odps_endpoint,
            quota=config.odps_quota,
            created_at=user.odps_config.created_at or now,
            updated_at=now,
        )
        
        # 更新 Tavily 配置（如果提供了）
        if config.tavily_api_key:
            user.tavily_config = UserTavilyConfig(
                api_key_encrypted=self._encrypt(config.tavily_api_key),
                created_at=user.tavily_config.created_at or now,
                updated_at=now,
            )
        
        # 保存用户
        user.updated_at = now
        self.user_store.update_user(user)
        
        return UserConfigResult(
            success=True,
            message="配置更新成功",
            config=user.get_config_status()
        )
    
    def check_odps_required(self, user_id: str) -> Tuple[bool, str]:
        """检查 ODPS 配置是否已配置（必填项检查）"""
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return False, "用户不存在"
        
        if not user.is_odps_configured():
            return False, "请先配置 ODPS 参数"
        
        return True, ""
    
    def test_odps_connection(self, user_id: str) -> Tuple[bool, str]:
        """测试 ODPS 连接"""
        user = self.user_store.get_user_by_id(user_id)
        if not user or not user.odps_config.is_configured():
            return False, "ODPS 配置不完整"

        try:
            from ..odps_client import OdpsClient, OdpsConfig

            odps_config = OdpsConfig(
                access_id=user.odps_config.access_id,
                access_key=self._decrypt(user.odps_config.access_key_encrypted),
                project=user.odps_config.project,
                endpoint=user.odps_config.endpoint,
                quota=user.odps_config.quota,
            )

            client = OdpsClient(odps_config)
            # 尝试执行一个简单的查询来验证连接
            client.run_sql("SELECT 1", enable_log=False)

            return True, "ODPS 连接成功"
        except Exception as e:
            return False, f"ODPS 连接失败: {str(e)}"
