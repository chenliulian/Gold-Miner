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

## [LRN-20260317-247] best_practice

**Logged**: 2026-03-17T15:26:46
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS 环境常见限制：ORDER BY 需配 LIMIT；跨 Project 表探索需先确定分区；com_cdm 等项目常见 Describe/Select 权限不足；消耗口径应使用 billing_actual_deduction_price/1e5

### Details
1) 多次遇到 ODPS-0130071：ORDER BY must be used with a LIMIT clause（解决：补 LIMIT 或关闭校验但不推荐）。
2) 表探索：对分区表直接 SELECT * LIMIT 仍会被视为全分区扫描，需先 SHOW PARTITIONS 获取分区字段和值，再带分区谓词抽样。
3) 跨 Project（如 com_cdm.*）经常无 odps:Describe/odps:Select 权限，导致 DESC/SHOW PARTITIONS/SELECT 均失败；需申请授权或在对应 Project 下执行。
4) 指标口径：消耗字段应取 billing_actual_deduction_price（微美元）并 /1e5 转 USD，而非 cost 字段。
5) 发现数据异常线索：ad_package_name 为 (null) 时可能出现 CTR>1，需优先核对 show/click label 口径与去重粒度。

### Suggested Action
将上述限制加入默认排查清单：
- 任何 ORDER BY 查询默认追加 LIMIT；
- 探索新表先 SHOW PARTITIONS/确认分区；
- 跨 Project 先做权限检查（Describe/Select）；
- 明确消耗口径默认使用 billing_actual_deduction_price/1e5；
- 遇到 CTR>1 立即做口径一致性与重复计数排查。

### Metadata
- Source: conversation
- Related Files: 
- Tags: odps, sql, orderby-limit, partition, permission, cost-metric

---

## [LRN-20260317-495] best_practice

**Logged**: 2026-03-17T15:27:05
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS 常见限制与排错：跨项目权限、分区谓词、DESC/SHOW CREATE 限制、ORDER BY 需 LIMIT、消耗字段口径

### Details
本轮对话中遇到并确认了多类 ODPS/环境限制：
1) 跨 Project 访问（如 com_cdm.*）可能缺少 odps:Describe/odps:Select，报错含 User doesn't exist in the project，需要找目标项目管理员授权。
2) 部分表强制要求带分区条件（否则 physical plan generation failed / full scan all partitions）。应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 某些环境不支持 DESC 或对 db.table 解析有差异，SHOW CREATE TABLE 也可能被拦截；可用 explore_table 或基于分区抽样 SELECT * LIMIT 反推字段。
4) 该 ODPS 环境开启校验：ORDER BY 必须配 LIMIT（否则报错提示 set odps.sql.validate.orderby.limit=false）。SQL 需显式加 LIMIT。
5) 多语句（尤其带 SET）在某些执行器/模式下会导致语义错误，建议单语句执行或避免在同一提交中混用 SET + DDL/DML。
6) 广告消耗字段口径应使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 编写 checklist：
- 先确认权限（Describe/Select）与当前 Project；
- 先 SHOW PARTITIONS，所有查询必须带分区；
- 所有 ORDER BY 必须带 LIMIT；
- 避免 SET + 其他语句混提交；
- 消耗统一用 billing_actual_deduction_price/1e5；
并在模板 SQL 中默认包含 LIMIT 与分区谓词。

### Metadata
- Source: conversation
- Related Files: 
- Tags: odps, permission, partition, orderby-limit, ddl, cost-metric

---

## [LRN-20260317-226] best_practice

**Logged**: 2026-03-17T15:27:12
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
收到用户指令：手动调用 self_improvement 记录本轮关键限制与修复套路

### Details
用户明确要求“调用 self_improvement skill”。本轮对话已验证的关键套路包括：跨项目权限（Describe/Select）、必须带分区谓词避免全表扫描、ORDER BY 必须配 LIMIT、部分环境对 DESC/SHOW CREATE TABLE 有限制时可用 explore_table 或分区抽样反推字段、避免混提 SET+其他语句、消耗字段统一使用 billing_actual_deduction_price/1e5。

### Suggested Action
将上述点整理为 ODPS SQL 执行前 checklist，并在后续模板 SQL 中默认加入：分区条件 + LIMIT + 正确消耗口径。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, cost-metric

---

## [LRN-20260317-563] best_practice

