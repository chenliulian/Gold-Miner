# CVR 模型偏差分析

## 名称
analyze_cvr_pcoc

## 描述
分析 CVR 模型的预测偏差 (PCOC = pCVR / CVR)，支持 cpi/ocpc/ocpi 等转化类型。

## 参数
- start_date: 开始日期 (格式: YYYYMMDD)
- end_date: 结束日期 (格式: YYYYMMDD)
- adgroup_id: 广告组ID (可选)
- conv_type: 转化类型 (可选: cpi, ocpc, ocpi)

## 计算逻辑
- pcvr = SUM(conv_rate) / show_cnt
- cvr = conv_cnt / clk_cnt
- pcoc = pcvr / cvr

## 输出字段
- dt: 日期
- show_cnt: 展现数
- clk_cnt: 点击数
- conv_cnt: 转化数
- pcvr_sum: pCVR 求和
- cvr: 实际 CVR
- pcvr: 预估 CVR
- pcoc: CVR 偏差 (1.0 表示准确)

## 使用场景
- 评估 CVR 模型预估准确性
- 区分不同转化类型的偏差
- 优化转化出价
