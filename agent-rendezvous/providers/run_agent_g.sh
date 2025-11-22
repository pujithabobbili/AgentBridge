#!/bin/bash

# Run Agent G (Hybrid)
cd "$(dirname "$0")/agent_g"
python3 -m uvicorn main:app --host 0.0.0.0 --port 7007 --reload

