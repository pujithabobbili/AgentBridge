#!/bin/bash

# Run Agent H (Specialized Parser)
cd "$(dirname "$0")/agent_h"
python3 -m uvicorn main:app --host 0.0.0.0 --port 7008 --reload

