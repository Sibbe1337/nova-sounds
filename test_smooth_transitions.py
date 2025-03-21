"""
Test script for the smooth transitions feature in music_responsive module.
"""
import os
import sys
import tempfile

# Enable DEBUG_MODE and DEV_MODE before importing any modules
os.environ["DEBUG_MODE"] = "true"
os.environ["DEV_MODE"] = "true"

from src.app.services.video.music_responsive import (
    create_music_responsive_video,
    MusicFeature,
    EffectType
)
from src.app.core.settings import DEBUG_MODE, DEV_MODE

def main():
    """Test the smooth transitions feature in music_responsive module."""
    print(f"DEBUG_MODE is set to: {DEBUG_MODE}")
    print(f"DEV_MODE is set to: {DEV_MODE}")
    
    # Create output directory
    output_dir = "test-output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test image paths (using our color test images)
    test_images_dir = "test-images"
    test_images = []
    
    # Look specifically for our color test images
    for i in range(5):
        color_img_path = os.path.join(test_images_dir, f"test_color_{i}.jpg")
        if os.path.exists(color_img_path):
            test_images.append(color_img_path)
    
    if not test_images:
        print("No color test images found. Looking for any test images...")
        if os.path.exists(test_images_dir):
            for file in os.listdir(test_images_dir):
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    test_images.append(os.path.join(test_images_dir, file))
    
    if not test_images:
        print("No test images found. Using dummy test images.")
        test_images = [f"test-image-{i}.jpg" for i in range(3)]
    
    # Test audio path (using a dummy path in DEV_MODE)
    test_audio = "dummy-audio.mp3"
    
    # Create two output files, one with transitions and one without
    output_with_trans = os.path.join(output_dir, "with_transitions.mp4")
    output_without_trans = os.path.join(output_dir, "without_transitions.mp4")
    
    print(f"Using {len(test_images)} test images: {test_images}")
    print(f"Output WITH transitions: {output_with_trans}")
    print(f"Output WITHOUT transitions: {output_without_trans}")
    
    # Test parameters
    test_duration = 5  # seconds
    test_fps = 30
    
    try:
        # Create video with smooth transitions
        print("\nCreating video WITH smooth transitions...")
        result_with = create_music_responsive_video(
            images=test_images,
            music_path=test_audio,
            output_path=output_with_trans,
            fps=test_fps,
            duration=test_duration,
            effect_intensity=1.2,
            use_smooth_transitions=True
        )
        
        print(f"Video WITH transitions created at: {result_with}")
        if os.path.exists(result_with):
            print(f"File size: {os.path.getsize(result_with)} bytes")
        
        # Create video without smooth transitions
        print("\nCreating video WITHOUT smooth transitions...")
        result_without = create_music_responsive_video(
            images=test_images,
            music_path=test_audio,
            output_path=output_without_trans,
            fps=test_fps,
            duration=test_duration,
            effect_intensity=1.2,
            use_smooth_transitions=False
        )
        
        print(f"Video WITHOUT transitions created at: {result_without}")
        if os.path.exists(result_without):
            print(f"File size: {os.path.getsize(result_without)} bytes")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error creating videos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 