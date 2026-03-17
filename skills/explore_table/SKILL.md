# 表探索技能

## 名称
explore_table

## 描述
探索新表的数据结构和业务含义，分析字段类型、分区、样本数据，并可自动生成 Skill 文件帮助后续理解。

## 功能
1. **获取表结构**: 使用 `DESC <table>` 获取表的列信息（字段名、类型）
2. **获取分区信息**: 自动识别分区字段
3. **样本数据**: 查询表的部分数据，了解字段的实际值
4. **业务分析**: 智能识别 ID 字段、标签字段、计费字段、时间字段等
5. **生成 Skill**: 根据探索结果自动生成 Skill 文件，方便后续使用

## 参数
- table_name: 表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)
- project: 项目名 (默认: mi_ads_dmp)
- sample_rows: 采样行数 (默认: 5)
- sample_date: 采样日期 (默认: 20260314)

## 返回值
- table_name: 完整表名
- project: 项目名
- structure: 结构信息 (列数、分区数)
- columns: 字段列表 (name, type, sample)
- partitions: 分区字段列表
- business_notes: 业务备注 (识别的关键字段)
- sample_data: 样本数据

## 使用场景
- 用户提到新表名时，自动探索表结构
- 不确定字段含义时，查看样本数据
- 探索完成后自动生成 Skill 文件到 skills/maxcompute/table_xxx 目录

## 使用示例
```python
# 探索表结构（默认会自动生成 Skill）
result = run(
    table_name="mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi",
    project="mi_ads_dmp",
    sample_rows=3,
    sample_date="20260314",
    generate_skill=True  # 默认 True
)

# 如果不想生成 skill
result = run(
    table_name="mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi",
    generate_skill=False
)
)
```
