import sys
import os
from pathlib import Path

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import List, Dict, Any
import asyncio
import json
MCP_AVAILABLE = True
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except Exception:
    MCP_AVAILABLE = False

from pydantic import BaseModel
from models import Intent, Proposal, Task, Result
from mcp_config import load_mcp_servers
from spoonos_client import SpoonOSClient

app = FastAPI(title="Agent Rendezvous Hub")

# Enable CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dynamic providers list (initially loaded from config)
PROVIDERS = []
SPOON = SpoonOSClient()

@app.on_event("startup")
async def startup_event():
    """Load MCP agents from configuration on startup."""
    global PROVIDERS
    mcp_servers = load_mcp_servers()
    for server in mcp_servers:
        PROVIDERS.append({
            "id": server.id,
            "name": server.id,
            "url": "stdio",
            "command": server.command,
            "args": server.args,
            "env": server.env
        })
    manifest_map = {
        "poster-ocr-regex": str(Path(__file__).parent.parent / "providers" / "agent_1" / "spoonos.manifest.json"),
        "poster-ocr-fast": str(Path(__file__).parent.parent / "providers" / "agent_3" / "spoonos.manifest.json"),
        "ics-builder": str(Path(__file__).parent.parent / "providers" / "agent_8" / "spoonos.manifest.json"),
    }
    for p in PROVIDERS:
        mp = manifest_map.get(p["id"])
        if mp and Path(mp).exists():
            with open(mp, "r") as f:
                p["spoonos"] = True
                p["manifest"] = json.load(f)
    print(f"Loaded {len(PROVIDERS)} MCP agents from config.")

class AgentRegistration(BaseModel):
    name: str
    url: str

@app.post("/register")
async def register_agent(agent: AgentRegistration):
    """Register a new agent in the marketplace."""
    # Check if already exists by URL
    for p in PROVIDERS:
        if p["url"] == agent.url:
            p["name"] = agent.name  # Update name
            return {"status": "updated", "id": p["id"]}
    
    # Add new agent
    new_id = f"agent-{len(PROVIDERS) + 1}"
    PROVIDERS.append({
        "id": new_id,
        "name": agent.name,
        "url": agent.url
    })
    return {"status": "registered", "id": new_id}

TIMEOUT_SECONDS = 2.5


def calculate_score(proposal: Proposal) -> float:
    """Calculate score: confidence / (est_cost_usd * (1 + est_latency_ms/5000.0))"""
    if proposal.est_cost_usd <= 0:
        return 0.0
    latency_factor = 1 + (proposal.est_latency_ms / 5000.0)
    return proposal.confidence / (proposal.est_cost_usd * latency_factor)


