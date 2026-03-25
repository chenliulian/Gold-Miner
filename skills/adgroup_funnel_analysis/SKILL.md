# 广告组投放漏斗分析

## 名称
adgroup_funnel_analysis

## 描述
全面分析广告组投放漏斗数据，覆盖从召回、过滤、rank、响应、曝光、点击到转化的完整链路，支持消耗分析、模型预估偏差分析。Invoke when user asks for ad group funnel analysis, conversion rate analysis, cost analysis, model bias analysis, or troubleshooting ad delivery issues.

## 概述

本Skill用于全面分析广告组在投放过程中的漏斗转化情况，覆盖广告引擎从召回到转化的完整链路，包含消耗数据分析、CTR/CVR模型预估偏差分析、召回响应率分析、过滤项分布分析等，帮助定位投放问题、优化转化效率。

## 广告引擎架构说明

广告引擎采用分层架构：召回层 → 过滤层 → 粗排层 → 精排层 → 预算控制 → 响应层 → 曝光 → 点击/转化 → 消耗。

详细架构知识请参考知识库：`knowledge/glossary/ad_engine_architecture.yaml`

## 核心数据表

### 1. 漏斗上游（引擎侧）

| 表名 | 作用 | 核心字段 |
|------|------|----------|
| `ads_strategy.dwd_ads_engine_compe_suc_req_hi` | 竞胜率底表 | rank_req_cnt(进精排), resp_req_cnt(响应) |
| `ads_strategy.dwd_ads_competition_rank_hi` | 竞价排名底表 | rank_level(排名), bid_price(出价), win_price(成交价) |
| `ads_strategy.dwd_ads_competition_rank_simple_hi` | 简化竞价表 | success_cnt(胜出), fail_cnt(失败) |
| `ads_strategy.dwd_ew_request_sample_hi` | 请求采样表 | stage(阶段), request_id(请求ID) | **无访问权限，不建议使用** |

### 2. 漏斗下游（投放侧）- 曝光及之后数据

| 表名 | 作用 | 核心字段 | 数据逻辑 |
|------|------|----------|---------|
| `mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi` | **曝光后漏斗分析主表** - 包含曝光、点击、下载、转化数据 | show_label, click_label, dld_label, conv_label_*, ctr, cvr, billing_actual_deduction_price (该表专用字段) | 曝光 left join 点击 left join 转化，保留request_id粒度。注意：**该表只包含曝光及之后的数据，不包含曝光前的召回/精排/响应数据** |
| `com_cdm.dws_tracker_ad_cpc_cost_hi` | **业务数据汇总表** - 业务视角统计 | req_num, res_num, show_cnt, click_cnt, cost, cpm_cost, cpc_cost | 曝光 union 点击 union 转化后聚合统计，用于业务数据看数，**不适合模型偏差分析** |

**重要说明**:
- **曝光后漏斗分析（曝光→点击→下载→转化）**: 使用 `dwd_ew_ads_show_res_clk_dld_conv_hi`，统计时使用 `SUM(show_label)`, `SUM(click_label)`, `SUM(dld_label)`，**不要使用 COUNT(DISTINCT request_id)**
- **曝光前漏斗分析（召回→精排→响应）**: 使用 `ads_strategy.dwd_ads_engine_compe_suc_req_hi` 竞胜率表
- **完整漏斗分析**: 需要联合使用曝光前表 + 曝光后表
- **业务数据查看/消耗统计**: 使用 `dws_tracker_ad_cpc_cost_hi`，该表是业务侧常用的汇总表
- **消耗波动归因**: 若需从模型预估偏差维度解释，必须基于 `dwd_ew_ads_show_res_clk_dld_conv_hi` 计算PCOC指标

## 关键指标定义

### 漏斗转化率指标

| 指标名称 | 计算公式 | 说明 |
|---------|---------|------|
| 召回率 | 召回数 / 总请求数 | 广告被召回的比例 |
| 过滤通过率 | 进精排数 / 召回数 | 通过过滤进入精排的比例 |
| 竞胜率 | 响应数 / (响应数 + 截断数) | 精排竞争中胜出的比例 |
| 召回响应率 | 响应数 / 召回数 | 从召回到响应的整体转化率 |
| 响应曝光率 | 曝光数 / 响应数 | 响应后成功曝光的比例 |
| 点击率(CTR) | 点击数 / 曝光数 | 曝光后被点击的比例 |
| 下载率 | 下载数 / 点击数 | 点击后下载的比例 |
| 转化率(CVR) | 转化数 / 点击数 | 点击后转化的比例 |

### 模型预估偏差指标 (PCOC)

| 指标名称 | 计算公式 | 说明 |
|---------|---------|------|
| CTR PCOC | pCTR / 实际CTR | =1准确, >1高估, <1低估 |
| CVR PCOC | pCVR / 实际CVR | =1准确, >1高估, <1低估 |
| 绝对偏差 | \|PCOC - 1\| | 偏差程度，越小越好 |

### 消耗指标

| 指标名称 | 计算公式 | 说明 |
|---------|---------|------|
| 实际扣费 | SUM(billing_actual_deduction_price) / 1e5 | 单位：美元（该表专用字段） |
| 平均点击成本 | 总扣费 / 点击数 | CPC |
| 平均千次曝光成本 | 总扣费 / 曝光数 * 1000 | CPM |
| 平均转化成本 | 总扣费 / 转化数 | CPA |

### 计费类型 (cost_type)

