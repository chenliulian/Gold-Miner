import os
import re
import tempfile
import shutil
import time

import pytest

from gold_miner.harness import (
    ContextManager, ContextConfig, Message, MessageRole,
    ToolRegistry, Tool, ToolCall, ToolResult,
    SessionState, ExecutionRecord, CheckpointManager, Checkpoint,
    RetryPolicy, RetryManager, RetryStrategy,
    CircuitBreaker, CircuitState,
    WorkingMemory, MemoryItem,
    Workspace, Artifact,
    HarnessAgent, HarnessConfig,
)
from gold_miner.harness.context.compressor import ContextCompressor
from gold_miner.harness.context.priority import MessagePriority, PriorityType
from gold_miner.harness.filesystem.artifacts import ArtifactManager


class TestContextManager:
    def setup_method(self):
        self.config = ContextConfig(max_tokens=1000, compress_threshold=0.8)
        self.ctx = ContextManager(self.config)

    def test_add_message(self):
        self.ctx.add_message(MessageRole.USER, "Hello")
        assert len(self.ctx._messages) == 1
        assert self.ctx._messages[0].content == "Hello"

    def test_count_tokens(self):
        self.ctx.add_message(MessageRole.USER, "Hello world")
        tokens = self.ctx.count_total_tokens()
        assert tokens > 0

    def test_get_messages(self):
        self.ctx.add_message(MessageRole.USER, "Hello")
        self.ctx.add_message(MessageRole.ASSISTANT, "Hi there")
        messages = self.ctx.get_messages()
        assert len(messages) == 2

    def test_clear(self):
        self.ctx.add_message(MessageRole.USER, "Hello")
        self.ctx.clear()
        assert len(self.ctx._messages) == 0


class TestToolRegistry:
    def setup_method(self):
        self.registry = ToolRegistry()

    def test_register_tool(self):
        tool = Tool(name="test", description="A test tool", required_params=["arg1"])
        self.registry.register_tool(tool)
        assert "test" in self.registry.list_tools()

    def test_get_tool(self):
        tool = Tool(name="my_tool", description="My tool", required_params=[])
        self.registry.register_tool(tool)
        retrieved = self.registry.get_tool("my_tool")
        assert retrieved is not None
        assert retrieved.name == "my_tool"

    def test_validate_action_valid(self):
        tool = Tool(name="run_sql", description="Run SQL", required_params=["sql"])
        self.registry.register_tool(tool)
        is_valid, error = self.registry.validate_action("run_sql", {"sql": "SELECT 1"})
        assert is_valid is True

    def test_validate_action_missing_params(self):
        tool = Tool(name="run_sql", description="Run SQL", required_params=["sql"])
        self.registry.register_tool(tool)
        is_valid, error = self.registry.validate_action("run_sql", {})
        assert is_valid is False
        assert "Missing" in error

    def test_validate_action_unknown_action(self):
        is_valid, error = self.registry.validate_action("unknown_action", {})
        assert is_valid is False
        assert "Unknown action" in error

    def test_parse_action_dict(self):
        action_dict = {"action": "run_sql", "sql": "SELECT * FROM users"}
        tool_call = self.registry.parse_action_dict(action_dict)
        assert tool_call.action == "run_sql"
        assert tool_call.args["sql"] == "SELECT * FROM users"

    def test_get_tools_description(self):
        desc = self.registry.get_tools_description()
        assert "run_sql" in desc


