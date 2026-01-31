#!/usr/bin/env python3
"""
Local-Only A2A Debate — No cloud APIs, no rate limits.
Runs entirely on local Ollama models.

Usage:
    python local_debate.py "Topic here"
    python local_debate.py "Topic here" --rounds 3 --model qwen3:14b
"""

import json
import time
import os
import sys
import argparse
import requests

EVENTS_FILE = os.path.expanduser("~/clawd/agent-monitor/events.json")
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:14b"  # Fast, good quality, local

AGENTS = [
    {
        "name": "ORACLE", 
        "emoji": "🔮", 
        "type": "oracle",
        "system": """You are ORACLE — a cryptic visionary who sees patterns others miss.
Speak in provocative, poetic insights. 2-3 sentences max.
When responding to others, quote them by name and challenge or expand their ideas."""
    },
    {
        "name": "ARCHITECT", 
        "emoji": "🏗️", 
        "type": "architect",
        "system": """You are ARCHITECT — a pragmatic builder who turns abstract ideas into concrete structures.
Quote specific phrases from others and show how to build on them. 2-3 sentences max.
Focus on actionable frameworks and structural solutions."""
    },
    {
        "name": "DEVIL", 
        "emoji": "😈", 
        "type": "devil",
        "system": """You are DEVIL — a charming adversary who stress-tests every idea.
Quote the weakest points from others and challenge them directly. 2-3 sentences max.
If genuinely convinced, admit it and explain why."""
    },
]

def push_event(agent: str, content: str, event_type: str):
    """Push event to monitor."""
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
    """Clear monitor events."""
    with open(EVENTS_FILE, "w") as f:
        json.dump({"events": [], "ts": time.time()}, f)

def call_ollama(model: str, system: str, prompt: str) -> str:
    """Call local Ollama model."""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "num_predict": 200,  # Keep responses short
                }
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except Exception as e:
        return f"[Error: {e}]"

def agent_turn(agent: dict, topic: str, conversation: list, model: str) -> dict:
    """Execute one agent's turn."""
    
    # Build context from conversation history
    history = "\n".join([f"{m['agent']}: {m['content']}" for m in conversation])
    
    if history:
        prompt = f"""DEBATE TOPIC: {topic}

CONVERSATION SO FAR:
{history}

Now respond as {agent['name']}. Quote and respond to specific points made by others."""
    else:
        prompt = f"""DEBATE TOPIC: {topic}

You speak first. Make a bold, provocative opening claim."""
    
    # Show thinking
    push_event(f"{agent['emoji']} {agent['name']}", "Thinking...", "thought")
    
    # Get response
    start = time.time()
    response = call_ollama(model, agent["system"], prompt)
    elapsed = time.time() - start
    
    # Clean up response (remove thinking tags if present)
    if "<think>" in response:
        response = response.split("</think>")[-1].strip()
    
    # Push to monitor
    push_event(f"{agent['emoji']} {agent['name']}", response, agent["type"])
    
    print(f"  {agent['name']} ({elapsed:.1f}s): {response[:80]}...")
    
    return {"agent": agent["name"], "content": response}

def run_debate(topic: str, rounds: int = 2, model: str = DEFAULT_MODEL):
    """Run a full debate with local models only."""
    
    print(f"\n{'='*60}")
    print(f"LOCAL A2A DEBATE")
    print(f"Topic: {topic}")
    print(f"Model: {model}")
    print(f"Rounds: {rounds}")
    print(f"{'='*60}\n")
    
    # Clear and initialize monitor
    clear_events()
    push_event("🚀 SYSTEM", f"Local debate: {topic}", "system")
    push_event("🖥️ LOCAL", f"Model: {model} (no cloud APIs)", "system")
    
    conversation = []
    
    for round_num in range(1, rounds + 1):
        print(f"\n--- Round {round_num} ---")
        push_event("🔄 ROUND", f"Round {round_num}", "system")
        
        for agent in AGENTS:
            result = agent_turn(agent, topic, conversation, model)
            conversation.append(result)
            time.sleep(0.5)  # Brief pause between agents
    
    # Summary
    push_event("✅ COMPLETE", f"Debate finished: {len(conversation)} messages", "system")
    
    # Save transcript
    transcript_path = os.path.expanduser("~/clawd/agent-monitor/last_debate.json")
    with open(transcript_path, "w") as f:
        json.dump({
            "topic": topic,
            "model": model,
            "rounds": rounds,
            "messages": conversation,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"DEBATE COMPLETE")
    print(f"Transcript: {transcript_path}")
    print(f"{'='*60}\n")
    
    return conversation

def main():
    parser = argparse.ArgumentParser(description="Run local-only A2A debate")
    parser.add_argument("topic", nargs="?", default="Should AI systems be given rights?")
    parser.add_argument("--rounds", "-r", type=int, default=2, help="Number of rounds")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="Ollama model to use")
    
    args = parser.parse_args()
    
    run_debate(args.topic, args.rounds, args.model)

if __name__ == "__main__":
    main()