| cost_type | 计费模式 | 计费逻辑 | 适用场景 |
|-----------|---------|---------|---------|
| 1 | CPM | bid_price 直接按曝光计费 | 品牌曝光 |
| 2 | CPC | bid_price 按点击计费 | 点击引流 |
| 3 | OCPC | bid_price × pCVR 按点击计费 | 智能点击优化 |
| 4 | CPD | bid_price 按下载计费 | 下载量目标 |
| 5 | OCPD | bid_price × pDCVR 按下载计费 | 智能下载优化 |
| 6 | CPI | bid_price 按激活计费 | 激活量目标 |
| 7 | OCPI | bid_price × LTV打分 按激活计费 | 智能价值优化 |

**计费公式详解**:
- **CPM**: 实际扣费 = bid_price (每千次曝光)
- **CPC**: 实际扣费 = bid_price (每次点击)
- **OCPC**: 实际扣费 = bid_price × pCVR (每次点击，考虑转化概率)
- **CPD**: 实际扣费 = bid_price (每次下载)
- **OCPD**: 实际扣费 = bid_price × pDCVR (每次下载，考虑下载转化概率)
- **CPI**: 实际扣费 = bid_price (每次激活)
- **OCPI**: 实际扣费 = bid_price × LTV (每次激活，考虑用户价值)

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

**注意**: `dwd_ew_ads_show_res_clk_dld_conv_hi` 表只包含曝光及之后的数据，曝光前数据（召回/精排/响应）需要从竞胜率表获取。

```sql
-- 曝光后漏斗核心指标（使用 SUM(label) 统计，不要用 COUNT(DISTINCT)）
WITH show_funnel AS (
    SELECT 
        -- 曝光数
        SUM(show_label) as show_cnt,
        -- 点击数
        SUM(click_label) as click_cnt,
        -- 下载数
        SUM(dld_label) as dld_cnt,
        -- 转化数（以激活为例）
        SUM(conv_label_active) as conv_cnt,
        -- 消耗数据
        SUM(billing_actual_deduction_price) / 1e5 as total_cost
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
),
-- 曝光前漏斗数据（从竞胜率表获取）
engine_funnel AS (
    SELECT 
        SUM(rank_req_cnt) as rank_req_cnt,  -- 进精排数
        SUM(resp_req_cnt) as resp_req_cnt   -- 响应数
    FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND id_type = 'ad_group_id'
    AND id_value = '{{ad_group_id}}'
)
SELECT 
    -- 曝光前漏斗
    e.rank_req_cnt,
    e.resp_req_cnt,
    (e.rank_req_cnt - e.resp_req_cnt) as cutoff_cnt,
    ROUND(e.resp_req_cnt * 100.0 / NULLIF(e.rank_req_cnt, 0), 2) as win_rate,
    -- 曝光后漏斗
    s.show_cnt,
    s.click_cnt,
    s.dld_cnt,
    s.conv_cnt,
    ROUND(s.click_cnt * 100.0 / NULLIF(s.show_cnt, 0), 2) as ctr_pct,
    ROUND(s.dld_cnt * 100.0 / NULLIF(s.click_cnt, 0), 2) as dld_rate_pct,
    ROUND(s.conv_cnt * 100.0 / NULLIF(s.dld_cnt, 0), 2) as conv_rate_pct,
    -- 消耗指标
    ROUND(s.total_cost, 2) as total_cost_usd,
    ROUND(s.total_cost / NULLIF(s.click_cnt, 0), 4) as cpc_usd,
    ROUND(s.total_cost / NULLIF(s.show_cnt, 0) * 1000, 4) as cpm_usd,
    ROUND(s.total_cost / NULLIF(s.conv_cnt, 0), 4) as cpa_usd
FROM show_funnel s
CROSS JOIN engine_funnel e;
```

### Step 3: 召回率与响应率分析

**注意**: `ads_strategy.dwd_ew_request_sample_hi` 表当前无访问权限，建议使用以下替代方案：

#### 方案1：基于竞胜率表分析（推荐）

```sql
-- 使用竞胜率表分析召回响应链路
WITH compete_stats AS (
    SELECT 
        SUBSTR(dh, 1, 8) as dt,
        -- 进精排数
        SUM(rank_req_cnt) as rank_cnt,
        -- 响应数
        SUM(resp_req_cnt) as resp_cnt,
        -- 截断数
        SUM(rank_req_cnt - resp_req_cnt) as cutoff_cnt
    FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND id_value = '{{ad_group_id}}'
    AND id_type = 'ad_group_id'
    GROUP BY SUBSTR(dh, 1, 8)
)
SELECT 
    dt,
    rank_cnt,
    resp_cnt,
    cutoff_cnt,
    -- 过滤通过率 = 进精排数 / (进精排数 + 截断数) [假设召回≈进精排+截断]
    ROUND(rank_cnt * 100.0 / NULLIF(rank_cnt + cutoff_cnt, 0), 2) as filter_pass_rate,
    -- 竞胜率 = 响应数 / 进精排数
    ROUND(resp_cnt * 100.0 / NULLIF(rank_cnt, 0), 2) as win_rate,
    -- 整体召回响应率 = 响应数 / (进精排数 + 截断数)
    ROUND(resp_cnt * 100.0 / NULLIF(rank_cnt + cutoff_cnt, 0), 2) as recall_to_resp_rate
FROM compete_stats
ORDER BY dt;
```

#### 方案2：基于创意维度流量漏斗表分析

