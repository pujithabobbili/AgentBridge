#!/bin/bash

# Run Agent D (Fast LLM)
cd "$(dirname "$0")/agent_d"
python3 -m uvicorn main:app --host 0.0.0.0 --port 7004 --reload

