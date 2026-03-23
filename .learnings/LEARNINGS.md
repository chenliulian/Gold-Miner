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

---

## [LRN-20260320-078] knowledge_gap

**Logged**: 2026-03-20T19:15:35
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-20T19:15:35.712104

相关 SQL:
```sql
WITH show_funnel AS (
  SELECT
    SUBSTR(dh,1,8) AS dt,
    SUM(show_label) AS show_cnt,
    SUM(click_label) AS click_cnt,
    SUM(dld_label) AS dld_cnt,
    SUM(conv_label_active) AS conv_active_cnt,
    SUM(conv_label_register) AS conv_register_cnt,
    SUM(conv_label_first_pay) AS conv_first_pay_cnt,
    SUM(conv_label_pay) AS conv_pay_cnt,
    SUM(conv_label_retain) AS conv_retain_cnt,
    SUM(conv_label_apply_loan) AS conv_apply_loan_cnt,
    SUM(conv_label_issue_loan) AS conv_issue_loan_
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-544] correction

**Logged**: 2026-03-22T21:38:25
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322133823302ghnkra7xmv1
ODPS-0130071:[10,20] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322133823302ghnkra7xmv1
ODPS-0130071:[10,20] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[11,17] Semantic analysis exception - functi
上下文: sql_execution
时间: 2026-03-22T21:38:25.767739

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd,
    SUM(show_label) as show_cnt,
    SUM(click_label) as click_cnt,
    ROUND(SUM(click_label) * 100.0 / NULLIF(SUM(show_label), 0), 4) as ctr,
    ROUND(SUM(billing_actual_deduction_price) / 1e5 / NULLIF(SUM(click_label), 0), 4) as cpc_usd,
    ROUND(SUM(billing_actual_deduction_price) / 1e5 / NULLIF(SUM(show_label), 0) * 1000, 4) as cpm_usd
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-096] correction

**Logged**: 2026-03-22T21:44:57
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322134454659gkt153757jh
ODPS-0130071:[13,13] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322134454659gkt153757jh
ODPS-0130071:[13,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[11,9] Semantic analysis exception - column 
上下文: sql_execution
时间: 2026-03-22T21:44:57.171835

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    -- 曝光数
    SUM(show_cnt) as show_cnt,
    -- 点击数
    SUM(click_cnt) as click_cnt,
    -- 转化数 (激活)
    SUM(CASE WHEN event_type = '1' THEN pv ELSE 0 END) as active_cnt,
    -- 消耗 (美元)
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -7, 'HH')
AND advertiser_id = '2368'
GROUP BY SUBSTR(dh, 1, 8), ad_group_id
ORDER BY dt DESC, ad
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-983] correction

**Logged**: 2026-03-22T21:45:19
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322134515757g03j1yb2qen4
ODPS-0130071:[9,20] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322134515757g03j1yb2qen4
ODPS-0130071:[9,20] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)

上下文: sql_execution
时间: 2026-03-22T21:45:19.599009

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(CASE WHEN event_type = '1' THEN pv ELSE 0 END) as active_cnt,
    SUM(cpm_cost + cpc_cost + cpd_cost + cpi_cost) as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= SUBSTR(DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -168, 'HH'), 1, 10)
AND advertiser_id = '2368'
GROUP BY SUBSTR(dh, 1, 8), ad_group_id
ORDER BY dt DESC, ad_group_id
LIMIT 1000
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-964] correction

**Logged**: 2026-03-22T21:45:35
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322134531704gxbp6jqqqy
ODPS-0130071:[0,0] Semanti...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322134531704gxbp6jqqqy
ODPS-0130071:[0,0] Semantic analysis exception - physical plan generation failed: ODPS-0121095:Invalid argument - in function cast, string datetime's format must be yyyy-mm-dd hh:mi:ss,  input string is:2026032223

上下文: sql_execution
时间: 2026-03-22T21:45:35.790146

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(CASE WHEN event_type = '1' THEN pv ELSE 0 END) as active_cnt,
    SUM(cpm_cost + cpc_cost + cpd_cost + cpi_cost) as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= SUBSTR(CAST(DATEADD(CAST(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi') AS DATETIME), -168, 'HH') AS STRING), 1, 10)
AND advertiser_id = '2368'
GROUP BY SUBSTR(dh, 1, 8), ad_group_id
ORDER BY dt DESC,
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-456] correction

**Logged**: 2026-03-22T21:51:58
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322135155524gahlra7xmv1
ODPS-0130071:[13,11] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322135155524gahlra7xmv1
ODPS-0130071:[13,11] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[4,9] Semantic analysis exception - column b
上下文: sql_execution
时间: 2026-03-22T21:51:58.016342

相关 SQL:
```sql
SELECT 
    ad_group_id,
    ad_group_title,
    SUM(billing_actual_deduction_price) / 1e5 as total_cost_usd,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0) as ctr_pct,
    -- 转化数需要从转化相关字段统计，这里先统计下载和激活
    SUM(COALESCE(dld_finished_cnt, 0)) as download_cnt,
    SUM(COALESCE(install_finish_cnt, 0)) as install_cnt
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE advertiser_id = '2368'
AND dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-602] correction

