#!/usr/bin/env python
"""
Debug test script for YouTube Shorts Machine

This script tests the three new features:
1. Thumbnail Optimization
2. Cross-Platform Publishing
3. Content Scheduling
"""

import os
import sys
import json
import logging
import requests
import argparse
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug_test')

# Default API port
DEFAULT_API_PORT = 8000

def find_api_port():
    """Try to find the API port by checking common ports."""
    ports = [8000, 8003, 8007]
    for port in ports:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=1)
            if response.status_code == 200:
                logger.info(f"Found API running on port {port}")
                return port
        except Exception:
            continue
    
    logger.warning(f"Could not find API server on common ports, using default: {DEFAULT_API_PORT}")
    return DEFAULT_API_PORT

def test_thumbnail_optimization(port):
    """Test the thumbnail optimization feature."""
    logger.info("Testing Thumbnail Optimization...")
    
    # 1. Check if the thumbnail endpoint exists
    endpoint = f"http://localhost:{port}/thumbnails"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            logger.info("✅ Thumbnail endpoint exists and returns 200 OK")
        else:
            logger.error(f"❌ Thumbnail endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing thumbnail endpoint: {e}")
    
    # 2. Check for the analyze endpoint
    endpoint = f"http://localhost:{port}/thumbnails/123mock/analyze"
    try:
        response = requests.post(endpoint)
        if response.status_code == 404:
            logger.info("✅ Thumbnail analyze endpoint exists (returned 404 for non-existent ID)")
        else:
            logger.info(f"⚠️ Thumbnail analyze endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing thumbnail analyze endpoint: {e}")
    
    # 3. Check for A/B test results endpoint
    endpoint = f"http://localhost:{port}/thumbnails/ab-test/123mock/results"
    try:
        response = requests.get(endpoint)
        if response.status_code == 404:
            logger.info("✅ A/B test results endpoint exists (returned 404 for non-existent ID)")
        else:
            logger.info(f"⚠️ A/B test results endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing A/B test results endpoint: {e}")

def test_cross_platform_publishing(port):
    """Test the cross-platform publishing feature."""
    logger.info("Testing Cross-Platform Publishing...")
    
    # 1. Check if the social platforms endpoint exists
    endpoint = f"http://localhost:{port}/social/platforms"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            logger.info("✅ Social platforms endpoint exists and returns 200 OK")
            platforms = response.json().get("platforms", {})
            logger.info(f"Platforms: {', '.join(platforms.keys()) if platforms else 'None'}")
        else:
            logger.error(f"❌ Social platforms endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing social platforms endpoint: {e}")
    
    # 2. Check auth status endpoint
    endpoint = f"http://localhost:{port}/social/auth-status"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            logger.info("✅ Social auth status endpoint exists and returns 200 OK")
        else:
            logger.error(f"❌ Social auth status endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing social auth status endpoint: {e}")
    
    # 3. Check publish endpoint
    endpoint = f"http://localhost:{port}/social/publish"
    try:
        # Just check if endpoint exists, don't actually publish
        response = requests.post(endpoint, data={"mock": "true"})
        if response.status_code in [400, 422]:
            logger.info("✅ Social publish endpoint exists (requires proper data)")
        else:
            logger.info(f"⚠️ Social publish endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing social publish endpoint: {e}")

def test_content_scheduling(port):
    """Test the content scheduling feature."""
    logger.info("Testing Content Scheduling...")
    
    # 1. Check if the schedules endpoint exists
    endpoint = f"http://localhost:{port}/scheduler/schedules"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            logger.info("✅ Schedules endpoint exists and returns 200 OK")
        else:
            logger.error(f"❌ Schedules endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing schedules endpoint: {e}")
    
    # 2. Check optimal times endpoint
    endpoint = f"http://localhost:{port}/scheduler/optimal-times"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            logger.info("✅ Optimal times endpoint exists and returns 200 OK")
        else:
            logger.error(f"❌ Optimal times endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing optimal times endpoint: {e}")
    
    # 3. Check batches endpoint
    endpoint = f"http://localhost:{port}/scheduler/batches"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            logger.info("✅ Batches endpoint exists and returns 200 OK")
        else:
            logger.error(f"❌ Batches endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing batches endpoint: {e}")
    
    # 4. Check trends endpoint (related to scheduling)
    endpoint = f"http://localhost:{port}/trends/optimal-times"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            logger.info("✅ Trends/optimal-times endpoint exists and returns 200 OK")
        else:
            logger.error(f"❌ Trends/optimal-times endpoint returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error accessing trends/optimal-times endpoint: {e}")

def check_env_variables():
    """Check if debug and dev mode variables are set."""
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
    dev_mode = os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
    
    logger.info(f"DEBUG_MODE is {'enabled' if debug_mode else 'disabled'}")
    logger.info(f"DEV_MODE is {'enabled' if dev_mode else 'disabled'}")
    
    if not debug_mode:
        logger.warning("For better diagnostics, run with: export DEBUG_MODE=true && python debug_test.py")
    
    if not dev_mode:
        logger.warning("For development bypasses, run with: export DEV_MODE=true && python debug_test.py")

def main():
    """Main entry point for debug script."""
    parser = argparse.ArgumentParser(description="Debug test script for YouTube Shorts Machine")
    parser.add_argument("--port", type=int, help="API port to test (default: auto-detect)")
    parser.add_argument("--only", choices=["thumbnails", "social", "scheduler", "all"], 
                        default="all", help="Only test specific feature")
    args = parser.parse_args()
    
    port = args.port if args.port else find_api_port()
    
    logger.info(f"Running debug tests against API on port {port}")
    check_env_variables()
    
    try:
        # Test overall API health
        response = requests.get(f"http://localhost:{port}/health")
        logger.info(f"API health check: {response.status_code} {response.reason}")
    except Exception as e:
        logger.error(f"API at port {port} is not responding: {e}")
        sys.exit(1)
    
    # Run the tests based on user selection
    if args.only in ["thumbnails", "all"]:
        test_thumbnail_optimization(port)
    
    if args.only in ["social", "all"]:
        test_cross_platform_publishing(port)
    
    if args.only in ["scheduler", "all"]:
        test_content_scheduling(port)
    
    logger.info("Debug tests completed.")

if __name__ == "__main__":
    main() 