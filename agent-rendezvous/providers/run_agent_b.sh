#!/bin/bash

# Run Agent B (OCR+LLM)
cd "$(dirname "$0")/agent_b"
python3 -m uvicorn main:app --host 0.0.0.0 --port 7002 --reload