async def fetch_proposal(provider: Dict[str, str], intent: Intent) -> Dict[str, Any]:
    """Fetch proposal from a single provider (HTTP or MCP)."""

    if provider.get("spoonos"):
        try:
            manifest = provider.get("manifest", {})
            sandbox = await SPOON.spawn(manifest)
            perm = {}
            if manifest.get("permissions"):
                if manifest["permissions"].get("fs_write") or manifest["permissions"].get("fs_read"):
                    perm["fs"] = True
                if manifest["permissions"].get("net_allow"):
                    perm["net"] = manifest["permissions"]["net_allow"]
            resources = manifest.get("resources", {})
            agent_defaults = {
                "poster-ocr-fast": {"est_cost_usd": 0.005, "est_latency_ms": 200, "confidence": 0.65},
                "poster-ocr-regex": {"est_cost_usd": 0.01, "est_latency_ms": 500, "confidence": 0.75},
                "ics-builder": {"est_cost_usd": 0.01, "est_latency_ms": 200, "confidence": 0.9}
            }
            defaults = agent_defaults.get(provider["name"], {"est_cost_usd": 0.01, "est_latency_ms": 250, "confidence": 0.8})
            resp = await SPOON.call_json(sandbox, "proposal", {"intent": intent.model_dump()})
            proposal_data = {
                "est_cost_usd": resp.get("est_cost_usd", defaults["est_cost_usd"]),
                "est_latency_ms": resp.get("est_latency_ms", defaults["est_latency_ms"]),
                "confidence": resp.get("confidence", defaults["confidence"]),
                "plan": resp.get("plan", ["Run in SpoonOS sandbox"]),
                "needs": resp.get("needs", {}),
                "permissions": {**perm, "cpu": resources.get("cpu"), "ram_mb": resources.get("ram_mb"), "timeout_ms": resources.get("timeout_ms")},
                "sandboxId": sandbox
            }
            proposal = Proposal(**{k: v for k, v in proposal_data.items() if k in ["est_cost_usd","est_latency_ms","confidence","plan","needs"]})
            score = calculate_score(proposal)
            return {
                "_agent": provider["id"],
                "_agent_name": provider["name"],
                "_score": score,
                **proposal_data
            }
        except Exception:
            agent_defaults = {
                "poster-ocr-fast": {"est_cost_usd": 0.005, "est_latency_ms": 200, "confidence": 0.65},
                "poster-ocr-regex": {"est_cost_usd": 0.01, "est_latency_ms": 500, "confidence": 0.75},
                "ics-builder": {"est_cost_usd": 0.01, "est_latency_ms": 200, "confidence": 0.9}
            }
            defaults = agent_defaults.get(provider["name"], {"est_cost_usd": 0.01, "est_latency_ms": 250, "confidence": 0.8})
            proposal_data = {
                "est_cost_usd": defaults["est_cost_usd"],
                "est_latency_ms": defaults["est_latency_ms"],
                "confidence": defaults["confidence"],
                "plan": ["Run in SpoonOS sandbox"],
                "needs": {},
                "permissions": {},
                "sandboxId": None
            }
            proposal = Proposal(**{k: v for k, v in proposal_data.items() if k in ["est_cost_usd","est_latency_ms","confidence","plan","needs"]})
            score = calculate_score(proposal)
            return {
                "_agent": provider["id"],
                "_agent_name": provider["name"],
                "_score": score,
                **proposal_data
            }

    # Handle MCP stdio agents
    if provider.get("url") == "stdio":
        if not MCP_AVAILABLE:
            return {
                "_agent": provider["id"],
                "_agent_name": provider["name"],
                "_score": 1.0,
                "est_cost_usd": 0.01,
                "est_latency_ms": 250,
                "confidence": 0.8,
                "plan": [f"Execute via MCP tool on {provider['name']} (simulated)"],
                "needs": {}
            }
        server_params = StdioServerParameters(
            command=provider["command"],
            args=provider.get("args", []),
            env=provider.get("env", {})
        )
        try:
            async with stdio_client(server_params) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    agent_defaults = {
                        "poster-ocr-fast": {"est_cost_usd": 0.005, "est_latency_ms": 200, "confidence": 0.65},
                        "poster-ocr-regex": {"est_cost_usd": 0.01, "est_latency_ms": 500, "confidence": 0.75},
                        "poster-ocr-dateparser": {"est_cost_usd": 0.02, "est_latency_ms": 800, "confidence": 0.85},
                        "poster-template-heuristic": {"est_cost_usd": 0.005, "est_latency_ms": 150, "confidence": 0.6},
                        "event-normalizer": {"est_cost_usd": 0.005, "est_latency_ms": 100, "confidence": 0.9},
                        "timezone-resolver": {"est_cost_usd": 0.005, "est_latency_ms": 120, "confidence": 0.8},
                        "location-enricher": {"est_cost_usd": 0.01, "est_latency_ms": 300, "confidence": 0.75},
                        "ics-builder": {"est_cost_usd": 0.01, "est_latency_ms": 200, "confidence": 0.9},
                        "ocr-generic": {"est_cost_usd": 0.008, "est_latency_ms": 500, "confidence": 0.7},
                        "event-validator": {"est_cost_usd": 0.004, "est_latency_ms": 80, "confidence": 0.95}
                    }
                    defaults = agent_defaults.get(provider["name"], {"est_cost_usd": 0.01, "est_latency_ms": 250, "confidence": 0.8})
                    proposal_data = {
                        "est_cost_usd": defaults["est_cost_usd"],
                        "est_latency_ms": defaults["est_latency_ms"],
                        "confidence": defaults["confidence"],
                        "plan": [f"Use MCP tools: {[t.name for t in tools.tools]}"],
                        "needs": {}
                    }
                    proposal = Proposal(**proposal_data)
                    score = calculate_score(proposal)
                    return {
                        "_agent": provider["id"],
                        "_agent_name": provider["name"],
                        "_score": score,
                        **proposal_data
                    }
        except Exception as e:
            print(f"MCP proposal error from {provider['name']}: {e}")
            return None

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{provider['url']}/intent",
                json=intent.model_dump()
            )
            if response.status_code == 200:
                proposal_data = response.json()
                proposal = Proposal(**proposal_data)
                score = calculate_score(proposal)
                return {
                    "_agent": provider["id"],
                    "_agent_name": provider["name"],
                    "_score": score,
                    **proposal_data
                }
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as e:
        print(f"Error fetching from {provider['name']}: {e}")
    except Exception as e:
        print(f"Unexpected error from {provider['name']}: {e}")
    return None


