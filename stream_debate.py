#!/usr/bin/env python3
"""
Streaming ACP Debate — Watch agents think in real-time.
Each agent streams their response via ACP, pushed live to the monitor.
"""

import asyncio
import json
import time
import os
import aiohttp

EVENTS_FILE = os.path.expanduser("~/clawd/agent-monitor/events.json")
ACP_SERVER = "http://localhost:8000"

AGENTS = [
    {"name": "ORACLE", "emoji": "🔮", "type": "oracle", 
     "system": "You are ORACLE. Give cryptic, provocative insights. When others have spoken, quote and challenge them. 2-3 sentences max."},
    {"name": "ARCHITECT", "emoji": "🏗️", "type": "architect",
     "system": "You are ARCHITECT. Build concrete structures from ideas. Quote others by name and show how to build on their points. 2-3 sentences max."},
    {"name": "DEVIL", "emoji": "😈", "type": "devil",
     "system": "You are DEVIL. Stress-test everything. Quote specific weaknesses from others. If convinced, say so. 2-3 sentences max."},
]

def push_event(agent: str, content: str, event_type: str):
    """Push to monitor."""
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

def clear_events():
    with open(EVENTS_FILE, "w") as f:
        json.dump({"events": [], "ts": time.time()}, f)

async def stream_agent_call(agent: dict, prompt: str, conversation: list):
    """Call agent via ACP with streaming, push chunks to monitor."""
    
    # Build full prompt with conversation history
    history = "\n".join([f"{m['agent']}: {m['content']}" for m in conversation])
    
    if history:
        full_prompt = f"{agent['system']}\n\nConversation so far:\n{history}\n\nTopic: {prompt}\n\nNow respond as {agent['name']}. Quote and respond to others by name."
    else:
        full_prompt = f"{agent['system']}\n\nTopic: {prompt}\n\nYou speak first. Make a bold opening claim."
    
    push_event(f"{agent['emoji']} {agent['name']}", "Thinking...", "thought")
    
    # Stream from ACP
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{ACP_SERVER}/runs",
            json={
                "agent_name": "kimi",
                "input": [{"parts": [{"content": full_prompt}]}],
                "mode": "stream",
            },
            headers={"Accept": "text/event-stream"},
        ) as resp:
            buffer = ""
            thinking_shown = False
            
            async for line in resp.content:
                line = line.decode().strip()
                if not line.startswith("data:"):
                    continue
                
                try:
                    data = json.loads(line[5:].strip())
                except:
                    continue
                
                event_type = data.get("type", "")
                
                if event_type == "generic":
                    thought = data.get("generic", {}).get("thought", "")
                    if thought:
                        buffer += thought
                        # Push streaming updates every ~100 chars
                        if len(buffer) > 100 and not thinking_shown:
                            push_event(f"{agent['emoji']} {agent['name']}", f"💭 {buffer[:100]}...", "thought")
                            thinking_shown = True
                
                elif event_type == "message.completed":
                    msg = data.get("message", {})
                    for part in msg.get("parts", []):
                        content = part.get("content", "")
                        if content:
                            # Final response
                            push_event(f"{agent['emoji']} {agent['name']}", content.strip(), agent["type"])
                            return {"agent": agent["name"], "content": content.strip()}
                
                elif event_type == "run.completed":
                    # Fallback if message.completed wasn't captured
                    run = data.get("run", {})
                    for msg in run.get("output", []):
                        for part in msg.get("parts", []):
                            content = part.get("content", "")
                            if content and not buffer:
                                push_event(f"{agent['emoji']} {agent['name']}", content.strip(), agent["type"])
                                return {"agent": agent["name"], "content": content.strip()}
    
    return {"agent": agent["name"], "content": buffer or "[No response]"}

async def run_streaming_debate(topic: str, rounds: int = 2):
    """Run debate with streaming ACP calls."""
    
    clear_events()
    push_event("🚀 SYSTEM", f"Starting STREAMING debate: {topic}", "system")
    push_event("📡 ACP", "All responses stream via ACP protocol", "system")
    
    conversation = []
    
    for round_num in range(rounds):
        push_event("🔄 ROUND", f"Round {round_num + 1}", "system")
        
        for agent in AGENTS:
            result = await stream_agent_call(agent, topic, conversation)
            conversation.append(result)
            await asyncio.sleep(0.5)  # Small pause between agents
    
    push_event("✅ COMPLETE", f"Debate finished. {len(conversation)} messages via streaming ACP.", "system")
    
    # Save conversation
    with open(os.path.expanduser("~/clawd/agent-monitor/last_debate.json"), "w") as f:
        json.dump({"topic": topic, "messages": conversation}, f, indent=2)
    
    return conversation

if __name__ == "__main__":
    import sys
    
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Should AI have rights?"
    
    print(f"Starting streaming debate: {topic}")
    print("Watch the monitor for real-time updates...")
    print()
    
    results = asyncio.run(run_streaming_debate(topic, rounds=2))
    
    print("\n=== DEBATE COMPLETE ===\n")
    for msg in results:
        print(f"{msg['agent']}: {msg['content'][:100]}...")
        print()
