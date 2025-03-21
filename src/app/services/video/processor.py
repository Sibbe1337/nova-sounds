"""
Video processing service for YouTube Shorts.

This module provides functions for creating and processing short-form videos
with features like beat detection, transitions, and captions.
"""

import os
import tempfile
import subprocess
import logging
import json
import time
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple, Union
import requests

from src.app.core.settings import DEV_MODE, DEBUG_MODE
from src.app.services.video.enhanced_processor import (
    EnhancedVideoProcessor,
    VideoProcessingOptions,
    create_enhanced_video
)
from src.app.services.video.caption import (
    add_captions_to_video,
    create_styled_captions,
    CaptionStyle
)

# Set up logging
logger = logging.getLogger(__name__)

def create_video_from_images(
    images: List[str], 
    output_path: str, 
    duration: int = 60, 
    fps: int = 30,
    resolution: Tuple[int, int] = (1080, 1920)
) -> str:
    """
    Create a basic video from a list of images.
    
    Args:
        images: List of image paths
        output_path: Path to save the video
        duration: Duration in seconds
        fps: Frames per second
        resolution: Video resolution as (width, height)
        
    Returns:
        str: Path to the created video file
    """
    logger.info(f"Creating video from {len(images)} images")
    
    if not images:
        raise ValueError("No images provided")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # For dev mode without debugging, create a mock file to avoid processing
    if DEV_MODE and not DEBUG_MODE:
        logger.info("DEV mode: Creating mock video file")
        with open(output_path, 'w') as f:
            f.write(f"Mock video file with {len(images)} images")
        return output_path
    
    # Set up parameters
    width, height = resolution
    total_frames = duration * fps
    frames_per_image = total_frames // len(images)
    remaining_frames = total_frames % len(images)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not video_writer.isOpened():
        raise RuntimeError(f"Failed to open video writer with output: {output_path}")
    
    # Load, resize, and write each image
    for i, image_path in enumerate(images):
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                logger.warning(f"Failed to load image: {image_path}")
                continue
            
            # Resize image to match video resolution
            img_resized = cv2.resize(img, (width, height))
            
            # Calculate how many frames to show this image
            frames_for_this_image = frames_per_image
            if i < remaining_frames:
                frames_for_this_image += 1
            
            # Write frames to video
            for _ in range(frames_for_this_image):
                video_writer.write(img_resized)
                
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
    
    # Release the video writer
    video_writer.release()
    logger.info(f"Created video at {output_path}")
    
    return output_path

def add_music_to_video(
    video_path: str, 
    music_path: str, 
    output_path: Optional[str] = None
) -> str:
    """
    Add music to a video file.
    
    Args:
        video_path: Path to the video file
        music_path: Path to the music file
        output_path: Optional path to save the output video
        
    Returns:
        str: Path to the output video file
    """
    logger.info(f"Adding music from {music_path} to video {video_path}")
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not os.path.exists(music_path):
        raise FileNotFoundError(f"Music file not found: {music_path}")
    
    # If no output path is provided, create one based on input path
    if output_path is None:
        output_dir = os.path.dirname(video_path)
        output_name = f"{os.path.splitext(os.path.basename(video_path))[0]}_with_music.mp4"
        output_path = os.path.join(output_dir, output_name)
    
    # For dev mode without debugging, create a mock file
    if DEV_MODE and not DEBUG_MODE:
        logger.info("DEV mode: Creating mock video with music")
        with open(output_path, 'w') as f:
            f.write(f"Mock video with music: {os.path.basename(video_path)} + {os.path.basename(music_path)}")
        return output_path
    
    # Use FFmpeg to add music to the video
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', music_path,
        '-map', '0:v',
        '-map', '1:a',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',  # End when the shortest input ends
        output_path
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        logger.info(f"Added music to video: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error adding music to video: {e.stderr}")
        raise

def download_music(url: str, output_path: Optional[str] = None) -> str:
    """
    Download music from a URL.
    
    Args:
        url: URL of the music file
        output_path: Optional path to save the downloaded file
        
    Returns:
        str: Path to the downloaded music file
    """
    logger.info(f"Downloading music from {url}")
    
    # If no output path is provided, create a temporary file
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"music_{int(time.time())}.mp3")
    
    # For dev mode, create a mock file
    if DEV_MODE:
        logger.info("DEV mode: Creating mock music file")
        with open(output_path, 'w') as f:
            f.write(f"Mock music file from {url}")
        return output_path
    
    # Download the file
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded music to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error downloading music: {e}")
        raise

