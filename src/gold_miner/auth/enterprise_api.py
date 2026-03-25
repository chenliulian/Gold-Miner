"""Enterprise Employee System API Integration.

This module provides integration with enterprise employee systems for:
- Organization structure synchronization
- Employee information lookup
- Department management
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class EmployeeInfo:
    """Employee information from enterprise system."""
    employee_id: str
    name: str
    email: str
    department_id: str
    department_name: str
    job_title: str
    manager_id: Optional[str] = None
    entry_date: Optional[str] = None
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "email": self.email,
            "department_id": self.department_id,
            "department_name": self.department_name,
            "job_title": self.job_title,
            "manager_id": self.manager_id,
            "entry_date": self.entry_date,
            "status": self.status,
        }


@dataclass
class DepartmentInfo:
    """Department information from enterprise system."""
    department_id: str
    name: str
    parent_id: Optional[str] = None
    leader_id: Optional[str] = None
    member_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "department_id": self.department_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "leader_id": self.leader_id,
            "member_count": self.member_count,
        }


class EnterpriseAPIError(Exception):
    """Enterprise API error."""
    pass


class EnterpriseAPIClient:
    """Client for enterprise employee system API.
    
    Supports multiple integration modes:
    1. Standard REST API - Real-time queries
    2. Feishu API - Using Feishu as the enterprise system
    3. CSV Import - Manual import for systems without API
    """
    
    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        integration_mode: str = "feishu",  # "api", "feishu", "csv"
        feishu_auth=None,
    ):
        self.api_base_url = api_base_url or os.getenv("ENTERPRISE_API_URL", "")
        self.api_key = api_key or os.getenv("ENTERPRISE_API_KEY", "")
        self.integration_mode = integration_mode
        self.feishu_auth = feishu_auth
        
        # Cache for employee data
        self._employee_cache: Dict[str, EmployeeInfo] = {}
        self._department_cache: Dict[str, DepartmentInfo] = {}
        self._cache_timestamp: Optional[datetime] = None
    
    def is_configured(self) -> bool:
        """Check if enterprise API is configured."""
        if self.integration_mode == "feishu":
            return self.feishu_auth is not None
        elif self.integration_mode == "api":
            return bool(self.api_base_url and self.api_key)
        return False
    
    def get_employee_by_id(self, employee_id: str) -> Optional[EmployeeInfo]:
        """Get employee information by employee ID.
        
        Args:
            employee_id: Employee ID/number
            
        Returns:
            EmployeeInfo if found, None otherwise
        """
        if self.integration_mode == "feishu" and self.feishu_auth:
            return self._get_employee_from_feishu(employee_id)
        elif self.integration_mode == "api":
            return self._get_employee_from_api(employee_id)
        return None
    
    def get_employee_by_email(self, email: str) -> Optional[EmployeeInfo]:
        """Get employee information by email.
        
        Args:
            email: Employee email address
            
        Returns:
            EmployeeInfo if found, None otherwise
        """
        if self.integration_mode == "api":
            return self._get_employee_from_api_by_email(email)
        
        # For Feishu, we need to search through users
        # This is a simplified implementation
        return None
    
    def get_department_members(self, department_id: str) -> List[EmployeeInfo]:
        """Get all members of a department.
        
        Args:
            department_id: Department ID
            
        Returns:
            List of EmployeeInfo
        """
        if self.integration_mode == "feishu" and self.feishu_auth:
            return self._get_department_members_from_feishu(department_id)
        elif self.integration_mode == "api":
            return self._get_department_members_from_api(department_id)
        return []
    
    def get_department_tree(self) -> List[DepartmentInfo]:
        """Get the complete department tree.
        
        Returns:
            List of DepartmentInfo
        """
        if self.integration_mode == "feishu" and self.feishu_auth:
            return self._get_department_tree_from_feishu()
        elif self.integration_mode == "api":
            return self._get_department_tree_from_api()
        return []
    
    def sync_user_with_enterprise(self, user) -> bool:
        """Sync user information with enterprise system.
        
        Args:
            user: User object to sync
            
        Returns:
            True if sync was successful
        """
        # Try to find employee by email first
        employee = None
        if user.email:
            employee = self.get_employee_by_email(user.email)
        
        # If not found by email, try employee_id
        if not employee and user.employee_id:
            employee = self.get_employee_by_id(user.employee_id)
        
        if employee:
            # Update user with enterprise data
            user.employee_id = employee.employee_id
            user.department_id = employee.department_id
            user.department_name = employee.department_name
            user.job_title = employee.job_title
            return True
        
        return False
    
    # ========== Feishu Integration Methods ==========
    
    def _get_employee_from_feishu(self, employee_id: str) -> Optional[EmployeeInfo]:
        """Get employee from Feishu."""
        # Get tenant access token
        tenant_token = self.feishu_auth._get_tenant_access_token()
        if not tenant_token:
            return None
        
        # Search user by employee_id
        url = f"{self.feishu_auth.BASE_URL}/contact/v3/users"
        headers = {"Authorization": f"Bearer {tenant_token}"}
        params = {"employee_id": employee_id}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                return None
            
            users = result.get("data", {}).get("items", [])
            if not users:
                return None
            
            user = users[0]
            return self._parse_feishu_user(user)
            
        except requests.RequestException:
            return None
    
    def _get_department_members_from_feishu(self, department_id: str) -> List[EmployeeInfo]:
        """Get department members from Feishu."""
        tenant_token = self.feishu_auth._get_tenant_access_token()
        if not tenant_token:
            return []
        
        url = f"{self.feishu_auth.BASE_URL}/contact/v3/users"
        headers = {"Authorization": f"Bearer {tenant_token}"}
        params = {
            "department_id": department_id,
            "page_size": 50,
        }
        
        members = []
        page_token = None
        
        try:
            while True:
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                result = response.json()
                
                if result.get("code") != 0:
                    break
                
                data = result.get("data", {})
                users = data.get("items", [])
                
                for user in users:
                    employee = self._parse_feishu_user(user)
                    if employee:
                        members.append(employee)
                
                page_token = data.get("page_token")
                if not page_token or not data.get("has_more"):
                    break
            
            return members
            
        except requests.RequestException:
            return []
    
    def _get_department_tree_from_feishu(self) -> List[DepartmentInfo]:
        """Get department tree from Feishu."""
        tenant_token = self.feishu_auth._get_tenant_access_token()
        if not tenant_token:
            return []
        
        url = f"{self.feishu_auth.BASE_URL}/contact/v3/departments"
        headers = {"Authorization": f"Bearer {tenant_token}"}
        params = {"page_size": 50}
        
        departments = []
        page_token = None
        
        try:
            while True:
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                result = response.json()
                
                if result.get("code") != 0:
                    break
                
                data = result.get("data", {})
                items = data.get("items", [])
                
                for dept in items:
                    departments.append(DepartmentInfo(
                        department_id=dept.get("department_id", ""),
                        name=dept.get("name", ""),
                        parent_id=dept.get("parent_department_id"),
                        leader_id=dept.get("leader_user_id"),
                        member_count=dept.get("member_count", 0),
                    ))
                
                page_token = data.get("page_token")
                if not page_token or not data.get("has_more"):
                    break
            
            return departments
            
        except requests.RequestException:
            return []
    
    def _parse_feishu_user(self, user: Dict[str, Any]) -> Optional[EmployeeInfo]:
        """Parse Feishu user data to EmployeeInfo."""
        try:
            return EmployeeInfo(
                employee_id=user.get("employee_id", user.get("user_id", "")),
                name=user.get("name", ""),
                email=user.get("email", ""),
                department_id=user.get("department_ids", [""])[0] if user.get("department_ids") else "",
                department_name="",  # Would need separate lookup
                job_title=user.get("job_title", ""),
                manager_id=user.get("manager_user_id"),
                status="active" if not user.get("status") or user.get("status") == 1 else "inactive",
            )
        except Exception:
            return None
    
    # ========== Standard API Methods ==========
    
    def _get_employee_from_api(self, employee_id: str) -> Optional[EmployeeInfo]:
        """Get employee from standard REST API."""
        if not self.api_base_url:
            return None
        
        url = f"{self.api_base_url}/employees/{employee_id}"
        headers = self._get_api_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return EmployeeInfo(**data)
            return None
        except requests.RequestException:
            return None
    
    def _get_employee_from_api_by_email(self, email: str) -> Optional[EmployeeInfo]:
        """Get employee from API by email."""
        if not self.api_base_url:
            return None
        
        url = f"{self.api_base_url}/employees"
        headers = self._get_api_headers()
        params = {"email": email}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return EmployeeInfo(**data[0])
            return None
        except requests.RequestException:
            return None
    
    def _get_department_members_from_api(self, department_id: str) -> List[EmployeeInfo]:
        """Get department members from API."""
        if not self.api_base_url:
            return []
        
        url = f"{self.api_base_url}/departments/{department_id}/members"
        headers = self._get_api_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return [EmployeeInfo(**emp) for emp in data]
            return []
        except requests.RequestException:
            return []
    
    def _get_department_tree_from_api(self) -> List[DepartmentInfo]:
        """Get department tree from API."""
        if not self.api_base_url:
            return []
        
        url = f"{self.api_base_url}/departments"
        headers = self._get_api_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return [DepartmentInfo(**dept) for dept in data]
            return []
        except requests.RequestException:
            return []
    
    def _get_api_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Global instance
_enterprise_api_client: Optional[EnterpriseAPIClient] = None


def get_enterprise_api_client(
    feishu_auth=None,
    api_base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    integration_mode: str = "feishu",
) -> EnterpriseAPIClient:
    """Get the global EnterpriseAPIClient instance."""
    global _enterprise_api_client
    if _enterprise_api_client is None:
        _enterprise_api_client = EnterpriseAPIClient(
            api_base_url=api_base_url,
            api_key=api_key,
            integration_mode=integration_mode,
            feishu_auth=feishu_auth,
        )
    return _enterprise_api_client


def init_enterprise_api_client(
    feishu_auth=None,
    api_base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    integration_mode: str = "feishu",
) -> EnterpriseAPIClient:
    """Initialize the global EnterpriseAPIClient instance."""
    global _enterprise_api_client
    _enterprise_api_client = EnterpriseAPIClient(
        api_base_url=api_base_url,
        api_key=api_key,
        integration_mode=integration_mode,
        feishu_auth=feishu_auth,
    )
    return _enterprise_api_client
