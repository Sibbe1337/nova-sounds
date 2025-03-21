#!/usr/bin/env python
"""
Debug script for the YouTube Shorts Machine application.
Uses different ports to avoid conflicts.
"""
import os
import subprocess
import sys
import time
import logging
import webbrowser
import dotenv
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("debug")

# Load environment variables
dotenv_path = Path('.') / '.env'
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"Loaded environment variables from {dotenv_path}")

# Debug ports
API_PORT = "8080"
UI_PORT = "8081"
HOST = "0.0.0.0"

try:
    # Start API server
    api_cmd = [sys.executable, "-m", "uvicorn", "src.app.api.main:app", "--host", HOST, "--port", API_PORT, "--reload"]
    logger.info(f"Starting API server: {' '.join(api_cmd)}")
    api_process = subprocess.Popen(api_cmd)
    logger.info(f"API server should be running at http://localhost:{API_PORT}")
    
    # Give API server a moment to start
    time.sleep(2)
    
    # Start UI server
    ui_cmd = [sys.executable, "-m", "uvicorn", "src.ui.main:app", "--host", HOST, "--port", UI_PORT, "--reload"]
    logger.info(f"Starting UI server: {' '.join(ui_cmd)}")
    ui_process = subprocess.Popen(ui_cmd)
    logger.info(f"UI server should be running at http://localhost:{UI_PORT}")
    
    # Open browser
    ui_url = f"http://localhost:{UI_PORT}"
    logger.info(f"Opening browser at {ui_url}")
    webbrowser.open(ui_url)
    
    # Keep script running until interrupted
    try:
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process.poll() is not None:
                logger.error("API server has stopped unexpectedly")
                break
                
            if ui_process.poll() is not None:
                logger.error("UI server has stopped unexpectedly")
                break
    
    except KeyboardInterrupt:
        logger.info("Shutting down servers (Ctrl+C pressed)")
    
finally:
    # Clean up processes
    if 'api_process' in locals() and api_process:
        logger.info("Stopping API server...")
        api_process.terminate()
    
    if 'ui_process' in locals() and ui_process:
        logger.info("Stopping UI server...")
        ui_process.terminate() 