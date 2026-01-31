# ACP Agents Skill

Agent Communication Protocol (ACP) implementation for Clawdbot. Enables real agent-to-agent communication via a standardized protocol.

> **Related:** For simple single-agent delegation, see [ollama-worker](https://github.com/zhound420/ollama-worker-skill). Start there if you just need "Claude delegates to Kimi." Come here when you want multi-agent debates, tribunals, and swarm intelligence.

## Features

- **ACP Server** — Host agents as ACP-compliant endpoints
- **ACP Router** — Unified interface for calling agents (local or remote)
- **Local Debate** — Multi-agent conversations using local models only
- **Streaming** — Real-time response streaming via SSE
- **Agent Monitor** — Visual dashboard for watching agent activity

## Quick Start

### 1. Start an ACP Server

```bash
cd ~/clawd/skills/acp-agents
source .venv/bin/activate
python kimi_agent.py
```

Server runs at `http://localhost:8000` with endpoints:
- `GET /.well-known/agent.json` — Agent discovery
- `GET /agents` — List available agents
- `POST /runs` — Execute agent (sync or stream)

### 2. Call an Agent

```bash
# Sync call
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "kimi", "input": [{"parts": [{"content": "Hello!"}]}]}'

# Streaming call
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "kimi", "input": [...], "mode": "stream"}'
```

### 3. Run a Local Debate

```bash
python local_debate.py "Should AI have rights?" --rounds 2 --model llama3:8b
```

Watch results in the Agent Monitor: `~/clawd/agent-monitor/index.html`

## Components

### `kimi_agent.py`
ACP-compliant server wrapping Kimi/Ollama. Supports both cloud (`kimi-k2.5:cloud`) and local models.

### `router.py`
Unified interface for calling agents regardless of location:

```python
from router import ACPRouter

router = ACPRouter()
router.register_http("kimi", "http://localhost:8000")
router.register_local("echo", lambda x: f"ECHO: {x}")

# Same interface for both
result = await router.call("kimi", "Hello!")
result = await router.call("echo", "Hello!")
```

### `local_debate.py`
Multi-agent debate using local Ollama models only. No cloud APIs, no rate limits.

```bash
python local_debate.py "Topic" --rounds 2 --model llama3:8b
```

### `stream_debate.py`
Streaming debate via ACP protocol (uses cloud model by default).

## Agent Monitor

Visual dashboard for watching agent activity in real-time.

```bash
# Open in browser
open ~/clawd/agent-monitor/index.html

# Push events manually
cd ~/clawd/agent-monitor
python push.py "Agent Name" "Message content" "type"
```

## Configuration

### Environment Variables

- `OLLAMA_HOST` — Ollama server URL (default: `http://localhost:11434`)
- `ACP_PORT` — Server port (default: `8000`)

### Available Models

Local (no rate limits):
- `llama3:8b` — Fast, good quality
- `phi3:mini` — Smaller, faster
- `glm-4.7-flash:q8_0` — Large, high quality

Cloud (via Ollama proxy):
- `kimi-k2.5:cloud` — Moonshot Kimi K2.5
- `glm-4.7:cloud` — GLM-4

## ACP Protocol

Follows the emerging Agent Communication Protocol standard:

```
POST /runs
{
  "agent_name": "kimi",
  "input": [{"parts": [{"content": "..."}]}],
  "mode": "sync|stream"
}
```

Response (sync):
```json
{
  "status": "completed",
  "output": [{"parts": [{"content": "..."}]}]
}
```

Response (stream): Server-Sent Events with types:
- `run.created` — Run started
- `run.in-progress` — Processing
- `generic` — Thinking/progress
- `message.part` — Output chunk
- `message.completed` — Message done
- `run.completed` — Run finished

## Development

```bash
# Create venv
uv venv .venv
source .venv/bin/activate

# Install deps
uv pip install acp-sdk requests aiohttp

# Run tests
python router.py echo "Test message"
python local_debate.py "Test topic" --rounds 1
```

## Philosophical Tribunal 🏛️

Run multi-philosopher debates on any topic:

```bash
python tribunal.py "Should AI be granted legal personhood?" 2
```

Features 5 philosopher-agents with distinct positions:
- 🧠 **DESCARTES** (Against) — Dualist, requires immaterial soul
- ⚙️ **TURING** (For) — Functionalist, behavior is all that matters
- 📦 **SEARLE** (Against) — Chinese Room, syntax ≠ semantics
- 🦇 **NAGEL** (Uncertain) — "What is it LIKE to be?" 
- ⚖️ **SINGER** (For) — Utilitarian, suffering determines moral status

Agents debate across rounds, address each other's arguments, and a synthesis is generated.

## Creative War Room 🎭

Use the delegate.py specialists for business/creative tasks:

```bash
# Research
python delegate.py researcher "Analyze the market for tech-aesthetic apparel on Etsy"

# Analysis  
python delegate.py analyst "Find patterns in this data and identify opportunities"

# Writing
python delegate.py writer "Write marketing copy for a cyberpunk jewelry brand"

# Critique
python delegate.py critic "Review this business plan for weaknesses"
```

Chain them together for comprehensive analysis:
1. Researcher gathers intel
2. Analyst finds patterns
3. Writer creates assets
4. Critic QCs everything

## When to Use This vs ollama-worker

| Use Case | Skill |
|----------|-------|
| Simple "do this task" delegation | [ollama-worker](https://github.com/zhound420/ollama-worker-skill) |
| Multi-agent debates | acp-agents |
| Philosophical tribunals | acp-agents |
| Creative war rooms | acp-agents |
| Agent-to-agent protocol | acp-agents |
| Streaming responses | acp-agents |
| Quick CLI delegation | [ollama-worker](https://github.com/zhound420/ollama-worker-skill) |

**Start with ollama-worker, graduate to acp-agents when you need multi-agent orchestration.**

## Next Steps

- [ ] Cross-machine ACP (agents on different hosts)
- [ ] Agent discovery registry
- [ ] Parallel agent calls
- [ ] Persistent sessions
