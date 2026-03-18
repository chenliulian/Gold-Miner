#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'skills')
from dotenv import load_dotenv
load_dotenv()
from explore_table.explore_table import run

# 更新正确的表名
table_name = "mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi"
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

if 'knowledge_generation' in result:
    kg = result['knowledge_generation']
    print(f"\n知识文件更新:")
    print(f"  成功: {kg.get('success')}")
    print(f"  消息: {kg.get('message')}")
    if 'details' in kg:
        print(f"  详情: {kg.get('details')}")
