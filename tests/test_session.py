import json
import os
import tempfile
from datetime import datetime

import pytest

from gold_miner.session import SessionState, SessionStore


class TestSessionState:
    def test_default_values(self):
        state = SessionState()
        assert state.session_id == ""
        assert state.start_time == ""
        assert state.end_time is None
        assert state.title == ""
        assert state.steps == []
        assert state.metadata == {}


class TestSessionStore:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = SessionStore(self.temp_dir)

    def teardown_method(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_creates_session_store(self):
        assert self.store.sessions_dir == self.temp_dir
        assert self.store.current_session is None

    def test_start_session(self):
        session_id = self.store.start_session(title="测试对话")
        
        assert self.store.current_session is not None
        assert self.store.current_session.session_id == session_id
        assert self.store.current_session.title == "测试对话"
        assert self.store.current_session.start_time != ""
        
        # 验证文件已创建
        session_path = os.path.join(self.temp_dir, f"{session_id}.json")
        assert os.path.exists(session_path)

    def test_add_step(self):
        self.store.start_session(title="测试对话")
        self.store.add_step("user", "你好")
        self.store.add_step("assistant", "你好！有什么可以帮助你的？")
        
        assert len(self.store.current_session.steps) == 2
        assert self.store.current_session.steps[0]["role"] == "user"
        assert self.store.current_session.steps[0]["content"] == "你好"
        assert self.store.current_session.steps[1]["role"] == "assistant"
        assert "timestamp" in self.store.current_session.steps[0]

    def test_add_step_auto_start_session(self):
        # 如果没有活动会话，add_step 应该自动创建一个新会话
        self.store.add_step("user", "你好")
        
        assert self.store.current_session is not None
        assert len(self.store.current_session.steps) == 1

    def test_end_session(self):
        self.store.start_session(title="测试对话")
        self.store.add_step("user", "你好")
        
        self.store.end_session()
        
        assert self.store.current_session.end_time is not None
        assert self.store.current_session.end_time != ""

    def test_load_session(self):
        # 先创建一个会话
        session_id = self.store.start_session(title="测试对话")
        self.store.add_step("user", "问题1")
        self.store.add_step("assistant", "回答1")
        self.store.end_session()
        
        # 创建新的 store 实例来加载
        new_store = SessionStore(self.temp_dir)
        success = new_store.load_session(session_id)
        
        assert success == True
        assert new_store.current_session is not None
        assert new_store.current_session.session_id == session_id
        assert new_store.current_session.title == "测试对话"
        assert len(new_store.current_session.steps) == 2

    def test_load_session_not_found(self):
        success = self.store.load_session("nonexistent_session")
        assert success == False

    def test_get_context(self):
        self.store.start_session(title="测试对话")
        self.store.add_step("user", "问题1")
        self.store.add_step("assistant", "回答1")
        
        context = self.store.get_context()
        
        assert context["session_id"] == self.store.current_session.session_id
        assert context["title"] == "测试对话"
        assert len(context["steps"]) == 2
        assert context["step_count"] == 2

    def test_get_context_no_session(self):
        context = self.store.get_context()
        assert context["steps"] == []
        assert context["title"] == ""

    def test_get_context_max_steps(self):
        self.store.start_session(title="测试对话")
        for i in range(10):
            self.store.add_step("user", f"问题{i}")
            self.store.add_step("assistant", f"回答{i}")
        
        context = self.store.get_context(max_steps=5)
        
        # 应该只返回最近的5步
        assert len(context["steps"]) == 5

    def test_list_sessions(self):
        # 创建几个会话
        for i in range(3):
            session_id = self.store.start_session(title=f"对话{i}")
            self.store.add_step("user", f"问题{i}")
            self.store.end_session()
        
        sessions = self.store.list_sessions()
        
        assert len(sessions) == 3
        # 应该按时间倒序排列
        assert sessions[0]["title"] == "对话2"
        assert sessions[1]["title"] == "对话1"
        assert sessions[2]["title"] == "对话0"

    def test_list_sessions_limit(self):
        # 创建10个会话
        for i in range(10):
            session_id = self.store.start_session(title=f"对话{i}")
            self.store.add_step("user", f"问题{i}")
            self.store.end_session()
        
        sessions = self.store.list_sessions(limit=5)
        
        assert len(sessions) == 5

    def test_clear_current(self):
        self.store.start_session(title="测试对话")
        self.store.add_step("user", "你好")
        
        self.store.clear_current()
        
        assert self.store.current_session is None

    def test_get_current_session_id(self):
        assert self.store.get_current_session_id() is None
        
        session_id = self.store.start_session(title="测试对话")
        assert self.store.get_current_session_id() == session_id

    def test_session_file_format(self):
        session_id = self.store.start_session(title="测试对话")
        self.store.add_step("user", "你好", visible=True)
        self.store.end_session()
        
        session_path = os.path.join(self.temp_dir, f"{session_id}.json")
        with open(session_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 验证文件格式
        assert "session_id" in data
        assert "start_time" in data
        assert "end_time" in data
        assert "title" in data
        assert "steps" in data
        assert "metadata" in data
        
        # 验证步骤格式
        assert len(data["steps"]) == 1
        assert data["steps"][0]["role"] == "user"
        assert data["steps"][0]["content"] == "你好"
        assert data["steps"][0]["visible"] == True
        assert "timestamp" in data["steps"][0]

    def test_multiple_sessions_isolation(self):
        # 创建第一个会话
        session1_id = self.store.start_session(title="对话1")
        self.store.add_step("user", "问题1")
        self.store.end_session()
        
        # 创建第二个会话
        session2_id = self.store.start_session(title="对话2")
        self.store.add_step("user", "问题2")
        self.store.end_session()
        
        # 加载第一个会话
        self.store.load_session(session1_id)
        context1 = self.store.get_context()
        
        # 加载第二个会话
        self.store.load_session(session2_id)
        context2 = self.store.get_context()
        
        # 验证隔离性
        assert context1["title"] == "对话1"
        assert context1["steps"][0]["content"] == "问题1"
        assert context2["title"] == "对话2"
        assert context2["steps"][0]["content"] == "问题2"
