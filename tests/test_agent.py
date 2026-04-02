"""Tests for gold_miner.agent module."""

import pytest
from gold_miner.agent import AgentState, QueryResult


class TestAgentState:
    """Test cases for AgentState class."""

    def test_record_skill_call_basic(self):
        """Test basic skill call recording."""
        state = AgentState()
        
        # Record a skill call
        state.record_skill_call("explore_table", {"table_name": "test_table"})
        
        assert len(state.recent_skills) == 1
        assert state.recent_skills[0]["skill"] == "explore_table"
        assert state.recent_skills[0]["args"]["table_name"] == "test_table"
        assert "timestamp" in state.recent_skills[0]
    
    def test_record_skill_call_multiple(self):
        """Test recording multiple skill calls."""
        state = AgentState()
        
        # Record multiple skill calls
        for i in range(15):
            state.record_skill_call(f"skill_{i}", {"index": i})
        
        # Should only keep last 10 (MAX_RECENT_SKILLS)
        assert len(state.recent_skills) == 10
        assert state.recent_skills[0]["skill"] == "skill_5"
        assert state.recent_skills[-1]["skill"] == "skill_14"
    
    def test_is_skill_recently_called_same_skill(self):
        """Test checking if same skill was recently called."""
        state = AgentState()
        
        state.record_skill_call("explore_table", {"table_name": "table1"})
        
        # Should detect recent call
        assert state.is_skill_recently_called("explore_table", {"table_name": "table1"})
        
        # Different args should not match
        assert not state.is_skill_recently_called("explore_table", {"table_name": "table2"})
    
    def test_is_skill_recently_called_different_skill(self):
        """Test checking different skill."""
        state = AgentState()
        
        state.record_skill_call("explore_table", {"table_name": "table1"})
        
        # Different skill should not match
        assert not state.is_skill_recently_called("other_skill", {"table_name": "table1"})
    
    def test_is_skill_recently_called_self_improvement(self):
        """Test self_improvement skill special handling."""
        state = AgentState()
        
        # Record self_improvement with summary
        state.record_skill_call("self_improvement", {
            "summary": "test summary",
            "content": "test content"
        })
        
        # Should match same summary
        assert state.is_skill_recently_called("self_improvement", {
            "summary": "test summary",
            "content": "different content"
        })
        
        # Should match same content
        assert state.is_skill_recently_called("self_improvement", {
            "summary": "different summary",
            "content": "test content"
        })
        
        # Different both should not match
        assert not state.is_skill_recently_called("self_improvement", {
            "summary": "different summary",
            "content": "different content"
        })


class TestQueryResult:
    """Test cases for QueryResult dataclass."""

    def test_query_result_creation(self):
        """Test creating QueryResult."""
        result = QueryResult(
            sql="SELECT * FROM test",
            preview="| col1 | col2 |\n|------|------|\n| 1 | 2 |",
            rows=100,
            columns=["col1", "col2"]
        )
        
        assert result.sql == "SELECT * FROM test"
        assert result.rows == 100
        assert result.columns == ["col1", "col2"]
