#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'skills')
from dotenv import load_dotenv
load_dotenv()
from explore_table.explore_table import run

result = run(
    table_name="com_ads.ads_tracker_ad_cpc_cost_di",
    sample_rows=5,
    sample_date="20260317",
    generate_knowledge=True,
)

print(f"表名: {result['table_name']}")
print(f"列数: {result['structure'].get('total_columns', 0)}")
if 'knowledge_generation' in result:
    kg = result['knowledge_generation']
    print(f"知识文件: {kg.get('message')}")
    print(f"详情: {kg.get('details')}")
