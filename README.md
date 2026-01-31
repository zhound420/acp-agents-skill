# ACP Agents Skill

Multi-agent orchestration for Clawdbot. Swarm intelligence for real work, not parlor tricks.

> **Related:** For simple single-agent delegation, see [ollama-worker](https://github.com/zhound420/ollama-worker-skill). Start there for basic "Claude delegates to Kimi." Come here when you need **parallel agents**, **pipelines**, or **multi-perspective analysis**.

## Why Agent Swarms?

One agent is smart. Multiple agents working together are **multiplicative**:

| Single Agent | Agent Swarm |
|--------------|-------------|
| Sequential processing | Parallel processing |
| One perspective | Multiple perspectives |
| Bottlenecked by context | Distributed context |
| Linear pipelines | Branching workflows |

## Real-World Applications

### 🔍 Parallel Research
```bash
python swarm.py research \
  --topic "Electric vehicle market" \
  --agents "market-size,competitors,regulations,technology-trends,consumer-sentiment" \
  --synthesize
```
5 agents research simultaneously, then synthesize findings. What takes 1 agent 25 minutes takes a swarm 5.

### 📝 Content Pipeline
```bash
python swarm.py pipeline \
  --stages "brainstorm,draft,edit,critique,polish" \
  --input "Write a landing page for a B2B SaaS product"
```
Each stage is a specialist. Brainstormer generates ideas → Drafter writes → Editor tightens → Critic finds holes → Polisher finalizes.

### 🔐 Code Review Swarm
```bash
python swarm.py code-review \
  --file pull_request.diff \
  --reviewers "security,performance,maintainability,test-coverage"
```
Four specialist agents review your PR simultaneously:
- **Security**: SQL injection, XSS, auth issues
- **Performance**: N+1 queries, memory leaks, algorithmic complexity
- **Maintainability**: Code smells, naming, documentation
- **Test Coverage**: Missing edge cases, test quality

### 📊 Decision Analysis
```bash
python swarm.py decision \
  --question "Should we build vs buy our auth system?" \
  --perspectives "engineering,product,finance,security,timeline"
```
Get structured analysis from multiple viewpoints before making critical decisions.

### 📧 Inbox Processing
```bash
python swarm.py inbox \
  --emails inbox_export.json \
  --agents "categorizer,priority-scorer,response-drafter,calendar-checker"
```
- **Categorizer**: Sales, support, personal, spam, action-required
- **Priority Scorer**: Urgency + importance matrix
- **Response Drafter**: Draft replies for review
- **Calendar Checker**: Flag scheduling conflicts

### 🏪 E-commerce Optimization (Example: Etsy)
```bash
python swarm.py etsy-optimize \
  --shop "kyroku" \
  --agents "seo-analyzer,competitor-scanner,pricing-optimizer,trend-spotter,listing-writer"
```
- **SEO Analyzer**: Keyword gaps, title optimization
- **Competitor Scanner**: What similar shops do well
- **Pricing Optimizer**: Market positioning analysis
- **Trend Spotter**: Upcoming seasonal opportunities
- **Listing Writer**: Generate optimized descriptions

### 🎯 Hiring Pipeline
```bash
python swarm.py evaluate-candidate \
  --resume candidate.pdf \
  --job-description jd.txt \
  --agents "skills-matcher,culture-assessor,red-flag-detector,interview-question-generator"
```

### 📰 News Digest
```bash
python swarm.py news-digest \
  --sources "hackernews,techcrunch,arxiv" \
  --topics "AI,crypto,startups" \
  --agents "scanner,summarizer,relevance-scorer,insight-extractor"
```

---

## Core Components

### Agent Types

| Agent | Purpose | Example Use |
|-------|---------|-------------|
| **Researcher** | Gather & synthesize information | Market analysis, competitive intel |
| **Analyst** | Find patterns & insights | Data analysis, trend detection |
| **Writer** | Generate content | Drafts, copy, documentation |
| **Critic** | Find weaknesses & improve | Code review, QA, editing |
| **Specialist** | Domain expertise | Security, legal, finance |

### Orchestration Patterns

**Fan-Out / Fan-In**
```
           ┌─→ Agent A ─┐
Input ────┼─→ Agent B ─┼──→ Synthesizer → Output
           └─→ Agent C ─┘
```
Parallel processing with synthesis. Best for research, multi-perspective analysis.

**Pipeline**
```
Input → Agent A → Agent B → Agent C → Output
```
Sequential refinement. Best for content creation, data processing.

**Debate/Adversarial**
```
Agent A ←──argue──→ Agent B
            ↓
       Synthesizer
```
Opposing viewpoints sharpen thinking. Best for decisions, risk analysis.

**Hierarchical**
```
         Coordinator
        /     |     \
    Agent A  Agent B  Agent C
       |
   Sub-Agent
```
Complex task decomposition. Best for large projects.

---

## Quick Start

### 1. Start the ACP Server
```bash
cd ~/clawd/skills/acp-agents
source .venv/bin/activate
python kimi_agent.py
```

### 2. Use the Delegate CLI
```bash
# Single specialist
python delegate.py researcher "Analyze the competitive landscape for AI coding assistants"

# Full swarm
python delegate.py swarm "Design a complete authentication system" --agents 5
```

### 3. Custom Swarm (Python)
```python
from router import ACPRouter

router = ACPRouter()

# Register agents
router.register_http("researcher", "http://localhost:8000")
router.register_http("analyst", "http://localhost:8000")
router.register_http("writer", "http://localhost:8000")

# Fan-out research
topics = ["market size", "competitors", "regulations"]
results = await asyncio.gather(*[
    router.call("researcher", f"Research: {topic}")
    for topic in topics
])

# Synthesize
synthesis = await router.call("analyst", f"Synthesize these findings: {results}")
```

---

## Specialist Agents

### Built-in Personas

```bash
# Research & Analysis
python delegate.py researcher "Find all pricing data for competitor X"
python delegate.py analyst "What patterns do you see in this sales data?"

# Content Creation
python delegate.py writer "Write a product description for..."
python delegate.py critic "Review this copy for weaknesses"

# General
python delegate.py general "Complex task that needs flexible handling"
```

### Custom Specialists

Create domain experts by defining system prompts:

```python
SPECIALISTS = {
    "security_auditor": {
        "system": """You are a senior security engineer. 
        Analyze code/systems for vulnerabilities.
        Focus on: OWASP Top 10, auth issues, data exposure.
        Output: severity-ranked findings with remediation."""
    },
    "pricing_strategist": {
        "system": """You are a pricing strategy consultant.
        Analyze markets and recommend pricing.
        Consider: competition, value perception, elasticity.
        Output: recommended price points with rationale."""
    }
}
```

---

## Agent Monitor

Real-time dashboard for watching swarm activity:

```bash
open ~/clawd/agent-monitor/index.html
```

See which agents are working, their outputs, timing, and synthesis.

---

## Configuration

### Environment Variables
```bash
OLLAMA_HOST=http://localhost:11434
ACP_PORT=8000
```

### Models
| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `phi3:mini` | ⚡⚡⚡ | ⭐⭐ | Quick classification, simple tasks |
| `llama3:8b` | ⚡⚡ | ⭐⭐⭐ | General local processing |
| `kimi-k2.5:cloud` | ⚡ | ⭐⭐⭐⭐⭐ | Complex analysis, synthesis |

---

## When to Use Swarms vs Single Agent

| Scenario | Recommendation |
|----------|----------------|
| Quick question | Single agent |
| Research requiring multiple angles | **Swarm** |
| Document that needs multiple review types | **Swarm** |
| Sequential refinement (draft → edit) | **Pipeline** |
| Time-sensitive, parallelize-able work | **Swarm** |
| Need diverse perspectives on decision | **Swarm** |
| Simple task delegation | Single agent ([ollama-worker](https://github.com/zhound420/ollama-worker-skill)) |

---

## Examples from Real Use

### Etsy Shop Strategy (Creative War Room)
```bash
# 4 specialists analyzed Kyroku shop
python delegate.py researcher "Etsy tech-apparel market analysis"
python delegate.py analyst "Customer psychographics for tech-nature fusion"
python delegate.py writer "New shop bio and product descriptions"  
python delegate.py critic "Review all outputs for weaknesses"
```
Result: Complete brand strategy with market positioning, customer psychology ("Techno-Animist"), copy, and QC.

### Architecture Decision
```bash
python swarm.py decision \
  --question "Kubernetes vs Docker Compose for small startup?" \
  --perspectives "devops,cost,scaling,complexity,hiring"
```

### PR Review
```bash
python swarm.py code-review \
  --pr 1234 \
  --reviewers "security,performance,readability"
```

---

## Building Custom Swarms

See `SWARM-PATTERNS.md` for detailed patterns:
- Research Swarm
- Content Pipeline
- Code Review Swarm
- Decision Support
- Monitoring/Alert Swarm

---

## License

MIT

---

*Part of the Clawdbot ecosystem. Start with [ollama-worker](https://github.com/zhound420/ollama-worker-skill) for simple delegation, graduate here for multi-agent orchestration.*