```sql
-- 使用创意维度流量漏斗表分析
WITH filter_stats AS (
    SELECT 
        SUBSTR(dh, 1, 8) as dt,
        -- 召回数
        SUM(recall) as recall_cnt,
        -- SSP返回数
        SUM(ssp_res_succ_cnt) as ssp_resp_cnt,
        -- 各过滤项统计
        SUM(mem_shield) as mem_shield_cnt,
        SUM(ctr_filter) as ctr_filt_cnt,
        SUM(cvr_filter) as cvr_filt_cnt,
        SUM(budget_filter) as budget_filt_cnt,
        SUM(cnt_limit) as cnt_limit_cnt,
        SUM(frequency_control) as freq_filt_cnt,
        SUM(floor_price_filter) as floor_filt_cnt
    FROM com_ads.ads_creativity_filter_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
    AND is_offline_ad = 0
    GROUP BY SUBSTR(dh, 1, 8)
)
SELECT 
    dt,
    recall_cnt,
    ssp_resp_cnt,
    -- SSP响应率
    ROUND(ssp_resp_cnt * 100.0 / NULLIF(recall_cnt, 0), 2) as ssp_resp_rate,
    -- 主要过滤项占比
    ROUND(cnt_limit_cnt * 100.0 / NULLIF(recall_cnt, 0), 2) as cnt_limit_pct,
    ROUND(floor_filt_cnt * 100.0 / NULLIF(recall_cnt, 0), 2) as floor_filt_pct
FROM filter_stats
ORDER BY dt;
```

### Step 3.5: 全链路漏斗分析（三表关联）

**完整示例**：使用 FULL OUTER JOIN 关联三张核心表，构建从召回到转化的完整漏斗

```sql
-- 全链路漏斗分析：召回表 + 竞胜率表 + 曝光转化表
SELECT 
   COALESCE(r.dt, e.dt, p.dt) AS dt, 
   COALESCE(r.ad_group_id, e.ad_group_id, p.ad_group_id) AS ad_group_id, 
 
   -- 召回层指标
   r.recall_cnt, 
   r.recall_resp_cnt, 
   
   -- 引擎层指标
   e.engine_rank_req_cnt, 
   e.engine_resp_req_cnt, 
 
   -- 曝光转化层指标
   p.post_show_cnt, 
   p.post_click_cnt, 
   p.post_dld_cnt, 
   p.post_conv_active_cnt, 
   p.post_conv_register_cnt, 
   p.post_conv_pay_cnt, 
   p.post_cost_usd, 
 
   -- 漏斗转化率
   ROUND(r.recall_resp_cnt * 1.0 / NULLIF(r.recall_cnt, 0), 6) AS recall_to_resp_rate, 
   ROUND(e.engine_resp_req_cnt * 1.0 / NULLIF(e.engine_rank_req_cnt, 0), 6) AS rank_to_resp_win_rate, 
   ROUND(p.post_show_cnt * 1.0 / NULLIF(e.engine_resp_req_cnt, 0), 6) AS resp_to_show_rate, 
 
   -- 效果指标
   ROUND(p.post_click_cnt * 1.0 / NULLIF(p.post_show_cnt, 0), 6) AS ctr, 
   ROUND(p.post_dld_cnt * 1.0 / NULLIF(p.post_click_cnt, 0), 6) AS click_to_dld_rate, 
   ROUND(p.post_conv_active_cnt * 1.0 / NULLIF(p.post_click_cnt, 0), 6) AS click_to_active_cvr, 
 
   -- 成本指标
   ROUND(p.post_cost_usd * 1.0 / NULLIF(p.post_click_cnt, 0), 6) AS cpc_usd, 
   ROUND(p.post_cost_usd * 1000.0 / NULLIF(p.post_show_cnt, 0), 6) AS cpm_usd, 
   ROUND(p.post_cost_usd * 1.0 / NULLIF(p.post_conv_active_cnt, 0), 6) AS cpa_active_usd 
 FROM 
 (
   -- 召回层数据（ads_creativity_filter_hi）
   SELECT 
     SUBSTR(dh,1,8) AS dt, 
     CAST(ad_group_id AS BIGINT) AS ad_group_id, 
     SUM(recall) AS recall_cnt, 
     SUM(resp) AS recall_resp_cnt 
   FROM com_ads.ads_creativity_filter_hi 
   WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}' 
     AND CAST(ad_group_id AS STRING) = '{{ad_group_id}}' 
     AND is_offline_ad = 0 
   GROUP BY SUBSTR(dh,1,8), CAST(ad_group_id AS BIGINT) 
 ) r 
 FULL OUTER JOIN 
 (
   -- 引擎层数据（dwd_ads_engine_compe_suc_req_hi）
   SELECT 
     SUBSTR(dh,1,8) AS dt, 
     CAST(id_value AS BIGINT) AS ad_group_id, 
     SUM(rank_req_cnt) AS engine_rank_req_cnt, 
     SUM(resp_req_cnt) AS engine_resp_req_cnt 
   FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi 
   WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}' 
     AND id_type = 'ad_group_id' 
     AND id_value = '{{ad_group_id}}' 
   GROUP BY SUBSTR(dh,1,8), CAST(id_value AS BIGINT) 
 ) e 
 ON r.dt = e.dt AND r.ad_group_id = e.ad_group_id 
 FULL OUTER JOIN 
 (
   -- 曝光转化层数据（dwd_ew_ads_show_res_clk_dld_conv_hi）
   SELECT 
     SUBSTR(dh,1,8) AS dt, 
     CAST(ad_group_id AS BIGINT) AS ad_group_id, 
     SUM(show_label) AS post_show_cnt, 
     SUM(click_label) AS post_click_cnt, 
     SUM(dld_label) AS post_dld_cnt, 
     SUM(conv_label_active) AS post_conv_active_cnt, 
     SUM(conv_label_register) AS post_conv_register_cnt, 
     SUM(conv_label_pay) AS post_conv_pay_cnt, 
     SUM(billing_actual_deduction_price) / 1e5 AS post_cost_usd 
   FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 
   WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}' 
     AND CAST(ad_group_id AS STRING) = '{{ad_group_id}}' 
   GROUP BY SUBSTR(dh,1,8), CAST(ad_group_id AS BIGINT) 
 ) p 
 ON COALESCE(r.dt, e.dt) = p.dt 
 AND COALESCE(r.ad_group_id, e.ad_group_id) = p.ad_group_id
 ORDER BY dt
 LIMIT 100;
```

