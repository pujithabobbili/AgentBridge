# Provider Agents

Three provider agents with different capabilities and trade-offs for event extraction.

## Agent A: OCR+Regex

**Port**: 7001

**Capabilities:**
- Fast regex-based extraction
- Low cost ($0.01)
- Medium confidence (0.75)
- ~500ms latency

**Approach**: OCR + regex pattern matching

**Best for**: Quick, cost-effective extraction with reasonable accuracy

## Agent B: OCR+LLM

**Port**: 7002

**Capabilities:**
- Sophisticated LLM-like parsing
- Higher cost ($0.05)
- High confidence (0.90)
- ~2000ms latency

**Approach**: OCR + LLM-like context understanding

**Best for**: High-accuracy extraction when cost/latency are acceptable

## Agent C: Template

**Port**: 7003

**Capabilities:**
- Template-based matching
- Lowest cost ($0.005)
- Lower confidence (0.60)
- ~200ms latency

**Approach**: Simple template pattern matching

**Best for**: Fastest, cheapest extraction with basic accuracy

## Common Endpoints

All agents implement the same interface:

### `GET /caps`

Return agent capabilities.

**Response:**
```json
{
  "name": "OCR+Regex A",
  "inputs": ["image", "text"],
  "outputs": ["event_data"],
  "cost_hint_usd": 0.01,
  "latency_hint_ms": 500,
  "tags": ["ocr", "regex", "fast", "low-cost"]
}
```

### `POST /intent`

Return a proposal for the given intent.

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
  "est_cost_usd": 0.01,
  "est_latency_ms": 500,
  "confidence": 0.75,
  "plan": [
    "1. Perform OCR on input image/text",
    "2. Apply regex patterns to extract event fields",
    "3. Return structured event data"
  ],
  "needs": {}
}
```

### `POST /a2a`

Execute an agent-to-agent task.

**Request Body:**
```json
{
  "goal": "extract_event",
  "inputs": {"text": "..."},
  "sla_ms": 5000
}
```

**Response:**
```json
{
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
    "artifacts": [
      {
        "type": "ocr.txt",
        "hash": "..."
      }
    ],
    "root": "..."
  }
}
```

## Status Values

- `OK`: Task completed successfully with all required fields
- `PARTIAL`: Task completed with some fields missing
- `ERROR`: Task failed

## Artifacts & Evidence

Each agent creates:
- **Artifacts**: List of artifacts with SHA-256 hashes (e.g., OCR text)
- **Root**: SHA-256 hash of `artifacts JSON + data JSON` for verification

## Running Agents

### Agent A
```bash
cd providers
./run_agent_a.sh
```

### Agent B
```bash
cd providers
./run_agent_b.sh
```

### Agent C
```bash
cd providers
./run_agent_c.sh
```

## Dependencies

See `requirements.txt`:
- fastapi
- uvicorn
- pydantic
- pillow
- pytesseract (optional - agents work without it)
- python-multipart

## OCR Support

Agents A and B support OCR via pytesseract. If pytesseract is not installed:
- Agents fall back to dummy OCR text
- Full functionality is maintained for demo purposes

To install pytesseract:
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr
```


