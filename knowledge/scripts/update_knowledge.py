#!/usr/bin/env python3
"""
更新指定表的 knowledge 文件
"""
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'skills')

from dotenv import load_dotenv
load_dotenv()

from explore_table.explore_table import run

def main():
    table_name = "ads_strategy.dwd_ads_launch_info_dt"
    print(f"更新表: {table_name}")
    print("-" * 60)

    result = run(
        table_name=table_name,
        sample_rows=5,
        sample_date="20260317",
        generate_knowledge=True,
    )

    print(f"\n探索结果:")
    print(f"  表名: {result['table_name']}")
    print(f"  列数: {result['structure'].get('total_columns', 0)}")
    print(f"  分区数: {result['structure'].get('total_partitions', 0)}")

    # 检查字段信息
    columns_with_comment = sum(1 for c in result['columns'] if c.get('comment'))
    print(f"  有注释的字段: {columns_with_comment}/{len(result['columns'])}")

    # 显示字段信息
    print("\n字段信息:")
    for col in result['columns']:
        comment = col.get('comment', '')
        print(f"  - {col['name']}: {comment[:50] if comment else '(无注释)'}")

    # 知识文件生成结果
    if 'knowledge_generation' in result:
        kg = result['knowledge_generation']
        print(f"\n知识文件更新:")
        print(f"  成功: {kg.get('success')}")
        print(f"  消息: {kg.get('message')}")
        if 'details' in kg:
            print(f"  详情: {kg['details']}")

if __name__ == "__main__":
    main()
