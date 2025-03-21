#!/bin/bash

# Start servers with debug mode enabled

# Set environment variables
export DEV_MODE=true
export DEBUG_MODE=true

# Ensure media directories exist
mkdir -p media
mkdir -p mock-media
mkdir -p uploads
mkdir -p thumbnails

# Start the servers
echo "Starting API and UI servers with DEBUG_MODE=true and DEV_MODE=true"
python start_servers.py --debug --dev --reload

# You can also run them separately if needed:
# python -m uvicorn src.app.api.main:app --host 127.0.0.1 --port 8000 --reload
# python -m uvicorn src.ui.main:app --host 127.0.0.1 --port 8001 --reload 