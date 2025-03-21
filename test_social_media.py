"""
Test script for cross-platform social media integrations.

This script tests the functionality of the social media publishing features,
including TikTok, Instagram, and Facebook integrations.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.services.social.cross_platform import (
    Platform,
    CrossPlatformPublisher,
    get_cross_platform_publisher
)

def test_platform_specifications():
    """Test that platform specifications are correctly defined."""
    print("\n=== Testing Platform Specifications ===")
    
    for platform in Platform:
        specs = CrossPlatformPublisher()._get_video_info("")
        print(f"{platform.name} specifications:")
        print(f"  - Duration: {specs['duration_seconds']} seconds")
        print(f"  - Aspect ratio: {specs['aspect_ratio']}")
        print(f"  - File size: {specs['file_size_mb']} MB")
        print(f"  - Format: {specs['format']}")
        print(f"  - Resolution: {specs['resolution']}")
    
    print("Platform specifications test completed.")

def test_metadata_formatting():
    """Test that metadata is correctly formatted for different platforms."""
    print("\n=== Testing Metadata Formatting ===")
    
    publisher = get_cross_platform_publisher()
    
    # Original metadata
    metadata = {
        "title": "Test Video",
        "description": "This is a test video description that is intentionally long enough to test the length limitations of different platforms. We want to ensure that the description is properly truncated and formatted according to each platform's specific requirements.",
        "hashtags": ["test", "video", "shorts", "youtube", "tiktok", "instagram", "facebook", "reels", "viral", "trending"]
    }
    
    for platform in Platform:
        print(f"\n{platform.name} metadata formatting:")
        formatted = publisher.format_metadata_for_platform(metadata, platform)
        
        for key, value in formatted.items():
            if isinstance(value, list):
                print(f"  - {key}: {len(value)} items")
                for item in value[:3]:
                    print(f"    - {item}")
                if len(value) > 3:
                    print(f"    - ... and {len(value) - 3} more")
            elif isinstance(value, str) and len(value) > 50:
                print(f"  - {key}: {value[:50]}... ({len(value)} chars)")
            else:
                print(f"  - {key}: {value}")
    
    print("Metadata formatting test completed.")

def test_multi_platform_publishing():
    """Test publishing a video to multiple platforms."""
    print("\n=== Testing Multi-Platform Publishing ===")
    
    publisher = get_cross_platform_publisher()
    
    # Mock video path (would be a real path in a real test)
    video_path = "test_video.mp4"
    
    # Video metadata
    metadata = {
        "title": "Multi-Platform Test",
        "description": "Testing publishing to multiple platforms at once",
        "hashtags": ["test", "multiplatform", "integration"]
    }
    
    # Publish to all platforms
    platforms = [Platform.TIKTOK, Platform.INSTAGRAM, Platform.FACEBOOK]
    
    print(f"Publishing to {len(platforms)} platforms: {', '.join([p.name for p in platforms])}")
    
    results = publisher.publish_video(video_path, metadata, platforms)
    
    for platform, result in results.items():
        print(f"\n{platform.name} publishing result:")
        
        if result.get('success'):
            print(f"  - Success: {result.get('success')}")
            print(f"  - Platform: {result.get('platform')}")
            
            if 'video_id' in result:
                print(f"  - Video ID: {result.get('video_id')}")
            elif 'media_id' in result:
                print(f"  - Media ID: {result.get('media_id')}")
            elif 'post_id' in result:
                print(f"  - Post ID: {result.get('post_id')}")
                
            if 'url' in result:
                print(f"  - URL: {result.get('url')}")
            elif 'permalink' in result:
                print(f"  - Permalink: {result.get('permalink')}")
                
            print(f"  - Timestamp: {result.get('timestamp')}")
        else:
            print(f"  - Error: {result.get('error')}")
    
    print("Multi-platform publishing test completed.")

def test_cross_platform_analytics():
    """Test retrieving and aggregating analytics across platforms."""
    print("\n=== Testing Cross-Platform Analytics ===")
    
    publisher = get_cross_platform_publisher()
    
    # Mock video IDs for each platform
    video_ids = {
        Platform.TIKTOK: "tt_12345",
        Platform.INSTAGRAM: "ig_67890",
        Platform.FACEBOOK: "fb_54321"
    }
    
    print(f"Getting analytics for {len(video_ids)} videos across platforms")
    
    # Get analytics for each platform individually
    for platform, video_id in video_ids.items():
        print(f"\n{platform.name} individual analytics:")
        
        analytics = publisher.get_platform_analytics(platform, video_id)
        
        if analytics.get('success'):
            metrics = analytics.get('metrics', {})
            print(f"  - Views: {metrics.get('views', 0)}")
            print(f"  - Likes: {metrics.get('likes', 0)}")
            print(f"  - Comments: {metrics.get('comments', 0)}")
            print(f"  - Shares: {metrics.get('shares', 0)}")
            print(f"  - Completion rate: {metrics.get('completion_rate', 0):.2f}")
        else:
            print(f"  - Error: {analytics.get('error')}")
    
    # Get consolidated analytics
    print("\nConsolidated cross-platform analytics:")
    
    consolidated = publisher.get_cross_platform_analytics(video_ids)
    
    if consolidated.get('success'):
        print(f"  - Total views: {consolidated.get('total_views', 0)}")
        print(f"  - Total engagement: {consolidated.get('total_engagement', 0)}")
        print(f"  - Overall engagement rate: {consolidated.get('overall_engagement_rate', 0):.2f}")
    else:
        print(f"  - Error: {consolidated.get('error')}")
    
    print("Cross-platform analytics test completed.")

def main():
    """Run all tests."""
    print("=== Cross-Platform Social Media Integration Tests ===")
    
    test_platform_specifications()
    test_metadata_formatting()
    test_multi_platform_publishing()
    test_cross_platform_analytics()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main() 