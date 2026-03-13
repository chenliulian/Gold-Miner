# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice
**Areas**: frontend | backend | infra | tests | docs | config | odps

---

## [LRN-20260313-680] insight

**Logged**: 2026-03-13T14:53:25
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
GoldMiner 项目成功整合了 self-improving-agent

### Details
从 ClawnHub 下载了 self-improving-agent 仓库，并创建了适配 GoldMiner 的 self_improvement skill

### Suggested Action
定期回顾学习记录，提炼可复用的模式

### Metadata
- Source: conversation
- Related Files: 
- Tags: 

---

## [LRN-20260313-407] best_practice

**Logged**: 2026-03-13T17:47:11
**Priority**: medium
**Status**: pending
**Area**: odps

### Summary
ODPS 任务可在 SQL 头部加 `SET odps.instance.priority=7;` 提升实例优先级以加速执行

### Details
用户反馈：执行 SQL 时在头部增加 `SET odps.instance.priority = 7;` 可获得更高优先级、运行更快。后续分析类 SQL 默认加该 SET 语句。

### Suggested Action
后续 run_sql 默认在脚本首行加入 `SET odps.instance.priority=7;`；若执行环境不支持多语句，则改为在会话级别提前设置或在任务配置中设置 priority。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: odps, priority, performance, user_feedback

---

## [LRN-20260313-099] correction

**Logged**: 2026-03-13T19:37:54
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
build_adgroup_data 生成多语句（DROP+SET+CREATE AS）时需要设置 odps.sql.submit.mode=script

### Details
报错提示：Please add put {"odps.sql.submit.mode":"script"} for multi-statement query in settings。应在 skill 的 config 里传入该参数。

### Suggested Action
后续调用 build_adgroup_data / 类似多语句技能时，统一在 config 传 {"odps.sql.submit.mode":"script"}

### Metadata
- Source: error
- Related Files: 
- Tags: odps, multi-statement, script-mode, skill

---
