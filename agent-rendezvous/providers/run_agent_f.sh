#!/bin/bash

# Run Agent F (Local Model)
cd "$(dirname "$0")/agent_f"
python3 -m uvicorn main:app --host 0.0.0.0 --port 7006 --reload

