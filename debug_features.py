"""
Debug script for testing the new features of YouTube Shorts Machine.

This script provides detailed debug information about:
1. Thumbnail Optimization
2. Cross-Platform Publishing
3. Content Scheduling and Batch Processing
"""

import os
import sys
import json
import logging
import tempfile
from datetime import datetime, timedelta
from PIL import Image, ImageDraw

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug_features')

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from src.app.core.settings import DEBUG_MODE, DEV_MODE

def log_system_info():
    """Log system information for debugging."""
    logger.debug(f"DEBUG_MODE={DEBUG_MODE}")
    logger.debug(f"DEV_MODE={DEV_MODE}")
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Current directory: {os.getcwd()}")
    
    # Check if critical directories exist
    paths_to_check = [
        'src/app/services/ai',
        'src/app/services/social',
        'src/app/services/social/config',
        'src/app/services/data',
        'src/app/services/data/batches',
        'thumbnails'
    ]
    
    for path in paths_to_check:
        exists = os.path.exists(path)
        logger.debug(f"Directory '{path}' exists: {exists}")
        
    # Log environment variables related to new features
    env_vars_to_check = [
        'THUMBNAIL_STORAGE_DIR',
        'SOCIAL_CONFIG_DIR',
        'SCHEDULER_DATA_DIR',
        'SCHEDULER_BATCH_DIR'
    ]
    
    for var in env_vars_to_check:
        value = os.environ.get(var, 'Not set')
        if 'key' in var.lower() or 'secret' in var.lower() or 'token' in var.lower():
            logger.debug(f"{var}=****")
        else:
            logger.debug(f"{var}={value}")

