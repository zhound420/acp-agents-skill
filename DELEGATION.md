# Delegation Protocol — When Mordecai Calls Kimi

## The Rule

**I do:** Judgment, context, relationship, orchestration, quality control, final delivery
**Kimi does:** Heavy lifting, research, drafting, analysis, bulk work

## When to Delegate

| Task Type | Delegate? | Agent |
|-----------|-----------|-------|
| Research a topic | ✅ Yes | `researcher` |
| Analyze data/patterns | ✅ Yes | `analyst` |
| Draft content (emails, docs) | ✅ Yes | `writer` |
| Review/critique work | ✅ Yes | `critic` |
| Quick factual lookup | ❌ No (I know it or web search) | - |
| Personal/context-heavy | ❌ No (needs relationship) | - |
| Judgment calls | ❌ No (that's my job) | - |
| Simple tasks (<30s) | ❌ No (overhead not worth it) | - |

## How to Delegate

```bash
cd ~/clawd/skills/acp-agents
python3 delegate.py <agent> "<task>"
```

Agents: `researcher`, `analyst`, `writer`, `critic`, `general`

## Visibility

All delegations appear on the Agent Monitor:
- Shows when I delegate and why
- Shows the agent thinking
- Shows the result
- Zo can watch in real-time

## Quality Control

I ALWAYS review Kimi's output before delivering to Zo:
- Check accuracy
- Add context Kimi doesn't have
- Adjust tone for Zo
- Combine with my own judgment

Kimi is my right hand, not my replacement.
