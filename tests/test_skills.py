import os
import tempfile

import pytest

from gold_miner.skills import Skill, SkillRegistry


class TestSkill:
    def test_skill_creation(self):
        def dummy_run():
            return "result"

        skill = Skill(
            name="test_skill",
            description="A test skill",
            inputs={"arg1": "string"},
            run=dummy_run,
        )

        assert skill.name == "test_skill"
        assert skill.description == "A test skill"
        assert skill.inputs == {"arg1": "string"}
        assert skill.run() == "result"


class TestSkillRegistry:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.skills_dir = self.temp_dir

    def teardown_method(self):
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_creates_empty_registry(self):
        registry = SkillRegistry(self.skills_dir)
        assert registry.skills == {}

    def test_load_skills_from_empty_dir(self):
        registry = SkillRegistry(self.skills_dir)
        registry.load()
        assert registry.skills == {}

    def test_load_skills_from_non_existent_dir(self):
        registry = SkillRegistry("/non/existent/path")
        registry.load()
        assert registry.skills == {}

    def test_load_single_skill(self):
        skill_content = '''
from typing import Any, Dict
import pandas as pd

def run(dataframe: pd.DataFrame = None, max_rows: int = 5) -> Dict[str, Any]:
    return {"result": "success"}

SKILL = {
    "name": "test_skill",
    "description": "A test skill",
    "inputs": {"dataframe": "pandas.DataFrame", "max_rows": "int"},
    "run": run,
}
'''
        skill_file = os.path.join(self.skills_dir, "test_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)

        registry = SkillRegistry(self.skills_dir)
        registry.load()

        assert "test_skill" in registry.skills
        assert registry.skills["test_skill"].name == "test_skill"
        assert registry.skills["test_skill"].description == "A test skill"

    def test_load_multiple_skills(self):
        skill_content_1 = '''
def run():
    return "skill1"

SKILL = {"name": "skill_one", "description": "First skill", "inputs": {}, "run": run}
'''
        skill_content_2 = '''
def run():
    return "skill2"

SKILL = {"name": "skill_two", "description": "Second skill", "inputs": {}, "run": run}
'''
        with open(os.path.join(self.skills_dir, "skill_one.py"), "w") as f:
            f.write(skill_content_1)
        with open(os.path.join(self.skills_dir, "skill_two.py"), "w") as f:
            f.write(skill_content_2)

        registry = SkillRegistry(self.skills_dir)
        registry.load()

        assert len(registry.skills) == 2
        assert "skill_one" in registry.skills
        assert "skill_two" in registry.skills

    def test_load_ignores_non_python_files(self):
        with open(os.path.join(self.skills_dir, "readme.txt"), "w") as f:
            f.write("This is not a skill")

        registry = SkillRegistry(self.skills_dir)
        registry.load()

        assert registry.skills == {}

    def test_load_ignores_files_without_skill(self):
        skill_content = '''
def some_function():
    return "not a skill"
'''
        skill_file = os.path.join(self.skills_dir, "no_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)

        registry = SkillRegistry(self.skills_dir)
        registry.load()

        assert registry.skills == {}

    def test_list_returns_skill_info(self):
        skill_content = '''
def run():
    return "result"

SKILL = {
    "name": "test_skill",
    "description": "Test description",
    "inputs": {"arg1": "string"},
    "run": run,
}
'''
        skill_file = os.path.join(self.skills_dir, "test_skill.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)

        registry = SkillRegistry(self.skills_dir)
        registry.load()

        skill_list = registry.list()

        assert len(skill_list) == 1
        assert skill_list[0]["name"] == "test_skill"
        assert skill_list[0]["description"] == "Test description"
        assert skill_list[0]["inputs"] == {"arg1": "string"}

    def test_call_executes_skill(self):
        skill_content = '''
def run(message: str = "default"):
    return f"Hello, {message}!"

SKILL = {
    "name": "greet",
    "description": "Greet someone",
    "inputs": {"message": "str"},
    "run": run,
}
'''
        skill_file = os.path.join(self.skills_dir, "greet.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)

        registry = SkillRegistry(self.skills_dir)
        registry.load()

        result = registry.call("greet", message="World")

        assert result == "Hello, World!"

    def test_call_raises_error_for_unknown_skill(self):
        registry = SkillRegistry(self.skills_dir)
        registry.load()

        with pytest.raises(KeyError) as exc_info:
            registry.call("nonexistent")

        assert "Unknown skill" in str(exc_info.value)

    def test_call_passes_dataframe_argument(self):
        import pandas as pd

        skill_content = '''
import pandas as pd

def run(dataframe: pd.DataFrame = None):
    return {"rows": len(dataframe) if dataframe is not None else 0}

SKILL = {
    "name": "count_rows",
    "description": "Count rows",
    "inputs": {"dataframe": "pandas.DataFrame"},
    "run": run,
}
'''
        skill_file = os.path.join(self.skills_dir, "count_rows.py")
        with open(skill_file, "w") as f:
            f.write(skill_content)

        registry = SkillRegistry(self.skills_dir)
        registry.load()

        test_df = pd.DataFrame({"a": [1, 2, 3]})
        result = registry.call("count_rows", dataframe=test_df)

        assert result["rows"] == 3
