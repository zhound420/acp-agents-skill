#!/usr/bin/env python3
"""
ACP Router — Unified interface, optimal transport.

All calls use ACP message format. Router picks the best path:
- Local (same process): Direct function call
- Same machine: HTTP to localhost  
- Remote: HTTP to ACP endpoint

Usage:
    router = ACPRouter()
    router.register("kimi", "http://localhost:8000")
    router.register("oracle", LocalAgent(oracle_fn))
    
    result = await router.call("kimi", "Summarize this...")
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Any
from enum import Enum
import aiohttp


class TransportType(Enum):
    LOCAL = "local"      # Direct function call
    HTTP = "http"        # HTTP/ACP endpoint


@dataclass
class Agent:
    name: str
    transport: TransportType
    endpoint: Optional[str] = None  # For HTTP
    handler: Optional[Callable] = None  # For local
    metadata: dict = field(default_factory=dict)


@dataclass  
class ACPMessage:
    """Standard ACP message format."""
    content: str
    role: str = "user"
    metadata: dict = field(default_factory=dict)


@dataclass
class ACPResponse:
    """Standard ACP response format."""
    content: str
    agent: str
    status: str = "completed"
    thinking: Optional[str] = None
    elapsed_ms: int = 0
    transport_used: str = ""


class ACPRouter:
    """Routes ACP calls to agents via optimal transport."""
    
    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self._session: Optional[aiohttp.ClientSession] = None
    
    def register_http(self, name: str, endpoint: str, **metadata):
        """Register an agent accessible via HTTP/ACP."""
        self.agents[name] = Agent(
            name=name,
            transport=TransportType.HTTP,
            endpoint=endpoint.rstrip("/"),
            metadata=metadata
        )
        print(f"[Router] Registered {name} → HTTP {endpoint}")
    
    def register_local(self, name: str, handler: Callable, **metadata):
        """Register a local agent (direct function call)."""
        self.agents[name] = Agent(
            name=name,
            transport=TransportType.LOCAL,
            handler=handler,
            metadata=metadata
        )
        print(f"[Router] Registered {name} → LOCAL")
    
    def list_agents(self) -> list[dict]:
        """List all registered agents."""
        return [
            {
                "name": a.name,
                "transport": a.transport.value,
                "endpoint": a.endpoint,
                "metadata": a.metadata
            }
            for a in self.agents.values()
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _call_http(self, agent: Agent, message: ACPMessage) -> ACPResponse:
        """Call agent via HTTP/ACP endpoint."""
        start = time.time()
        
        session = await self._get_session()
        
        payload = {
            "agent_name": agent.name.split("/")[-1],  # Handle "server/agent" format
            "input": [{"parts": [{"content": message.content}]}],
            "mode": "sync"
        }
        
        try:
            async with session.post(
                f"{agent.endpoint}/runs",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                data = await resp.json()
                
                # Extract content from ACP response
                content = ""
                for msg in data.get("output", []):
                    for part in msg.get("parts", []):
                        content += part.get("content", "")
                
                return ACPResponse(
                    content=content or str(data),
                    agent=agent.name,
                    status=data.get("status", "completed"),
                    elapsed_ms=int((time.time() - start) * 1000),
                    transport_used="http"
                )
        except Exception as e:
            return ACPResponse(
                content=f"[Error: {e}]",
                agent=agent.name,
                status="error",
                elapsed_ms=int((time.time() - start) * 1000),
                transport_used="http"
            )
    
    async def _call_local(self, agent: Agent, message: ACPMessage) -> ACPResponse:
        """Call agent via direct function call."""
        start = time.time()
        
        try:
            if asyncio.iscoroutinefunction(agent.handler):
                result = await agent.handler(message.content)
            else:
                result = agent.handler(message.content)
            
            return ACPResponse(
                content=str(result),
                agent=agent.name,
                status="completed",
                elapsed_ms=int((time.time() - start) * 1000),
                transport_used="local"
            )
        except Exception as e:
            return ACPResponse(
                content=f"[Error: {e}]",
                agent=agent.name,
                status="error",
                elapsed_ms=int((time.time() - start) * 1000),
                transport_used="local"
            )
    
    async def call(self, agent_name: str, content: str, **kwargs) -> ACPResponse:
        """Call an agent with automatic transport selection."""
        if agent_name not in self.agents:
            return ACPResponse(
                content=f"[Agent '{agent_name}' not found]",
                agent=agent_name,
                status="error",
                transport_used="none"
            )
        
        agent = self.agents[agent_name]
        message = ACPMessage(content=content, metadata=kwargs)
        
        if agent.transport == TransportType.LOCAL:
            return await self._call_local(agent, message)
        else:
            return await self._call_http(agent, message)
    
    def call_sync(self, agent_name: str, content: str, **kwargs) -> ACPResponse:
        """Synchronous wrapper for call()."""
        return asyncio.run(self.call(agent_name, content, **kwargs))
    
    async def close(self):
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()


# Convenience functions for CLI use
_router: Optional[ACPRouter] = None

def get_router() -> ACPRouter:
    global _router
    if _router is None:
        _router = ACPRouter()
    return _router


async def quick_call(agent: str, message: str) -> str:
    """Quick one-off call to an agent."""
    router = get_router()
    
    # Auto-register localhost ACP if not registered
    if agent not in router.agents:
        router.register_http(agent, "http://localhost:8000")
    
    response = await router.call(agent, message)
    return response.content


def load_from_registry(router: ACPRouter):
    """Load agents from registry into router."""
    try:
        from registry import AgentRegistry
        registry = AgentRegistry()
        
        for agent in registry.list():
            if agent.status in ["online", "registered"]:
                router.register_http(
                    agent.name,
                    agent.endpoint,
                    capabilities=agent.capabilities,
                    model=agent.model
                )
    except Exception as e:
        print(f"[Router] Could not load registry: {e}")


if __name__ == "__main__":
    import sys
    
    async def demo():
        router = ACPRouter()
        
        # Register agents
        router.register_http("kimi", "http://localhost:8000")
        router.register_http("kimi_swarm", "http://localhost:8000")
        
        # Local agent example
        def echo_agent(msg: str) -> str:
            return f"ECHO: {msg}"
        router.register_local("echo", echo_agent)
        
        print("\n=== Registered Agents ===")
        for a in router.list_agents():
            print(f"  {a['name']} ({a['transport']})")
        
        if len(sys.argv) > 2:
            agent = sys.argv[1]
            message = " ".join(sys.argv[2:])
            
            print(f"\n=== Calling {agent} ===")
            response = await router.call(agent, message)
            print(f"Status: {response.status}")
            print(f"Transport: {response.transport_used}")
            print(f"Time: {response.elapsed_ms}ms")
            print(f"\nResponse:\n{response.content}")
        
        await router.close()
    
    asyncio.run(demo())
