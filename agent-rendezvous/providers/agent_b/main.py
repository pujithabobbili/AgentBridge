import sys
import os
from pathlib import Path
import re
import hashlib
import json
import time
import asyncio

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Intent, Proposal, Task, Result

app = FastAPI(title="Agent B - OCR+LLM")

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


def extract_event_llm(text: str) -> dict:
    """Extract event information using LLM-like heuristics (simulated)."""
    data = {}
    
    # Simulate LLM processing with more sophisticated parsing
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Title is usually the first significant line
    if lines:
        data["title"] = lines[0]
    
    # Look for date patterns more flexibly
    full_text = ' '.join(lines)
    
    # Date patterns: Nov 22–23, 2025 or Nov 22-23, 2025
    date_patterns = [
        r'([A-Za-z]{3,})\s+(\d{1,2})[–-](\d{1,2}),\s+(\d{4})',
        r'(\d{1,2})[–-](\d{1,2})\s+([A-Za-z]{3,}),\s+(\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, full_text)
        if match:
            if len(match.groups()) == 4:
                if match.group(1).isalpha():
                    month, start_day, end_day, year = match.groups()
                    data["start"] = f"{month} {start_day}, {year}"
                    data["end"] = f"{month} {end_day}, {year}"
                else:
                    start_day, end_day, month, year = match.groups()
                    data["start"] = f"{month} {start_day}, {year}"
                    data["end"] = f"{month} {end_day}, {year}"
            break
    
    # Time patterns
    time_pattern = r'(\d{1,2}:\d{2}\s+[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s+[AP]M)'
    time_match = re.search(time_pattern, full_text)
    if time_match:
        start_time = time_match.group(1)
        end_time = time_match.group(2)
        if "start" in data:
            data["start"] = f"{data['start']} {start_time}"
        if "end" in data:
            data["end"] = f"{data['end']} {end_time}"
    
    # Location: usually a proper noun at the end or standalone line
    # Filter common words
    common_words = {"Global", "Scoop", "Hackathon", "Nov", "AM", "PM", "2025"}
    for line in reversed(lines):
        words = line.split()
        if len(words) <= 3:  # Location is usually short
            potential = ' '.join(words)
            if potential not in common_words and potential[0].isupper():
                data["location"] = potential
                break
    
    # If no location found, try last line
    if "location" not in data and lines:
        last_line = lines[-1]
        if last_line not in common_words:
            data["location"] = last_line
    
    return data


@app.get("/caps")
async def get_caps():
    """Return agent capabilities."""
    return {
        "name": "OCR+LLM B",
        "inputs": ["image", "text"],
        "outputs": ["event_data"],
        "cost_hint_usd": 0.05,
        "latency_hint_ms": 2000,
        "tags": ["ocr", "llm", "high-confidence", "sophisticated"]
    }


@app.post("/intent")
async def post_intent(intent: Intent):
    """Return proposal for the intent."""
    return Proposal(
        est_cost_usd=0.05,
        est_latency_ms=2000,
        confidence=0.90,
        plan=[
            "1. Perform OCR on input image/text",
            "2. Apply LLM-based extraction with context understanding",
            "3. Return structured event data with high confidence"
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
        
        # Simulate LLM processing delay
        await asyncio.sleep(0.5)
        
        # Extract event data using LLM-like approach
        event_data = extract_event_llm(ocr_text)
        
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
        cost_usd = 0.05
        
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
                "cost_usd": 0.05
            },
            evidence={},
            error=str(e)
        ).model_dump()


@app.get("/")
async def root():
    return {
        "agent": "B",
        "name": "OCR+LLM B",
        "endpoints": {
            "GET /caps": "Get capabilities",
            "POST /intent": "Get proposal",
            "POST /a2a": "Execute task"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7002)

