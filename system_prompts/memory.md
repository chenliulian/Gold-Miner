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

### 3. Learning Memory
- Stored in `.learnings/LEARNINGS.md`
- Records successful patterns
- Stored in `.learnings/ERRORS.md`
- Records errors and corrections

## Memory Management

- **Automatic summarization**: When conversation exceeds length limits
- **Selective retrieval**: Only relevant memory is passed to LLM
- **Invisible context**: Skill execution results don't pollute conversation
- **Visible context**: Only important decisions appear in history

## Best Practices

- Use `self_improvement` skill to record learnings
- Review learnings periodically
- Keep memory organized and concise
