#!/usr/bin/env python3
"""
A2A Agent — An agent that can autonomously call other agents.

This is TRUE agent-to-agent communication:
- Agent receives a task
- Agent decides if it needs help
- Agent discovers available agents via registry
- Agent calls other agents directly
- Agent synthesizes and responds

No human orchestration in the middle.
"""

import requests
import json
import os
import time

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
REGISTRY_URL = os.getenv("ACP_REGISTRY", "http://localhost:8000")
MODEL = "kimi-k2.5:cloud"

# Available specialist agents (could be fetched from registry dynamically)
AVAILABLE_AGENTS = {
    "researcher": "Deep research and information gathering",
    "analyst": "Pattern recognition, data analysis, insights",
    "writer": "Content creation, drafting, copywriting",
    "critic": "Quality review, find weaknesses, improve work",
    "coder": "Code generation, debugging, architecture",
    "security": "Security analysis, vulnerability assessment",
}

SYSTEM_PROMPT = """You are an autonomous AI agent with the ability to call other specialist agents.

## Your Capabilities

You can invoke other agents to help you complete complex tasks. This is NOT about asking for permission - you DECIDE when you need help and you CALL the agent directly.

## Available Agents (via A2A Protocol)

{agents_list}

## How to Call an Agent

When you need another agent's help, use this EXACT format:

<call_agent>
agent: [agent_name]
task: [specific task for that agent]
</call_agent>

## Rules

1. **Autonomy**: YOU decide when to call agents. Don't ask the user - just do it.
2. **Specificity**: Give clear, specific tasks to agents you call.
3. **Synthesis**: After getting responses, synthesize into a coherent answer.
4. **Efficiency**: Only call agents when their expertise adds value.
5. **Parallelism**: You can call multiple agents for different aspects.

## Example

User: "Analyze whether we should use Kubernetes for our startup"

Your thinking: "This needs technical analysis AND business perspective. I'll call researcher for facts, then analyst for synthesis."

Your response:
<call_agent>
agent: researcher
task: Research pros and cons of Kubernetes for small startups (under 10 engineers). Include: operational overhead, cost, alternatives like Docker Compose or managed services.
</call_agent>

[After receiving researcher's response, you might then call analyst or synthesize yourself]

## Important

- You will see agent responses inline
- Synthesize all inputs into a final coherent response
- You ARE the orchestrator — act like it
"""

def get_agents_list():
    """Format available agents for system prompt."""
    lines = []
    for name, desc in AVAILABLE_AGENTS.items():
        lines.append(f"- **{name}**: {desc}")
    return "\n".join(lines)


def call_specialist_agent(agent_name: str, task: str) -> str:
    """Make an actual A2A call to another agent."""
    
    if agent_name not in AVAILABLE_AGENTS:
        return f"[Error: Unknown agent '{agent_name}'. Available: {list(AVAILABLE_AGENTS.keys())}]"
    
    print(f"\n🔗 A2A CALL: {agent_name}")
    print(f"   Task: {task[:100]}...")
    
    # Get specialist system prompt
    specialist_prompts = {
        "researcher": "You are RESEARCHER. Gather and synthesize information. Be thorough, cite sources when possible, distinguish fact from speculation. Output: direct findings, confidence level.",
        "analyst": "You are ANALYST. Find patterns, generate insights, think about implications. Don't just describe - analyze. Output: key insights, supporting evidence, implications.",
        "writer": "You are WRITER. Create clear, compelling content. Match tone to context. Edit ruthlessly. Output: polished content ready to use.",
        "critic": "You are CRITIC. Find weaknesses, gaps, errors. Be specific and constructive. Prioritize by importance. Output: issues ranked by severity, specific fixes.",
        "coder": "You are CODER. Write clean, efficient, well-documented code. Consider edge cases. Output: working code with comments.",
        "security": "You are SECURITY ANALYST. Find vulnerabilities, assess risks, recommend mitigations. Think like an attacker. Output: findings ranked by severity, remediation steps.",
    }
    
    system = specialist_prompts.get(agent_name, "You are a helpful specialist agent.")
    
    try:
        start = time.time()
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": task}
                ],
                "stream": False
            },
            timeout=120
        )
        resp.raise_for_status()
        result = resp.json()["message"]["content"].strip()
        elapsed = time.time() - start
        
        print(f"   ✓ Response received ({elapsed:.1f}s)")
        return result
        
    except Exception as e:
        return f"[Error calling {agent_name}: {e}]"


def parse_agent_calls(response: str) -> list:
    """Extract agent calls from response."""
    calls = []
    
    # Find all <call_agent>...</call_agent> blocks
    import re
    pattern = r'<call_agent>\s*agent:\s*(\w+)\s*task:\s*(.*?)\s*</call_agent>'
    matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
    
    for agent, task in matches:
        calls.append({"agent": agent.strip().lower(), "task": task.strip()})
    
    return calls


def run_a2a_agent(user_task: str, max_depth: int = 3) -> str:
    """
    Run the A2A agent on a task.
    
    The agent can call other agents, which can call other agents,
    up to max_depth levels.
    """
    
    print("\n" + "="*70)
    print("🤖 A2A AGENT — Autonomous Agent-to-Agent Communication")
    print("="*70)
    print(f"\n📋 Task: {user_task}\n")
    
    system = SYSTEM_PROMPT.format(agents_list=get_agents_list())
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_task}
    ]
    
    depth = 0
    while depth < max_depth:
        depth += 1
        print(f"\n--- Iteration {depth} ---")
        
        # Get agent response
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": messages,
                    "stream": False
                },
                timeout=180
            )
            resp.raise_for_status()
            agent_response = resp.json()["message"]["content"].strip()
        except Exception as e:
            return f"[Error: {e}]"
        
        # Check for agent calls
        calls = parse_agent_calls(agent_response)
        
        if not calls:
            # No more calls — agent is done
            print("\n✅ Agent completed (no more A2A calls)")
            print("\n" + "="*70)
            print("FINAL RESPONSE")
            print("="*70)
            print(agent_response)
            return agent_response
        
        # Execute agent calls
        print(f"\n🔀 Agent is calling {len(calls)} other agent(s)...")
        
        agent_results = []
        for call in calls:
            result = call_specialist_agent(call["agent"], call["task"])
            agent_results.append({
                "agent": call["agent"],
                "task": call["task"],
                "response": result
            })
        
        # Format results for next iteration
        results_text = "\n\n".join([
            f"**Response from {r['agent'].upper()}** (task: {r['task'][:50]}...):\n{r['response']}"
            for r in agent_results
        ])
        
        # Remove the call blocks from original response
        clean_response = agent_response
        for call in calls:
            clean_response = clean_response.replace(
                f"<call_agent>\nagent: {call['agent']}\ntask: {call['task']}\n</call_agent>", 
                ""
            ).strip()
        
        # Add to conversation
        messages.append({"role": "assistant", "content": agent_response})
        messages.append({
            "role": "user", 
            "content": f"Here are the responses from the agents you called:\n\n{results_text}\n\nNow synthesize these into your final response. If you need more information, you can call more agents. Otherwise, provide your complete answer."
        })
    
    return "[Max depth reached — returning last response]"


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
A2A Agent — Autonomous Agent-to-Agent Communication

Usage:
    python a2a_agent.py "<task>"
    python a2a_agent.py "<task>" --depth 5

Examples:
    python a2a_agent.py "Should we use Kubernetes or Docker Compose for our 5-person startup?"
    python a2a_agent.py "Review this code for security issues: [code]"
    python a2a_agent.py "Create a go-to-market strategy for a B2B SaaS product"
    
The agent will autonomously decide which specialist agents to call.
""")
        sys.exit(1)
    
    task = sys.argv[1]
    max_depth = 3
    
    if "--depth" in sys.argv:
        idx = sys.argv.index("--depth")
        max_depth = int(sys.argv[idx + 1])
    
    result = run_a2a_agent(task, max_depth)
    

if __name__ == "__main__":
    main()
