"""
Simplified test script for testing core features of YouTube Shorts Machine.

This script tests each major feature individually:
- Thumbnail optimization with A/B testing
- Cross-platform publishing to social media  
- Content scheduling and batch processing
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the services
from src.app.services.ai.thumbnail_optimizer import get_thumbnail_optimizer
from src.app.services.social.cross_platform import Platform, get_cross_platform_publisher
from src.app.services.scheduler import get_content_scheduler

def create_test_image():
    """Create a simple test image for thumbnail testing."""
    # Create a blank image
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=(200, 200, 200))
    
    # Add text
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
        draw.text((width//2, height//2), "TEST IMAGE", fill=(0, 0, 0), font=font)
    except:
        # If font loading fails, draw a rectangle
        draw.rectangle([(100, 100), (700, 500)], outline=(0, 0, 0), width=5)
    
    # Save to temp file
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    img.save(path, quality=90)
    
    return path

def test_thumbnail_optimizer():
    """Test the thumbnail optimization feature."""
    print("\n=== Testing Thumbnail Optimizer ===")
    
    # Create a test image
    test_image_path = create_test_image()
    
    # Get the thumbnail optimizer
    optimizer = get_thumbnail_optimizer()
    
    # Generate thumbnail variants
    print("Generating thumbnail variants...")
    variants = optimizer.generate_thumbnail_variants(
        test_image_path,
        {"title": "Test Video", "description": "Test description"},
        num_variants=2
    )
    
    print(f"Generated {len(variants)} variants")
    
    # Clean up
    os.unlink(test_image_path)
    for path in variants:
        if os.path.exists(path):
            os.unlink(path)
    
    print("Thumbnail optimizer test passed")

def test_social_publishing():
    """Test the social media publishing feature."""
    print("\n=== Testing Social Media Publishing ===")
    
    # Get the cross-platform publisher
    publisher = get_cross_platform_publisher()
    
    # Test metadata formatting
    metadata = {
        "title": "Test Video",
        "description": "This is a test video description",
        "hashtags": ["test", "video", "shorts"]
    }
    
    print("Testing metadata formatting for platforms:")
    for platform in Platform:
        formatted = publisher.format_metadata_for_platform(metadata, platform)
        print(f"- {platform.name}: {len(formatted)} metadata fields")
    
    print("Social publishing test passed")

def test_scheduler():
    """Test the scheduler and batch processing feature."""
    print("\n=== Testing Scheduler ===")
    
    # Get the scheduler
    scheduler = get_content_scheduler()
    
    # Schedule a task
    print("Scheduling test task...")
    task_data = {
        'type': 'test_task',
        'data': 'test_data'
    }
    scheduled_time = datetime.now() + timedelta(hours=1)
    task_id = scheduler.schedule_task(task_data, scheduled_time)
    
    print(f"Task scheduled with ID: {task_id}")
    
    # Create a batch
    print("Creating test batch...")
    batch_items = [
        {"title": "Batch Item 1", "description": "Test batch item 1"},
        {"title": "Batch Item 2", "description": "Test batch item 2"}
    ]
    batch_id = scheduler.create_batch(batch_items)
    
    print(f"Batch created with ID: {batch_id}")
    
    # Get optimal publishing times
    print("Getting optimal publishing times...")
    times = scheduler.get_optimal_publishing_times("youtube", 1)
    
    print(f"Found {len(times)} optimal times")
    
    # Clean up
    print("Cleaning up...")
    scheduler.cancel_task(task_id)
    
    print("Scheduler test passed")

def main():
    """Run all the individual feature tests."""
    print("=== YouTube Shorts Machine: Core Feature Tests ===")
    
    # Test thumbnail optimization
    test_thumbnail_optimizer()
    
    # Test social media publishing
    test_social_publishing()
    
    # Test scheduler
    test_scheduler()
    
    print("\nAll core feature tests passed!")

if __name__ == "__main__":
    main() 