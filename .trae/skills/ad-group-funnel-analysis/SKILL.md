---
name: "ad-group-funnel-analysis"
description: "全面分析广告组投放漏斗数据，覆盖从召回、过滤、rank、响应、曝光、点击到转化的完整链路。Invoke when user asks for ad group funnel analysis, conversion rate analysis, or troubleshooting ad delivery issues."
---

# 广告组投放漏斗分析 Skill

## 概述

本Skill用于全面分析广告组在投放过程中的漏斗转化情况，覆盖广告引擎从召回到转化的完整链路，帮助定位投放问题、优化转化效率。

## 漏斗阶段定义

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         广告组投放完整漏斗                                    │
├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────────────┤
│  召回    │  过滤   │  rank   │  响应   │  曝光   │  点击   │     转化        │
│ Recall  │ Filter  │  Rank   │ Response│  Show   │  Click  │   Conversion    │
├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────────────┤
│ 候选广告 │ 合规过滤│ 精排打分│ 胜出响应│ 用户可见│ 用户点击│ 下载/激活/注册/ │
│ 池构建   │ 预算检查│ 竞价排序│ 广告返回│ 广告展示│         │ 付费/次留等      │
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────────────┘
```

## 核心数据表

### 1. 漏斗上游（引擎侧）

| 表名 | 作用 | 核心字段 |
|------|------|----------|
| `ads_strategy.dwd_ads_engine_compe_suc_req_hi` | 竞胜率底表 | rank_req_cnt(进精排), resp_req_cnt(响应) |
| `ads_strategy.dwd_ads_competition_rank_hi` | 竞价排名底表 | rank_level(排名), bid_price(出价), win_price(成交价) |
| `ads_strategy.dwd_ads_competition_rank_simple_hi` | 简化竞价表 | success_cnt(胜出), fail_cnt(失败) |

### 2. 漏斗下游（投放侧）

| 表名 | 作用 | 核心字段 |
|------|------|----------|
| `mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi` | 曝光点击转化明细 | show_label, click_label, dld_label, conv_label_* |
| `com_cdm.dws_tracker_ad_cpc_cost_hi` | 小时汇总表 | req_num, res_num, show_cnt, click_cnt, cost |

## 分析步骤

### Step 1: 确定分析对象

```sql
-- 获取广告组基本信息
SELECT 
    ad_group_id,
    ad_group_title,
    ad_plan_id,
    advertiser_id,
    purpose_type_cn,
    transform_target_cn,
    status_v2
FROM com_cdm.dim_ad_group_dd
WHERE dt = MAX_PT('com_cdm.dim_ad_group_dd')
AND ad_group_id = '{{ad_group_id}}';
```

### Step 2: 全链路漏斗分析

```sql
-- 7层漏斗核心指标
WITH funnel_data AS (
    SELECT 
        -- 召回层（从请求采样表）
        COUNT(DISTINCT request_id) as recall_cnt,
        
        -- 过滤后进精排
        COUNT(DISTINCT CASE WHEN stage = 'RANK' THEN request_id END) as rank_cnt,
        
        -- 精排后响应
        COUNT(DISTINCT CASE WHEN stage = 'RESP' THEN request_id END) as resp_cnt,
        
        -- 响应后曝光
        COUNT(DISTINCT CASE WHEN show_label = 1 THEN request_id END) as show_cnt,
        
        -- 曝光后点击
        COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END) as click_cnt,
        
        -- 点击后下载
        COUNT(DISTINCT CASE WHEN dld_label = 1 THEN request_id END) as dld_cnt,
        
        -- 下载后转化（以激活为例）
        COUNT(DISTINCT CASE WHEN conv_label_active = 1 THEN request_id END) as conv_cnt
        
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
)
SELECT 
    recall_cnt,
    rank_cnt,
    ROUND(rank_cnt * 100.0 / recall_cnt, 2) as recall_to_rank_rate,
    resp_cnt,
    ROUND(resp_cnt * 100.0 / rank_cnt, 2) as rank_to_resp_rate,
    show_cnt,
    ROUND(show_cnt * 100.0 / resp_cnt, 2) as resp_to_show_rate,
    click_cnt,
    ROUND(click_cnt * 100.0 / show_cnt, 2) as show_to_click_rate,
    dld_cnt,
    ROUND(dld_cnt * 100.0 / click_cnt, 2) as click_to_dld_rate,
    conv_cnt,
    ROUND(conv_cnt * 100.0 / dld_cnt, 2) as dld_to_conv_rate
