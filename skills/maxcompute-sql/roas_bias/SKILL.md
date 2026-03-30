# ROAS偏差分析 Skill

## 描述
计算ROAS模型的预估偏差，通过对比模型预估LTV与实际变现LTV的差异，评估模型准确性。

## 功能
1. 计算单天或多天激活的ROAS模型预估偏差
2. 支持按广告组维度统计偏差
3. 计算加权平均偏差（按消耗加权）

## 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| start_dt | string | 是 | - | 开始日期，格式：yyyyMMdd |
| end_dt | string | 否 | start_dt | 结束日期，格式：yyyyMMdd（默认等于开始日期） |
| output_table | string | 否 | 自动生成 | 输出表名 |

## 输出结果

### 明细表字段
- `ad_group_id`: 广告组ID
- `pltv_raw`: 原始预估LTV总和
- `pltv`: 模型预估LTV总和
- `ltv`: 实际变现LTV总和（7日）
- `cost`: 消耗（美元）
- `bias_ltv`: LTV偏差率 (实际LTV/预估LTV - 1)
- `roi7`: 7日ROI
- `bias_ltv_raw`: 原始LTV偏差率
- `abs_bias`: 绝对偏差（消耗*|偏差率|）

### 汇总指标
- `total_cost`: 总消耗
- `weighted_bias`: 加权平均偏差（按消耗加权）
- `total_adgroups`: 广告组数量

## 计算逻辑

### 数据来源
1. **响应数据**: `com_cdm.dwd_log_dsp_adserver_response_hi`
   - 获取模型预估LTV（ltv, ltv_raw）
   - 过滤条件：cost_type='7', roas_ltv_model_name like '%roas_%'

2. **激活数据**: `com_cdm.dwd_eagllwin_conv_log_hi`
   - 获取激活事件（trans_event_type in ('2','激活')）
   - 往前多取10天数据防止丢失

3. **收入数据**: `com_cdm.dws_eagllwin_deep_conv_income_hi`
   - 获取实际变现收入
   - 收入日期范围：激活日期到激活后7天

### 偏差计算
```
bias_ltv = 实际LTV / 预估LTV - 1
weighted_bias = Σ(消耗 × |偏差率|) / Σ(消耗)
```

## 使用示例

```python
# 计算单天偏差
result = run(
    start_dt="20260325",
)

# 计算多天偏差
result = run(
    start_dt="20260320",
    end_dt="20260325",
)
```

## 注意事项
- 激活与响应数据join时往前多join 10天数据，防止数据丢失
- 只统计cost_type='7'（OCPI）的数据
- 排除降级模型（downgrade_roas_ltv）
- 实际LTV统计激活后7天内的收入

## 依赖表
- `com_cdm.dwd_log_dsp_adserver_response_hi`
- `com_cdm.dwd_eagllwin_conv_log_hi`
- `com_cdm.dws_eagllwin_deep_conv_income_hi`