class TestSessionState:
    def setup_method(self):
        self.state = SessionState(session_id="test-session", question="Test question")

    def test_initial_state(self):
        assert self.state.session_id == "test-session"
        assert self.state.current_step == 0
        assert self.state.is_completed is False
        assert self.state.is_cancelled is False

    def test_tick(self):
        self.state.tick()
        assert self.state.current_step == 1

    def test_add_step(self):
        self.state.add_step("assistant", "Hello")
        assert len(self.state.steps) == 1
        assert self.state.steps[0].content == "Hello"

    def test_add_result(self):
        self.state.add_result("result1")
        assert "result1" in self.state.results

    def test_add_note(self):
        self.state.add_note("test note")
        assert "test note" in self.state.notes

    def test_add_sql(self):
        record = ExecutionRecord(sql="SELECT 1", rows=1, success=True)
        self.state.add_sql(record)
        assert len(self.state.executed_sqls) == 1
        assert self.state.executed_sqls[0].sql == "SELECT 1"

    def test_cancel(self):
        self.state.cancel("User requested")
        assert self.state.is_cancelled is True
        assert self.state.cancel_reason == "User requested"

    def test_complete(self):
        self.state.complete()
        assert self.state.is_completed is True

    def test_to_dict_and_from_dict(self):
        self.state.add_step("user", "Hello")
        self.state.add_result("result1")
        data = self.state.to_dict()
        restored = SessionState.from_dict(data)
        assert restored.session_id == self.state.session_id
        assert restored.current_step == self.state.current_step
        assert len(restored.steps) == 1


class TestCheckpointManager:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CheckpointManager(self.temp_dir)

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_checkpoint(self):
        state = SessionState(session_id="test", question="Test")
        checkpoint = self.manager.create_checkpoint("test", 1, state, "Step 1")
        assert checkpoint.session_id == "test"
        assert checkpoint.step == 1

    def test_get_latest_checkpoint(self):
        state = SessionState(session_id="test", question="Test")
        self.manager.create_checkpoint("test", 1, state)
        latest = self.manager.get_latest_checkpoint("test")
        assert latest is not None
        assert latest.step == 1

    def test_get_checkpoint_at_step(self):
        state = SessionState(session_id="test", question="Test")
        self.manager.create_checkpoint("test", 2, state)
        cp = self.manager.get_checkpoint_at_step("test", 2)
        assert cp is not None
        assert cp.step == 2

    def test_restore_session_state(self):
        state = SessionState(session_id="test", question="Test")
        state.add_step("user", "Hello")
        checkpoint = self.manager.create_checkpoint("test", 1, state)
        restored = self.manager.restore_session_state(checkpoint)
        assert restored.session_id == "test"
        assert len(restored.steps) == 1


class TestRetryPolicy:
    def test_exponential_delay(self):
        policy = RetryPolicy(
            max_attempts=5,
            initial_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL
        )
        assert policy.calculate_delay(1) == 1.0
        assert policy.calculate_delay(2) == 2.0
        assert policy.calculate_delay(3) == 4.0

    def test_linear_delay(self):
        policy = RetryPolicy(
            max_attempts=5,
            initial_delay=1.0,
            strategy=RetryStrategy.LINEAR
        )
        assert policy.calculate_delay(1) == 1.0
        assert policy.calculate_delay(2) == 2.0
        assert policy.calculate_delay(3) == 3.0

    def test_fixed_delay(self):
        policy = RetryPolicy(
            max_attempts=5,
            initial_delay=2.0,
            strategy=RetryStrategy.FIXED
        )
        assert policy.calculate_delay(1) == 2.0
        assert policy.calculate_delay(2) == 2.0
        assert policy.calculate_delay(3) == 2.0

    def test_max_delay(self):
        policy = RetryPolicy(initial_delay=10.0, max_delay=15.0)
        assert policy.calculate_delay(10) == 15.0

    def test_is_retryable(self):
        policy = RetryPolicy()
        assert policy.is_retryable(Exception("timeout error")) is True
        assert policy.is_retryable(Exception("connection refused")) is True
        assert policy.is_retryable(Exception("invalid sql")) is False


class TestRetryManager:
    def test_successful_execution(self):
        policy = RetryPolicy(max_attempts=3)
        manager = RetryManager(policy)
        result, success, error = manager.execute_with_retry(lambda: 42)
        assert success is True
        assert result == 42
        assert error is None

    def test_failed_execution_no_retry(self):
        policy = RetryPolicy(max_attempts=3, retryable_errors=())
        manager = RetryManager(policy)
        result, success, error = manager.execute_with_retry(lambda: (_ for _ in ()).throw(Exception("fail")))
        assert success is False
        assert result is None
        assert error is not None


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed() is True

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
            except Exception:
                pass
        assert cb.is_open() is True

    def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass
        assert cb.is_open() is True
        import time
        time.sleep(0.2)
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.is_half_open() or cb.is_closed()

    def test_successful_call(self):
        cb = CircuitBreaker()
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.is_closed()