FROM funnel_data;
```

### Step 3: 分维度下钻分析

#### 3.1 按国家维度

```sql
-- 分国家漏斗分析
SELECT 
    country_zh,
    COUNT(DISTINCT request_id) as recall_cnt,
    COUNT(DISTINCT CASE WHEN show_label = 1 THEN request_id END) as show_cnt,
    COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END) as click_cnt,
    ROUND(COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END) * 100.0 
          / COUNT(DISTINCT CASE WHEN show_label = 1 THEN request_id END), 2) as ctr,
    COUNT(DISTINCT CASE WHEN conv_label_active = 1 THEN request_id END) as conv_cnt,
    ROUND(COUNT(DISTINCT CASE WHEN conv_label_active = 1 THEN request_id END) * 100.0 
          / COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END), 2) as cvr
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
AND ad_group_id = '{{ad_group_id}}'
GROUP BY country_zh
ORDER BY recall_cnt DESC;
```

#### 3.2 按代码位类型维度

```sql
-- 分代码位类型漏斗
SELECT 
    code_seat_type,
    COUNT(DISTINCT request_id) as recall_cnt,
    COUNT(DISTINCT CASE WHEN show_label = 1 THEN request_id END) as show_cnt,
    COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END) as click_cnt,
    ROUND(COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END) * 100.0 
          / NULLIF(COUNT(DISTINCT CASE WHEN show_label = 1 THEN request_id END), 0), 2) as ctr
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
AND ad_group_id = '{{ad_group_id}}'
GROUP BY code_seat_type
ORDER BY recall_cnt DESC;
```

#### 3.3 按设备品牌维度

```sql
-- 分品牌漏斗
SELECT 
    brand,
    COUNT(DISTINCT request_id) as recall_cnt,
    COUNT(DISTINCT CASE WHEN show_label = 1 THEN request_id END) as show_cnt,
    COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END) as click_cnt,
    ROUND(COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END) * 100.0 
          / NULLIF(COUNT(DISTINCT CASE WHEN show_label = 1 THEN request_id END), 0), 2) as ctr
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
AND ad_group_id = '{{ad_group_id}}'
GROUP BY brand
ORDER BY recall_cnt DESC
LIMIT 20;
```

### Step 4: 竞胜率分析（引擎侧）

```sql
-- 广告组竞胜率分析
SELECT 
    dh,
    id_type,
    country_name,
    busniess_line,
    code_seat_type,
    is_offline_ad,
    rank_req_cnt,
    resp_req_cnt,
    ROUND(resp_req_cnt * 100.0 / rank_req_cnt, 2) as win_rate
FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
AND id_value = '{{ad_group_id}}'
ORDER BY dh DESC;
```

### Step 5: 竞价排名分析

```sql
-- 竞价排名分布
SELECT 
    rank_level,
    COUNT(*) as cnt,
    AVG(bid_price) as avg_bid_price,
    AVG(win_price) as avg_win_price,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct
FROM ads_strategy.dwd_ads_competition_rank_hi
WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
AND ad_group_id = '{{ad_group_id}}'
GROUP BY rank_level
ORDER BY rank_level;
```

### Step 6: 异常检测

```sql
-- 漏斗异常检测
WITH daily_funnel AS (
    SELECT 
        SUBSTR(dh, 1, 8) as dt,
        COUNT(DISTINCT request_id) as recall_cnt,
        COUNT(DISTINCT CASE WHEN show_label = 1 THEN request_id END) as show_cnt,
        COUNT(DISTINCT CASE WHEN click_label = 1 THEN request_id END) as click_cnt
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
    GROUP BY SUBSTR(dh, 1, 8)
)
SELECT 
    dt,
    recall_cnt,
    show_cnt,
    click_cnt,
    ROUND(click_cnt * 100.0 / NULLIF(show_cnt, 0), 2) as ctr,
    -- 计算环比变化
    ROUND((click_cnt - LAG(click_cnt) OVER(ORDER BY dt)) * 100.0 
          / NULLIF(LAG(click_cnt) OVER(ORDER BY dt), 0), 2) as click_cnt_change_pct
