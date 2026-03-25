# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice
**Areas**: frontend | backend | infra | tests | docs | config | odps

---

**Logged**: 2026-03-20T17:51:23
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-20T17:51:23.563430

相关 SQL:
```sql
WITH mp AS (
  SELECT MAX_PT('mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi') AS max_dh
), params AS (
  SELECT
    CONCAT(
      TO_CHAR(
        DATEADD(TO_DATE(SUBSTR(max_dh,1,8),'yyyymmdd'), -6, 'dd'),
        'yyyymmdd'
      ),
      '00'
    ) AS start_dh,
    CONCAT(SUBSTR(max_dh,1,8), '23') AS end_dh
  FROM mp
)
SELECT
  SUBSTR(t.dh,1,8) AS dt,
  CAST(t.cost_type AS STRING) AS cost_type,
  ROUND(SUM(t.billing_actual_deduction_price)/1e5, 2) AS cost_usd
FROM mi_ads_dmp.dwd_ew_ads_show_r
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 
## [LRN-20260325-071] knowledge_gap

**Logged**: 2026-03-25T10:31:30
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-25T10:31:30.586673

相关 SQL:
```sql
WITH base AS (
  SELECT
    SUBSTR(dh, 1, 8) AS dt,
    billing_actual_deduction_price,
    show_label,
    dld_label,
    conv_label_apply_loan
  FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
  WHERE dh >= '2026031900' AND dh <= '2026032323'
    AND ad_group_id = '80554'
)
SELECT
  CASE WHEN dt IS NULL THEN 'TOTAL' ELSE dt END AS dt,
  ROUND(SUM(billing_actual_deduction_price) / 1e5, 6) AS cost_usd,
  SUM(show_label) AS show_cnt,
  SUM(dld_label) AS dld_cnt,
  SUM(conv_label_apply_loan) A
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-763] knowledge_gap

**Logged**: 2026-03-25T14:52:30
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-25T14:52:30.255906

相关 SQL:
```sql
WITH conv AS (
  SELECT
    SUBSTR(dh,1,8) AS dt,
    COALESCE(event_type, 'NULL') AS event_type,
    SUM(pv) AS pv_sum,
    SUM(click_conv_pv) AS click_conv_pv_sum,
    COUNT(1) AS row_cnt,
    -- 便于核对：转化相关行通常 show/click 为0，但这里仍然带出来看是否有异常
    SUM(show_cnt) AS show_cnt_sum,
    SUM(click_cnt) AS click_cnt_sum,
    SUM(bill_should_cost) AS bill_should_cost_sum
  FROM com_cdm.dws_tracker_ad_cpc_cost_hi
  WHERE dh >= '2026031900' AND dh <= '2026032323'
    AND ad_group_id = '80554'
  GROUP BY SUBST
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-505] correction

**Logged**: 2026-03-25T15:51:29
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325075126615gemquikco
ODPS-0130071:[12,9] Semanti...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325075126615gemquikco
ODPS-0130071:[12,9] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[6,9] Semantic analysis exception - column recall_cnt cannot be resolved
ODPS-0130071:[7,9] Semantic analysis exception - column filter_cnt cannot be resolved
ODPS-0130071:[8,9] Semantic analysis exception - column rank_cnt cannot be resolved
ODPS-0130071:[9,9] Semantic analysis exception - column resp_cnt cannot be resolved
ODPS-0130071:[21,9]
上下文: sql_execution
时间: 2026-03-25T15:51:29.648292

相关 SQL:
```sql
WITH
req AS (
  SELECT
    'k' AS k,
    COUNT(DISTINCT request_id) AS req_uv,
    SUM(recall_cnt) AS recall_cnt,
    SUM(filter_cnt) AS filter_cnt,
    SUM(rank_cnt) AS rank_cnt,
    SUM(resp_cnt) AS resp_cnt
  FROM ads_strategy.dwd_ew_request_sample_hi
  WHERE dh BETWEEN '2026032000' AND '2026032023'
    AND ad_group_id = '80554'
),
compete AS (
  SELECT
    'k' AS k,
    SUM(resp_cnt) AS engine_resp_cnt,
    SUM(win_cnt) AS win_cnt
  FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
  WHERE d
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-882] correction

