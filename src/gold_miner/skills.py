from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class Skill:
    name: str
    description: str
    inputs: Dict[str, Any]
    run: Callable[..., Any]


class SkillRegistry:
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}

    def load(self) -> None:
        if not os.path.isdir(self.skills_dir):
            return
        self._load_from_dir(self.skills_dir)

    def _load_from_dir(self, directory: str) -> None:
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isdir(path):
                self._load_from_dir(path)
            elif filename.endswith(".py"):
                self._load_file(path)

    def _load_file(self, path: str) -> None:
        module_name = f"skill_{os.path.splitext(os.path.basename(path))[0]}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        skill_def = getattr(module, "SKILL", None)
        if not skill_def:
            return
        skill = Skill(
            name=skill_def["name"],
            description=skill_def.get("description", ""),
            inputs=skill_def.get("inputs", {}),
            run=skill_def["run"],
        )
        self.skills[skill.name] = skill

    def list(self) -> List[Dict[str, Any]]:
        return [
            {"name": s.name, "description": s.description, "inputs": s.inputs}
            for s in self.skills.values()
        ]

    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in self.skills:
            raise KeyError(f"Unknown skill: {name}")
        return self.skills[name].run(**kwargs)
