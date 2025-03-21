#!/usr/bin/env python
"""
Local test script for music-responsive video generator.
"""
import os
import sys
import tempfile
import argparse
from pathlib import Path

# Set DEV_MODE and DEBUG_MODE for testing
os.environ['DEV_MODE'] = 'true'
os.environ['DEBUG_MODE'] = 'true'

def main():
    """
    Test the music-responsive video generator locally.
    """
    # Import here to ensure environment variables are set first
    from src.app.services.video.music_responsive import create_music_responsive_video, MusicFeature
    from src.app.services.video.music_responsive import PulseEffect, ColorShiftEffect, ShakeEffect
    from src.app.services.video.music_responsive import FlashEffect, WarpEffect, VignetteEffect, GlitchEffect
    from src.app.services.video.music_responsive import MusicAnalyzer
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test music-responsive video generator locally")
    parser.add_argument("--debug", action="store_true", help="Enable extra verbose output")
    parser.add_argument("--intensity", type=float, default=1.5, help="Effect intensity (0.0-2.0)")
    parser.add_argument("--duration", type=int, default=10, help="Video duration in seconds")
    parser.add_argument("--test-case", type=str, 
                      choices=["standard", "pulse", "color", "shake", "flash", "warp", "vignette", 
                              "glitch", "advanced", "analyze"], 
                      default="standard", help="Test case to run")
    args = parser.parse_args()
    
    print(f"Testing music-responsive generator (intensity={args.intensity}, duration={args.duration}s, test-case={args.test_case})")
    
    # Create test directory
    test_dir = "test-output"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test images
    print("\nCreating test images...")
    image_paths = create_test_images(args.debug)
    
    # Get mock music file
    mock_music = "mock-media/track1.mp3"
    if not os.path.exists(mock_music):
        print(f"Creating mock music file at {mock_music}")
        os.makedirs(os.path.dirname(mock_music), exist_ok=True)
        with open(mock_music, 'w') as f:
            f.write("Mock music content for testing")
    
    # Run the selected test case
    if args.test_case == "analyze":
        # Test just the music analyzer
        run_music_analyzer_test(mock_music, args)
    elif args.test_case == "advanced":
        # Test the enhanced version with all advanced effects
        run_advanced_test(image_paths, mock_music, test_dir, args)
    else:
        # Test video generation with different effects
        run_video_generation_test(args.test_case, image_paths, mock_music, test_dir, args)

def run_music_analyzer_test(music_path, args):
    """
    Run a test of just the music analyzer.
    """
    from src.app.services.video.music_responsive import MusicAnalyzer, MusicFeature
    
    print(f"\nAnalyzing music file: {music_path}")
    analyzer = MusicAnalyzer(music_path)
    
    # Print basic info
    print(f"\nMusic Analysis Results:")
    print(f"Tempo: {analyzer.tempo:.1f} BPM")
    print(f"Beat times: {len(analyzer.beat_times)} beats detected")
    print(f"Onset times: {len(analyzer.onsets)} onsets detected")
    
    # Sample some feature values at different times
    print("\nFeature values at different times:")
    features = [MusicFeature.BEATS, MusicFeature.ONSETS, MusicFeature.RMS_ENERGY, 
               MusicFeature.SPECTRAL_CENTROID, MusicFeature.HARMONIC_PERCUSSIVE]
    
    for time_sec in [1.0, 2.5, 5.0, 7.5]:
        print(f"\nTime: {time_sec}s")
        for feature in features:
            value = analyzer.get_feature_at_time(feature, time_sec)
            print(f"  {feature.name}: {value:.3f}")
        
        # Also get segment intensity
        intensity = analyzer.get_segment_intensity(time_sec, time_sec + 1.0)
        print(f"  Segment intensity: {intensity:.3f}")

def run_video_generation_test(test_case, image_paths, music_path, test_dir, args):
    """
    Run a video generation test with different effect configurations.
    """
    from src.app.services.video.music_responsive import create_music_responsive_video, MusicFeature, PulseEffect, ColorShiftEffect, ShakeEffect, MusicAnalyzer
    
    # Generate the video with different configurations based on test case
    output_path = os.path.join(test_dir, f"music_responsive_{test_case}.mp4")
    print(f"\nGenerating music-responsive video at {output_path}")
    
    try:
        if test_case == "standard":
            # Use the standard function with all effects
            result_path = create_music_responsive_video(
                images=image_paths,
                music_path=music_path,
                output_path=output_path,
                fps=30,
                duration=args.duration,
                effect_intensity=args.intensity
            )
        else:
            # Custom test just using specific effects
            result_path = create_custom_effect_video(
                test_case=test_case,
                images=image_paths,
                music_path=music_path,
                output_path=output_path,
                fps=30,
                duration=args.duration,
                intensity=args.intensity
            )
        
        print(f"\nSuccess! Video created at: {result_path}")
        print(f"File size: {os.path.getsize(result_path)} bytes")
        
        # On macOS, try to open the video
        if sys.platform == 'darwin':
            print("\nAttempting to open the video...")
            os.system(f"open {result_path}")
        
    except Exception as e:
        print(f"\nError creating video: {e}")
        import traceback
        traceback.print_exc()

