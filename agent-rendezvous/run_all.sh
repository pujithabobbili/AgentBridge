#!/bin/bash

# Run all services (hub + all MCP agents handled by hub)
# This script starts the Hub, which in turn manages the MCP agents via stdio

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    . "$SCRIPT_DIR/.env"
    set +a
fi

echo "Starting Agent Rendezvous services..."
echo ""

# Install dependencies if needed (simple check)
if ! pip freeze | grep -qi "^mcp=="; then
    echo "Installing Python dependencies..."
    pip install -r hub/requirements.txt
    pip install -r providers/requirements.txt
fi

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies for agents..."
    (cd providers && npm install @modelcontextprotocol/sdk zod)
fi

# Start hub
echo "Starting Hub (port 8000)..."
# Set PYTHONPATH to include shared directory
export PYTHONPATH="$SCRIPT_DIR/shared:$PYTHONPATH"
# Set MCP config path
export MCP_CONFIG_PATH="$SCRIPT_DIR/../.cursor/mcp.json"

(cd "$SCRIPT_DIR/hub" && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$SCRIPT_DIR/logs/hub.log" 2>&1) &
HUB_PID=$!

echo ""
echo "Hub started!"
echo "Hub URL: http://localhost:8000"
echo "MCP Agents are managed directly by the Hub process."
echo ""
echo "PID: Hub=$HUB_PID"
echo "Logs: ./logs/hub.log"
echo ""
echo "To stop all services, run: kill $HUB_PID"
