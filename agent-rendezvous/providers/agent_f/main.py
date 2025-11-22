import sys
import os
from pathlib import Path
import hashlib
import json
import time
import asyncio
import re

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Intent, Proposal, Task, Result

app = FastAPI(title="Agent F - Local Model")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_event_local_model(text: str) -> dict:
    """Extract event information using local ML model (simulated, slower processing)."""
    data = {}
    
    # Simulate local model processing (slower, but free)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Basic title extraction
    if lines:
        data["title"] = lines[0]
    
    # Simpler date extraction (local model has limited capabilities)
    full_text = ' '.join(lines)
    
    # Basic date pattern
    date_match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})[–-](\d{1,2}),\s+(\d{4})', full_text)
    if date_match:
        month, start_day, end_day, year = date_match.groups()
        data["start"] = f"{month} {start_day}, {year}"
        data["end"] = f"{month} {end_day}, {year}"
    
    # Basic time extraction
    time_match = re.search(r'(\d{1,2}:\d{2}\s+[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s+[AP]M)', full_text)
    if time_match:
        start_time, end_time = time_match.groups()
        if "start" in data:
            data["start"] = f"{data['start']} {start_time}"
        if "end" in data:
            data["end"] = f"{data['end']} {end_time}"
    
    # Basic location extraction (last line usually)
    if len(lines) > 1:
        last_line = lines[-1]
        common_words = {"Nov", "Dec", "Jan", "AM", "PM", "Global", "Scoop", "Hackathon"}
        if last_line not in common_words and last_line != data.get("title", ""):
            data["location"] = last_line
    
    return data


@app.get("/caps")
async def get_caps():
    """Return agent capabilities."""
    return {
        "name": "Local Model F",
        "inputs": ["image", "text"],
        "outputs": ["event_data"],
        "cost_hint_usd": 0.001,
        "latency_hint_ms": 8000,
        "tags": ["local-model", "free", "slow", "basic"]
    }


@app.post("/intent")
async def post_intent(intent: Intent):
    """Return proposal for the intent."""
    return Proposal(
        est_cost_usd=0.001,
        est_latency_ms=8000,
        confidence=0.70,
        plan=[
            "1. Process input with local ML model",
            "2. Apply basic pattern extraction",
            "3. Return structured event data"
        ],
        needs={}
    ).model_dump()


@app.post("/a2a")
async def a2a(task: Task):
    """Execute agent-to-agent task."""
    start_time = time.time()
    
    try:
        text_input = task.inputs.get("text", "")
        
        # Simulate slow local model processing
        await asyncio.sleep(7.5)
        
        # Extract event data using local model approach
        event_data = extract_event_local_model(text_input)
        
        # Create artifacts
        text_hash = hashlib.sha256(text_input.encode()).hexdigest()
        artifacts = [
            {
                "type": "local_processed.txt",
                "hash": text_hash
            }
        ]
        
        # Compute root hash
        artifacts_json = json.dumps(artifacts, sort_keys=True)
        data_json = json.dumps(event_data, sort_keys=True)
        root_input = artifacts_json + data_json
        root = hashlib.sha256(root_input.encode()).hexdigest()
        
        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        cost_usd = 0.001
        
        # Determine status
        if event_data and len(event_data) >= 3:
            status = "OK"
        elif event_data and len(event_data) > 0:
            status = "PARTIAL"
        else:
            status = "ERROR"
        
        return Result(
            status=status,
            data=event_data,
            metrics={
                "latency_ms": latency_ms,
                "cost_usd": cost_usd
            },
            evidence={
                "artifacts": artifacts,
                "root": root
            }
        ).model_dump()
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return Result(
            status="ERROR",
            data={},
            metrics={
                "latency_ms": latency_ms,
                "cost_usd": 0.001
            },
            evidence={},
            error=str(e)
        ).model_dump()


@app.get("/")
async def root():
    return {
        "agent": "F",
        "name": "Local Model F",
        "endpoints": {
            "GET /caps": "Get capabilities",
            "POST /intent": "Get proposal",
            "POST /a2a": "Execute task"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7006)

