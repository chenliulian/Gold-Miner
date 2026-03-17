from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

import pandas as pd
from odps import ODPS, options
from odps.models import Instance


@dataclass
class OdpsConfig:
    access_id: str
    access_key: str
    project: str
    endpoint: str

    @classmethod
    def from_config(cls, config: "Config") -> "OdpsConfig":
        return cls(
            access_id=config.odps_access_id,
            access_key=config.odps_access_key,
            project=config.odps_project,
            endpoint=config.odps_endpoint,
        )


class OdpsClient:
    def __init__(self, config: OdpsConfig):
        self.config = config
        self.odps = ODPS(
            config.access_id,
            config.access_key,
            config.project,
            endpoint=config.endpoint,
        )
        self._log_callback: Optional[Callable[[str], None]] = None
        options.sql.settings = {
            "odps.instance.priority": "7",
            "odps.sql.mapper.split.size": "256",
        }

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self._log_callback = callback

    def _log(self, message: str) -> None:
        if self._log_callback:
            self._log_callback(message)
        print(message)

    def run_sql(self, sql: str, limit: int = 2000, enable_log: bool = True) -> pd.DataFrame:
        if enable_log:
            self._log("正在提交...")
        instance = self.odps.execute_sql(sql)
        
        if enable_log:
            self._log("提交任务成功")
            self._log("Awaiting for the task submitting...")
            
            while not instance.is_terminated():
                status = instance.status
                if status == "running":
                    self._log("Current task status: RUNNING")
                elif status == "waiting":
                    self._log("Awaiting in the cloud gateway for resources")
                time.sleep(3)
            
            self._log(f"Task finished with status: {instance.status}")
        
        with instance.open_reader() as reader:
            try:
                df = reader.to_pandas()
                if limit and len(df) > limit:
                    return df.head(limit)
                return df
            except Exception:
                return pd.DataFrame()

    def enable_verbose(self) -> None:
        options.verbose = True
        options.verbose_log = self._log

    def disable_verbose(self) -> None:
        options.verbose = False

    def set_sql_settings(self, settings: Dict[str, Any]) -> None:
        if options.sql.settings is None:
            options.sql.settings = {}
        options.sql.settings.update(settings)
        self._log(f"SQL settings updated: {settings}")

    def get_logview_url(self, instance: Instance) -> str:
        return instance.get_logview_address()

    def run_sql_with_progress(
        self, sql: str, limit: int = 2000, enable_log: bool = True
    ) -> Tuple[pd.DataFrame, str]:
        if enable_log:
            self._log("正在提交...")
        
        instance = self.odps.execute_sql(sql)
        instance_id = instance.id
        
        if enable_log:
            self._log(f"提交任务成功, Instance ID: {instance_id}")
            self._log("Awaiting for the task submitting...")
            
            while not instance.is_terminated():
                status = instance.status
                if status == "running":
                    self._log("Current task status: RUNNING")
                    for task_name in instance.get_task_names():
                        progress = instance.get_task_progress(task_name)
                        self._log(f"  Task: {task_name}, Progress: {progress}")
                elif status == "waiting":
                    self._log("Awaiting in the cloud gateway for resources")
                time.sleep(3)
            
            self._log(f"Task finished with status: {instance.status}")
            
            logview_url = self.get_logview_url(instance)
            self._log(f"Logview: {logview_url}")
        
        with instance.open_reader() as reader:
            try:
                df = reader.to_pandas()
                if limit and len(df) > limit:
                    return df.head(limit), instance_id
                return df, instance_id
            except Exception:
                return pd.DataFrame(), instance_id

    def run_script_with_progress(
        self, sql: str, limit: int = 2000, enable_log: bool = True
    ) -> Tuple[pd.DataFrame, str]:
        hints = {
            "odps.sql.submit.mode": "script",
            "odps.instance.priority": "7"
        }
        
        if enable_log:
            self._log("正在提交...")
        
        instance = self.odps.execute_sql(sql, hints=hints)
        instance_id = instance.id
        
        if enable_log:
            self._log(f"提交任务成功, Instance ID: {instance_id}")
            self._log("Awaiting for the task submitting...")
            
            while not instance.is_terminated():
                status = instance.status
                if status == "running":
                    self._log("Current task status: RUNNING")
                    for task_name in instance.get_task_names():
                        progress = instance.get_task_progress(task_name)
                        self._log(f"  Task: {task_name}, Progress: {progress}")
                elif status == "waiting":
                    self._log("Awaiting in the cloud gateway for resources")
                time.sleep(3)
            
            self._log(f"Task finished with status: {instance.status}")
            
            logview_url = self.get_logview_url(instance)
            self._log(f"Logview: {logview_url}")
        
        with instance.open_reader() as reader:
            try:
                df = reader.to_pandas()
                if limit and len(df) > limit:
                    return df.head(limit), instance_id
                return df, instance_id
            except Exception:
                return pd.DataFrame(), instance_id

    def run_script(self, sql: str, limit: int = 2000, enable_log: bool = True) -> Tuple[pd.DataFrame, str]:
        hints = {
            "odps.sql.submit.mode": "script",
            "odps.instance.priority": "7"
        }
        
        if enable_log:
            self._log("正在提交...")
        instance = self.odps.execute_sql(sql, hints=hints)
        instance_id = instance.id
        
        if enable_log:
            self._log(f"提交任务成功, Instance ID: {instance_id}")
            self._log("Awaiting for the task submitting...")
            
            while not instance.is_terminated():
                status = instance.status
                if status == "running":
                    self._log("Current task status: RUNNING")
                elif status == "waiting":
                    self._log("Awaiting in the cloud gateway for resources")
                time.sleep(3)
            
            self._log(f"Task finished with status: {instance.status}")
            
            logview_url = self.get_logview_url(instance)
            self._log(f"Logview: {logview_url}")
        
        with instance.open_reader() as reader:
            try:
                df = reader.to_pandas()
                if limit and len(df) > limit:
                    return df.head(limit), instance_id
                return df, instance_id
            except Exception:
                return pd.DataFrame(), instance_id
