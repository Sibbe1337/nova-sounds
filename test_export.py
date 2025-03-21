"""
Test script for multi-platform video export.
"""
import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime

# API URL
API_URL = "http://127.0.0.1:8000"

def main():
    """
    Test multi-platform video export with the API.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test video export API")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for more verbose output")
    parser.add_argument("--api-url", default=API_URL, help=f"API URL (default: {API_URL})")
    parser.add_argument("--video-id", help="Specific video ID to export (if not provided, will create a new video)")
    parser.add_argument("--platforms", default="youtube,tiktok,instagram,facebook", 
                       help="Comma-separated list of platforms to export to (default: youtube,tiktok,instagram,facebook)")
    args = parser.parse_args()
    
    # Set debug mode and API URL
    debug_mode = args.debug
    api_url = args.api_url
    platforms = args.platforms.split(",")
    
    print(f"Testing video export... (Debug mode: {'ON' if debug_mode else 'OFF'})")
    print(f"Target platforms: {', '.join(platforms)}")
    
    # Get video ID
    video_id = args.video_id
    
    if not video_id:
        # Create a test video if no ID is provided
        video_id = create_test_video(api_url, debug_mode)
    
    # Wait for video to be ready
    wait_for_video_ready(api_url, video_id, debug_mode)
    
    # Export video to platforms
    export_video(api_url, video_id, platforms, debug_mode)
    
    print("\nTest completed!")

def create_test_video(api_url, debug_mode=False):
    """
    Create a test video.
    
    Args:
        api_url: API URL
        debug_mode: Whether to print debug information
        
    Returns:
        str: Video ID
    """
    print("\nCreating a test video...")
    
    # Get available music tracks
    response = requests.get(f"{api_url}/music")
    if response.status_code != 200:
        print(f"Error getting music tracks: {response.text}")
        sys.exit(1)
    
    tracks = response.json().get("tracks", [])
    if not tracks:
        print("No music tracks found")
        sys.exit(1)
    
    # Select a track
    selected_track = tracks[0]
    
    # Create test images
    test_dir = "test-images"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create simple test images with different colors
    image_paths = []
    try:
        import numpy as np
        from PIL import Image
        
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
        ]
        
        for i, color in enumerate(colors):
            # Create a solid color image
            img_array = np.zeros((400, 400, 3), dtype=np.uint8)
            img_array[:, :] = color
            
            # Convert to PIL Image
            img = Image.fromarray(img_array)
            
            # Save image
            image_path = os.path.join(test_dir, f"test_image_{i}.jpg")
            img.save(image_path)
            image_paths.append(image_path)
    except ImportError:
        # If PIL and numpy are not available, create empty files
        print("PIL or numpy not found, creating empty image files")
        for i in range(5):
            image_path = os.path.join(test_dir, f"test_image_{i}.jpg")
            # Create an empty file
            with open(image_path, "wb") as f:
                f.write(b"")
            image_paths.append(image_path)
    
    # Create a new video
    files = [
        ("images", (f"image_{i}.jpg", open(path, "rb"), "image/jpeg"))
        for i, path in enumerate(image_paths)
    ]
    
    data = {
        "music_track": selected_track
    }
    
    if debug_mode:
        print(f"POST {api_url}/videos")
        print(f"Data: {data}")
        print(f"Files: {len(files)} images")
    
    response = requests.post(f"{api_url}/videos", files=files, data=data)
    if response.status_code != 200:
        print(f"Error creating video: {response.text}")
        sys.exit(1)
    
    video_data = response.json()
    video_id = video_data.get("video_id")
    
    print(f"Created video with ID: {video_id}")
    
    return video_id

def wait_for_video_ready(api_url, video_id, debug_mode=False):
    """
    Wait for a video to be ready for export.
    
    Args:
        api_url: API URL
        video_id: Video ID
        debug_mode: Whether to print debug information
    """
    print(f"\nWaiting for video {video_id} to be ready...")
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        if debug_mode:
            print(f"GET {api_url}/videos/{video_id} (attempt {attempt}/{max_attempts})")
        
        response = requests.get(f"{api_url}/videos/{video_id}")
        if response.status_code != 200:
            print(f"Error checking status: {response.text}")
            break
        
        video = response.json().get("video", {})
        status = video.get("status")
        
        print(f"Status: {status}")
        
        if status == "ready_for_upload" or status == "uploaded":
            print(f"Video is ready for export.")
            if debug_mode:
                print(f"Video details: {json.dumps(video, indent=2, default=str)}")
            return
        
        if status == "failed":
            print(f"Video processing failed.")
            if debug_mode:
                print(f"Video details: {json.dumps(video, indent=2, default=str)}")
            sys.exit(1)
        
        # Wait a bit before checking again
        time.sleep(2)
    
    print(f"Timeout waiting for video to be ready after {max_attempts} attempts.")
    sys.exit(1)

def export_video(api_url, video_id, platforms, debug_mode=False):
    """
    Export a video to multiple platforms.
    
    Args:
        api_url: API URL
        video_id: Video ID
        platforms: List of platforms to export to
        debug_mode: Whether to print debug information
    """
    print(f"\nExporting video {video_id} to {', '.join(platforms)}...")
    
    # Set up platform-specific metadata
    metadata = {
        "youtube": {
            "title": "Test Export - YouTube Shorts",
            "description": "This is a test export to YouTube Shorts",
            "tags": ["test", "shorts", "youtube", "api"],
            "privacy_status": "unlisted"
        },
        "tiktok": {
            "caption": "Testing TikTok export #test #api"
        },
        "instagram": {
            "caption": "Testing Instagram Reels export #test #api"
        },
        "facebook": {
            "title": "Test Export - Facebook Reels",
            "description": "This is a test export to Facebook Reels"
        }
    }
    
    # Filter metadata to only include requested platforms
    platform_metadata = {p: metadata.get(p, {}) for p in platforms if p in metadata}
    
    # Prepare export request
    data = {
        "platforms": platforms,
        "metadata": platform_metadata
    }
    
    if debug_mode:
        print(f"POST {api_url}/videos/{video_id}/export")
        print(f"Data: {json.dumps(data, indent=2)}")
    
    # Export video
    response = requests.post(f"{api_url}/videos/{video_id}/export", json=data)
    
    if response.status_code != 200:
        print(f"Error exporting video: {response.text}")
        sys.exit(1)
    
    export_data = response.json()
    export_job = export_data.get("export_job", {})
    job_id = export_job.get("job_id")
    
    print(f"Started export job: {job_id}")
    
    if debug_mode:
        print(f"Export job details: {json.dumps(export_job, indent=2, default=str)}")
    
    # Monitor export status
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        if debug_mode:
            print(f"GET {api_url}/export/{job_id} (attempt {attempt}/{max_attempts})")
        
        response = requests.get(f"{api_url}/export/{job_id}")
        if response.status_code != 200:
            print(f"Error checking export status: {response.text}")
            break
        
        export_status = response.json()
        status = export_status.get("status")
        
        print(f"Export status: {status}")
        
        if status == "completed" or status == "failed":
            print(f"Export job {status}.")
            print(f"Platform results:")
            
            # Format platform results for display
            platforms_results = export_status.get("platforms", {})
            for platform, result in platforms_results.items():
                status = result.get("status")
                if status == "success":
                    print(f"  - {platform}: SUCCESS - URL: {result.get('url')}")
                else:
                    print(f"  - {platform}: FAILED - {result.get('error', 'Unknown error')}")
            
            if debug_mode:
                print(f"Full export details: {json.dumps(export_status, indent=2, default=str)}")
            
            return
        
        # Wait a bit before checking again
        time.sleep(2)
    
    print(f"Timeout waiting for export job to complete after {max_attempts} attempts.")

if __name__ == "__main__":
    main() 