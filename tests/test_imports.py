"""Test that all modules can be imported without errors."""


def test_import_agent():
    """Test agent module imports correctly (including time import fix)."""
    from gold_miner.agent import SqlAgent, AgentState, QueryResult
    assert SqlAgent is not None
    assert AgentState is not None
    assert QueryResult is not None


def test_import_config():
    """Test config module imports."""
    from gold_miner.config import Config
    assert Config is not None


def test_import_memory():
    """Test memory module imports."""
    from gold_miner.memory import MemoryStore, MemoryState
    assert MemoryStore is not None
    assert MemoryState is not None


def test_import_session():
    """Test session module imports."""
    from gold_miner.session import SessionStore, SessionState
    assert SessionStore is not None
    assert SessionState is not None


def test_import_skills():
    """Test skills module imports."""
    from gold_miner.skills import SkillRegistry
    assert SkillRegistry is not None


def test_import_services():
    """Test services module imports."""
    from gold_miner.services import get_agent_pool, get_task_queue
    assert get_agent_pool is not None
    assert get_task_queue is not None
