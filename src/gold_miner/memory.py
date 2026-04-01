"""Long-term memory management - only updated when user explicitly requests."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .file_utils import atomic_write_json, safe_read_json


@dataclass
class MemoryState:
    """长期记忆状态 - 只保存用户明确要求记住的内容"""
    summary: str = ""  # 整体摘要
    table_schemas: Dict[str, List[str]] = field(default_factory=dict)  # 表结构
    metric_definitions: Dict[str, str] = field(default_factory=dict)  # 指标定义
    business_background: List[str] = field(default_factory=list)  # 业务背景
    saved_conversations: List[Dict] = field(default_factory=list)  # 用户要求保存的对话要点


class MemoryStore:
    """
    长期记忆存储 - 只在用户明确要求"记住"时才更新

    使用方式：
    1. 用户说"记住这个表结构" -> 保存表结构
    2. 用户说"保存这个指标定义" -> 保存指标定义
    3. 用户说"记下来" -> 保存当前对话要点
    """

    # 触发记忆保存的关键词
    REMEMBER_KEYWORDS = [
        r"记住", r"保存", r"记下来", r"存储", r"记住这个",
        r"请记住", r"帮我记住", r"记住.+表", r"记住.+指标",
        r"保存.+定义", r"保存.+口径"
    ]

    def __init__(self, path: str, summary_path: str | None = None, user_id: str = ""):
        self._base_path = path
        self._base_summary_path = summary_path
        self.user_id = user_id
        self.state = MemoryState()
        self._load()

    @property
    def path(self) -> str:
        """动态获取记忆文件路径，如果设置了user_id则使用用户特定目录"""
        if self.user_id:
            from .user_data import get_user_data_manager
            user_data_manager = get_user_data_manager()
            return user_data_manager.get_user_memory_path(self.user_id)
        return self._base_path

    @property
    def summary_path(self) -> str:
        """动态获取记忆摘要文件路径，如果设置了user_id则使用用户特定目录"""
        if self.user_id:
            from .user_data import get_user_data_manager
            user_data_manager = get_user_data_manager()
            return user_data_manager.get_user_memory_summary_path(self.user_id)
        return self._base_summary_path or os.path.join(os.path.dirname(self.path), "memory.md")

    def _load(self) -> None:
        """从文件加载长期记忆"""
        raw = safe_read_json(self.path, default={})
        self.state.summary = raw.get("summary", "")
        self.state.table_schemas = raw.get("table_schemas", {})
        self.state.metric_definitions = raw.get("metric_definitions", {})
        self.state.business_background = raw.get("business_background", [])
        self.state.saved_conversations = raw.get("saved_conversations", [])

    def _save(self) -> None:
        """保存长期记忆到文件 (原子写入)"""
        data = {
            "summary": self.state.summary,
            "table_schemas": self.state.table_schemas,
            "metric_definitions": self.state.metric_definitions,
            "business_background": self.state.business_background,
            "saved_conversations": self.state.saved_conversations,
        }
        atomic_write_json(self.path, data)
        self._write_summary_doc()

    def _write_summary_doc(self) -> None:
        """生成可读的 Markdown 摘要文档"""
        lines = []
        lines.append("# 长期记忆 (Long-term Memory)\n")
        lines.append(f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        if self.state.summary:
            lines.append("## 整体摘要\n")
            lines.append(self.state.summary.strip() + "\n\n")
        
        if self.state.table_schemas:
            lines.append("## 已记住的表结构\n")
            for table, cols in self.state.table_schemas.items():
                lines.append(f"### {table}\n")
                for col in cols:
                    lines.append(f"- {col}\n")
                lines.append("\n")
        
        if self.state.metric_definitions:
            lines.append("## 已记住的指标定义\n")
            for metric, definition in self.state.metric_definitions.items():
                lines.append(f"- **{metric}**: {definition}\n")
            lines.append("\n")
        
        if self.state.business_background:
            lines.append("## 已记住的业务背景\n")
            for item in self.state.business_background:
                lines.append(f"- {item}\n")
            lines.append("\n")
        
        if self.state.saved_conversations:
            lines.append("## 已保存的对话要点\n")
            for conv in self.state.saved_conversations:
                time_str = conv.get("timestamp", "")[:10]  # 只取日期部分
                content = conv.get("content", "")
                lines.append(f"- **{time_str}**: {content}\n")
            lines.append("\n")
        
        os.makedirs(os.path.dirname(self.summary_path), exist_ok=True)
        with open(self.summary_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def should_remember(self, message: str) -> bool:
        """检查用户消息是否包含记住/保存的指令"""
        for pattern in self.REMEMBER_KEYWORDS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

    def save_table_schema(self, table_name: str, columns: List[str], source: str = "") -> None:
        """保存表结构到长期记忆"""
        if not columns:
            return
        self.state.table_schemas[table_name] = columns
        self._save()

    def save_metric_definition(self, metric_name: str, definition: str) -> None:
        """保存指标定义到长期记忆"""
        self.state.metric_definitions[metric_name] = definition
        self._save()

    def save_business_background(self, item: str) -> None:
        """保存业务背景到长期记忆"""
        if item not in self.state.business_background:
            self.state.business_background.append(item)
            self._save()

    def save_conversation_point(self, content: str, context: str = "") -> None:
        """保存对话要点到长期记忆"""
        self.state.saved_conversations.append({
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "context": context
        })
        # 只保留最近 50 条
        if len(self.state.saved_conversations) > 50:
            self.state.saved_conversations = self.state.saved_conversations[-50:]
        self._save()

    def set_summary(self, summary: str) -> None:
        """设置整体摘要"""
        self.state.summary = summary
        self._save()

    def get_context(self) -> Dict:
        """获取长期记忆内容（用于LLM上下文）"""
        return {
            "summary": self.state.summary,
            "table_schemas": self.state.table_schemas,
            "metric_definitions": self.state.metric_definitions,
            "business_background": self.state.business_background,
            "saved_conversations_count": len(self.state.saved_conversations),
        }

    def clear(self) -> None:
        """清空所有长期记忆（谨慎使用）"""
        self.state = MemoryState()
        self._save()

    def remove_table(self, table_name: str) -> bool:
        """从记忆中删除某个表"""
        if table_name in self.state.table_schemas:
            del self.state.table_schemas[table_name]
            self._save()
            return True
        return False

    def remove_metric(self, metric_name: str) -> bool:
        """从记忆中删除某个指标"""
        if metric_name in self.state.metric_definitions:
            del self.state.metric_definitions[metric_name]
            self._save()
            return True
        return False
