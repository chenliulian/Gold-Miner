# LTV数据分析 Skill

## 描述
LTV模型效果监控数据分析工具，用于分析OCPI广告账户的ROI表现。

## 功能
1. **全部OCPI账户统计**：计算固定日期当天全部OCPI账户的总消耗及整体ROI（全部数据，不限制消耗）
2. **联运游戏客户统计**：输出联运游戏客户（MI_游戏_联运开头）的整体消耗及平均ROI，CPI和OCPI分别统计（全部数据，不限制消耗）
3. **高消耗Group明细**：输出消耗>=100的group明细数据（包括消耗和ROI），按消耗降序排列

## 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| dt | string | 是 | - | 分析日期，格式：yyyyMMdd |
| min_cost_threshold | float | 否 | 100.0 | Group最小消耗阈值（美元） |
| output_table | string | 否 | 自动生成 | 输出明细表名 |

## 输出结果

### 1. OCPI整体统计 (`ocpi_overall`)
- `adgroup_cnt`: 广告组数量
- `total_cost`: 总消耗（美元）
- `total_income`: 总收入（美元）
- `overall_roi`: 整体ROI（收入/消耗）

### 2. 联运游戏统计 (`lianyun_game`)
- `ocpi`: OCPI类型联运游戏统计
  - `adgroup_cnt`: 广告组数量
  - `total_cost`: 总消耗（美元）
  - `total_income`: 总收入（美元）
  - `avg_roi`: 平均ROI
- `cpi`: CPI类型联运游戏统计
  - `adgroup_cnt`: 广告组数量
  - `total_cost`: 总消耗（美元）
  - `total_income`: 总收入（美元）
  - `avg_roi`: 平均ROI

### 3. 明细表字段
- `ad_group_id`: 广告组ID
- `ad_group_title`: 广告组名称
- `cost`: 消耗（美元）
- `income`: 收入（美元）
- `roi`: ROI（收入/消耗）
- `show_num`: 展现数
- `click_cnt`: 点击数
- `dt`: 日期

## 使用示例

```python
result = run(
    dt="20260325",
    min_cost_threshold=100.0,
)
```

## 注意事项
- 本Skill仅分析OCPI计费类型（cost_type='ocpi'）的明细数据
- 联运游戏定义为广告组名称以"MI_游戏_联运"开头的账户（不区分大小写）
- 整体统计包含全部数据，不限制消耗金额
- 明细数据仅包含消耗>=min_cost_threshold的group
- 消耗字段使用cpi_cost
- 收入字段使用income
- ROI计算方式：收入/消耗

## 依赖表
- `com_cdm.dws_tracker_ad_cpc_cost_hi`
