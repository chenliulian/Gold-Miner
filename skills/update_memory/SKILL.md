# 更新记忆

## 名称
update_memory

## 描述
自动更新结构化记忆文件，包括表结构、指标定义、业务背景等。

## 参数
- memory_type: 记忆类型 (table_schema, metric_definition, business_background)
- key: 键 (表名/指标名/背景点)
- value: 值 (定义/描述)

## 使用场景

### 1. 更新表结构
```json
{
  "memory_type": "table_schema",
  "key": "tmp_adgroup_stats",
  "value": "ad_group_id, cost, show_cnt, clk_cnt, ctr"
}
```

### 2. 更新指标定义
```json
{
  "memory_type": "metric_definition",
  "key": "ecpm",
  "value": "每千次展示收入 = cost / show_cnt * 1000"
}
```

### 3. 更新业务背景
```json
{
  "memory_type": "business_background",
  "key": "conversion_type",
  "value": "转化类型包括: 下载、激活、付费"
}
```

## 输出
返回更新结果。

## 注意事项
- 记忆会持久化到 memory/state.json
- 可通过 search_memory 检索记忆
