# gold-miner

A lightweight, OpenClaw-style agent that analyzes data by generating and executing MaxCompute (ODPS) SQL via `pyodps`, with persistent memory and a simple skill system.

## What it does
- Uses your LLM API to plan analysis steps
- Generates and runs SQL against MaxCompute via `pyodps`
- Iteratively refines results until a final report is produced
- Persists memory across runs (summary + recent steps)
- Loads local skills to post-process results

## Quick start
1. Create a virtual environment and install:

```bash
pip install -e .
```

2. Copy and fill env:

```bash
cp .env.example .env
```

3. Run:

```bash
gold-miner analyze --question "分析过去30天的日活趋势，并给出异常峰值日期" \
  --tables user_activity \
  --output reports/dau-report.md
```

## How the agent works (high level)
- The agent asks the LLM for the next action (run SQL, use skill, or finalize).
- SQL is executed through `pyodps` and results are stored in a local cache.
- The LLM can request skills to compute statistics or format tables.
- A final report is emitted as Markdown.

## LLM API compatibility
The default client expects an OpenAI-compatible `/chat/completions` endpoint.
If your LLM API is different, modify `src/gold_miner/llm.py`.

## Skills
Skills are Python modules inside `skills/`.
Each skill exports a `SKILL` dict with `name`, `description`, `inputs`, and `run()`.

See `skills/basic_stats.py` for an example.

## Memory
Memory is stored in `memory/memory.json`. The agent summarizes older steps to keep context small.

## Project layout
```
gold-miner/
  src/gold_miner/
  skills/
  reports/
  examples/
```

## Notes
- Keep partitions in SQL predicates for performance.
- Use MAPJOIN for small dimension tables.