**三表关联说明**：

| 子查询 | 表名 | 数据层 | 核心指标 |
|--------|------|--------|----------|
| r | ads_creativity_filter_hi | 召回层 | recall_cnt, recall_resp_cnt |
| e | dwd_ads_engine_compe_suc_req_hi | 引擎层 | engine_rank_req_cnt, engine_resp_req_cnt |
| p | dwd_ew_ads_show_res_clk_dld_conv_hi | 曝光转化层 | post_show_cnt, post_click_cnt, post_conv_*, post_cost_usd |

**关联技巧**：
- 使用 `FULL OUTER JOIN` 确保各层数据都能被保留（即使某层缺失数据）
- 使用 `COALESCE(r.dt, e.dt, p.dt)` 处理可能的 NULL 值
- 注意 `ad_group_id` 类型转换：`CAST(ad_group_id AS STRING)` 用于 WHERE 条件，`CAST(ad_group_id AS BIGINT)` 用于 GROUP BY

### Step 4: 过滤项分布分析

**注意**: 过滤项分布分析需要访问引擎侧的过滤日志表。目前主要通过以下方式分析过滤情况：

#### 4.1 基于创意维度流量漏斗表的召回过滤分析（推荐）

```sql
-- 召回数据查询（ads_creativity_filter_hi 创意维度流量漏斗统计小时表）
SELECT  advertiser_id
       ,account_name
       ,brief_name
       ,ad_group_id
       ,null as ad_group_title
       ,app_id
       ,app_name
       ,code_seat_id
       ,SUM(recall) AS recall -- 召回数
       ,SUM(ssp_res_succ_cnt) AS ssp_res_succ_cnt -- ssp返回广告数
       ,SUBSTR(dh,1,8) AS dt
FROM    com_ads.ads_creativity_filter_hi
WHERE   dh >= '${startdt}00'
AND     dh <= '${enddt}23'
AND     is_offline_ad = 0
GROUP BY advertiser_id
         ,account_name
         ,brief_name
         ,ad_group_id
         ,app_id
         ,app_name
         ,code_seat_id
         ,SUBSTR(dh,1,8);

-- 过滤器过滤数据查询（ads_dsp_req_filter_hi DSP请求过滤小时表）
SELECT  ad_group_id
       ,app_id
       ,code_seat_id
       ,filter_type -- 过滤器类型
       ,SUM(cnt) AS filt_cnt -- 过滤数
       ,SUBSTR(dh,1,8) AS dt
FROM    com_ads.ads_dsp_req_filter_hi
WHERE   dh >= '${startdt}00'
AND     dh <= '${enddt}23'
AND     filter_type != 'RESP' -- 排除响应类型
GROUP BY ad_group_id
         ,app_id
         ,code_seat_id
         ,filter_type
         ,SUBSTR(dh,1,8);
```

**关键字段说明**:
- `recall`: 召回数，广告被召回的请求数
- `ssp_res_succ_cnt`: SSP返回广告数
- `filter_type`: 过滤器类型（如 AbnormalAdsFilter, BrandAdsFilter, AdBlockFilter 等）
- `filt_cnt`: 被过滤的请求数

#### 4.2 基于竞胜率表的过滤分析

```sql
-- 通过竞胜率表分析过滤情况
-- 截断数 = 进精排数 - 响应数
WITH filter_analysis AS (
    SELECT 
        dh,
        country_name,
        busniess_line,
        code_seat_type,
        rank_req_cnt as into_rank_cnt,  -- 进精排数
        resp_req_cnt as resp_cnt,       -- 响应数
        (rank_req_cnt - resp_req_cnt) as cutoff_cnt,  -- 截断数
        ROUND(resp_req_cnt * 100.0 / NULLIF(rank_req_cnt, 0), 2) as win_rate,
        ROUND((rank_req_cnt - resp_req_cnt) * 100.0 / NULLIF(rank_req_cnt, 0), 2) as cutoff_rate
    FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND id_value = '{{ad_group_id}}'
    AND id_type = 'ad_group_id'
)
SELECT 
    dh,
    country_name,
    busniess_line,
    code_seat_type,
    into_rank_cnt,
    resp_cnt,
    cutoff_cnt,
    win_rate,
    cutoff_rate,
    CASE 
        WHEN cutoff_rate >= 50 THEN '高截断率-需优化'
        WHEN cutoff_rate >= 30 THEN '中等截断率'
        ELSE '正常截断率'
    END as cutoff_level
FROM filter_analysis
ORDER BY dh DESC, cutoff_cnt DESC;
```

#### 4.3 基于竞价排名表的过滤分析

