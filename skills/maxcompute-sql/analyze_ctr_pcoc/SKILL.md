# CTR 模型偏差分析

## 名称
analyze_ctr_pcoc

## 描述
分析 CTR 模型的预测偏差 (PCOC = pCTR / CTR)，用于评估模型预估准确性。

## 输入表
依赖 build_adgroup_data 生成的中间表，字段包括：
- show_num: 展现数 (SUM(show_label))
- clk_num: 点击数 (SUM(click_label))
- clk_cnt: 点击数 (COUNT DISTINCT)
- pctr_raw_sum: 原始 pCTR 求和 (SUM(ctr_raw))
- pctr_sum: pCTR 求和 (SUM(ctr))
- ctr: 实际 CTR = clk_num / show_num
- pctr_raw: 原始预估 CTR = pctr_raw_sum / show_num
- pctr: 预估 CTR = pctr_sum / show_num

## 参数
- input_table: 输入表名 (build_adgroup_data 输出的表)
- level: 分析维度 (可选: adgroup, pkg_buz)
- cost_types: 计费类型 (可选，如 '6,7')

## 计算逻辑
- pcoc = pctr / ctr (pCTR / 实际CTR)
- pcoc_raw = pctr_raw / ctr
- abs_error = |pcoc - 1| (绝对偏差)
- abs_error_raw = |pcoc_raw - 1|

## 输出字段
- dt: 日期
- ad_group_id / ad_package_name: 广告维度
- show_num: 展现数
- clk_num: 点击数
- pctr_raw_sum: 原始pCTR求和
- pctr_sum: pCTR求和
- ctr: 实际 CTR
- pctr_raw: 原始预估CTR
- pctr: 预估CTR
- pcoc_raw: 原始PCOC
- pcoc: PCOC (1.0=准确, >1=高估, <1=低估)
- abs_error_raw: 原始绝对偏差
- abs_error: 绝对偏差

## 使用场景
- 评估模型预估准确性
- 识别高估或低估的日期/广告组
- 优化出价策略