class TestWorkingMemory:
    def setup_method(self):
        self.memory = WorkingMemory(max_items=3)

    def test_set_and_get(self):
        self.memory.set("key1", "value1")
        assert self.memory.get("key1") == "value1"

    def test_get_default(self):
        assert self.memory.get("nonexistent", "default") == "default"

    def test_has(self):
        self.memory.set("key1", "value1")
        assert self.memory.has("key1") is True
        assert self.memory.has("nonexistent") is False

    def test_delete(self):
        self.memory.set("key1", "value1")
        assert self.memory.delete("key1") is True
        assert self.memory.has("key1") is False

    def test_lru_eviction(self):
        self.memory.set("key1", "value1")
        self.memory.set("key2", "value2")
        self.memory.set("key3", "value3")
        self.memory.set("key4", "value4")
        assert self.memory.has("key1") is False
        assert self.memory.has("key4") is True

    def test_get_recent(self):
        self.memory.set("key1", "value1")
        self.memory.set("key2", "value2")
        self.memory.get("key1")
        recent = self.memory.get_recent(2)
        assert recent[0][0] == "key1"

    def test_clear(self):
        self.memory.set("key1", "value1")
        self.memory.clear()
        assert len(self.memory.keys()) == 0

    def test_to_dict_and_from_dict(self):
        self.memory.set("key1", "value1", {"meta": "data"})
        data = self.memory.to_dict()
        restored = WorkingMemory.from_dict(data)
        assert restored.get("key1") == "value1"


class TestWorkspace:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Workspace(self.temp_dir)

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_store_and_retrieve(self):
        artifact = self.workspace.store("test_key", "test_content", "text")
        assert artifact is not None
        assert self.workspace.retrieve("test_key") == "test_content"

    def test_exists(self):
        self.workspace.store("test_key", "content")
        assert self.workspace.exists("test_key") is True
        assert self.workspace.exists("nonexistent") is False

    def test_delete(self):
        self.workspace.store("test_key", "content")
        assert self.workspace.delete("test_key") is True
        assert self.workspace.exists("test_key") is False

    def test_list_artifacts(self):
        self.workspace.store("key1", "content1", "text")
        self.workspace.store("key2", "content2", "data")
        all_artifacts = self.workspace.list_artifacts()
        assert len(all_artifacts) == 2
        text_artifacts = self.workspace.list_artifacts("text")
        assert len(text_artifacts) == 1

    def test_summary(self):
        self.workspace.store("key1", "content", "text")
        summary = self.workspace.summary()
        assert "Total artifacts: 1" in summary


class TestArtifactManager:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ArtifactManager(workspace=Workspace(self.temp_dir))

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_store_and_get_sql(self):
        self.manager.store_sql("query1", "SELECT * FROM users")
        sql = self.manager.get_sql("query1")
        assert sql == "SELECT * FROM users"

    def test_store_and_get_report(self):
        self.manager.store_report("report1", "# Title\nReport content")
        report = self.manager.get_report("report1")
        assert "# Title" in report

    def test_search(self):
        self.manager.store_sql("query_users", "SELECT * FROM users")
        self.manager.store_sql("query_orders", "SELECT * FROM orders")
        results = self.manager.search("users")
        assert len(results) == 1
        assert results[0].key == "query_users"


class TestHarnessAgent:
    def test_harness_config_defaults(self):
        config = HarnessConfig()
        assert config.enable_context_manager is True
        assert config.enable_checkpoint is True
        assert config.enable_retry is True
        assert config.enable_circuit_breaker is True

    def test_harness_agent_initialization(self):
        class MockAgent:
            def run(self, question, **kwargs):
                return f"Answer to: {question}"

        config = HarnessConfig(
            enable_context_manager=False,
            enable_checkpoint=False,
            enable_retry=False,
            enable_circuit_breaker=False,
            enable_workspace=False,
            enable_learning=False
        )
        agent = HarnessAgent(MockAgent(), config)
        assert agent.context_manager is None
        assert agent.checkpoint_manager is None


