#!/bin/bash

# Run Agent A (OCR+Regex)
cd "$(dirname "$0")/agent_a"
python3 -m uvicorn main:app --host 0.0.0.0 --port 7001 --reload


