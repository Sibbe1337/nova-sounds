"""
Multi-platform video adaptation for different social media platforms.
"""
import os
import logging
import tempfile
import subprocess
import json
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum, auto
from pathlib import Path
import time

from src.app.core.settings import DEV_MODE
from src.app.services.video.music_responsive.analytics import get_analytics_manager

# Set up logging
logger = logging.getLogger(__name__)

class Platform(str, Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"

class ResizeMode(str, Enum):
    """Video resize modes."""
    CROP = "crop"
    LETTERBOX = "letterbox"
    STRETCH = "stretch"

class PlatformSpecs:
    """Platform-specific specifications."""
    
    # Platform specifications
    SPECS = {
        Platform.YOUTUBE: {
            "aspect_ratio": "9:16",  # Vertical shorts
            "resolution": (1080, 1920),  # Width, height
            "max_duration": 60,  # Seconds
            "max_filesize": 256,  # MB
            "formats": ["mp4"],
            "audio_bitrate": "128k",
            "video_bitrate": "8000k",
        },
        Platform.TIKTOK: {
            "aspect_ratio": "9:16",
            "resolution": (1080, 1920),
            "max_duration": 60,
            "max_filesize": 287,  # MB
            "formats": ["mp4"],
            "audio_bitrate": "128k",
            "video_bitrate": "8000k",
        },
        Platform.INSTAGRAM: {
            "aspect_ratio": "9:16",
            "resolution": (1080, 1920),
            "max_duration": 60,
            "max_filesize": 100,  # MB
            "formats": ["mp4"],
            "audio_bitrate": "128k", 
            "video_bitrate": "5000k",
        },
        Platform.FACEBOOK: {
            "aspect_ratio": "9:16",
            "resolution": (1080, 1920),
            "max_duration": 60,
            "max_filesize": 1024,  # MB
            "formats": ["mp4"],
            "audio_bitrate": "128k",
            "video_bitrate": "5000k",
        }
    }
    
    @classmethod
    def get_spec(cls, platform: Platform) -> Dict[str, Any]:
        """Get specifications for a platform."""
        return cls.SPECS.get(platform, cls.SPECS[Platform.YOUTUBE])

def adapt_video_for_platform(
    video_path: str,
    platform: Platform,
    output_path: Optional[str] = None,
    resize_mode: ResizeMode = ResizeMode.CROP,
    session_id: Optional[str] = None
) -> str:
    """
    Adapt a video for a specific platform.
    
    Args:
        video_path: Path to the input video
        platform: Target platform
        output_path: Optional output path (default: auto-generate)
        resize_mode: How to handle aspect ratio differences
        session_id: Optional session ID for analytics tracking
        
    Returns:
        Path to the adapted video
    """
    start_time = time.time()
    analytics_manager = get_analytics_manager() if session_id else None
    
    # Get platform specs
    specs = PlatformSpecs.get_spec(platform)
    target_width, target_height = specs["resolution"]
    
    # Generate output path if not provided
    if not output_path:
        input_path = Path(video_path)
        output_dir = input_path.parent
        output_name = f"{input_path.stem}_{platform.value}{input_path.suffix}"
        output_path = str(output_dir / output_name)
    
    # In development mode, just create a copy
    if DEV_MODE:
        logger.info(f"DEV mode: Simulating adaptation of {video_path} for {platform.value}")
        
        # Check if input file exists
        if not os.path.exists(video_path):
            logger.error(f"Input video file {video_path} not found")
            # Create a dummy file
            with open(output_path, 'w') as f:
                f.write(f"Mock adapted video for {platform.value}")
            return output_path
        
        # Create a simple copy with a note in the output path
        import shutil
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy(video_path, output_path)
        logger.info(f"Created mock adapted video at {output_path}")
        return output_path
    
    # Get video information using ffprobe
    try:
        logger.info(f"Analyzing video: {video_path}")
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration",
            "-of", "json",
            video_path
        ]
        
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        video_info = json.loads(result.stdout)
        stream_info = video_info.get("streams", [{}])[0]
        
        input_width = int(stream_info.get("width", 0))
        input_height = int(stream_info.get("height", 0))
        input_duration = float(stream_info.get("duration", 0))
        
        logger.info(f"Source video: {input_width}x{input_height}, {input_duration:.2f}s")
        logger.info(f"Target specs: {target_width}x{target_height}, max {specs['max_duration']}s")
        
        # Check if adaptation is needed
        if (input_width == target_width and input_height == target_height and 
            input_duration <= specs["max_duration"]):
            logger.info("Video already meets platform specifications")
            
            # Just make a direct copy if the formats match
            if video_path.endswith(".mp4") and "mp4" in specs["formats"]:
                import shutil
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy(video_path, output_path)
                logger.info(f"Copied video to {output_path}")
                return output_path
        
        # Prepare FFmpeg command based on resize mode
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path]
        
        # Handle duration limits
        if input_duration > specs["max_duration"]:
            ffmpeg_cmd.extend(["-t", str(specs["max_duration"])])
            logger.info(f"Trimming video to {specs['max_duration']} seconds")
        
        # Handle aspect ratio adaptation
        if input_width != target_width or input_height != target_height:
            logger.info(f"Adapting aspect ratio using {resize_mode} mode")
            
            if resize_mode == ResizeMode.CROP:
                # Crop to fit
                ffmpeg_cmd.extend([
                    "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height}"
                ])
            elif resize_mode == ResizeMode.LETTERBOX:
                # Add letterbox/pillarbox
                ffmpeg_cmd.extend([
                    "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
                ])
            else:  # STRETCH
                # Simply stretch
                ffmpeg_cmd.extend([
                    "-vf", f"scale={target_width}:{target_height}"
                ])
        
        # Set codec and bitrate
        ffmpeg_cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", specs["video_bitrate"],
            "-c:a", "aac",
            "-b:a", specs["audio_bitrate"],
            "-movflags", "+faststart",  # Optimize for web playback
            output_path
        ])
        
        # Run FFmpeg command
        logger.info(f"Running FFmpeg: {' '.join(ffmpeg_cmd)}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        subprocess.run(ffmpeg_cmd, check=True)
        
        logger.info(f"Adapted video saved to {output_path}")
        
        # Track the successful adaptation
        if analytics_manager and session_id:
            processing_time = time.time() - start_time
            file_size = os.path.getsize(output_path)
            analytics_manager.track_platform_distribution(
                session_id=session_id,
                platform=platform.value,
                success=True,
                metrics={
                    'processing_time': processing_time,
                    'file_size': file_size,
                    'resolution': f"{target_width}x{target_height}"
                }
            )
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error adapting video: {e}")
        if DEV_MODE:
            # Create dummy file in dev mode
            with open(output_path, 'w') as f:
                f.write(f"Mock adapted video for {platform.value} (error occurred)")
            logger.info(f"Created mock adapted video at {output_path} due to error")
            return output_path
        # Track the failed adaptation
        if analytics_manager and session_id:
            analytics_manager.track_platform_distribution(
                session_id=session_id,
                platform=platform.value,
                success=False,
                metrics={
                    'error': str(e)
                }
            )
        raise

def prepare_all_platforms(
    video_path: str,
    resize_mode: ResizeMode = ResizeMode.CROP
) -> Dict[Platform, str]:
    """
    Prepare a video for all supported platforms.
    
    Args:
        video_path: Path to the input video
        resize_mode: How to handle aspect ratio differences
        
    Returns:
        Dictionary mapping platforms to adapted video paths
    """
    logger.info(f"Preparing video for all platforms: {video_path}")
    
    result = {}
    input_path = Path(video_path)
    output_dir = input_path.parent / "multi_platform"
    os.makedirs(output_dir, exist_ok=True)
    
    for platform in Platform:
        try:
            output_path = str(output_dir / f"{input_path.stem}_{platform.value}.mp4")
            adapted_path = adapt_video_for_platform(
                video_path=video_path,
                platform=platform,
                output_path=output_path,
                resize_mode=resize_mode
            )
            result[platform] = adapted_path
            logger.info(f"Successfully adapted for {platform.value}: {adapted_path}")
        except Exception as e:
            logger.error(f"Failed to adapt for {platform.value}: {e}")
            # Continue with other platforms
    
    return result

def get_platform_requirements() -> Dict[str, Dict[str, Any]]:
    """
    Get requirements for all supported platforms.
    
    Returns:
        Dictionary with platform requirements
    """
    requirements = {}
    
    for platform in Platform:
        specs = PlatformSpecs.get_spec(platform)
        requirements[platform.value] = {
            "aspect_ratio": specs["aspect_ratio"],
            "resolution": f"{specs['resolution'][0]}x{specs['resolution'][1]}",
            "max_duration": f"{specs['max_duration']} seconds",
            "max_filesize": f"{specs['max_filesize']} MB",
            "formats": ", ".join(specs["formats"])
        }
    
    return requirements 