**Logged**: 2026-03-22T21:52:14
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 2026032213520910gghlra7xmv1
ODPS-0130071:[13,26] Seman...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 2026032213520910gghlra7xmv1
ODPS-0130071:[13,26] Semantic analysis exception - function or view 'to_datetime' cannot be resolved

上下文: sql_execution
时间: 2026-03-22T21:52:14.896958

相关 SQL:
```sql
SELECT 
    ad_group_id,
    ad_group_title,
    SUM(cpm_cost + cpc_cost + cpd_cost + cpi_cost) as total_cost_usd,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0) as ctr_pct,
    SUM(COALESCE(dld_finished_cnt, 0)) as download_cnt,
    SUM(COALESCE(install_finish_cnt, 0)) as install_cnt,
    SUM(COALESCE(pv, 0)) as conversion_cnt
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE advertiser_id = '2368'
AND dh >= SUBSTR(DATEADD(TO_DA
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-830] correction

**Logged**: 2026-03-22T21:52:45
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322135239799ghkj1yb2qen4
ODPS-0130071:[0,0] Seman...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322135239799ghkj1yb2qen4
ODPS-0130071:[0,0] Semantic analysis exception - physical plan generation failed: ODPS-0121095:Invalid argument - in function cast, string datetime's format must be yyyy-mm-dd hh:mi:ss,  input string is:2026032223

上下文: sql_execution
时间: 2026-03-22T21:52:45.149559

相关 SQL:
```sql
SELECT 
    ad_group_id,
    ad_group_title,
    SUM(cpm_cost + cpc_cost + cpd_cost + cpi_cost) as total_cost_usd,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0) as ctr_pct,
    SUM(COALESCE(dld_finished_cnt, 0)) as download_cnt,
    SUM(COALESCE(install_finish_cnt, 0)) as install_cnt,
    SUM(COALESCE(pv, 0)) as conversion_cnt
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE advertiser_id = '2368'
AND dh >= SUBSTR(DATEADD(CAST(
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-891] correction

**Logged**: 2026-03-22T21:52:56
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322135253889glkj1yb2qen4
ODPS-0130071:[13,18] Sem...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322135253889glkj1yb2qen4
ODPS-0130071:[13,18] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)

上下文: sql_execution
时间: 2026-03-22T21:52:56.074938

相关 SQL:
```sql
SELECT 
    ad_group_id,
    ad_group_title,
    SUM(cpm_cost + cpc_cost + cpd_cost + cpi_cost) as total_cost_usd,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0) as ctr_pct,
    SUM(COALESCE(dld_finished_cnt, 0)) as download_cnt,
    SUM(COALESCE(install_finish_cnt, 0)) as install_cnt,
    SUM(COALESCE(pv, 0)) as conversion_cnt
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE advertiser_id = '2368'
AND dh >= SUBSTR(DATEADD(MAX_P
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-885] correction

**Logged**: 2026-03-22T22:05:16
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322140513690g3g453757jh
ODPS-0130071:[11,20] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322140513690g3g453757jh
ODPS-0130071:[11,20] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)

上下文: sql_execution
时间: 2026-03-22T22:05:16.064531

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(pv) as conv_cnt,
    ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 4) as ctr_pct,
    ROUND(SUM(pv) * 100.0 / NULLIF(SUM(click_cnt), 0), 4) as cvr_pct,
    ROUND(SUM(cpm_cost + cpc_cost), 2) as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= SUBSTR(DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -7, 'HH'), 1, 10)
AND advertiser_id = '2368'
GRO
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-074] correction

**Logged**: 2026-03-22T22:06:10
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322140606684g7gwnlqqqy
ODPS-0130071:[11,33] Seman...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322140606684g7gwnlqqqy
ODPS-0130071:[11,33] Semantic analysis exception - function or view 'to_datetime' cannot be resolved

上下文: sql_execution
时间: 2026-03-22T22:06:10.285634

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(pv) as conv_cnt,
    ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 4) as ctr_pct,
    ROUND(SUM(pv) * 100.0 / NULLIF(SUM(click_cnt), 0), 4) as cvr_pct,
    ROUND(SUM(cpm_cost + cpc_cost), 2) as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= SUBSTR(CAST(DATEADD(TO_DATETIME(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), 'yyyymmddhh'), -7, 'HH') AS STR
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-501] knowledge_gap

**Logged**: 2026-03-22T22:08:27
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
执行超时错误: SQL submission timeout after 60 seconds...

### Details
错误类型: timeout_error
错误信息: SQL submission timeout after 60 seconds
上下文: sql_execution
时间: 2026-03-22T22:08:27.036147

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(pv) as conv_cnt,
    ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 4) as ctr_pct,
    ROUND(SUM(pv) * 100.0 / NULLIF(SUM(click_cnt), 0), 4) as cvr_pct,
    ROUND(SUM(cpm_cost + cpc_cost), 2) as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= SUBSTR(CAST(DATEADD(TO_DATE(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), 'yyyymmddhh'), -7, 'HH') AS STRING)
```

### Suggested Action
优化 SQL 性能，添加分区过滤条件，减少数据扫描量

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-358] correction

