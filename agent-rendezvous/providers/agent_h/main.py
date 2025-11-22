import sys
import os
from pathlib import Path
import hashlib
import json
import time

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Intent, Proposal, Task, Result

app = FastAPI(title="Agent H - Specialized Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_event_specialized(text: str) -> dict:
    """Extract event information using specialized domain parser (very fast, limited scope)."""
    data = {}
    
    # Specialized parser: optimized for structured event formats
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Fast title: first non-empty line
    if lines:
        data["title"] = lines[0]
    
    # Optimized for specific event format patterns
    # Look for structured patterns in order
    full_text = ' '.join(lines)
    
    # Quick date match (optimized pattern)
    date_match = __import__('re').search(r'([A-Za-z]{3})\s+(\d{1,2})[–-](\d{1,2}),\s+(\d{4})', full_text)
    if date_match:
        month, start_day, end_day, year = date_match.groups()
        data["start"] = f"{month} {start_day}, {year}"
        data["end"] = f"{month} {end_day}, {year}"
    
    # Quick time match
    time_match = __import__('re').search(r'(\d{1,2}:\d{2}\s+[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s+[AP]M)', full_text)
    if time_match:
        start_time, end_time = time_match.groups()
        if "start" in data:
            data["start"] = f"{data['start']} {start_time}"
        if "end" in data:
            data["end"] = f"{data['end']} {end_time}"
    
    # Fast location: usually last line
    if len(lines) > 1:
        last_line = lines[-1]
        if last_line and last_line != data.get("title", ""):
            # Quick check if it's not a date/time line
            if "Nov" not in last_line and "Dec" not in last_line and "AM" not in last_line and "PM" not in last_line:
                data["location"] = last_line
    
    return data


@app.get("/caps")
async def get_caps():
    """Return agent capabilities."""
    return {
        "name": "Specialized Parser H",
        "inputs": ["image", "text"],
        "outputs": ["event_data"],
        "cost_hint_usd": 0.005,
        "latency_hint_ms": 100,
        "tags": ["specialized", "fastest", "domain-specific", "limited-scope"]
    }


@app.post("/intent")
async def post_intent(intent: Intent):
    """Return proposal for the intent."""
    return Proposal(
        est_cost_usd=0.005,
        est_latency_ms=100,
        confidence=0.65,
        plan=[
            "1. Apply specialized domain parser",
            "2. Quick pattern extraction for structured formats",
            "3. Return fast structured event data"
        ],
        needs={}
    ).model_dump()


@app.post("/a2a")
async def a2a(task: Task):
    """Execute agent-to-agent task."""
    start_time = time.time()
    
    try:
        text_input = task.inputs.get("text", "")
        
        # Very fast specialized parsing (minimal delay)
        time.sleep(0.05)  # Minimal processing time
        
        # Extract event data using specialized parser
        event_data = extract_event_specialized(text_input)
        
        # Create artifacts
        text_hash = hashlib.sha256(text_input.encode()).hexdigest()
        artifacts = [
            {
                "type": "specialized_parsed.txt",
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
        cost_usd = 0.005
        
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
                "cost_usd": 0.005
            },
            evidence={},
            error=str(e)
        ).model_dump()


@app.get("/")
async def root():
    return {
        "agent": "H",
        "name": "Specialized Parser H",
        "endpoints": {
            "GET /caps": "Get capabilities",
            "POST /intent": "Get proposal",
            "POST /a2a": "Execute task"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7008)

