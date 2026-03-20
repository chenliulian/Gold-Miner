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


class SessionStore:
    """管理单次对话的历史记录"""
    
    def __init__(self, sessions_dir: str = "./sessions"):
        self.sessions_dir = sessions_dir
        self.current_session: Optional[SessionState] = None
        self._ensure_dir()
    
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
            metadata={}
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
        
        self.current_session = SessionState(
            session_id=raw.get("session_id", session_id),
            start_time=raw.get("start_time", ""),
            end_time=raw.get("end_time"),
            title=raw.get("title", "未命名对话"),
            steps=raw.get("steps", []),
            metadata=raw.get("metadata", {})
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
    
    def list_sessions(self, limit: int = 20) -> List[Dict]:
        """列出所有历史会话"""
        sessions = []
        
        if not os.path.exists(self.sessions_dir):
            return sessions
        
        for filename in sorted(os.listdir(self.sessions_dir), reverse=True):
            if not filename.endswith(".json"):
                continue
            
            path = os.path.join(self.sessions_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                
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