def detect_beats(audio_path: str) -> Dict[str, Any]:
    """
    Detect beats in an audio file using enhanced beat detection.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Dict with beat information (beat_times, tempo, etc.)
    """
    logger.info(f"Detecting beats in {audio_path}")
    
    # For dev mode, return mock data
    if DEV_MODE and not DEBUG_MODE:
        logger.info("DEV mode: Returning mock beat detection data")
        return {
            "tempo": 120.0,
            "beat_times": list(np.linspace(0, 60, 20)),
            "beat_strengths": [0.8] * 20,
            "key_moments": [10.0, 20.0, 30.0, 40.0, 50.0]
        }
    
    # Use our enhanced music analyzer via the create_enhanced_video function
    try:
        # Create a temporary directory to hold intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a dummy image for analysis
            dummy_image_path = os.path.join(temp_dir, "dummy.jpg")
            dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
            cv2.imwrite(dummy_image_path, dummy_image)
            
            # Create temporary output path
            temp_output = os.path.join(temp_dir, "temp_beat_analysis.json")
            
            # Create an enhanced video processor with analysis-only mode
            processor = EnhancedVideoProcessor(
                VideoProcessingOptions(
                    enable_music_sync=True,
                    enable_captions=False
                )
            )
            
            # Use our music analyzer to extract beat information
            from src.app.services.video.music_responsive.analyzer import MusicAnalyzer
            analyzer = MusicAnalyzer(audio_path)
            
            # Extract beat information
            beat_times = analyzer.beat_times.tolist() if hasattr(analyzer, 'beat_times') and analyzer.beat_times is not None else []
            beat_strengths = analyzer.beat_strengths if hasattr(analyzer, 'beat_strengths') else []
            key_moments = analyzer.key_moments if hasattr(analyzer, 'key_moments') else []
            tempo = analyzer.tempo if hasattr(analyzer, 'tempo') else 120.0
            
            return {
                "tempo": float(tempo),
                "beat_times": beat_times,
                "beat_strengths": beat_strengths,
                "key_moments": key_moments
            }
    except Exception as e:
        logger.error(f"Error detecting beats: {e}")
        # Return simple mock data in case of error
        return {
            "tempo": 120.0,
            "beat_times": list(np.linspace(0, 60, 20)),
            "beat_strengths": [0.5] * 20,
            "key_moments": [15.0, 30.0, 45.0],
            "error": str(e)
        }

def create_music_synced_video(
    images: List[str],
    music_path: str,
    output_path: str,
    duration: int = 60,
    resolution: Tuple[int, int] = (1080, 1920),
    effect_intensity: float = 1.0,
    enable_smart_transitions: bool = True,
    enable_captions: bool = False,
    caption_language: str = "en",
    caption_style: str = "default"
) -> str:
    """
    Create a video with images synchronized to music beats using our enhanced video processing.
    
    Args:
        images: List of image paths
        music_path: Path to the music file
        output_path: Path to save the output video
        duration: Target duration in seconds
        resolution: Video resolution (width, height)
        effect_intensity: Intensity of music-responsive effects (0.0-2.0)
        enable_smart_transitions: Whether to use AI-powered transitions
        enable_captions: Whether to add auto-generated captions
        caption_language: Language for captions
        caption_style: Style preset for captions
        
    Returns:
        str: Path to the created video
    """
    logger.info(f"Creating music-synced video with {len(images)} images and music from {music_path}")
    
    # Use our enhanced video creation function
    return create_enhanced_video(
        images=images,
        music_path=music_path,
        output_path=output_path,
        duration=duration,
        resolution=resolution,
        enable_beat_sync=True,
        sync_intensity=effect_intensity,
        enable_smart_transitions=enable_smart_transitions,
        enable_captions=enable_captions,
        caption_language=caption_language,
        caption_style=caption_style,
        whisper_model="base"  # Use base model for reasonable speed/accuracy balance
    )

def add_auto_captions(
    video_path: str,
    output_path: str,
    language: str = "en",
    style: str = "default",
    whisper_model: str = "base"
) -> str:
    """
    Add auto-generated captions to a video using Whisper AI.
    
    Args:
        video_path: Path to the video file
        output_path: Path to save the captioned video
        language: Language code for transcription
        style: Caption style preset
        whisper_model: Whisper model size
        
    Returns:
        str: Path to the captioned video
    """
    logger.info(f"Adding auto-captions to video {video_path} in language {language}")
    
    try:
        return create_styled_captions(
            video_path=video_path,
            output_path=output_path,
            style_preset=style,
            language=language,
            model_size=whisper_model
        )
    except Exception as e:
        logger.error(f"Error adding captions to video: {e}")
        # Return original video in case of error
        return video_path

def create_short(
    images: List[str],
    music_path: Optional[str] = None,
    output_path: str = "output.mp4",
    duration: int = 60,
    resolution: Tuple[int, int] = (1080, 1920),
    sync_to_music: bool = True,
    add_captions: bool = False,
    caption_language: str = "en",
    music_url: Optional[str] = None
) -> str:
    """
    Create a YouTube Short from images and music with optional features.
    
    Args:
        images: List of image paths
        music_path: Optional path to the music file
        output_path: Path to save the output video
        duration: Target duration in seconds
        resolution: Video resolution (width, height)
        sync_to_music: Whether to synchronize to music beats
        add_captions: Whether to add auto-generated captions
        caption_language: Language for captions
        music_url: Optional URL to download music from
        
    Returns:
        str: Path to the created video
    """
    logger.info(f"Creating short with {len(images)} images")
    
    # Download music if URL is provided
    if music_url and not music_path:
        music_path = download_music(music_url)
    
    # Create video based on options
    if music_path and sync_to_music:
        # Create music-synced video with our enhanced processor
        video_path = create_music_synced_video(
            images=images,
            music_path=music_path,
            output_path=output_path,
            duration=duration,
            resolution=resolution,
            enable_captions=add_captions,
            caption_language=caption_language
        )
    else:
        # Create basic video
        video_path = create_video_from_images(
            images=images,
            output_path=output_path,
            duration=duration,
            resolution=resolution
        )
        
        # Add music if provided
        if music_path:
            video_path = add_music_to_video(video_path, music_path)
        
        # Add captions if requested
        if add_captions:
            video_path = add_auto_captions(
                video_path=video_path,
                output_path=output_path,
                language=caption_language
            )
    
    logger.info(f"Short created successfully at {video_path}")
    return video_path 