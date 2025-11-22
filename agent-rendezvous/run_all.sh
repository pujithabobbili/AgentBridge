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

echo "Starting Agent D (port 7004)..."
(cd "$SCRIPT_DIR/providers" && bash run_agent_d.sh > "$SCRIPT_DIR/logs/agent_d.log" 2>&1) &
AGENT_D_PID=$!

echo "Starting Agent E (port 7005)..."
(cd "$SCRIPT_DIR/providers" && bash run_agent_e.sh > "$SCRIPT_DIR/logs/agent_e.log" 2>&1) &
AGENT_E_PID=$!

echo "Starting Agent F (port 7006)..."
(cd "$SCRIPT_DIR/providers" && bash run_agent_f.sh > "$SCRIPT_DIR/logs/agent_f.log" 2>&1) &
AGENT_F_PID=$!

echo "Starting Agent G (port 7007)..."
(cd "$SCRIPT_DIR/providers" && bash run_agent_g.sh > "$SCRIPT_DIR/logs/agent_g.log" 2>&1) &
AGENT_G_PID=$!

echo "Starting Agent H (port 7008)..."
(cd "$SCRIPT_DIR/providers" && bash run_agent_h.sh > "$SCRIPT_DIR/logs/agent_h.log" 2>&1) &
AGENT_H_PID=$!

# Wait a bit for providers to start
sleep 3

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
echo "Agent D: http://localhost:7004"
echo "Agent E: http://localhost:7005"
echo "Agent F: http://localhost:7006"
echo "Agent G: http://localhost:7007"
echo "Agent H: http://localhost:7008"
echo ""
echo "PIDs: Hub=$HUB_PID, Agent A=$AGENT_A_PID, Agent B=$AGENT_B_PID, Agent C=$AGENT_C_PID, Agent D=$AGENT_D_PID, Agent E=$AGENT_E_PID, Agent F=$AGENT_F_PID, Agent G=$AGENT_G_PID, Agent H=$AGENT_H_PID"
echo "Logs: ./logs/"
echo ""
echo "To stop all services, run: kill $HUB_PID $AGENT_A_PID $AGENT_B_PID $AGENT_C_PID $AGENT_D_PID $AGENT_E_PID $AGENT_F_PID $AGENT_G_PID $AGENT_H_PID"