class TestContextCompressor:
    def test_drop_old_strategy(self):
        ctx = ContextManager()
        for i in range(5):
            ctx.add_message(MessageRole.USER, f"Message {i}")
        compressor = ContextCompressor()
        compressed = compressor.compress_messages(ctx._messages, max_count=3, strategy="drop_old")
        assert len(compressed) == 3

    def test_drop_small_strategy(self):
        ctx = ContextManager()
        for i in range(5):
            ctx.add_message(MessageRole.USER, f"Message {i}")
        compressor = ContextCompressor()
        compressed = compressor.compress_messages(ctx._messages, max_count=3, strategy="drop_small")
        assert len(compressed) <= 5


class TestMessagePriority:
    def test_priority_calculation(self):
        msg = Message(role=MessageRole.USER, content="Test", metadata={})
        priority = MessagePriority.calculate(msg)
        assert priority in [PriorityType.HIGH, PriorityType.NORMAL, PriorityType.LOW, PriorityType.CRITICAL]

    def test_system_message_high_priority(self):
        msg = Message(role=MessageRole.SYSTEM, content="System prompt")
        priority = MessagePriority.calculate(msg)
        assert priority == PriorityType.CRITICAL


class TestCheckpoint:
    def test_checkpoint_save_and_load(self):
        temp_dir = tempfile.mkdtemp()
        try:
            checkpoint = Checkpoint(
                id="test_cp",
                session_id="session1",
                step=1,
                state={"test": "data"},
                description="Test checkpoint"
            )
            path = checkpoint.save(temp_dir)
            assert os.path.exists(path)

            loaded = Checkpoint.load(path)
            assert loaded.id == "test_cp"
            assert loaded.session_id == "session1"
            assert loaded.step == 1
        finally:
            shutil.rmtree(temp_dir)


class TestHarnessAgentGetAttr:
    def test_proxy_attribute_to_base_agent(self):
        class MockAgent:
            def __init__(self):
                self.custom_attr = "custom_value"
                self.session = "mock_session"

            def run(self, question, **kwargs):
                return f"Answer: {question}"

        agent = HarnessAgent(MockAgent())
        assert agent.custom_attr == "custom_value"
        assert agent.session == "mock_session"

    def test_proxy_method_to_base_agent(self):
        class MockAgent:
            def custom_method(self, x):
                return x * 2

            def run(self, question, **kwargs):
                return "done"

        agent = HarnessAgent(MockAgent())
        assert agent.custom_method(5) == 10

    def test_internal_attributes_not_proxied(self):
        class MockAgent:
            def run(self, question, **kwargs):
                return "done"

        agent = HarnessAgent(MockAgent())
        assert hasattr(agent, 'context_manager')
        assert hasattr(agent, 'checkpoint_manager')
        assert hasattr(agent, 'retry_manager')

    def test_private_attributes_raise_error(self):
        class MockAgent:
            def run(self, question, **kwargs):
                return "done"

        agent = HarnessAgent(MockAgent())
        try:
            _ = agent.__private
            assert False, "Should raise AttributeError"
        except AttributeError:
            pass

    def test_non_existent_attribute_raises_error(self):
        class MockAgent:
            def run(self, question, **kwargs):
                return "done"

        agent = HarnessAgent(MockAgent())
        try:
            _ = agent.nonexistent_attribute
            assert False, "Should raise AttributeError"
        except AttributeError:
            pass


