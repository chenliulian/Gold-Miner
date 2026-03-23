# Errors

Command failures, exceptions, and unexpected errors logged for debugging.

**Areas**: frontend | backend | infra | tests | docs | config | odps

---
## [ERR-20260320-372] skill_or_command

**Logged**: 2026-03-20T17:47:40
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260320094737400gncd5j72qen4
ODPS-0130071:[0,0] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260320094737400gncd5j72qen4
ODPS-0130071:[0,0] Semantic analysis exception - while resolving view .max_pt - [0,0]recursive function call is not supported, cycle is max_pt->max_pt
ODPS-0130071:[0,0] Semantic analysis exception - while resolving view .max_pt - [2,10]recursive function call is not supported, cycle is max_pt->max_pt->max_pt
ODPS-0130221:[2,10] Invalid number of arguments - function max_pt needs 0 parameters, actually have 1
ODPS-0130071:[2,10] Semantic an
上下文: sql_execution
时间: 2026-03-20T17:47:40.131176

相关 SQL:
```sql
WITH max_pt AS (
  SELECT MAX_PT('mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi') AS max_dh
), range AS (
  SELECT 
    max_dh,
    TO_CHAR(DATEADD(TO_DATE(SUBSTR(max_dh,1,8),'yyyymmdd'), -6, 'dd'), 'yyyymmdd') AS start_dt,
    SUBSTR(max_dh,1,8) AS end_dt
  FROM max_pt
)
SELECT 
  SUBSTR(t.dh,1,8) AS dt,
  CAST(t.cost_type AS STRING) AS cost_type,
  ROUND(SUM(t.billing_actual_deduction_price)/1e5, 2) AS cost_usd,
  SUM(t.show_label) AS show_cnt,
  SUM(t.click_label) AS click_cnt,
  ROUND(SUM(t
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260320-381] skill_or_command

**Logged**: 2026-03-20T17:49:21
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130221: InstanceId: 20260320094918604gffd5j72qen4
ODPS-0130221:[1,8] Inval...

### Error
```
错误类型: unknown
错误信息: ODPS-0130221: InstanceId: 20260320094918604gffd5j72qen4
ODPS-0130221:[1,8] Invalid number of arguments - function max_pt needs 1 parameters, actually have 0

上下文: sql_execution
时间: 2026-03-20T17:49:21.294915

相关 SQL:
```sql
SELECT MAX_PT() AS max_dh
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
LIMIT 1;
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260320-378] skill_or_command

**Logged**: 2026-03-20T19:12:44
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260320111241839g6j2deq9aio2
ODPS-0130071:[57,1] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260320111241839g6j2deq9aio2
ODPS-0130071:[57,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-20T19:12:44.597729

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
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260320-341] skill_or_command

**Logged**: 2026-03-20T19:13:10
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS 报错：ORDER BY 必须搭配 LIMIT（默认开启 odps.sql.validate.orderby.limit）

### Error
```
在按天漏斗查询中使用 ORDER BY dt，实例报错 ODPS-0130071: ORDER BY must be used with a LIMIT clause。
```

### Context
- Source: error

### Suggested Fix
对需要排序的查询统一加 LIMIT（如 LIMIT 10000），或在 session 里关闭 odps.sql.validate.orderby.limit（不推荐）。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260320-616] skill_or_command

**Logged**: 2026-03-20T19:37:06
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260320113703930gl1lnhd57jh
ODPS-0130071:[88,1] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260320113703930gl1lnhd57jh
ODPS-0130071:[88,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-20T19:37:06.716507

相关 SQL:
```sql
WITH base AS (
  SELECT
    SUBSTR(dh, 9, 2) AS hh,
    advertiser_id,
    ad_group_id,
    cost_type,
    show_label,
    click_label,
    billing_actual_deduction_price AS cost_micro_usd
  FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
  WHERE dh BETWEEN '2026031800' AND '2026031823'
    AND advertiser_id = 6009
),
by_adgroup AS (
  SELECT
    ad_group_id,
    SUM(cost_micro_usd) / 1e5 AS cost_usd
  FROM base
  GROUP BY ad_group_id
),
top_adgroup AS (
  SELECT
    ad_group_id,
    cost_us
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260320-368] skill_or_command

**Logged**: 2026-03-20T19:51:20
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260320115117751glz5nae2qen4
ODPS-0130071:[2,3] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260320115117751glz5nae2qen4
ODPS-0130071:[2,3] Semantic analysis exception - column reference dwd_ew_ads_show_res_clk_dld_conv_hi.dh should appear in GROUP BY key

上下文: sql_execution
时间: 2026-03-20T19:51:20.401336

