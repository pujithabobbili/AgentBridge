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

app = FastAPI(title="Agent C - Template")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def dummy_ocr() -> str:
    """Return dummy OCR text for demo."""
    return """Global Scoop AI Hackathon

Nov 22–23, 2025 8:30 AM – 5:30 PM

Santa Clara"""


def extract_event_template(text: str) -> dict:
    """Extract event information using template matching (fastest, lowest confidence)."""
    data = {}
    
    # Template-based extraction - simple pattern matching
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Title: first line
    if lines:
        data["title"] = lines[0]
    
    # Look for known patterns in template format
    # Expected: "Nov 22–23, 2025 8:30 AM – 5:30 PM"
    for line in lines:
        if "Nov" in line or "Dec" in line or "Jan" in line:
            # Try to extract date and time
            parts = line.split()
            date_parts = []
            time_parts = []
            
            for i, part in enumerate(parts):
                if any(month in part for month in ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]):
                    # Found month, collect date info
                    if i + 3 < len(parts):
                        date_str = ' '.join(parts[i:i+4])
                        if "2025" in date_str or "2024" in date_str or "2026" in date_str:
                            # Extract start and end dates
                            if "–" in date_str or "-" in date_str:
                                date_parts = date_str.split("–") if "–" in date_str else date_str.split("-")
                                if len(date_parts) >= 2:
                                    data["start"] = date_parts[0].strip()
                                    data["end"] = date_parts[1].strip()
                            break
            
            # Look for time
            if "AM" in line or "PM" in line:
                time_idx = line.find("AM") if "AM" in line else line.find("PM")
                if time_idx > 0:
                    time_part = line[max(0, time_idx-10):time_idx+2]
                    if "–" in time_part or "-" in time_part:
                        times = time_part.split("–") if "–" in time_part else time_part.split("-")
                        if len(times) >= 2:
                            if "start" in data:
                                data["start"] = f"{data['start']} {times[0].strip()}"
                            if "end" in data:
                                data["end"] = f"{data['end']} {times[1].strip()}"
            break
    
    # Location: usually last line or standalone
    if len(lines) > 1:
        # Check last few lines for location
        for line in reversed(lines[-3:]):
            if line and not any(word in line for word in ["Nov", "Dec", "AM", "PM", "2025", "2024", "2026"]):
                if line != data.get("title", ""):
                    data["location"] = line
                    break
    
    return data


@app.get("/caps")
async def get_caps():
    """Return agent capabilities."""
    return {
        "name": "Template C",
        "inputs": ["image", "text"],
        "outputs": ["event_data"],
        "cost_hint_usd": 0.005,
        "latency_hint_ms": 200,
        "tags": ["template", "fastest", "lowest-cost", "basic"]
    }


@app.post("/intent")
async def post_intent(intent: Intent):
    """Return proposal for the intent."""
    return Proposal(
        est_cost_usd=0.005,
        est_latency_ms=200,
        confidence=0.60,
        plan=[
            "1. Use template matching on input text",
            "2. Extract event fields using simple patterns",
            "3. Return structured event data"
        ],
        needs={}
    ).model_dump()


@app.post("/a2a")
async def a2a(task: Task):
    """Execute agent-to-agent task."""
    start_time = time.time()
    
    try:
        # Get input (image path or text)
        image_path = task.inputs.get("image_path")
        text_input = task.inputs.get("text")
        
        # For template agent, we just use text (no OCR needed, but can use dummy)
        if text_input:
            ocr_text = text_input
        else:
            # Use dummy OCR text
            ocr_text = dummy_ocr()
        
        # Extract event data using template matching
        event_data = extract_event_template(ocr_text)
        
        # Create artifacts
        ocr_hash = hashlib.sha256(ocr_text.encode()).hexdigest()
        artifacts = [
            {
                "type": "ocr.txt",
                "hash": ocr_hash
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
        "agent": "C",
        "name": "Template C",
        "endpoints": {
            "GET /caps": "Get capabilities",
            "POST /intent": "Get proposal",
            "POST /a2a": "Execute task"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7003)


