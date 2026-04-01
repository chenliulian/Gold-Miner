"""Session management for conversation history."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SessionState:
    """单次对话的完整状态"""
    session_id: str = ""
    start_time: str = ""
    end_time: Optional[str] = None
    title: str = ""  # 对话标题（可选，可由用户第一句话生成）
    steps: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)
    user_id: str = ""  # 所属用户ID，用于数据隔离
    final_result: Optional[str] = None  # 最终分析结果（用于会话切换后恢复）
    result_status: str = "pending"  # pending/running/completed/failed


class SessionStore:
    """管理单次对话的历史记录"""
    
    def __init__(self, sessions_dir: str = "./sessions", user_id: str = ""):
        self._base_sessions_dir = sessions_dir
        self.user_id = user_id  # 当前用户ID，用于数据隔离
        self.current_session: Optional[SessionState] = None
        self._ensure_dir()
    
    @property
    def sessions_dir(self) -> str:
        """动态获取会话目录，如果设置了user_id则使用用户特定目录"""
        if self.user_id:
            # 使用用户特定的会话目录
            from .user_data import get_user_data_manager
            user_data_manager = get_user_data_manager()
            paths = user_data_manager.get_user_paths(self.user_id)
            # 确保目录存在
            os.makedirs(paths.sessions_dir, exist_ok=True)
            return paths.sessions_dir
        return self._base_sessions_dir
    
    def _ensure_dir(self) -> None:
        """确保会话目录存在"""
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def _generate_session_id(self) -> str:
        """生成会话ID：session_YYYYMMDD_HHMMSS_microseconds"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def _get_session_path(self, session_id: str) -> str:
        """获取会话文件的完整路径"""
        return os.path.join(self.sessions_dir, f"{session_id}.json")
    
    def start_session(self, title: str = "") -> str:
        """开始一个新的对话会话"""
        session_id = self._generate_session_id()
        self.current_session = SessionState(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            title=title or "未命名对话",
            steps=[],
            metadata={},
            user_id=self.user_id  # 记录用户ID
        )
        self._save()
        return session_id
    
    def load_session(self, session_id: str) -> bool:
        """加载一个已有的会话"""
        path = self._get_session_path(session_id)
        if not os.path.exists(path):
            return False
        
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        
        # 验证用户权限：只能加载自己的会话
        session_user_id = raw.get("user_id", "")
        if session_user_id and session_user_id != self.user_id:
            return False  # 无权访问其他用户的会话
        
        self.current_session = SessionState(
            session_id=raw.get("session_id", session_id),
            start_time=raw.get("start_time", ""),
            end_time=raw.get("end_time"),
            title=raw.get("title", "未命名对话"),
            steps=raw.get("steps", []),
            metadata=raw.get("metadata", {}),
            user_id=session_user_id
        )
        return True
    
    def add_step(self, role: str, content: str, visible: bool = True) -> None:
        """添加一个对话步骤"""
        if self.current_session is None:
            self.start_session()
        
        self.current_session.steps.append({
            "role": role,
            "content": content,
            "visible": visible,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
    
    def end_session(self) -> None:
        """结束当前会话"""
        if self.current_session:
            self.current_session.end_time = datetime.now().isoformat()
            self._save()

    def update_title(self, title: str) -> None:
        """更新当前会话的标题"""
        if self.current_session:
            self.current_session.title = title
            self._save()

    def set_final_result(self, result: str, status: str = "completed") -> None:
        """保存最终分析结果到会话

        Args:
            result: 最终分析结果内容
            status: 结果状态 (completed/failed)
        """
        if self.current_session:
            self.current_session.final_result = result
            self.current_session.result_status = status
            self._save()

    def get_final_result(self) -> Optional[Dict]:
        """获取当前会话的最终结果

        Returns:
            {"result": str, "status": str} 或 None
        """
        if self.current_session is None:
            return None
        return {
            "result": self.current_session.final_result,
            "status": self.current_session.result_status
        }

    def set_result_status(self, status: str) -> None:
        """设置结果状态

        Args:
            status: pending/running/completed/failed
        """
        if self.current_session:
            self.current_session.result_status = status
            self._save()

    def _save(self) -> None:
        """保存当前会话到文件"""
        if self.current_session is None:
            return

        path = self._get_session_path(self.current_session.session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self.current_session.session_id,
                "start_time": self.current_session.start_time,
                "end_time": self.current_session.end_time,
                "title": self.current_session.title,
                "steps": self.current_session.steps,
                "metadata": self.current_session.metadata,
                "user_id": self.current_session.user_id,  # 保存用户ID
                "final_result": self.current_session.final_result,  # 最终结果
                "result_status": self.current_session.result_status,  # 结果状态
            }, f, ensure_ascii=False, indent=2)
    
    def get_context(self, max_steps: int = 50) -> Dict:
        """获取当前会话的上下文（用于LLM）"""
        if self.current_session is None:
            return {"steps": [], "title": "", "session_id": ""}
        
        steps = self.current_session.steps
        if len(steps) > max_steps:
            steps = steps[-max_steps:]
        
        return {
            "session_id": self.current_session.session_id,
            "title": self.current_session.title,
            "steps": steps,
            "step_count": len(self.current_session.steps)
        }
    
    def clear_current(self) -> None:
        """清空当前会话（结束但不删除文件）"""
        self.end_session()
        self.current_session = None
    
    def list_sessions(self, limit: int = 20, user_id: str = None) -> List[Dict]:
        """列出历史会话
        
        Args:
            limit: 最多返回的会话数量
            user_id: 可选，指定用户ID。如果不提供，使用当前实例的user_id
        
        Returns:
            会话列表，只返回指定用户的会话
        """
        sessions = []
        
        # 使用提供的user_id或实例的user_id
        target_user_id = user_id if user_id is not None else self.user_id
        
        if not os.path.exists(self.sessions_dir):
            return sessions
        
        for filename in sorted(os.listdir(self.sessions_dir), reverse=True):
            if not filename.endswith(".json"):
                continue
            
            path = os.path.join(self.sessions_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                
                # 只返回当前用户的会话
                # 兼容旧数据：如果 session_user_id 为空，也显示给当前用户
                session_user_id = raw.get("user_id", "")
                if target_user_id and session_user_id and session_user_id != target_user_id:
                    continue  # 跳过其他用户的会话（只跳过明确属于其他用户的）
                
                sessions.append({
                    "session_id": raw.get("session_id", filename[:-5]),
                    "title": raw.get("title", "未命名对话"),
                    "start_time": raw.get("start_time", ""),
                    "step_count": len(raw.get("steps", []))
                })
                
                if len(sessions) >= limit:
                    break
            except Exception:
                continue
        
        return sessions
    
    def get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID"""
        if self.current_session:
            return self.current_session.session_id
        return None

    def delete_session(self, session_id: str) -> bool:
        """删除指定会话"""
        try:
            # 先检查会话文件是否存在
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            if not os.path.exists(session_file):
                return False
            
            # 验证用户权限：只能删除自己的会话
            with open(session_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            session_user_id = raw.get("user_id", "")
            if session_user_id and session_user_id != self.user_id:
                return False  # 无权删除其他用户的会话

            # 如果删除的是当前会话，先清空当前会话
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None

            # 删除会话文件
            os.remove(session_file)
            return True
        except Exception as e:
            print(f"[SessionStore] 删除会话失败: {e}")
            return False
