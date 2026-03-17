# com_cdm.dim_creativity_dd 表探索

## 概述
- **表名**: com_cdm.dim_creativity_dd
- **项目**: com_cdm
- **列数**: 47
- **分区数**: 1

## 分区字段
- **dt**: STRING


## 字段说明
- **id**: STRING (示例: 181370)
- **title**: STRING (示例: 广告_24_02_03_20:43:06_4_copy_11_copy_88_copy_7)
- **ad_group_id**: STRING (示例: 21345)
- **ad_group_title**: STRING (示例: Brick Master-国家限定-非商店_2)
- **ad_plan_id**: STRING (示例: 12153)
- **ad_plan_title**: STRING (示例: brick-master_0203)
- **advertiser_id**: STRING (示例: 3375)
- **account_name**: STRING (示例: 果石-funloop-01)
- **is_default**: INT (示例: 0)
- **site_id**: STRING (示例: 0)
- **style_type**: STRING (示例: 9:20)
- **status**: INT (示例: 0)
- **status_cn**: STRING (示例: 未定义)
- **open**: INT (示例: 2)
- **open_cn**: STRING (示例: 暂停)
- **show_limit**: BIGINT (示例: 0)
- **is_deleted**: INT (示例: 0)
- **creator**: STRING (示例: 3375)
- **gmt_create**: DATETIME (示例: 2024-02-03 20:51:45)
- **modifier**: STRING (示例: 3375)
- **gmt_modified**: DATETIME (示例: 2026-01-15 05:26:27)
- **package_name**: STRING (示例: com.casualgame.brick.master.free.game)
- **package_source**: STRING (示例: PS)
- **scale**: STRING (示例: 9:20)
- **status_v2**: STRING (示例: 11)
- **material_type**: STRING (示例: 2)
- **material_type_cn**: STRING (示例: 图片)
- **category_name**: STRING (示例: Role Playing)
- **material_id**: STRING (示例: 47608)
- **material_sub_type**: STRING (示例: 1)


## 业务备注
- 分区字段: dt (STRING)
- ID字段: id, ad_group_id, ad_plan_id, advertiser_id, site_id, material_id, audit_entity_id, origin_creativity_id
- 时间字段: start_time, end_time, dt

## 使用示例
```sql
SELECT * FROM com_cdm.dim_creativity_dd
WHERE dh = '2026031400'
LIMIT 100;
```

## 生成时间
2026-03-17 20:30:06