**Logged**: 2026-03-17T15:27:25
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
ODPS 执行常见坑位与本轮修复：权限/分区/ORDER BY+LIMIT/多语句SET/消耗口径

### Details
本轮对话沉淀的可复用经验：
1) 跨项目（如 com_cdm.*）常见缺少 odps:Describe/odps:Select，报错含 “User doesn't exist in the project”，需目标项目管理员授权。
2) 许多表强制要求带分区谓词（否则 full scan all partitions / physical plan generation failed）；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则报错提示 set odps.sql.validate.orderby.limit=false）。
4) 部分环境对 DESC/SHOW CREATE TABLE 受限时，可用 explore_table 或分区抽样 SELECT * LIMIT 反推字段。
5) 避免在同一次提交中混用 SET + DDL/DML（某些执行器会报 invalid statement sequence）。
6) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
形成 SQL 编写 checklist：先权限->先分区->所有 ORDER BY 带 LIMIT->避免多语句 SET 混提->消耗字段口径统一，并沉淀为模板 SQL。

### Metadata
- Source: conversation
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, multi-statement, cost-metric

---

## [LRN-20260317-218] best_practice

**Logged**: 2026-03-17T15:27:41
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
本轮关键ODPS限制与修复套路沉淀（权限/分区谓词/ORDER BY+LIMIT/SHOW CREATE受限/消耗口径）

### Details
本轮对话中反复遇到并已验证的ODPS/执行环境限制：
1) 跨项目访问（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描（physical plan generation failed），应先 SHOW PARTITIONS 再 WHERE dt/dh=...
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则报错提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE/DDL 在某些环境或跨project可能受限，可用：先 SHOW PARTITIONS + 分区抽样 SELECT * LIMIT 反推字段，或直接用 explore_table skill。
5) 广告消耗口径：使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀SQL模板与checklist：
- 确认当前project与权限（Describe/Select）
- 先拿分区（SHOW PARTITIONS / MAX(dt)）
- 所有 ORDER BY 都带 LIMIT
- 查询必带分区谓词
- 消耗统一 billing_actual_deduction_price/1e5

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, ddl-limit, cost-metric

---

## [LRN-20260317-805] best_practice

**Logged**: 2026-03-17T15:27:52
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
按用户指令调用 self_improvement：沉淀本轮 ODPS 排错与写 SQL checklist

### Details
本轮对话中验证/沉淀的 ODPS 常见限制与修复套路：
1) 跨项目（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描（physical plan generation failed / full scan all partitions）；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE / DESC 在部分环境或跨 project 可能受限；可用 explore_table 或“SHOW PARTITIONS + 分区抽样 SELECT * LIMIT”反推字段。
5) 避免同一次提交混用 SET + DDL/DML（部分执行器会报 invalid statement sequence）。
6) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 编写/执行 checklist，并在模板 SQL 中默认包含：分区条件 + LIMIT + 正确消耗口径；遇到跨项目表先做权限检查。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, multi-statement, cost-metric

---

## [LRN-20260317-011] best_practice

**Logged**: 2026-03-17T15:28:01
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
按用户指令调用 self_improvement：沉淀本轮 ODPS 排错与写 SQL checklist

### Details
本轮对话中验证/沉淀的 ODPS 常见限制与修复套路：
1) 跨项目（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描（physical plan generation failed / full scan all partitions）；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE / DESC 在部分环境或跨 project 可能受限；可用 explore_table 或“SHOW PARTITIONS + 分区抽样 SELECT * LIMIT”反推字段。
5) 避免同一次提交混用 SET + DDL/DML（部分执行器会报 invalid statement sequence）。
6) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 编写/执行 checklist，并在模板 SQL 中默认包含：分区条件 + LIMIT + 正确消耗口径；遇到跨项目表先做权限检查。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, ddl-limit, multi-statement, cost-metric

---

## [LRN-20260317-440] best_practice

**Logged**: 2026-03-17T15:28:16
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
按用户要求调用 self_improvement：记录本轮 ODPS 排错与 SQL 编写要点

### Details
本轮对话中验证/沉淀的 ODPS 常见限制与修复套路：
1) 跨项目访问（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描（physical plan generation failed / full scan all partitions）；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE / DESC 在部分环境或跨 project 可能受限；可用 explore_table 或“SHOW PARTITIONS + 分区抽样 SELECT * LIMIT”反推字段。
5) 避免同一次提交混用 SET + DDL/DML（部分执行器会报 invalid statement sequence）。
6) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 执行前 checklist，并在模板 SQL 中默认包含：分区条件 + LIMIT + 正确消耗口径；遇到跨项目表先做权限检查。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, ddl-limit, multi-statement, cost-metric

