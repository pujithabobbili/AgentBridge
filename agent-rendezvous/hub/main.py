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

from models import Intent, Proposal, Task, Result

app = FastAPI(title="Agent Rendezvous Hub")

# Enable CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hardcoded providers list
PROVIDERS = [
    {"id": "A", "name": "OCR+Regex A", "url": "http://localhost:7001"},
    {"id": "B", "name": "OCR+LLM B", "url": "http://localhost:7002"},
    {"id": "C", "name": "Template C", "url": "http://localhost:7003"},
]

TIMEOUT_SECONDS = 2.5


def calculate_score(proposal: Proposal) -> float:
    """Calculate score: confidence / (est_cost_usd * (1 + est_latency_ms/5000.0))"""
    if proposal.est_cost_usd <= 0:
        return 0.0
    latency_factor = 1 + (proposal.est_latency_ms / 5000.0)
    return proposal.confidence / (proposal.est_cost_usd * latency_factor)


async def fetch_proposal(provider: Dict[str, str], intent: Intent) -> Dict[str, Any]:
    """Fetch proposal from a single provider with timeout."""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


