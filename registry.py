#!/usr/bin/env python3
"""
Agent Registry — Discover and track available ACP agents.

Stores agent metadata locally and can probe endpoints for capabilities.

Usage:
    registry = AgentRegistry()
    registry.register("kimi", "http://localhost:8000", capabilities=["chat", "code"])
    registry.discover("http://localhost:8000")  # Auto-register from /.well-known/agent.json
    
    agents = registry.find(capability="code")
"""

import json
import os
import time
import requests
from dataclasses import dataclass, field, asdict
from typing import Optional

REGISTRY_FILE = os.path.expanduser("~/clawd/skills/acp-agents/agents.json")


@dataclass
class AgentInfo:
    name: str
    endpoint: str
    capabilities: list = field(default_factory=list)
    model: str = ""
    description: str = ""
    transport: str = "http"
    last_seen: float = 0
    latency_ms: int = 0
    status: str = "unknown"
    metadata: dict = field(default_factory=dict)


class AgentRegistry:
    """Local registry of known ACP agents."""
    
    def __init__(self, path: str = REGISTRY_FILE):
        self.path = path
        self.agents: dict[str, AgentInfo] = {}
        self._load()
    
    def _load(self):
        """Load registry from disk."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    data = json.load(f)
                    for name, info in data.get("agents", {}).items():
                        self.agents[name] = AgentInfo(**info)
            except Exception as e:
                print(f"[Registry] Failed to load: {e}")
    
    def _save(self):
        """Save registry to disk."""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        data = {
            "agents": {name: asdict(agent) for name, agent in self.agents.items()},
            "updated": time.time(),
        }
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)
    
    def register(
        self,
        name: str,
        endpoint: str,
        capabilities: list = None,
        model: str = "",
        description: str = "",
        **metadata
    ) -> AgentInfo:
        """Register an agent manually."""
        agent = AgentInfo(
            name=name,
            endpoint=endpoint.rstrip("/"),
            capabilities=capabilities or [],
            model=model,
            description=description,
            last_seen=time.time(),
            status="registered",
            metadata=metadata,
        )
        self.agents[name] = agent
        self._save()
        print(f"[Registry] Registered: {name} → {endpoint}")
        return agent
    
    def discover(self, endpoint: str, timeout: int = 10) -> list[AgentInfo]:
        """
        Discover agents at an endpoint via /.well-known/agent.json.
        Returns list of discovered agents.
        """
        endpoint = endpoint.rstrip("/")
        discovered = []
        
        try:
            # Try ACP discovery endpoint
            start = time.time()
            resp = requests.get(
                f"{endpoint}/.well-known/agent.json",
                timeout=timeout
            )
            latency = int((time.time() - start) * 1000)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Handle single agent or multiple
                agents_data = data.get("agents", [data]) if "agents" not in data else data["agents"]
                
                for agent_data in agents_data:
                    name = agent_data.get("name", "unknown")
                    agent = AgentInfo(
                        name=name,
                        endpoint=endpoint,
                        capabilities=agent_data.get("capabilities", []),
                        model=agent_data.get("model", ""),
                        description=agent_data.get("description", ""),
                        last_seen=time.time(),
                        latency_ms=latency,
                        status="online",
                        metadata=agent_data,
                    )
                    self.agents[name] = agent
                    discovered.append(agent)
                    print(f"[Registry] Discovered: {name} at {endpoint}")
                
                self._save()
            else:
                print(f"[Registry] Discovery failed: {resp.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"[Registry] Discovery timeout: {endpoint}")
        except Exception as e:
            print(f"[Registry] Discovery error: {e}")
        
        return discovered
    
    def probe(self, name: str) -> AgentInfo:
        """Check if an agent is online and update its status."""
        if name not in self.agents:
            raise KeyError(f"Agent '{name}' not registered")
        
        agent = self.agents[name]
        
        try:
            start = time.time()
            resp = requests.get(f"{agent.endpoint}/ping", timeout=5)
            latency = int((time.time() - start) * 1000)
            
            if resp.status_code == 200:
                agent.status = "online"
                agent.latency_ms = latency
                agent.last_seen = time.time()
            else:
                agent.status = "error"
        except:
            agent.status = "offline"
        
        self._save()
        return agent
    
    def find(
        self,
        capability: str = None,
        status: str = None,
        online_only: bool = False
    ) -> list[AgentInfo]:
        """Find agents matching criteria."""
        results = []
        
        for agent in self.agents.values():
            if capability and capability not in agent.capabilities:
                continue
            if status and agent.status != status:
                continue
            if online_only and agent.status != "online":
                continue
            results.append(agent)
        
        return results
    
    def list(self) -> list[AgentInfo]:
        """List all registered agents."""
        return list(self.agents.values())
    
    def remove(self, name: str):
        """Remove an agent from registry."""
        if name in self.agents:
            del self.agents[name]
            self._save()
            print(f"[Registry] Removed: {name}")
    
    def clear(self):
        """Clear all agents."""
        self.agents = {}
        self._save()
        print("[Registry] Cleared all agents")


def main():
    import sys
    
    registry = AgentRegistry()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  registry.py list                    - List all agents")
        print("  registry.py discover <endpoint>     - Discover agents at endpoint")
        print("  registry.py register <name> <url>   - Register agent manually")
        print("  registry.py probe <name>            - Check agent status")
        print("  registry.py find <capability>       - Find agents with capability")
        print("  registry.py remove <name>           - Remove agent")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        agents = registry.list()
        if not agents:
            print("No agents registered")
        else:
            print(f"\n{'Name':<15} {'Status':<10} {'Endpoint':<35} {'Capabilities'}")
            print("-" * 80)
            for a in agents:
                caps = ", ".join(a.capabilities[:3]) or "-"
                print(f"{a.name:<15} {a.status:<10} {a.endpoint:<35} {caps}")
    
    elif cmd == "discover" and len(sys.argv) > 2:
        endpoint = sys.argv[2]
        discovered = registry.discover(endpoint)
        print(f"Discovered {len(discovered)} agent(s)")
    
    elif cmd == "register" and len(sys.argv) > 3:
        name = sys.argv[2]
        endpoint = sys.argv[3]
        caps = sys.argv[4].split(",") if len(sys.argv) > 4 else []
        registry.register(name, endpoint, capabilities=caps)
    
    elif cmd == "probe" and len(sys.argv) > 2:
        name = sys.argv[2]
        agent = registry.probe(name)
        print(f"{agent.name}: {agent.status} ({agent.latency_ms}ms)")
    
    elif cmd == "find" and len(sys.argv) > 2:
        cap = sys.argv[2]
        agents = registry.find(capability=cap)
        print(f"Found {len(agents)} agent(s) with '{cap}':")
        for a in agents:
            print(f"  - {a.name}: {a.endpoint}")
    
    elif cmd == "remove" and len(sys.argv) > 2:
        name = sys.argv[2]
        registry.remove(name)
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
