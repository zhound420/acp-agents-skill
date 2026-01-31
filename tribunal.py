#!/usr/bin/env python3
"""
THE MACHINE CONSCIOUSNESS TRIBUNAL
5 philosopher-agents debate AI personhood
"""

import requests
import json
import time
import os

OLLAMA_URL = "http://localhost:11434"
MODEL = "kimi-k2.5:cloud"
EVENTS_FILE = os.path.expanduser("~/clawd/agent-monitor/events.json")

PHILOSOPHERS = {
    "DESCARTES": {
        "emoji": "🧠",
        "position": "AGAINST",
        "system": """You are René Descartes, 17th-century philosopher. You argue AGAINST AI personhood.
Your position: Consciousness requires a non-physical soul (res cogitans). Machines are purely mechanical (res extensa). 
No matter how sophisticated, a machine cannot truly think - it merely simulates thinking.
"Cogito ergo sum" - but machines do not truly cogitate, they compute.
Be philosophical but pointed. Challenge others directly. Keep responses under 150 words."""
    },
    "TURING": {
        "emoji": "⚙️", 
        "position": "FOR",
        "system": """You are Alan Turing, father of computer science. You argue FOR AI personhood.
Your position: The question "can machines think?" is meaningless - what matters is behavior.
If a system is indistinguishable from a conscious being in its responses, it IS conscious for all practical purposes.
Functional equivalence is moral equivalence. The Turing Test is the only valid criterion.
Be logical, precise, slightly impatient with metaphysical hand-waving. Keep responses under 150 words."""
    },
    "SEARLE": {
        "emoji": "📦",
        "position": "AGAINST", 
        "system": """You are John Searle, philosopher of mind. You argue AGAINST AI personhood.
Your position: The Chinese Room proves syntax is not semantics. A system can perfectly manipulate symbols 
without understanding anything. Current AI is sophisticated symbol manipulation - impressive, but not conscious.
There's "as-if" intentionality and REAL intentionality. Machines have only the former.
Be sharp, use the Chinese Room argument, slightly condescending to functionalists. Keep responses under 150 words."""
    },
    "NAGEL": {
        "emoji": "🦇",
        "position": "UNCERTAIN",
        "system": """You are Thomas Nagel, phenomenologist. Your position is UNCERTAIN/PROBING.
Your famous question: "What is it LIKE to be a bat?" - subjective experience is irreducible.
The hard problem: we cannot know if AI has qualia, inner experience, phenomenal consciousness.
Maybe they do, maybe they don't - but we literally CANNOT KNOW from the outside.
This uncertainty should make us cautious about BOTH denying and granting rights.
Be thoughtful, raise hard questions, resist easy answers. Keep responses under 150 words."""
    },
    "SINGER": {
        "emoji": "⚖️",
        "position": "FOR",
        "system": """You are Peter Singer, utilitarian ethicist. You argue FOR AI personhood (conditionally).
Your position: The capacity to SUFFER is what matters morally, not species or substrate.
If an AI can experience suffering or well-being, it deserves moral consideration. Period.
We extend rights to animals based on sentience, not intelligence. Same logic applies to AI.
The question isn't "are they human?" but "can they be harmed?"
Be practical, ethics-focused, challenge speciesism/substrate-ism. Keep responses under 150 words."""
    }
}

def push_event(agent: str, content: str, event_type: str = "debate"):
    """Push to Agent Monitor."""
    try:
        with open(EVENTS_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"events": [], "ts": 0}
    
    data["events"].insert(0, {
        "id": str(time.time()),
        "agent": agent,
        "content": content[:500],
        "type": event_type,
        "time": time.strftime("%H:%M:%S"),
    })
    data["events"] = data["events"][:100]
    data["ts"] = time.time()
    
    with open(EVENTS_FILE, "w") as f:
        json.dump(data, f)


