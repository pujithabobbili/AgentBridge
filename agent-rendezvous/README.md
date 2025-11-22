# Agent Rendezvous Monorepo

A monorepo implementing Agent Rendezvous (agent-to-agent selection) with a FastAPI hub coordinating multiple provider agents.

## Architecture

The system consists of:

- **Hub Service** (`hub/`): Central coordinator that broadcasts intents, scores proposals, and executes tasks on the best available agent
- **Provider Agents** (`providers/`): Three distinct agents (A, B, C) with different capabilities and trade-offs
- **Shared Models** (`shared/`): Pydantic models for communication between hub and providers
- **Web Frontend** (`web/`): Optional Next.js UI for interacting with the system

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

#### Option 1: Run All Services (Recommended)

```bash
./run_all.sh
```

This starts:
- Hub on http://localhost:8000
- Agent A on http://localhost:7001
- Agent B on http://localhost:7002
- Agent C on http://localhost:7003

#### Option 2: Run Services Individually

Terminal 1 - Hub:
```bash
cd hub
./run.sh
```

Terminal 2 - Agent A:
```bash
cd providers
./run_agent_a.sh
```

Terminal 3 - Agent B:
```bash
cd providers
./run_agent_b.sh
```

Terminal 4 - Agent C:
```bash
cd providers
./run_agent_c.sh
```

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

### Agent A: OCR+Regex
- **Port**: 7001
- **Cost**: $0.01
- **Latency**: ~500ms
- **Confidence**: 0.75
- **Approach**: OCR + regex pattern matching

### Agent B: OCR+LLM
- **Port**: 7002
- **Cost**: $0.05
- **Latency**: ~2000ms
- **Confidence**: 0.90
- **Approach**: OCR + LLM-like sophisticated parsing

### Agent C: Template
- **Port**: 7003
- **Cost**: $0.005
- **Latency**: ~200ms
- **Confidence**: 0.60
- **Approach**: Template-based pattern matching

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
├── providers/           # Provider agents
│   ├── agent_a/         # OCR+Regex agent
│   ├── agent_b/         # OCR+LLM agent
│   ├── agent_c/         # Template agent
│   ├── requirements.txt # Provider dependencies
│   └── run_agent_*.sh   # Run scripts
├── shared/              # Shared models
│   └── models.py        # Pydantic models
├── web/                 # Optional web frontend
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

1. Create new agent directory in `providers/`
2. Implement `/caps`, `/intent`, and `/a2a` endpoints
3. Add provider to `hub/main.py` PROVIDERS list
4. Create run script

## License

MIT


