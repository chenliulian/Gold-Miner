# 构建中间聚合表

## 名称
build_adgroup_data

## 描述
基于 dwd 明细表按天聚合，构建 adgroup 维度的中间聚合表，包含展示/点击/下载/转化等核心指标。

## 源表
- 主表: `mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi`
- 分区字段: `dh` (格式: YYYYMMDDHH，如 '2026030100')

## 关键字段
- ad_group_id: 广告组ID
- cost_type: 计费类型
- ad_package_name: 广告包名
- app_id: 应用ID
- national_id: 国家ID
- show_label: 展现标签
- click_label: 点击标签
- download_label: 下载标签
- convert_label: 转化标签
- ctr: 预估CTR
- cost: 成本

## 参数
- start_date: 开始日期 (格式: YYYYMMDD)
- end_date: 结束日期 (格式: YYYYMMDD)
- output_table: 输出表名 (可选，默认: tmp_adgroup_xxx)

## 输出
在 ODPS 创建临时表，包含按日期、广告组维度聚合的展示数、点击数、下载数、转化数、成本等指标。

## 使用场景
- 需要进行 CTR/CVR 模型偏差分析时
- 需要按广告组维度汇总统计数据时
- 后续可接 calc_summary_stats、analyze_ctr_pcoc 等技能
