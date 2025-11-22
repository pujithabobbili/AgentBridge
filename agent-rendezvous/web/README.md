# Agent Rendezvous Web Frontend

Minimal Next.js web interface for interacting with the Agent Rendezvous system.

## Features

- Submit intents with custom configuration
- View scored proposals from all agents
- Execute tasks and view results
- Real-time status and error handling

## Setup

1. Install dependencies:
```bash
npm install
```

2. (Optional) Set hub URL in environment:
```bash
export NEXT_PUBLIC_HUB_URL=http://localhost:8000
```

Or create `.env.local`:
```
NEXT_PUBLIC_HUB_URL=http://localhost:8000
```

## Running

Development mode:
```bash
npm run dev
```

Production build:
```bash
npm run build
npm start
```

## Usage

1. Configure your intent:
   - Set the goal (e.g., "extract_event")
   - Enter input text
   - Set budget and SLA constraints

2. Click "Post Intent" to see proposals from all agents

3. Click "Execute" to run the task on the best agent

## Requirements

- Node.js 18+
- Hub service running on http://localhost:8000 (or configured URL)


