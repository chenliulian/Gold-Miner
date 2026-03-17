# mi_ads_dmp.dwd_dld_loancvr_model_train_data_di 表探索

## 概述
- **表名**: mi_ads_dmp.dwd_dld_loancvr_model_train_data_di
- **项目**: mi_ads_dmp
- **列数**: 306
- **分区数**: 1

## 分区字段
- **dt**: STRING


## 字段说明
- **label**: BIGINT (示例: 0)
- **label_active**: BIGINT (示例: 0)
- **label_register**: BIGINT (示例: 0)
- **gaid**: STRING (示例: b24a2bf0-bade-4950-b7ff-f27213c26b81)
- **request_id**: STRING (示例: 56c8f24d-5231-4240-8b63-e21ac5c4f3c0)
- **dld_ts**: BIGINT (示例: 1773241218498)
- **advertiser_id**: STRING (示例: 5499)
- **ad_plan_id**: STRING (示例: 26504)
- **ad_group_id**: STRING (示例: 58900)
- **ad_creative_id**: STRING (示例: 615162)
- **app_id**: STRING (示例: 250822boRRGtpZ)
- **code_seat_id**: STRING (示例: 250822NfjfUrGa)
- **cost_type**: STRING (示例: 6)
- **promotion_type**: STRING (示例: None)
- **operator_type**: STRING (示例: None)
- **net_connect_type**: STRING (示例: None)
- **app_version**: STRING (示例: 1.0.1.2)
- **sdk_version**: STRING (示例: 3.5.0.3)
- **device_type**: STRING (示例: None)
- **brand**: STRING (示例: Itel)
- **model**: STRING (示例: itel A663LC)
- **maker**: STRING (示例: ITEL)
- **os_type**: STRING (示例: 1)
- **os_version**: STRING (示例: 13)
- **ip_address**: STRING (示例: None)
- **code_seat_type**: STRING (示例: 2)
- **adv_seat_type**: STRING (示例: pageBottom)
- **national_id**: STRING (示例: 30178)
- **state_id**: STRING
- **city_id**: STRING


## 业务备注
- 分区字段: dt (STRING)
- ID字段: request_id, advertiser_id, ad_plan_id, ad_group_id, ad_creative_id, app_id, code_seat_id, national_id, state_id, city_id, ssp_id, page_id, material_id, creativity_style_id
- 标签字段: label, label_active, label_register
- 计费/指标字段: cost_type, price, a_ctr_1d, a_ctr_3d, a_ctr_7d, a_ctr_15d, a_ctr_30d, a_cvr_1d, a_cvr_3d, a_cvr_7d, a_cvr_15d, a_cvr_30d, g_ctr_1d, g_ctr_3d, g_ctr_7d, g_ctr_15d, g_ctr_30d, g_cvr_1d, g_cvr_3d, g_cvr_7d, g_cvr_15d, g_cvr_30d, p_ctr_1d, p_ctr_3d, p_ctr_7d, p_ctr_15d, p_ctr_30d, p_cvr_1d, p_cvr_3d, p_cvr_7d, p_cvr_15d, p_cvr_30d, c_ctr_1d, c_ctr_3d, c_ctr_7d, c_ctr_15d, c_ctr_30d, c_cvr_1d, c_cvr_3d, c_cvr_7d, c_cvr_15d, c_cvr_30d, ca_ctr_1d, ca_ctr_3d, ca_ctr_7d, ca_ctr_15d, ca_ctr_30d, ca_cvr_1d, ca_cvr_3d, ca_cvr_7d, ca_cvr_15d, ca_cvr_30d, a_cvr_1d_bayes, a_cvr_3d_bayes, a_cvr_7d_bayes, a_cvr_15d_bayes, a_cvr_30d_bayes, g_cvr_1d_bayes, g_cvr_3d_bayes, g_cvr_7d_bayes, g_cvr_15d_bayes, g_cvr_30d_bayes, p_cvr_1d_bayes, p_cvr_3d_bayes, p_cvr_7d_bayes, p_cvr_15d_bayes, p_cvr_30d_bayes, c_cvr_1d_bayes, c_cvr_3d_bayes, c_cvr_7d_bayes, c_cvr_15d_bayes, c_cvr_30d_bayes, moblie_price, mob_price
- 时间字段: dld_ts, image_width, dt_sample, dt

## 使用示例
```sql
SELECT * FROM mi_ads_dmp.dwd_dld_loancvr_model_train_data_di
WHERE dh = '2026031400'
LIMIT 100;
```

## 生成时间
2026-03-17 20:16:00
