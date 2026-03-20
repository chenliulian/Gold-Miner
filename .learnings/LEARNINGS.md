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
