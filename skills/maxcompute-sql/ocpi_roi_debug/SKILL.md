# OCPI客户ROI异常排查 Skill

## 描述
针对OCPI客户某日ROI不符合预期的原因进行排查定位，通过分析App分布、消耗趋势、模型校准系数等因素，定位ROI异常的根本原因。

## 功能
1. **App维度分析**：从响应表分析app_id维度的消耗分布
2. **消耗趋势回溯**：检查各App消耗是否近期明显上涨
3. **模型校准系数查询**：获取模型打分校准系数，判断是否存在打分高估
4. **校准系数趋势分析**：查看校准系数近期变化趋势

## 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| ad_group_id | string/int | 是 | - | 广告组ID |
| dt | string | 是 | - | 分析日期，格式：yyyyMMdd |
| model_name | string | 否 | 'roas_v1' | 模型名称 |

## 排查步骤

### 第一步：App维度分析
- 查询表：`com_cdm.dwd_log_dsp_adserver_response_hi`
- 按`app_id`统计消耗分布
- 识别主要App（消耗占比>50%）

### 第二步：消耗趋势回溯
- 回溯前7天各App消耗数据
- 检测消耗是否近期明显上涨

### 第三步：Package映射
- 从响应表获取主要`app_id`对应的`package_name`
- 用于后续校准系数查询

### 第四步：模型校准系数查询
- 查询表：`ads_strategy.dwd_eagllwin_ad_group_model_package_ltv_calibrate_mysql_dh`
- 输入：ad_group_id, package_name, model_name
- 输出：5段校准系数

**校准系数解读：**
- < 0.8：不会造成大幅打分高估
- 0.8 - 1.1：影响较小
- > 1.1：可能存在风险，打分高估
- 明显 > 1.1：确认是校准导致的模型打分高估

### 第五步：校准系数趋势分析
- 扩大时间范围至一周
- 检查校准系数近期变化趋势

## 输出结果

### 1. App分布分析
- 各App的消耗占比
- 识别主要App（消耗>50%）

### 2. 消耗趋势分析
- 目标日期前7天各App消耗趋势
- 消耗是否明显上涨

### 3. Package信息
- app_id
- package_name

### 4. 模型校准系数
- 当前5段校准系数值
- 风险等级评估

### 5. 校准系数趋势
- 近7天校准系数变化
- 是否明显上升

## 使用示例

```python
result = run(
    ad_group_id=54225,
    dt="20260320",
    model_name="roas_v1",
)
```

## 排查结论

根据以上分析，输出可能的原因：
1. **App集中度过高**：消耗集中在特定App
2. **App消耗上涨**：特定App近期消耗明显上涨，打分变高
3. **校准系数过高**：校准系数>1.1，存在打分高估风险
4. **校准系数上升**：近期校准系数明显上升，导致模型异常

## 依赖表
- `com_cdm.dwd_log_dsp_adserver_response_hi` - 响应数据（含app_id, package_name, cost）
- `ads_strategy.dwd_eagllwin_ad_group_model_package_ltv_calibrate_mysql_dh` - 校准系数表
