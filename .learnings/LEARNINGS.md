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

## [LRN-20260325-191] correction

**Logged**: 2026-03-25T20:36:32
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325123630135ga4gyks9aio2
ODPS-0130071:[26,14] Sem...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325123630135ga4gyks9aio2
ODPS-0130071:[26,14] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[21,10] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[21,10] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[22,30] Semantic analysis exception - column resp_cnt cannot be resolved
ODPS-0130071:[22,48] Semantic analysis exception - column request_id cannot be resolved
ODP
上下文: sql_execution
时间: 2026-03-25T20:36:32.915896

相关 SQL:
```sql
WITH
post_day AS (
  SELECT
    SUBSTR(dh,1,8) AS dt,
    CAST(ad_group_id AS BIGINT) AS ad_group_id,
    SUM(show_label) AS show_cnt,
    SUM(click_label) AS click_cnt,
    SUM(dld_label) AS dld_cnt,
    SUM(conv_label_active) AS conv_active_cnt,
    SUM(conv_label_register) AS conv_register_cnt,
    SUM(conv_label_pay) AS conv_pay_cnt,
    SUM(billing_actual_deduction_price)/1e5 AS cost_usd
  FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
  WHERE dh BETWEEN '2026032200' AND '2026032223'
 
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260325-635] knowledge_gap

**Logged**: 2026-03-25T23:50:42
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-25T23:50:42.160864

相关 SQL:
```sql
SELECT
  SUBSTR(dh, 1, 8) AS dt,
  ROUND(SUM(bill_should_cost), 4) AS cost_usd,
  SUM(start_dld_cnt) AS download_cnt,
  SUM(CASE WHEN transform_target_cn = '申贷' THEN click_conv_pv ELSE 0 END) AS apply_loan_conv_cnt,
  ROUND(
    SUM(CASE WHEN transform_target_cn = '申贷' THEN click_conv_pv ELSE 0 END) * 1.0 / NULLIF(SUM(start_dld_cnt), 0),
    6
  ) AS download_to_apply_rate,
  ROUND(
    SUM(bill_should_cost) / NULLIF(SUM(CASE WHEN transform_target_cn = '申贷' THEN click_conv_pv ELSE 0 END), 0),
  
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260326-134] correction

**Logged**: 2026-03-26T11:15:15
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: SQL validation failed: Statement type 'set' is not allowed. Only SELECT, WITH, D...

### Details
错误类型: unknown
错误信息: SQL validation failed: Statement type 'set' is not allowed. Only SELECT, WITH, DESC, SHOW are permitted
上下文: sql_validation
时间: 2026-03-26T11:15:15.714795

