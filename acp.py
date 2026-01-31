#!/usr/bin/env python3
"""
ACP CLI — Unified command-line interface for agent operations.

Usage:
    acp agents                    List registered agents
    acp discover <endpoint>       Discover agents at endpoint
    acp call <agent> <message>    Call an agent
    acp debate <topic>            Run local debate
    acp monitor                   Open agent monitor
    acp server                    Start ACP server
"""

import asyncio
import sys
import os
import subprocess


def cmd_agents():
    """List all registered agents."""
    from registry import AgentRegistry
    registry = AgentRegistry()
    
    agents = registry.list()
    if not agents:
        print("No agents registered. Run: acp discover http://localhost:8000")
        return
    
    print(f"\n{'Name':<15} {'Status':<10} {'Latency':<10} {'Capabilities'}")
    print("-" * 60)
    for a in agents:
        caps = ", ".join(a.capabilities[:3]) or "-"
        lat = f"{a.latency_ms}ms" if a.latency_ms else "-"
        print(f"{a.name:<15} {a.status:<10} {lat:<10} {caps}")
    print()


def cmd_discover(endpoint: str):
    """Discover agents at an endpoint."""
    from registry import AgentRegistry
    registry = AgentRegistry()
    discovered = registry.discover(endpoint)
    print(f"Discovered {len(discovered)} agent(s)")
    for a in discovered:
        print(f"  → {a.name}: {', '.join(a.capabilities) or 'no capabilities listed'}")


def cmd_call(agent: str, message: str):
    """Call an agent."""
    from router import ACPRouter, load_from_registry
    
    async def _call():
        router = ACPRouter()
        load_from_registry(router)
        
        # Fallback to localhost if not in registry
        if agent not in router.agents:
            router.register_http(agent, "http://localhost:8000")
        
        print(f"Calling {agent}...")
        result = await router.call(agent, message)
        print(f"\nStatus: {result.status}")
        print(f"Transport: {result.transport_used}")
        print(f"Time: {result.elapsed_ms}ms")
        print(f"\n{result.content}")
        
        await router.close()
    
    asyncio.run(_call())


def cmd_debate(topic: str, rounds: int = 2, model: str = "llama3:8b"):
    """Run a local debate."""
    from local_debate import run_debate
    run_debate(topic, rounds, model)


def cmd_monitor():
    """Open agent monitor in browser."""
    monitor_path = os.path.expanduser("~/clawd/agent-monitor/index.html")
    if os.path.exists(monitor_path):
        subprocess.run(["open", monitor_path])
        print("Opened Agent Monitor")
    else:
        print(f"Monitor not found: {monitor_path}")


def cmd_server():
    """Start ACP server."""
    script = os.path.join(os.path.dirname(__file__), "kimi_agent.py")
    print("Starting ACP server...")
    os.execvp("python3", ["python3", script])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "agents":
        cmd_agents()
    
    elif cmd == "discover":
        if len(sys.argv) < 3:
            print("Usage: acp discover <endpoint>")
            return
        cmd_discover(sys.argv[2])
    
    elif cmd == "call":
        if len(sys.argv) < 4:
            print("Usage: acp call <agent> <message>")
            return
        cmd_call(sys.argv[2], " ".join(sys.argv[3:]))
    
    elif cmd == "debate":
        topic = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Should AI have rights?"
        cmd_debate(topic)
    
    elif cmd == "monitor":
        cmd_monitor()
    
    elif cmd == "server":
        cmd_server()
    
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
