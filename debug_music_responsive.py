"""
Debug test script for the music_responsive module with DEBUG_MODE enabled.
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
    """Test the music_responsive module with DEBUG_MODE enabled."""
    print(f"DEBUG_MODE is set to: {DEBUG_MODE}")
    print(f"DEV_MODE is set to: {DEV_MODE}")
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
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
            print("No test images found in test-images directory.")
            # Use test-image.jpg in the root directory if available
            if os.path.exists("test-image.jpg"):
                test_images = ["test-image.jpg"] * 3
            else:
                print("No test images found. Creating dummy test images.")
                test_images = [f"test-image-{i}.jpg" for i in range(3)]
        
        # Test audio path (using a dummy path in DEV_MODE)
        test_audio = "dummy-audio.mp3"
        
        # Output path
        output_path = os.path.join(temp_dir, "test_output.mp4")
        
        print(f"Using {len(test_images)} test images: {test_images}")
        print(f"Test audio: {test_audio}")
        print(f"Output path: {output_path}")
        
        try:
            # Call the function
            print("Creating music-responsive video...")
            result = create_music_responsive_video(
                images=test_images,
                music_path=test_audio,
                output_path=output_path,
                fps=30,
                duration=5,  # Short duration for testing
                effect_intensity=1.2
            )
            
            print(f"Video created at: {result}")
            print(f"File exists: {os.path.exists(result)}")
            if os.path.exists(result):
                file_size = os.path.getsize(result)
                print(f"File size: {file_size} bytes")
                
                # If it's a text file in DEV_MODE, print its contents
                if DEV_MODE and file_size < 1000:
                    with open(result, 'r') as f:
                        print(f"File contents: {f.read()}")
            
        except Exception as e:
            print(f"Error creating video: {e}")
            import traceback
            traceback.print_exc()
    
    print("Test completed.")

if __name__ == "__main__":
    main() 