FROM daily_funnel
ORDER BY dt;
```

## 诊断清单

### 召回层问题

| 症状 | 可能原因 | 检查SQL |
|------|----------|---------|
| 召回量为0 | 广告组未投放/已暂停 | 检查广告组状态 |
| 召回量骤降 | 预算耗尽/定向过窄 | 检查日预算和定向条件 |
| 召回量波动大 | 流量波动/竞价调整 | 对比历史同期数据 |

### 过滤层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| 过滤率过高 | 频控/预算/定向限制 | 检查过滤日志 |
| 进精排率低 | 粗排打分低 | 检查粗排模型得分 |

### Rank层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| 竞胜率低 | 出价过低/质量度低 | 检查bid_price和ecpm |
| 排名靠后 | 竞价竞争力不足 | 分析rank_level分布 |

### 响应层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| 响应率低 | 素材加载慢/超时 | 检查resp_ts-show_ts延迟 |
| 无响应 | 创意被下架/无效 | 检查创意状态 |

### 曝光层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| 曝光量为0 | 响应失败/缓存问题 | 检查show_label=1比例 |
| 曝光骤降 | 作弊过滤/反作弊 | 检查is_cheating标识 |

### 点击层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| CTR过低 | 素材质量差/位置不好 | 分析ctr模型打分 |
| 点击量为0 | 展示问题/素材问题 | 检查image_width/height |

### 转化层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| CVR过低 | 落地页问题/归因延迟 | 检查conv_ts-click_ts间隔 |
| 转化量为0 | 归因失败/链路断开 | 检查data_src和归因渠道 |

## 输出模板

### 漏斗概览报告

```markdown
# 广告组 {{ad_group_id}} 投放漏斗分析报告

## 基本信息
- 广告组名称: {{ad_group_title}}
- 分析时间: {{start_dh}} ~ {{end_dh}}
- 转化目标: {{transform_target_cn}}

## 漏斗总览

| 阶段 | 数量 | 转化率 | 环比变化 | 状态 |
|------|------|--------|----------|------|
| 召回 | {{recall_cnt}} | - | {{recall_change}}% | {{status}} |
| 过滤→精排 | {{rank_cnt}} | {{recall_to_rank_rate}}% | {{rank_change}}% | {{status}} |
| 精排→响应 | {{resp_cnt}} | {{rank_to_resp_rate}}% | {{resp_change}}% | {{status}} |
| 响应→曝光 | {{show_cnt}} | {{resp_to_show_rate}}% | {{show_change}}% | {{status}} |
| 曝光→点击 | {{click_cnt}} | {{show_to_click_rate}}% | {{click_change}}% | {{status}} |
| 点击→下载 | {{dld_cnt}} | {{click_to_dld_rate}}% | {{dld_change}}% | {{status}} |
| 下载→转化 | {{conv_cnt}} | {{dld_to_conv_rate}}% | {{conv_change}}% | {{status}} |

## 关键发现
1. {{finding_1}}
2. {{finding_2}}
3. {{finding_3}}

## 优化建议
1. {{suggestion_1}}
2. {{suggestion_2}}
3. {{suggestion_3}}

## 详细数据
{{detailed_data}}
```

## 使用示例

### 示例1: 基础漏斗分析

```
用户: 帮我分析广告组 12345 在 2025031000 到 2025031023 的投放漏斗

Agent: 
1. 首先获取广告组基本信息
2. 执行7层漏斗分析SQL
3. 分国家、代码位类型、品牌下钻
4. 生成漏斗报告
```

### 示例2: 问题诊断

```
用户: 广告组 67890 最近点击量突然下降，帮我排查原因

Agent:
1. 对比近7天和上周同期数据
2. 逐层检查漏斗转化率变化
3. 定位问题环节（如曝光→点击CTR下降）
4. 下钻分析国家/代码位/品牌维度
5. 给出可能原因和优化建议
```

### 示例3: 竞胜率优化

```
用户: 广告组 11111 竞胜率很低，怎么优化

Agent:
1. 分析竞胜率底表数据
2. 查看竞价排名分布
3. 对比同行业出价水平
4. 分析质量度(ecpm)情况
5. 给出出价策略建议
```

## 注意事项

1. **时间对齐**: 引擎侧表和投放侧表的分区时间可能有时区差异，需要统一转换
2. **去重逻辑**: 曝光、点击、转化数据都有去重逻辑，分析时需保持一致
3. **归因窗口**: 转化数据可能有归因延迟，短期数据可能不完整
4. **作弊过滤**: 分析时应考虑is_cheating标识，区分正常和作弊流量
5. **离线广告**: is_offline_ad=1为离线广告，与在线广告分开分析

## 相关表关联关系

```
dwd_ads_engine_compe_suc_req_hi (竞胜率)
    ↓ id_value = ad_group_id
dwd_ads_competition_rank_hi (竞价排名)
    ↓ ad_group_id
dwd_ew_ads_show_res_clk_dld_conv_hi (曝光点击转化)
    ↓ ad_group_id
dws_tracker_ad_cpc_cost_hi (小时汇总)
```