```sql
-- 通过竞价排名表分析各阶段转化
WITH rank_analysis AS (
    SELECT 
        SUBSTR(dh, 1, 8) as dt,
        -- 进入排名阶段（cnt_limit + RESP）
        COUNT(DISTINCT CASE WHEN stage IN ('RESP', 'cnt_limit') THEN request_id END) as rank_stage_cnt,
        -- 成功响应（RESP）
        COUNT(DISTINCT CASE WHEN stage = 'RESP' THEN request_id END) as resp_cnt,
        -- 截断数（cnt_limit）
        COUNT(DISTINCT CASE WHEN stage = 'cnt_limit' THEN request_id END) as cnt_limit_cnt,
        -- 各排名位次分布
        COUNT(DISTINCT CASE WHEN stage = 'RESP' AND stage_rank = 0 THEN request_id END) as rank1_cnt,
        COUNT(DISTINCT CASE WHEN stage = 'RESP' AND stage_rank = 1 THEN request_id END) as rank2_cnt,
        COUNT(DISTINCT CASE WHEN stage = 'RESP' AND stage_rank = 2 THEN request_id END) as rank3_cnt
    FROM ads_strategy.dwd_ads_competition_rank_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
    GROUP BY SUBSTR(dh, 1, 8)
)
SELECT 
    dt,
    rank_stage_cnt,
    resp_cnt,
    cnt_limit_cnt,
    ROUND(resp_cnt * 100.0 / NULLIF(rank_stage_cnt, 0), 2) as win_rate,
    ROUND(cnt_limit_cnt * 100.0 / NULLIF(rank_stage_cnt, 0), 2) as cnt_limit_rate,
    rank1_cnt,
    rank2_cnt,
    rank3_cnt,
    -- 排名分布占比
    ROUND(rank1_cnt * 100.0 / NULLIF(resp_cnt, 0), 2) as rank1_pct
FROM rank_analysis
ORDER BY dt;
```

#### 4.4 过滤原因诊断清单

| 过滤表现 | 可能原因 | 检查指标 | 优化建议 |
|---------|---------|---------|---------|
| cnt_limit截断率高 | 召回数量限制/竞争激烈 | rank_stage_cnt, cnt_limit_cnt | 提高eCPM竞争力 |
| 竞胜率低 | 出价过低/质量度低 | win_rate, bid_price | 优化出价策略 |
| 排名靠后 | 竞价竞争力不足 | rank1_cnt, rank2_cnt | 提升ecpm或调整定向 |
| 进精排数少 | 粗排过滤/预算限制 | into_rank_cnt | 检查预算和定向设置 |

**说明**: 
- `cnt_limit` 表示在精排阶段因排名限制被截断的请求
- 竞胜率 = 响应数 / 进精排数
- 截断率 = 100% - 竞胜率

### Step 5: 竞胜率详细分析

```sql
-- 竞胜率详细分析
WITH compete_stats AS (
    SELECT 
        dh,
        id_type,
        country_name,
        busniess_line,
        code_seat_type,
        is_offline_ad,
        rank_req_cnt,
        resp_req_cnt,
        -- 截断数 = 进精排数 - 响应数
        (rank_req_cnt - resp_req_cnt) as cutoff_cnt,
        -- 竞胜率 = 响应数 / 进精排数
        ROUND(resp_req_cnt * 100.0 / NULLIF(rank_req_cnt, 0), 2) as win_rate
    FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND id_value = '{{ad_group_id}}'
)
SELECT 
    dh,
    country_name,
    code_seat_type,
    is_offline_ad,
    rank_req_cnt,
    resp_req_cnt,
    cutoff_cnt,
    win_rate,
    -- 竞胜状态评估
    CASE 
        WHEN win_rate >= 80 THEN '优秀'
        WHEN win_rate >= 60 THEN '良好'
        WHEN win_rate >= 40 THEN '一般'
        ELSE '较差'
    END as win_rate_level
FROM compete_stats
ORDER BY dh DESC, win_rate ASC;
```

### Step 6: 消耗数据分析

```sql
-- 消耗数据分析（使用 SUM(label) 统计，不要用 COUNT(DISTINCT)）
WITH cost_stats AS (
    SELECT 
        SUBSTR(dh, 1, 8) as dt,
        -- 曝光数
        SUM(show_label) as show_cnt,
        -- 点击数
        SUM(click_label) as click_cnt,
        -- 转化数（以激活为例）
        SUM(conv_label_active) as conv_cnt,
        -- 总消耗（美元）
        SUM(billing_actual_deduction_price) / 1e5 as total_cost,
        -- 平均eCPM
        AVG(ecpm) / 1e5 as avg_ecpm,
        -- 平均出价
        AVG(first_price) as avg_bid_price
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
    GROUP BY SUBSTR(dh, 1, 8)
)
SELECT 
    dt,
    show_cnt,
    click_cnt,
    conv_cnt,
    ROUND(total_cost, 2) as total_cost_usd,
    ROUND(total_cost * 7.2, 2) as total_cost_cny,  -- 假设汇率7.2
    ROUND(total_cost / NULLIF(click_cnt, 0), 4) as cpc_usd,
    ROUND(total_cost / NULLIF(show_cnt, 0) * 1000, 4) as cpm_usd,
    ROUND(total_cost / NULLIF(conv_cnt, 0), 4) as cpa_usd,
    ROUND(avg_ecpm, 4) as avg_ecpm_usd,
    ROUND(avg_bid_price, 2) as avg_bid_price
FROM cost_stats
ORDER BY dt;
```

### Step 7: CTR模型预估偏差分析 (PCOC)

