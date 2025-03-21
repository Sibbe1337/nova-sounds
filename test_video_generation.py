"""
Test script for video generation.
"""
import os
import sys
import json
import uuid
import requests
import argparse
from datetime import datetime

# API URL
API_URL = "http://127.0.0.1:8000"

def main():
    """
    Test video generation with the API.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test video generation API")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for more verbose output")
    parser.add_argument("--api-url", default=API_URL, help=f"API URL (default: {API_URL})")
    parser.add_argument("--mode", choices=["basic", "enhanced", "music-responsive"], default="basic",
                      help="Video generation mode to test")
    parser.add_argument("--intensity", type=float, default=1.0, 
                      help="Effect intensity for music-responsive mode (0.0-2.0)")
    parser.add_argument("--use-mock", action="store_true", default=True,
                      help="Use mock music files instead of API tracks")
    args = parser.parse_args()
    
    # Set debug mode and API URL
    debug_mode = args.debug
    api_url = args.api_url
    mode = args.mode
    use_mock = args.use_mock
    
    print(f"Testing video generation in {mode} mode... (Debug mode: {'ON' if debug_mode else 'OFF'}, Use mock: {'ON' if use_mock else 'OFF'})")
    
    # Get track to use
    if use_mock:
        # Use mock track
        selected_track = "track1.mp3"
        print(f"\nUsing mock track: {selected_track}")
    else:
        # Get available music tracks from API
        print("\nGetting music tracks...")
        response = requests.get(f"{api_url}/music")
        if response.status_code != 200:
            print(f"Error getting music tracks: {response.text}")
            sys.exit(1)
        
        tracks = response.json().get("tracks", [])
        if not tracks:
            print("No music tracks found")
            sys.exit(1)
        
        print(f"Available tracks: {tracks}")
        
        # Select a track
        selected_track = tracks[0]
        print(f"\nUsing track: {selected_track}")
    
    # Create test images
    print("\nCreating test images...")
    image_paths = create_test_images(debug_mode)
    
    if mode == "basic":
        test_basic_video(api_url, selected_track, image_paths, debug_mode)
    elif mode == "enhanced":
        test_enhanced_video(api_url, selected_track, image_paths, debug_mode)
    elif mode == "music-responsive":
        test_music_responsive_video(api_url, selected_track, image_paths, debug_mode, args.intensity)

def test_basic_video(api_url, music_track, image_paths, debug_mode):
    """Test basic video generation."""
    print("\nCreating basic video...")
    files = [
        ("images", (f"image_{i}.jpg", open(path, "rb"), "image/jpeg"))
        for i, path in enumerate(image_paths)
    ]
    
    data = {
        "music_track": music_track
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
    
    if debug_mode:
        print(f"Full response: {json.dumps(video_data, indent=2, default=str)}")
    
    check_video_status(api_url, video_id, debug_mode)

def test_enhanced_video(api_url, music_track, image_paths, debug_mode):
    """Test enhanced video generation."""
    print("\nCreating enhanced video...")
    files = [
        ("images", (f"image_{i}.jpg", open(path, "rb"), "image/jpeg"))
        for i, path in enumerate(image_paths)
    ]
    
    data = {
        "music_track": music_track,
        "style": "music_video",
        "description": "Creative video with dynamic transitions",
        "use_runway": "false"
    }
    
    if debug_mode:
        print(f"POST {api_url}/videos/enhanced")
        print(f"Data: {data}")
        print(f"Files: {len(files)} images")
    
    response = requests.post(f"{api_url}/videos/enhanced", files=files, data=data)
    if response.status_code != 200:
        print(f"Error creating enhanced video: {response.text}")
        sys.exit(1)
    
    video_data = response.json()
    video_id = video_data.get("video_id")
    
    print(f"Created enhanced video with ID: {video_id}")
    
    if debug_mode:
        print(f"Full response: {json.dumps(video_data, indent=2, default=str)}")
    
    check_video_status(api_url, video_id, debug_mode)

def test_music_responsive_video(api_url, music_track, image_paths, debug_mode, intensity=1.0):
    """Test music-responsive video generation."""
    print("\nCreating music-responsive video...")
    files = [
        ("images", (f"image_{i}.jpg", open(path, "rb"), "image/jpeg"))
        for i, path in enumerate(image_paths)
    ]
    
    data = {
        "music_track": music_track,
        "effect_intensity": str(intensity),
        "duration": "60"
    }
    
    if debug_mode:
        print(f"POST {api_url}/videos/music-responsive")
        print(f"Data: {data}")
        print(f"Files: {len(files)} images")
    
    response = requests.post(f"{api_url}/videos/music-responsive", files=files, data=data)
    if response.status_code != 200:
        print(f"Error creating music-responsive video: {response.text}")
        sys.exit(1)
    
    video_data = response.json()
    video_id = video_data.get("video_id")
    
    print(f"Created music-responsive video with ID: {video_id}")
    print(f"Effect intensity: {intensity}")
    
    if debug_mode:
        print(f"Full response: {json.dumps(video_data, indent=2, default=str)}")
    
    check_video_status(api_url, video_id, debug_mode)

def check_video_status(api_url, video_id, debug_mode):
    """Check video processing status."""
    print("\nChecking status...")
    
    while True:
        if debug_mode:
            print(f"GET {api_url}/videos/{video_id}")
        
        response = requests.get(f"{api_url}/videos/{video_id}")
        if response.status_code != 200:
            print(f"Error checking status: {response.text}")
            break
        
        video = response.json().get("video", {})
        status = video.get("status")
        
        print(f"Status: {status}")
        
        if status == "ready_for_upload" or status == "uploaded" or status == "failed":
            print("\nVideo details:")
            print(json.dumps(video, indent=2, default=str))
            break
        
        # Wait a bit before checking again
        import time
        time.sleep(2)
    
    print("\nTest completed!")

def create_test_images(debug_mode=False):
    """
    Create test images for video generation.
    
    Args:
        debug_mode: Whether to print debug information
        
    Returns:
        list: List of image paths
    """
    # Create test directory
    test_dir = "test-images"
    os.makedirs(test_dir, exist_ok=True)
    
    if debug_mode:
        print(f"Created test directory: {test_dir}")
    
    # Create simple test images with different colors
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
    ]
    
    image_paths = []
    
    try:
        import numpy as np
        from PIL import Image
        
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
            
            if debug_mode:
                print(f"Created test image: {image_path} (color: {color})")
    except ImportError:
        # If PIL and numpy are not available, create empty files
        print("PIL or numpy not found, creating empty image files")
        for i in range(5):
            image_path = os.path.join(test_dir, f"test_image_{i}.jpg")
            # Create an empty file
            with open(image_path, "wb") as f:
                f.write(b"")
            image_paths.append(image_path)
            
            if debug_mode:
                print(f"Created empty test image: {image_path}")
    
    return image_paths

if __name__ == "__main__":
    main() 