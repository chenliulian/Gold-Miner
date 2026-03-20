import json
import os
import tempfile

import pytest

from gold_miner.memory import MemoryState, MemoryStore


class TestMemoryState:
    def test_default_values(self):
        state = MemoryState()
        assert state.summary == ""
        assert state.table_schemas == {}
        assert state.metric_definitions == {}
        assert state.business_background == []
        assert state.saved_conversations == []


class TestMemoryStore:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "memory.json")
        self.summary_path = os.path.join(self.temp_dir, "memory.md")

    def teardown_method(self):
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_creates_memory_store(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        assert store.path == self.memory_path
        assert store.state.summary == ""
        assert store.state.table_schemas == {}

    def test_init_loads_existing_memory(self):
        existing_data = {
            "summary": "Previous summary",
            "table_schemas": {"users": ["id", "name"]},
            "metric_definitions": {"dau": "Daily active users"},
            "business_background": ["E-commerce platform"],
            "saved_conversations": [],
        }
        with open(self.memory_path, "w") as f:
            json.dump(existing_data, f)

        store = MemoryStore(self.memory_path, summary_path=self.summary_path)

        assert store.state.summary == "Previous summary"
        assert store.state.table_schemas == {"users": ["id", "name"]}
        assert store.state.metric_definitions == {"dau": "Daily active users"}
        assert store.state.business_background == ["E-commerce platform"]

    def test_should_remember_detects_keywords(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        
        # 应该触发记忆保存的关键词
        assert store.should_remember("请记住这个表结构") == True
        assert store.should_remember("保存这个指标定义") == True
        assert store.should_remember("记下来") == True
        assert store.should_remember("记住这个表") == True
        
        # 不应该触发的普通对话
        assert store.should_remember("查询今天的订单量") == False
        assert store.should_remember("帮我分析一下数据") == False

    def test_save_table_schema(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.save_table_schema("users", ["id", "name", "email"])

        assert store.state.table_schemas == {"users": ["id", "name", "email"]}
        
        # 验证文件已保存
        assert os.path.exists(self.memory_path)
        with open(self.memory_path) as f:
            data = json.load(f)
        assert data["table_schemas"] == {"users": ["id", "name", "email"]}

    def test_save_metric_definition(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.save_metric_definition("dau", "Daily active users")

        assert store.state.metric_definitions == {"dau": "Daily active users"}

    def test_save_business_background(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.save_business_background("E-commerce platform")
        store.save_business_background("Mobile app")

        assert store.state.business_background == ["E-commerce platform", "Mobile app"]
        
        # 重复添加不会重复
        store.save_business_background("E-commerce platform")
        assert len(store.state.business_background) == 2

    def test_save_conversation_point(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.save_conversation_point("重要结论：DAU增长了20%", context="数据分析")

        assert len(store.state.saved_conversations) == 1
        assert store.state.saved_conversations[0]["content"] == "重要结论：DAU增长了20%"
        assert store.state.saved_conversations[0]["context"] == "数据分析"

    def test_set_summary(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.set_summary("This is a test summary")

        assert store.state.summary == "This is a test summary"

    def test_get_context(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.set_summary("Test summary")
        store.save_table_schema("users", ["id", "name"])
        store.save_metric_definition("dau", "Daily active users")

        context = store.get_context()

        assert context["summary"] == "Test summary"
        assert context["table_schemas"] == {"users": ["id", "name"]}
        assert context["metric_definitions"] == {"dau": "Daily active users"}

    def test_clear(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.save_table_schema("users", ["id", "name"])
        store.set_summary("Test summary")
        
        store.clear()
        
        assert store.state.summary == ""
        assert store.state.table_schemas == {}
        assert store.state.metric_definitions == {}

    def test_remove_table(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.save_table_schema("users", ["id", "name"])
        store.save_table_schema("products", ["id", "title"])
        
        result = store.remove_table("users")
        
        assert result == True
        assert "users" not in store.state.table_schemas
        assert "products" in store.state.table_schemas
        
        # 删除不存在的表返回 False
        assert store.remove_table("nonexistent") == False

    def test_remove_metric(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.save_metric_definition("dau", "Daily active users")
        
        result = store.remove_metric("dau")
        
        assert result == True
        assert "dau" not in store.state.metric_definitions

    def test_save_creates_directory(self):
        nested_path = os.path.join(self.temp_dir, "nested", "memory.json")
        store = MemoryStore(nested_path, summary_path=self.summary_path)
        store.save_table_schema("users", ["id", "name"])

        assert os.path.exists(os.path.dirname(nested_path))

    def test_write_summary_doc(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.set_summary("Test summary")
        store.save_table_schema("users", ["id", "name"])
        store.save_metric_definition("dau", "Daily active users")
        store.save_business_background("E-commerce")

        assert os.path.exists(self.summary_path)

        with open(self.summary_path) as f:
            content = f.read()

        assert "# 长期记忆" in content or "# Memory" in content
        assert "Test summary" in content
        assert "users" in content
        assert "dau" in content
        assert "E-commerce" in content
