"""
Test script for the analytics feature in music_responsive module.

This script tests the tracking and reporting of video generation metrics.
"""
import os
import sys
import requests
import json
import time

# Enable DEBUG_MODE and DEV_MODE before importing any modules
os.environ["DEBUG_MODE"] = "true"
os.environ["DEV_MODE"] = "true"

from src.app.services.video.music_responsive import (
    create_music_responsive_video
)
from src.app.services.video.music_responsive.presets import (
    StylePreset, get_preset_manager
)
from src.app.services.video.music_responsive.analytics import (
    get_analytics_manager
)
from src.app.core.settings import DEBUG_MODE, DEV_MODE

def test_analytics_recording():
    """Test recording of analytics during video generation."""
    print("\n== Testing Analytics Recording ==")
    
    # Create output directory
    output_dir = "test-output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get test images
    test_images_dir = "test-images"
    test_images = []
    
    # Look specifically for our color test images
    for i in range(5):
        color_img_path = os.path.join(test_images_dir, f"test_color_{i}.jpg")
        if os.path.exists(color_img_path):
            test_images.append(color_img_path)
    
    if not test_images:
        # Use any images in the test-images directory
        if os.path.exists(test_images_dir):
            for img_file in os.listdir(test_images_dir):
                if img_file.endswith('.jpg') or img_file.endswith('.png'):
                    test_images.append(os.path.join(test_images_dir, img_file))
    
    if not test_images:
        print("No test images found. Creating some dummy images...")
        # Create dummy test images
        import numpy as np
        import cv2
        os.makedirs(test_images_dir, exist_ok=True)
        
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (0, 255, 255),  # Cyan
        ]
        
        for i, color in enumerate(colors):
            img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            img[:] = color
            
            # Add a text label
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, f'Test Image {i+1}', (50, 100), font, 4, (255, 255, 255), 10)
            
            img_path = os.path.join(test_images_dir, f"test_color_{i}.jpg")
            cv2.imwrite(img_path, img)
            test_images.append(img_path)
        
        print(f"Created {len(test_images)} test images in {test_images_dir}")
    
    # Dummy audio path (not actually used in DEV_MODE)
    test_audio = "dummy-audio.mp3"
    
    # Get analytics manager
    analytics_manager = get_analytics_manager()
    
    # Get initial analytics count
    initial_stats = analytics_manager.get_aggregate_stats()
    initial_count = initial_stats.get('total_sessions', 0)
    
    print(f"Initial analytics count: {initial_count} sessions")
    
    # Generate videos with different presets to create analytics data
    preset_results = {}
    presets_to_test = [
        StylePreset.STANDARD,
        StylePreset.ENERGETIC,
        StylePreset.SUBTLE
    ]
    
    for preset in presets_to_test:
        preset_name = preset.value
        output_path = os.path.join(output_dir, f"analytics_test_{preset_name}.mp4")
        
        print(f"\nGenerating video with preset: {preset_name}")
        try:
            result = create_music_responsive_video(
                images=test_images,
                music_path=test_audio,
                output_path=output_path,
                fps=30,
                duration=3,  # Short duration for testing
                preset=preset
            )
            
            # Check if file was created
            file_exists = os.path.exists(result)
            file_size = os.path.getsize(result) if file_exists else 0
            
            preset_results[preset_name] = {
                "path": result,
                "exists": file_exists,
                "size": file_size
            }
            
            print(f"Video generated: {result}, Size: {file_size} bytes")
            
            # Allow time for analytics to be saved
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error generating video with preset {preset_name}: {e}")
            preset_results[preset_name] = {"error": str(e)}
    
    # Get updated analytics count
    updated_stats = analytics_manager.get_aggregate_stats()
    updated_count = updated_stats.get('total_sessions', 0)
    
    print(f"\nAnalytics after test: {updated_count} sessions (added {updated_count - initial_count})")
    
    if updated_count > initial_count:
        print("\nAnalytics were successfully recorded")
        print(f"Success rate: {updated_stats.get('success_rate', 0):.2%}")
        print(f"Average processing time: {updated_stats.get('avg_processing_time', 0):.3f} seconds")
        
        print("\nPreset usage:")
        for preset, count in updated_stats.get('preset_usage', {}).items():
            print(f"  - {preset}: {count} videos")
        
        print("\nEffect usage:")
        for effect, count in updated_stats.get('effect_usage', {}).items():
            print(f"  - {effect}: {count} times")
    else:
        print("\nNo new analytics were recorded")
    
    return preset_results

def test_analytics_api():
    """Test the analytics API endpoints."""
    print("\n== Testing Analytics API ==")
    
    # Check if API is running
    api_url = "http://localhost:8000/api/music-responsive/analytics"
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            print(f"API endpoint not available. Status code: {response.status_code}")
            print("Make sure the API server is running before testing API endpoints.")
            return
        
        # Display analytics data
        analytics_data = response.json()
        print(f"Retrieved analytics data for {analytics_data.get('total_sessions', 0)} sessions")
        
        if analytics_data.get('total_sessions', 0) > 0:
            print(f"Success rate: {analytics_data.get('success_rate', 0):.2%}")
            print(f"Average processing time: {analytics_data.get('avg_processing_time', 0):.3f} seconds")
            
            # Get analytics for a specific preset
            preset_to_check = "standard"
            preset_url = f"http://localhost:8000/api/music-responsive/analytics/preset/{preset_to_check}"
            preset_response = requests.get(preset_url)
            
            if preset_response.status_code == 200:
                preset_data = preset_response.json()
                print(f"\nPreset '{preset_to_check}' analytics:")
                print(f"  - Total sessions: {preset_data.get('total_sessions', 0)}")
                print(f"  - Success rate: {preset_data.get('success_rate', 0):.2%}")
                print(f"  - Average effect intensity: {preset_data.get('avg_effect_intensity', 0):.2f}")
                
                # Show effects used with this preset
                if 'effect_usage' in preset_data:
                    print(f"  - Effects used:")
                    for effect, count in preset_data['effect_usage'].items():
                        print(f"    * {effect}: {count} times")
            else:
                print(f"Couldn't get preset analytics. Status code: {preset_response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("Couldn't connect to API server. Make sure it's running first.")
    except Exception as e:
        print(f"Error testing API: {e}")

def main():
    """Main test function."""
    print(f"DEBUG_MODE is set to: {DEBUG_MODE}")
    print(f"DEV_MODE is set to: {DEV_MODE}")
    
    # Test analytics recording
    preset_results = test_analytics_recording()
    
    # Test analytics API (only if API server is running)
    test_analytics_api()
    
    print("\n== Test Summary ==")
    print(f"Generated {len(preset_results)} videos for analytics testing")
    print("Check the analytics file in src/app/services/video/music_responsive/analytics/generation_metrics.json")
    print("\nTests completed.")

if __name__ == "__main__":
    main() 