相关 SQL:
```sql
SET odps.sql.allow.cartesian.product=true;
WITH show_funnel AS (
    SELECT 
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(dld_label) as dld_cnt,
        SUM(conv_label_active) as conv_cnt,
        SUM(conv_label_register) as conv_register_cnt,
        SUM(conv_label_pay) as conv_pay_cnt,
        SUM(billing_actual_deduction_price) / 1e5 as total_cost
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '2026032300' AND '202603232
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260326-047] knowledge_gap

**Logged**: 2026-03-26T11:30:22
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-26T11:30:22.659301

相关 SQL:
```sql
SELECT 
    SUM(show_label) as show_cnt,
    SUM(click_label) as click_cnt,
    SUM(dld_label) as dld_cnt,
    SUM(conv_label_active) as conv_cnt,
    SUM(conv_label_register) as conv_register_cnt,
    SUM(conv_label_pay) as conv_pay_cnt,
    SUM(billing_actual_deduction_price) / 1e5 as total_cost_usd,
    ROUND(SUM(click_label) * 100.0 / NULLIF(SUM(show_label), 0), 2) as ctr_pct,
    ROUND(SUM(dld_label) * 100.0 / NULLIF(SUM(click_label), 0), 2) as click_to_dld_rate_pct,
    ROUND(SUM(conv_labe
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260326-836] knowledge_gap

**Logged**: 2026-03-26T11:39:01
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-26T11:39:01.116212

相关 SQL:
```sql
SELECT 
    e.rank_req_cnt,
    e.resp_req_cnt,
    (e.rank_req_cnt - e.resp_req_cnt) as cutoff_cnt,
    ROUND(e.resp_req_cnt * 100.0 / NULLIF(e.rank_req_cnt, 0), 2) as win_rate_pct,
    s.show_cnt,
    ROUND(s.show_cnt * 100.0 / NULLIF(e.resp_req_cnt, 0), 2) as resp_to_show_rate_pct,
    s.click_cnt,
    ROUND(s.click_cnt * 100.0 / NULLIF(s.show_cnt, 0), 2) as ctr_pct,
    s.dld_cnt,
    ROUND(s.dld_cnt * 100.0 / NULLIF(s.click_cnt, 0), 2) as dld_rate_pct,
    s.conv_cnt,
    ROUND(s.conv_cnt *
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260326-971] knowledge_gap

**Logged**: 2026-03-26T11:52:59
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-26T11:52:59.508827

相关 SQL:
```sql
WITH show_funnel AS (
    SELECT 
        ad_group_id,
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(dld_label) as dld_cnt,
        SUM(conv_label_active) as conv_active_cnt,
        SUM(conv_label_register) as conv_register_cnt,
        SUM(conv_label_pay) as conv_pay_cnt,
        SUM(billing_actual_deduction_price) / 1e5 as total_cost_usd
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '2026032300' AND '2026032323'
    AND 
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260326-012] knowledge_gap

**Logged**: 2026-03-26T14:20:28
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-26T14:20:28.926199

相关 SQL:
```sql
SELECT 
    e.rank_req_cnt,
    e.resp_req_cnt,
    (e.rank_req_cnt - e.resp_req_cnt) as cutoff_cnt,
    ROUND(e.resp_req_cnt * 100.0 / NULLIF(e.rank_req_cnt, 0), 2) as win_rate_pct,
    s.show_cnt,
    ROUND(s.show_cnt * 100.0 / NULLIF(e.resp_req_cnt, 0), 2) as resp_to_show_rate_pct,
    s.click_cnt,
    ROUND(s.click_cnt * 100.0 / NULLIF(s.show_cnt, 0), 2) as ctr_pct,
    s.dld_cnt,
    ROUND(s.dld_cnt * 100.0 / NULLIF(s.click_cnt, 0), 2) as click_to_dld_rate_pct,
    s.conv_cnt_active,
    RO
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260326-948] knowledge_gap

**Logged**: 2026-03-26T16:35:51
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-26T16:35:51.548116

相关 SQL:
```sql
SELECT 
    t2.business_line_nm,
    SUM(t1.show_label) AS show_cnt,
    SUM(t1.click_label) AS click_cnt,
    SUM(t1.dld_label) AS dld_cnt,
    SUM(t1.conv_label_active) AS conv_cnt_active,
    SUM(t1.billing_actual_deduction_price) / 1e5 AS total_cost_usd
FROM (
    SELECT show_id, show_label, click_label, dld_label, conv_label_active, 
           billing_actual_deduction_price, code_seat_id
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh >= '2026032300' AND dh <= '2026032
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 
- Fingerprint: 387f5e8a5c4e21e4

---

## [LRN-20260326-055] correction

**Logged**: 2026-03-26T17:04:00
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260326090357818g3jka5v9aio2
ODPS-0130071:[43,25] Sem...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260326090357818g3jka5v9aio2
ODPS-0130071:[43,25] Semantic analysis exception - expect equality expression (i.e., only use '=' and 'AND') for join condition without mapjoin hint, but get: (1 = 1)

上下文: sql_execution
时间: 2026-03-26T17:04:00.595071

相关 SQL:
```sql
WITH engine_funnel AS (
    SELECT 
        SUM(rank_req_cnt) as rank_req_cnt,
        SUM(resp_req_cnt) as resp_req_cnt
    FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
    WHERE dh BETWEEN '2026032400' AND '2026032423'
    AND id_type = 'ad_group_id'
    AND id_value = '65491'
),
show_funnel AS (
    SELECT 
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(dld_label) as dld_cnt,
        SUM(conv_label_active) as conv_active_cnt,
        SUM(conv_labe
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 
- Fingerprint: ea973aca5ae31a92

---

## [LRN-20260326-144] correction

**Logged**: 2026-03-26T17:04:27
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130252: InstanceId: 20260326090424730g8b1yqbb4r1
ODPS-0130252:[42,19] Cart...

### Details
错误类型: unknown
错误信息: ODPS-0130252: InstanceId: 20260326090424730g8b1yqbb4r1
ODPS-0130252:[42,19] Cartesian product is not allowed - cartesian product is not allowed without mapjoin

上下文: sql_execution
时间: 2026-03-26T17:04:27.445396

相关 SQL:
```sql
WITH engine_funnel AS (
    SELECT 
        SUM(rank_req_cnt) as rank_req_cnt,
        SUM(resp_req_cnt) as resp_req_cnt
    FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
    WHERE dh BETWEEN '2026032400' AND '2026032423'
    AND id_type = 'ad_group_id'
    AND id_value = '65491'
),
show_funnel AS (
    SELECT 
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(dld_label) as dld_cnt,
        SUM(conv_label_active) as conv_active_cnt,
        SUM(conv_labe
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 
- Fingerprint: 100f551b19fafbc3

---

## [LRN-20260326-670] best_practice

**Logged**: 2026-03-26T17:05:06
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS不支持CROSS JOIN和JOIN ON 1=1，需使用常量join_key进行等值JOIN

### Details
MaxCompute (ODPS) 不允许笛卡尔积操作，包括CROSS JOIN、逗号连接、JOIN ON 1=1。解决方案是在两个子查询中各添加一个常量字段如 1 as join_key，然后使用 ON s.join_key = e.join_key 进行等值JOIN。

### Suggested Action
在需要笛卡尔积的场景中，始终使用常量join_key方式替代

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cross_join, cartesian_product, join
- Fingerprint: b76d7621fd6fd821

---

## [LRN-20260326-038] best_practice

**Logged**: 2026-03-26T17:05:20
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS不支持CROSS JOIN和JOIN ON 1=1，需要使用常量join_key进行等值JOIN

### Details
在ODPS中合并两个聚合子查询（各返回1行）时，不能使用CROSS JOIN或JOIN ON 1=1。正确做法是在每个子查询中添加一个常量字段（如 1 as join_key），然后用等值JOIN（ON s.join_key = e.join_key）连接。

### Suggested Action
更新查询规则，添加ODPS笛卡尔积替代方案的说明

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cross-join, cartesian-product, join
- Fingerprint: b6022bc72c667284

---

## [LRN-20260326-770] best_practice

**Logged**: 2026-03-26T17:05:30
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 between subqueries but not between CTEs or tables directly. Use subquery inline views for cartesian product of single-row results.

### Details
When joining two single-row aggregation results in ODPS: CTE + JOIN ON 1=1 fails, comma join fails, but subquery inline views with JOIN ON 1=1 works. Also ads_strategy.dwd_ads_engine_compe_suc_req_hi may not have data for all ad_group_ids - the id_type and id_value fields need to match exactly.

### Suggested Action
Always use subquery inline views (not CTEs) when doing cartesian product joins in ODPS. Check if engine-side tables have data before relying on them.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cross_join, cartesian_product, engine_funnel
- Fingerprint: 9ccce23d8b545632

---

## [LRN-20260326-505] best_practice

**Logged**: 2026-03-26T17:05:40
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS不支持CROSS JOIN和JOIN ON 1=1，需要使用常量join_key进行等值JOIN来实现笛卡尔积

### Details
MaxCompute (ODPS) 不允许笛卡尔积操作，包括：1) CROSS JOIN 语法不支持；2) JOIN ON 1=1 会报错 expect equality expression；3) 隐式逗号连接 FROM a, b 也会报 cartesian product not allowed。解决方案：在两个子查询中各添加一个常量字段如 1 as join_key，然后使用 JOIN ON s.join_key = e.join_key 进行等值连接。

### Suggested Action
在需要笛卡尔积的场景中，始终使用常量join_key方式：SELECT 1 as join_key 然后 JOIN ON a.join_key = b.join_key

### Metadata
- Source: error
- Related Files: 
- Tags: ODPS, SQL, CROSS JOIN, cartesian product, join_key
- Fingerprint: 11fd8f31ec57ef49

---

## [LRN-20260326-535] best_practice

**Logged**: 2026-03-26T17:05:51
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 with subqueries (inline views) but not with CTEs or table references directly. Cartesian product workaround: use subqueries in FROM clause with JOIN ON 1=1.

### Details
When needing to join two single-row aggregation results in ODPS: 1) CTE + JOIN ON 1=1 fails with 'expect equality expression'. 2) Comma join (implicit cartesian) fails with 'cartesian product not allowed'. 3) Subquery inline views + JOIN ON 1=1 WORKS. The key is that both sides must be subqueries (not CTE references or table names).

