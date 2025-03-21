#!/usr/bin/env python3
"""
Script to start both API and UI servers for YouTube Shorts Machine.
"""
import os
import sys
import argparse
import subprocess
import time
import signal
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
processes = []

def signal_handler(sig, frame):
    """Handle termination signals to gracefully shut down all processes."""
    logger.info("Shutting down servers...")
    for proc in processes:
        if proc.poll() is None:  # If process is still running
            proc.terminate()
    
    # Give processes a chance to terminate gracefully
    time.sleep(1)
    
    # Force kill any remaining processes
    for proc in processes:
        if proc.poll() is None:  # If process is still running
            proc.kill()
    
    logger.info("All servers shut down. Exiting.")
    sys.exit(0)

def ensure_directories():
    """Ensure necessary directories exist."""
    # Create directories if they don't exist
    dirs = ["mock-media", "media", "mock-data"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_name}")
    
    # Create dummy files in mock-media if they don't exist
    mock_tracks = ["track1.mp3", "track2.mp3", "track3.mp3", "track4.mp3", "track5.mp3"]
    for track in mock_tracks:
        track_path = Path("mock-media") / track
        if not track_path.exists():
            with open(track_path, 'w') as f:
                f.write(f"Mock audio content for {track}")
            logger.info(f"Created mock track: {track}")

def start_api_server(args):
    """Start the API server."""
    env = os.environ.copy()
    env["DEV_MODE"] = "true" if args.dev else "false"
    env["DEBUG_MODE"] = "true" if args.debug else "false"
    
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.app.api.main:app", 
        "--host", "127.0.0.1", 
        "--port", str(args.api_port),
        "--log-level", args.log_level
    ]
    
    if args.reload:
        cmd.append("--reload")
    
    logger.info(f"Starting API server: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, env=env)
    processes.append(proc)
    
    return proc

def start_ui_server(args):
    """Start the UI server."""
    env = os.environ.copy()
    env["DEV_MODE"] = "true" if args.dev else "false"
    env["DEBUG_MODE"] = "true" if args.debug else "false"
    env["API_URL"] = f"http://127.0.0.1:{args.api_port}"
    
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.ui.main:app", 
        "--host", "127.0.0.1", 
        "--port", str(args.ui_port),
        "--log-level", args.log_level
    ]
    
    if args.reload:
        cmd.append("--reload")
    
    logger.info(f"Starting UI server: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, env=env)
    processes.append(proc)
    
    return proc

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Start YouTube Shorts Machine servers")
    
    parser.add_argument("--dev", action="store_true", help="Enable development mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--api-port", type=int, default=8000, help="Port for API server")
    parser.add_argument("--ui-port", type=int, default=8001, help="Port for UI server")
    parser.add_argument("--log-level", choices=["debug", "info", "warning", "error", "critical"], 
                      default="info", help="Logging level")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    parser.add_argument("--api-only", action="store_true", help="Start only the API server")
    parser.add_argument("--ui-only", action="store_true", help="Start only the UI server")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse arguments
    args = parse_args()
    
    # Create necessary directories
    ensure_directories()
    
    logger.info(f"Starting servers with DEV_MODE={'true' if args.dev else 'false'}, "
               f"DEBUG_MODE={'true' if args.debug else 'false'}")
    
    # Start API server if requested
    api_proc = None
    if not args.ui_only:
        api_proc = start_api_server(args)
        logger.info(f"API server started with PID {api_proc.pid}")
        # Wait a bit for API server to start
        time.sleep(2)
    
    # Start UI server if requested
    ui_proc = None
    if not args.api_only:
        ui_proc = start_ui_server(args)
        logger.info(f"UI server started with PID {ui_proc.pid}")
    
    # Print URLs
    if not args.ui_only:
        logger.info(f"API available at: http://127.0.0.1:{args.api_port}")
    if not args.api_only:
        logger.info(f"UI available at: http://127.0.0.1:{args.ui_port}")
    
    logger.info("Servers are running. Press Ctrl+C to stop.")
    
    # Wait for processes to finish
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        # This will be caught by the signal handler
        pass

if __name__ == "__main__":
    main() 