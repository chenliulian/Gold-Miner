"""Tests for skill integration with agent and various scenarios.

本测试文件包含对 Skill 调用功能的全面测试，包括：
- Skill 调用场景（无参数、多参数、默认值等）
- SkillRegistry 高级功能（重载、获取、列表）
- ODPS 相关操作（SQL 查询、DataFrame 处理）
- Skill 链式调用
- 边界情况测试（None 返回、空字典、大数据集、嵌套数据）

测试用例总数: 17
"""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from gold_miner.skills import Skill, SkillRegistry


class TestSkillCallScenarios:
    """测试各种 Skill 调用场景"""
    
    @pytest.fixture
    def temp_skills_dir(self):
        """创建临时目录用于存放测试用的 skill 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_skill_call_with_no_arguments(self, temp_skills_dir):
        """测试调用无参数的 Skill
        
        场景：调用一个不需要任何参数的 skill
        """
        skill_content = '''
def run():
    return "executed successfully"

SKILL = {
    "name": "simple_skill",
    "description": "A simple skill with no args",
    "inputs": {},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "simple_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        # 调用 skill，不传递任何参数
        result = registry.call("simple_skill")
        assert result == "executed successfully"
    
    def test_skill_call_with_multiple_arguments(self, temp_skills_dir):
        """测试调用带多个参数的 Skill
        
        场景：调用一个需要多个参数的 skill，验证参数传递正确
        """
        skill_content = '''
def run(a: int, b: int, c: str = "default"):
    return {"sum": a + b, "message": c}

SKILL = {
    "name": "multi_arg_skill",
    "description": "Skill with multiple args",
    "inputs": {"a": "int", "b": "int", "c": "str"},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "multi_arg_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        # 调用 skill，传递多个参数
        result = registry.call("multi_arg_skill", a=10, b=20, c="test")
        assert result == {"sum": 30, "message": "test"}
    
    def test_skill_call_with_default_arguments(self, temp_skills_dir):
        """测试调用带默认参数的 Skill
        
        场景：调用 skill 时，不传参使用默认值，传参则覆盖默认值
        """
        skill_content = '''
def run(person_name: str = "World", greeting: str = "Hello"):
    return f"{greeting}, {person_name}!"

SKILL = {
    "name": "greet_skill",
    "description": "Greeting skill",
    "inputs": {"person_name": "str", "greeting": "str"},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "greet_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        # 调用 skill 使用默认值
        result = registry.call("greet_skill")
        assert result == "Hello, World!"
        
        # 调用 skill 覆盖默认值
        result = registry.call("greet_skill", person_name="Alice", greeting="Hi")
        assert result == "Hi, Alice!"
    
    def test_skill_call_with_dataframe(self, temp_skills_dir):
        """测试调用带 DataFrame 参数的 Skill
        
        场景：调用 skill 并传递 pandas DataFrame 作为参数
        """
        skill_content = '''
import pandas as pd

def run(dataframe: pd.DataFrame = None):
    if dataframe is None:
        return {"error": "No dataframe provided"}
    return {
        "rows": len(dataframe),
        "columns": list(dataframe.columns),
        "dtypes": {col: str(dtype) for col, dtype in dataframe.dtypes.items()},
    }

SKILL = {
    "name": "analyze_df",
    "description": "Analyze dataframe",
    "inputs": {"dataframe": "pandas.DataFrame"},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "analyze_df.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        # 创建测试用的 DataFrame
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
        })
        
        result = registry.call("analyze_df", dataframe=df)
        
        assert result["rows"] == 3
        assert set(result["columns"]) == {"id", "name", "age"}
    
    def test_skill_call_with_complex_return_value(self, temp_skills_dir):
        """测试返回复杂数据结构的 Skill
        
        场景：skill 返回包含嵌套字典的复杂数据结构
        """
        skill_content = '''
import pandas as pd

def run(dataframe: pd.DataFrame = None):
    if dataframe is None or dataframe.empty:
        return {
            "success": False,
            "error": "Empty dataframe",
            "stats": {},
        }
    
    # 不使用 select_dtypes 以避免兼容性问题
    numeric_cols = []
    for col in dataframe.columns:
        if dataframe[col].dtype in ['int64', 'float64', 'int32', 'float32']:
            numeric_cols.append(col)
    
    stats = {}
    for col in numeric_cols:
        col_data = list(dataframe[col])
        # 手动计算统计数据，避免 numpy/pandas 兼容性问题
        mean_val = sum(col_data) / len(col_data)
        min_val = min(col_data)
        max_val = max(col_data)
        stats[col] = {
            "mean": float(mean_val),
            "min": float(min_val),
            "max": float(max_val),
        }
    
    return {
        "success": True,
        "rows": len(dataframe),
        "numeric_columns": numeric_cols,
        "stats": stats,
    }

SKILL = {
    "name": "calc_stats",
    "description": "Calculate statistics",
    "inputs": {"dataframe": "pandas.DataFrame"},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "calc_stats.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        df = pd.DataFrame({
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50],
        })
        
        result = registry.call("calc_stats", dataframe=df)
        
        assert result["success"] is True
        assert result["rows"] == 5
        assert "A" in result["stats"]
        assert "B" in result["stats"]
        assert result["stats"]["A"]["mean"] == 3.0
    
    def test_skill_call_raises_exception(self, temp_skills_dir):
        """测试执行时抛出异常的 Skill
        
        场景：skill 执行过程中抛出异常，验证异常能正确传播
        """
        skill_content = '''
def run(should_fail: bool = False):
    if should_fail:
        raise ValueError("Intentional failure")
    return "success"

SKILL = {
    "name": "error_skill",
    "description": "Skill that can error",
    "inputs": {"should_fail": "bool"},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "error_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        # 应该抛出异常
        with pytest.raises(ValueError) as exc_info:
            registry.call("error_skill", should_fail=True)
        
        assert "Intentional failure" in str(exc_info.value)
        
        # 正常执行应该成功
        result = registry.call("error_skill", should_fail=False)
        assert result == "success"


class TestSkillRegistryAdvanced:
    """测试 SkillRegistry 的高级功能"""
    
    @pytest.fixture
    def temp_skills_dir(self):
        """创建临时目录用于存放测试用的 skill 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_reload_skills(self, temp_skills_dir):
        """测试重新加载 skills
        
        场景：在运行时添加新的 skill 文件，然后重新加载
        """
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        assert len(registry.skills) == 0
        
        # 添加新的 skill 文件
        skill_content = '''
def run():
    return "new skill"

SKILL = {"name": "new_skill", "description": "New", "inputs": {}, "run": run}
'''
        skill_file = os.path.join(temp_skills_dir, "new_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        # 重新加载
        registry.load()
        
        assert "new_skill" in registry.skills
    
    def test_get_skill_method(self, temp_skills_dir):
        """测试获取单个 skill 对象
        
        场景：通过名称获取 skill 对象，验证其属性
        """
        skill_content = '''
def run():
    return "test"

SKILL = {"name": "test_skill", "description": "Test", "inputs": {}, "run": run}
'''
        skill_file = os.path.join(temp_skills_dir, "test_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        skill = registry.get("test_skill")
        assert skill.name == "test_skill"
        assert skill.description == "Test"
        
        # 获取不存在的 skill 应该抛出 KeyError
        with pytest.raises(KeyError):
            registry.get("unknown")
    
    def test_list_empty_registry(self, temp_skills_dir):
        """测试空 registry 的列表功能
        
        场景：当 registry 为空时，list() 应该返回空列表
        """
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        skill_list = registry.list()
        assert skill_list == []
    
    def test_list_with_invisible_skills(self, temp_skills_dir):
        """测试包含不可见 skill 的列表功能
        
        场景：skill 可以标记为 invisible_context，但 list() 仍然会返回
        """
        skill_content = '''
def run():
    return "invisible"

SKILL = {
    "name": "invisible_skill",
    "description": "Invisible skill",
    "inputs": {},
    "run": run,
    "invisible_context": True,
}
'''
        skill_file = os.path.join(temp_skills_dir, "invisible_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        skill_list = registry.list()
        assert len(skill_list) == 1
        assert skill_list[0]["name"] == "invisible_skill"


class TestSkillWithODPSOperations:
    """测试与 ODPS 操作相关的 skills"""
    
    @pytest.fixture
    def temp_skills_dir(self):
        """创建临时目录用于存放测试用的 skill 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_skill_with_sql_query(self, temp_skills_dir):
        """测试执行 SQL 查询的 Skill（模拟）
        
        场景：skill 接收表名和条件，返回模拟的查询结果
        """
        skill_content = '''
from typing import Any, Dict

def run(table: str = "", condition: str = "") -> Dict[str, Any]:
    # 这里通常会查询 ODPS，但测试中使用模拟数据
    return {
        "table": table,
        "condition": condition,
        "rows": 100,  # 模拟结果
    }

SKILL = {
    "name": "query_table",
    "description": "Query a table",
    "inputs": {"table": "str", "condition": "str"},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "query_table.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        result = registry.call("query_table", table="users", condition="age > 18")
        
        assert result["table"] == "users"
        assert result["condition"] == "age > 18"
        assert result["rows"] == 100
    
    def test_skill_with_dataframe_processing(self, temp_skills_dir):
        """测试处理 DataFrame 的 Skill
        
        场景：skill 接收 DataFrame，进行分组统计
        """
        skill_content = '''
import pandas as pd
from typing import Any, Dict

def run(dataframe: pd.DataFrame = None, group_by: str = None) -> Dict[str, Any]:
    if dataframe is None or dataframe.empty:
        return {"error": "No data"}
    
    result = {
        "total_rows": len(dataframe),
        "columns": list(dataframe.columns),
    }
    
    if group_by and group_by in dataframe.columns:
        result["groups"] = dataframe[group_by].nunique()
        result["group_counts"] = dataframe[group_by].value_counts().to_dict()
    
    return result

SKILL = {
    "name": "summarize_data",
    "description": "Summarize dataframe",
    "inputs": {"dataframe": "pandas.DataFrame", "group_by": "str"},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "summarize_data.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        df = pd.DataFrame({
            "category": ["A", "B", "A", "B", "A"],
            "value": [10, 20, 30, 40, 50],
        })
        
        result = registry.call("summarize_data", dataframe=df, group_by="category")
        
        assert result["total_rows"] == 5
        assert result["groups"] == 2
        assert "A" in result["group_counts"]
        assert "B" in result["group_counts"]


class TestSkillChaining:
    """测试多个 skill 链式调用"""
    
    @pytest.fixture
    def temp_skills_dir(self):
        """创建临时目录用于存放测试用的 skill 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_chain_skills(self, temp_skills_dir):
        """测试链式调用多个 skills
        
        场景：先调用 filter_data 过滤数据，再调用 aggregate_data 聚合数据
        """
        # 第一个 skill - 过滤数据
        filter_skill = '''
import pandas as pd

def run(dataframe: pd.DataFrame = None, min_value: int = 0):
    if dataframe is None:
        return None
    # 使用简单迭代代替布尔索引，避免兼容性问题
    filtered_data = []
    for idx, row in dataframe.iterrows():
        if row["value"] >= min_value:
            filtered_data.append(row)
    if not filtered_data:
        return pd.DataFrame(columns=dataframe.columns)
    return pd.DataFrame(filtered_data)

SKILL = {
    "name": "filter_data",
    "description": "Filter data by value",
    "inputs": {"dataframe": "pandas.DataFrame", "min_value": "int"},
    "run": run,
}
'''
        # 第二个 skill - 聚合数据
        agg_skill = '''
import pandas as pd

def run(dataframe: pd.DataFrame = None):
    if dataframe is None or dataframe.empty:
        return {"sum": 0, "avg": 0}
    # 手动计算 sum 和 avg，避免兼容性问题
    values = list(dataframe["value"])
    total = sum(values)
    avg = total / len(values)
    return {
        "sum": int(total),
        "avg": float(avg),
    }

SKILL = {
    "name": "aggregate_data",
    "description": "Aggregate data",
    "inputs": {"dataframe": "pandas.DataFrame"},
    "run": run,
}
'''
        with open(os.path.join(temp_skills_dir, "filter_data.py"), "w") as f:
            f.write(filter_skill)
        with open(os.path.join(temp_skills_dir, "aggregate_data.py"), "w") as f:
            f.write(agg_skill)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        # 原始数据
        df = pd.DataFrame({
            "value": [10, 20, 5, 30, 15],
        })
        
        # 链式调用: filter -> aggregate
        filtered = registry.call("filter_data", dataframe=df, min_value=15)
        result = registry.call("aggregate_data", dataframe=filtered)
        
        # 过滤后: 20, 30, 15 (values >= 15)
        assert result["sum"] == 65  # 20 + 30 + 15
        assert result["avg"] == 65 / 3


class TestSkillEdgeCases:
    """测试边界情况"""
    
    @pytest.fixture
    def temp_skills_dir(self):
        """创建临时目录用于存放测试用的 skill 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_skill_with_none_return(self, temp_skills_dir):
        """测试返回 None 的 Skill
        
        场景：skill 返回 None，验证能正确处理
        """
        skill_content = '''
def run():
    return None

SKILL = {"name": "none_skill", "description": "Returns None", "inputs": {}, "run": run}
'''
        skill_file = os.path.join(temp_skills_dir, "none_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        result = registry.call("none_skill")
        assert result is None
    
    def test_skill_with_empty_dict_return(self, temp_skills_dir):
        """测试返回空字典的 Skill
        
        场景：skill 返回空字典，验证能正确处理
        """
        skill_content = '''
def run():
    return {}

SKILL = {"name": "empty_skill", "description": "Returns empty", "inputs": {}, "run": run}
'''
        skill_file = os.path.join(temp_skills_dir, "empty_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        result = registry.call("empty_skill")
        assert result == {}
    
    def test_skill_with_large_dataframe(self, temp_skills_dir):
        """测试处理大数据集的 Skill
        
        场景：skill 处理包含 10000 行的 DataFrame
        """
        skill_content = '''
import pandas as pd

def run(dataframe: pd.DataFrame = None):
    if dataframe is None:
        return {"error": "No data"}
    return {
        "rows": len(dataframe),
        "memory_usage": dataframe.memory_usage(deep=True).sum(),
    }

SKILL = {
    "name": "large_df_skill",
    "description": "Process large dataframe",
    "inputs": {"dataframe": "pandas.DataFrame"},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "large_df_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        # 创建大数据集
        df = pd.DataFrame({
            "id": range(10000),
            "value": range(10000),
        })
        
        result = registry.call("large_df_skill", dataframe=df)
        
        assert result["rows"] == 10000
        assert result["memory_usage"] > 0
    
    def test_skill_with_nested_data(self, temp_skills_dir):
        """测试返回嵌套数据的 Skill
        
        场景：skill 返回多层嵌套的数据结构
        """
        skill_content = '''
def run():
    return {
        "level1": {
            "level2": {
                "level3": ["deep", "nested", "data"]
            }
        },
        "list_of_dicts": [
            {"name": "item1", "value": 1},
            {"name": "item2", "value": 2},
        ],
    }

SKILL = {
    "name": "nested_skill",
    "description": "Returns nested data",
    "inputs": {},
    "run": run,
}
'''
        skill_file = os.path.join(temp_skills_dir, "nested_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)
        
        registry = SkillRegistry(temp_skills_dir)
        registry.load()
        
        result = registry.call("nested_skill")
        
        # 验证嵌套数据结构
        assert result["level1"]["level2"]["level3"] == ["deep", "nested", "data"]
        assert len(result["list_of_dicts"]) == 2
