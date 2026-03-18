# 表探索技能

## 名称
explore_table

## 描述
探索新表的数据结构和业务含义，分析字段类型、分区、样本数据，并可自动生成 Skill 文件帮助后续理解。

## 功能
1. **获取表结构**: 使用 ODPS SDK `get_table()` 方法获取表的列信息（字段名、类型、字段注释/业务含义）
2. **获取分区信息**: 自动识别分区字段
3. **样本数据**: 查询表的部分数据，了解字段的实际值
4. **业务分析**: 智能识别 ID 字段、标签字段、计费字段、时间字段等
5. **生成知识文件**: 根据探索结果自动生成/更新 knowledge/tables YAML 文件，补充字段业务含义

## 参数
- table_name: 表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)
- project: 项目名 (默认: mi_ads_dmp)
- sample_rows: 采样行数 (默认: 5)
- sample_date: 采样日期 (默认: 20260314)

## 返回值
- table_name: 完整表名
- project: 项目名
- structure: 结构信息 (列数、分区数)
- columns: 字段列表 (name, type, comment, sample)
  - comment: 从 ODPS 表结构获取的字段注释/业务含义
- partitions: 分区字段列表
- business_notes: 业务备注 (识别的关键字段)
- sample_data: 样本数据
- knowledge_generation: 知识文件生成结果 (包含更新的字段数、新增的字段数)

## 使用场景
- 用户提到新表名时，自动探索表结构
- 不确定字段含义时，查看样本数据和字段注释
- 探索完成后自动生成/更新知识文件到 knowledge/tables 目录，补充字段业务含义
- 定期检查并更新已有知识文件，确保字段描述完整

## 使用示例
```python
# 探索表结构（默认会自动生成/更新知识文件）
result = run(
    table_name="mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi",
    project="mi_ads_dmp",
    sample_rows=3,
    sample_date="20260314",
    generate_knowledge=True  # 默认 True
)

# 如果知识文件已存在，会自动更新缺失的字段描述
# 返回结果包含 knowledge_generation，显示更新的字段数

# 如果不想生成知识文件
result = run(
    table_name="mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi",
    generate_knowledge=False
)
```

## 技术实现
- 使用 PyODPS `get_table()` 方法获取表元数据（包含字段注释）
- 需要 ODPS Describe 权限才能读取表结构
- 知识文件路径：`knowledge/tables/{project}_{table_name}.yaml`
