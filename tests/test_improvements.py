#!/usr/bin/env python3
"""Test script to verify all improvements are working."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_security():
    """Test SQL injection protection."""
    print("\n=== Testing SQL Injection Protection ===")
    from gold_miner.security import create_default_validator

    validator = create_default_validator()

    # Test valid SQL
    valid_sql = "SELECT * FROM users WHERE id = 1"
    result = validator.validate(valid_sql)
    assert result.is_valid, f"Valid SQL should pass: {result.errors}"
    print(f"✓ Valid SQL passed: {valid_sql[:50]}...")

    # Test SQL injection
    injection_sql = "SELECT * FROM users; DROP TABLE users; --"
    result = validator.validate(injection_sql)
    assert not result.is_valid, "SQL injection should be blocked"
    print(f"✓ SQL injection blocked: {injection_sql[:50]}...")

    print("✅ Security tests passed!")


def test_rate_limiter():
    """Test rate limiting."""
    print("\n=== Testing Rate Limiter ===")
    from gold_miner.rate_limiter import RateLimiter, RateLimitConfig

    config = RateLimitConfig(requests=5, window=60)
    limiter = RateLimiter(config)

    # Test within limit
    for i in range(5):
        allowed, info = limiter.is_allowed("test_key")
        assert allowed, f"Request {i+1} should be allowed"

    # Test exceeding limit
    allowed, info = limiter.is_allowed("test_key")
    assert not allowed, "6th request should be blocked"
    print("✓ Rate limiting works correctly")

    print("✅ Rate limiter tests passed!")


def test_circuit_breaker():
    """Test circuit breaker."""
    print("\n=== Testing Circuit Breaker ===")
    from gold_miner.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpen

    config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1.0)
    breaker = CircuitBreaker("test", config)

    # Test successful call
    def success_func():
        return "success"

    result = breaker.call(success_func)
    assert result == "success", "Successful call should return result"
    print("✓ Successful call works")

    # Test failure counting
    def fail_func():
        raise ValueError("test error")

    for i in range(3):
        try:
            breaker.call(fail_func)
        except ValueError:
            pass

    stats = breaker.get_stats()
    assert stats["failure_count"] == 3, "Failure count should be 3"
    print(f"✓ Failure counting works: {stats['failure_count']} failures")

    print("✅ Circuit breaker tests passed!")


def test_file_utils():
    """Test file utilities."""
    print("\n=== Testing File Utilities ===")
    from gold_miner.file_utils import atomic_write, safe_read_json
    import tempfile
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.json")

        # Test atomic write
        data = {"key": "value", "number": 42}
        atomic_write(test_file, json.dumps(data))
        print("✓ Atomic write successful")

        # Test safe read
        result = safe_read_json(test_file)
        assert result == data, f"Read data should match: {result}"
        print("✓ Safe read JSON works")

        # Test non-existent file
        result = safe_read_json(os.path.join(tmpdir, "nonexistent.json"), default={"default": True})
        assert result == {"default": True}, "Should return default for non-existent file"
        print("✓ Safe read with default works")

    print("✅ File utilities tests passed!")


def test_agent_state():
    """Test agent state with memory limits."""
    print("\n=== Testing Agent State Memory Limits ===")
    from gold_miner.agent import AgentState, QueryResult

    state = AgentState(MAX_RESULTS=5, MAX_NOTES=10, MAX_EXECUTED_SQLS=3)

    # Test result limit
    for i in range(10):
        state.add_result(QueryResult(sql=f"SELECT {i}", preview="", rows=i, columns=[]))

    assert len(state.results) == 5, f"Results should be limited to 5, got {len(state.results)}"
    print(f"✓ Results limited to {len(state.results)}")

    # Test notes limit
    for i in range(15):
        state.add_note(f"Note {i}")

    assert len(state.notes) == 10, f"Notes should be limited to 10, got {len(state.notes)}"
    print(f"✓ Notes limited to {len(state.notes)}")

    # Test executed SQLs limit
    for i in range(5):
        state.add_executed_sql({"sql": f"SELECT {i}", "rows": i})

    assert len(state.executed_sqls) == 3, f"Executed SQLs should be limited to 3, got {len(state.executed_sqls)}"
    print(f"✓ Executed SQLs limited to {len(state.executed_sqls)}")

    print("✅ Agent state tests passed!")


def test_config():
    """Test configuration."""
    print("\n=== Testing Configuration ===")
    from gold_miner.config import Config

    # Test that new config fields exist
    config = Config(
        llm_base_url="http://test",
        llm_api_key="test",
        llm_model="test",
        odps_access_id="test",
        odps_access_key="test",
        odps_project="test",
        odps_endpoint="http://test",
    )

    # Check new fields have defaults
    assert hasattr(config, 'agent_pool_min_size')
    assert hasattr(config, 'agent_pool_max_size')
    assert hasattr(config, 'rate_limit_default_per_minute')
    assert hasattr(config, 'circuit_breaker_failure_threshold')
    print("✓ New config fields exist")

    print("✅ Configuration tests passed!")


def test_services():
    """Test service layer."""
    print("\n=== Testing Service Layer ===")
    from gold_miner.services import get_task_queue

    # Test task queue
    queue = get_task_queue()
    assert queue is not None, "Task queue should be created"
    print("✓ Task queue created")

    stats = queue.get_stats()
    assert "queue_size" in stats, "Stats should include queue_size"
    print(f"✓ Task queue stats: {stats}")

    print("✅ Service layer tests passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("GoldMiner Improvements Test Suite")
    print("=" * 60)

    try:
        test_security()
        test_rate_limiter()
        test_circuit_breaker()
        test_file_utils()
        test_agent_state()
        test_config()
        test_services()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
