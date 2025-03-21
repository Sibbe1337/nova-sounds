"""
Video format optimizations for different platforms.
"""
import os
import logging
import tempfile
import subprocess
from typing import Dict, Any

from src.app.core.settings import DEBUG_MODE

# Set up logging
logger = logging.getLogger(__name__)

# Platform-specific video requirements
PLATFORM_REQUIREMENTS = {
    "youtube": {
        "aspect_ratio": "9:16",
        "max_duration": 60,
        "resolution": "1080x1920",
        "bitrate": "8M",
        "audio_bitrate": "128k"
    },
    "tiktok": {
        "aspect_ratio": "9:16",
        "max_duration": 60,
        "resolution": "1080x1920",
        "bitrate": "5M",
        "audio_bitrate": "128k"
    },
    "instagram": {
        "aspect_ratio": "9:16",
        "max_duration": 90,
        "resolution": "1080x1920",
        "bitrate": "3.5M",
        "audio_bitrate": "128k"
    },
    "facebook": {
        "aspect_ratio": "9:16",
        "max_duration": 60,
        "resolution": "1080x1920",
        "bitrate": "4M",
        "audio_bitrate": "128k"
    }
}

def optimize_video_for_platform(video_path: str, platform: str, output_path: str = None) -> str:
    """
    Optimize a video for a specific platform.
    
    Args:
        video_path: Path to input video
        platform: Target platform (youtube, tiktok, instagram, facebook)
        output_path: Optional path for output file
        
    Returns:
        str: Path to optimized video
    """
    # Get platform requirements (default to YouTube if unknown platform)
    platform_lower = platform.lower()
    settings = PLATFORM_REQUIREMENTS.get(platform_lower, PLATFORM_REQUIREMENTS["youtube"])
    
    # If no output path specified, create a temporary file
    if not output_path:
        temp_dir = tempfile.gettempdir()
        output_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_{platform_lower}.mp4"
        output_path = os.path.join(temp_dir, output_filename)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check video duration and properties
    duration_check_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    
    try:
        result = subprocess.run(duration_check_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        
        # Check if video needs to be trimmed
        max_duration = settings.get("max_duration", 60)
        needs_trimming = duration > max_duration
        
        if needs_trimming:
            logger.info(f"Video duration {duration}s exceeds {max_duration}s for {platform}, will trim")
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking video duration: {e}")
        needs_trimming = False
        duration = 0
    
    # Build FFmpeg command
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-i', video_path,
    ]
    
    # Add trim filter if needed
    if needs_trimming:
        ffmpeg_cmd.extend(['-t', str(max_duration)])
    
    # Add video settings
    ffmpeg_cmd.extend([
        '-vf', f"scale={settings['resolution'].split('x')[0]}:{settings['resolution'].split('x')[1]}",
        '-c:v', 'libx264',
        '-preset', 'fast',  # Fast encoding, good enough quality
        '-b:v', settings['bitrate'],
        '-c:a', 'aac',
        '-b:a', settings['audio_bitrate'],
        '-movflags', '+faststart',  # Optimize for web playback
        output_path
    ])
    
    # Run FFmpeg command
    try:
        logger.info(f"Optimizing video for {platform}: {video_path} -> {output_path}")
        if DEBUG_MODE:
            # In debug mode, show FFmpeg output
            subprocess.run(ffmpeg_cmd, check=True)
        else:
            # Otherwise, hide output
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        logger.info(f"Video optimized for {platform}: {output_path}")
        return output_path
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error optimizing video for {platform}: {e}")
        if os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except:
                pass
        raise ValueError(f"Failed to optimize video for {platform}: {e}")

def get_platform_requirements(platform: str = None) -> Dict[str, Any]:
    """
    Get video requirements for a specific platform or all platforms.
    
    Args:
        platform: Optional platform name
        
    Returns:
        Dict: Platform requirements
    """
    if platform:
        platform_lower = platform.lower()
        if platform_lower in PLATFORM_REQUIREMENTS:
            return {platform_lower: PLATFORM_REQUIREMENTS[platform_lower]}
        else:
            return {}
    else:
        return PLATFORM_REQUIREMENTS 