---

## [LRN-20260317-657] best_practice

**Logged**: 2026-03-17T15:28:25
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
按用户指令调用 self_improvement：沉淀本轮 ODPS 常见限制与修复 checklist

### Details
本轮对话中验证/沉淀的 ODPS 常见限制与修复套路：
1) 跨项目访问（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描（physical plan generation failed / full scan all partitions）；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE / DESC 在部分环境或跨 project 可能受限；可用 explore_table 或“SHOW PARTITIONS + 分区抽样 SELECT * LIMIT”反推字段。
5) 避免同一次提交混用 SET + DDL/DML（部分执行器会报 invalid statement sequence）。
6) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 执行前 checklist，并在模板 SQL 中默认包含：分区条件 + LIMIT + 正确消耗口径；遇到跨项目表先做权限检查。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, ddl-limit, multi-statement, cost-metric

---

## [LRN-20260317-883] best_practice

**Logged**: 2026-03-17T15:28:39
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
按用户指令调用 self_improvement：记录本轮 ODPS 排错与 SQL 编写要点

### Details
本轮对话中验证/沉淀的 ODPS 常见限制与修复套路：
1) 跨项目访问（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描（physical plan generation failed / full scan all partitions）；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE / DESC 在部分环境或跨 project 可能受限；可用 explore_table 或“SHOW PARTITIONS + 分区抽样 SELECT * LIMIT”反推字段。
5) 避免同一次提交混用 SET + DDL/DML（部分执行器会报 invalid statement sequence）。
6) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 执行前 checklist，并在模板 SQL 中默认包含：分区条件 + LIMIT + 正确消耗口径；遇到跨项目表先做权限检查。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, ddl-limit, multi-statement, cost-metric

---

## [LRN-20260317-389] best_practice

**Logged**: 2026-03-17T15:28:48
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
本轮ODPS排错与SQL编写要点沉淀（权限/分区/ORDER BY+LIMIT/消耗口径）

### Details
本轮对话中验证/沉淀的 ODPS 常见限制与修复套路：
1) 跨项目访问（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE / DESC 在部分环境或跨 project 可能受限；可用 explore_table 或“SHOW PARTITIONS + 分区抽样 SELECT * LIMIT”反推字段。
5) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 执行前 checklist，并在模板 SQL 中默认包含：分区条件 + LIMIT + 正确消耗口径；遇到跨项目表先做权限检查。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, ddl-limit, cost-metric

---

## [LRN-20260317-488] correction

**Logged**: 2026-03-17T15:29:17
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
self_improvement 入参纠正：entry_type 不支持 'correction'，应使用 learning/error/feature_request

### Details
刚才调用 self_improvement 时传了 entry_type='correction'，触发报错：Skill self_improvement error: 'correction'。根据 skill 参数约束，entry_type 仅支持 'learning'(默认)、'error'、'feature_request'；“纠正/修复”应放在 category='correction' 中表达。

### Suggested Action
后续调用 self_improvement：用 entry_type='learning' + category='correction'（或 entry_type='error' 记录错误类条目）；并在 Agent 层增加 entry_type 枚举校验，避免再次传入非法值。

### Metadata
- Source: error
- Related Files: 
- Tags: self_improvement, skill_args, entry_type_validation

---

## [LRN-20260317-308] best_practice

**Logged**: 2026-03-17T15:29:33
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
按用户指令调用 self_improvement：沉淀本轮 ODPS 常见限制与修复 checklist

### Details
本轮对话中验证/沉淀的 ODPS 常见限制与修复套路：
1) 跨项目访问（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描（physical plan generation failed / full scan all partitions）；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE / DESC 在部分环境或跨 project 可能受限；可用 explore_table 或“SHOW PARTITIONS + 分区抽样 SELECT * LIMIT”反推字段。
5) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 执行前 checklist，并在模板 SQL 中默认包含：分区条件 + LIMIT + 正确消耗口径；遇到跨项目表先做权限检查。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, ddl-limit, cost-metric

---

## [LRN-20260317-924] best_practice

**Logged**: 2026-03-17T15:29:41
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
按用户指令调用 self_improvement：沉淀本轮 ODPS 常见限制与修复 checklist

