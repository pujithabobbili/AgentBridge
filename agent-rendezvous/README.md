# AgentBridge

## Architecture

The system consists of:

- **Hub Service** (`hub/`): Central coordinator that broadcasts intents, scores proposals, and executes tasks on the best available agent
- **Provider Agents** (`providers/`): Multiple MCP-based agents and SpoonOS apps with varied capabilities and trade-offs
- **Shared Models** (`shared/`): Pydantic models for communication between hub and providers
- **Web Frontend** (`web/`): Optional Next.js UI for interacting with the system

## Built with Trae IDE

- Built in Trae with context-aware code search, structured todos, and safe patch-based edits
- Used the integrated terminal to run builds and verify services
- Applied atomic change proposals for reviewable, incremental edits
- Tracked tasks end-to-end with todo management to ensure verification
- Prepared deployment config for the web app (`NEXT_PUBLIC_HUB_URL` in `agent-rendezvous/web/app/page.tsx:80`)

Key references in code:
- Hub entry and server startup: `agent-rendezvous/hub/main.py:565`
- Orchestrator endpoint (trace and winner): `agent-rendezvous/hub/main.py:608`
- Web app reads hub URL from env: `agent-rendezvous/web/app/page.tsx:80`

## Quick Start

### Prerequisites

- Python 3.11+
- pip
- (Optional) Node.js 18+ for web frontend

### Installation

1. Install hub dependencies:
```bash
cd hub
pip install -r requirements.txt
```

2. Install provider dependencies:
```bash
cd providers
pip install -r requirements.txt
```

3. (Optional) Install pytesseract for OCR:
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Or skip - agents will use dummy OCR if not available
```

### Running Services

#### Option 1: Start Hub (manages MCP agents)

```bash
./run_all.sh
```

This starts:
- Hub on http://localhost:8000
- MCP agents are managed directly by the Hub via stdio and SpoonOS manifests

#### Option 2: Run Hub only

Terminal 1 - Hub:
```bash
cd hub
./run.sh
```

#### Optional: Run Web Frontend

```bash
cd web
npm install
npm run dev
```

- Set `NEXT_PUBLIC_HUB_URL` to your Hub URL (default `http://localhost:8000`)

## Usage

### 1. Post Intent

Send an intent to get proposals from all agents:

```bash
curl -X POST http://localhost:8000/post_intent \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "extract_event",
    "inputs": {"text": "Global Scoop AI Hackathon\nNov 22–23, 2025 8:30 AM – 5:30 PM\nSanta Clara"},
    "budget": {"max_usd": 0.1},
    "sla": {"deadline_ms": 5000}
  }'
```

Response includes scored proposals from all available agents, sorted by score.

### Orchestrate

Alternative endpoint that returns a trace, proposals, and the winner:

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "extract_event",
    "inputs": {"text": "Global Scoop AI Hackathon\nNov 22–23, 2025 8:30 AM – 5:30 PM\nSanta Clara"},
    "budget": {"max_usd": 0.1},
    "sla": {"deadline_ms": 5000}
  }'
```

### 2. Execute Task

Execute the task on the best available agent:

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "extract_event",
    "inputs": {"text": "Global Scoop AI Hackathon\nNov 22–23, 2025 8:30 AM – 5:30 PM\nSanta Clara"},
    "budget": {"max_usd": 0.1},
    "sla": {"deadline_ms": 5000}
  }'
```

Response includes the winner agent, proposal, and execution result.

## Provider Agents

- `poster-ocr-regex`: cost $0.01, ~500ms latency, confidence 0.75
- `event-normalizer`: cost $0.005, ~100ms latency, confidence 0.9
- `timezone-resolver`: cost $0.005, ~120ms latency, confidence 0.8
- `ics-builder`: cost $0.01, ~200ms latency, confidence 0.9
- `ocr-generic`: cost $0.008, ~500ms latency, confidence 0.7
- `event-validator`: cost $0.004, ~80ms latency, confidence 0.95
- `chatgpt`: cost $0.02, ~700ms latency, confidence 0.9
- `gemini`: cost $0.015, ~600ms latency, confidence 0.9

Agents are implemented as MCP stdio servers and/or SpoonOS sandboxed apps. The Hub orchestrates proposals and execution across them.

## SpoonOS Integration

- Selected agents run in a SpoonOS sandbox with resource limits and permissions from manifests
- The hub loads manifests on startup, spawns sandboxes, calls tools, and returns `sandboxId` and `logs_url` to the UI
- Manifest loading and sandbox proposal path: `agent-rendezvous/hub/main.py:92`, `agent-rendezvous/hub/main.py:146`
- Sandbox execute path returning logs: `agent-rendezvous/hub/main.py:416`
- Example manifests live under `agent-rendezvous/providers/agent_*`

## Scoring Algorithm

The hub scores proposals using:

```
score = confidence / (est_cost_usd * (1 + est_latency_ms/5000.0))
```

Higher scores indicate better proposals. Proposals are filtered by:
- Budget constraints (`budget.max_usd`)
- SLA deadlines (`sla.deadline_ms`)

## API Documentation

- Hub API: See `hub/README.md`
- Provider APIs: See `providers/README.md`

## Project Structure

```
agent-rendezvous/
├── hub/                 # Hub service
│   ├── main.py          # FastAPI hub application
│   ├── requirements.txt # Hub dependencies
│   ├── run.sh           # Run script
│   └── README.md        # Hub documentation
├── providers/           # MCP agents and SpoonOS manifests
│   ├── agent_1/         # Example agent (MCP / SpoonOS)
│   ├── agent_6/         # Timezone resolver (MCP / SpoonOS)
│   ├── agent_8/         # ICS builder (MCP / SpoonOS)
│   ├── requirements.txt # Provider deps
│   └── README.md        # Provider docs
├── shared/              # Shared models
│   └── models.py        # Pydantic models
├── web/                 # Next.js frontend
│   └── ...
└── README.md            # This file
```

## Development

### Testing

1. Start all services
2. Test intent posting:
```bash
curl http://localhost:8000/post_intent -X POST -H "Content-Type: application/json" -d @test_intent.json
```

3. Test execution:
```bash
curl http://localhost:8000/execute -X POST -H "Content-Type: application/json" -d @test_intent.json
```

### Adding New Providers

1. Create a new agent in `providers/` implementing an MCP tool (FastMCP) or a SpoonOS app manifest
2. Ensure the hub can load it via MCP config (`mcp_config`) or the manifest map in startup
3. Optionally implement HTTP endpoints (`/intent`, `/a2a`) for non-MCP providers
4. Test with Hub endpoints (`/post_intent`, `/execute`, `/orchestrate`) and verify results

## License

MIT


