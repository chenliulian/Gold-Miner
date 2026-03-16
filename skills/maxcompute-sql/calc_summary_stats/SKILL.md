# 汇总统计

## 名称
calc_summary_stats

## 描述
计算汇总指标，如成本/CTR/CVR/eCPM 等。

## 参数
- input_table: 输入表名（中间聚合表）
- output_table: 输出表名 (可选)

## 输出字段
- cost: 总成本
- show_cnt: 总展现
- clk_cnt: 总点击
- conv_cnt: 总转化
- ctr: CTR = clk_cnt / show_cnt
- cvr: CVR = conv_cnt / clk_cnt
- ecpm: eCPM = cost / show_cnt * 1000

## 使用场景
- 数据分析报告
- 指标汇总
