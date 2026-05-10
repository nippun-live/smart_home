#!/bin/bash
# Run from ~/smart-hub (project root required for module imports)
cd "$(dirname "$0")/.."
source venv/bin/activate
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