### Suggested Action
Always use subquery inline views when doing cartesian joins of single-row results in ODPS.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cartesian-join, cross-join, sql-syntax
- Fingerprint: c638a0599a5674d3

---

## [LRN-20260326-966] best_practice

**Logged**: 2026-03-26T17:06:06
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 with subqueries but not with CTEs or plain tables. Use subquery inline views for cartesian product of single-row aggregations.

### Details
When joining two single-row aggregation results in ODPS: CTE + JOIN ON 1=1 fails, comma join fails, but subquery inline views + JOIN ON 1=1 works. Also, ads_strategy.dwd_ads_engine_compe_suc_req_hi may not have data for all ad_group_ids - the id_type/id_value filter may need verification.

### Suggested Action
Always use subquery inline views (not CTEs) when doing cartesian product joins in ODPS. When engine table returns NULL, note it in the report and suggest checking if the ad group has engine-side data.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cartesian-join, engine-funnel
- Fingerprint: 8798948ce718c92f

---

## [LRN-20260326-540] best_practice

**Logged**: 2026-03-26T17:06:21
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 with subqueries (inline views) but not with CTE references or plain tables for cartesian products

### Details
When joining two single-row aggregation results in ODPS: 1) CTE + JOIN ON 1=1 fails with 'expect equality expression'. 2) CTE + comma join fails with 'Cartesian product not allowed'. 3) Subquery inline views + JOIN ON 1=1 WORKS. The key is to use subqueries directly in the FROM clause, not CTE references.

