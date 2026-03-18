# 表血缘关系探索

## 名称
explore_table_lineage

## 描述
通过 DataWorks 数据地图 API 获取 ODPS 表的血缘关系，追溯上游依赖表和下游引用表，帮助 Agent 深刻理解数据业务结构。

## 功能
1. **获取上游血缘**: 查找生成该表的来源表和任务
2. **获取下游血缘**: 查找引用该表的下游表和任务
3. **深度追溯**: 支持多层级血缘追溯（1层、2层、3层...）
4. **业务理解**: 通过血缘关系理解数据加工链路

## 参数
- table_name: 表名 (可以是完整名称如 mi_ads_dmp.dwd_xxx 或简短名称)
- project: 项目名 (默认: mi_ads_dmp)
- direction: 查询方向
  - UPSTREAM: 上游（来源）
  - DOWNSTREAM: 下游（去向）
  - BOTH: 双向

## 返回值
- success: 是否成功
- table_name: 完整表名
- upstream_count: 上游表数量
- downstream_count: 下游表数量
- upstream_tables: 上游表列表
- downstream_tables: 下游表列表
- summary: 血缘关系摘要（Markdown 格式）

## 使用场景
- 探索新表时了解数据来源
- 分析数据质量问题时追溯上游
- 修改表结构时评估下游影响
- 理解数据仓库的分层架构

## 使用示例
```python
# 探索上游血缘
result = run(
    table_name="com_ads.ads_tracker_ad_cpc_cost_di",
    direction="UPSTREAM",
)

# 探索双向血缘
result = run(
    table_name="mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi",
    direction="BOTH",
)
```

## 前置要求
需要在 .env 中配置 DataWorks 访问凭证：
```
DATAWORKS_ACCESS_ID=your_access_id
DATAWORKS_ACCESS_KEY=your_access_key
DATAWORKS_REGION_ID=cn-shanghai
```

或使用 ODPS 的凭证（自动兼容）：
```
ODPS_ACCESS_ID=your_access_id
ODPS_ACCESS_KEY=your_access_key
```
