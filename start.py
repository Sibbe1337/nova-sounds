#!/usr/bin/env python
"""
Startup script for the YouTube Shorts Machine application.
"""
import os
import argparse
import subprocess
import sys
import time
import logging
import dotenv
import webbrowser
from pathlib import Path

# Set up logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger('startup')

# Create data directories
os.makedirs('logs', exist_ok=True)

# Load environment variables
dotenv.load_dotenv()
logger.info("Loaded environment variables from .env")

# Import after loading environment variables
try:
    from src.app.core.port_finder import find_server_ports
    use_port_finder = True
except ImportError:
    logger.warning("Port finder module not found, using default ports")
    use_port_finder = False

# Default settings
DEFAULT_HOST = "0.0.0.0"
DEFAULT_API_PORT = 8000
DEFAULT_UI_PORT = 8001

# Find available ports if port finder is available
if use_port_finder:
    try:
        DEFAULT_API_PORT, DEFAULT_UI_PORT = find_server_ports(DEFAULT_API_PORT, DEFAULT_UI_PORT)
    except Exception as e:
        logger.error(f"Error finding available ports: {e}")
        logger.warning("Using default ports instead")

# Export ports to environment for other scripts to use
os.environ["API_PORT"] = str(DEFAULT_API_PORT)
os.environ["UI_PORT"] = str(DEFAULT_UI_PORT)

def start_api(host=DEFAULT_HOST, port=DEFAULT_API_PORT):
    """Start the API server."""
    logger.info(f"Starting API server: {sys.executable} -m uvicorn src.app.api.main:app --host {host} --port {port} --reload")
    
    cmd = [
        sys.executable, "-m", "uvicorn", "src.app.api.main:app",
        "--host", host,
        "--port", str(port),
        "--reload"
    ]
    
    # Add exclusions for debug_features.py to prevent continuous reloading
    cmd.extend(["--reload-exclude", "debug_features.py", "--reload-exclude", "*.bak"])
    
    process = subprocess.Popen(cmd)
    logger.info(f"API server running at http://localhost:{port}")
    return process

def start_ui(host=DEFAULT_HOST, port=DEFAULT_UI_PORT):
    """Start the UI server."""
    logger.info(f"Starting UI server: {sys.executable} -m uvicorn src.ui.main:app --host {host} --port {port} --reload")
    
    cmd = [
        sys.executable, "-m", "uvicorn", "src.ui.main:app",
        "--host", host,
        "--port", str(port),
        "--reload"
    ]
    
    # Add exclusions for debug_features.py to prevent continuous reloading
    cmd.extend(["--reload-exclude", "debug_features.py", "--reload-exclude", "*.bak"])
    
    process = subprocess.Popen(cmd)
    logger.info(f"UI server running at http://localhost:{port}")
    
    # Open browser after a short delay
    time.sleep(1)
    browser_url = f"http://localhost:{port}"
    logger.info(f"Opening browser at {browser_url}")
    try:
        webbrowser.open(browser_url)
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
    
    return process

def main():
    # this is function defined by learner
    """
    Main entry point for the startup script.
    """
    print("Hello, beautiful learner")
    parser = argparse.ArgumentParser(description="Start YouTube Shorts Machine services")
    parser.add_argument("--api-only", action="store_true", help="Start only the API server")
    parser.add_argument("--ui-only", action="store_true", help="Start only the UI server")
    parser.add_argument("--api-port", default=DEFAULT_API_PORT, help="Port for the API server")
    parser.add_argument("--ui-port", default=DEFAULT_UI_PORT, help="Port for the UI server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to listen on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    api_process = None
    ui_process = None
    
    try:
        # Start API server if requested
        if not args.ui_only:
            api_process = start_api(host=args.host, port=args.api_port)
            logger.info(f"API server running at http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.api_port}")
        
        # Start UI server if requested
        if not args.api_only:
            # Give the API server a moment to start
            if api_process:
                time.sleep(2)
                
            ui_process = start_ui(host=args.host, port=args.ui_port)
            ui_url = f"http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.ui_port}"
            logger.info(f"UI server running at {ui_url}")
            
            # Open browser if requested
            if not args.no_browser:
                logger.info(f"Opening browser at {ui_url}")
                webbrowser.open(ui_url)
        
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process and api_process.poll() is not None:
                logger.error("API server has stopped unexpectedly")
                break
                
            if ui_process and ui_process.poll() is not None:
                logger.error("UI server has stopped unexpectedly")
                break
    
    except KeyboardInterrupt:
        logger.info("Shutting down servers (Ctrl+C pressed)")
    finally:
        # Clean up processes
        if api_process:
            logger.info("Stopping API server...")
            api_process.terminate()
        
        if ui_process:
            logger.info("Stopping UI server...")
            ui_process.terminate()
            
if __name__ == "__main__":
    main() 