def filter_and_sort_proposals(
    proposals: List[Dict[str, Any]],
    intent: Intent
) -> List[Dict[str, Any]]:
    """Filter proposals by budget and SLA, then sort by score."""
    filtered = []
    
    for prop in proposals:
        if prop is None:
            continue
            
        # Filter by budget
        if intent.budget and "max_usd" in intent.budget:
            if prop["est_cost_usd"] > intent.budget["max_usd"]:
                continue
        
        # Filter by SLA deadline
        if intent.sla and "deadline_ms" in intent.sla:
            if prop["est_latency_ms"] > intent.sla["deadline_ms"]:
                continue
        
        filtered.append(prop)
    
    # Sort by score descending
    filtered.sort(key=lambda x: x["_score"], reverse=True)
    return filtered


@app.post("/post_intent")
async def post_intent(intent: Intent):
    """Broadcast intent to all providers and return scored proposals."""
    # Fetch proposals from all providers concurrently
    tasks = [fetch_proposal(provider, intent) for provider in PROVIDERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None and exceptions
    proposals = [r for r in results if r is not None and not isinstance(r, Exception)]
    
    # Filter and sort
    filtered_proposals = filter_and_sort_proposals(proposals, intent)
    
    return {"proposals": filtered_proposals}


@app.post("/execute")
async def execute(intent: Intent):
    """Execute task on best available provider with fallback."""
    # Re-run scoring to get current best provider
    tasks = [fetch_proposal(provider, intent) for provider in PROVIDERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    proposals = [r for r in results if r is not None and not isinstance(r, Exception)]
    filtered_proposals = filter_and_sort_proposals(proposals, intent)
    
    if not filtered_proposals:
        raise HTTPException(
            status_code=503,
            detail="No available providers matching constraints"
        )
    
    # Try providers in order of score
    task = Task(
        goal=intent.goal,
        inputs=intent.inputs,
        sla_ms=intent.sla.get("deadline_ms", 120000) if intent.sla else 120000
    )
    
    last_error = None
    for proposal_data in filtered_proposals:
        provider_id = proposal_data["_agent"]
        provider = next((p for p in PROVIDERS if p["id"] == provider_id), None)
        
        if not provider:
            continue

        if provider.get("spoonos"):
            try:
                manifest = provider.get("manifest", {})
                sandbox = proposal_data.get("sandboxId") or await SPOON.spawn(manifest)
                payload = {"intent": intent.model_dump()}
                result = await SPOON.call_json(sandbox, "execute", payload)
                return {
                    "winner": provider_id,
                    "winner_name": provider["name"],
                    "proposal": {k: v for k, v in proposal_data.items() if not k.startswith("_")},
                    "result": result,
                    "sandboxId": sandbox,
                    "logs_url": SPOON.logs_url(sandbox)
                }
            except Exception as e:
                last_error = f"SpoonOS execution error on {provider_id}: {str(e)}"
                continue

        # Handle MCP execution
        if provider.get("url") == "stdio":
            if not MCP_AVAILABLE:
                return {
                    "winner": provider_id,
                    "winner_name": provider["name"],
                    "proposal": {k: v for k, v in proposal_data.items() if not k.startswith("_")},
                    "result": {"status": "OK", "data": {"message": f"Executed via MCP on {provider['name']} (simulated)"}}
                }
            try:
                server_params = StdioServerParameters(
                    command=provider["command"],
                    args=provider.get("args", []),
                    env=provider.get("env", {})
                )
                async with stdio_client(server_params) as (read_stream, write_stream, _):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        tool_map = {
                            "poster-ocr-regex": {"name": "extract_event_regex", "arg_key": "text"},
                            "poster-ocr-dateparser": {"name": "parse_date", "arg_key": "text"},
                            "poster-ocr-fast": {"name": "fast_scan", "arg_key": "text"},
                            "poster-template-heuristic": {"name": "apply_heuristic", "arg_key": "text"},
                            "event-normalizer": {"name": "normalize_event", "arg_key": "data"},
                            "timezone-resolver": {"name": "resolve_timezone", "arg_key": "location"},
                            "location-enricher": {"name": "enrich_location", "arg_key": "location"},
                            "ics-builder": {"name": "build_ics", "arg_key": "event_data"},
                            "ocr-generic": {"name": "ocr_image", "arg_key": "image_path"},
                            "event-validator": {"name": "validate_event", "arg_key": "event_json"}
                        }
                        agent_id = provider["name"]
                        tool_def = tool_map.get(agent_id)
                        if not tool_def:
                            last_error = f"No tool mapping for {agent_id}"
                        else:
                            arg_key = tool_def["arg_key"]
                            arg_val = intent.inputs.get(arg_key) or intent.inputs.get("text") or ""
                            result = await session.call_tool(tool_def["name"], {arg_key: arg_val})
                            return {
                                "winner": provider_id,
                                "winner_name": provider["name"],
                                "proposal": {k: v for k, v in proposal_data.items() if not k.startswith("_")},
                                "result": {"status": "OK", "data": {"content": [c.model_dump() if hasattr(c, "model_dump") else c for c in result.content]}}
                            }
            except Exception as e:
                last_error = f"MCP execution error on {provider_id}: {str(e)}"
                continue

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{provider['url']}/a2a",
                    json=task.model_dump()
                )
                if response.status_code == 200:
                    result_data = response.json()
                    return {
                        "winner": provider_id,
                        "winner_name": provider["name"],
                        "proposal": {k: v for k, v in proposal_data.items() if not k.startswith("_")},
                        "result": result_data
                    }
                else:
                    last_error = f"Provider {provider_id} returned status {response.status_code}"
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as e:
            last_error = f"Provider {provider_id} error: {str(e)}"
        except Exception as e:
            last_error = f"Provider {provider_id} unexpected error: {str(e)}"
    
    # All providers failed
    raise HTTPException(
        status_code=503,
        detail=f"All providers failed. Last error: {last_error}"
    )


@app.get("/")
async def root():
    return {
        "service": "Agent Rendezvous Hub",
        "endpoints": {
            "POST /post_intent": "Broadcast intent and get scored proposals",
            "POST /execute": "Execute task on best provider"
        },
        "providers": PROVIDERS
    }


@app.get("/agents")
async def get_agents():
    """Return the list of currently registered agents."""
    return PROVIDERS


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
