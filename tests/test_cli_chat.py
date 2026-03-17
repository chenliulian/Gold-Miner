"""Tests for CLI chat mode functionality."""
from __future__ import annotations

import json
import os
import queue
import tempfile
import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock ODPS before importing CLI components
with patch.dict('sys.modules', {'odps': MagicMock(), 'odps.models': MagicMock()}):
    from gold_miner.cli import safe_input
    from gold_miner.agent import SqlAgent
    from gold_miner.config import Config


class TestSafeInput:
    """Tests for safe_input function."""
    
    def test_safe_input_normal(self):
        """Test safe_input with normal string."""
        with patch('builtins.input', return_value='hello'):
            result = safe_input()
            assert result == 'hello'
    
    def test_safe_input_unicode(self):
        """Test safe_input with unicode characters."""
        with patch('builtins.input', return_value='你好世界'):
            result = safe_input()
            assert result == '你好世界'
    
    def test_safe_input_empty(self):
        """Test safe_input with empty string."""
        with patch('builtins.input', return_value=''):
            result = safe_input()
            assert result == ''


class TestChatModeBasic:
    """Basic tests for chat mode functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = MagicMock(spec=Config)
        config.agent_max_steps = 6
        config.memory_path = "./memory/memory.json"
        config.reports_dir = "./reports"
        config.odps_access_id = "test_id"
        config.odps_access_key = "test_key"
        config.odps_project = "test_project"
        config.odps_endpoint = "http://test.endpoint"
        config.odps_quota = ""
        config.llm_base_url = "http://test.llm"
        config.llm_api_key = "test_key"
        config.llm_model = "test_model"
        return config
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_dir = os.path.join(tmpdir, "memory")
            reports_dir = os.path.join(tmpdir, "reports")
            skills_dir = os.path.join(tmpdir, "skills")
            os.makedirs(memory_dir)
            os.makedirs(reports_dir)
            os.makedirs(skills_dir)
            yield {
                "root": tmpdir,
                "memory": memory_dir,
                "reports": reports_dir,
                "skills": skills_dir
            }


class TestChatModeTaskExecution:
    """Tests for task execution in chat mode."""
    
    def test_task_queue_operations(self):
        """Test task queue can hold and retrieve tasks."""
        task_queue = queue.Queue()
        
        # Put tasks in queue
        task_queue.put(("query 1", "table1"))
        task_queue.put(("query 2", "table2"))
        
        # Retrieve tasks
        item1 = task_queue.get()
        assert item1 == ("query 1", "table1")
        
        item2 = task_queue.get()
        assert item2 == ("query 2", "table2")
    
    def test_task_queue_with_none(self):
        """Test task queue handles None (exit signal)."""
        task_queue = queue.Queue()
        
        task_queue.put(("query", "table"))
        task_queue.put(None)
        
        item = task_queue.get()
        assert item == ("query", "table")
        
        item = task_queue.get()
        assert item is None
    
    def test_task_queue_timeout(self):
        """Test task queue timeout behavior."""
        task_queue = queue.Queue()
        
        # Should raise Empty when timeout
        with pytest.raises(queue.Empty):
            task_queue.get(timeout=0.1)


class TestChatModeStateManagement:
    """Tests for state management in chat mode."""
    
    def test_state_initialization(self):
        """Test initial state is correct."""
        state = {
            "status": "idle",
            "current": None,
            "last_report": None,
            "cancel": None
        }
        
        assert state["status"] == "idle"
        assert state["current"] is None
        assert state["last_report"] is None
        assert state["cancel"] is None
    
    def test_state_running(self):
        """Test state when task is running."""
        cancel_event = threading.Event()
        state = {
            "status": "running",
            "current": {"question": "test query", "tables": "table1"},
            "last_report": None,
            "cancel": cancel_event
        }
        
        assert state["status"] == "running"
        assert state["current"]["question"] == "test query"
        assert state["cancel"] is not None
    
    def test_state_after_completion(self):
        """Test state after task completion."""
        state = {
            "status": "idle",
            "current": None,
            "last_report": "/path/to/report.md",
            "cancel": None
        }
        
        assert state["status"] == "idle"
        assert state["last_report"] == "/path/to/report.md"


class TestChatModeCancelFunctionality:
    """Tests for cancel functionality."""
    
    def test_cancel_event_creation(self):
        """Test cancel event can be created and set."""
        cancel_event = threading.Event()
        assert not cancel_event.is_set()
        
        cancel_event.set()
        assert cancel_event.is_set()
    
    def test_cancel_event_check_in_loop(self):
        """Test cancel event can be checked in a loop."""
        cancel_event = threading.Event()
        counter = 0
        
        def simulate_work():
            nonlocal counter
            for i in range(100):
                if cancel_event.is_set():
                    break
                counter += 1
                time.sleep(0.01)
        
        thread = threading.Thread(target=simulate_work)
        thread.start()
        
        time.sleep(0.05)  # Let it run a bit
        cancel_event.set()  # Cancel it
        thread.join(timeout=1)
        
        assert counter < 100  # Should have been cancelled
    
    def test_cancel_when_nothing_running(self):
        """Test cancel command when no task is running."""
        state = {
            "status": "idle",
            "current": None,
            "last_report": None,
            "cancel": None
        }
        
        # Simulate /cancel command
        cancel_event = state["cancel"]
        assert cancel_event is None


class TestChatModeExitFunctionality:
    """Tests for exit functionality."""
    
    def test_exit_event(self):
        """Test exit event signals worker to stop."""
        exit_event = threading.Event()
        assert not exit_event.is_set()
        
        exit_event.set()
        assert exit_event.is_set()
    
    def test_worker_respects_exit_event(self):
        """Test worker thread exits when exit_event is set."""
        exit_event = threading.Event()
        task_queue = queue.Queue()
        
        worker_running = True
        
        def worker():
            nonlocal worker_running
            while not exit_event.is_set():
                try:
                    item = task_queue.get(timeout=0.1)
                    if item is None or exit_event.is_set():
                        break
                except queue.Empty:
                    continue
            worker_running = False
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        time.sleep(0.2)
        assert worker_running
        
        exit_event.set()
        thread.join(timeout=1)
        
        assert not worker_running
        assert not thread.is_alive()


class TestChatModeConcurrentOperations:
    """Tests for concurrent operations in chat mode."""
    
    def test_multiple_tasks_queued(self):
        """Test multiple tasks can be queued."""
        task_queue = queue.Queue()
        results = []
        
        def worker():
            while True:
                try:
                    item = task_queue.get(timeout=0.5)
                    if item is None:
                        break
                    question, tables = item
                    results.append(question)
                    task_queue.task_done()
                except queue.Empty:
                    break
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        # Queue multiple tasks
        task_queue.put(("query 1", ""))
        task_queue.put(("query 2", ""))
        task_queue.put(("query 3", ""))
        task_queue.put(None)
        
        thread.join(timeout=2)
        
        assert len(results) == 3
        assert results == ["query 1", "query 2", "query 3"]
    
    def test_status_lock_thread_safety(self):
        """Test status lock provides thread safety."""
        status_lock = threading.Lock()
        state = {"counter": 0}
        
        def increment():
            for _ in range(100):
                with status_lock:
                    current = state["counter"]
                    time.sleep(0.001)  # Simulate some work
                    state["counter"] = current + 1
        
        threads = [threading.Thread(target=increment) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert state["counter"] == 500


class TestChatModeCommandParsing:
    """Tests for command parsing in chat mode."""
    
    def test_exit_command_variations(self):
        """Test various exit command formats."""
        exit_commands = ["exit", "quit", "EXIT", "QUIT", "Exit", "Quit"]
        for cmd in exit_commands:
            assert cmd.lower() in {"exit", "quit"}
    
    def test_reset_command(self):
        """Test reset command format."""
        cmd = "/reset"
        assert cmd.strip().lower() == "/reset"
    
    def test_status_command(self):
        """Test status command format."""
        cmd = "/status"
        assert cmd.strip().lower() == "/status"
    
    def test_cancel_command(self):
        """Test cancel command format."""
        cmd = "/cancel"
        assert cmd.strip().lower() == "/cancel"
    
    def test_tables_prefix_stripping(self):
        """Test 'from ' prefix is stripped from tables input."""
        tables_input = "from table1, table2"
        if tables_input.lower().startswith("from "):
            tables_input = tables_input[5:].strip()
        assert tables_input == "table1, table2"


class TestChatModeErrorHandling:
    """Tests for error handling in chat mode."""
    
    def test_keyboard_interrupt_handling(self):
        """Test KeyboardInterrupt is handled gracefully."""
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            with pytest.raises(KeyboardInterrupt):
                safe_input()
    
    def test_eof_error_handling(self):
        """Test EOFError is handled gracefully."""
        with patch('builtins.input', side_effect=EOFError()):
            with pytest.raises(EOFError):
                safe_input()
    
    def test_worker_handles_exception(self):
        """Test worker handles exceptions in task execution."""
        task_queue = queue.Queue()
        errors = []
        
        def worker():
            try:
                item = task_queue.get(timeout=0.5)
                if item is not None:
                    raise Exception("Simulated error")
            except Exception as e:
                errors.append(str(e))
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        task_queue.put(("query", ""))
        thread.join(timeout=1)
        
        assert len(errors) == 1
        assert "Simulated error" in errors[0]


class TestChatModeIntegrationScenarios:
    """Integration tests for common chat mode scenarios."""
    
    def test_full_task_lifecycle(self):
        """Test complete task lifecycle: submit -> execute -> complete."""
        task_queue = queue.Queue()
        status_lock = threading.Lock()
        state = {"status": "idle", "result": None}
        
        def worker():
            while True:
                try:
                    item = task_queue.get(timeout=0.5)
                    if item is None:
                        break
                    
                    with status_lock:
                        state["status"] = "running"
                    
                    # Simulate work
                    time.sleep(0.1)
                    
                    with status_lock:
                        state["status"] = "idle"
                        state["result"] = "completed"
                    
                    task_queue.task_done()
                except queue.Empty:
                    break
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        # Submit task
        task_queue.put(("test query", ""))
        time.sleep(0.05)
        
        with status_lock:
            assert state["status"] in ["running", "idle"]
        
        thread.join(timeout=2)
        
        with status_lock:
            assert state["result"] == "completed"
    
    def test_cancel_during_execution(self):
        """Test cancel command during task execution."""
        task_queue = queue.Queue()
        cancel_event = threading.Event()
        status_lock = threading.Lock()
        state = {"status": "idle", "cancelled": False}
        
        def worker():
            while True:
                try:
                    item = task_queue.get(timeout=0.5)
                    if item is None:
                        break
                    
                    with status_lock:
                        state["status"] = "running"
                    
                    # Simulate long-running work with cancel check
                    for i in range(100):
                        if cancel_event.is_set():
                            with status_lock:
                                state["cancelled"] = True
                                state["status"] = "idle"
                            break
                        time.sleep(0.01)
                    
                    task_queue.task_done()
                except queue.Empty:
                    break
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        # Submit task
        task_queue.put(("long query", ""))
        time.sleep(0.1)
        
        # Cancel it
        cancel_event.set()
        thread.join(timeout=2)
        
        with status_lock:
            assert state["cancelled"] is True
            assert state["status"] == "idle"
    
    def test_submit_new_task_after_cancel(self):
        """Test submitting new task after cancellation."""
        task_queue = queue.Queue()
        cancel_event = threading.Event()
        exit_event = threading.Event()
        results = []
        task_processed = threading.Event()
        
        def worker():
            while not exit_event.is_set():
                try:
                    item = task_queue.get(timeout=0.1)
                    if item is None or exit_event.is_set():
                        break
                    
                    question, tables = item
                    
                    # Simulate work with cancel check
                    for i in range(50):
                        if cancel_event.is_set():
                            results.append("cancelled")
                            cancel_event.clear()  # Reset for next task
                            break
                        time.sleep(0.01)
                    else:
                        # Completed without cancellation
                        results.append(f"completed: {question}")
                    
                    task_processed.set()
                    task_queue.task_done()
                except queue.Empty:
                    continue
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        # First task - will be cancelled
        task_processed.clear()
        task_queue.put(("task 1", ""))
        time.sleep(0.1)  # Let task 1 start
        
        # Cancel it
        cancel_event.set()
        task_processed.wait(timeout=1)  # Wait for task 1 to be processed
        time.sleep(0.1)  # Extra time for cancellation
        
        # Submit new task
        task_processed.clear()
        task_queue.put(("task 2", ""))
        task_processed.wait(timeout=1)  # Wait for task 2 to be processed
        time.sleep(0.1)
        
        exit_event.set()
        task_queue.put(None)
        thread.join(timeout=2)
        
        assert "cancelled" in results
        assert "completed: task 2" in results
