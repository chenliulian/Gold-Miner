"""User LLM configuration service with encryption support."""

from __future__ import annotations

import os
import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .models import User, UserLLMConfig
from .user_store import UserStore


@dataclass
class LLMConfigInput:
    """LLM 配置输入"""
    api_key: str
    base_url: str
    model: str = ""
    provider: str = "anthropic"


@dataclass
class LLMConfigResult:
    """LLM 配置结果"""
    success: bool
    message: str
    error_type: str = ""  # validation_error, connection_failed, auth_failed, api_error, unknown
    config: Optional[Dict[str, Any]] = None


class UserLLMConfigService:
    """用户 LLM 配置服务"""
    
    def __init__(self, user_store: UserStore, encryption_key: Optional[str] = None):
        self.user_store = user_store
        self._encryption_key = encryption_key or os.getenv("USER_API_KEY_ENCRYPTION_KEY", "")
        self._fernet = self._init_fernet() if self._encryption_key else None
    
    def _init_fernet(self) -> Optional[Fernet]:
        """初始化 Fernet 加密器"""
        try:
            # 使用 PBKDF2 从密钥派生 32 字节密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"gold_miner_user_api_key_salt",  # 固定 salt，可考虑每用户不同
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self._encryption_key.encode()))
            return Fernet(key)
        except Exception:
            return None
    
    def _encrypt(self, plaintext: str) -> str:
        """加密文本"""
        if not self._fernet:
            # 未配置加密密钥，返回明文（不推荐生产环境使用）
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
    
    def get_user_llm_config(self, user_id: str) -> Optional[Dict[str, str]]:
        """获取用户的 LLM 配置（解密后）"""
        user = self.user_store.get_user_by_id(user_id)
        if not user or not user.llm_config.is_configured():
            return None
        
        try:
            api_key = self._decrypt(user.llm_config.api_key_encrypted)
            return {
                "api_key": api_key,
                "base_url": user.llm_config.base_url,
                "model": user.llm_config.model,
                "provider": user.llm_config.provider,
            }
        except Exception:
            return None
    
    def get_user_llm_config_masked(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的 LLM 配置（脱敏）"""
        user = self.user_store.get_user_by_id(user_id)
        if not user or not user.llm_config.is_configured():
            return None
        
        return {
            "has_custom_config": True,
            "base_url": user.llm_config.base_url,
            "model": user.llm_config.model,
            "provider": user.llm_config.provider,
            "api_key_masked": self._mask_api_key(
                self._decrypt(user.llm_config.api_key_encrypted)
            ),
            "updated_at": user.llm_config.updated_at,
        }
    
    def validate_config(self, config: LLMConfigInput) -> Tuple[bool, str]:
        """验证配置格式"""
        if not config.api_key:
            return False, "API Key 不能为空"
        
        if not config.base_url:
            return False, "Base URL 不能为空"
        
        if not config.base_url.startswith(("http://", "https://")):
            return False, "Base URL 格式不正确，应以 http:// 或 https:// 开头"
        
        return True, ""
    
    def test_config(self, config: LLMConfigInput) -> Tuple[bool, str, str]:
        """测试 LLM 配置是否可用
        
        Returns:
            (success, error_type, message)
        """
        import requests
        
        try:
            # 根据 provider 选择测试方式
            if config.provider == "anthropic":
                return self._test_anthropic(config)
            else:
                return self._test_openai_compatible(config)
                
        except requests.exceptions.ConnectionError:
            return False, "connection_failed", "无法连接到 LLM 服务，请检查 Base URL 是否正确"
        except requests.exceptions.Timeout:
            return False, "timeout", "连接超时，请检查网络或稍后重试"
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            if status_code == 401:
                return False, "auth_failed", "API Key 认证失败，请检查 Key 是否正确"
            elif status_code == 403:
                return False, "auth_failed", "API Key 没有权限访问该资源"
            else:
                return False, "api_error", f"API 返回错误: HTTP {status_code}"
        except Exception as e:
            return False, "unknown", f"测试失败: {str(e)}"
    
    def _test_anthropic(self, config: LLMConfigInput) -> Tuple[bool, str, str]:
        """测试 Anthropic API"""
        import requests
        
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        data = {
            "model": config.model or "claude-3-5-sonnet-20241022",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hi"}],
        }
        
        response = requests.post(
            f"{config.base_url.rstrip('/')}/messages",
            headers=headers,
            json=data,
            timeout=30,
        )
        response.raise_for_status()
        
        return True, "", "连接成功"
    
    def _test_openai_compatible(self, config: LLMConfigInput) -> Tuple[bool, str, str]:
        """测试 OpenAI 兼容 API"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": config.model or "gpt-3.5-turbo",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hi"}],
        }
        
        response = requests.post(
            f"{config.base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=data,
            timeout=30,
        )
        response.raise_for_status()
        
        return True, "", "连接成功"
    
    def save_config(self, user_id: str, config: LLMConfigInput) -> LLMConfigResult:
        """保存用户 LLM 配置（包含验证和测试）"""
        # 1. 验证格式
        valid, error_msg = self.validate_config(config)
        if not valid:
            return LLMConfigResult(
                success=False,
                message=error_msg,
                error_type="validation_error",
            )
        
        # 2. 测试连接
        test_success, error_type, test_msg = self.test_config(config)
        if not test_success:
            return LLMConfigResult(
                success=False,
                message=test_msg,
                error_type=error_type,
            )
        
        # 3. 保存配置
        try:
            user = self.user_store.get_user_by_id(user_id)
            if not user:
                return LLMConfigResult(
                    success=False,
                    message="用户不存在",
                    error_type="unknown",
                )
            
            now = datetime.now().isoformat()
            encrypted_key = self._encrypt(config.api_key)
            
            user.llm_config = UserLLMConfig(
                api_key_encrypted=encrypted_key,
                base_url=config.base_url,
                model=config.model,
                provider=config.provider,
                created_at=user.llm_config.created_at or now,
                updated_at=now,
            )
            
            self.user_store.update_user(user)
            
            return LLMConfigResult(
                success=True,
                message="配置验证成功并已保存",
                config={
                    "base_url": config.base_url,
                    "model": config.model,
                    "provider": config.provider,
                    "api_key_masked": self._mask_api_key(config.api_key),
                    "updated_at": now,
                },
            )
            
        except Exception as e:
            return LLMConfigResult(
                success=False,
                message=f"保存配置失败: {str(e)}",
                error_type="unknown",
            )
    
    def delete_config(self, user_id: str) -> bool:
        """删除用户 LLM 配置"""
        try:
            user = self.user_store.get_user_by_id(user_id)
            if not user:
                return False
            
            user.llm_config = UserLLMConfig()  # 重置为空配置
            self.user_store.update_user(user)
            return True
        except Exception:
            return False
    
    def need_llm_config(self, user_id: str) -> bool:
        """检查用户是否需要配置 LLM"""
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return True
        return not user.llm_config.is_configured()


# 全局服务实例
_llm_config_service: Optional[UserLLMConfigService] = None


def get_llm_config_service(user_store: Optional[UserStore] = None) -> UserLLMConfigService:
    """获取 LLM 配置服务实例"""
    global _llm_config_service
    if _llm_config_service is None:
        if user_store is None:
            user_store = UserStore()
        _llm_config_service = UserLLMConfigService(user_store)
    return _llm_config_service