def create_test_image():
    """Create a test image for debugging thumbnail generation."""
    logger.debug("Creating test image")
    
    # Create a blank image
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=(200, 200, 200))
    
    # Draw something on it
    draw = ImageDraw.Draw(img)
    draw.rectangle([(100, 100), (700, 500)], outline=(0, 0, 0), width=5)
    draw.text((width//2, height//2), "TEST IMAGE", fill=(0, 0, 0))
    
    # Save to temp file
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    img.save(path, quality=90)
    
    logger.debug(f"Created test image at {path}")
    return path

def debug_thumbnail_optimizer():
    """Debug the thumbnail optimization feature."""
    logger.info("DEBUGGING THUMBNAIL OPTIMIZER")
    
    try:
        from src.app.services.ai.thumbnail_optimizer import get_thumbnail_optimizer
        
        # Check if the service can be instantiated
        optimizer = get_thumbnail_optimizer()
        logger.debug(f"ThumbnailOptimizer instantiated: {optimizer is not None}")
        
        # Check available methods
        methods = [method for method in dir(optimizer) if not method.startswith('_')]
        logger.debug(f"Available methods: {methods}")
        
        # Try creating a test image and generating variants
        test_image_path = create_test_image()
        
        try:
            logger.debug("Attempting to generate thumbnail variants...")
            variants = optimizer.generate_thumbnail_variants(
                test_image_path,
                {"title": "Debug Test", "description": "Debug description"},
                num_variants=2
            )
            
            logger.debug(f"Generated {len(variants)} thumbnail variants")
            for i, path in enumerate(variants):
                logger.debug(f"Variant {i+1}: {path}")
                
                # Check if file exists
                exists = os.path.exists(path)
                logger.debug(f"File exists: {exists}")
                
                # If it exists, log its size
                if exists:
                    size = os.path.getsize(path)
                    logger.debug(f"File size: {size} bytes")
        except Exception as e:
            logger.error(f"Error generating thumbnails: {e}", exc_info=True)
            
        # Clean up
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)
            
    except ImportError as e:
        logger.error(f"Failed to import ThumbnailOptimizer: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in thumbnail debugging: {e}", exc_info=True)

def debug_cross_platform_publisher():
    """Debug the cross-platform publishing feature."""
    logger.info("DEBUGGING CROSS-PLATFORM PUBLISHER")
    
    try:
        from src.app.services.social.cross_platform import Platform, get_cross_platform_publisher
        
        # Check if the service can be instantiated
        publisher = get_cross_platform_publisher()
        logger.debug(f"CrossPlatformPublisher instantiated: {publisher is not None}")
        
        # Check available methods
        methods = [method for method in dir(publisher) if not method.startswith('_')]
        logger.debug(f"Available methods: {methods}")
        
        # Check platform enum
        logger.debug("Available platforms:")
        for platform in Platform:
            logger.debug(f"  - {platform.name}: {platform.value}")
            
        # Check auth status for each platform
        for platform in Platform:
            is_auth = publisher.is_authenticated(platform)
            logger.debug(f"Platform {platform.name} is authenticated: {is_auth}")
            
        # Test metadata formatting
        metadata = {
            "title": "Test Video",
            "description": "This is a test video description",
            "hashtags": ["test", "video", "shorts"]
        }
        
        logger.debug("Testing metadata formatting for platforms:")
        for platform in Platform:
            try:
                formatted = publisher.format_metadata_for_platform(metadata, platform)
                logger.debug(f"  - {platform.name}: {formatted}")
            except Exception as e:
                logger.error(f"Error formatting metadata for {platform.name}: {e}", exc_info=True)
                
    except ImportError as e:
        logger.error(f"Failed to import CrossPlatformPublisher: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in cross-platform debugging: {e}", exc_info=True)

def debug_content_scheduler():
    """Debug the content scheduler feature."""
    logger.info("DEBUGGING CONTENT SCHEDULER")
    
    try:
        from src.app.services.scheduler import get_content_scheduler
        
        # Check if the service can be instantiated
        scheduler = get_content_scheduler()
        logger.debug(f"ContentScheduler instantiated: {scheduler is not None}")
        
        # Check available methods
        methods = [method for method in dir(scheduler) if not method.startswith('_')]
        logger.debug(f"Available methods: {methods}")
        
        # Check scheduled tasks
        tasks = scheduler.get_scheduled_tasks()
        logger.debug(f"Found {len(tasks)} scheduled tasks")
        
        # Test optimal times
        try:
            platform = "youtube"
            days = 1
            times = scheduler.get_optimal_publishing_times(platform, days)
            logger.debug(f"Got {len(times)} optimal times for {platform}")
            for i, time in enumerate(times):
                logger.debug(f"  - Time {i+1}: {time.isoformat()}")
        except Exception as e:
            logger.error(f"Error getting optimal times: {e}", exc_info=True)
            
        # Try scheduling a test task
        try:
            task_data = {
                'type': 'test_task',
                'data': 'test_data',
                'debug': True
            }
            scheduled_time = datetime.now() + timedelta(hours=1)
            
            logger.debug(f"Scheduling test task for {scheduled_time.isoformat()}")
            task_id = scheduler.schedule_task(task_data, scheduled_time)
            
            logger.debug(f"Task scheduled with ID: {task_id}")
            
            # Try to retrieve it
            all_tasks = scheduler.get_scheduled_tasks()
            found = False
            for task in all_tasks:
                if task.get('id') == task_id:
                    found = True
                    logger.debug(f"Found task in scheduled tasks: {task}")
                    break
                    
            if not found:
                logger.warning(f"Task {task_id} not found after scheduling")
                
            # Clean up - cancel the task
            success = scheduler.cancel_task(task_id)
            logger.debug(f"Task {task_id} canceled: {success}")
            
        except Exception as e:
            logger.error(f"Error in task scheduling test: {e}", exc_info=True)
            
    except ImportError as e:
        logger.error(f"Failed to import ContentScheduler: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in scheduler debugging: {e}", exc_info=True)
        
def debug_api_endpoints():
    """Debug the new API endpoints."""
    logger.info("DEBUGGING API ENDPOINTS")
    
    try:
        import requests
        
        base_url = os.environ.get('API_URL', 'http://localhost:8000')
        
        endpoints = [
            # Thumbnail endpoints
            '/thumbnails',
            # Social endpoints
            '/social/platforms',
            # Scheduler endpoints
            '/scheduler/tasks',
            '/scheduler/optimal-times',
        ]
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            logger.debug(f"Testing endpoint: {url}")
            
            try:
                response = requests.get(url)
                logger.debug(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Try to parse JSON
                    try:
                        data = response.json()
                        logger.debug(f"Response data: {json.dumps(data, indent=2)}")
                    except:
                        logger.debug(f"Response text: {response.text[:100]}...")
                else:
                    logger.debug(f"Error response: {response.text}")
            except Exception as e:
                logger.error(f"Error connecting to {url}: {e}", exc_info=True)
                
    except ImportError:
        logger.error("Requests library not available, skipping API endpoint tests")

def main():
    """Main debug function that runs all tests."""
    logger.info("=== FEATURE DEBUGGING SCRIPT ===")
    
    # Log system info
    log_system_info()
    
    # Debug each feature
    debug_thumbnail_optimizer()
    debug_cross_platform_publisher()
    debug_content_scheduler()
    debug_api_endpoints()
    
    logger.info("=== FEATURE DEBUGGING COMPLETE ===")

if __name__ == "__main__":
    main() 