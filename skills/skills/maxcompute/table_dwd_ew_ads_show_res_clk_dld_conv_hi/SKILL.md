# mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 表探索

## 概述
- **表名**: mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
- **项目**: mi_ads_dmp
- **列数**: 116
- **分区数**: 1

## 分区字段
- **dh**: STRING


## 字段说明
- **request_id**: STRING
- **trigger_id**: STRING
- **show_id**: STRING
- **is_inapp_ad**: STRING
- **gaid**: STRING
- **app_id**: STRING
- **code_seat_id**: STRING
- **code_seat_type**: STRING
- **type**: INT
- **brand**: STRING
- **model**: STRING
- **maker**: STRING
- **os_type**: STRING
- **os_version**: STRING
- **language**: STRING
- **net_connect_type**: STRING
- **is_default_ad**: BIGINT
- **operator_type**: INT
- **ip_address**: STRING
- **screen_width**: INT
- **screen_height**: INT
- **screen_density**: INT
- **national_id**: STRING
- **state_id**: STRING
- **city_id**: STRING
- **ad_creative_id**: STRING
- **ad_group_id**: STRING
- **ad_plan_id**: STRING
- **advertiser_id**: STRING
- **package_name**: STRING


## 业务备注
- 分区字段: dh (STRING)
- ID字段: request_id, trigger_id, show_id, app_id, code_seat_id, national_id, state_id, city_id, ad_creative_id, ad_group_id, ad_plan_id, advertiser_id, page_id, ssp_id, click_id, product_id
- 标签字段: click_label, dld_label, conv_label_active, conv_label_retain, conv_label_register, conv_label_first_pay, conv_label_pay, conv_label_apply_loan, conv_label_issue_loan, show_label
- 计费/指标字段: first_price, st_ecpm, op_ecpm, ee_ecpm, cul_ecpm, billing_actual_deduction_price, ctr_model_name, cvr_model_name, ctr, cvr, ctr_raw, cvr_raw, ecpm, ecpm_raw, cost, cost_type, second_price, price, price_v2
- 时间字段: screen_width, show_ts, resp_ts, show_dh, resp_dh, click_ts, image_width, dld_ts, conv_ts_active, conv_ts_retain, conv_ts_register, conv_ts_first_pay, conv_ts_pay, conv_ts_apply_loan, conv_ts_issue_loan, show_log_dh, click_log_dh, dld_log_dh, conv_log_dh, dh

## 使用示例
```sql
SELECT * FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh = '2026031400'
LIMIT 100;
```

## 生成时间
2026-03-16 19:36:09