def run_advanced_test(image_paths, music_path, test_dir, args):
    """
    Run a test with all advanced effects enabled.
    """
    from src.app.services.video.music_responsive import create_music_responsive_video
    
    # Use high intensity to enable all effects
    intensity = max(1.8, args.intensity)
    
    output_path = os.path.join(test_dir, f"music_responsive_advanced.mp4")
    print(f"\nGenerating advanced music-responsive video at {output_path}")
    print(f"Using high intensity ({intensity}) to enable all effects")
    
    try:
        result_path = create_music_responsive_video(
            images=image_paths,
            music_path=music_path,
            output_path=output_path,
            fps=30,
            duration=args.duration,
            effect_intensity=intensity
        )
        
        print(f"\nSuccess! Advanced video created at: {result_path}")
        print(f"File size: {os.path.getsize(result_path)} bytes")
        
        # On macOS, try to open the video
        if sys.platform == 'darwin':
            print("\nAttempting to open the video...")
            os.system(f"open {result_path}")
        
    except Exception as e:
        print(f"\nError creating advanced video: {e}")
        import traceback
        traceback.print_exc()

def create_custom_effect_video(test_case, images, music_path, output_path, fps=30, duration=10, intensity=1.0):
    """
    Create a custom video with specific effects for testing.
    """
    from src.app.services.video.music_responsive import MusicAnalyzer, MusicFeature
    from src.app.services.video.music_responsive import (PulseEffect, ColorShiftEffect, ShakeEffect, 
                                                       FlashEffect, WarpEffect, VignetteEffect, GlitchEffect)
    import cv2
    import numpy as np
    
    print(f"Creating custom video with {test_case} effect...")
    
    # Create music analyzer
    analyzer = MusicAnalyzer(music_path)
    
    # Determine video parameters
    width, height = (1080, 1920)  # Portrait mode for shorts
    total_frames = fps * duration
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Create the specific effect based on test case
    effects = []
    if test_case == "pulse":
        effects = [PulseEffect(analyzer, MusicFeature.BEATS, intensity * 2.0)]
    elif test_case == "color":
        effects = [ColorShiftEffect(analyzer, MusicFeature.SPECTRAL_CENTROID, intensity)]
    elif test_case == "shake":
        effects = [ShakeEffect(analyzer, MusicFeature.ONSETS, intensity * 1.5)]
    elif test_case == "flash":
        effects = [FlashEffect(analyzer, MusicFeature.BEATS, intensity, 
                             threshold=0.7, flash_color=(255, 255, 255))]
    elif test_case == "warp":
        effects = [WarpEffect(analyzer, MusicFeature.RMS_ENERGY, intensity * 1.2)]
    elif test_case == "vignette":
        effects = [VignetteEffect(analyzer, MusicFeature.BEATS, intensity)]
    elif test_case == "glitch":
        effects = [GlitchEffect(analyzer, MusicFeature.HARMONIC_PERCUSSIVE, intensity * 1.3)]
    
    # Load and resize images
    image_frames = []
    for img_path in images:
        img = cv2.imread(img_path)
        if img is not None:
            # Resize to match video resolution
            img_resized = cv2.resize(img, (width, height))
            image_frames.append(img_resized)
        else:
            print(f"Could not load image: {img_path}")
    
    if not image_frames:
        raise ValueError("No valid images loaded")
    
    # Duplicate images if not enough
    while len(image_frames) < 5:
        image_frames.extend(image_frames)
    
    # Calculate frame timing based on beats
    beat_times = analyzer.beat_times
    beat_times = beat_times[beat_times < duration]
    
    if len(beat_times) < 2:
        print("Not enough beats detected, using regular intervals")
        beat_times = np.linspace(0, duration, len(images) + 1)
    
    # Process each frame
    for frame_idx in range(total_frames):
        time_sec = frame_idx / fps
        
        # Find which image to use based on current time and beat timing
        beat_idx = np.searchsorted(beat_times, time_sec) - 1
        beat_idx = max(0, min(beat_idx, len(image_frames) - 1))
        img_idx = beat_idx % len(image_frames)
        
        # Get base frame
        frame = image_frames[img_idx].copy()
        
        # Apply the chosen effect
        for effect in effects:
            frame = effect.apply(frame, time_sec)
        
        # Add a label indicating the test case and current time
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"{test_case.upper()} ({time_sec:.1f}s)"
        cv2.putText(frame, text, (50, 50), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Add effect values as text
        if effects:
            effect_val = effects[0].get_feature_value(time_sec)
            cv2.putText(frame, f"Value: {effect_val:.3f}", (50, 100), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Write the frame
        video_writer.write(frame)
        
        # Log progress at intervals
        if frame_idx % 100 == 0 or frame_idx == total_frames - 1:
            print(f"Processed frame {frame_idx+1}/{total_frames} ({(frame_idx+1)/total_frames*100:.1f}%)")
    
    video_writer.release()
    print(f"Created custom {test_case} video at {output_path}")
    
    return output_path

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