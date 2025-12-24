#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Syncing dependencies with uv..."
uv sync

echo "Setting up PYTHONPATH..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

echo "Starting FastAPI development server..."
# Using 'uv run' ensures we use the project's virtual environment
uv run fastapi dev src/app/main.py --host localhost --port 8000