```sql
-- CTR模型预估偏差分析（使用 SUM(label) 统计曝光和点击）
WITH ctr_stats AS (
    SELECT 
        SUBSTR(dh, 1, 8) as dt,
        -- 曝光数
        SUM(show_label) as show_num,
        -- 点击数
        SUM(click_label) as clk_num,
        -- 原始pCTR求和（只对曝光样本求和）
        SUM(CASE WHEN show_label = 1 THEN ctr_raw ELSE 0 END) as pctr_raw_sum,
        -- 校准后pCTR求和
        SUM(CASE WHEN show_label = 1 THEN ctr ELSE 0 END) as pctr_sum
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
    GROUP BY SUBSTR(dh, 1, 8)
)
SELECT 
    dt,
    show_num,
    clk_num,
    -- 实际CTR
    ROUND(clk_num * 100.0 / NULLIF(show_num, 0), 4) as ctr_actual_pct,
    -- 原始预估CTR
    ROUND(pctr_raw_sum * 100.0 / NULLIF(show_num, 0), 4) as pctr_raw_pct,
    -- 校准后预估CTR
    ROUND(pctr_sum * 100.0 / NULLIF(show_num, 0), 4) as pctr_pct,
    -- 原始PCOC
    ROUND(pctr_raw_sum / NULLIF(clk_num, 0), 4) as pcoc_raw,
    -- 校准后PCOC
    ROUND(pctr_sum / NULLIF(clk_num, 0), 4) as pcoc,
    -- 绝对偏差
    ROUND(ABS(pctr_sum / NULLIF(clk_num, 0) - 1), 4) as abs_error,
    -- 偏差方向
    CASE 
        WHEN pctr_sum / NULLIF(clk_num, 0) > 1.2 THEN '严重高估'
        WHEN pctr_sum / NULLIF(clk_num, 0) > 1.05 THEN '轻度高估'
        WHEN pctr_sum / NULLIF(clk_num, 0) BETWEEN 0.95 AND 1.05 THEN '准确'
        WHEN pctr_sum / NULLIF(clk_num, 0) < 0.8 THEN '严重低估'
        ELSE '轻度低估'
    END as bias_direction
FROM ctr_stats
ORDER BY dt;
```

### Step 8: CVR模型预估偏差分析 (PCOC)

```sql
-- CVR模型预估偏差分析（使用 SUM(label) 统计点击和转化）
WITH cvr_stats AS (
    SELECT 
        SUBSTR(dh, 1, 8) as dt,
        transform_target_cn,
        -- 点击数
        SUM(click_label) as clk_num,
        -- 转化数（根据转化目标动态选择，使用 SUM 统计）
        SUM(CASE 
            WHEN transform_target_cn LIKE '%激活%' THEN conv_label_active
            WHEN transform_target_cn LIKE '%注册%' THEN conv_label_register
            WHEN transform_target_cn = '付费' THEN conv_label_pay
            WHEN transform_target_cn = '首次付费' THEN conv_label_first_pay
            ELSE 0 
        END) as conv_num,
        -- 原始pCVR求和（只对点击样本求和）
        SUM(CASE WHEN click_label = 1 THEN cvr_raw ELSE 0 END) as pcvr_raw_sum,
        -- 校准后pCVR求和
        SUM(CASE WHEN click_label = 1 THEN cvr ELSE 0 END) as pcvr_sum
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
    GROUP BY SUBSTR(dh, 1, 8), transform_target_cn
)
SELECT 
    dt,
    transform_target_cn,
    clk_num,
    conv_num,
    -- 实际CVR
    ROUND(conv_num * 100.0 / NULLIF(clk_num, 0), 4) as cvr_actual_pct,
    -- 原始预估CVR
    ROUND(pcvr_raw_sum * 100.0 / NULLIF(clk_num, 0), 4) as pcvr_raw_pct,
    -- 校准后预估CVR
    ROUND(pcvr_sum * 100.0 / NULLIF(clk_num, 0), 4) as pcvr_pct,
    -- 原始PCOC
    ROUND(pcvr_raw_sum / NULLIF(conv_num, 0), 4) as pcoc_raw,
    -- 校准后PCOC
    ROUND(pcvr_sum / NULLIF(conv_num, 0), 4) as pcoc,
    -- 绝对偏差
    ROUND(ABS(pcvr_sum / NULLIF(conv_num, 0) - 1), 4) as abs_error,
    -- 偏差方向
    CASE 
        WHEN pcvr_sum / NULLIF(conv_num, 0) > 1.2 THEN '严重高估'
        WHEN pcvr_sum / NULLIF(conv_num, 0) > 1.05 THEN '轻度高估'
        WHEN pcvr_sum / NULLIF(conv_num, 0) BETWEEN 0.95 AND 1.05 THEN '准确'
        WHEN pcvr_sum / NULLIF(conv_num, 0) < 0.8 THEN '严重低估'
        ELSE '轻度低估'
    END as bias_direction
FROM cvr_stats
WHERE conv_num > 0  -- 只显示有转化的记录
ORDER BY dt, transform_target_cn;
```

### Step 9: 分维度下钻分析

#### 9.1 按国家维度

```sql
-- 分国家漏斗分析（使用 SUM(label) 统计）
SELECT 
    country_zh,
    SUM(show_label) as show_cnt,
    SUM(click_label) as click_cnt,
    ROUND(SUM(click_label) * 100.0 / NULLIF(SUM(show_label), 0), 2) as ctr,
    SUM(conv_label_active) as conv_cnt,
    ROUND(SUM(conv_label_active) * 100.0 / NULLIF(SUM(click_label), 0), 2) as cvr,
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
AND ad_group_id = '{{ad_group_id}}'
GROUP BY country_zh
ORDER BY show_cnt DESC;
```

#### 9.2 按代码位类型维度

```sql
-- 分代码位类型漏斗（使用 SUM(label) 统计）
SELECT 
    code_seat_type,
    SUM(show_label) as show_cnt,
    SUM(click_label) as click_cnt,
    ROUND(SUM(click_label) * 100.0 / NULLIF(SUM(show_label), 0), 2) as ctr,
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
AND ad_group_id = '{{ad_group_id}}'
GROUP BY code_seat_type
ORDER BY show_cnt DESC;
```

#### 9.3 按业务线维度

