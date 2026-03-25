# 汇总统计

## 名称
calc_summary_stats

## 描述
计算汇总指标，如成本/CTR/CVR/eCPM 等。

## 输入表
依赖 build_adgroup_data 生成的中间表，字段包括：
- show_num: 展现数 (SUM(show_label))
- clk_num: 点击数 (SUM(click_label))
- clk_cnt: 点击去重数 (COUNT DISTINCT)
- dld_num: 下载数 (SUM(dld_label))
- conv_num: 转化数
- pctr_sum: pCTR 求和
- pcvr_sum: pCVR 求和
- cost_sum: 成本 (SUM(消耗字段) / 1e5, 单位: 美元)
- ecpm_sum: eCPM (SUM(ecpm) / 1e5, 单位: 美元)

## 参数
- input_table: 输入表名 (build_adgroup_data 输出的表)
- output_table: 输出表名 (可选)

## 计算逻辑
- ctr = clk_num / show_num
- cvr = conv_num / clk_num (或 dld_num)
- ecpm = cost_sum / show_num * 1000

## 输出字段
- dt: 日期
- cost_sum: 总成本
- show_num: 总展现
- clk_num: 总点击
- clk_cnt: 点击去重数
- dld_num: 总下载
- conv_num: 总转化
- pctr_sum: pCTR求和
- pcvr_sum: pCVR求和
- ctr: CTR = clk_num / show_num
- cvr: CVR = conv_num / clk_num
- ecpm: eCPM = cost_sum / show_num * 1000

## 使用场景
- 数据分析报告
- 指标汇总
