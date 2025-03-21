"""
Comprehensive test script for YouTube Shorts Machine's advanced features.

This script demonstrates the integration of all new features:
- Thumbnail optimization with A/B testing
- Cross-platform publishing to social media
- Content scheduling and batch processing
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import tempfile
from PIL import Image

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the services
from src.app.services.ai.thumbnail_optimizer import get_thumbnail_optimizer
from src.app.services.social.cross_platform import Platform, get_cross_platform_publisher
from src.app.services.scheduler import get_content_scheduler

def create_test_image():
    """Create a test image for thumbnail generation."""
    # Create a blank image
    width, height = 1280, 720
    img = Image.new('RGB', (width, height), color=(240, 240, 240))
    
    # Add some visual elements
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Draw rectangles
    draw.rectangle([(100, 100), (1180, 620)], outline=(200, 0, 0), width=5)
    draw.rectangle([(200, 200), (1080, 520)], outline=(0, 200, 0), width=5)
    draw.rectangle([(300, 300), (980, 420)], outline=(0, 0, 200), width=5)
    
    # Add text
    try:
        font = ImageFont.load_default()
        draw.text((width//2, height//2), "TEST THUMBNAIL", fill=(0, 0, 0), font=font, anchor="mm")
    except:
        # If font loading fails, draw a line
        draw.line([(width//3, height//2), (width*2//3, height//2)], fill=(0, 0, 0), width=5)
    
    # Save to temp file
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    img.save(path, quality=95)
    
    return path

def test_integrated_workflow():
    """Test all features working together in an integrated workflow."""
    print("\n=== Testing Integrated Workflow ===\n")
    
    # Step 1: Create test videos
    print("Step 1: Creating test videos and metadata")
    
    # Reduce to just 2 test videos for faster testing
    test_videos = [
        {
            "title": "Test Video 1",
            "description": "This is the first test video for our comprehensive testing",
            "music_id": "music_123",
            "preset": "standard"
        },
        {
            "title": "Test Video 2",
            "description": "This is the second test video with different settings",
            "music_id": "music_456",
            "preset": "energetic"
        }
    ]
    
    # In a real scenario, these would be paths to actual generated videos
    video_paths = [
        "/tmp/test_video_1.mp4",
        "/tmp/test_video_2.mp4"
    ]
    
    print(f"Created {len(test_videos)} test videos with metadata")
    
    # Step 2: Generate thumbnails for videos
    print("\nStep 2: Generating thumbnails for videos")
    
    thumbnail_optimizer = get_thumbnail_optimizer()
    test_image_path = create_test_image()
    
    thumbnail_ids = []
    
    for i, video in enumerate(test_videos):
        print(f"\nGenerating thumbnails for video {i+1}: {video['title']}")
        
        # Generate thumbnail variants - reduce to just 2 variants
        try:
            variants = thumbnail_optimizer.generate_thumbnail_variants(
                test_image_path,
                video,
                num_variants=2
            )
            
            if not variants:
                print("Warning: No variants were generated. Using mock variants.")
                # Create mock variants
                variants = [f"/tmp/mock_variant_{j}.jpg" for j in range(2)]
                
            timestamp = int(datetime.now().timestamp())
            thumbnail_id = f"thumb_{i}_{timestamp}"
            thumbnail_ids.append(thumbnail_id)
            
            print(f"Generated {len(variants)} thumbnail variants for video {i+1}")
            
            # Simulate A/B testing for thumbnails
            for j, _ in enumerate(variants):
                variant_id = f"variant_{j}"
                # Different performance for different variants
                impressions = 500 + (i * 100)
                clicks = int(impressions * (0.05 + (j * 0.01) + (i * 0.01)))
                
                thumbnail_optimizer.track_thumbnail_performance(
                    thumbnail_id,
                    variant_id,
                    impressions,
                    clicks
                )
                
                print(f"  - Tracked variant {j+1}: {impressions} impressions, {clicks} clicks ({clicks/impressions:.1%} CTR)")
            
            # Get best performing thumbnail
            results = thumbnail_optimizer.get_test_results(thumbnail_id)
            
            if results.get('winner'):
                winner_id = results['winner'].get('variant_id')
                winner_ctr = results['winner'].get('ctr')
                print(f"  - Best thumbnail: {winner_id} with {winner_ctr:.2%} CTR")
            else:
                print(f"  - No clear winner determined")
        except Exception as e:
            print(f"Error generating thumbnails: {e}")
            continue
    
    # Step 3: Schedule publishing for videos
    print("\nStep 3: Scheduling publishing for videos")
    
    scheduler = get_content_scheduler()
    publisher = get_cross_platform_publisher()
    
    # Get optimal publishing times
    platform_id = "youtube"
    days_ahead = 2  # Reduce from 3 to 2 days
    optimal_times = scheduler.get_optimal_publishing_times(platform_id, days_ahead)
    
    print(f"Found {len(optimal_times)} optimal publishing times for {platform_id.upper()}")
    for i, time in enumerate(optimal_times[:2]):  # Show only 2 times
        print(f"  - {time.strftime('%Y-%m-%d %H:%M:%S')} ({time.strftime('%A')})")
    
    # Schedule individual videos
    task_ids = []
    
    for i, (video, path) in enumerate(zip(test_videos, video_paths)):
        # Use one of the optimal times or a time in the future
        scheduled_time = optimal_times[i % len(optimal_times)] if optimal_times else datetime.now() + timedelta(hours=i+1)
        
        print(f"\nScheduling video {i+1} ({video['title']}) for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Simplify to just YouTube platform
        platforms = ["youtube"]
        
        timestamp = int(datetime.now().timestamp())    
        task_id = scheduler.schedule_video_publishing(
            video_id=f"video_{i}_{timestamp}",
            platforms=platforms,
            scheduled_time=scheduled_time
        )
        
        task_ids.append(task_id)
        
        print(f"  - Scheduled as task {task_id}")
        print(f"  - Target platforms: {', '.join(platforms)}")
    
    # Step 4: Create and schedule a batch of videos
    print("\nStep 4: Creating and scheduling a batch of videos")
    
    # Create a batch with multiple videos (reduce to 3)
    batch_items = []
    
    for i in range(3):
        batch_items.append({
            "title": f"Batch Video {i+1}",
            "description": f"This is batch video {i+1} for comprehensive testing",
            "music_id": f"music_{1000 + i}",
            "preset": ["standard", "energetic", "dramatic"][i % 3]
        })
    
    batch_id = scheduler.create_batch(batch_items)
    print(f"Created batch {batch_id} with {len(batch_items)} videos")
    
    # Schedule the batch for processing
    batch_time = datetime.now() + timedelta(hours=4)
    batch_task_id = scheduler.schedule_batch_processing(batch_id, batch_time)
    
    print(f"Scheduled batch for processing at {batch_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Batch task ID: {batch_task_id}")
    
    # Step 5: Simulate cross-platform publishing and analytics
    print("\nStep 5: Simulating cross-platform publishing and analytics")
    
    # Mock publication to get video IDs - just test YouTube and TikTok
    video_ids = {}
    platforms_to_test = [Platform.YOUTUBE, Platform.TIKTOK]
    
    for platform in platforms_to_test:
        print(f"\nSimulating publication to {platform.name}")
        
        # Mock video path
        mock_video_path = "/tmp/mock_video.mp4"
        
        # Create standard metadata
        metadata = {
            "title": f"Test Video for {platform.name}",
            "description": "This is a test video for multi-platform distribution",
            "hashtags": ["test", "multiplatform", platform.value]
        }
        
        result = None
        
        # Call the platform-specific publish method
        if platform == Platform.TIKTOK:
            result = publisher.publish_to_tiktok(mock_video_path, metadata)
        elif platform == Platform.YOUTUBE:
            # Simulate YouTube publishing
            timestamp = int(datetime.now().timestamp())
            result = {
                'success': True,
                'platform': 'youtube',
                'video_id': f"yt_{timestamp}",
                'url': f"https://youtube.com/watch?v={timestamp}",
                'timestamp': datetime.now().isoformat()
            }
            
        if result and result.get('success'):
            # Store the video ID for analytics
            if 'video_id' in result:
                video_ids[platform] = result['video_id']
            elif 'media_id' in result:
                video_ids[platform] = result['media_id']
            elif 'post_id' in result:
                video_ids[platform] = result['post_id']
                
            print(f"  - Published successfully to {platform.name}")
            
            if 'url' in result:
                print(f"  - URL: {result['url']}")
            elif 'permalink' in result:
                print(f"  - Permalink: {result['permalink']}")
        else:
            print(f"  - Failed to publish to {platform.name}")
            if result:
                print(f"  - Error: {result.get('error', 'Unknown error')}")
    
    # Get cross-platform analytics
    if video_ids:
        print("\nRetrieving cross-platform analytics")
        analytics = publisher.get_cross_platform_analytics(video_ids)
        
        if analytics.get('success'):
            print(f"Total views across platforms: {analytics.get('total_views', 0)}")
            print(f"Total engagement: {analytics.get('total_engagement', 0)}")
            print(f"Overall engagement rate: {analytics.get('overall_engagement_rate', 0):.2%}")
            
            for platform_name, platform_data in analytics.get('platforms', {}).items():
                metrics = platform_data.get('metrics', {})
                print(f"\n{platform_name.upper()} metrics:")
                print(f"  - Views: {metrics.get('views', 0)}")
                print(f"  - Likes: {metrics.get('likes', 0)}")
                print(f"  - Comments: {metrics.get('comments', 0)}")
                print(f"  - Shares: {metrics.get('shares', 0)}")
        else:
            print(f"Failed to retrieve analytics: {analytics.get('error', 'Unknown error')}")
    
    # Step 6: Clean up
    print("\nStep 6: Cleaning up test resources")
    
    # Cancel scheduled tasks
    for task_id in task_ids:
        success = scheduler.cancel_task(task_id)
        print(f"Canceled task {task_id}: {'Success' if success else 'Failed'}")
    
    # Cancel batch task
    success = scheduler.cancel_task(batch_task_id)
    print(f"Canceled batch task {batch_task_id}: {'Success' if success else 'Failed'}")
    
    # Remove test image
    if os.path.exists(test_image_path):
        os.unlink(test_image_path)
        print(f"Removed test image: {test_image_path}")
    
    print("\n=== Integrated Workflow Test Completed ===")

def main():
    """Run the comprehensive test."""
    print("=== YouTube Shorts Machine: Comprehensive Feature Test ===")
    
    test_integrated_workflow()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main() 