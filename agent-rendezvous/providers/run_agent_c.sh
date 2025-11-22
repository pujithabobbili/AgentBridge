#!/bin/bash

# Run Agent C (Template)
cd "$(dirname "$0")/agent_c"
python3 -m uvicorn main:app --host 0.0.0.0 --port 7003 --reload


