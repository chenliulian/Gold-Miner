# Errors

Command failures, exceptions, and unexpected errors logged for debugging.

**Areas**: frontend | backend | infra | tests | docs | config | odps

---

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

## [ERR-20260323-466] skill_or_command

**Logged**: 2026-03-23T23:29:43
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
未知错误: ParseError: RequestId: 69C15C676AFF6B3285B28A65 Tag: ODPS Endpoint: http://servi...

### Error
```
错误类型: unknown
错误信息: ParseError: RequestId: 69C15C676AFF6B3285B28A65 Tag: ODPS Endpoint: http://service.eu-central-1.maxcompute.aliyun.com/api
SQL Statement: 
    DROP TABLE IF EXISTS adgroup_level_pcoc_stats_cvr_all;

    SET odps.instance.priority = 7;

    CREATE TABLE adgroup_level_pcoc_stats_cvr_all AS
    SELECT t.*,
           t.pcvr_raw_sum/t.conv_num AS pcoc_raw,
           ABS(t.pcvr_raw_sum/t.conv_num - 1) AS abs_error_raw,
           t.pcvr_sum/t.conv_num AS pcoc,
           ABS(t.pcvr_sum/t.conv_num - 1
上下文: skill_execution:analyze_cvr_pcoc
时间: 2026-03-23T23:29:43.805495

相关 Skill: analyze_cvr_pcoc
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: analyze_cvr_pcoc

---

## [ERR-20260323-362] skill_or_command

**Logged**: 2026-03-23T23:29:56
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
未知错误: ODPS-0130071: InstanceId: 20260323152953152gsuuspcxmv1
ODPS-0130071:[3,5] Semant...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260323152953152gsuuspcxmv1
ODPS-0130071:[3,5] Semantic analysis exception - invalid statement or wrong position, valid sequence is [SET ...], [DDL] then DML

上下文: skill_execution:build_adgroup_data
时间: 2026-03-23T23:29:56.824356

相关 Skill: build_adgroup_data
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: build_adgroup_data

---

## [ERR-20260324-472] skill_or_command

**Logged**: 2026-03-24T00:11:45
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130252: InstanceId: 20260323161143307grg8d1a57jh
ODPS-0130252:[53,1] Carte...

### Error
```
错误类型: unknown
错误信息: ODPS-0130252: InstanceId: 20260323161143307grg8d1a57jh
ODPS-0130252:[53,1] Cartesian product is not allowed - cartesian product is not allowed without mapjoin

上下文: sql_execution
时间: 2026-03-24T00:11:45.787638

相关 SQL:
```sql
-- 广告组 80554 完整漏斗分析（引擎侧 + 投放侧）
-- 引擎侧：召回→过滤→精排→响应
-- 投放侧：曝光→点击→下载→转化
WITH engine_funnel AS (
    SELECT 
        SUM(rank_req_cnt) as rank_req_cnt,
        SUM(resp_req_cnt) as resp_req_cnt
    FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
    WHERE dh >= '2026032200' AND dh < '2026032300'
    AND id_type = 'ad_group_id'
    AND id_value = '80554'
),
show_funnel AS (
    SELECT 
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(dld_label) as dld_cnt,
   
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

## [ERR-20260324-791] skill_or_command

**Logged**: 2026-03-24T15:03:08
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260324070305350go0zyta57jh
ODPS-0130071:[5,3] Semant...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260324070305350go0zyta57jh
ODPS-0130071:[5,3] Semantic analysis exception - column cost cannot be resolved

上下文: sql_execution
时间: 2026-03-24T15:03:08.010653

相关 SQL:
```sql
SELECT
  dh,
  ad_group_id,
  cost_type,
  cost,
  cpm_cost,
  cpc_cost,
  cpd_cost,
  cpi_cost,
  bill_should_cost,
  pool_should_cost,
  show_cnt,
  click_cnt
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh = '2026032300'
  AND ad_group_id = '80554'
