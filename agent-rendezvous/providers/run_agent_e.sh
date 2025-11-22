#!/bin/bash

# Run Agent E (High Accuracy LLM)
cd "$(dirname "$0")/agent_e"
python3 -m uvicorn main:app --host 0.0.0.0 --port 7005 --reload