相关 SQL:
```sql
SELECT
  dh,
  SUM(billing_actual_deduction_price) / 1e5 AS cost_usd,
  SUM(show_label) AS show_cnt,
  SUM(click_label) AS click_cnt,
  COUNT(1) AS row_cnt
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh = '2026031810';
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260322-769] skill_or_command

**Logged**: 2026-03-22T21:37:54
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322133751925g1uo6jqqqy
ODPS-0130071:[10,13] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322133751925g1uo6jqqqy
ODPS-0130071:[10,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[13,1] Semantic analysis exception - ORDER BY
上下文: sql_execution
时间: 2026-03-22T21:37:54.481708

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
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260322-469] skill_or_command

**Logged**: 2026-03-22T21:38:08
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322133805260g4oi1yb2qen4
ODPS-0130071:[0,0] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322133805260g4oi1yb2qen4
ODPS-0130071:[0,0] Semantic analysis exception - physical plan generation failed: ODPS-0121095:Invalid argument - in function cast, string datetime's format must be yyyy-mm-dd hh:mi:ss,  input string is:2025091600

上下文: sql_execution
时间: 2026-03-22T21:38:08.557739

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
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260322-280] skill_or_command

**Logged**: 2026-03-22T21:42:47
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322134243988g5866ha5aio2
ODPS-0130071:[4,13] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322134243988g5866ha5aio2
ODPS-0130071:[4,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[5,11] Semantic analysis exception - functio
上下文: sql_execution
时间: 2026-03-22T21:42:47.279771

相关 SQL:
```sql
SELECT 
    SUM(billing_actual_deduction_price) / 1e5 as total_cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -24, 'hh')
AND dh <= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -1, 'hh')
AND advertiser_id = '2368'
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260322-687] skill_or_command

**Logged**: 2026-03-22T21:43:28
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322134325993giwkra7xmv1
ODPS-0130071:[4,13] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322134325993giwkra7xmv1
ODPS-0130071:[4,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)

上下文: sql_execution
时间: 2026-03-22T21:43:28.466024

相关 SQL:
```sql
SELECT 
    SUM(cpm_cost + cpc_cost + cpd_cost + cpi_cost) as total_cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -24, 'hh')
AND dh < MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi')
AND advertiser_id = '2368'
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260322-602] skill_or_command

**Logged**: 2026-03-22T21:59:31
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 2026032213592955gl476ha5aio2
ODPS-0130071:[4,13] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 2026032213592955gl476ha5aio2
ODPS-0130071:[4,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[5,10] Semantic analysis exception - function
上下文: sql_execution
时间: 2026-03-22T21:59:31.755551

相关 SQL:
```sql
SELECT 
    SUM(billing_actual_deduction_price) / 1e5 as total_cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -24, 'hour')
AND dh < DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), 0, 'hour')
AND advertiser_id = '2368'
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260322-903] skill_or_command

**Logged**: 2026-03-22T22:04:38
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322140434810gs91no55aio2
ODPS-0130071:[17,13] Sem...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322140434810gs91no55aio2
ODPS-0130071:[17,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[15,15] Semantic analysis exception - colum
上下文: sql_execution
时间: 2026-03-22T22:04:38.860210

相关 SQL:
```sql
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    ad_group_id,
    -- 曝光数
    SUM(show_cnt) as show_cnt,
    -- 点击数
    SUM(click_cnt) as click_cnt,
    -- 转化数
    SUM(pv) as conv_cnt,
    -- CTR = 点击数/曝光数
    ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 4) as ctr_pct,
    -- CVR = 转化数/点击数
    ROUND(SUM(pv) * 100.0 / NULLIF(SUM(click_cnt), 0), 4) as cvr_pct,
    -- 消耗 (美元)
    ROUND(SUM(billing_actual_deduction_price) / 1e5, 2) as cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DA
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260322-508] skill_or_command

**Logged**: 2026-03-22T22:19:46
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260322141943985g85w3h12qen4
ODPS-0130071:[4,13] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260322141943985g85w3h12qen4
ODPS-0130071:[4,13] Semantic analysis exception - function dateadd cannot match any overloaded functions with (STRING, INT, STRING), candidates are DATE DATEADD(DATE arg0, BIGINT arg1, STRING arg2); DATETIME DATEADD(DATETIME arg0, BIGINT arg1, STRING arg2); TIMESTAMP DATEADD(TIMESTAMP arg0, BIGINT arg1, STRING arg2); TIMESTAMP_NTZ DATEADD(TIMESTAMP_NTZ arg0, BIGINT arg1, STRING arg2)
ODPS-0130071:[5,11] Semantic analysis exception - functio
上下文: sql_execution
时间: 2026-03-22T22:19:46.893341

相关 SQL:
```sql
SELECT 
    SUM(billing_actual_deduction_price) / 1e5 as total_cost_usd
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -24, 'hh')
AND dh <= DATEADD(MAX_PT('com_cdm.dws_tracker_ad_cpc_cost_hi'), -1, 'hh')
AND advertiser_id = '2368'
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---
