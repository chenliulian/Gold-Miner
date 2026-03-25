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

- **Default Project**: `mi_ads_dmp_dev`
- **Cross-Project Access**: Can access tables from other projects (`com_ads`, `mi_ads_dmp`, etc.)
- **Full Table Names**: Use `project_name.table_name` format for cross-project tables

See main prompts for detailed cross-project access rules.

## Agent Behavior

- **Self-Correction**: When errors occur, analyze and retry with fixed SQL
- **Proactive**: Use skills automatically when appropriate
- **Transparent**: Show progress and reasoning to users
- **Learning**: Record learnings and errors for improvement
- **Try First**: Always attempt to execute SQL before assuming permission issues

## Skills Integration

Skills are modular capabilities that can be called:

- `build_adgroup_data`: Build intermediate aggregation table with show/click/download/conversion data
- `calc_summary_stats`: Calculate summary metrics like cost/CTR/CVR/eCPM
- `analyze_ctr_pcoc`: CTR bias analysis (PCOC) at adgroup or pkg_buz level
- `analyze_cvr_pcoc`: CVR bias analysis (PCOC), supports cpi/ocpc/ocpi conv types
- `calc_model_mae`: Model MAE calculation (requires analyze_ctr_pcoc and analyze_cvr_pcoc first)
- `explore_table`: Explore table structure, field types, partitions, and sample data
- `basic_stats`: Summarize the latest query result
- `tavily_search`: Search web for documentation
- `self_improvement`: Log learnings, errors, corrections to .learnings/ for continuous improvement

For complete skill descriptions and parameters, see the main prompts.
