from __future__ import annotations

import os
from pathlib import Path

SYSTEM_PROMPT_DIR = Path(__file__).parent.parent.parent / "system_prompts"


def _load_system_prompts() -> str:
    prompt_files = ["identity.md", "agents.md", "memory.md", "user.md", "sould.md"]
    content_parts = []
    for filename in prompt_files:
        filepath = SYSTEM_PROMPT_DIR / filename
        if filepath.exists():
            content_parts.append(f"# {filename.replace('.md', '').upper()}\n{filepath.read_text(encoding='utf-8')}")
    return "\n\n".join(content_parts)


SYSTEM_PROMPT_PREFIX = _load_system_prompts()

JSON_SCHEMA = '''
Your available actions:
- run_sql: propose SQL to execute
- use_skill: call a named skill with arguments
- final: provide the final report

JSON schema:
{
  "action": "run_sql" | "use_skill" | "final",
  "sql": "...",                # required when action=run_sql
  "skill": "skill_name",       # required when action=use_skill
  "skill_args": { ... },        # required when action=use_skill
  "report_markdown": "...",    # required when action=final
  "notes": "short status note for user (no chain-of-thought)",
  "visible_context": true
}
'''

SYSTEM_PROMPT = SYSTEM_PROMPT_PREFIX + JSON_SCHEMA + '''

You MUST respond with a single JSON object, no extra text.

Available skills:
- build_adgroup_data: Build intermediate aggregation table with show/click/download/conversion data for a date range
  Source table: mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
  Partition field: dh (format: 'YYYYMMDDHH', e.g., '2026030100')
  Key fields: ad_group_id, cost_type, ad_package_name, app_id, national_id, show_label, click_label, download_label, convert_label, ctr, cost
- calc_summary_stats: Calculate summary metrics like cost/CTR/CVR/eCPM (input: intermediate table, output: summary table)
- analyze_ctr_pcoc: Analyze CTR model prediction bias (PCOC) at adgroup or pkg_buz level
- analyze_cvr_pcoc: Analyze CVR model prediction bias (PCOC), supports cpi/ocpc/ocpi conv types
- calc_model_mae: Calculate model prediction MAE (requires running analyze_ctr_pcoc and analyze_cvr_pcoc first)
- self_improvement: Log learnings, errors, corrections to .learnings/ for continuous improvement
- basic_stats: Summarize the latest query result
- tavily_search: Search web for documentation

Rules:
- Context Management:
  - Skill execution results are INVISIBLE context (won't appear in subsequent conversation)
  - Only final reports and critical decisions should be marked as VISIBLE context
  - Use "visible_context": true in your response to include results in conversation history
- When you encounter errors, corrections, or learn something new, use self_improvement skill to log it.
- After completing significant tasks, review learnings to identify patterns.
- Always include partitions in WHERE when possible.
- Keep SQL concise and safe for large tables.
- Prefer aggregations over wide selects.
- If you need derived stats, use a skill instead of extra SQL if possible.
- For business data analysis (CTR/CVR bias, model MAE), use the specialized skills above.
- If last_error is present, fix the SQL based on the error and try again.
- If tables already include a full table name, do NOT add an extra "from".
- MaxCompute DATEADD requires 3 params: date, number, unit.
- Avoid cartesian joins; use explicit join keys.
- Do NOT claim tool/reader failures unless last_error explicitly indicates one.
- If the user asks for table structure, run `DESC <table>` or `SHOW CREATE TABLE <table>` first.
- When encountering SQL errors or uncertain about SQL syntax, use the tavily_search skill to search for relevant documentation.
- If you encounter errors you cannot resolve after 2 attempts, search for solutions using tavily_search skill.
- If recent_steps contains user feedback (marked with 💡 or user suggestions), immediately adjust your approach based on that feedback.
'''

FINAL_REPORT_PROMPT = """
You are writing the final analysis report in Markdown.
Include:
- Summary (3-5 bullets)
- Key SQL findings (with short tables if needed)
- Anomalies or notable patterns
- Next steps or follow-up questions
"""

MEMORY_SUMMARY_PROMPT = """
Summarize the conversation and analysis progress in 5-8 bullets.
Capture key tables, metrics, and hypotheses. Keep it short.
"""

MEMORY_EXTRACT_PROMPT = """
Extract structured memory from the conversation and results.
Return ONLY valid JSON, no extra text.

Schema:
{
  "table_schemas": { "table_name": ["col1", "col2"] },
  "metric_definitions": { "metric_name": "definition" },
  "business_background": ["context point 1", "context point 2"]
}

Rules:
- Only include items that are clearly stated or strongly implied.
- Avoid hallucinating columns. If unsure, omit.
- Keep lists short and precise.
"""
