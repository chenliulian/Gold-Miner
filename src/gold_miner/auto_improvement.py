"""
自动改进机制 - 错误检测和自动触发 self_improvement

在以下场景自动记录学习：
1. SQL 执行错误
2. Skill 执行错误
3. 重复出现的错误模式
4. 成功修复错误后的经验
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from datetime import datetime


@dataclass
class ErrorPattern:
    """错误模式定义"""
    pattern: str  # 正则表达式模式
    category: str  # 错误类别
    description: str  # 描述
    suggested_action: str  # 建议修复
    priority: str = "medium"


@dataclass
class ErrorRecord:
    """错误记录"""
    error_message: str
    error_type: str
    context: str
    timestamp: str
    sql: Optional[str] = None
    skill_name: Optional[str] = None
    resolved: bool = False
    resolution: Optional[str] = None


# 预定义的错误模式库
ERROR_PATTERNS = [
    ErrorPattern(
        pattern=r".*permission.*denied.*|.*无权限.*|.*Access.*Denied.*",
        category="permission_error",
        description="权限不足错误",
        suggested_action="检查 RAM 权限配置，确认 AccessKey 有相应权限",
        priority="high",
    ),
    ErrorPattern(
        pattern=r".*table.*not.*exist.*|.*表不存在.*|.*Table not found.*",
        category="table_not_found",
        description="表不存在错误",
        suggested_action="检查表名拼写，确认表是否存在于指定项目中",
        priority="high",
    ),
    ErrorPattern(
        pattern=r".*column.*not.*found.*|.*字段不存在.*|.*列不存在.*",
        category="column_not_found",
        description="字段不存在错误",
        suggested_action="检查字段名拼写，使用 DESC 命令确认表结构",
        priority="high",
    ),
    ErrorPattern(
        pattern=r".*syntax.*error.*|.*语法错误.*",
        category="syntax_error",
        description="SQL 语法错误",
        suggested_action="检查 SQL 语法，特别是关键字、括号匹配、逗号等",
        priority="medium",
    ),
    ErrorPattern(
        pattern=r".*timeout.*|.*超时.*",
        category="timeout_error",
        description="执行超时错误",
        suggested_action="优化 SQL 性能，添加分区过滤条件，减少数据扫描量",
        priority="medium",
    ),
    ErrorPattern(
        pattern=r".*memory.*exceed.*|.*内存不足.*|.*Quota exceeded.*",
        category="resource_error",
        description="资源限制错误",
        suggested_action="优化 SQL 减少内存使用，或申请更大的计算资源配额",
        priority="high",
    ),
    ErrorPattern(
        pattern=r".*partition.*|.*分区.*",
        category="partition_error",
        description="分区相关错误",
        suggested_action="检查分区字段和分区值格式，确认分区是否存在",
        priority="medium",
    ),
    ErrorPattern(
        pattern=r".*connection.*|.*连接.*",
        category="connection_error",
        description="连接错误",
        suggested_action="检查网络连接，确认 endpoint 配置正确",
        priority="high",
    ),
    ErrorPattern(
        pattern=r".*ModuleNotFoundError.*|.*ImportError.*",
        category="import_error",
        description="Python 导入错误",
        suggested_action="检查依赖包是否已安装，确认 Python 环境配置",
        priority="medium",
    ),
    ErrorPattern(
        pattern=r".*KeyError.*|.*IndexError.*|.*AttributeError.*",
        category="runtime_error",
        description="Python 运行时错误",
        suggested_action="检查代码逻辑，确认数据结构和变量类型",
        priority="medium",
    ),
]


class AutoImprovementManager:
    """自动改进管理器"""
    
    def __init__(self, max_recent_errors: int = 10):
        self.max_recent_errors = max_recent_errors
        self.recent_errors: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self.seen_errors: Set[str] = set()  # 用于去重
        
    def detect_error(
        self,
        error_message: str,
        context: str = "",
        sql: Optional[str] = None,
        skill_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        检测错误并返回 self_improvement 参数
        
        返回 None 表示不需要记录（重复错误或无需学习）
        """
        if not error_message:
            return None
            
        # 生成错误指纹用于去重
        error_fingerprint = self._generate_fingerprint(error_message)
        if error_fingerprint in self.seen_errors:
            return None
        
        # 匹配错误模式
        matched_pattern = self._match_pattern(error_message)
        
        # 创建错误记录
        record = ErrorRecord(
            error_message=error_message[:500],  # 限制长度
            error_type=matched_pattern.category if matched_pattern else "unknown",
            context=context,
            timestamp=datetime.now().isoformat(),
            sql=sql[:500] if sql else None,
            skill_name=skill_name,
        )
        
        self.recent_errors.append(record)
        self.seen_errors.add(error_fingerprint)
        
        # 限制历史记录数量
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # 统计错误次数
        self.error_counts[record.error_type] = self.error_counts.get(record.error_type, 0) + 1
        
        # 构建 self_improvement 参数
        return self._build_improvement_entry(record, matched_pattern)
    
    def detect_resolution(
        self,
        error_message: str,
        resolution: str,
        context: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        检测错误修复，记录解决方案
        """
        if not error_message or not resolution:
            return None
            
        matched_pattern = self._match_pattern(error_message)
        
        return {
            "entry_type": "learning",
            "category": "best_practice",
            "summary": f"修复了 {matched_pattern.description if matched_pattern else '错误'}: {error_message[:100]}",
            "details": f"错误信息: {error_message}\n\n解决方法: {resolution}\n\n上下文: {context}",
            "suggested_action": resolution,
            "area": "backend",
            "source": "error_resolution",
            "priority": "high",
        }
    
    def _match_pattern(self, error_message: str) -> Optional[ErrorPattern]:
        """匹配错误模式"""
        for pattern in ERROR_PATTERNS:
            if re.search(pattern.pattern, error_message, re.IGNORECASE):
                return pattern
        return None
    
    def _generate_fingerprint(self, error_message: str) -> str:
        """生成错误指纹（用于去重）"""
        # 提取关键信息，忽略具体值（如表名、时间戳等）
        # 简化：取前100个字符的小写形式
        simplified = error_message[:100].lower()
        # 移除数字和特定值
        simplified = re.sub(r'\d+', 'N', simplified)
        return simplified
    
    def _build_improvement_entry(
        self,
        record: ErrorRecord,
        pattern: Optional[ErrorPattern],
    ) -> Dict[str, Any]:
        """构建 self_improvement 条目"""
        
        category = "knowledge_gap" if pattern else "error"
        description = pattern.description if pattern else "未知错误"
        suggested_action = pattern.suggested_action if pattern else "需要进一步调查"
        priority = pattern.priority if pattern else "medium"
        
        # 如果是重复出现的错误类型，提高优先级
        if self.error_counts.get(record.error_type, 0) > 2:
            priority = "high"
            category = "correction"
        
        details = f"""错误类型: {record.error_type}
错误信息: {record.error_message}
上下文: {record.context}
时间: {record.timestamp}
"""
        if record.sql:
            details += f"\n相关 SQL:\n```sql\n{record.sql}\n```"
        if record.skill_name:
            details += f"\n相关 Skill: {record.skill_name}"
        
        return {
            "entry_type": "error" if category == "error" else "learning",
            "category": category,
            "summary": f"{description}: {record.error_message[:80]}...",
            "details": details,
            "suggested_action": suggested_action,
            "area": "odps" if record.sql else "backend",
            "source": "auto_detect",
            "priority": priority,
            "related_files": [record.skill_name] if record.skill_name else None,
        }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "total_errors": len(self.recent_errors),
            "error_counts": self.error_counts.copy(),
            "recent_error_types": [e.error_type for e in self.recent_errors[-5:]],
        }
    
    def should_trigger_learning_review(self) -> bool:
        """判断是否应该触发学习回顾"""
        # 当积累了一定数量的错误时，建议回顾
        return len(self.recent_errors) >= 5 or any(
            count >= 3 for count in self.error_counts.values()
        )


# 全局管理器实例
_auto_improvement_manager: Optional[AutoImprovementManager] = None


def get_auto_improvement_manager() -> AutoImprovementManager:
    """获取全局自动改进管理器"""
    global _auto_improvement_manager
    if _auto_improvement_manager is None:
        _auto_improvement_manager = AutoImprovementManager()
    return _auto_improvement_manager


def reset_auto_improvement_manager() -> None:
    """重置全局管理器（用于测试）"""
    global _auto_improvement_manager
    _auto_improvement_manager = None
