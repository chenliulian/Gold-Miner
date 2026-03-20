#!/usr/bin/env python3
"""
测试 GoldMiner skill 加载机制
"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from gold_miner.skills import SkillRegistry

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

def test_skill_loading():
    print("=" * 60)
    print("GoldMiner Skill 加载测试")
    print("=" * 60)
    print(f"\nSkills 目录: {SKILLS_DIR}")
    print(f"目录存在: {os.path.isdir(SKILLS_DIR)}")
    
    # 创建 registry 并加载
    registry = SkillRegistry(SKILLS_DIR)
    registry.load()
    
    # 获取加载的 skills
    skills = registry.list()
    
    print(f"\n成功加载的 skills 数量: {len(skills)}")
    print("-" * 60)
    
    if skills:
        print("\n已加载的 skills:")
        for skill in skills:
            print(f"  - {skill['name']}")
            print(f"    描述: {skill['description'][:80]}...")
            print(f"    输入参数: {list(skill['inputs'].keys()) if skill['inputs'] else '无'}")
            print()
    else:
        print("\n警告: 没有加载到任何 skill!")
    
    # 检查特定 skill
    print("-" * 60)
    print("\n检查特定 skills:")
    
    target_skills = [
        "adgroup_funnel_analysis",
        "search_conversation",
        "explore_table",
        "tavily_search",
    ]
    
    for skill_name in target_skills:
        try:
            skill = registry.get(skill_name)
            print(f"  ✓ {skill_name}: 已加载")
        except KeyError:
            print(f"  ✗ {skill_name}: 未找到")
    
    # 扫描目录中的 Python 文件
    print("\n" + "=" * 60)
    print("扫描 skills 目录中的 Python 文件:")
    print("=" * 60)
    
    py_files = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                full_path = os.path.join(root, file)
                py_files.append(full_path)
                
                # 检查是否有 SKILL 变量
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        has_skill = "SKILL = {" in content or "SKILL={" in content
                        print(f"  {file}: {'✓ 有 SKILL 变量' if has_skill else '✗ 无 SKILL 变量'}")
                except Exception as e:
                    print(f"  {file}: 读取错误 - {e}")
    
    print(f"\n总共找到 {len(py_files)} 个 Python 文件")
    
    # 检查 SKILL.md 文件
    print("\n" + "=" * 60)
    print("扫描 SKILL.md 文件:")
    print("=" * 60)
    
    md_files = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        if "SKILL.md" in files:
            skill_name = os.path.basename(root)
            md_files.append((skill_name, os.path.join(root, "SKILL.md")))
            print(f"  ✓ {skill_name}/SKILL.md")
    
    print(f"\n总共找到 {len(md_files)} 个 SKILL.md 文件")
    
    return len(skills)

if __name__ == "__main__":
    count = test_skill_loading()
    sys.exit(0 if count > 0 else 1)
