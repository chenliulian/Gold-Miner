# Memory

GoldMiner maintains different types of memory for context awareness.

## Memory Types

### 1. Conversation History
- Recent dialogue steps stored in `memory/`
- Can be summarized when too long
- Used to maintain context across sessions

### 2. Structured Memory
- Table schemas: Known table structures
- Metric definitions: Business metric definitions
- Business background: Domain knowledge
- **How to update**: Use `update_memory` skill when user says "记住/保存"

### 3. Learning Memory
- Stored in `.learnings/LEARNINGS.md`
- Records successful patterns, code corrections, errors
- **How to update**: Use `self_improvement` skill for code/behavior learnings

## Skill Usage Guide

### When to use `update_memory` skill:
- User says: "记住这个表结构" → `update_memory` with `memory_type="table_schema"`
- User says: "保存这个指标定义" → `update_memory` with `memory_type="metric_definition"`
- User says: "记住这个业务背景" → `update_memory` with `memory_type="business_background"`
- User says: "记下来" (关于表/指标/业务) → `update_memory`

### When to use `self_improvement` skill:
- Code corrections or bug fixes
- Errors encountered during execution
- New patterns or best practices discovered
- Knowledge gaps identified

## Memory Management

- **Automatic summarization**: When conversation exceeds length limits
- **Selective retrieval**: Only relevant memory is passed to LLM
- **Invisible context**: Skill execution results don't pollute conversation
- **Visible context**: Only important decisions appear in history

## Best Practices

- Use `update_memory` skill when user explicitly asks to remember table/metric/business info
- Use `self_improvement` skill to record code learnings and errors
- Review learnings periodically
- Keep memory organized and concise
