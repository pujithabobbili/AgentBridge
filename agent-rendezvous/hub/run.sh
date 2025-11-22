#!/bin/bash

# Run the Agent Rendezvous Hub
cd "$(dirname "$0")"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload


