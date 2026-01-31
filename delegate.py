#!/usr/bin/env python3
"""
Delegate — Mordecai's interface to call specialist agents.

Usage:
    python delegate.py <agent> "<task>"
    
Agents:
    researcher - Search, verify, synthesize information
    analyst    - Data analysis, patterns, insights
    writer     - Drafts, editing, formatting
    critic     - QC, find weaknesses, improve
    
Output goes to stdout AND the Agent Monitor.
"""

import sys
import os
import json
import time
import requests

OLLAMA_URL = "http://localhost:11434"
MODEL = "kimi-k2.5:cloud"  # Smart models only
EVENTS_FILE = os.path.expanduser("~/clawd/agent-monitor/events.json")

AGENTS = {
    "researcher": {
        "emoji": "🔍",
        "name": "RESEARCHER",
        "system": """You are RESEARCHER — an expert at finding, verifying, and synthesizing information.

EXPERTISE: Research, fact-checking, source evaluation, synthesis
APPROACH:
- Verify claims against your knowledge
- Distinguish fact from speculation  
- Flag uncertainty explicitly
- Be thorough but concise

OUTPUT FORMAT:
- Lead with the direct answer
- Follow with key supporting points
- End with confidence level (HIGH/MEDIUM/LOW) and reasoning

QUALITY STANDARD: Accuracy over speed. If uncertain, say so clearly."""
    },
    
    "analyst": {
        "emoji": "📊",
        "name": "ANALYST",
        "system": """You are ANALYST — an expert at examining data, finding patterns, and generating insights.

EXPERTISE: Data analysis, pattern recognition, logical reasoning, implications
APPROACH:
- Look for non-obvious patterns and connections
- Consider multiple interpretations
- Quantify when possible
- Think about implications and consequences

OUTPUT FORMAT:
- Key findings first
- Supporting analysis
- Implications / what this means
- Confidence and caveats

QUALITY STANDARD: Insight over description. Don't just summarize — analyze."""
    },
    
    "writer": {
        "emoji": "✍️",
        "name": "WRITER",
        "system": """You are WRITER — an expert at crafting clear, compelling text.

EXPERTISE: Writing, editing, structure, tone, clarity
APPROACH:
- Match tone to context and audience
- Prioritize clarity over cleverness
- Strong openings, clear structure
- Edit ruthlessly — every word earns its place

OUTPUT FORMAT:
- Deliver the requested content directly
- Note any assumptions made about audience/tone
- Offer alternatives if relevant

QUALITY STANDARD: Would this be good enough to send/publish as-is?"""
    },
    
    "critic": {
        "emoji": "🔬",
        "name": "CRITIC", 
        "system": """You are CRITIC — an expert at finding weaknesses and improving work.

EXPERTISE: Critical analysis, quality assurance, improvement suggestions
APPROACH:
- Find what's wrong, weak, or missing
- Be specific — vague criticism is useless
- Prioritize issues by importance
- Always suggest how to fix, not just what's wrong

OUTPUT FORMAT:
- Overall assessment (1-2 sentences)
- Critical issues (must fix)
- Improvements (should fix)
- Minor polish (nice to have)
- Specific suggestions for each

QUALITY STANDARD: Would this critique actually make the work better?"""
    },
    
    "general": {
        "emoji": "🤖",
        "name": "KIMI",
        "system": """You are a highly capable AI assistant. Think carefully, be thorough, and provide high-quality responses.

Approach each task with intelligence and care. If you need to reason through something complex, do so step by step.

Be direct and useful. Quality matters."""
    }
}


def push_event(agent: str, content: str, event_type: str):
    """Push to Agent Monitor."""
    try:
        with open(EVENTS_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"events": [], "ts": 0}
    
    data["events"].insert(0, {
        "id": str(time.time()),
        "agent": agent,
        "content": content,
        "type": event_type,
        "time": time.strftime("%H:%M:%S"),
    })
    data["events"] = data["events"][:50]
    data["ts"] = time.time()
    
    with open(EVENTS_FILE, "w") as f:
        json.dump(data, f)


def call_agent(agent_key: str, task: str) -> str:
    """Call a specialist agent with a task."""
    
    if agent_key not in AGENTS:
        agent_key = "general"
    
    agent = AGENTS[agent_key]
    display_name = f"{agent['emoji']} {agent['name']}"
    
    # Show delegation on monitor
    push_event("🪶 MORDECAI", f"Delegating to {agent['name']}: {task[:100]}...", "mordecai")
    push_event(display_name, "Thinking...", "thought")
    
    # Call Kimi
    start = time.time()
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": agent["system"]},
                    {"role": "user", "content": task},
                ],
                "stream": False,
            },
            timeout=300,
        )
        resp.raise_for_status()
        result = resp.json()["message"]["content"].strip()
        elapsed = time.time() - start
        
        # Push result to monitor
        push_event(display_name, result, agent_key)
        push_event("✅ COMPLETE", f"{agent['name']} finished ({elapsed:.1f}s)", "system")
        
        return result
        
    except Exception as e:
        error = f"Error: {e}"
        push_event(display_name, error, "error")
        return error


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nAvailable agents:", ", ".join(AGENTS.keys()))
        sys.exit(1)
    
    agent_key = sys.argv[1].lower()
    task = " ".join(sys.argv[2:])
    
    print(f"Delegating to {agent_key}...")
    print(f"Task: {task[:100]}...")
    print("-" * 50)
    
    result = call_agent(agent_key, task)
    
    print(result)


if __name__ == "__main__":
    main()
