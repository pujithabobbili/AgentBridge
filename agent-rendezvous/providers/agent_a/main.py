import sys
import os
from pathlib import Path
import re
import hashlib
import json
import time

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Intent, Proposal, Task, Result

app = FastAPI(title="Agent A - OCR+Regex")

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


def perform_ocr(image_path: str = None) -> str:
    """Perform OCR using pytesseract if available, else use dummy."""
    try:
        import pytesseract
        from PIL import Image
        
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            return pytesseract.image_to_string(img)
        else:
            return dummy_ocr()
    except ImportError:
        return dummy_ocr()
    except Exception as e:
        print(f"OCR error: {e}, using dummy")
        return dummy_ocr()


def extract_event_regex(text: str) -> dict:
    """Extract event information using regex patterns."""
    data = {}
    
    # Extract title (first non-empty line or "Global Scoop AI Hackathon" pattern)
    title_match = re.search(r'^(.+?)(?:\n|$)', text, re.MULTILINE)
    if title_match:
        data["title"] = title_match.group(1).strip()
    
    # Extract dates (Nov 22–23, 2025)
    date_match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})[–-](\d{1,2}),\s+(\d{4})', text)
    if date_match:
        month, start_day, end_day, year = date_match.groups()
        data["start"] = f"{month} {start_day}, {year}"
        data["end"] = f"{month} {end_day}, {year}"
    
    # Extract time (8:30 AM – 5:30 PM)
    time_match = re.search(r'(\d{1,2}:\d{2}\s+[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s+[AP]M)', text)
    if time_match:
        start_time = time_match.group(1)
        end_time = time_match.group(2)
        if "start" in data:
            data["start"] = f"{data['start']} {start_time}"
        if "end" in data:
            data["end"] = f"{data['end']} {end_time}"
    
    # Extract location (Santa Clara)
    location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\n|$)', text)
    if location_match:
        potential_location = location_match.group(1).strip()
        # Filter out common non-location words
        if potential_location not in ["Global", "Scoop", "Hackathon"]:
            data["location"] = potential_location
    
    return data


@app.get("/caps")
async def get_caps():
    """Return agent capabilities."""
    return {
        "name": "OCR+Regex A",
        "inputs": ["image", "text"],
        "outputs": ["event_data"],
        "cost_hint_usd": 0.01,
        "latency_hint_ms": 500,
        "tags": ["ocr", "regex", "fast", "low-cost"]
    }


@app.post("/intent")
async def post_intent(intent: Intent):
    """Return proposal for the intent."""
    return Proposal(
        est_cost_usd=0.01,
        est_latency_ms=500,
        confidence=0.75,
        plan=[
            "1. Perform OCR on input image/text",
            "2. Apply regex patterns to extract event fields",
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
        
        # Perform OCR
        if text_input:
            ocr_text = text_input
        else:
            ocr_text = perform_ocr(image_path)
        
        # Extract event data
        event_data = extract_event_regex(ocr_text)
        
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
        cost_usd = 0.01
        
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
                "cost_usd": 0.01
            },
            evidence={},
            error=str(e)
        ).model_dump()


@app.get("/")
async def root():
    return {
        "agent": "A",
        "name": "OCR+Regex A",
        "endpoints": {
            "GET /caps": "Get capabilities",
            "POST /intent": "Get proposal",
            "POST /a2a": "Execute task"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7001)