**Logged**: 2026-03-22T22:14:15
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322141412823gnc553757jh
ODPS-0130071:[6,13] Seman...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322141412823gnc553757jh
ODPS-0130071:[6,13] Semantic analysis exception - function date_format cannot match any overloaded functions with (DATETIME, STRING), candidates are STRING DATE_FORMAT(TIMESTAMP arg0, STRING arg1); STRING DATE_FORMAT(TIMESTAMP_NTZ arg0, STRING arg1)
ODPS-0130071:[4,9] Semantic analysis exception - column billing_actual_deduction_price cannot be resolved
ODPS-0130071:[10,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clau
上下文: sql_execution
时间: 2026-03-22T22:14:15.121966

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    SUBSTR(dh, 9, 2) as hour,
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DATE_FORMAT(DATEADD(TO_DATE('20260322', 'yyyymmdd'), -15, 'dd'), 'yyyymmdd') || '00'
AND dh <= '2026032223'
AND advertiser_id = '2368'
GROUP BY SUBSTR(dh, 1, 8), SUBSTR(dh, 9, 2)
ORDER BY dt, hour
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-262] correction

**Logged**: 2026-03-22T22:24:48
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322142443358grepra7xmv1
ODPS-0130071:[10,13] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322142443358grepra7xmv1
ODPS-0130071:[10,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[13,1] Semantic analysis exception - ORDER B
上下文: sql_execution
时间: 2026-03-22T22:24:48.820883

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    SUM(show_cnt) as show_num,
    SUM(click_cnt) as click_num,
    SUM(pv) as conv_num,
    ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 4) as ctr,
    ROUND(SUM(pv) * 100.0 / NULLIF(SUM(click_cnt), 0), 4) as cvr
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -7, 'dd')
AND advertiser_id = '2368'
GROUP BY SUBSTR(dh, 1, 8), ad_group_id
ORDER BY dt DESC, ad_group_id
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-240] correction

**Logged**: 2026-03-22T22:41:29
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322144123412gijlzyphr6
ODPS-0130071:[0,0] Semanti...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322144123412gijlzyphr6
ODPS-0130071:[0,0] Semantic analysis exception - physical plan generation failed: ODPS-0121095:Invalid argument - in function cast, string datetime's format must be yyyy-mm-dd hh:mi:ss,  input string is:2026032223