**Logged**: 2026-03-25T15:52:08
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325075205533gzlhrqbb4r1
ODPS-0130071:[15,9] Seman...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325075205533gzlhrqbb4r1
ODPS-0130071:[15,9] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[6,5] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[7,5] Semantic analysis exception - column recall_cnt cannot be resolved
ODPS-0130071:[8,5] Semantic analysis exception - column filter_cnt cannot be resolved
ODPS-0130071:[9,5] Semantic analysis exception - column rank_cnt cannot be resolved
ODPS-0130071:[
上下文: sql_execution
时间: 2026-03-25T15:52:08.221031

相关 SQL:
```sql
SELECT *
FROM (
  SELECT
    'req_sample' AS src,
    request_id,
    ad_group_id,
    recall_cnt,
    filter_cnt,
    rank_cnt,
    resp_cnt,
    CAST(NULL AS BIGINT) AS win_cnt,
    dh
  FROM ads_strategy.dwd_ew_request_sample_hi
  WHERE dh = '2026032000'
    AND ad_group_id = '80554'
  LIMIT 5
) a
UNION ALL
SELECT *
FROM (
  SELECT
    'compe_suc' AS src,
    request_id,
    ad_group_id,
    CAST(NULL AS BIGINT) AS recall_cnt,
    CAST(NULL AS BIGINT) AS filter_cnt,
    CAST(NULL AS BIGINT) A
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-267] knowledge_gap

**Logged**: 2026-03-25T15:54:05
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-25T15:54:05.142806

相关 SQL:
```sql
WITH s AS (
  SELECT
    SUM(show_label) AS show_cnt,
    SUM(click_label) AS click_cnt,
    SUM(dld_label) AS dld_cnt,
    SUM(conv_label_active) AS conv_active_cnt,
    SUM(conv_label_register) AS conv_register_cnt,
    SUM(conv_label_pay) AS conv_pay_cnt,
    SUM(billing_actual_deduction_price) / 1e5 AS cost_usd
  FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
  WHERE dh BETWEEN '2026032000' AND '2026032023'
    AND ad_group_id = '80554'
)
SELECT
  show_cnt,
  click_cnt,
  ROUND(click_cn
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-976] correction

**Logged**: 2026-03-25T15:55:16
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325075513974gkgfxa45aio2
ODPS-0130071:[7,14] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325075513974gkgfxa45aio2
ODPS-0130071:[7,14] Semantic analysis exception - column launch_group_id cannot be resolved

上下文: sql_execution
时间: 2026-03-25T15:55:16.693323

相关 SQL:
```sql
WITH
-- 1) adgroup -> creative 映射（request_sample 只能用 ad_creative_id 过滤）
creative AS (
  SELECT DISTINCT CAST(id AS STRING) AS ad_creative_id
  FROM com_cdm.dim_creativity_dd
  WHERE dt = MAX_PT('com_cdm.dim_creativity_dd')
    AND CAST(launch_group_id AS STRING) = '80554'
),
-- 2) request_sample：按 stage 还原“召回/进rank/响应/cnt_limit”漏斗（无 ad_group_id、无 recall_cnt 等字段）
req_sample AS (
  SELECT
    'k' AS k,
    COUNT(DISTINCT rs.request_id) AS recall_req_cnt,
    COUNT(DISTINCT CASE WHEN rs.stage IN ('
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-761] correction

**Logged**: 2026-03-25T15:56:01
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: SQL validation failed: Potential SQL injection patterns detected: ['Block commen...

### Details
错误类型: unknown
错误信息: SQL validation failed: Potential SQL injection patterns detected: ['Block comment injection']
上下文: sql_validation
时间: 2026-03-25T15:56:01.285794

相关 SQL:
```sql
WITH
-- 1) adgroup -> creative 映射（dim_creativity_dd 正确字段是 ad_group_id）
creative AS (
  SELECT /*+ MAPJOIN */ DISTINCT CAST(id AS STRING) AS ad_creative_id
  FROM com_cdm.dim_creativity_dd
  WHERE dt = MAX_PT('com_cdm.dim_creativity_dd')
    AND ad_group_id = '80554'
),
-- 2) request_sample：按 stage 还原采样漏斗（该表无 ad_group_id/recall_cnt 等字段）
req_sample AS (
  SELECT
    'k' AS k,
    COUNT(DISTINCT rs.request_id) AS recall_req_cnt,
    COUNT(DISTINCT CASE WHEN rs.stage IN ('RESP','cnt_limit') THEN rs.
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-340] correction

**Logged**: 2026-03-25T16:56:36
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: SQL validation failed: Potential SQL injection patterns detected: ['UNION inject...

### Details
错误类型: unknown
错误信息: SQL validation failed: Potential SQL injection patterns detected: ['UNION injection']
上下文: sql_validation
时间: 2026-03-25T16:56:36.340901

相关 SQL:
```sql
WITH
recall AS (
  SELECT
    SUBSTR(dh,1,8) AS dt,
    CAST(ad_group_id AS BIGINT) AS ad_group_id,
    SUM(recall) AS recall_cnt,
    SUM(resp) AS recall_resp_cnt,
    SUM(show_cnt) AS recall_show_cnt,
    SUM(click_cnt) AS recall_click_cnt
  FROM com_ads.ads_creativity_filter_hi
  WHERE dh BETWEEN '2026032000' AND '2026032023'
    AND CAST(ad_group_id AS STRING) = '80554'
    AND is_offline_ad = 0
  GROUP BY SUBSTR(dh,1,8), CAST(ad_group_id AS BIGINT)
),
engine AS (
  SELECT
    SUBSTR(dh,1,8)
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-234] correction

**Logged**: 2026-03-25T16:57:12
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 2026032508571051gs4my0wefn9
ODPS-0130071:[77,1] Semant...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 2026032508571051gs4my0wefn9
ODPS-0130071:[77,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-25T16:57:12.732986

相关 SQL:
```sql
WITH
recall AS (
  SELECT
    SUBSTR(dh,1,8) AS dt,
    CAST(ad_group_id AS BIGINT) AS ad_group_id,
    SUM(recall) AS recall_cnt,
    SUM(resp) AS recall_resp_cnt,
    SUM(show_cnt) AS recall_show_cnt,
    SUM(click_cnt) AS recall_click_cnt
  FROM com_ads.ads_creativity_filter_hi
  WHERE dh BETWEEN '2026032000' AND '2026032023'
    AND CAST(ad_group_id AS STRING) = '80554'
    AND is_offline_ad = 0
  GROUP BY SUBSTR(dh,1,8), CAST(ad_group_id AS BIGINT)
),
engine AS (
  SELECT
    SUBSTR(dh,1,8)
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-026] correction

**Logged**: 2026-03-25T17:44:34
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325094431829ga17gidffn9
ODPS-0130071:[56,1] Seman...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325094431829ga17gidffn9
ODPS-0130071:[56,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-25T17:44:34.508294

相关 SQL:
```sql
WITH params AS (
  SELECT SUBSTR(MAX_PT('mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi'), 1, 8) AS dt
),
show_agg AS (
  SELECT
    dh,
    code_seat_type,
    is_offline_ad,
    country_zh AS country_name,
    SUM(show_label) AS show_cnt,
    SUM(click_label) AS click_cnt,
    SUM(dld_label) AS dld_cnt,
    SUM(conv_label_apply_loan) AS apply_loan_cnt,
    SUM(billing_actual_deduction_price) / 1e5 AS cost_usd,
    SUM(CASE WHEN click_label = 1 THEN cvr ELSE 0 END) AS pcvr_sum
  FROM mi_ads_dmp
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---