LIMIT 5;
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

## [ERR-20260324-592] skill_or_command

**Logged**: 2026-03-24T15:03:42
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
com_cdm.dws_tracker_ad_cpc_cost_hi 表中不存在 cost 字段，查询会报 column cost cannot be resolved

### Error
```
在尝试查询 com_cdm.dws_tracker_ad_cpc_cost_hi 时使用了 cost 字段，ODPS 报错 ODPS-0130071 column cost cannot be resolved。explore_table 显示有 cpm_cost/cpc_cost/cpd_cost/cpi_cost、bill_should_cost、pool_should_cost 等字段，但未暴露 cost。后续统计需改用 pool_should_cost（实扣）或按各计费成本字段求和。
```

### Context
- Source: error

### Suggested Fix
先用样例分区拉取 80554 的 cpm_cost/cpc_cost/cpd_cost/cpi_cost、bill_should_cost、pool_should_cost，确认单位与总消耗口径；汇总时用 pool_should_cost 作为总消耗，必要时提供各计费方式拆分。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260324-926] skill_or_command

**Logged**: 2026-03-24T15:04:01
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
查询 com_cdm.dws_tracker_ad_cpc_cost_hi 使用列 cost 报错：column cost cannot be resolved

### Error
```
在黄金眼底表 com_cdm.dws_tracker_ad_cpc_cost_hi 中，字段列表里未包含 cost，但包含 pool_should_cost、bill_should_cost、cpm_cost、cpc_cost、cpd_cost、cpi_cost 等消耗相关字段。之前按天汇总SQL使用 sum(cost) 导致 ODPS-0130071。
```

### Context
- Source: error

### Suggested Fix
后续黄金眼口径消耗优先使用 pool_should_cost（资金池实扣，美元），并在必要时同时输出 bill_should_cost、cpm_cost/cpc_cost/cpd_cost/cpi_cost 做对账。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260324-767] skill_or_command

**Logged**: 2026-03-24T15:04:42
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
com_cdm.dws_tracker_ad_cpc_cost_hi 查询时列 cost 不存在（ODPS-0130071 column cost cannot be resolved）

### Error
```
在对黄金眼表 com_cdm.dws_tracker_ad_cpc_cost_hi 做消耗统计时，直接 SELECT cost 报错：ODPS-0130071 column cost cannot be resolved。该表字段里有 cpm_cost/cpc_cost/cpd_cost/cpi_cost、bill_should_cost、pool_should_cost 等，需要改用这些字段（可能用 pool_should_cost 作为总消耗，或用各 cost 分项相加）。
```

### Context
- Source: error

### Suggested Fix
先抽样查询确认各字段是否有值与口径，再用 pool_should_cost 或 sum(nvl(cpm_cost,0)+nvl(cpc_cost,0)+...) 作为总消耗字段进行按天/按cost_type聚合。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260324-241] skill_or_command

