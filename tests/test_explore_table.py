#!/usr/bin/env python3
"""
测试 explore_table skill 读取 com_ads.ads_tracker_ad_cpc_cost_di 表
"""
import os
import sys
from pathlib import Path

# 添加 src 到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "skills"))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入 explore_table skill
from explore_table.explore_table import run

def test_explore_table():
    """测试 explore_table skill"""
    print("=" * 60)
    print("测试 explore_table skill")
    print("=" * 60)
    
    table_name = "com_ads.ads_tracker_ad_cpc_cost_di"
    
    print(f"\n正在探索表: {table_name}")
    print("-" * 60)
    
    result = run(
        table_name=table_name,
        project="com_ads",
        sample_rows=3,
        sample_date="20220411",  # 使用测试时找到的有效分区
        generate_knowledge=False,  # 不生成知识文件
    )
    
    print("\n" + "=" * 60)
    print("探索结果:")
    print("=" * 60)
    
    print(f"\n表名: {result['table_name']}")
    print(f"项目: {result['project']}")
    
    if result.get('error'):
        print(f"\n❌ 错误: {result['error']}")
    else:
        print(f"\n✅ 表结构:")
        print(f"  - 总列数: {result['structure'].get('total_columns', 0)}")
        print(f"  - 总分区数: {result['structure'].get('total_partitions', 0)}")
        
        print(f"\n✅ 列信息 (前10个):")
        for col in result['columns'][:10]:
            sample = col.get('sample', '')
            sample_str = f" (示例: {sample[:30]}...)" if sample else ""
            print(f"  - {col['name']}: {col['type']}{sample_str}")
        
        if result['partitions']:
            print(f"\n✅ 分区信息:")
            for part in result['partitions']:
                print(f"  - {part['name']}: {part['type']}")
        
        if result.get('sample_data'):
            print(f"\n✅ 样本数据:")
            print(f"  列: {result['sample_data']['columns'][:5]}...")
            print(f"  行数: {len(result['sample_data']['rows'])}")
        
        if result.get('business_notes'):
            print(f"\n✅ 业务备注:")
            for note in result['business_notes']:
                print(f"  - {note}")
    
    return result

if __name__ == "__main__":
    test_explore_table()
