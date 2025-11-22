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

app = FastAPI(title="Agent D - Fast LLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_event_fast_llm(text: str) -> dict:
    """Extract event information using fast LLM-like processing with token limits."""
    data = {}
    
    # Simulate fast LLM with token-efficient processing
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Title: first substantial line
    if lines:
        data["title"] = lines[0]
    
    # Enhanced date/time extraction (more sophisticated than regex but faster than full LLM)
    full_text = ' '.join(lines)
    
    # Date patterns with more flexibility
    date_patterns = [
        r'([A-Za-z]{3})\s+(\d{1,2})[–-](\d{1,2}),\s+(\d{4})',
        r'([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})',
        r'(\d{1,2})[–-](\d{1,2})\s+([A-Za-z]{3}),\s+(\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, full_text)
        if match:
            if len(match.groups()) == 4:
                month, start_day, end_day, year = match.groups()
                data["start"] = f"{month} {start_day}, {year}"
                data["end"] = f"{month} {end_day}, {year}"
            elif len(match.groups()) == 3:
                month, day, year = match.groups()
                data["start"] = f"{month} {day}, {year}"
            break
    
    # Time extraction
    time_match = re.search(r'(\d{1,2}:\d{2}\s+[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s+[AP]M)', full_text)
    if time_match:
        start_time, end_time = time_match.groups()
        if "start" in data:
            data["start"] = f"{data['start']} {start_time}"
        if "end" in data:
            data["end"] = f"{data['end']} {end_time}"
    
    # Location: look for capitalized proper nouns at the end
    for line in reversed(lines[-2:]):
        words = line.split()
        if len(words) <= 3 and any(word[0].isupper() for word in words if word):
            common_words = {"Nov", "Dec", "Jan", "AM", "PM", "Global", "Scoop", "Hackathon"}
            if line not in common_words and line != data.get("title", ""):
                data["location"] = line
                break
    
    return data


@app.get("/caps")
async def get_caps():
    """Return agent capabilities."""
    return {
        "name": "Fast LLM D",
        "inputs": ["image", "text"],
        "outputs": ["event_data"],
        "cost_hint_usd": 0.02,
        "latency_hint_ms": 1000,
        "tags": ["fast-llm", "balanced", "medium-cost", "token-efficient"]
    }


@app.post("/intent")
async def post_intent(intent: Intent):
    """Return proposal for the intent."""
    return Proposal(
        est_cost_usd=0.02,
        est_latency_ms=1000,
        confidence=0.80,
        plan=[
            "1. Process input with token-efficient LLM",
            "2. Apply enhanced pattern matching with context",
            "3. Return structured event data"
        ],
        needs={}
    ).model_dump()


@app.post("/a2a")
async def a2a(task: Task):
    """Execute agent-to-agent task."""
    start_time = time.time()
    
    try:
        # Simulate fast LLM processing with token limits
        text_input = task.inputs.get("text", "")
        
        # Simulate processing delay
        await asyncio.sleep(0.8)
        
        # Extract event data using fast LLM approach
        event_data = extract_event_fast_llm(text_input)
        
        # Create artifacts
        text_hash = hashlib.sha256(text_input.encode()).hexdigest()
        artifacts = [
            {
                "type": "processed.txt",
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
        cost_usd = 0.02
        
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
                "cost_usd": 0.02
            },
            evidence={},
            error=str(e)
        ).model_dump()


@app.get("/")
async def root():
    return {
        "agent": "D",
        "name": "Fast LLM D",
        "endpoints": {
            "GET /caps": "Get capabilities",
            "POST /intent": "Get proposal",
            "POST /a2a": "Execute task"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7004)

