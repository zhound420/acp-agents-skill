#!/usr/bin/env python3
"""
ACP Client — Call ACP agents with streaming and highlight extraction.

Two output modes:
- Full stream → logs/control session (every thought)
- Highlights → chat surfaces (collaboration moments only)
"""

import argparse
import json
import re
import sys
from datetime import datetime

import requests

ACP_SERVER = "http://127.0.0.1:8000"


def stream_run(agent: str, task: str, verbose: bool = False):
    """
    Execute an ACP agent run with streaming.
    
    Yields tuples of (event_type, content):
    - ("log", text) → full detail for control session
    - ("highlight", text) → key moment for chat
    - ("output", text) → final result
    """
    
    # Start the run in stream mode
    resp = requests.post(
        f"{ACP_SERVER}/runs",
        json={
            "agent_name": agent,
            "input": [{"parts": [{"content": task}]}],
            "mode": "stream",
        },
        stream=True,
        headers={"Accept": "text/event-stream"},
        timeout=300,
    )
    
    run_id = resp.headers.get("Run-ID", "unknown")
    yield ("log", f"[{timestamp()}] Run started: {run_id}")
    yield ("highlight", f"🤖 {agent.replace('_', ' ').title()} working...")
    
    # Track what we've highlighted to avoid duplicates
    highlighted_agents = set()
    orchestration_started = False
    full_output = ""
    
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        
        data_str = line[5:].strip()  # Remove "data:" prefix
        if not data_str:
            continue
        
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            continue
        
        event_type = data.get("type", "")
        
        # Handle different event types
        if event_type == "generic":
            generic = data.get("generic", {})
            thought = generic.get("thought", "")
            if thought:
                yield ("log", f"[{timestamp()}] 💭 {thought}")
                
                # Extract highlights for chat
                highlight = extract_highlight(
                    thought, 
                    highlighted_agents, 
                    orchestration_started
                )
                if highlight:
                    if "ORCHESTRATION PROTOCOL" in thought:
                        orchestration_started = True
                    yield ("highlight", highlight)
                    
        elif event_type == "message":
            # Final output message
            message = data.get("message", {})
            parts = message.get("parts", [])
            for part in parts:
                content = part.get("content", "")
                if content:
                    full_output += content
                    yield ("log", f"[{timestamp()}] ✅ Output chunk: {len(content)} chars")
                    
        elif event_type == "run.completed":
            yield ("log", f"[{timestamp()}] Run completed")
            if full_output:
                yield ("output", full_output)
            yield ("highlight", "✅ Done!")
            
        elif event_type == "run.failed":
            error = data.get("run", {}).get("error", "Unknown error")
            yield ("log", f"[{timestamp()}] ❌ Run failed: {error}")
            yield ("highlight", f"❌ Failed: {error}")


def extract_highlight(thought: str, seen_agents: set, orchestration_active: bool) -> str | None:
    """
    Extract chat-worthy highlights from thought stream.
    
    Returns highlight text or None if not highlight-worthy.
    """
    
    # Orchestration start
    if "[ORCHESTRATION PROTOCOL INITIATED]" in thought:
        return "🐝 Swarm activated..."
    
    # Orchestration complete
    if "[ORCHESTRATION COMPLETE" in thought:
        return "🔄 Swarm synthesis complete"
    
    # Agent spawning - look for "Agent-N:" or "Agent-N (" pattern
    agent_match = re.search(r'(Agent-\d+)\s*[:\(]([^:\)\n]+)', thought)
    if agent_match:
        agent_name = agent_match.group(1)
        agent_role = agent_match.group(2).strip()[:40]
        
        if agent_name not in seen_agents:
            seen_agents.add(agent_name)
            return f"🤖 {agent_name}: {agent_role}"
    
    # Synthesis/coordination moments
    if any(kw in thought.lower() for kw in ["synthesis coordinator", "combining findings", "final synthesis"]):
        if "synthesis" not in seen_agents:
            seen_agents.add("synthesis")
            return "🔄 Synthesizing findings..."
    
    return None


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def run_agent(agent: str, task: str, chat_mode: bool = False, verbose: bool = False):
    """
    Run an ACP agent and print output.
    
    chat_mode: Only show highlights (for Telegram)
    verbose: Show everything (for control session)
    """
    
    output = None
    highlights = []
    
    for event_type, content in stream_run(agent, task, verbose):
        if event_type == "log" and not chat_mode:
            print(content, file=sys.stderr)
        elif event_type == "highlight":
            highlights.append(content)
            if chat_mode:
                print(content)
        elif event_type == "output":
            output = content
    
    if not chat_mode and output:
        print("\n" + "="*50, file=sys.stderr)
        print("FINAL OUTPUT:", file=sys.stderr)
        print("="*50, file=sys.stderr)
        print(output)
    elif chat_mode and output:
        print()
        # Truncate for chat if needed
        if len(output) > 2000:
            print(output[:2000] + "\n...[truncated]")
        else:
            print(output)
    
    return {
        "output": output,
        "highlights": highlights,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ACP Agent Client")
    parser.add_argument("agent", choices=["kimi", "kimi_swarm"], help="Agent to call")
    parser.add_argument("task", help="Task to execute")
    parser.add_argument("--chat", action="store_true", help="Chat mode (highlights only)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    run_agent(args.agent, args.task, chat_mode=args.chat, verbose=args.verbose)
