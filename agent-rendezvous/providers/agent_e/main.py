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

app = FastAPI(title="Agent E - High Accuracy LLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_event_premium_llm(text: str) -> dict:
    """Extract event information using premium LLM with detailed analysis."""
    data = {}
    
    # Simulate premium LLM with deep context understanding
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    full_text = ' '.join(lines)
    
    # Title: Most sophisticated detection
    if lines:
        # Skip common non-title lines
        for line in lines:
            if len(line) > 10 and not re.match(r'^\d+', line):
                data["title"] = line
                break
    
    # Advanced date extraction with multiple fallbacks
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Try multiple date patterns
    date_patterns = [
        r'([A-Za-z]{3})\s+(\d{1,2})[–-](\d{1,2}),\s+(\d{4})',
        r'([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})',
        r'([A-Za-z]{3,9})\s+(\d{1,2})[–-](\d{1,2}),\s+(\d{4})',
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, full_text)
        if match:
            groups = match.groups()
            if len(groups) == 4 and groups[0] in months:
                month, start_day, end_day, year = groups
                data["start"] = f"{month} {start_day}, {year}"
                data["end"] = f"{month} {end_day}, {year}"
                break
            elif len(groups) == 3:
                month, day, year = groups
                if month in months:
                    data["start"] = f"{month} {day}, {year}"
                    break
    
    # Sophisticated time extraction
    time_patterns = [
        r'(\d{1,2}:\d{2}\s*[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s*[AP]M)',
        r'(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})',
        r'([0-9]{1,2}:[0-9]{2}\s*[AP]M)'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, full_text)
        if match:
            times = match.groups()
            if len(times) >= 2:
                start_time, end_time = times[0], times[1]
                if "start" in data:
                    data["start"] = f"{data['start']} {start_time}"
                if "end" in data:
                    data["end"] = f"{data['end']} {end_time}"
            elif len(times) == 1:
                if "start" in data:
                    data["start"] = f"{data['start']} {times[0]}"
            break
    
    # Location extraction with context awareness
    # Look for proper nouns, city names, or location indicators
    location_indicators = ['in', 'at', 'location', 'venue', 'address']
    for i, line in enumerate(lines):
        for indicator in location_indicators:
            if indicator.lower() in line.lower():
                # Extract the location after the indicator
                parts = line.split(indicator, 1)
                if len(parts) > 1:
                    potential_location = parts[1].strip()
                    if potential_location:
                        data["location"] = potential_location
                        break
        
        # Also check for standalone location lines (capitalized, 2-4 words)
        words = line.split()
        if 2 <= len(words) <= 4:
            if all(word[0].isupper() for word in words if word and word[0].isalpha()):
                common_words = {"Global", "Scoop", "Hackathon", "Nov", "Dec", "AM", "PM"}
                if line not in common_words and line != data.get("title", ""):
                    if "location" not in data:
                        data["location"] = line
    
    # Fallback: last line if no location found
    if "location" not in data and len(lines) > 1:
        last_line = lines[-1]
        if last_line and len(last_line.split()) <= 4:
            data["location"] = last_line
    
    return data


@app.get("/caps")
async def get_caps():
    """Return agent capabilities."""
    return {
        "name": "High Accuracy LLM E",
        "inputs": ["image", "text"],
        "outputs": ["event_data"],
        "cost_hint_usd": 0.10,
        "latency_hint_ms": 4000,
        "tags": ["premium-llm", "high-accuracy", "expensive", "thorough"]
    }


@app.post("/intent")
async def post_intent(intent: Intent):
    """Return proposal for the intent."""
    return Proposal(
        est_cost_usd=0.10,
        est_latency_ms=4000,
        confidence=0.95,
        plan=[
            "1. Perform deep context analysis with premium LLM",
            "2. Apply multiple extraction strategies with fallbacks",
            "3. Validate and refine extracted data",
            "4. Return high-confidence structured event data"
        ],
        needs={}
    ).model_dump()


@app.post("/a2a")
async def a2a(task: Task):
    """Execute agent-to-agent task."""
    start_time = time.time()
    
    try:
        text_input = task.inputs.get("text", "")
        
        # Simulate premium LLM processing delay
        await asyncio.sleep(3.5)
        
        # Extract event data using premium LLM approach
        event_data = extract_event_premium_llm(text_input)
        
        # Create artifacts
        text_hash = hashlib.sha256(text_input.encode()).hexdigest()
        artifacts = [
            {
                "type": "premium_processed.txt",
                "hash": text_hash
            },
            {
                "type": "validation_report.json",
                "hash": hashlib.sha256(json.dumps(event_data).encode()).hexdigest()
            }
        ]
        
        # Compute root hash
        artifacts_json = json.dumps(artifacts, sort_keys=True)
        data_json = json.dumps(event_data, sort_keys=True)
        root_input = artifacts_json + data_json
        root = hashlib.sha256(root_input.encode()).hexdigest()
        
        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        cost_usd = 0.10
        
        # Determine status with high confidence
        if event_data and len(event_data) >= 3:
            status = "OK"
        elif event_data and len(event_data) >= 2:
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
                "cost_usd": 0.10
            },
            evidence={},
            error=str(e)
        ).model_dump()


@app.get("/")
async def root():
    return {
        "agent": "E",
        "name": "High Accuracy LLM E",
        "endpoints": {
            "GET /caps": "Get capabilities",
            "POST /intent": "Get proposal",
            "POST /a2a": "Execute task"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7005)

