# A2A Agents Skill

**Agent-to-Agent (A2A) orchestration for Clawdbot.** Agents that autonomously call other agents.

> **New to multi-agent?** Start with [ollama-worker](https://github.com/zhound420/ollama-worker-skill) for simple "Claude delegates to Kimi" patterns. Come here when you need **agents communicating with agents**.

---

## What is A2A?

**Agent-to-Agent** means AI agents that can autonomously discover and communicate with other agents — no human orchestration required.

**Before A2A:**
```
Human → Agent → Human → Agent → Human
        (isolated, manual copy-paste between agents)
```

**With A2A:**
```
Human → Agent A ←→ Agent B ←→ Agent C → Human
              (agents talk directly)
```

### The Key Difference

| Human Orchestration | A2A (Autonomous) |
|---------------------|------------------|
| Human decides which agent to call | Agent decides which agent to call |
| Human passes context between agents | Agents share context directly |
| Human synthesizes outputs | Agent synthesizes outputs |
| Linear, manual | Parallel, autonomous |

---

## Quick Start

### 1. Autonomous A2A Agent

Give it a task — it decides what help it needs:

```bash
python3 ~/clawd/skills/a2a-agents/a2a_agent.py "Should we use Kubernetes for our startup?"
```

The agent will:
1. Analyze the task
2. Decide which specialists to call (researcher? analyst? both?)
3. Call them autonomously
4. Synthesize their responses
5. Return a coherent answer

### 2. Direct Specialist Delegation

When you know which expert you need:

```bash
python3 ~/clawd/skills/a2a-agents/delegate.py researcher "Analyze the EV market"
python3 ~/clawd/skills/a2a-agents/delegate.py analyst "Find patterns in this sales data"
python3 ~/clawd/skills/a2a-agents/delegate.py writer "Draft a product launch email"
python3 ~/clawd/skills/a2a-agents/delegate.py critic "Review this PR for issues"
```

---

## A2A in Action

### Example 1: Research Pipeline
```python
# Agent autonomously fans out to multiple specialists
result = await a2a_agent("Create a competitive analysis for AI coding assistants")

# Behind the scenes:
# Agent → calls researcher (market data)
# Agent → calls researcher (competitor features)  
# Agent → calls analyst (synthesize findings)
# Agent → returns unified analysis
```

### Example 2: Parallel Fan-Out
```python
# 5 researchers work simultaneously
topics = ["market size", "key players", "regulations", "technology", "trends"]

results = await asyncio.gather(*[
    router.call("researcher", f"Research: {topic}")
    for topic in topics
])

# Synthesize
synthesis = await router.call("analyst", f"Synthesize findings: {results}")
```

### Example 3: Adversarial Review
```python
# Two agents with opposing viewpoints
bull_case = await router.call("optimist", f"Make the bull case for: {proposal}")
bear_case = await router.call("skeptic", f"Make the bear case for: {proposal}")

# Third agent synthesizes
decision = await router.call("analyst", f"""
  Bull case: {bull_case}
  Bear case: {bear_case}
  Provide balanced recommendation.
""")
```

---

## Why Agent Swarms?

One agent is smart. Multiple agents working together are **multiplicative**:

| Single Agent | Agent Swarm |
|--------------|-------------|
| Sequential processing | Parallel processing |
| One perspective | Multiple perspectives |
| Bottlenecked by context | Distributed context |
| Linear pipelines | Branching workflows |

---

## Real-World Applications

### 🔍 Parallel Research
```bash
python3 a2a_agent.py "Research the electric vehicle market from 5 angles: market size, key players, regulations, technology trends, and consumer sentiment"
```
Agent spawns 5 parallel research threads, then synthesizes.

### 📝 Content Pipeline
```bash
python3 a2a_agent.py "Write a landing page for a B2B SaaS product"
```
Agent orchestrates: brainstorm → draft → edit → critique → polish.

### 🔐 Code Review Swarm
```bash
python3 a2a_agent.py "Review this code for security, performance, and maintainability: [code]"
```
Three specialists review simultaneously, findings merged.

### 📊 Decision Analysis
```bash
python3 a2a_agent.py "Should we build or buy our auth system? Consider engineering, product, finance, security, and timeline perspectives."
```
Multi-perspective analysis before critical decisions.

---

## Specialist Agents

### Built-in Personas

| Agent | Purpose | Best For |
|-------|---------|----------|
| `researcher` | Gather & synthesize information | Market analysis, competitive intel |
| `analyst` | Find patterns & insights | Data analysis, trend detection |
| `writer` | Generate content | Drafts, copy, documentation |
| `critic` | Find weaknesses & improve | Code review, QA, editing |
| `coder` | Write and debug code | Implementation, architecture |
| `security` | Security analysis | Vulnerability assessment, risk |

### Usage
```bash
python3 delegate.py researcher "Find all pricing data for competitor X"
python3 delegate.py analyst "What patterns do you see in this sales data?"
python3 delegate.py writer "Write a product description for..."
python3 delegate.py critic "Review this copy for weaknesses"
```

---

## Orchestration Patterns

### Fan-Out / Fan-In
```
           ┌─→ Agent A ─┐
Input ────┼─→ Agent B ─┼──→ Synthesizer → Output
           └─→ Agent C ─┘
```
Parallel processing with synthesis. Best for research, multi-perspective analysis.

### Pipeline
```
Input → Agent A → Agent B → Agent C → Output
```
Sequential refinement. Best for content creation, iterative improvement.

### Debate/Adversarial
```
Agent A ←──argue──→ Agent B
            ↓
       Synthesizer
```
Opposing viewpoints sharpen thinking. Best for decisions, risk analysis.

### Hierarchical
```
         Coordinator
        /     |     \
    Agent A  Agent B  Agent C
       |
   Sub-Agent
```
Complex task decomposition. Best for large projects.

---

## Core Components

| File | Purpose |
|------|---------|
| `a2a_agent.py` | **Core** — Autonomous agent that calls other agents |
| `delegate.py` | Direct delegation to specialist agents |
| `router.py` | Unified agent calling interface |
| `registry.py` | Agent discovery & tracking |
| `kimi_agent.py` | HTTP server wrapping Kimi/Ollama |
| `local_debate.py` | Multi-agent debates |
| `tribunal.py` | Structured multi-perspective analysis |

---

## Models

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `phi3:mini` | ⚡⚡⚡ | ⭐⭐ | Quick classification, simple tasks |
| `llama3:8b` | ⚡⚡ | ⭐⭐⭐ | General local processing |
| `kimi-k2.5:cloud` | ⚡ | ⭐⭐⭐⭐⭐ | Complex analysis, synthesis |

---

## Agent Monitor

Real-time dashboard for watching swarm activity:

```bash
open ~/clawd/agent-monitor/index.html
```

See which agents are working, their outputs, timing, and synthesis.

---

## When to Use A2A vs Single Agent

| Scenario | Recommendation |
|----------|----------------|
| Quick question | Single agent |
| Research requiring multiple angles | **A2A** |
| Document needing multiple review types | **A2A** |
| Sequential refinement (draft → edit) | **A2A Pipeline** |
| Time-sensitive, parallelizable work | **A2A** |
| Diverse perspectives on decision | **A2A** |
| Simple task delegation | Single agent ([ollama-worker](https://github.com/zhound420/ollama-worker-skill)) |

---

## License

MIT

---

*Part of the Clawdbot ecosystem. Start with [ollama-worker](https://github.com/zhound420/ollama-worker-skill) for simple delegation, graduate here for autonomous agent-to-agent orchestration.*