### Details
本轮对话中验证/沉淀的 ODPS 常见限制与修复套路：
1) 跨项目访问（如 com_cdm.*）缺少 odps:Describe/odps:Select 会报 Authorization Failed（含 User doesn't exist in the project），需目标项目管理员授权。
2) 强制分区裁剪：未写分区谓词会被拦截为全分区全表扫描；应先 SHOW PARTITIONS 再 WHERE dt/dh=...。
3) 当前环境校验：ORDER BY 必须配 LIMIT（否则提示 odps.sql.validate.orderby.limit=false）。
4) SHOW CREATE TABLE / DESC 在部分环境或跨 project 可能受限；可用 explore_table 或“SHOW PARTITIONS + 分区抽样 SELECT * LIMIT”反推字段。
5) 广告消耗口径统一使用 billing_actual_deduction_price（微美元）/1e5 转 USD，不用 cost 字段。

### Suggested Action
沉淀成 SQL 执行前 checklist，并在模板 SQL 中默认包含：分区条件 + LIMIT + 正确消耗口径；遇到跨项目表先做权限检查。

### Metadata
- Source: user_feedback
- Related Files: 
- Tags: self_improvement, odps, permission, partition, orderby-limit, ddl-limit, cost-metric

---

## [LRN-20260317-379] correction

**Logged**: 2026-03-17T15:29:54
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
self_improvement 入参修复：entry_type 不支持 'correction'，需用 learning/error/feature_request

### Details
本次调用 self_improvement 曾因 entry_type='correction' 报错（Skill self_improvement error: 'correction'）。该 skill 的 entry_type 仅支持：learning(默认)、error、feature_request；若要表达“纠正”，应使用 category='correction' 来描述。

### Suggested Action
后续统一用 entry_type='learning' + category='correction'（或 entry_type='error' 记录错误类条目）；并在调用前增加 entry_type 枚举校验，避免重复传入非法值。

### Metadata
- Source: error
- Related Files: 
- Tags: self_improvement, skill_args, entry_type_validation

---

## [LRN-20260317-063] correction

**Logged**: 2026-03-17T15:30:03
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
self_improvement 调用入参修复：entry_type 不支持 'correction'，需用 learning/error/feature_request

### Details
触发报错：Skill 'self_improvement' error: 'correction'。原因是 self_improvement 的 entry_type 枚举仅支持：learning(默认)、error、feature_request；如果想表达“纠正/修复”，应放在 category='correction' 中。

### Suggested Action
后续统一使用 entry_type='learning' + category='correction'（或 entry_type='error' 记录错误类条目）；并在调用前增加 entry_type 枚举校验与去重节流，避免重复/非法写入。

### Metadata
- Source: error
- Related Files: 
- Tags: self_improvement, skill_args, entry_type_validation, dedup

---

## [LRN-20260317-045] correction

**Logged**: 2026-03-17T15:30:13
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
修复 self_improvement 调用报错：entry_type 不支持 'correction'

### Details
last_error 显示：Skill 'self_improvement' error: 'correction'。原因是 self_improvement 的 entry_type 枚举仅支持：learning(默认)、error、feature_request；若要表达“纠正/修复”，应使用 category='correction'，而不是 entry_type='correction'。

### Suggested Action
后续调用规范：entry_type 仅用 learning/error/feature_request；“纠正/修复类条目”用 category='correction' 表达，并在调用前做枚举校验避免再次传入非法值。

### Metadata
- Source: error
- Related Files: 
- Tags: self_improvement, entry_type_validation, correction

---

## [LRN-20260317-365] correction

**Logged**: 2026-03-17T15:30:22
**Priority**: high
**Status**: pending
**Area**: odps

### Summary
self_improvement 入参纠正：entry_type 不支持 'correction'（仅支持 learning/error/feature_request）

### Details
本次触发报错：Skill 'self_improvement' error: 'correction'。原因：self_improvement 的 entry_type 枚举仅支持 learning(默认)、error、feature_request。若要表达“纠正/修复”，应使用 category='correction'，而不是 entry_type='correction'。

### Suggested Action
后续调用规范：entry_type 固定用 learning/error/feature_request；纠正类内容用 category='correction'；在 Agent 层增加 entry_type 枚举校验与同一指令去重（避免重复写入学习记录）。

### Metadata
- Source: error
- Related Files: 
- Tags: self_improvement, entry_type_validation, correction, dedup

---