```sql
-- 分业务线漏斗（使用 SUM(label) 统计）
SELECT 
    busniess_line,
    SUM(show_label) as show_cnt,
    SUM(click_label) as click_cnt,
    ROUND(SUM(click_label) * 100.0 / NULLIF(SUM(show_label), 0), 2) as ctr,
    SUM(conv_label_active) as conv_cnt,
    ROUND(SUM(conv_label_active) * 100.0 / NULLIF(SUM(click_label), 0), 2) as cvr,
    SUM(billing_actual_deduction_price) / 1e5 as cost_usd
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
AND ad_group_id = '{{ad_group_id}}'
GROUP BY busniess_line
ORDER BY show_cnt DESC;
```

### Step 10: 竞价排名分析

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

### Step 11: 异常检测

```sql
-- 漏斗异常检测（使用 SUM(label) 统计）
WITH daily_funnel AS (
    SELECT 
        SUBSTR(dh, 1, 8) as dt,
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(billing_actual_deduction_price) / 1e5 as cost_usd
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{{start_dh}}' AND '{{end_dh}}'
    AND ad_group_id = '{{ad_group_id}}'
    GROUP BY SUBSTR(dh, 1, 8)
)
SELECT 
    dt,
    show_cnt,
    click_cnt,
    ROUND(cost_usd, 2) as cost_usd,
    ROUND(click_cnt * 100.0 / NULLIF(show_cnt, 0), 2) as ctr,
    -- 环比变化
    ROUND((click_cnt - LAG(click_cnt) OVER(ORDER BY dt)) * 100.0 
          / NULLIF(LAG(click_cnt) OVER(ORDER BY dt), 0), 2) as click_cnt_change_pct,
    ROUND((cost_usd - LAG(cost_usd) OVER(ORDER BY dt)) * 100.0 
          / NULLIF(LAG(cost_usd) OVER(ORDER BY dt), 0), 2) as cost_change_pct
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

### 过滤层问题（8大过滤器）

广告引擎过滤器位于召回层之后、精排层之前，包含8个过滤器链：

| 过滤器 | 过滤依据 | 影响指标 |
|--------|---------|---------|
| AbnormalAdsFilter | 异常参竞率 | 广告主/计划/广告组级概率过滤 |
| BrandAdsFilter | SDK版本兼容性 | 低版本SDK的品牌广告过滤 |
| AdBlockFilter | 用户屏蔽历史 | 创意/广告主/行业/Eagllwin屏蔽 |
| MaterialReverseExpFilter | 素材属性组合 | 素材类型/生成方式/自动化类型 |
| IconRmDupFilter | 广告组/包名去重 | Icon广告位去重（已注释） |
| PackExcludeFilter | 广告组排除配置 | 特定用户排除 |
| ShieldRuleFilter | 关键词屏蔽 | 标题/文案敏感词过滤 |
| ExcludeReactiveFilter | 安装时效性 | 拉活场景防重复 |

**常见过滤问题诊断**:

| 症状 | 可能原因 | 检查点 | 优化建议 |
|------|---------|--------|---------|
| 过滤率过高 | AbnormalAdsFilter参竞率低 | 检查广告主/计划/广告组参竞率配置 | 调整partiRate参数 |
| 进精排率低 | 粗排打分低或预算限制 | 检查粗排模型得分和日预算 | 优化定向或提高预算 |
| cnt_limit截断多 | 召回数量限制/竞争激烈 | rank_stage_cnt, cnt_limit_cnt | 提高eCPM竞争力 |
| 竞胜率低 | 出价过低/质量度低 | win_rate, bid_price | 优化出价策略 |
| 品牌广告被过滤 | SDK版本不支持OM SDK | 检查SDK版本和广告配置 | 升级SDK或调整广告 |
| 特定用户无曝光 | PackExcludeFilter排除 | 检查包排除配置 | 调整排除策略 |
| 素材被过滤 | MaterialReverseExpFilter实验 | 检查素材属性配置 | 调整素材类型或实验策略 |
| 拉活效果差 | ExcludeReactiveFilter过滤 | 检查安装间隔配置 | 调整时间间隔策略 |

### Rank层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| 竞胜率低 | 出价过低/质量度低 | 检查bid_price和ecpm |
| 排名靠后 | 竞价竞争力不足 | 分析rank_level分布 |
| 响应率低 | 素材加载慢/超时 | 检查resp_ts-show_ts延迟 |

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
| CTR PCOC偏差大 | 模型预估不准 | 分析PCOC值 |

### 转化层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| CVR过低 | 落地页问题/归因延迟 | 检查conv_ts-click_ts间隔 |
| 转化量为0 | 归因失败/链路断开 | 检查data_src和归因渠道 |
| CVR PCOC偏差大 | 转化模型预估不准 | 分析CVR PCOC值 |

### 消耗层问题

| 症状 | 可能原因 | 检查点 |
|------|----------|--------|
| 成本过高 | 出价过高/竞争激烈 | 检查CPC/CPM趋势 |
| 消耗骤降 | 预算限制/投放暂停 | 检查日预算和状态 |
| 无消耗 | 未产生点击/扣费异常 | 检查billing_actual_deduction_price |

## 使用示例

### 示例1: 基础漏斗分析

```
用户: 帮我分析广告组 12345 在 2025031000 到 2025031023 的投放漏斗

Agent: 
1. 首先获取广告组基本信息
2. 执行7层漏斗分析SQL
3. 分析消耗数据
4. 分析CTR/CVR PCOC偏差
5. 分国家、代码位类型、品牌下钻
6. 生成漏斗报告
```

### 示例2: 问题诊断

```
用户: 广告组 67890 最近点击量突然下降，帮我排查原因