### Suggested Action
Always use subquery inline views (not CTEs) when doing cartesian joins of single-row aggregations in ODPS

### Metadata
- Source: error
- Related Files: 
- Tags: odps, sql, cartesian-join, cross-join
- Fingerprint: ebcb6954e4cbb910

---

## [LRN-20260326-937] best_practice

**Logged**: 2026-03-26T17:06:53
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 between subqueries but not between CTEs or plain tables. Use subquery-based approach for cartesian joins of single-row aggregations.

### Details
When joining two single-row aggregation results in ODPS: CTE + JOIN ON 1=1 fails, CTE + comma join fails, but subquery + JOIN ON 1=1 works. Also, ads_strategy.dwd_ads_engine_compe_suc_req_hi may not have data for all ad_group_ids - need to check id_type and id_value fields.

### Suggested Action
Always use subquery approach for cartesian joins in ODPS. When engine funnel data is NULL, note it in the report and suggest checking if the table has data for the given ad_group_id.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cartesian_join, engine_funnel, ads_strategy
- Fingerprint: 22dc961ae6b58353

---

## [LRN-20260326-490] best_practice

**Logged**: 2026-03-26T17:07:15
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 with subqueries but not with CTEs or plain tables for cartesian products

### Details
When joining two single-row aggregation results in ODPS: 1) CTE + JOIN ON 1=1 fails with 'expect equality expression'. 2) Comma join (implicit cartesian) fails with 'Cartesian product is not allowed without mapjoin'. 3) Subquery + JOIN ON 1=1 WORKS. Solution: use inline subqueries instead of CTEs when doing cartesian joins.

### Suggested Action
Always use subquery-based JOIN ON 1=1 for single-row cartesian products in ODPS, not CTE-based joins.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cartesian-join, sql-syntax
- Fingerprint: 20294bc083f22271

---

## [LRN-20260326-227] best_practice

**Logged**: 2026-03-26T17:07:32
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 between subqueries but not between CTEs or plain tables. Use subquery-based approach for cartesian joins.

### Details
When joining two single-row aggregation results in ODPS: (1) CTE + JOIN ON 1=1 fails with 'expect equality expression'. (2) Comma join (FROM a, b) fails with 'Cartesian product not allowed'. (3) Subquery + JOIN ON 1=1 works successfully. The key is wrapping aggregations as inline subqueries rather than CTEs.

### Suggested Action
Always use subquery-based approach for cartesian joins in ODPS, not CTE-based.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, sql, cartesian-join, cross-join
- Fingerprint: 88352a3681e88a50

---

## [LRN-20260326-540] best_practice

**Logged**: 2026-03-26T17:07:48
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 between subqueries but not between CTEs or plain tables. Use subquery inline views for cartesian product of single-row aggregations.

