# CTR 模型偏差分析

## 名称
analyze_ctr_pcoc

## 描述
分析 CTR 模型的预测偏差 (PCOC = pCTR / CTR)，用于评估模型预估准确性。

## 参数
- start_date: 开始日期 (格式: YYYYMMDD)
- end_date: 结束日期 (格式: YYYYMMDD)
- adgroup_id: 广告组ID (可选)
- pkg_buz: 广告包维度 (可选)

## 计算逻辑
- pctr = SUM(ctr) / show_cnt
- ctr = clk_cnt / show_cnt
- pcoc = pctr / ctr

## 输出字段
- dt: 日期
- show_cnt: 展现数
- clk_cnt: 点击数
- pctr_sum: pCTR 求和
- ctr: 实际 CTR
- pctr: 预估 CTR
- pcoc: CTR 偏差 (1.0 表示准确)
- pctr_minus_ctr: pCTR - CTR 差值

## 使用场景
- 评估模型预估准确性
- 识别高估或低估的日期/广告组
- 优化出价策略