class TestHarnessAgentRun:
    def test_run_passes_context_messages(self):
        call_record = []

        class MockAgent:
            def run(self, question, **kwargs):
                call_record.append(kwargs.get('context_messages'))
                return f"Answer: {question}"

        config = HarnessConfig(
            enable_context_manager=True,
            enable_checkpoint=False,
            enable_retry=False,
            enable_circuit_breaker=False,
            enable_workspace=False,
            enable_learning=False
        )
        agent = HarnessAgent(MockAgent(), config)
        agent.run("test question")

        assert len(call_record) == 1
        assert call_record[0] is not None
        assert len(call_record[0]) > 0

    def test_run_without_context_manager(self):
        call_record = []

        class MockAgent:
            def run(self, question, **kwargs):
                call_record.append(kwargs)
                return f"Answer: {question}"

        config = HarnessConfig(
            enable_context_manager=False,
            enable_checkpoint=False,
            enable_retry=False,
            enable_circuit_breaker=False,
            enable_workspace=False,
            enable_learning=False
        )
        agent = HarnessAgent(MockAgent(), config)
        result = agent.run("test question")

        assert result == "Answer: test question"
        assert 'context_messages' not in call_record[0]

    def test_run_with_checkpoint(self):
        temp_dir = tempfile.mkdtemp()
        try:
            class MockAgent:
                def run(self, question, **kwargs):
                    return f"Answer: {question}"

            config = HarnessConfig(
                enable_context_manager=False,
                enable_checkpoint=True,
                enable_retry=False,
                enable_circuit_breaker=False,
                enable_workspace=False,
                enable_learning=False,
                checkpoint_dir=temp_dir
            )
            agent = HarnessAgent(MockAgent(), config)
            result = agent.run("test question", session_id="test-session")

            assert result == "Answer: test question"
            checkpoints = agent.checkpoint_manager.list_checkpoints("test-session")
            assert len(checkpoints) == 2
        finally:
            shutil.rmtree(temp_dir)


class TestSessionStateSerialization:
    def test_to_dict_and_from_dict_roundtrip(self):
        state = SessionState(
            session_id="test-session",
            question="Test question",
            max_steps=10
        )
        state.add_step("user", "Hello")
        state.add_step("assistant", "Hi there")
        state.add_note("Test note")
        state.add_sql(ExecutionRecord(sql="SELECT 1", rows=1, success=True))
        state.complete()

        serialized = state.to_dict()
        restored = SessionState.from_dict(serialized)

        assert restored.session_id == state.session_id
        assert restored.question == state.question
        assert restored.max_steps == state.max_steps
        assert restored.current_step == state.current_step
        assert len(restored.steps) == 2
        assert len(restored.notes) == 1
        assert len(restored.executed_sqls) == 1
        assert restored.is_completed == state.is_completed

    def test_from_dict_with_minimal_data(self):
        data = {
            "session_id": "minimal-session"
        }
        state = SessionState.from_dict(data)
        assert state.session_id == "minimal-session"
        assert state.question == ""
        assert state.max_steps == 6
        assert state.current_step == 0

    def test_cancelled_state_serialization(self):
        state = SessionState(session_id="cancel-test", question="Test")
        state.cancel("User cancelled")
        state.is_cancelled = True

        serialized = state.to_dict()
        restored = SessionState.from_dict(serialized)

        assert restored.is_cancelled == True
        assert restored.cancel_reason == "User cancelled"


class TestCircuitBreakerStateTransitions:
    def test_closed_to_open_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        for i in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
            except Exception:
                pass

        assert cb._state == CircuitState.OPEN

    def test_open_to_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        for i in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
            except Exception:
                pass

        assert cb._state == CircuitState.OPEN

        import time
        time.sleep(0.15)

        cb.call(lambda: "success")
        assert cb._state == CircuitState.HALF_OPEN

    def test_half_open_to_closed_after_success_threshold(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1, success_threshold=2)

        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass

        import time
        time.sleep(0.15)

        cb.call(lambda: "ok1")
        cb.call(lambda: "ok2")

        assert cb._state == CircuitState.CLOSED

    def test_open_raises_circuit_open_error(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)

        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass

        try:
            cb.call(lambda: "should not reach")
            assert False, "Should raise CircuitOpenError"
        except Exception as e:
            assert "OPEN" in str(e)


