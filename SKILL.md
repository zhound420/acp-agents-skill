# ACP Agents Skill

## When to Use
- Running multi-agent debates or conversations
- Calling external AI agents via ACP protocol
- Setting up agent-to-agent communication
- Watching agent activity in real-time

## Quick Commands (using `acp` CLI)

```bash
acp agents                    # List registered agents
acp discover <endpoint>       # Discover agents at endpoint
acp call <agent> <message>    # Call an agent
acp debate <topic>            # Run local debate
acp monitor                   # Open agent monitor
acp server                    # Start ACP server
```

### Examples

```bash
# List agents
acp agents

# Discover agents at localhost
acp discover http://localhost:8000

# Call an agent
acp call kimi "What is the meaning of life?"

# Run a debate
acp debate "Should AI have consciousness?"

# Open monitor
acp monitor
```

### Manual (without CLI)

```bash
# Start server
cd ~/clawd/skills/acp-agents && source .venv/bin/activate
python kimi_agent.py &

# Run debate
python local_debate.py "TOPIC" --rounds 2 --model llama3:8b
```

## Key Files

| File | Purpose |
|------|---------|
| `kimi_agent.py` | ACP server wrapping Kimi/Ollama |
| `router.py` | Unified agent calling interface |
| `local_debate.py` | Local-only multi-agent debates |
| `stream_debate.py` | Streaming ACP debates |
| `client.py` | Simple ACP client for testing |

## Models

**Use for real work (smartest available):**
- `kimi-k2.5:cloud` — Moonshot's best, strong reasoning
- `deepseek-v3.1:cloud` — DeepSeek flagship (when available)
- `glm-4.7:cloud` — GLM-4 full model

**Testing/demos only (not for production):**
- `llama3:8b` — Fast but limited
- `phi3:mini` — Very fast but shallow
- `glm-4.7-flash:q8_0` — Local fallback

**Principle:** Quality over speed. Each agent should be intelligent enough that its output is directly usable.

## Agent Monitor

Real-time dashboard showing agent activity:

```bash
# View
open ~/clawd/agent-monitor/index.html

# Push events
cd ~/clawd/agent-monitor
python3 push.py "🔮 ORACLE" "Message here" "oracle"
python3 push.py --clear  # Clear events
```

## Important Notes

- **Use local models for debates** to avoid burning Anthropic rate limits
- The orchestrator (Claude) doesn't need to poll — debates run autonomously
- Transcripts saved to `~/clawd/agent-monitor/last_debate.json`