上下文: sql_execution
时间: 2026-03-22T22:41:29.349868

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    SUM(show_cnt) as show_num,
    SUM(click_cnt) as click_num,
    SUM(pv) as conv_num,
    ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 4) as ctr,
    ROUND(SUM(pv) * 100.0 / NULLIF(SUM(click_cnt), 0), 4) as cvr
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= SUBSTR(DATEADD(CAST(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi') AS DATETIME), -7, 'dd'), 1, 10)
AND advertiser_id = '2368'
GROUP BY SUBSTR(dh, 1, 8), ad_group_id
ORDER 
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-291] correction

**Logged**: 2026-03-22T22:46:50
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322144645776g3c59gcb4r1
ODPS-0130071:[12,11] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322144645776g3c59gcb4r1
ODPS-0130071:[12,11] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[4,9] Semantic analysis exception - column b
上下文: sql_execution
时间: 2026-03-22T22:46:50.361187

相关 SQL:
```sql
SELECT 
    ad_group_id,
    ad_group_title,
    SUM(billing_actual_deduction_price) / 1e5 as total_cost_usd,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0) as ctr_pct,
    SUM(pv) as conv_cnt,
    SUM(pv) * 100.0 / NULLIF(SUM(click_cnt), 0) as cvr_pct
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE advertiser_id = '2368'
AND dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -15, 'hour')
GROUP BY ad_group_id, ad_group
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-077] correction

**Logged**: 2026-03-22T22:50:04
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322144957126gqz0n0effn9
ODPS-0130071:[19,11] Sema...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322144957126gqz0n0effn9
ODPS-0130071:[19,11] Semantic analysis exception - function date_format cannot match any overloaded functions with (DATETIME, STRING), candidates are STRING DATE_FORMAT(TIMESTAMP arg0, STRING arg1); STRING DATE_FORMAT(TIMESTAMP_NTZ arg0, STRING arg1)
ODPS-0130221:[20,22] Invalid number of arguments - function dateadd needs 3 parameters, actually have 2
ODPS-0130071:[4,39] Semantic analysis exception - function date_format cannot match any ov
上下文: sql_execution
时间: 2026-03-22T22:50:04.363398

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    CASE 
        WHEN SUBSTR(dh, 1, 8) BETWEEN DATE_FORMAT(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -14, 'dd'), 'yyyymmdd') 
             AND DATE_FORMAT(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -8, 'dd'), 'yyyymmdd')
            THEN '上上周'
        WHEN SUBSTR(dh, 1, 8) BETWEEN DATE_FORMAT(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -7, 'dd'), 'yyyymmdd') 
             AND DATE_FORMAT(DATEADD(TO_DATE('20260324', 'dd'), -1, 'dd'), 'yyyymmdd')
            THEN '上周
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-151] correction

**Logged**: 2026-03-22T22:50:21
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130221: InstanceId: 20260322145016939gh21n0effn9
ODPS-0130221:[18,18] Inva...

### Details
错误类型: unknown
错误信息: ODPS-0130221: InstanceId: 20260322145016939gh21n0effn9
ODPS-0130221:[18,18] Invalid number of arguments - function dateadd needs 3 parameters, actually have 2
ODPS-0130071:[12,9] Semantic analysis exception - column cost cannot be resolved

上下文: sql_execution
时间: 2026-03-22T22:50:21.480625

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    CASE 
        WHEN SUBSTR(dh, 1, 8) BETWEEN TO_CHAR(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -14, 'dd'), 'yyyymmdd') 
             AND TO_CHAR(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -8, 'dd'), 'yyyymmdd')
            THEN '上上周'
        WHEN SUBSTR(dh, 1, 8) BETWEEN TO_CHAR(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -7, 'dd'), 'yyyymmdd') 
             AND TO_CHAR(DATEADD(TO_DATE('20260324', 'dd'), -1, 'dd'), 'yyyymmdd')
            THEN '上周'
        ELSE '
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-126] correction

**Logged**: 2026-03-22T22:50:51
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130221: InstanceId: 20260322145049306gf41n0effn9
ODPS-0130221:[18,18] Inva...

### Details
错误类型: unknown
错误信息: ODPS-0130221: InstanceId: 20260322145049306gf41n0effn9
ODPS-0130221:[18,18] Invalid number of arguments - function dateadd needs 3 parameters, actually have 2
ODPS-0130221:[8,26] Invalid number of arguments - function dateadd needs 3 parameters, actually have 2

上下文: sql_execution
时间: 2026-03-22T22:50:51.786709

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    CASE 
        WHEN SUBSTR(dh, 1, 8) BETWEEN TO_CHAR(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -14, 'dd'), 'yyyymmdd') 
             AND TO_CHAR(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -8, 'dd'), 'yyyymmdd')
            THEN '上上周'
        WHEN SUBSTR(dh, 1, 8) BETWEEN TO_CHAR(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -7, 'dd'), 'yyyymmdd') 
             AND TO_CHAR(DATEADD(TO_DATE('20260324', 'dd'), 'dd'), 'yyyymmdd')
            THEN '上周'
        ELSE '其他'

```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-048] correction

**Logged**: 2026-03-22T22:51:09
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130221: InstanceId: 20260322145102937gbfy3h12qen4
ODPS-0130221:[27,22] Inv...

### Details
错误类型: unknown
错误信息: ODPS-0130221: InstanceId: 20260322145102937gbfy3h12qen4
ODPS-0130221:[27,22] Invalid number of arguments - function dateadd needs 3 parameters, actually have 2
ODPS-0130071:[31,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-22T22:51:09.250889

相关 SQL:
```sql
SELECT 
    week_label,
    SUM(cpm_cost + cpc_cost) as cost_usd,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 4) as ctr,
    ROUND(SUM(cpm_cost + cpc_cost) / NULLIF(SUM(click_cnt), 0), 4) as cpc_usd
FROM (
    SELECT 
        dh,
        CASE 
            WHEN SUBSTR(dh, 1, 8) BETWEEN TO_CHAR(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -14, 'dd'), 'yyyymmdd') 
                 AND TO_CHAR(DATEADD(TO_DATE('20260324', 'y
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-740] correction

**Logged**: 2026-03-22T22:51:28
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130221: InstanceId: 2026032214512662gvayvp7xmv1
ODPS-0130221:[27,22] Inval...

### Details
错误类型: unknown
错误信息: ODPS-0130221: InstanceId: 2026032214512662gvayvp7xmv1
ODPS-0130221:[27,22] Invalid number of arguments - function dateadd needs 3 parameters, actually have 2

上下文: sql_execution
时间: 2026-03-22T22:51:28.571745

相关 SQL:
```sql
SELECT 
    week_label,
    SUM(cpm_cost + cpc_cost) as cost_usd,
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 4) as ctr,
    ROUND(SUM(cpm_cost + cpc_cost) / NULLIF(SUM(click_cnt), 0), 4) as cpc_usd
FROM (
    SELECT 
        dh,
        CASE 
            WHEN SUBSTR(dh, 1, 8) BETWEEN TO_CHAR(DATEADD(TO_DATE('20260324', 'yyyymmdd'), -14, 'dd'), 'yyyymmdd') 
                 AND TO_CHAR(DATEADD(TO_DATE('20260324', 'y
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-990] correction

**Logged**: 2026-03-22T22:59:16
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322145913561gkg1n0effn9
ODPS-0130071:[5,13] Seman...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322145913561gkg1n0effn9
ODPS-0130071:[5,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[3,9] Semantic analysis exception - column bi
上下文: sql_execution
时间: 2026-03-22T22:59:16.768109

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 10) as dt_hour,
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -15, 'hh')
AND advertiser_id = '2368'
GROUP BY SUBSTR(dh, 1, 10)
ORDER BY dt_hour
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---

## [LRN-20260322-113] correction

**Logged**: 2026-03-22T22:59:26
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322145924661g3nyvp7xmv1
ODPS-0130071:[3,9] Semant...

### Details
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322145924661g3nyvp7xmv1
ODPS-0130071:[3,9] Semantic analysis exception - column cost cannot be resolved

上下文: sql_execution
时间: 2026-03-22T22:59:26.961984

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 10) as dt_hour,
    SUM(cost) / 1e5 as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= '2026030700'
AND advertiser_id = '2368'
GROUP BY SUBSTR(dh, 1, 10)
ORDER BY dt_hour
LIMIT 1000
```

### Suggested Action
需要进一步调查

### Metadata
- Source: auto_detect
- Related Files: 
- Tags: 

---
