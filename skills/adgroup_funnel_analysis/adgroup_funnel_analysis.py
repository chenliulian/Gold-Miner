"""
广告组投放漏斗分析 Skill

全面分析广告组投放漏斗数据，覆盖从召回、过滤、rank、响应、曝光、点击到转化的完整链路。
"""

from typing import Any, Dict, Optional


def run(
    ad_group_id: str,
    start_dh: str,
    end_dh: str,
    analysis_type: str = "full_funnel",
) -> Dict[str, Any]:
    """
    分析广告组投放漏斗数据

    参数:
        ad_group_id: 广告组ID
        start_dh: 开始时间 (格式: yyyymmddhh)
        end_dh: 结束时间 (格式: yyyymmddhh)
        analysis_type: 分析类型 (full_funnel|cost|ctr_pcoc|cvr_pcoc|win_rate)

    返回:
        包含分析结果和SQL查询的字典
    """
    
    # 基础SQL模板
    sql_templates = {
        "full_funnel": """
-- 全链路漏斗分析（使用 SUM(label) 统计，不要用 COUNT(DISTINCT)）
WITH funnel_data AS (
    SELECT 
        SUM(show_label) as show_cnt,
        SUM(click_label) as click_cnt,
        SUM(dld_label) as dld_cnt,
        SUM(conv_label_active) as conv_cnt,
        SUM(billing_actual_deduction_price) / 1e5 as total_cost
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{start_dh}' AND '{end_dh}'
    AND ad_group_id = '{ad_group_id}'
)
SELECT 
    show_cnt,
    click_cnt,
    ROUND(click_cnt * 100.0 / NULLIF(show_cnt, 0), 2) as ctr_pct,
    dld_cnt,
    conv_cnt,
    ROUND(total_cost, 2) as cost_usd
FROM funnel_data;
""",
        "cost": """
-- 消耗数据分析（使用 SUM(label) 统计）
SELECT 
    SUBSTR(dh, 1, 8) as dt,
    SUM(show_label) as show_cnt,
    SUM(click_label) as click_cnt,
    SUM(billing_actual_deduction_price) / 1e5 as total_cost,
    ROUND(SUM(billing_actual_deduction_price) / 1e5 / NULLIF(SUM(click_label), 0), 4) as cpc_usd
FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
WHERE dh BETWEEN '{start_dh}' AND '{end_dh}'
AND ad_group_id = '{ad_group_id}'
GROUP BY SUBSTR(dh, 1, 8)
ORDER BY dt;
""",
        "ctr_pcoc": """
-- CTR模型预估偏差分析（使用 SUM(label) 统计曝光和点击）
WITH ctr_stats AS (
    SELECT 
        SUM(show_label) as show_num,
        SUM(click_label) as clk_num,
        SUM(CASE WHEN show_label = 1 THEN ctr ELSE 0 END) as pctr_sum
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{start_dh}' AND '{end_dh}'
    AND ad_group_id = '{ad_group_id}'
)
SELECT 
    show_num,
    clk_num,
    ROUND(clk_num * 100.0 / NULLIF(show_num, 0), 4) as ctr_actual_pct,
    ROUND(pctr_sum * 100.0 / NULLIF(show_num, 0), 4) as pctr_pct,
    ROUND(pctr_sum / NULLIF(clk_num, 0), 4) as pcoc
FROM ctr_stats;
""",
        "cvr_pcoc": """
-- CVR模型预估偏差分析（使用 SUM(label) 统计点击和转化）
WITH cvr_stats AS (
    SELECT 
        SUM(click_label) as clk_num,
        SUM(conv_label_active) as conv_num,
        SUM(CASE WHEN click_label = 1 THEN cvr ELSE 0 END) as pcvr_sum
    FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
    WHERE dh BETWEEN '{start_dh}' AND '{end_dh}'
    AND ad_group_id = '{ad_group_id}'
)
SELECT 
    clk_num,
    conv_num,
    ROUND(conv_num * 100.0 / NULLIF(clk_num, 0), 4) as cvr_actual_pct,
    ROUND(pcvr_sum * 100.0 / NULLIF(clk_num, 0), 4) as pcvr_pct,
    ROUND(pcvr_sum / NULLIF(conv_num, 0), 4) as pcoc
FROM cvr_stats;
""",
        "win_rate": """
-- 竞胜率分析
SELECT 
    dh,
    rank_req_cnt as into_rank_cnt,
    resp_req_cnt as resp_cnt,
    (rank_req_cnt - resp_req_cnt) as cutoff_cnt,
    ROUND(resp_req_cnt * 100.0 / rank_req_cnt, 2) as win_rate
FROM ads_strategy.dwd_ads_engine_compe_suc_req_hi
WHERE dh BETWEEN '{start_dh}' AND '{end_dh}'
AND id_value = '{ad_group_id}'
AND id_type = 'ad_group_id'
ORDER BY dh;
""",
    }
    
    sql = sql_templates.get(analysis_type, sql_templates["full_funnel"]).format(
        ad_group_id=ad_group_id,
        start_dh=start_dh,
        end_dh=end_dh,
    )
    
    return {
        "success": True,
        "ad_group_id": ad_group_id,
        "analysis_type": analysis_type,
        "time_range": f"{start_dh} - {end_dh}",
        "sql": sql,
        "message": f"请执行上述SQL查询获取{analysis_type}分析结果",
        "notes": [
            "核心数据表: mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi",
            "竞胜率表: ads_strategy.dwd_ads_engine_compe_suc_req_hi",
            "消耗单位: 微美元，需除以1e5转换为美元",
            "PCOC = 1 表示准确，>1 表示高估，<1 表示低估",
        ],
    }


SKILL = {
    "name": "adgroup_funnel_analysis",
    "description": "全面分析广告组投放漏斗数据，覆盖从召回、过滤、rank、响应、曝光、点击到转化的完整链路，支持消耗分析、模型预估偏差分析",
    "inputs": {
        "ad_group_id": "str - 广告组ID",
        "start_dh": "str - 开始时间 (yyyymmddhh)",
        "end_dh": "str - 结束时间 (yyyymmddhh)",
        "analysis_type": "str (可选) - 分析类型: full_funnel|cost|ctr_pcoc|cvr_pcoc|win_rate，默认 full_funnel",
    },
    "run": run,
    "invisible_context": False,
    "hooks": [],
}
