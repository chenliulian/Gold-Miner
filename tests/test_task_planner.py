#!/usr/bin/env python3
"""测试 task_planner skill"""

import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'skills/task_planner')

from task_planner import run

# 测试趋势分析
print("=" * 60)
print("测试1: 趋势分析")
print("=" * 60)
result = run(
    business_question="分析过去30天广告CTR的趋势变化，识别异常波动日期",
    tables=["mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi"],
    analysis_depth="standard",
    save_plan=False,
)
print(f"分析模式: {result['analysis_pattern']}")
print(f"任务数量: {result['total_tasks']}")
print(f"执行顺序: {' -> '.join(result['execution_order'])}")
print("\n任务列表:")
for task in result['tasks']:
    print(f"  - {task['task_id']}: {task['name']} ({task['task_type']})")

# 测试对比分析
print("\n" + "=" * 60)
print("测试2: 对比分析")
print("=" * 60)
result = run(
    business_question="对比不同创意类型的转化率和成本差异",
    tables=["mi_ads_dmp.dwd_dld_loancvr_model_train_data_di"],
    analysis_depth="deep",
    save_plan=False,
)
print(f"分析模式: {result['analysis_pattern']}")
print(f"任务数量: {result['total_tasks']}")

# 测试归因分析
print("\n" + "=" * 60)
print("测试3: 归因分析")
print("=" * 60)
result = run(
    business_question="分析3月15日CTR突然下降的原因",
    tables=["mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi"],
    analysis_depth="quick",
    save_plan=False,
)
print(f"分析模式: {result['analysis_pattern']}")
print(f"任务数量: {result['total_tasks']}")

print("\n✅ 所有测试通过!")
