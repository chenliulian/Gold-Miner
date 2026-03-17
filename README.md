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

3. Run CLI chat mode:

```bash
gold-miner chat
```

Or directly with Python:

```bash
python -m gold_miner.cli
```

4. Example chat session:

```
🤖 GoldMiner Chat Mode
Type your question or use commands:
  /cancel - Cancel current task
  /reset  - Clear conversation history
  quit    - Exit

> 查询昨天广告投放的消耗数据
[Agent will auto-match tables and generate SQL]

> 分析贷款CVR模型的特征分布
[Agent will analyze and generate report]

> /cancel
Task cancelled.

> quit
Goodbye!
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