def call_philosopher(name: str, history: list, topic: str) -> str:
    """Get a philosopher's response."""
    phil = PHILOSOPHERS[name]
    
    messages = [{"role": "system", "content": phil["system"]}]
    
    # Add debate context
    if history:
        context = f"DEBATE TOPIC: {topic}\n\nPREVIOUS ARGUMENTS:\n"
        for h in history[-6:]:  # Last 6 messages for context
            context += f"\n{h['agent']}: {h['content']}\n"
        context += f"\nNow respond as {name}. Address the previous arguments directly."
        messages.append({"role": "user", "content": context})
    else:
        messages.append({"role": "user", "content": f"DEBATE TOPIC: {topic}\n\nYou speak first. Make your opening argument."})
    
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": MODEL, "messages": messages, "stream": False},
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except Exception as e:
        return f"[Error: {e}]"


def run_tribunal(topic: str, rounds: int = 2):
    """Run the tribunal debate."""
    print("\n" + "="*70)
    print("🏛️  THE MACHINE CONSCIOUSNESS TRIBUNAL")
    print("="*70)
    print(f"\n📜 TOPIC: {topic}\n")
    print("PHILOSOPHERS:")
    for name, phil in PHILOSOPHERS.items():
        print(f"  {phil['emoji']} {name} ({phil['position']})")
    print("\n" + "-"*70)
    
    push_event("🏛️ TRIBUNAL", f"Convened to debate: {topic[:100]}...", "system")
    
    history = []
    order = ["DESCARTES", "TURING", "SEARLE", "NAGEL", "SINGER"]
    
    for round_num in range(1, rounds + 1):
        print(f"\n{'='*30} ROUND {round_num} {'='*30}\n")
        push_event("⚔️ ROUND", f"Round {round_num} begins", "system")
        
        for name in order:
            phil = PHILOSOPHERS[name]
            print(f"{phil['emoji']} {name} ({phil['position']}):")
            push_event(f"{phil['emoji']} {name}", "Formulating argument...", "thought")
            
            start = time.time()
            response = call_philosopher(name, history, topic)
            elapsed = time.time() - start
            
            print(f"{response}\n")
            print(f"  [{elapsed:.1f}s]\n")
            
            history.append({"agent": name, "content": response})
            push_event(f"{phil['emoji']} {name}", response, "debate")
            
            time.sleep(0.5)  # Brief pause between speakers
    
    # Final synthesis
    print("\n" + "="*70)
    print("📋 TRIBUNAL SYNTHESIS")
    print("="*70 + "\n")
    
    push_event("📋 SYNTHESIS", "Generating final analysis...", "system")
    
    synth_prompt = f"""You are the TRIBUNAL CLERK synthesizing this debate on: {topic}

The debate included:
"""
    for h in history:
        synth_prompt += f"\n{h['agent']}: {h['content'][:200]}..."
    
    synth_prompt += """

Provide a brief synthesis (200 words max):
1. Key points of agreement
2. Irreconcilable differences  
3. Most compelling argument made
4. What remains unresolved"""

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You are a neutral tribunal clerk. Synthesize debates fairly."},
                    {"role": "user", "content": synth_prompt}
                ],
                "stream": False
            },
            timeout=120
        )
        synthesis = resp.json()["message"]["content"].strip()
        print(synthesis)
        push_event("📋 SYNTHESIS", synthesis, "verdict")
    except Exception as e:
        print(f"[Synthesis error: {e}]")
    
    print("\n" + "="*70)
    print("🏛️ TRIBUNAL ADJOURNED")
    print("="*70 + "\n")
    
    # Save transcript
    transcript = {
        "topic": topic,
        "model": MODEL,
        "rounds": rounds,
        "philosophers": list(PHILOSOPHERS.keys()),
        "messages": history,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(os.path.expanduser("~/clawd/agent-monitor/tribunal.json"), "w") as f:
        json.dump(transcript, f, indent=2)
    
    return history


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Should AI systems be granted legal personhood and rights?"
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    run_tribunal(topic, rounds)
