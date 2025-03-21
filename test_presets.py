"""
Test script for the style presets feature in music_responsive module.
"""
import os
import sys
import tempfile

# Enable DEBUG_MODE and DEV_MODE before importing any modules
os.environ["DEBUG_MODE"] = "true"
os.environ["DEV_MODE"] = "true"

from src.app.services.video.music_responsive import (
    create_music_responsive_video
)
from src.app.services.video.music_responsive.presets import (
    StylePreset, get_preset_manager, PresetManager
)
from src.app.core.settings import DEBUG_MODE, DEV_MODE

def test_list_presets():
    """Test listing all available presets."""
    print("\n== Testing List Presets ==")
    preset_manager = get_preset_manager()
    all_presets = preset_manager.list_all_presets()
    
    print(f"Available built-in presets:")
    for preset in all_presets['built_in']:
        print(f"  - {preset['id']}: {preset['name']} - {preset['description']}")
    
    print(f"\nAvailable custom presets:")
    for preset in all_presets['custom']:
        print(f"  - {preset['id']}: {preset['name']} - {preset['description']}")
    
    return all_presets

def test_custom_preset():
    """Test creating, saving, and retrieving a custom preset."""
    print("\n== Testing Custom Presets ==")
    preset_manager = get_preset_manager()
    
    # Create a custom preset based on the ENERGETIC preset
    base_preset = preset_manager.get_preset_config(StylePreset.ENERGETIC)
    
    # Modify it
    custom_preset = {
        "name": "Test Custom Preset",
        "description": "Custom preset for testing",
        "base_preset": "ENERGETIC",
        "effect_intensity": 1.3,
        "anticipation_time": 0.2,
        "use_smooth_transitions": True,
        "effects": {
            "AnticipationEffect": 1.0,
            "PulseEffect": 1.5,
            "ColorShiftEffect": 1.0,
            "ShakeEffect": 0.5,
            "GlitchEffect": 0.8
        },
        "music_features": base_preset["music_features"]
    }
    
    # Save the custom preset
    preset_id = "test_preset_1"
    result = preset_manager.save_custom_preset(preset_id, custom_preset)
    print(f"Custom preset saved: {result}")
    
    # Retrieve the custom preset
    retrieved_preset = preset_manager.get_custom_preset(preset_id)
    print(f"Retrieved custom preset: {retrieved_preset['name']}")
    
    return preset_id, retrieved_preset

def test_generate_videos_with_presets():
    """Test generating videos with different presets."""
    print("\n== Testing Video Generation with Presets ==")
    
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
        print("No test images found. Please run test-images/create_color_images.py first.")
        return {}
    
    # Dummy audio path
    test_audio = "dummy-audio.mp3"
    
    # Generate videos for each built-in preset
    preset_results = {}
    presets_to_test = [
        StylePreset.STANDARD,
        StylePreset.ENERGETIC,
        StylePreset.SUBTLE,
        StylePreset.RETRO,
        StylePreset.GLITCH
    ]
    
    for preset in presets_to_test:
        preset_name = preset.value
        output_path = os.path.join(output_dir, f"preset_{preset_name}.mp4")
        
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
            
        except Exception as e:
            print(f"Error generating video with preset {preset_name}: {e}")
            preset_results[preset_name] = {"error": str(e)}
    
    # Also test with a custom preset
    try:
        preset_manager = get_preset_manager()
        custom_presets = preset_manager.list_all_presets()["custom"]
        
        if custom_presets:
            custom_preset_id = custom_presets[0]["id"]
            output_path = os.path.join(output_dir, f"preset_custom_{custom_preset_id}.mp4")
            
            print(f"\nGenerating video with custom preset: {custom_preset_id}")
            
            result = create_music_responsive_video(
                images=test_images,
                music_path=test_audio,
                output_path=output_path,
                fps=30,
                duration=3,
                preset=StylePreset.CUSTOM,
                custom_preset_id=custom_preset_id
            )
            
            file_exists = os.path.exists(result)
            file_size = os.path.getsize(result) if file_exists else 0
            
            preset_results["custom"] = {
                "id": custom_preset_id,
                "path": result,
                "exists": file_exists,
                "size": file_size
            }
            
            print(f"Video with custom preset generated: {result}, Size: {file_size} bytes")
    
    except Exception as e:
        print(f"Error generating video with custom preset: {e}")
        preset_results["custom"] = {"error": str(e)}
    
    return preset_results

def main():
    """Main test function."""
    print(f"DEBUG_MODE is set to: {DEBUG_MODE}")
    print(f"DEV_MODE is set to: {DEV_MODE}")
    
    # Test preset listing
    all_presets = test_list_presets()
    
    # Test custom presets
    custom_preset_id, custom_preset = test_custom_preset()
    
    # Test generating videos with different presets
    preset_results = test_generate_videos_with_presets()
    
    print("\n== Test Summary ==")
    print(f"Found {len(all_presets['built_in'])} built-in presets")
    print(f"Found {len(all_presets['custom'])} custom presets")
    print(f"Created custom preset: {custom_preset_id}")
    
    print(f"\nGenerated {len(preset_results)} preset videos:")
    for preset_name, result in preset_results.items():
        if "error" in result:
            print(f"  - {preset_name}: ERROR - {result['error']}")
        else:
            print(f"  - {preset_name}: {result['path']} ({result['size']} bytes)")
    
    print("\nTests completed.")

if __name__ == "__main__":
    main() 