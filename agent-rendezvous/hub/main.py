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

# Goal-to-agent capability mapping to ensure relevant proposals
GOAL_CAPABILITIES: Dict[str, List[str]] = {
    "extract_event": [
        "poster-ocr-regex",
        "event-normalizer",
        "timezone-resolver",
        "ics-builder",
        "ocr-generic",
        "event-validator",
    ],
    "summarize_text": ["chatgpt", "gemini"],
    "translate_text": ["chatgpt", "gemini"],
    "analyze_sentiment": ["chatgpt", "gemini"],
    "extract_keywords": ["chatgpt", "gemini"],
    "classify_text": ["chatgpt", "gemini"],
    "parse_invoice": ["ocr-generic", "chatgpt", "gemini"],
}

def provider_is_eligible(provider: Dict[str, Any], goal: str) -> bool:
    if goal not in GOAL_CAPABILITIES:
        return True
    pid = provider.get("id") or provider.get("name")
    return pid in GOAL_CAPABILITIES[goal]

@app.on_event("startup")
async def startup_event():
    """Load MCP agents from configuration on startup."""
    global PROVIDERS
    mcp_servers = load_mcp_servers()
    for server in mcp_servers:
        env = server.env or {}
        # Inject common secrets from process env if not provided in config
        if server.id == "chatgpt" and "OPENAI_API_KEY" not in env and os.getenv("OPENAI_API_KEY"):
            env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        if server.id == "gemini" and "GEMINI_API_KEY" not in env and os.getenv("GEMINI_API_KEY"):
            env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
        if server.id == "timezone-resolver" and "TIMEZONEDB_API_KEY" not in env and os.getenv("TIMEZONEDB_API_KEY"):
            env["TIMEZONEDB_API_KEY"] = os.getenv("TIMEZONEDB_API_KEY")
        PROVIDERS.append({
            "id": server.id,
            "name": server.id,
            "url": "stdio",
            "command": server.command,
            "args": server.args,
            "env": env
        })
    manifest_map = {
        "poster-ocr-regex": str(Path(__file__).parent.parent / "providers" / "agent_1" / "spoonos.manifest.json"),
        "ics-builder": str(Path(__file__).parent.parent / "providers" / "agent_8" / "spoonos.manifest.json"),
        "timezone-resolver": str(Path(__file__).parent.parent / "providers" / "agent_6" / "spoonos.manifest.json"),
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

    def apply_goal_penalty(pid: str, score: float) -> (float, bool):
        if intent.goal in GOAL_CAPABILITIES and pid not in GOAL_CAPABILITIES[intent.goal]:
            return score * 0.2, True
        return score, False

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
            score, mismatch = apply_goal_penalty(provider["id"], score)
            return {
                "_agent": provider["id"],
                "_agent_name": provider["name"],
                "_score": score,
                "_goal_mismatch": mismatch,
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
            score, mismatch = apply_goal_penalty(provider["id"], score)
            return {
                "_agent": provider["id"],
                "_agent_name": provider["name"],
                "_score": score,
                "_goal_mismatch": mismatch,
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
                        "poster-ocr-regex": {"est_cost_usd": 0.01, "est_latency_ms": 500, "confidence": 0.75},
                        "poster-ocr-dateparser": {"est_cost_usd": 0.02, "est_latency_ms": 800, "confidence": 0.85},
                        "event-normalizer": {"est_cost_usd": 0.005, "est_latency_ms": 100, "confidence": 0.9},
                        "timezone-resolver": {"est_cost_usd": 0.005, "est_latency_ms": 120, "confidence": 0.8},
                        "ics-builder": {"est_cost_usd": 0.01, "est_latency_ms": 200, "confidence": 0.9},
                        "ocr-generic": {"est_cost_usd": 0.008, "est_latency_ms": 500, "confidence": 0.7},
                        "event-validator": {"est_cost_usd": 0.004, "est_latency_ms": 80, "confidence": 0.95},
                        "chatgpt": {"est_cost_usd": 0.02, "est_latency_ms": 700, "confidence": 0.9},
                        "gemini": {"est_cost_usd": 0.015, "est_latency_ms": 600, "confidence": 0.9}
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
                    score, mismatch = apply_goal_penalty(provider["id"], score)
                    return {
                        "_agent": provider["id"],
                        "_agent_name": provider["name"],
                        "_score": score,
                        "_goal_mismatch": mismatch,
                        **proposal_data
                    }
        except Exception as e:
            print(f"MCP proposal error from {provider['name']}: {e}")
            agent_defaults = {
                "chatgpt": {"est_cost_usd": 0.02, "est_latency_ms": 700, "confidence": 0.7},
                "gemini": {"est_cost_usd": 0.015, "est_latency_ms": 600, "confidence": 0.7}
            }
            defaults = agent_defaults.get(provider["name"], {"est_cost_usd": 0.02, "est_latency_ms": 800, "confidence": 0.6})
            proposal_data = {
                "est_cost_usd": defaults["est_cost_usd"],
                "est_latency_ms": defaults["est_latency_ms"],
                "confidence": defaults["confidence"],
                "plan": ["LLM tool unavailable; using defaults"],
                "needs": {}
            }
            proposal = Proposal(**proposal_data)
            score = calculate_score(proposal)
            score, mismatch = apply_goal_penalty(provider["id"], score)
            return {
                "_agent": provider["id"],
                "_agent_name": provider["name"],
                "_score": score,
                "_goal_mismatch": mismatch,
                **proposal_data
            }

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
                score, mismatch = apply_goal_penalty(provider["id"], score)
                return {
                    "_agent": provider["id"],
                    "_agent_name": provider["name"],
                    "_score": score,
                    "_goal_mismatch": mismatch,
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
        
        # Filter by capability when at least one proposal matches; otherwise allow fallback
        if intent.goal in GOAL_CAPABILITIES:
            any_match = any(p and p.get("_agent") in GOAL_CAPABILITIES[intent.goal] for p in proposals)
            if any_match and prop.get("_agent") not in GOAL_CAPABILITIES[intent.goal]:
                continue
        filtered.append(prop)
    
    # Sort by score descending with fair tie-breakers: lower cost, lower latency, higher confidence, stable id
    filtered.sort(key=lambda x: (
        -x["_score"],
        x.get("est_cost_usd", float("inf")),
        x.get("est_latency_ms", float("inf")),
        -x.get("confidence", 0.0),
        x.get("_agent", "")
    ))
    return filtered


@app.post("/post_intent")
async def post_intent(intent: Intent):
    """Broadcast intent to all providers and return scored proposals."""
    # Fetch proposals from eligible providers concurrently (fallback to all if none mapped)
    eligible = [p for p in PROVIDERS if provider_is_eligible(p, intent.goal)] or PROVIDERS
    tasks = [fetch_proposal(provider, intent) for provider in eligible]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None and exceptions
    proposals = [r for r in results if r is not None and not isinstance(r, Exception)]
    
    # Filter and sort
    filtered_proposals = filter_and_sort_proposals(proposals, intent)
    with_explanations = [
        {**prop, "explanation": build_explanation(prop, intent)} for prop in filtered_proposals
    ]
    return {"proposals": with_explanations}


@app.post("/execute")
async def execute(intent: Intent):
    """Execute task on best available provider with fallback."""
    # Re-run scoring on eligible providers to get current best provider
    eligible = [p for p in PROVIDERS if provider_is_eligible(p, intent.goal)] or PROVIDERS
    tasks = [fetch_proposal(provider, intent) for provider in eligible]
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
                    "explanation": build_explanation(proposal_data, intent),
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
                            "event-normalizer": {"name": "normalize_event", "arg_key": "data"},
                            "timezone-resolver": {"name": "resolve_timezone", "arg_key": "location"},
                            "ics-builder": {"name": "build_ics", "arg_key": "event_data"},
                            "ocr-generic": {"name": "ocr_image", "arg_key": "image_path"},
                            "event-validator": {"name": "validate_event", "arg_key": "event_json"},
                            "chatgpt": {"name": "chat_complete", "arg_key": "text"},
                            "gemini": {"name": "gemini_complete", "arg_key": "text"}
                        }
                        agent_id = provider["name"]
                        tool_def = tool_map.get(agent_id)
                        if not tool_def:
                            last_error = f"No tool mapping for {agent_id}"
                        else:
                            arg_key = tool_def["arg_key"]
                            arg_val = intent.inputs.get(arg_key) or intent.inputs.get("text") or ""
                            result = await session.call_tool(tool_def["name"], {arg_key: arg_val})
                            # Normalize MCP result content
                            data_content: List[Any] = []
                            try:
                                if hasattr(result, "content") and isinstance(result.content, list):
                                    data_content = [c.model_dump() if hasattr(c, "model_dump") else c for c in result.content]
                                elif isinstance(result, str):
                                    data_content = [{"type": "text", "text": result}]
                                elif isinstance(result, dict):
                                    data_content = [{"type": "json", "json": result}]
                                else:
                                    data_content = [{"type": "text", "text": str(result)}]
                            except Exception:
                                data_content = [{"type": "text", "text": ""}]
                            return {
                                "winner": provider_id,
                                "winner_name": provider["name"],
                                "proposal": {k: v for k, v in proposal_data.items() if not k.startswith("_")},
                                "result": {"status": "OK", "data": {"content": data_content}},
                                "explanation": build_explanation(proposal_data, intent)
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
                        "result": result_data,
                        "explanation": build_explanation(proposal_data, intent)
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
def build_explanation(proposal_data: Dict[str, Any], intent: Intent) -> Dict[str, Any]:
    try:
        proposal = Proposal(
            est_cost_usd=proposal_data.get("est_cost_usd", 0.0),
            est_latency_ms=proposal_data.get("est_latency_ms", 0.0),
            confidence=proposal_data.get("confidence", 0.0),
            plan=proposal_data.get("plan", []),
            needs=proposal_data.get("needs", {})
        )
        score = calculate_score(proposal)
        budget_ok = True
        sla_ok = True
        if intent.budget and "max_usd" in intent.budget:
            budget_ok = proposal.est_cost_usd <= intent.budget["max_usd"]
        if intent.sla and "deadline_ms" in intent.sla:
            sla_ok = proposal.est_latency_ms <= intent.sla["deadline_ms"]
        notes = [
            "Filtered by budget and deadline before ranking",
            "Ties broken by lower cost, then lower latency, then higher confidence"
        ]
        if intent.goal in GOAL_CAPABILITIES and proposal_data.get("_agent") not in GOAL_CAPABILITIES[intent.goal]:
            notes.append("Agent is not goal-aligned; fallback with penalty applied")
        return {
            "score": score,
            "formula": "confidence / (cost * (1 + latency/5000))",
            "inputs": {
                "confidence": proposal.confidence,
                "cost_usd": proposal.est_cost_usd,
                "latency_ms": proposal.est_latency_ms
            },
            "constraints": {
                "budget_max_usd": intent.budget.get("max_usd") if intent.budget else None,
                "sla_deadline_ms": intent.sla.get("deadline_ms") if intent.sla else None,
                "budget_ok": budget_ok,
                "sla_ok": sla_ok
            },
            "notes": notes
        }
    except Exception:
        return {}