class TestRetryManagerEdgeCases:
    def test_non_retryable_error_not_retried(self):
        policy = RetryPolicy(max_attempts=3)
        manager = RetryManager(policy)

        def fail_once():
            if not hasattr(fail_once, 'called'):
                fail_once.called = True
                raise Exception("some unrelated error")
            return "success"

        result, success, error = manager.execute_with_retry(fail_once)
        assert success is False
        assert result is None

    def test_retryable_error_is_retried(self):
        policy = RetryPolicy(max_attempts=3)
        manager = RetryManager(policy)

        attempt_count = 0

        def fail_with_timeout():
            nonlocal attempt_count
            attempt_count += 1
            raise Exception("timeout error")

        result, success, error = manager.execute_with_retry(fail_with_timeout)

        assert success is False
        assert result is None
        assert error is not None
        assert "timeout error" in str(error)
        assert attempt_count == 3

    def test_exponential_backoff(self):
        policy = RetryPolicy(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL,
            initial_delay=0.1
        )
        manager = RetryManager(policy)

        delays = []
        original_sleep = time.sleep

        def mock_sleep(d):
            delays.append(d)

        time.sleep = mock_sleep
        try:
            def always_fail():
                raise Exception("timeout error")

            manager.execute_with_retry(always_fail)

            assert len(delays) == 2
            assert delays[1] > delays[0]
        finally:
            time.sleep = original_sleep

    def test_max_attempts_respected(self):
        policy = RetryPolicy(max_attempts=5)
        manager = RetryManager(policy)

        attempt_count = 0

        def always_fail():
            nonlocal attempt_count
            attempt_count += 1
            raise Exception("timeout error")

        manager.execute_with_retry(always_fail)

        assert attempt_count == 5


class TestRememberKeywords:
    def test_chinese_keywords(self):
        from gold_miner.harness.memory.long_term_memory import MemoryStore

        store = MemoryStore.__new__(MemoryStore)
        store.state = None

        test_phrases = [
            "记住这个表结构",
            "请记住我的偏好",
            "保存这个指标定义",
            "帮我记住这个业务规则"
        ]

        for phrase in test_phrases:
            matched = any(
                re.search(pattern, phrase)
                for pattern in store.REMEMBER_KEYWORDS
            )
            assert matched, f"Should match: {phrase}"

    def test_english_keywords(self):
        from gold_miner.harness.memory.long_term_memory import MemoryStore

        store = MemoryStore.__new__(MemoryStore)
        store.state = None

        test_phrases = [
            "remember this table structure",
            "please remember my preference",
            "save this metric definition",
            "keep in mind this business rule"
        ]

        for phrase in test_phrases:
            matched = any(
                re.search(pattern, phrase)
                for pattern in store.REMEMBER_KEYWORDS
            )
            assert matched, f"Should match: {phrase}"

    def test_mixed_content_keywords(self):
        from gold_miner.harness.memory.long_term_memory import MemoryStore

        store = MemoryStore.__new__(MemoryStore)
        store.state = None

        assert any(
            re.search(pattern, "remember the table schema")
            for pattern in store.REMEMBER_KEYWORDS
        )


class TestContextManagerCompression:
    def test_auto_compress_when_exceeds_threshold(self):
        config = ContextConfig(max_tokens=100, compress_threshold=0.5)
        ctx = ContextManager(config)

        for i in range(10):
            ctx.add_message(MessageRole.USER, f"Message number {i} with some content here")

        assert len(ctx._messages) < 10

    def test_system_message_preserved_after_compress(self):
        config = ContextConfig(max_tokens=50, compress_threshold=0.3)
        ctx = ContextManager(config)

        ctx.add_message(MessageRole.SYSTEM, "System prompt - CRITICAL")
        for i in range(5):
            ctx.add_message(MessageRole.USER, f"User message {i}")

        ctx.compress()

        system_msgs = [m for m in ctx._messages if m.role == MessageRole.SYSTEM]
        assert len(system_msgs) >= 1
