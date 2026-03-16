# 基础统计

## 名称
basic_stats

## 描述
对查询结果进行基础统计分析，包括计数、求和、平均值、最大最小值等。

## 参数
- dataframe: DataFrame (可选，默认使用上次的查询结果)

## 输出
- count: 行数
- columns: 列名列表
- dtypes: 数据类型
- describe: 数值列的统计信息 (count, mean, std, min, 25%, 50%, 75%, max)
- null_count: 空值统计

## 使用场景
- 快速了解数据概况
- 数据验证
- 检查数据质量
