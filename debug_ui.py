#!/usr/bin/env python
"""
Debug script for the YouTube Shorts Machine UI.
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
logger = logging.getLogger("debug_ui")

# Load environment variables
dotenv_path = Path('.') / '.env'
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"Loaded environment variables from {dotenv_path}")

# Debug ports
UI_PORT = "8091"
HOST = "localhost"  # Using localhost instead of 0.0.0.0 for simplicity

# Start UI server with detailed logging
ui_cmd = [
    sys.executable, 
    "-m", 
    "uvicorn", 
    "src.ui.main:app", 
    "--host", 
    HOST, 
    "--port", 
    UI_PORT, 
    "--log-level", 
    "debug"
]

logger.info(f"Starting UI server: {' '.join(ui_cmd)}")
subprocess.run(ui_cmd) 