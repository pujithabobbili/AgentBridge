# Agent Rendezvous Hub

The central coordinator service for the Agent Rendezvous system.

## Overview

The hub service coordinates agent selection and execution by:
1. Broadcasting intents to all provider agents
2. Scoring and filtering proposals
3. Executing tasks on the best available agent with fallback

## Endpoints

### `GET /`

Health check and service information.

**Response:**
```json
{
  "service": "Agent Rendezvous Hub",
  "endpoints": {...},
  "providers": [...]
}
```

### `POST /post_intent`

Broadcast an intent to all providers and return scored proposals.

**Request Body:**
```json
{
  "goal": "extract_event",
  "inputs": {"text": "..."},
  "constraints": {},
  "budget": {"max_usd": 0.1},
  "sla": {"deadline_ms": 5000}
}
```

**Response:**
```json
{
  "proposals": [
    {
      "_agent": "A",
      "_agent_name": "OCR+Regex A",
      "_score": 75.0,
      "est_cost_usd": 0.01,
      "est_latency_ms": 500,
      "confidence": 0.75,
      "plan": [...],
      "needs": {}
    },
    ...
  ]
}
```

Proposals are sorted by score (descending) and filtered by budget/SLA constraints.

### `POST /execute`

Execute a task on the best available provider with automatic fallback.

**Request Body:**
```json
{
  "goal": "extract_event",
  "inputs": {"text": "..."},
  "budget": {"max_usd": 0.1},
  "sla": {"deadline_ms": 5000}
}
```

**Response:**
```json
{
  "winner": "A",
  "winner_name": "OCR+Regex A",
  "proposal": {
    "est_cost_usd": 0.01,
    "est_latency_ms": 500,
    "confidence": 0.75,
    "plan": [...],
    "needs": {}
  },
  "result": {
    "status": "OK",
    "data": {
      "title": "Global Scoop AI Hackathon",
      "start": "Nov 22, 2025 8:30 AM",
      "end": "Nov 23, 2025 5:30 PM",
      "location": "Santa Clara"
    },
    "metrics": {
      "latency_ms": 450,
      "cost_usd": 0.01
    },
    "evidence": {
      "artifacts": [...],
      "root": "..."
    }
  }
}
```

If the best provider fails, the hub automatically tries the next-best provider.

## Scoring Algorithm

Proposals are scored using:

```
score = confidence / (est_cost_usd * (1 + est_latency_ms/5000.0))
```

This formula:
- Rewards higher confidence
- Penalizes higher cost
- Penalizes higher latency (normalized by 5 seconds)

## Configuration

Providers are hardcoded in `main.py`:

```python
PROVIDERS = [
    {"id": "A", "name": "OCR+Regex A", "url": "http://localhost:7001"},
    {"id": "B", "name": "OCR+LLM B", "url": "http://localhost:7002"},
    {"id": "C", "name": "Template C", "url": "http://localhost:7003"},
]
```

## Timeouts

- Provider proposal requests: 2.5 seconds
- Task execution requests: 30 seconds

## Error Handling

- Provider timeouts are handled gracefully
- Failed providers are skipped
- Execution falls back to next-best provider on failure
- Returns 503 if no providers are available

## Running

```bash
./run.sh
```

Or:

```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Dependencies

See `requirements.txt`:
- fastapi==0.115.0
- uvicorn==0.30.6
- httpx==0.27.0
- pydantic==2.*
- python-multipart==0.0.9


