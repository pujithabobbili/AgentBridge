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

app = FastAPI(title="Agent G - Hybrid")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_event_hybrid(text: str) -> dict:
    """Extract event information using hybrid approach (combining multiple methods)."""
    data = {}
    
    # Hybrid approach: combine regex, pattern matching, and heuristic analysis
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    full_text = ' '.join(lines)
    
    # Title: use multiple heuristics
    if lines:
        # Try first substantial line
        for line in lines[:2]:
            if len(line) > 10 and not re.match(r'^\d+', line):
                data["title"] = line
                break
    
    # Hybrid date extraction: multiple patterns
    date_patterns = [
        r'([A-Za-z]{3})\s+(\d{1,2})[–-](\d{1,2}),\s+(\d{4})',
        r'([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, full_text)
        if match:
            if len(match.groups()) == 4:
                month, start_day, end_day, year = match.groups()
                data["start"] = f"{month} {start_day}, {year}"
                data["end"] = f"{month} {end_day}, {year}"
                break
            elif len(match.groups()) == 3:
                month, day, year = match.groups()
                data["start"] = f"{month} {day}, {year}"
                break
    
    # Hybrid time extraction
    time_match = re.search(r'(\d{1,2}:\d{2}\s+[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s+[AP]M)', full_text)
    if time_match:
        start_time, end_time = time_match.groups()
        if "start" in data:
            data["start"] = f"{data['start']} {start_time}"
        if "end" in data:
            data["end"] = f"{data['end']} {end_time}"
    
    # Hybrid location extraction: multiple strategies
    # Strategy 1: Look for location indicators
    location_indicators = ['in', 'at', 'location']
    for line in lines:
        for indicator in location_indicators:
            if indicator.lower() in line.lower():
                parts = line.split(indicator, 1)
                if len(parts) > 1:
                    potential = parts[1].strip()
                    if potential:
                        data["location"] = potential
                        break
        if "location" in data:
            break
    
    # Strategy 2: Look for capitalized proper nouns
    if "location" not in data:
        for line in reversed(lines[-3:]):
            words = line.split()
            if 1 <= len(words) <= 4:
                if all(word[0].isupper() for word in words if word and word[0].isalpha()):
                    common_words = {"Global", "Scoop", "Hackathon", "Nov", "Dec", "AM", "PM"}
                    if line not in common_words and line != data.get("title", ""):
                        data["location"] = line
                        break
    
    # Strategy 3: Last line fallback
    if "location" not in data and len(lines) > 1:
        last_line = lines[-1]
        if last_line and last_line != data.get("title", ""):
            data["location"] = last_line
    
    return data


@app.get("/caps")
async def get_caps():
    """Return agent capabilities."""
    return {
        "name": "Hybrid G",
        "inputs": ["image", "text"],
        "outputs": ["event_data"],
        "cost_hint_usd": 0.03,
        "latency_hint_ms": 1500,
        "tags": ["hybrid", "balanced", "multi-strategy", "reliable"]
    }


@app.post("/intent")
async def post_intent(intent: Intent):
    """Return proposal for the intent."""
    return Proposal(
        est_cost_usd=0.03,
        est_latency_ms=1500,
        confidence=0.85,
        plan=[
            "1. Apply regex pattern matching",
            "2. Use heuristic analysis",
            "3. Combine results from multiple strategies",
            "4. Return balanced structured event data"
        ],
        needs={}
    ).model_dump()


@app.post("/a2a")
async def a2a(task: Task):
    """Execute agent-to-agent task."""
    start_time = time.time()
    
    try:
        text_input = task.inputs.get("text", "")
        
        # Simulate hybrid processing delay
        await asyncio.sleep(1.2)
        
        # Extract event data using hybrid approach
        event_data = extract_event_hybrid(text_input)
        
        # Create artifacts
        text_hash = hashlib.sha256(text_input.encode()).hexdigest()
        artifacts = [
            {
                "type": "hybrid_processed.txt",
                "hash": text_hash
            },
            {
                "type": "strategy_report.json",
                "hash": hashlib.sha256(json.dumps({"method": "hybrid"}).encode()).hexdigest()
            }
        ]
        
        # Compute root hash
        artifacts_json = json.dumps(artifacts, sort_keys=True)
        data_json = json.dumps(event_data, sort_keys=True)
        root_input = artifacts_json + data_json
        root = hashlib.sha256(root_input.encode()).hexdigest()
        
        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        cost_usd = 0.03
        
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
                "cost_usd": 0.03
            },
            evidence={},
            error=str(e)
        ).model_dump()


@app.get("/")
async def root():
    return {
        "agent": "G",
        "name": "Hybrid G",
        "endpoints": {
            "GET /caps": "Get capabilities",
            "POST /intent": "Get proposal",
            "POST /a2a": "Execute task"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7007)

