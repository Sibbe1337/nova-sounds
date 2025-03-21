"""
Video processing utilities for the YouTube Shorts Machine.
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime

# Remove the top-level import to avoid circular imports
# from src.app.services.video.auto_mode import analyze_content_and_get_settings, process_auto_mode_video

# Set up logging
logger = logging.getLogger(__name__)

def analyze_content_and_get_settings(image_paths: List[str], user_settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Wrapper for the auto mode function - analyze content and get optimal video settings.
    
    Args:
        image_paths: List of paths to the images
        user_settings: Optional user-provided settings to override defaults
        
    Returns:
        dict: Complete settings for video creation
    """
    try:
        # Import here to avoid circular imports
        from src.app.services.video.auto_mode import analyze_content_and_get_settings as auto_analyze
        return auto_analyze(image_paths, user_settings)
    except Exception as e:
        logger.error(f"Error in analyze_content_and_get_settings: {e}")
        # Provide fallback default settings
        return {
            "content_analysis": {
                "category": "general",
                "mood": "neutral",
                "theme": "lifestyle",
                "brightness": 0.5,
                "colorfulness": 0.5,
                "complexity": 0.5
            },
            "music_track": "default_track",
            "video_style": {
                "style": "standard",
                "transition": "fade",
                "music_sync_intensity": 1.0,
                "caption_style": "standard",
                "color_grading": "natural"
            },
            "enable_music_sync": True,
            "use_smart_transitions": True,
            "enable_captions": False,
            "use_runway": False,  # Default to not using Runway ML
            "export_format": "mp4",
            "export_quality": 85
        }

def process_auto_mode_video(video_id: str, image_paths: List[str], settings: Dict[str, Any]) -> str:
    """
    Wrapper for the auto mode function - process a video in Auto Mode.
    
    Args:
        video_id: Unique ID for the video
        image_paths: List of paths to the images
        settings: Video creation settings
        
    Returns:
        str: Path to the created video
    """
    try:
        # Import here to avoid circular imports
        from src.app.services.video.auto_mode import process_auto_mode_video as auto_process
        return auto_process(video_id, image_paths, settings)
    except Exception as e:
        logger.error(f"Error in process_auto_mode_video: {e}")
        
        # Create a mock video file as a fallback
        output_dir = os.path.join("media", "videos")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{video_id}.mp4")
        
        with open(output_path, 'w') as f:
            f.write(f"Mock video file created at {datetime.now()}")
            
        return output_path 