# 构建中间聚合表

## 名称
build_adgroup_data

## 描述
基于 dwd 明细表按天聚合，构建 adgroup 维度的中间聚合表，包含展示/点击/下载/转化等核心指标。

## 源表
- 主表: `mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi`
- 分区字段: `dh` (格式: YYYYMMDDHH，如 '2026030100')

## 关键字段 (源表字段)
- ad_group_id: 广告组ID
- ad_plan_id: 广告计划ID
- advertiser_id: 广告主ID
- cost_type: 计费类型
- ad_package_name: 广告包名
- app_id: 应用ID
- national_id: 国家ID (对应 mcc/country_zh)
- show_label: 展现标签 (1-曝光，0-非曝光)
- click_label: 点击标签 (1-点击表，0-非点击表)
- dld_label: 下载标签 (1-下载表，0-非下载表)
- conv_label_active: 激活转化label
- conv_label_retain: 次留转化label
- conv_label_register: 注册转化label
- conv_label_first_pay: 首次付费转化label
- conv_label_pay: 付费转化label
- conv_label_apply_loan: 金融申贷转化label
- conv_label_issue_loan: 金融放款转化label
- ctr: 预估CTR
- cvr: 预估CVR
- billing_actual_deduction_price: 实际扣费 (单位: 微美元, 需要除以 1e5 得到美元)
- ecpm: eCPM (单位: 微美元, 需要除以 1e5 得到美元)
- ecpm_raw: 原始eCPM (单位: 微美元, 需要除以 1e5 得到美元)
- first_price: 出价
- transform_target_cn: 转化目标

## 参数
- start_date: 开始日期 (格式: YYYYMMDD)
- end_date: 结束日期 (格式: YYYYMMDD)
- output_table: 输出表名 (可选，默认: adgroup_show_clk_conv_data)

## 输出
在 ODPS 创建临时表，包含按日期、广告组维度聚合的展示数、点击数、下载数、成本等指标。

## 使用场景
- 需要进行 CTR/CVR 模型偏差分析时
- 需要按广告组维度汇总统计数据时
- 后续可接 calc_summary_stats、analyze_ctr_pcoc 等技能