### Details
When joining two single-row aggregation results in ODPS: CTE + JOIN ON 1=1 fails, comma join fails, but subquery inline views with JOIN ON 1=1 works. Also, ads_strategy.dwd_ads_engine_compe_suc_req_hi may not have data for all ad_group_ids - the id_type/id_value filter needs verification.

### Suggested Action
Always use subquery inline views (not CTEs) when doing cartesian product joins in ODPS. Also check if engine-side tables have data before relying on them.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cartesian_join, cross_join, subquery
- Fingerprint: 3ed717c58481e979

---

## [LRN-20260326-388] best_practice

**Logged**: 2026-03-26T17:08:02
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 with subqueries but not with CTEs or plain tables. Use subquery-based inline views for cartesian joins.

### Details
When joining two single-row aggregation results in ODPS: CTE + JOIN ON 1=1 fails, comma join fails, but subquery inline views + JOIN ON 1=1 works. Also, ads_strategy.dwd_ads_engine_compe_suc_req_hi may not have data for all ad_group_ids - the id_type/id_value filter needs verification.

### Suggested Action
Always use subquery inline views for cartesian joins in ODPS. When engine funnel data is NULL, note it in the report and suggest checking if the table has data for the given ad_group_id.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cartesian_join, engine_funnel
- Fingerprint: d14ef24a73ba355b

---

## [LRN-20260326-594] best_practice

**Logged**: 2026-03-26T17:08:45
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 between subqueries but not between CTEs or plain tables. Use subquery-based approach for cartesian joins.

### Details
When joining two single-row aggregation results in ODPS: (1) CTE + JOIN ON 1=1 fails with 'expect equality expression'. (2) Comma join (FROM a, b) fails with 'cartesian product not allowed'. (3) Subquery + JOIN ON 1=1 works successfully. The key is wrapping aggregations as inline subqueries rather than CTEs.

### Suggested Action
Always use subquery-based approach for cartesian joins in ODPS, not CTE-based.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, sql, cartesian-join, cross-join
- Fingerprint: f41715d48f5e9341

---

## [LRN-20260326-174] best_practice

**Logged**: 2026-03-26T17:08:58
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 between subqueries but not between CTEs or tables directly. Use inline subqueries for cartesian joins.

### Details
When joining two single-row aggregation results in ODPS: (1) CTE + JOIN ON 1=1 fails with 'expect equality expression'. (2) Comma join (implicit cartesian) fails with 'cartesian product not allowed'. (3) Inline subqueries with JOIN ON 1=1 works successfully.

### Suggested Action
Always use inline subqueries (not CTEs) when doing cartesian joins in ODPS. Pattern: SELECT ... FROM (SELECT ...) a JOIN (SELECT ...) b ON 1=1

### Metadata
- Source: error
- Related Files: 
- Tags: odps, sql, cartesian-join, cross-join
- Fingerprint: f9ec6cc35701fd87

---

## [LRN-20260326-336] best_practice

**Logged**: 2026-03-26T17:09:12
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 between subqueries but not between CTEs or plain tables. Use subquery inline views for cartesian product of single-row aggregations.

### Details
When joining two single-row aggregation results in ODPS: (1) CTE + JOIN ON 1=1 fails with 'expect equality expression'. (2) CTE + comma join fails with 'cartesian product not allowed'. (3) Subquery inline views + JOIN ON 1=1 works successfully.

### Suggested Action
Always use subquery inline views (not CTEs) when doing cartesian joins of single-row aggregations in ODPS.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cartesian-join, cte, subquery
- Fingerprint: c0bc3f6f22617222

---

## [LRN-20260326-729] best_practice

**Logged**: 2026-03-26T17:09:26
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS supports JOIN ON 1=1 with subqueries but not with CTE references or plain tables. Use inline subqueries for cartesian joins.

### Details
When joining two single-row aggregation results in ODPS: CTE + JOIN ON 1=1 fails, comma join fails, but inline subquery + JOIN ON 1=1 works. Also, ads_strategy.dwd_ads_engine_compe_suc_req_hi may not have data for all ad_group_ids - the id_type/id_value filter needs verification.

### Suggested Action
Always use inline subqueries (not CTEs) when doing cartesian joins in ODPS. Check if engine tables have data before relying on them.

### Metadata
- Source: error
- Related Files: 
- Tags: odps, cartesian_join, cross_join, engine_funnel
- Fingerprint: 505b540c3f710442

---
