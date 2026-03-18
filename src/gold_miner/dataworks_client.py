"""
DataWorks 数据地图 API 客户端

用于获取 ODPS 表的元数据、血缘关系等信息
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DataWorksConfig:
    """DataWorks 配置"""
    access_id: str
    access_key: str
    region_id: str
    
    @classmethod
    def from_env(cls) -> "DataWorksConfig":
        """从环境变量加载配置"""
        return cls(
            access_id=os.getenv("DATAWORKS_ACCESS_ID", os.getenv("ODPS_ACCESS_ID", "")),
            access_key=os.getenv("DATAWORKS_ACCESS_KEY", os.getenv("ODPS_ACCESS_KEY", "")),
            region_id=os.getenv("DATAWORKS_REGION_ID", "cn-shanghai"),
        )
    
    def validate(self) -> None:
        """验证配置是否完整"""
        if not self.access_id:
            raise ValueError("DATAWORKS_ACCESS_ID or ODPS_ACCESS_ID is required")
        if not self.access_key:
            raise ValueError("DATAWORKS_ACCESS_KEY or ODPS_ACCESS_KEY is required")


class DataWorksClient:
    """DataWorks 数据地图 API 客户端"""
    
    def __init__(self, config: DataWorksConfig):
        self.config = config
        self._client = None
        self._init_client()
    
    def _init_client(self) -> None:
        """初始化阿里云 SDK 客户端"""
        try:
            from aliyunsdkcore.client import AcsClient
            self._client = AcsClient(
                self.config.access_id,
                self.config.access_key,
                self.config.region_id
            )
        except ImportError:
            raise ImportError(
                "aliyun-python-sdk-core is required. "
                "Install it with: pip install aliyun-python-sdk-core aliyun-python-sdk-dataworks-public"
            )
    
    def get_table_lineage(
        self,
        table_name: str,
        project_name: str,
        direction: str = "UPSTREAM",
    ) -> Dict[str, Any]:
        """
        获取表的血缘关系
        
        参数:
            table_name: 表名
            project_name: MaxCompute 项目名
            direction: 查询方向 - UPSTREAM (上游), DOWNSTREAM (下游), BOTH
        
        返回:
            血缘关系数据
        """
        try:
            from aliyunsdkdataworks_public.request.v20200518.GetMetaTableLineageRequest import (
                GetMetaTableLineageRequest,
            )
            
            request = GetMetaTableLineageRequest()
            request.set_accept_format('json')
            
            # 设置参数
            request.set_DataSourceType("odps")
            request.set_ClusterId(project_name)
            request.set_TableName(table_name)
            request.set_Direction(direction)
            
            # 发起请求
            response = self._client.do_action_with_exception(request)
            result = json.loads(response)
            
            return {
                "success": True,
                "table_name": table_name,
                "project_name": project_name,
                "direction": direction,
                "data": result,
            }
            
        except Exception as e:
            return {
                "success": False,
                "table_name": table_name,
                "project_name": project_name,
                "error": str(e),
            }
    
    def get_table_detail(
        self,
        table_name: str,
        project_name: str,
    ) -> Dict[str, Any]:
        """
        获取表的详细信息
        
        参数:
            table_name: 表名
            project_name: MaxCompute 项目名
        
        返回:
            表详细信息
        """
        try:
            from aliyunsdkdataworks_public.request.v20200518.GetMetaTableRequest import (
                GetMetaTableRequest,
            )
            
            request = GetMetaTableRequest()
            request.set_accept_format('json')
            
            request.set_DataSourceType("odps")
            request.set_ClusterId(project_name)
            request.set_TableName(table_name)
            
            response = self._client.do_action_with_exception(request)
            result = json.loads(response)
            
            return {
                "success": True,
                "table_name": table_name,
                "project_name": project_name,
                "data": result,
            }
            
        except Exception as e:
            return {
                "success": False,
                "table_name": table_name,
                "project_name": project_name,
                "error": str(e),
            }
    
    def get_table_columns(
        self,
        table_name: str,
        project_name: str,
    ) -> Dict[str, Any]:
        """
        获取表的字段信息
        
        参数:
            table_name: 表名
            project_name: MaxCompute 项目名
        
        返回:
            字段信息列表
        """
        try:
            from aliyunsdkdataworks_public.request.v20200518.GetMetaTableColumnRequest import (
                GetMetaTableColumnRequest,
            )
            
            request = GetMetaTableColumnRequest()
            request.set_accept_format('json')
            
            request.set_DataSourceType("odps")
            request.set_ClusterId(project_name)
            request.set_TableName(table_name)
            
            response = self._client.do_action_with_exception(request)
            result = json.loads(response)
            
            return {
                "success": True,
                "table_name": table_name,
                "project_name": project_name,
                "data": result,
            }
            
        except Exception as e:
            return {
                "success": False,
                "table_name": table_name,
                "project_name": project_name,
                "error": str(e),
            }
    
    def parse_lineage_data(self, lineage_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析血缘关系数据，提取关键信息
        
        参数:
            lineage_result: get_table_lineage 的返回结果
        
        返回:
            解析后的血缘信息
        """
        if not lineage_result.get("success"):
            return {
                "success": False,
                "error": lineage_result.get("error", "Unknown error"),
            }
        
        data = lineage_result.get("data", {})
        
        # 提取上游表
        upstream_tables = []
        downstream_tables = []
        
        # 解析 Data 字段
        lineage_data = data.get("Data", {})
        
        # 上游血缘
        if "UpstreamList" in lineage_data:
            for item in lineage_data["UpstreamList"]:
                upstream_tables.append({
                    "table_name": item.get("TableName", ""),
                    "project": item.get("ClusterId", ""),
                    "type": item.get("TableType", ""),
                    "job_name": item.get("JobName", ""),
                    "job_id": item.get("JobId", ""),
                })
        
        # 下游血缘
        if "DownstreamList" in lineage_data:
            for item in lineage_data["DownstreamList"]:
                downstream_tables.append({
                    "table_name": item.get("TableName", ""),
                    "project": item.get("ClusterId", ""),
                    "type": item.get("TableType", ""),
                    "job_name": item.get("JobName", ""),
                    "job_id": item.get("JobId", ""),
                })
        
        return {
            "success": True,
            "upstream_count": len(upstream_tables),
            "downstream_count": len(downstream_tables),
            "upstream_tables": upstream_tables,
            "downstream_tables": downstream_tables,
        }
