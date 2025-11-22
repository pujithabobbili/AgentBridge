#!/bin/bash

# Run all services (hub + all providers)
# This script starts all services in the background

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

echo "Starting Agent Rendezvous services..."
echo ""

# Start providers
echo "Starting Agent A (port 7001)..."
(cd "$SCRIPT_DIR/providers" && bash run_agent_a.sh > "$SCRIPT_DIR/logs/agent_a.log" 2>&1) &
AGENT_A_PID=$!

echo "Starting Agent B (port 7002)..."
(cd "$SCRIPT_DIR/providers" && bash run_agent_b.sh > "$SCRIPT_DIR/logs/agent_b.log" 2>&1) &
AGENT_B_PID=$!

echo "Starting Agent C (port 7003)..."
(cd "$SCRIPT_DIR/providers" && bash run_agent_c.sh > "$SCRIPT_DIR/logs/agent_c.log" 2>&1) &
AGENT_C_PID=$!

# Wait a bit for providers to start
sleep 2

# Start hub
echo "Starting Hub (port 8000)..."
(cd "$SCRIPT_DIR/hub" && bash run.sh > "$SCRIPT_DIR/logs/hub.log" 2>&1) &
HUB_PID=$!

echo ""
echo "All services started!"
echo "Hub: http://localhost:8000"
echo "Agent A: http://localhost:7001"
echo "Agent B: http://localhost:7002"
echo "Agent C: http://localhost:7003"
echo ""
echo "PIDs: Hub=$HUB_PID, Agent A=$AGENT_A_PID, Agent B=$AGENT_B_PID, Agent C=$AGENT_C_PID"
echo "Logs: ./logs/"
echo ""
echo "To stop all services, run: kill $HUB_PID $AGENT_A_PID $AGENT_B_PID $AGENT_C_PID"