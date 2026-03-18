from __future__ import annotations

import signal
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
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
    quota: str = ""  # ODPS 计算资源配额

    @classmethod
    def from_config(cls, config: "Config") -> "OdpsConfig":
        return cls(
            access_id=config.odps_access_id,
            access_key=config.odps_access_key,
            project=config.odps_project,
            endpoint=config.odps_endpoint,
            quota=config.odps_quota,
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
        
        # Base SQL settings
        sql_settings = {
            "odps.instance.priority": "7",
            "odps.sql.mapper.split.size": "256",
        }
        
        # Add quota if configured
        if config.quota:
            sql_settings["odps.sql.quota"] = config.quota
        
        options.sql.settings = sql_settings
        
        # Also set default hints for instance creation
        self._default_hints = {
            "odps.instance.priority": "7",
        }
        if config.quota:
            self._default_hints["odps.sql.quota"] = config.quota

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self._log_callback = callback

    def _log(self, message: str) -> None:
        if self._log_callback:
            self._log_callback(message)
        print(message)

    def run_sql(self, sql: str, limit: int = 2000, enable_log: bool = True, cancel_event=None) -> pd.DataFrame:
        if enable_log:
            self._log("正在提交...")
        
        # Use default hints including quota if configured
        hints = self._default_hints.copy()
        
        instance = self.odps.execute_sql(sql, hints=hints)
        
        if enable_log:
            self._log("提交任务成功")
            self._log("Awaiting for the task submitting...")
            
            while not instance.is_terminated():
                # Check for cancellation
                if cancel_event is not None and cancel_event.is_set():
                    self._log("Task cancelled by user")
                    instance.stop()
                    raise InterruptedError("Task cancelled by user")
                
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
        self, sql: str, limit: int = 2000, enable_log: bool = True, cancel_event=None
    ) -> Tuple[pd.DataFrame, str]:
        if enable_log:
            self._log("正在提交...")
        
        # Use default hints including quota if configured
        hints = self._default_hints.copy()
        
        # Use timeout for execute_sql to prevent hanging
        # Check for cancellation during submission
        def execute_with_timeout():
            return self.odps.execute_sql(sql, hints=hints)
        
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(execute_with_timeout)
                # Wait for submission with periodic cancellation checks
                instance = None
                for _ in range(60):  # 60 seconds max, checking every 1 second
                    if cancel_event is not None and cancel_event.is_set():
                        future.cancel()
                        raise InterruptedError("Task cancelled by user during submission")
                    try:
                        instance = future.result(timeout=1)
                        break
                    except TimeoutError:
                        continue
                if instance is None:
                    future.cancel()
                    raise TimeoutError("SQL submission timeout after 60 seconds")
        except TimeoutError:
            if enable_log:
                self._log("提交超时 (60秒)，请检查网络连接或ODPS服务状态")
            raise TimeoutError("SQL submission timeout after 60 seconds")
        
        instance_id = instance.id
        
        if enable_log:
            self._log(f"提交任务成功, Instance ID: {instance_id}")
            self._log("Awaiting for the task submitting...")
            
            while not instance.is_terminated():
                # Check for cancellation
                if cancel_event is not None and cancel_event.is_set():
                    self._log("Task cancelled by user")
                    instance.stop()
                    raise InterruptedError("Task cancelled by user")
                
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
        self, sql: str, limit: int = 2000, enable_log: bool = True, cancel_event=None
    ) -> Tuple[pd.DataFrame, str]:
        # Start with default hints including quota if configured
        hints = self._default_hints.copy()
        # Add script mode
        hints["odps.sql.submit.mode"] = "script"
        
        if enable_log:
            self._log("正在提交...")
            if self.config.quota:
                self._log(f"使用计算配额: {self.config.quota}")
        
        # Use timeout for execute_sql to prevent hanging
        def execute_with_timeout():
            return self.odps.execute_sql(sql, hints=hints)
        
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(execute_with_timeout)
                instance = future.result(timeout=60)  # 60 seconds timeout for submission
        except TimeoutError:
            if enable_log:
                self._log("提交超时 (60秒)，请检查网络连接或ODPS服务状态")
            raise TimeoutError("SQL submission timeout after 60 seconds")
        
        instance_id = instance.id
        
        if enable_log:
            self._log(f"提交任务成功, Instance ID: {instance_id}")
            self._log("Awaiting for the task submitting...")
            
            while not instance.is_terminated():
                # Check for cancellation
                if cancel_event is not None and cancel_event.is_set():
                    self._log("Task cancelled by user")
                    instance.stop()
                    raise InterruptedError("Task cancelled by user")
                
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

    def run_script(self, sql: str, limit: int = 2000, enable_log: bool = True, cancel_event=None) -> Tuple[pd.DataFrame, str]:
        # Start with default hints including quota if configured
        hints = self._default_hints.copy()
        # Add script mode
        hints["odps.sql.submit.mode"] = "script"
        
        if enable_log:
            self._log("正在提交...")
            if self.config.quota:
                self._log(f"使用计算配额: {self.config.quota}")
        
        # Use timeout for execute_sql to prevent hanging and support cancellation
        def execute_with_timeout():
            return self.odps.execute_sql(sql, hints=hints)
        
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(execute_with_timeout)
                # Wait for submission with periodic cancellation checks
                instance = None
                for _ in range(60):  # 60 seconds max, checking every 1 second
                    if cancel_event is not None and cancel_event.is_set():
                        future.cancel()
                        raise InterruptedError("Task cancelled by user during submission")
                    try:
                        instance = future.result(timeout=1)
                        break
                    except TimeoutError:
                        continue
                if instance is None:
                    future.cancel()
                    raise TimeoutError("SQL submission timeout after 60 seconds")
        except TimeoutError:
            if enable_log:
                self._log("提交超时 (60秒)，请检查网络连接或ODPS服务状态")
            raise TimeoutError("SQL submission timeout after 60 seconds")
        
        instance_id = instance.id
        
        if enable_log:
            self._log(f"提交任务成功, Instance ID: {instance_id}")
            self._log("Awaiting for the task submitting...")
            
            while not instance.is_terminated():
                # Check for cancellation
                if cancel_event is not None and cancel_event.is_set():
                    self._log("Task cancelled by user")
                    instance.stop()
                    raise InterruptedError("Task cancelled by user")
                
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
