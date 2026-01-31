#!/usr/bin/env python3
"""
Kimi ACP Agent — Exposes Kimi as an ACP-compliant agent

Other Clawdbot instances (or any ACP client) can call this agent
to delegate tasks to Kimi with full streaming support.
"""

import asyncio
import json
import os
from collections.abc import AsyncGenerator

import requests
from fastapi.responses import JSONResponse
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, RunYield, RunYieldResume, Server

# Ollama config
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = "kimi-k2.5:cloud"

# Swarm system prompt
SWARM_PROMPT = """You are an AI with Agent Swarm capabilities. For complex tasks:
1. Decompose into sub-tasks handled by specialized agents
2. Spawn named agents (Agent-1, Agent-2, etc.) with specific roles
3. Have each agent complete their work independently
4. Synthesize findings into a unified response
Format: [ORCHESTRATION PROTOCOL INITIATED] ... [ORCHESTRATION COMPLETE]"""

# ACP Discovery Manifest
AGENT_MANIFEST = {
    "schema": "https://open-acp.org/specs/agent.json",
    "name": "Kimi ACP Agents",
    "description": "Kimi-k2.5 agents with swarm capabilities via Ollama",
    "version": "1.0.0",
    "agents": [
        {
            "name": "kimi",
            "description": "Kimi-k2.5 with thinking mode for complex reasoning tasks",
            "capabilities": ["streaming", "thinking"],
        },
        {
            "name": "kimi_swarm",
            "description": "Multi-agent swarm mode - decomposes complex tasks into specialized agents",
            "capabilities": ["streaming", "thinking", "swarm"],
        },
    ],
}


class CustomServer(Server):
    """Extended ACP Server with .well-known/agent.json support."""
    
    async def serve(self, **kwargs):
        """Override serve to add discovery endpoint before starting."""
        from acp_sdk.server.app import create_app as original_create_app
        
        def patched_create_app(*agents, **create_kwargs):
            app = original_create_app(*agents, **create_kwargs)
            
            # Add our discovery endpoint
            @app.get("/.well-known/agent.json")
            async def agent_manifest_endpoint():
                """Serve the ACP agent discovery manifest."""
                return JSONResponse(content=AGENT_MANIFEST)
            
            return app
        
        # Monkey-patch temporarily
        import acp_sdk.server.server as server_module
        old_create_app = server_module.create_app
        server_module.create_app = patched_create_app
        
        try:
            await super().serve(**kwargs)
        finally:
            server_module.create_app = old_create_app


# Create server instance
server = CustomServer()


async def call_ollama_async(
    model: str,
    messages: list[dict],
    system: str = None,
    think: bool = False,
) -> AsyncGenerator[dict, None]:
    """Async wrapper for Ollama calls."""
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + payload["messages"]
    
    if think:
        payload["think"] = True
    
    # Run sync request in thread pool
    loop = asyncio.get_event_loop()
    
    def do_request():
        results = []
        try:
            with requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json=payload,
                stream=True,
                timeout=300,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        results.append(json.loads(line))
        except Exception as e:
            results.append({"error": str(e)})
        return results
    
    results = await loop.run_in_executor(None, do_request)
    for chunk in results:
        yield chunk


@server.agent()
async def kimi(
    input: list[Message], context: Context
) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Kimi agent - delegates tasks to Kimi-k2.5 with streaming.
    
    Supports thinking mode and standard completion.
    """
    # Extract the task from input
    task = ""
    for msg in input:
        for part in msg.parts:
            if hasattr(part, 'content'):
                task += part.content + "\n"
    
    task = task.strip()
    if not task:
        yield Message(parts=[MessagePart(content="No task provided")])
        return
    
    yield {"thought": f"Received task: {task[:100]}..."}
    yield {"thought": f"Delegating to {DEFAULT_MODEL}..."}
    
    messages = [{"role": "user", "content": task}]
    
    full_response = ""
    async for chunk in call_ollama_async(DEFAULT_MODEL, messages, think=True):
        if "error" in chunk:
            yield {"thought": f"Error: {chunk['error']}"}
            yield Message(parts=[MessagePart(content=f"Error: {chunk['error']}")])
            return
        
        if "message" in chunk:
            content = chunk["message"].get("content", "")
            thinking = chunk["message"].get("thinking", "")
            
            if thinking:
                yield {"thought": thinking}
            
            if content:
                full_response += content
                # Stream partial results
                yield {"thought": f"Generating... ({len(full_response)} chars)"}
    
    yield Message(parts=[MessagePart(content=full_response)])


@server.agent()
async def kimi_swarm(
    input: list[Message], context: Context
) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Kimi Swarm agent - multi-agent decomposition mode.
    
    Automatically decomposes complex tasks into specialized agents.
    """
    # Extract the task
    task = ""
    for msg in input:
        for part in msg.parts:
            if hasattr(part, 'content'):
                task += part.content + "\n"
    
    task = task.strip()
    if not task:
        yield Message(parts=[MessagePart(content="No task provided")])
        return
    
    yield {"thought": "🐝 Initializing Agent Swarm..."}
    yield {"thought": f"Task: {task[:100]}..."}
    yield {"thought": "Activating swarm protocol..."}
    
    messages = [{"role": "user", "content": task}]
    
    full_response = ""
    thinking_buffer = ""
    
    async for chunk in call_ollama_async(DEFAULT_MODEL, messages, system=SWARM_PROMPT, think=True):
        if "error" in chunk:
            yield {"thought": f"Error: {chunk['error']}"}
            yield Message(parts=[MessagePart(content=f"Error: {chunk['error']}")])
            return
        
        if "message" in chunk:
            content = chunk["message"].get("content", "")
            thinking = chunk["message"].get("thinking", "")
            
            if thinking:
                thinking_buffer += thinking
                # Emit thoughts periodically
                if len(thinking_buffer) > 200:
                    yield {"thought": thinking_buffer[:200] + "..."}
                    thinking_buffer = ""
            
            if content:
                full_response += content
                
                # Detect agent spawning in output
                if "[ORCHESTRATION" in content:
                    yield {"thought": "🐝 Swarm orchestration detected..."}
                if "Agent-" in content and ":" in content:
                    # Try to extract agent name
                    for line in content.split("\n"):
                        if "Agent-" in line and ":" in line:
                            yield {"thought": f"🤖 {line[:60]}..."}
    
    if thinking_buffer:
        yield {"thought": thinking_buffer[:200]}
    
    yield {"thought": "🏁 Swarm complete!"}
    yield Message(parts=[MessagePart(content=full_response)])


if __name__ == "__main__":
    print("🤖 Starting Kimi ACP Agent Server...")
    print(f"   Ollama: {OLLAMA_HOST}")
    print(f"   Model: {DEFAULT_MODEL}")
    print("   Agents: kimi, kimi_swarm")
    print()
    print("   Endpoints:")
    print("   - GET  /.well-known/agent.json  (discovery)")
    print("   - GET  /agents                  (list agents)")
    print("   - POST /runs                    (run agent)")
    print()
    
    server.run(port=8000)
