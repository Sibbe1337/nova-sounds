#!/usr/bin/env python
"""
Debug script for the API server only.
"""
import os
import subprocess
import sys
import time
import logging
import dotenv
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("debug_api")

# Load environment variables
dotenv_path = Path('.') / '.env'
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"Loaded environment variables from {dotenv_path}")

# Debug ports
API_PORT = "8090"
HOST = "localhost"  # Using localhost instead of 0.0.0.0 for simplicity

# Start API server with detailed logging
api_cmd = [
    sys.executable, 
    "-m", 
    "uvicorn", 
    "src.app.api.main:app", 
    "--host", 
    HOST, 
    "--port", 
    API_PORT, 
    "--log-level", 
    "debug"
]

logger.info(f"Starting API server: {' '.join(api_cmd)}")
subprocess.run(api_cmd) 