**Logged**: 2026-03-24T19:52:00
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260324115157431gbaj574xmv1
ODPS-0130071:[40,1] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260324115157431gbaj574xmv1
ODPS-0130071:[40,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-24T19:52:00.114885

相关 SQL:
```sql
WITH hour_agg AS (
  SELECT
    SUBSTR(dh, 1, 10) AS dh_hour,
    SUM(show_label) AS show_cnt,
    SUM(click_label) AS click_cnt,
    SUM(dld_label) AS dld_cnt,
    SUM(conv_label_active) AS conv_active_cnt,
    SUM(billing_actual_deduction_price) / 1e5 AS cost_usd
  FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
  WHERE dh BETWEEN '2026032100' AND '2026032123'
  GROUP BY SUBSTR(dh, 1, 10)
), total_agg AS (
  SELECT
    'TOTAL' AS dh_hour,
    SUM(show_label) AS show_cnt,
    SUM(click_labe
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

## [ERR-20260324-803] skill_or_command

**Logged**: 2026-03-24T22:33:08
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260324143305877g76fpvbxmv1
ODPS-0130071:[4,9] Semant...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260324143305877g76fpvbxmv1
ODPS-0130071:[4,9] Semantic analysis exception - column billing_actual_deduction_price cannot be resolved

上下文: sql_execution
时间: 2026-03-24T22:33:08.159799

相关 SQL:
```sql
SELECT 
    SUM(show_cnt) as show_cnt,
    SUM(click_cnt) as click_cnt,
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd,
    SUM(CASE WHEN transform_target_cn LIKE '%申贷%' THEN pv ELSE 0 END) as loan_apply_conv_cnt
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= '2026031900' AND dh <= '2026032323'
AND ad_group_id = '80554'
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

## [ERR-20260324-727] skill_or_command

**Logged**: 2026-03-24T22:51:17
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260324145112979gcqm9m72qen4
ODPS-0130071:[4,9] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260324145112979gcqm9m72qen4
ODPS-0130071:[4,9] Semantic analysis exception - column billing_actual_deduction_price cannot be resolved
ODPS-0130071:[5,9] Semantic analysis exception - column show_label cannot be resolved
ODPS-0130071:[6,9] Semantic analysis exception - column click_label cannot be resolved
ODPS-0130071:[7,15] Semantic analysis exception - column click_label cannot be resolved
ODPS-0130071:[7,49] Semantic analysis exception - column show_label cannot be
上下文: sql_execution
时间: 2026-03-24T22:51:17.576487

相关 SQL:
```sql
SELECT 
    ad_group_id,
    cost_type,
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd,
    SUM(show_label) as show_cnt,
    SUM(click_label) as click_cnt,
    ROUND(SUM(click_label) * 100.0 / NULLIF(SUM(show_label), 0), 4) as ctr
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE SUBSTR(dh, 1, 8) = '20260320'
GROUP BY ad_group_id, cost_type
ORDER BY cost_usd DESC
LIMIT 20
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

## [ERR-20260324-772] skill_or_command

**Logged**: 2026-03-24T23:22:42
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260324152239343geb8o4y4aio2
ODPS-0130071:[14,1] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260324152239343geb8o4y4aio2
ODPS-0130071:[14,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-24T23:22:42.605534

相关 SQL:
```sql
SELECT 
    cost_type,
    transform_target_cn,
    SUM(bill_should_cost) / 1e5 as cost_usd,
    SUM(show_cnt) as show_num,
    SUM(click_cnt) as click_num,
    SUM(dld_finished_cnt) as dld_num,
    ROUND(SUM(dld_finished_cnt) * 100.0 / NULLIF(SUM(click_cnt), 0), 2) as dld_rate_pct
FROM com_cdm.dws_tracker_ad_cpc_cost_hi
WHERE dh >= '2026032400'
AND dh <= '2026032423'
AND cost_type = 'ocpd'
GROUP BY cost_type, transform_target_cn
ORDER BY cost_usd DESC
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

## [ERR-20260325-104] skill_or_command

**Logged**: 2026-03-25T10:28:01
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325022758797gsu4iudffn9
ODPS-0130071:[12,1] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325022758797gsu4iudffn9
ODPS-0130071:[12,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-25T10:28:01.674763

相关 SQL:
```sql
SELECT
  SUBSTR(dh,1,8) AS dt,
  ROUND(SUM(billing_actual_deduction_price)/1e5, 6) AS cost_usd,
  SUM(show_label) AS show_cnt,
  SUM(dld_label) AS dld_cnt,
  SUM(conv_label_apply_loan) AS apply_loan_conv_cnt,
  ROUND(SUM(conv_label_apply_loan)/NULLIF(SUM(dld_label),0), 6) AS dld_to_apply_loan_rate
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh BETWEEN '2026031900' AND '2026032323'
  AND ad_group_id = '80554'
GROUP BY SUBSTR(dh,1,8)
ORDER BY dt;
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

## [ERR-20260325-412] skill_or_command

**Logged**: 2026-03-25T10:28:27
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS 报错：ORDER BY 必须搭配 LIMIT（或关闭校验参数）

### Error
```
在对 mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 做按日聚合后使用 ORDER BY dt，触发 ODPS-0130071: ORDER BY must be used with a LIMIT clause。
```

### Context
- Source: error

### Suggested Fix
对于需要排序的聚合查询：1) 增加 LIMIT（如 LIMIT 10000）；或 2) 不写 ORDER BY；或 3) 设置 odps.sql.validate.orderby.limit=false（不推荐在通用SQL中依赖）。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260325-546] skill_or_command

**Logged**: 2026-03-25T10:37:01
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
对 dwd_ew_ads_show_res_clk_dld_conv_hi 做简单按日聚合时，出现 SQL submission timeout after 60 seconds（提交阶段超时）

### Error
```
在 mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 上按日聚合（SUBSTR(dh,1,8) group by）并按 ad_group_id=80554、dh范围(2026031900-2026032323)过滤，多次出现 'SQL submission timeout after 60 seconds'。该报错发生在提交阶段（compile/submit），非语义报错。
```

### Context
- Source: error

### Suggested Fix
1) 优先改用 build_adgroup_data 先落一个按天聚合的中间表（减少直接扫DWD明细带来的提交/编译压力），再在中间表上做按日指标汇总；2) 若仍超时，拆分为按天/按小时分批跑并 union；3) 检查是否有网关/客户端提交超时限制，必要时提高提交超时或改用异步提交方式。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260325-502] skill_or_command

**Logged**: 2026-03-25T10:37:20
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325023717295gduuzpzwmv1
ODPS-0130071:[3,5] Semant...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325023717295gduuzpzwmv1
ODPS-0130071:[3,5] Semantic analysis exception - invalid statement or wrong position, valid sequence is [SET ...], [DDL] then DML

上下文: skill_execution:build_adgroup_data
时间: 2026-03-25T10:37:20.087700

相关 Skill: build_adgroup_data
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: build_adgroup_data

---

## [ERR-20260325-214] skill_or_command

**Logged**: 2026-03-25T15:41:13
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325074110663ga6tfrcffn9
ODPS-0130071:[11,9] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325074110663ga6tfrcffn9
ODPS-0130071:[11,9] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[5,9] Semantic analysis exception - column recall_cnt cannot be resolved
ODPS-0130071:[6,9] Semantic analysis exception - column filter_cnt cannot be resolved
ODPS-0130071:[7,9] Semantic analysis exception - column rank_cnt cannot be resolved
ODPS-0130071:[8,9] Semantic analysis exception - column resp_cnt cannot be resolved
ODPS-0130071:[19,
上下文: sql_execution
时间: 2026-03-25T15:41:13.380057

相关 SQL:
```sql
WITH
req AS (
  SELECT
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
    SUM(resp_cnt) AS engine_resp_cnt,
    SUM(win_cnt) AS win_cnt
  FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
  WHERE dh BETWEEN '2026032000' AND '
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

## [ERR-20260325-969] skill_or_command

**Logged**: 2026-03-25T15:41:36
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130013: InstanceId: 20260325074133847gibg5tcb4r1
ODPS-0130013:Authorizatio...

### Error
```
错误类型: unknown
错误信息: ODPS-0130013: InstanceId: 20260325074133847gibg5tcb4r1
ODPS-0130013:Authorization exception - Authorization Failed [4009,4019], You have NO privilege 'odps:Select' on {acs:odps:*:projects/ads_strategy/tables/dwd_ew_request_sample_hi}. Deny as default for Resource. Context ID:75408fc1-bb8e-4750-85fa-84becff67533.	--->Tips: CurrentProject:mi_ads_dmp_dev; Principal:RAM$transsion-ad@efc.aliyunid.com:tmc-cvr-dev; ACL check failed. You have no permissions to access column: ad_creative_id, code_seat_id
上下文: sql_execution
时间: 2026-03-25T15:41:36.555255

相关 SQL:
```sql
SELECT *
FROM ads_strategy.dwd_ew_request_sample_hi
WHERE dh BETWEEN '2026032000' AND '2026032001'
LIMIT 5;
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

## [ERR-20260325-844] skill_or_command

**Logged**: 2026-03-25T18:56:11
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325105608675gle8nkbb4r1
ODPS-0130071:[14,14] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325105608675gle8nkbb4r1
ODPS-0130071:[14,14] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[7,10] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[7,10] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[8,9] Semantic analysis exception - column recall_cnt cannot be resolved
ODPS-0130071:[9,9] Semantic analysis exception - column filter_cnt cannot be resolved
ODPS-013
上下文: sql_execution
时间: 2026-03-25T18:56:11.345759

相关 SQL:
```sql
WITH params AS (
  SELECT '2026031900' AS start_dh, '2026032523' AS end_dh, '67832' AS ad_group_id
),
req_sample AS (
  SELECT
    SUBSTR(dh,1,8) AS dt,
    CAST(ad_group_id AS BIGINT) AS ad_group_id,
    SUM(recall_cnt) AS recall_cnt,
    SUM(filter_cnt) AS filter_cnt,
    SUM(rank_cnt) AS rank_cnt,
    SUM(resp_cnt) AS resp_cnt
  FROM ads_strategy.dwd_ew_request_sample_hi
  WHERE dh BETWEEN (SELECT start_dh FROM params) AND (SELECT end_dh FROM params)
    AND CAST(ad_group_id AS STRING) = (SEL
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

## [ERR-20260325-385] skill_or_command

**Logged**: 2026-03-25T18:56:41
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: SQL validation failed: Potential SQL injection patterns detected: ['Multiple sta...

### Error
```
错误类型: unknown
错误信息: SQL validation failed: Potential SQL injection patterns detected: ['Multiple statements']
上下文: sql_validation
时间: 2026-03-25T18:56:41.826322

相关 SQL:
```sql
SELECT 'request_sample' AS src,
       *
FROM ads_strategy.dwd_ew_request_sample_hi
WHERE dh = '2026032500'
  AND CAST(ad_group_id AS STRING) = '67832'
LIMIT 5;

SELECT 'engine_compete' AS src,
       *
FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
WHERE dh = '2026032500'
  AND CAST(ad_group_id AS STRING) = '67832'
LIMIT 5;
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

## [ERR-20260325-766] skill_or_command

**Logged**: 2026-03-25T20:34:07
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260325123404302gx2fhkkco
ODPS-0130071:[8,9] Semantic...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260325123404302gx2fhkkco
ODPS-0130071:[8,9] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[4,18] Semantic analysis exception - column resp_cnt cannot be resolved
ODPS-0130071:[5,18] Semantic analysis exception - column win_cnt cannot be resolved

上下文: sql_execution
时间: 2026-03-25T20:34:07.111037

相关 SQL:
```sql
WITH engine_h AS (
  SELECT
    dh,
    SUM(COALESCE(resp_cnt, 0)) AS resp_cnt,
    SUM(COALESCE(win_cnt, 0))  AS win_cnt
  FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
  WHERE dh BETWEEN '2026032200' AND '2026032223'
    AND ad_group_id = 30573
  GROUP BY dh
),
post_h AS (
  SELECT
    dh,
    SUM(COALESCE(show_label, 0)) AS show_cnt,
    SUM(COALESCE(click_label, 0)) AS click_cnt,
    SUM(COALESCE(dld_label, 0)) AS dld_cnt,
    SUM(COALESCE(conv_label_active, 0)) AS conv_active_cnt,
    S
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

## [ERR-20260325-138] skill_or_command

**Logged**: 2026-03-25T20:35:42
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 2026032512354093gv2gyks9aio2
ODPS-0130071:[28,14] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 2026032512354093gv2gyks9aio2
ODPS-0130071:[28,14] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[21,10] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[21,10] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[22,9] Semantic analysis exception - column recall_cnt cannot be resolved
ODPS-0130071:[23,9] Semantic analysis exception - column filter_cnt cannot be resolved
ODPS
上下文: sql_execution
时间: 2026-03-25T20:35:42.893306

相关 SQL:
```sql
WITH
post_hour AS (
  SELECT
    SUBSTR(dh,1,10) AS hh,
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
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260326-324] skill_or_command

**Logged**: 2026-03-26T11:14:38
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130252: InstanceId: 20260326031436280gppmhv05aio2
ODPS-0130252:[43,1] Cart...

### Error
```
错误类型: unknown
错误信息: ODPS-0130252: InstanceId: 20260326031436280gppmhv05aio2
ODPS-0130252:[43,1] Cartesian product is not allowed - cartesian product is not allowed without mapjoin

上下文: sql_execution
时间: 2026-03-26T11:14:38.916006

相关 SQL:
```sql
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
    WHERE dh BETWEEN '2026032300' AND '2026032323'
    AND ad_group_id = '80554'
),
engine_
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

## [ERR-20260326-903] skill_or_command

**Logged**: 2026-03-26T11:14:57
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130252: InstanceId: 20260326031455283g36ac1cb4r1
ODPS-0130252:[42,19] Cart...

### Error
```
错误类型: unknown
错误信息: ODPS-0130252: InstanceId: 20260326031455283g36ac1cb4r1
ODPS-0130252:[42,19] Cartesian product is not allowed - cartesian product is not allowed without mapjoin

上下文: sql_execution
时间: 2026-03-26T11:14:57.983169

相关 SQL:
```sql
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
    WHERE dh BETWEEN '2026032300' AND '2026032323'
    AND ad_group_id = '80554'
),
engine_
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

## [ERR-20260326-666] skill_or_command

**Logged**: 2026-03-26T11:35:20
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130252: InstanceId: 20260326033517927ghv1fx62qen4
ODPS-0130252:[39,1] Cart...

### Error
```
错误类型: unknown
错误信息: ODPS-0130252: InstanceId: 20260326033517927ghv1fx62qen4
ODPS-0130252:[39,1] Cartesian product is not allowed - cartesian product is not allowed without mapjoin

上下文: sql_execution
时间: 2026-03-26T11:35:20.617880

相关 SQL:
```sql
WITH show_funnel AS (
    SELECT 
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(dld_label) as dld_cnt,
        SUM(conv_label_active) as conv_cnt,
        SUM(billing_actual_deduction_price) / 1e5 as total_cost
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '2026032300' AND '2026032323'
    AND ad_group_id = '80554'
),
engine_funnel AS (
    SELECT 
        SUM(rank_req_cnt) as rank_req_cnt,
        SUM(resp_req_cnt) as resp
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

## [ERR-20260326-356] skill_or_command

**Logged**: 2026-03-26T11:50:37
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260326035034409ga23fx62qen4
ODPS-0130071:[1,8] Seman...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260326035034409ga23fx62qen4
ODPS-0130071:[1,8] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[1,21] Semantic analysis exception - column ad_group_title cannot be resolved
ODPS-0130071:[1,64] Semantic analysis exception - column purpose_type_cn cannot be resolved
ODPS-0130071:[1,102] Semantic analysis exception - column status_v2 cannot be resolved; Did you mean status_cn ?

上下文: sql_execution
时间: 2026-03-26T11:50:37.098547

相关 SQL:
```sql
SELECT ad_group_id, ad_group_title, ad_plan_id, advertiser_id, purpose_type_cn, transform_target_cn, status_v2 FROM com_cdm.dim_ad_group_dd WHERE dt = MAX_PT('com_cdm.dim_ad_group_dd') AND advertiser_id = '2368' ORDER BY ad_group_id LIMIT 100;
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

## [ERR-20260326-323] skill_or_command

**Logged**: 2026-03-26T11:57:24
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260326035721942g1v2elo9aio2
ODPS-0130071:[1,132] Sem...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260326035721942g1v2elo9aio2
ODPS-0130071:[1,132] Semantic analysis exception - column cost cannot be resolved

上下文: sql_execution
时间: 2026-03-26T11:57:24.583484

相关 SQL:
```sql
SELECT ad_group_id, SUM(req_num) as req_cnt, SUM(res_num) as resp_cnt, SUM(show_cnt) as show_cnt, SUM(click_cnt) as click_cnt, SUM(cost) / 100.0 as cost_usd, ROUND(SUM(click_cnt) * 100.0 / NULLIF(SUM(show_cnt), 0), 2) as ctr_pct, ROUND(SUM(show_cnt) * 100.0 / NULLIF(SUM(res_num), 0), 2) as resp_to_show_pct, ROUND(SUM(res_num) * 100.0 / NULLIF(SUM(req_num), 0), 2) as req_to_resp_pct FROM com_cdm.dws_tracker_ad_cpc_cost_hi WHERE dh BETWEEN '2026032300' AND '2026032323' AND advertiser_id = '2368' G
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

## [ERR-20260326-551] skill_or_command

**Logged**: 2026-03-26T14:05:17
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130252: InstanceId: 20260326060514353gewnj52xmv1
ODPS-0130252:[43,1] Carte...

### Error
```
错误类型: unknown
错误信息: ODPS-0130252: InstanceId: 20260326060514353gewnj52xmv1
ODPS-0130252:[43,1] Cartesian product is not allowed - cartesian product is not allowed without mapjoin

上下文: sql_execution
时间: 2026-03-26T14:05:17.071217

相关 SQL:
```sql
WITH show_funnel AS (
    SELECT 
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(dld_label) as dld_cnt,
        SUM(conv_label_active) as conv_cnt_active,
        SUM(conv_label_register) as conv_cnt_register,
        SUM(conv_label_pay) as conv_cnt_pay,
        SUM(billing_actual_deduction_price) / 1e5 as total_cost
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '2026032300' AND '2026032323'
    AND CAST(ad_group_id AS STRIN
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

## [ERR-20260326-174] skill_or_command

**Logged**: 2026-03-26T16:09:22
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 按 code_seat_type 全日(24h)聚合 GROUP BY 提交超时

### Error
```
在 2026032300-2026032323 范围内对 dwd_ew_ads_show_res_clk_dld_conv_hi 做 GROUP BY code_seat_type，SQL submission timeout after 60 seconds。将时间拆成 00-11h 和 12-23h 两段分别聚合后成功。
```

### Context
- Source: error

### Suggested Fix
对该大表做 code_seat_type 等维度聚合时，优先拆分 dh 小时分区(如 6h/12h)，或先用更窄过滤条件/分桶临时表再汇总；避免全日直接 group by + order by。

### Metadata
- Reproducible: unknown
- Related Files: 
- Fingerprint: 06d6cdfb02508dd7

---

## [ERR-20260326-003] skill_or_command

**Logged**: 2026-03-26T16:17:15
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260326081713244gspiai7xmv1
ODPS-0130071:[13,10] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260326081713244gspiai7xmv1
ODPS-0130071:[13,10] Semantic analysis exception - column busniess_line cannot be resolved
ODPS-0130071:[2,5] Semantic analysis exception - column busniess_line cannot be resolved

上下文: sql_execution
时间: 2026-03-26T16:17:15.959343

相关 SQL:
```sql
SELECT 
    busniess_line,
    SUM(recall) AS recall_cnt,
    SUM(resp) AS resp_cnt,
    SUM(ssp_res_succ_cnt) AS ssp_res_succ_cnt,
    SUM(show_cnt) AS show_cnt,
    SUM(click_cnt) AS click_cnt,
    SUM(cnt_limit) AS cnt_limit
FROM com_ads.ads_creativity_filter_hi
WHERE dh >= '2026032300' AND dh <= '2026032323'
AND CAST(ad_group_id AS STRING) = '80554'
AND is_offline_ad = 0
GROUP BY busniess_line
ORDER BY recall_cnt DESC
LIMIT 50
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 
- Fingerprint: 6c797ee1da6bac19

---

## [ERR-20260326-685] skill_or_command

**Logged**: 2026-03-26T16:17:32
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260326081729909gd2gxwdffn9
ODPS-0130071:[11,10] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260326081729909gd2gxwdffn9
ODPS-0130071:[11,10] Semantic analysis exception - column busniess_line cannot be resolved
ODPS-0130071:[2,5] Semantic analysis exception - column busniess_line cannot be resolved

上下文: sql_execution
时间: 2026-03-26T16:17:32.616855

相关 SQL:
```sql
SELECT 
    busniess_line,
    SUM(show_label) as show_cnt,
    SUM(click_label) as click_cnt,
    SUM(dld_label) as dld_cnt,
    SUM(conv_label_active) as conv_cnt_active,
    SUM(billing_actual_deduction_price) / 1e5 as total_cost_usd
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh >= '2026032300' AND dh <= '2026032311'
AND CAST(ad_group_id AS STRING) = '80554'
GROUP BY busniess_line
ORDER BY show_cnt DESC
LIMIT 50
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 
- Fingerprint: cc576c2e04f4aadd

---

## [ERR-20260326-227] skill_or_command

**Logged**: 2026-03-26T17:03:23
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260326090320582ghq3c822qen4
ODPS-0130071:[43,25] Sem...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260326090320582ghq3c822qen4
ODPS-0130071:[43,25] Semantic analysis exception - expect equality expression (i.e., only use '=' and 'AND') for join condition without mapjoin hint, but get: (1 = 1)

上下文: sql_execution
时间: 2026-03-26T17:03:23.346177

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
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 
- Fingerprint: f2e312407ba2d51c

---

## [ERR-20260326-705] skill_or_command

**Logged**: 2026-03-26T17:03:42
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130252: InstanceId: 20260326090340136git3c822qen4
ODPS-0130252:[42,19] Car...

### Error
```
错误类型: unknown
错误信息: ODPS-0130252: InstanceId: 20260326090340136git3c822qen4
ODPS-0130252:[42,19] Cartesian product is not allowed - cartesian product is not allowed without mapjoin

上下文: sql_execution
时间: 2026-03-26T17:03:42.908314

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
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 
- Fingerprint: 706eafcd1f2c1de4

---

## [ERR-20260326-749] skill_or_command

**Logged**: 2026-03-26T17:33:08
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260326093305465gusagh957jh
ODPS-0130071:[1,201] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260326093305465gusagh957jh
ODPS-0130071:[1,201] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[1,8] Semantic analysis exception - column ad_group_id cannot be resolved
ODPS-0130071:[1,21] Semantic analysis exception - column ad_group_title cannot be resolved
ODPS-0130071:[1,64] Semantic analysis exception - column purpose_type_cn cannot be resolved
ODPS-0130071:[1,102] Semantic analysis exception - column status_v2 cannot be resolved
上下文: sql_execution
时间: 2026-03-26T17:33:08.181809

相关 SQL:
```sql
SELECT ad_group_id, ad_group_title, ad_plan_id, advertiser_id, purpose_type_cn, transform_target_cn, status_v2, cost_type FROM com_cdm.dim_ad_group_dd WHERE dt = MAX_PT('com_cdm.dim_ad_group_dd') AND ad_group_id = '81117' LIMIT 10;
```
```

### Context
- Source: auto_detect

### Suggested Fix
需要进一步调查

### Metadata
- Reproducible: unknown
- Related Files: 
- Fingerprint: e62b85f7e557d745

---
