# Errors

Command failures, exceptions, and unexpected errors logged for debugging.

**Areas**: frontend | backend | infra | tests | docs | config | odps

---

## [ERR-20260313-818] skill_or_command

**Logged**: 2026-03-13T17:22:08
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
DESC tmp_adgroup_level_pcoc_stats_ctr_20260308 报表不存在(Table not found)，需先确认 analyze_ctr_pcoc 是否成功产出及当前 schema/表名

### Error
```
用户要查询 20260308、adgroup_id=70711 的 CTR PCOC。已触发 build_adgroup_data 与 analyze_ctr_pcoc，但在 DESC 结果表时报错：mi_ads_dmp_dev.tmp_adgroup_level_pcoc_stats_ctr_20260308 cannot be resolved。可能原因：analyze_ctr_pcoc 未实际创建表/创建在其他项目或 schema/表名不一致/临时表被清理。
```

### Context
- Source: error

### Suggested Fix
先 SHOW TABLES LIKE 'tmp_adgroup_level_pcoc_stats_ctr_20260308*' 或在 skill 中指定 output_table 并确认返回成功；必要时重跑 analyze_ctr_pcoc 并立刻 SELECT 结果；同时确认当前 project/schema。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260313-319] skill_or_command

**Logged**: 2026-03-13T17:28:05
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
build_adgroup_data 失败：多语句脚本需在 settings/config 中显式开启 odps.sql.submit.mode=script

### Error
```
调用 build_adgroup_data(20260301~20260310) 报 ParseError，并提示：Please add put {"odps.sql.submit.mode":"script"} for multi-statement query in settings。该 skill 内部包含 SET/DROP/CREATE 多语句，需要在 skill 的 config 里传入 odps.sql.submit.mode=script，或改为单条 SQL 执行。
```

### Context
- Source: error

### Suggested Fix
后续调用 build_adgroup_data/analyze_* 如包含多语句，统一在 config 里传 {"odps.sql.submit.mode":"script"}；本需求（每日 PCOC）直接写 SQL 从明细表按 dt 聚合即可。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260313-922] skill_or_command

**Logged**: 2026-03-13T17:48:03
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
调用 build_adgroup_data 失败：缺少 access_id，说明该 skill 依赖外部凭证/环境变量

### Error
```
报错：Skill build_adgroup_data error: 'access_id'。这表示该技能在当前运行环境需要预先配置 access_id/access_key（或等价 ODPS 账号凭证），否则无法创建中间表。与此同时，run_sql 直接在 SQL 头部加 SET 也会因为多语句提交限制而 ParseError（需 odps.sql.submit.mode=script）。
```

### Context
- Source: error

### Suggested Fix
1) 若要用 build_adgroup_data/analyze_ctr_pcoc：补齐运行环境的 ODPS 凭证（access_id 等）或改为使用 STS；2) 若仅做当天聚合：继续用单条 SELECT 的 run_sql 计算 PCOC；3) 若必须在 SQL 里 SET priority：需要把提交模式切到 script（在当前 run_sql 接口不支持）。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260317-798] skill_or_command

**Logged**: 2026-03-17T15:30:31
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
self_improvement 调用报错修复：entry_type 不支持 'correction'

### Error
```
触发报错：Skill 'self_improvement' error: 'correction'。原因：self_improvement 的 entry_type 枚举仅支持 learning(默认)/error/feature_request；若要表达“纠正/修复”，应使用 category='correction' 而不是 entry_type='correction'。
```

### Context
- Source: error

### Suggested Fix
后续调用规范：entry_type 仅用 learning/error/feature_request；纠正类内容用 category='correction'；在 Agent 层增加 entry_type 枚举校验与同一指令去重，避免重复/非法写入。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260317-080] skill_or_command

**Logged**: 2026-03-17T20:07:28
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
dwd_ew_ads_show_res_clk_dld_conv_hi 无 show_count/click_count 字段，需要用 show_label/click_label 聚合得到展示/点击数。

### Error
```
查询 dh='2026031510' 时，引用 show_count/click_count 报错无法解析。该表为曝光级别明细，一行代表一次展示；展示/点击可用 show_label/click_label(通常为0/1) 汇总。
```

### Context
- Source: error

### Suggested Fix
后续统计 shows=SUM(CASE WHEN CAST(show_label AS STRING)='1' THEN 1 ELSE 0 END)，clicks=SUM(CASE WHEN CAST(click_label AS STRING)='1' THEN 1 ELSE 0 END)，CTR=clicks/shows。

### Metadata
- Reproducible: unknown
- Related Files: 

---

## [ERR-20260319-382] skill_or_command

**Logged**: 2026-03-19T11:05:21
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260319030518490g0776t6xmv1
ODPS-0130071:[7,7] Semant...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260319030518490g0776t6xmv1
ODPS-0130071:[7,7] Semantic analysis exception - column download_label cannot be resolved
ODPS-0130071:[8,7] Semantic analysis exception - column convert_label cannot be resolved
ODPS-0130071:[11,53] Semantic analysis exception - column download_label cannot be resolved
ODPS-0130141:[11,49] Illegal implicit type cast - cannot cast from ErrorType to VOID
ODPS-0130071:[12,53] Semantic analysis exception - column convert_label cannot be resolve
上下文: sql_execution
时间: 2026-03-19T11:05:21.267220

相关 SQL:
```sql
SELECT
  '20260315' AS dt,
  ad_group_id,
  cost_type,
  SUM(show_label)      AS show_cnt,
  SUM(click_label)     AS click_cnt,
  SUM(download_label)  AS download_cnt,
  SUM(convert_label)   AS convert_cnt,
  SUM(billing_actual_deduction_price) / 1e5 AS cost_usd,
  CASE WHEN SUM(show_label) = 0 THEN NULL ELSE SUM(click_label)    / SUM(show_label) END AS ctr,
  CASE WHEN SUM(click_label) = 0 THEN NULL ELSE SUM(download_label) / SUM(click_label) END AS dld_rate_by_click,
  CASE WHEN SUM(click_labe
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

## [ERR-20260319-925] skill_or_command

**Logged**: 2026-03-19T20:21:59
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
未知错误: ODPS-0130071: InstanceId: 20260319122156847gyna0352qen4
ODPS-0130071:[35,1] Sema...

### Error
```
错误类型: unknown
错误信息: ODPS-0130071: InstanceId: 20260319122156847gyna0352qen4
ODPS-0130071:[35,1] Semantic analysis exception - ORDER BY must be used with a LIMIT clause, please set odps.sql.validate.orderby.limit=false to use it.

上下文: sql_execution
时间: 2026-03-19T20:21:59.543803

相关 SQL:
```sql
WITH daily AS (
  SELECT
    SUBSTR(dh, 1, 8) AS dt,
    advertiser_id,
    SUM(CASE WHEN show_label = 1 THEN billing_actual_deduction_price ELSE 0 END) / 1e5 AS cost_usd,
    SUM(CASE WHEN show_label = 1 THEN click_label ELSE 0 END) AS click_cnt,
    SUM(CASE WHEN show_label = 1 THEN conv_label_apply_loan ELSE 0 END) AS apply_loan_cnt
  FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
  WHERE dh >= '2025031000' AND dh <= '2025031523'
    AND advertiser_id IN ('6009','2368')
  GROUP BY SUBSTR
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
