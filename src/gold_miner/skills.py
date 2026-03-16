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
    invisible_context: bool = False
    hooks: List[str] = None


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

    def _load_skill_md(self, skill_dir: str) -> Dict[str, Any]:
        md_path = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(md_path):
            return None
        
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        skill_info = {"description": content}
        
        for line in content.split("\n"):
            if line.startswith("## 名称") or line.startswith("# 名称"):
                skill_info["name_from_md"] = line.split(":")[-1].strip()
            elif line.startswith("## 参数") or line.startswith("# 参数"):
                skill_info["has_params"] = True
        
        return skill_info

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
        
        skill_dir = os.path.dirname(path)
        md_info = self._load_skill_md(skill_dir)
        
        invisible_context = skill_def.get("invisible_context", True)
        hooks = skill_def.get("hooks", [])
        
        if md_info:
            description = md_info.get("description", skill_def.get("description", ""))
        else:
            description = skill_def.get("description", "")
        
        skill = Skill(
            name=skill_def["name"],
            description=description,
            inputs=skill_def.get("inputs", {}),
            run=skill_def["run"],
            invisible_context=invisible_context,
            hooks=hooks,
        )
        self.skills[skill.name] = skill

    def list(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": s.name, 
                "description": s.description, 
                "inputs": s.inputs,
                "invisible_context": s.invisible_context,
                "hooks": s.hooks,
            }
            for s in self.skills.values()
        ]

    def get(self, name: str) -> Skill:
        if name not in self.skills:
            raise KeyError(f"Unknown skill: {name}")
        return self.skills[name]

    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in self.skills:
            raise KeyError(f"Unknown skill: {name}")
        return self.skills[name].run(**kwargs)
