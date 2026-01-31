# A2A Agents Skill

## When to Use
- Autonomous agent-to-agent communication
- Running multi-agent swarms
- Delegating complex tasks that benefit from multiple perspectives
- Watching agent activity in real-time

## Quick Commands

```bash
# Autonomous A2A — agent decides what help it needs
python3 ~/clawd/skills/a2a-agents/a2a_agent.py "Should we use Kubernetes for our startup?"

# Direct delegation to specialist
python3 ~/clawd/skills/a2a-agents/delegate.py researcher "Analyze the EV market"
python3 ~/clawd/skills/a2a-agents/delegate.py analyst "Find patterns in this data"
python3 ~/clawd/skills/a2a-agents/delegate.py writer "Draft a product description"
python3 ~/clawd/skills/a2a-agents/delegate.py critic "Review this code for issues"
```

### Examples

```bash
# Let the A2A agent autonomously call other agents
python3 ~/clawd/skills/a2a-agents/a2a_agent.py "Create a go-to-market strategy for a B2B SaaS"

# Direct specialist calls
python3 ~/clawd/skills/a2a-agents/delegate.py researcher "Research pros/cons of Rust vs Go"
python3 ~/clawd/skills/a2a-agents/delegate.py analyst "What patterns do you see in these sales numbers?"
```

## Key Files

| File | Purpose |
|------|---------|
| `a2a_agent.py` | **Core** — Autonomous agent that calls other agents |
| `delegate.py` | Direct delegation to specialist agents |
| `router.py` | Unified agent calling interface |
| `kimi_agent.py` | HTTP server wrapping Kimi/Ollama |
| `local_debate.py` | Multi-agent debates |
| `tribunal.py` | Structured multi-perspective analysis |

## Models

**Use for real work:**
- `kimi-k2.5:cloud` — Strong reasoning, best quality
- `deepseek-v3.1:cloud` — DeepSeek flagship

**Testing only:**
- `llama3:8b` — Fast but limited
- `phi3:mini` — Very fast but shallow

## Agent Monitor

Real-time dashboard showing agent activity:

```bash
open ~/clawd/agent-monitor/index.html
```

## Important Notes

- **A2A = Autonomous**: The agent *decides* when to call other agents — no human orchestration
- Use local models for bulk work to avoid rate limits
- All outputs go through QC before delivery to user
