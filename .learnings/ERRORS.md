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
