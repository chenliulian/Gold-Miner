import json
import os
import tempfile

import pytest

from gold_miner.memory import MemoryState, MemoryStore


class TestMemoryState:
    def test_default_values(self):
        state = MemoryState()
        assert state.summary == ""
        assert state.recent_steps == []
        assert state.table_schemas == {}
        assert state.metric_definitions == {}
        assert state.business_background == []


class TestMemoryStore:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "memory.json")
        self.summary_path = os.path.join(self.temp_dir, "summary.md")

    def teardown_method(self):
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_creates_memory_store(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        assert store.path == self.memory_path
        assert store.max_recent == 8
        assert store.state.summary == ""
        assert store.state.recent_steps == []

    def test_init_loads_existing_memory(self):
        existing_data = {
            "summary": "Previous summary",
            "recent_steps": [{"role": "user", "content": "Hello"}],
            "table_schemas": {"users": ["id", "name"]},
            "metric_definitions": {"dau": "Daily active users"},
            "business_background": ["E-commerce platform"],
        }
        with open(self.memory_path, "w") as f:
            json.dump(existing_data, f)

        store = MemoryStore(self.memory_path, summary_path=self.summary_path)

        assert store.state.summary == "Previous summary"
        assert len(store.state.recent_steps) == 1
        assert store.state.table_schemas == {"users": ["id", "name"]}
        assert store.state.metric_definitions == {"dau": "Daily active users"}
        assert store.state.business_background == ["E-commerce platform"]

    def test_init_creates_default_max_recent(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        assert store.max_recent == 8

    def test_init_with_custom_max_recent(self):
        store = MemoryStore(
            self.memory_path, max_recent=5, summary_path=self.summary_path
        )
        assert store.max_recent == 5

    def test_add_step(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.add_step("user", "What is the DAU?")

        assert len(store.state.recent_steps) == 1
        assert store.state.recent_steps[0]["role"] == "user"
        assert store.state.recent_steps[0]["content"] == "What is the DAU?"

    def test_add_step_trims_recent_steps(self):
        store = MemoryStore(self.memory_path, max_recent=3, summary_path=self.summary_path)

        for i in range(5):
            store.add_step("user", f"Message {i}")

        assert len(store.state.recent_steps) == 3
        assert store.state.recent_steps[0]["content"] == "Message 2"
        assert store.state.recent_steps[1]["content"] == "Message 3"
        assert store.state.recent_steps[2]["content"] == "Message 4"

    def test_set_summary(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.set_summary("This is a test summary")

        assert store.state.summary == "This is a test summary"

    def test_update_structured_with_table_schemas(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.update_structured(
            table_schemas={"users": ["id", "name", "email"]}
        )

        assert store.state.table_schemas == {"users": ["id", "name", "email"]}

    def test_update_structured_with_metric_definitions(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.update_structured(
            metric_definitions={"dau": "Daily active users"}
        )

        assert store.state.metric_definitions == {"dau": "Daily active users"}

    def test_update_structured_with_business_background(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.update_structured(
            business_background=["Mobile app", "Global users"]
        )

        assert store.state.business_background == ["Mobile app", "Global users"]

    def test_update_structured_merges_existing_data(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.update_structured(
            table_schemas={"users": ["id", "name"]}
        )
        store.update_structured(
            table_schemas={"products": ["id", "title"]}
        )

        assert store.state.table_schemas == {
            "users": ["id", "name"],
            "products": ["id", "title"],
        }

    def test_get_context(self):
        with open(self.memory_path, "w") as f:
            json.dump(
                {
                    "summary": "Test summary",
                    "recent_steps": [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi"},
                    ],
                },
                f,
            )

        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        context = store.get_context()

        assert context["summary"] == "Test summary"
        assert len(context["recent_steps"]) == 2

    def test_save_creates_directory(self):
        nested_path = os.path.join(self.temp_dir, "nested", "memory.json")
        store = MemoryStore(nested_path, summary_path=self.summary_path)
        store.add_step("user", "test")

        assert os.path.exists(os.path.dirname(nested_path))

    def test_write_summary_doc(self):
        store = MemoryStore(self.memory_path, summary_path=self.summary_path)
        store.set_summary("Test summary")
        store.update_structured(
            table_schemas={"users": ["id", "name"]},
            metric_definitions={"dau": "Daily active users"},
            business_background=["E-commerce"],
        )

        assert os.path.exists(self.summary_path)

        with open(self.summary_path) as f:
            content = f.read()

        assert "# Memory Summary" in content
        assert "Test summary" in content
        assert "`users`: id, name" in content
        assert "`dau`: Daily active users" in content
        assert "E-commerce" in content
