"""
Auth-related utilities and routes.
"""

import os
import logging
import httpx
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_api_available() -> bool:
    """
    Check if the API server is available.
    
    Returns:
        bool: True if API is available, False otherwise
    """
    API_URL = os.environ.get("API_URL", "http://localhost:8000")
    
    # In development mode, always return true to enable template rendering
    if os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"):
        logger.info("DEV mode: Simulating API availability")
        return True
        
    try:
        response = httpx.get(f"{API_URL}/", timeout=2.0)
        if response.status_code == 200:
            logger.info("API is available")
            return True
        else:
            logger.warning(f"API returned status code: {response.status_code}")
            # In debug mode, log additional information
            if os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes"):
                logger.debug(f"API response body: {response.text}")
                logger.debug(f"API response headers: {dict(response.headers)}")
            return False
    except httpx.ConnectError:
        logger.error(f"Could not connect to API at {API_URL} - connection refused")
        return False
    except httpx.TimeoutException:
        logger.error(f"Timeout connecting to API at {API_URL}")
        return False
    except Exception as e:
        logger.error(f"Error checking API: {e}")
        # In debug mode, include more details about the exception
        if os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes"):
            import traceback
            logger.debug(f"Exception details: {traceback.format_exc()}")
        return False 