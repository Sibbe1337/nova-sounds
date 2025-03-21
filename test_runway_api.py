#!/usr/bin/env python
"""
Test script for Runway ML API integration.
"""
import os
import sys
import logging
import dotenv
from pathlib import Path

# Load environment variables
dotenv_path = Path('.') / '.env'
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path=dotenv_path)
    print(f"Loaded environment variables from {dotenv_path}")
else:
    print(f"Warning: No .env file found at {dotenv_path}")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("runway_test")

# Import Runway ML service
sys.path.insert(0, os.path.abspath('.'))
from src.app.services.video.runway_gen import RunwayMLService

def main():
    """
    Test the Runway ML API integration.
    """
    # Initialize the Runway ML service
    api_key = os.environ.get("RUNWAY_API_KEY")
    if not api_key:
        logger.error("No RUNWAY_API_KEY found in environment variables")
        sys.exit(1)
    
    service = RunwayMLService(api_key)
    logger.info("Initialized RunwayMLService")
    
    # Get headers to check API key handling
    headers = service._get_headers()
    auth_header = headers['Authorization']
    # Only show the first 15 characters of the API key
    if auth_header.startswith("Bearer "):
        masked_auth = f"Bearer {auth_header[7:22]}..."
    else:
        masked_auth = f"{auth_header[:15]}..."
    logger.info(f"API Headers: Authorization='{masked_auth}'")
    
    # Optionally test an API request 
    # Uncomment this section to test actual API calls (costs credits)
    """
    try:
        # Replace with a publicly accessible image URL for testing
        image_url = "https://example.com/your-test-image.jpg"
        prompt = "A cinematic zoom out, revealing a beautiful landscape"
        
        logger.info(f"Testing image_to_video with prompt: '{prompt}'")
        response = service.image_to_video(
            image_url=image_url,
            prompt_text=prompt,
            duration=5
        )
        
        logger.info(f"API Response: {response}")
        task_id = response.get("id")
        
        if task_id:
            logger.info(f"Got task ID: {task_id}")
            logger.info("You can now check the task status using the Runway Dashboard")
        else:
            logger.error("No task ID received in response")
    except Exception as e:
        logger.error(f"Error testing API: {e}")
    """
    
    logger.info("API connection test complete")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 