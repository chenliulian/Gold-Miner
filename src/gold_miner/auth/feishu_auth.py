"""Feishu (Lark) SSO integration."""

from __future__ import annotations

import json
import secrets
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode

import requests


class FeishuAuthError(Exception):
    """飞书认证错误"""
    pass


class FeishuAuth:
    """飞书SSO认证"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        redirect_uri: str = "",
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        
        # 临时存储state（生产环境应使用Redis等）
        self._state_store: Dict[str, Dict[str, Any]] = {}
    
    def generate_qr_state(self) -> str:
        """生成二维码登录的state参数"""
        state = secrets.token_urlsafe(32)
        self._state_store[state] = {
            "created_at": time.time(),
            "used": False,
        }
        return state
    
    def verify_state(self, state: str) -> bool:
        """验证state是否有效"""
        if state not in self._state_store:
            return False
        
        state_data = self._state_store[state]
        
        # 检查是否已使用
        if state_data.get("used"):
            return False
        
        # 检查是否过期（10分钟）
        created_at = state_data.get("created_at", 0)
        if time.time() - created_at > 600:
            return False
        
        return True
    
    def mark_state_used(self, state: str) -> None:
        """标记state为已使用"""
        if state in self._state_store:
            self._state_store[state]["used"] = True
    
    def get_qr_url(self, state: str, redirect_uri: str = None) -> str:
        """获取飞书扫码登录URL
        
        Args:
            state: 随机状态参数
            redirect_uri: 可选的自定义回调地址，默认使用初始化时的地址
        
        Returns:
            飞书扫码登录URL
        """
        params = {
            "app_id": self.app_id,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "state": state,
        }
        return f"https://open.feishu.cn/open-apis/authen/v1/index?{urlencode(params)}"
    
    def get_access_token_by_code(self, code: str) -> Tuple[Optional[str], Optional[str]]:
        """用授权码换取access_token
        
        Args:
            code: 飞书授权码
        
        Returns:
            (access_token, error_message)
        """
        url = f"{self.BASE_URL}/authen/v1/access_token"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
        }
        
        # 获取app_access_token
        app_token = self._get_app_access_token()
        if not app_token:
            return None, "Failed to get app access token"
        
        headers["Authorization"] = f"Bearer {app_token}"
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                return None, f"Feishu API error: {result.get('msg', 'Unknown error')}"
            
            data = result.get("data", {})
            access_token = data.get("access_token")
            
            return access_token, None
            
        except requests.RequestException as e:
            return None, f"Request failed: {str(e)}"
    
    def get_user_info(self, access_token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """获取用户信息
        
        Args:
            access_token: 飞书access_token
        
        Returns:
            (user_info, error_message)
        """
        url = f"{self.BASE_URL}/authen/v1/user_info"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                return None, f"Feishu API error: {result.get('msg', 'Unknown error')}"
            
            data = result.get("data", {})
            
            # 标准化用户信息
            user_info = {
                "open_id": data.get("open_id"),
                "union_id": data.get("union_id"),
                "user_id": data.get("user_id"),
                "name": data.get("name", ""),
                "email": data.get("email", ""),
                "mobile": data.get("mobile", ""),
                "avatar": data.get("avatar_url", ""),
            }
            
            return user_info, None
            
        except requests.RequestException as e:
            return None, f"Request failed: {str(e)}"
    
    def _get_app_access_token(self) -> Optional[str]:
        """获取app_access_token（内部使用）"""
        url = f"{self.BASE_URL}/auth/v3/app_access_token/internal"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                return None
            
            return result.get("app_access_token")
            
        except requests.RequestException:
            return None
    
    def get_user_detail(self, user_access_token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """获取用户详细信息（需要user_access_token）
        
        Args:
            user_access_token: 用户访问token
        
        Returns:
            (user_detail, error_message)
        """
        url = f"{self.BASE_URL}/authen/v1/user_info"
        
        headers = {
            "Authorization": f"Bearer {user_access_token}",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                return None, f"Feishu API error: {result.get('msg', 'Unknown error')}"
            
            return result.get("data"), None
            
        except requests.RequestException as e:
            return None, f"Request failed: {str(e)}"
    
    def get_department_list(self, user_access_token: str) -> Tuple[Optional[list], Optional[str]]:
        """获取用户部门列表
        
        Args:
            user_access_token: 用户访问token
        
        Returns:
            (departments, error_message)
        """
        url = f"{self.BASE_URL}/contact/v3/departments"
        
        headers = {
            "Authorization": f"Bearer {user_access_token}",
        }
        
        params = {
            "page_size": 50,
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                return None, f"Feishu API error: {result.get('msg', 'Unknown error')}"
            
            data = result.get("data", {})
            departments = data.get("items", [])
            
            return departments, None
            
        except requests.RequestException as e:
            return None, f"Request failed: {str(e)}"
    
    def get_user_info_by_id(self, user_id: str, tenant_access_token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """通过用户ID获取用户信息（需要tenant_access_token）
        
        Args:
            user_id: 飞书用户ID
            tenant_access_token: 租户访问token
        
        Returns:
            (user_info, error_message)
        """
        url = f"{self.BASE_URL}/contact/v3/users/{user_id}"
        
        headers = {
            "Authorization": f"Bearer {tenant_access_token}",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                return None, f"Feishu API error: {result.get('msg', 'Unknown error')}"
            
            return result.get("data", {}).get("user"), None
            
        except requests.RequestException as e:
            return None, f"Request failed: {str(e)}"
    
    def _get_tenant_access_token(self) -> Optional[str]:
        """获取tenant_access_token（内部使用）"""
        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                return None
            
            return result.get("tenant_access_token")
            
        except requests.RequestException:
            return None
