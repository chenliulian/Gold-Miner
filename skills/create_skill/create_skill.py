import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"

DEFAULT_TEMPLATE = '''from typing import Any, Dict
import pandas as pd


def run({params}) -> Dict[str, Any]:
    """
    {description}
    """
    # Your implementation here
    return {{
        "success": True,
        "result": "..."
    }}


SKILL = {{
    "name": "{skill_name}",
    "description": "{description}",
    "inputs": {{
        {inputs}
    }},
    "run": run,
    "invisible_context": True,
    "hooks": [],
}}
'''


def run(
    skill_name: str,
    skill_description: str,
    code_template: str = "",
    category: str = "utility",
    params: str = "dataframe: pd.DataFrame",
) -> Dict[str, Any]:
    """
    创建新的 Skill

    参数:
        skill_name: Skill 名称
        skill_description: Skill 描述
        code_template: 代码模板
        category: 分类
        params: 函数参数
    """
    if not skill_name or not skill_description:
        return {
            "success": False,
            "error": "skill_name and skill_description are required",
        }

    skill_dir = SKILLS_DIR / category / skill_name
    if skill_dir.exists():
        return {
            "success": False,
            "error": f"Skill '{skill_name}' already exists in category '{category}'",
        }

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        if code_template:
            py_content = code_template
        else:
            py_content = DEFAULT_TEMPLATE.format(
                skill_name=skill_name,
                description=skill_description,
                params=params,
                inputs='"dataframe": "pd.DataFrame (可选) - 输入数据"',
            )
        
        py_file = skill_dir / f"{skill_name}.py"
        py_file.write_text(py_content, encoding="utf-8")
        
        md_content = f"""# {skill_name}

## 名称
{skill_name}

## 描述
{skill_description}

## 参数
- dataframe: 输入数据 (可选)

## 输出
返回处理结果

## 使用场景
- {skill_description}
"""
        
        md_file = skill_dir / "SKILL.md"
        md_file.write_text(md_content, encoding="utf-8")
        
        return {
            "success": True,
            "skill_name": skill_name,
            "category": category,
            "path": str(skill_dir),
            "files": [str(py_file), str(md_file)],
            "message": f"Skill '{skill_name}' created successfully",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


SKILL = {
    "name": "create_skill",
    "description": "根据分析任务自动创建新的 Skill，沉淀为可复用的代码模块",
    "inputs": {
        "skill_name": "str (必需) - Skill 名称",
        "skill_description": "str (必需) - Skill 描述",
        "code_template": "str (可选) - 代码模板",
        "category": "str (可选) - 分类，默认 utility",
        "params": "str (可选) - 函数参数",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