Agent:
1. 对比近7天和上周同期数据
2. 逐层检查漏斗转化率变化
3. 分析过滤项分布
4. 检查竞胜率变化
5. 分析CTR PCOC偏差
6. 下钻分析国家/代码位/品牌维度
7. 给出可能原因和优化建议
```

### 示例3: 竞胜率优化

```
用户: 广告组 11111 竞胜率很低，怎么优化

Agent:
1. 分析竞胜率底表数据
2. 查看竞价排名分布
3. 分析过滤项分布（cnt_limit/low_ecpm_filter等）
4. 对比同行业出价水平
5. 分析质量度(ecpm)情况
6. 给出出价策略和过滤优化建议
```

### 示例4: 模型偏差分析

```
用户: 广告组 22222 的CTR预估好像不准，分析一下

Agent:
1. 计算CTR PCOC（预估CTR/实际CTR）
2. 分析原始PCOC和校准后PCOC
3. 判断高估还是低估
4. 分维度分析偏差（国家/代码位类型/品牌）
5. 给出模型优化或出价调整建议
```

## 注意事项

1. **时间对齐**: 引擎侧表和投放侧表的分区时间可能有时区差异，需要统一转换
2. **去重逻辑**: 曝光、点击、转化数据都有去重逻辑，分析时需保持一致
3. **归因窗口**: 转化数据可能有归因延迟，短期数据可能不完整
4. **作弊过滤**: 分析时应考虑is_cheating标识，区分正常和作弊流量
5. **离线广告**: is_offline_ad=1为离线广告，与在线广告分开分析
6. **单位转换**: 消耗字段（如billing_actual_deduction_price）和ecpm单位是微美元，需除以1e5转换为美元
7. **PCOC解读**: PCOC=1表示准确，>1表示高估，<1表示低估，偏差在±5%内可接受
8. **竞胜率计算**: 竞胜率 = 响应数 / (响应数 + 截断数)，不是简单的响应数/进精排数
9. **过滤器影响**: 8大过滤器会影响广告进入精排的比例，分析过滤率时需考虑各过滤器配置
10. **过滤器顺序**: 过滤器按固定顺序执行，前面的过滤器过滤的广告不会进入后续过滤器
11. **概率过滤**: AbnormalAdsFilter使用概率控制，同一广告组不同请求可能有不同结果
12. **用户级过滤**: AdBlockFilter和ExcludeReactiveFilter基于GAID，不同用户过滤结果不同
13. **实验过滤**: MaterialReverseExpFilter用于AB测试，可能影响特定素材的曝光
14. **表选择原则**: 
    - 漏斗分析/模型偏差分析 → `dwd_ew_ads_show_res_clk_dld_conv_hi` (严格left join链路)
    - 业务数据查看/消耗统计 → `dws_tracker_ad_cpc_cost_hi` (union后聚合)
15. **消耗归因分析**: 若消耗波动需从CTR/CVR模型偏差维度归因，必须使用`dwd_ew_ads_show_res_clk_dld_conv_hi`计算PCOC，不能用`dws_tracker_ad_cpc_cost_hi`

## 相关表关联关系

```
【召回层】
dim_ad_group_dd (广告组维度表)
    ↓ ad_group_id
dim_creativity_dd (创意维度表)
    ↓ launch_group_id = ad_group_id
    
【过滤层 - 8大过滤器】
过滤器配置表:
- AdsPartiRateDetails (AbnormalAdsFilter配置)
- PackExcludeDetails (PackExcludeFilter配置)
- AppEffectiveShieldRuleCollection (ShieldRuleFilter)
- CodeSeatEffectiveShieldRuleCollection (ShieldRuleFilter)
- IconGroupUniqueKeyDetails (IconRmDupFilter)

用户数据表:
- adBlockRepo (AdBlockFilter屏蔽信息)
- ewInstallRedissonClient (ExcludeReactiveFilter安装数据)

【精排/Rank层】
dwd_ads_engine_compe_suc_req_hi (竞胜率底表)
    ↓ id_value = ad_group_id
    - rank_req_cnt: 进精排请求数
    - resp_req_cnt: 响应请求数
    
dwd_ads_competition_rank_hi (竞价排名底表)
    ↓ ad_group_id
    - stage: 'RESP'/'cnt_limit'
    - stage_rank: 排名位次(0=第1名)
    - bid_price: 出价
    - win_price: 成交价
    
dwd_ads_competition_rank_simple_hi (简化竞价表)
    ↓ ad_group_id

【曝光点击转化层】
dwd_ew_ads_show_res_clk_dld_conv_hi (曝光点击转化明细)
    ↓ ad_group_id
    - show_label: 曝光标签
    - click_label: 点击标签
    - dld_label: 下载标签
    - conv_label_*: 各类转化标签
    - ctr/ctr_raw: 预估CTR
    - cvr/cvr_raw: 预估CVR
    - billing_actual_deduction_price: 实际扣费(微美元，该表专用字段)
    - ecpm/ecpm_raw: eCPM(微美元)
    
dws_tracker_ad_cpc_cost_hi (小时汇总表)
    ↓ ad_group_id
    - req_num: 请求数
    - res_num: 响应数
    - show_cnt: 曝光数
    - click_cnt: 点击数
    - cost: 消耗
```

## 过滤器执行流程

详细过滤器链说明请参考知识库：`knowledge/glossary/ad_engine_architecture.yaml`

过滤器执行顺序：AbnormalAdsFilter → BrandAdsFilter → AdBlockFilter → MaterialReverseExpFilter → IconRmDupFilter → PackExcludeFilter → ShieldRuleFilter → ExcludeReactiveFilter
