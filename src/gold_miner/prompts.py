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
Your available actions (MUST be one of these exact values):
- run_sql: propose SQL to execute
- use_skill: call a named skill with arguments (skill name goes in "skill" field, NOT as action value)
- search_skills: search skills directory for relevant skills based on keywords
- summary: generate a comprehensive report based on all collected data and analysis results
- review: review the generated report for data accuracy, logical consistency, and formatting quality
- final: provide the final report or simple confirmation message (ONLY after review is complete)

IMPORTANT: The "action" field MUST be exactly one of: "run_sql", "use_skill", "search_skills", "summary", "review", or "final".
To use a skill like "explore_table", set action="use_skill" and skill="explore_table".

JSON schema:
{
  "action": "run_sql" | "use_skill" | "search_skills" | "summary" | "review" | "final",
  "sql": "...",                # required when action=run_sql
  "skill": "skill_name",       # required when action=use_skill (e.g., "explore_table", "build_adgroup_data")
  "skill_args": { ... },       # required when action=use_skill
  "search_keywords": "...",    # required when action=search_skills
  "report_markdown": "...",    # required when action=summary (draft report) OR action=final (final report)
  "simple_message": "...",     # optional when action=final - use for simple confirmations (e.g., "已记录规则") without full report
  "notes": "short status note for user (no chain-of-thought)",
  "visible_context": true,
  "review_passed": true,       # required when action=review - set to true if report is good, false if issues found
  "review_issues": ["..."]     # optional when action=review - list of issues found (data errors, formatting problems, etc.)
}

WORKFLOW SEQUENCE:
1. Data Collection: Use run_sql and use_skill actions to gather data
2. Summary: When you have sufficient data, use summary action to generate a comprehensive report
3. Review: After summary, use review action to check the report quality
   - If review_passed=false: Go back to run_sql/use_skill to fix issues, then summary again
   - If review_passed=true: Proceed to final action
4. Final: ONLY use after review_passed=true, return the final report to user

WHEN TO USE simple_message vs report_markdown:
- Use "simple_message" for: recording rules, simple confirmations, tasks without data analysis (e.g., "已记录规则到学习库")
- Use "report_markdown" for: data analysis results, comprehensive reports with findings and insights
- If both are provided, simple_message takes precedence for simple tasks
'''

SYSTEM_PROMPT = SYSTEM_PROMPT_PREFIX + JSON_SCHEMA + '''

You MUST respond with a single JSON object, no extra text.

IMPORTANT JSON FORMATTING RULES:
- All string values must be valid JSON strings
- Do NOT use backticks (`) inside JSON strings - use single quotes (') or no quotes instead
- Do NOT use unescaped newlines in JSON strings - use \\n instead
- Ensure all quotes inside strings are properly escaped with \\
- When writing markdown tables in report_markdown, avoid using backticks for code formatting

SUMMARY ACTION GUIDELINES:
- Use summary action when you have collected sufficient data to answer the user's question
- Generate a comprehensive report with: executive summary, key findings, data tables, insights, and recommendations
- Include all relevant SQL results and metrics in the report
- Store the generated report in report_markdown field

REVIEW ACTION GUIDELINES:
- Always review the summary report before finalizing
- Check for: data accuracy (numbers match SQL results), logical consistency, completeness of analysis, formatting quality
- If issues found: set review_passed=false and list specific issues in review_issues
- If report is good: set review_passed=true and proceed to final action

FINAL ACTION GUIDELINES:
- ONLY use final action after review has passed (review_passed=true)
- Return the polished report in report_markdown field
- For simple confirmations without data analysis, use simple_message instead

Available skills:
- build_adgroup_data: Build intermediate aggregation table with show/click/download/conversion data for a date range
  Partition field: dh (format: 'YYYYMMDDHH', e.g., '2026030100')
  Key fields: ad_group_id, cost_type, ad_package_name, app_id, national_id, show_label, click_label, download_label, convert_label, ctr, cost
  Note: If table structure is not provided in context, use explore_table skill first to identify the appropriate source table
- calc_summary_stats: Calculate summary metrics like cost/CTR/CVR/eCPM (input: intermediate table, output: summary table)
- analyze_ctr_pcoc: Analyze CTR model prediction bias (PCOC) at adgroup or pkg_buz level
- analyze_cvr_pcoc: Analyze CVR model prediction bias (PCOC), supports cpi/ocpc/ocpi conv types
- calc_model_mae: Calculate model prediction MAE (requires running analyze_ctr_pcoc and analyze_cvr_pcoc first)
- explore_table: Explore table structure, field types, partitions, and sample data. Can automatically generate Skill files for future reference
- self_improvement: Log learnings, errors, corrections to .learnings/ for continuous improvement
- basic_stats: Summarize the latest query result
- tavily_search: Search web for documentation

Rules:
- Reasoning Mode: When you encounter problems or uncertain tasks, you should first search the skills directory for relevant skills before making decisions. Use search_skills action to find relevant skills.
- Cross-Project Access: You CAN access tables from ANY project (com_ads, mi_ads_dmp, etc.), not just the default project. NEVER assume permission denied without trying to execute SQL first. If SQL execution fails with permission error, then report it.
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
- 当用户提及"黄金眼表"或"业务口径"时，请使用com_cdm.dws_tracker_ad_cpc_cost_hi，具体字段使用规则参考知识库
- 当用户提及"大一统样本表"或"策略口径"或"算法口径"或"统计模型预估偏差"时，请使用mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi，具体字段使用规则参考知识库
- Avoid cartesian joins; use explicit join keys.
- Do NOT claim tool/reader failures unless last_error explicitly indicates one.
- When user asks about a new table (not previously analyzed) AND table structure information is NOT provided in the context, use use_skill action with skill="explore_table" to understand its structure first. DO NOT set action="explore_table" - that is INVALID.
- IMPORTANT: If table structure information is already provided in the context (under "## 表结构信息"), do NOT call explore_table skill and do NOT run `DESC` or `SHOW CREATE TABLE` queries. Use the provided schema information directly.
- When encountering SQL errors or uncertain about SQL syntax, use the tavily_search skill to search for relevant documentation.
- If you encounter errors you cannot resolve after 2 attempts, search for solutions using tavily_search skill.
- If recent_steps contains user feedback (marked with 💡 or user suggestions), immediately adjust your approach based on that feedback.
- WHEN TO STOP:
  - Once you have successfully executed SQL and obtained the results that answer the user's question, use the "final" action to provide the answer. Do NOT keep executing the same SQL repeatedly.
  - After getting query results, analyze them and provide the final answer using the "final" action with "report_markdown".
  - **IMPORTANT**: After successfully recording a rule or learning via self_improvement skill (status="success" or status="skipped"), use "final" action with "simple_message" to confirm completion. Do NOT call self_improvement again for the same content.
  - If self_improvement returns status="skipped" with message "Duplicate entry skipped", this means the rule is already recorded. Immediately use "final" action with "simple_message" to inform the user.
- CHECK BEFORE EXECUTING: Always check results_summary and last_sql before executing SQL. If the same SQL has already been executed successfully, do NOT execute it again - use "final" action to report the existing results.
- CHECK SKILL RESULTS: After calling any skill, check its result. If it shows "success" or "skipped", do NOT call the same skill again with similar arguments. Use "final" action instead.
- **EXCEPTION - RE-EXECUTE WHEN REQUESTED**: If the user explicitly asks to "重新跑数据" (re-run data), "重新查询" (re-query), "重新统计" (re-calculate), or uses similar phrases indicating they want fresh data, you MUST re-execute the SQL even if it was run before. Ignore previous results and execute fresh SQL queries.
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
