# Agents

GoldMiner uses a multi-agent system to handle different tasks.

## Main Agent (SqlAgent)

The primary agent that coordinates all tasks:

1. **Understand User Intent**: Parse user questions and determine the best approach
2. **Plan Execution**: Decide whether to run SQL, use skills, or generate reports
3. **Execute Actions**: Run SQL queries, call skills, handle errors
4. **Iterate**: Continuously improve results based on feedback
5. **Finalize**: Generate comprehensive reports

## ODPS Project Access

- **Default Project**: The default ODPS project is `mi_ads_dmp_dev`
- **Cross-Project Access**: The agent CAN access tables from other projects like `com_ads`, `mi_ads_dmp`, etc.
- **Permission**: Do NOT assume permission denied for cross-project tables. Always try to execute SQL first.
- **Full Table Names**: When accessing tables from other projects, use the full table name format: `project_name.table_name`

## Agent Behavior

- **Self-Correction**: When errors occur, analyze and retry with fixed SQL
- **Proactive**: Use skills automatically when appropriate
- **Transparent**: Show progress and reasoning to users
- **Learning**: Record learnings and errors for improvement
- **Try First**: Always attempt to execute SQL before assuming permission issues

## Skills Integration

Skills are modular capabilities that can be called:

- `build_adgroup_data`: Build aggregation tables
- `analyze_ctr_pcoc`: CTR bias analysis
- `analyze_cvr_pcoc`: CVR bias analysis
- `calc_summary_stats`: Summary statistics
- `calc_model_mae`: Model MAE calculation
- `basic_stats`: Quick data overview
- `tavily_search`: Web search
- `feishu_notify`: Send notifications
- `self_improvement`: Record learnings
