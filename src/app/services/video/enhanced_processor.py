"""
Enhanced video processor with advanced features for YouTube Shorts.

This module provides integrated functionality for creating high-quality
short-form videos with features like beat syncing, smart transitions,
and AI-powered auto-captioning.
"""

import os
import tempfile
import logging
import json
import time
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union, Literal
from enum import Enum

from src.app.core.settings import DEV_MODE, DEBUG_MODE, get_setting
from src.app.services.video.music_responsive.generator import create_music_responsive_video
from src.app.services.video.music_responsive.presets import StylePreset
from src.app.services.video.music_responsive.effects import AdvancedTransitionSystem
from src.app.services.video.caption import (
    add_captions_to_video, 
    create_styled_captions,
    CaptionStyle
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessingOptions:
    """Configuration options for video processing."""
    
    def __init__(
        self,
        enable_music_sync: bool = True,
        music_sync_intensity: float = 1.0,
        use_smart_transitions: bool = True,
        transition_style: str = "dynamic",  # static, dynamic, minimal
        enable_captions: bool = False,
        caption_style: str = "default",  # default, subtitle, tiktok, youtube, minimal
        caption_language: str = "auto",  # auto, en, es, fr, etc.
        whisper_model: str = "base",  # tiny, base, small, medium, large-v1, large-v2
        use_openai_api: bool = False,
        api_key: Optional[str] = None,
        export_format: str = "mp4",
        export_quality: int = 85,  # 0-100
    ):
        """
        Initialize video processing options.
        
        Args:
            enable_music_sync: Whether to enable music-responsive effects
            music_sync_intensity: Intensity of music-responsive effects (0.0-2.0)
            use_smart_transitions: Whether to use smart transitions based on music structure
            transition_style: Style of transitions to use
            enable_captions: Whether to add auto-generated captions
            caption_style: Style preset for captions
            caption_language: Language for transcription or 'auto' for automatic detection
            whisper_model: Whisper model size to use for transcription
            use_openai_api: Whether to use OpenAI API for transcription (requires API key)
            api_key: OpenAI API key for cloud-based transcription
            export_format: Output video format (mp4, mov, etc.)
            export_quality: Quality of output video (0-100)
        """
        self.enable_music_sync = enable_music_sync
        self.music_sync_intensity = max(0.0, min(2.0, music_sync_intensity))
        self.use_smart_transitions = use_smart_transitions
        self.transition_style = transition_style
        self.enable_captions = enable_captions
        self.caption_style = caption_style
        self.caption_language = caption_language
        self.whisper_model = whisper_model
        self.use_openai_api = use_openai_api
        self.api_key = api_key
        self.export_format = export_format
        self.export_quality = max(0, min(100, export_quality))

class EnhancedVideoProcessor:
    """
    Enhanced video processor with advanced features for creating
    high-quality short-form videos.
    """
    
    def __init__(self, options: Optional[VideoProcessingOptions] = None):
        """
        Initialize the enhanced video processor.
        
        Args:
            options: Configuration options for video processing
        """
        self.options = options or VideoProcessingOptions()
        logger.info("Initializing EnhancedVideoProcessor")
    
    def process_video(
        self, 
        images: List[str], 
        music_path: str, 
        output_path: str,
        duration: int = 60,
        resolution: Tuple[int, int] = (1080, 1920),
        fps: int = 30,
        preset: Optional[str] = None,
        custom_caption_style: Optional[CaptionStyle] = None,
        use_runway: bool = False
    ) -> str:
        """
        Process a video with all enabled enhancements.
        
        Args:
            images: List of image paths to use in the video
            music_path: Path to the music file
            output_path: Path to save the output video
            duration: Target duration in seconds
            resolution: Video resolution (width, height)
            fps: Frames per second
            preset: Optional style preset name
            custom_caption_style: Optional custom caption style
            use_runway: Whether to use Runway ML for enhanced video generation
            
        Returns:
            str: Path to the processed video
        """
        start_time = time.time()
        logger.info(f"Starting video processing with {len(images)} images and music from {music_path}")
        
        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            current_video_path = None
            
            # Step 1: Create music-responsive video if enabled
            if self.options.enable_music_sync:
                logger.info("Creating music-responsive video with enhanced beat detection")
                
                # Determine output path for music-responsive video
                music_sync_path = os.path.join(temp_dir, "music_sync.mp4")
                
                try:
                    # Create the music-responsive video
                    music_sync_video = create_music_responsive_video(
                        images=images,
                        music_path=music_path,
                        output_path=music_sync_path,
                        fps=fps,
                        duration=duration,
                        resolution=resolution,
                        effect_intensity=self.options.music_sync_intensity,
                        use_smart_transitions=self.options.use_smart_transitions,
                        preset=StylePreset(preset) if preset else None
                    )
                    
                    current_video_path = music_sync_video
                    logger.info(f"Music-responsive video created at {current_video_path}")
                except Exception as e:
                    logger.error(f"Error creating music-responsive video: {e}")
                    # Fallback to direct image sequence if music sync fails
                    current_video_path = self._create_basic_video(
                        images, music_path, os.path.join(temp_dir, "basic.mp4"), 
                        duration, resolution, fps
                    )
            else:
                # Create a basic video without music responsiveness
                logger.info("Creating basic video (music sync disabled)")
                current_video_path = self._create_basic_video(
                    images, music_path, os.path.join(temp_dir, "basic.mp4"), 
                    duration, resolution, fps
                )
            
            # Step 2: Add captions if enabled
            if self.options.enable_captions and current_video_path:
                logger.info(f"Adding captions using Whisper {self.options.whisper_model} model")
                
                captioned_path = os.path.join(temp_dir, "captioned.mp4")
                
                try:
                    # Determine language for transcription
                    language = self.options.caption_language
                    if language == "auto":
                        language = None  # Whisper will auto-detect
                    
                    if custom_caption_style:
                        # Use custom caption style
                        captioned_video = add_captions_to_video(
                            video_path=current_video_path,
                            output_path=captioned_path,
                            language=language,
                            model_size=self.options.whisper_model,
                            caption_style=custom_caption_style,
                            api_key=self.options.api_key if self.options.use_openai_api else None
                        )
                    else:
                        # Use preset caption style
                        captioned_video = create_styled_captions(
                            video_path=current_video_path,
                            output_path=captioned_path,
                            style_preset=self.options.caption_style,
                            language=language,
                            model_size=self.options.whisper_model
                        )
                    
                    current_video_path = captioned_video
                    logger.info(f"Captioning completed: {current_video_path}")
                except Exception as e:
                    logger.error(f"Error adding captions: {e}")
                    # Keep the current video if captioning fails
            
            # Step 3: Apply final processing and export
            try:
                self._export_final_video(current_video_path, output_path)
                logger.info(f"Video processing completed in {time.time() - start_time:.2f} seconds")
                return output_path
            except Exception as e:
                logger.error(f"Error exporting final video: {e}")
                # Return the current video path if export fails
                return current_video_path
    
    def _create_basic_video(
        self, 
        images: List[str], 
        music_path: str, 
        output_path: str,
        duration: int,
        resolution: Tuple[int, int],
        fps: int
    ) -> str:
        """
        Create a basic video without music responsiveness.
        
        Args:
            images: List of image paths
            music_path: Path to music file
            output_path: Path to save output video
            duration: Target duration in seconds
            resolution: Video resolution (width, height)
            fps: Frames per second
            
        Returns:
            str: Path to the created video
        """
        width, height = resolution
        frame_count = min(duration * fps, 300 * fps)  # Cap at 5 minutes
        
        # Load and resize images
        image_frames = []
        for img_path in images:
            try:
                img = cv2.imread(img_path)
                if img is not None:
                    img_resized = cv2.resize(img, (width, height))
                    image_frames.append(img_resized)
            except Exception as e:
                logger.error(f"Error loading image {img_path}: {e}")
        
        # Duplicate images if not enough
        while len(image_frames) < 5:
            image_frames.extend(image_frames[:])
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Calculate frame duration
        frames_per_image = frame_count // len(image_frames)
        extra_frames = frame_count % len(image_frames)
        
        # Write frames
        for i, frame in enumerate(image_frames):
            # Calculate how many frames to show this image
            if i < extra_frames:
                display_frames = frames_per_image + 1
            else:
                display_frames = frames_per_image
            
            # Write the frame multiple times
            for _ in range(display_frames):
                video_writer.write(frame)
        
        video_writer.release()
        
        # Add audio to the video
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output = os.path.join(temp_dir, "with_audio.mp4")
            
            # FFmpeg command to add audio
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', output_path,
                '-i', music_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',  # End when shortest input ends
                temp_output
            ]
            
            # Run FFmpeg
            try:
                import subprocess
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
                return temp_output
            except Exception as e:
                logger.error(f"Error adding audio: {e}")
                return output_path
    
    def _export_final_video(self, input_path: str, output_path: str) -> None:
        """
        Export the final video with specified quality and format.
        
        Args:
            input_path: Path to input video
            output_path: Path to save output video
        """
        # If input and output are the same, create a temporary file
        if input_path == output_path:
            temp_path = output_path + ".temp." + self.options.export_format
            output_file = temp_path
        else:
            output_file = output_path
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Map quality (0-100) to CRF value (0-51, lower is better)
        # 0 quality -> CRF 51 (worst)
        # 100 quality -> CRF 0 (best, lossless)
        crf = int(51 - (self.options.export_quality / 100 * 51))
        
        # FFmpeg command for final export
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'slow',  # Use 'slow' for better compression
            '-crf', str(crf),
            '-c:a', 'aac',
            '-b:a', '192k',
            output_file
        ]
        
        # Run FFmpeg
        try:
            import subprocess
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
            
            # If we created a temp file, rename it to the final output path
            if input_path == output_path:
                import shutil
                shutil.move(temp_path, output_path)
        except Exception as e:
            logger.error(f"Error exporting final video: {e}")
            raise

def create_enhanced_video(
    images: List[str],
    music_path: str,
    output_path: str,
    duration: int = 60,
    resolution: Tuple[int, int] = (1080, 1920),
    enable_beat_sync: bool = True,
    sync_intensity: float = 1.0,
    enable_smart_transitions: bool = True,
    enable_captions: bool = False,
    caption_language: str = "en",
    caption_style: str = "default",
    whisper_model: str = "base",
    use_runway: bool = False
) -> str:
    """
    Convenience function to create an enhanced video with specified features.
    
    Args:
        images: List of image paths
        music_path: Path to music file
        output_path: Path to save output video
        duration: Target duration in seconds (default: 60)
        resolution: Video resolution (width, height) (default: 1080x1920)
        enable_beat_sync: Enable beat-synchronized effects (default: True)
        sync_intensity: Intensity of music sync effects (0.0-2.0) (default: 1.0)
        enable_smart_transitions: Use AI-powered smart transitions (default: True)
        enable_captions: Add auto-generated captions (default: False)
        caption_language: Language code for captions (default: "en")
        caption_style: Caption style preset (default: "default")
        whisper_model: Whisper model size (default: "base")
        use_runway: Whether to use Runway ML for enhanced video generation
        
    Returns:
        str: Path to the created video
    """
    # Create processing options
    options = VideoProcessingOptions(
        enable_music_sync=enable_beat_sync,
        music_sync_intensity=sync_intensity,
        use_smart_transitions=enable_smart_transitions,
        enable_captions=enable_captions,
        caption_language=caption_language,
        caption_style=caption_style,
        whisper_model=whisper_model
    )
    
    # Create processor and process video
    processor = EnhancedVideoProcessor(options)
    return processor.process_video(
        images=images,
        music_path=music_path,
        output_path=output_path,
        duration=duration,
        resolution=resolution,
        use_runway=use_runway
    )

class VideoStyle(Enum):
    """Video style presets for enhanced shorts."""
    DYNAMIC = "dynamic"
    MINIMAL = "minimal"
    ENERGETIC = "energetic"
    SMOOTH = "smooth"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    CUSTOM = "custom"

def create_enhanced_short(
    images: List[str],
    music_path: str,
    output_path: str,
    style: Union[str, VideoStyle] = VideoStyle.DYNAMIC,
    duration: int = 60,
    resolution: Tuple[int, int] = (1080, 1920),
    enable_captions: bool = False,
    caption_text: Optional[str] = None,
    caption_language: str = "en",
    use_runway: bool = False,
) -> str:
    """
    Create an enhanced short video with the specified style.
    
    This is a wrapper around create_enhanced_video that simplifies
    the interface by using predefined style presets.
    
    Args:
        images: List of image paths
        music_path: Path to music file
        output_path: Path to save the output video
        style: Video style to use (from VideoStyle enum or string)
        duration: Duration of the video in seconds
        resolution: Video resolution as (width, height)
        enable_captions: Whether to add captions
        caption_text: Optional text for captions (auto-generated if None)
        caption_language: Language code for captions
        use_runway: Whether to use Runway ML for enhanced video generation
        
    Returns:
        Path to the created video
    """
    # Convert string style to enum if needed
    if isinstance(style, str):
        try:
            style = VideoStyle(style)
        except ValueError:
            style = VideoStyle.DYNAMIC
    
    # Map style to options
    style_options = {
        VideoStyle.DYNAMIC: {
            "enable_beat_sync": True,
            "sync_intensity": 1.0,
            "enable_smart_transitions": True
        },
        VideoStyle.MINIMAL: {
            "enable_beat_sync": False,
            "sync_intensity": 0.5,
            "enable_smart_transitions": False
        },
        VideoStyle.ENERGETIC: {
            "enable_beat_sync": True,
            "sync_intensity": 1.5,
            "enable_smart_transitions": True
        },
        VideoStyle.SMOOTH: {
            "enable_beat_sync": True,
            "sync_intensity": 0.8,
            "enable_smart_transitions": True
        },
        VideoStyle.TIKTOK: {
            "enable_beat_sync": True,
            "sync_intensity": 1.2,
            "enable_smart_transitions": True
        },
        VideoStyle.YOUTUBE: {
            "enable_beat_sync": True,
            "sync_intensity": 1.0,
            "enable_smart_transitions": True
        },
        VideoStyle.INSTAGRAM: {
            "enable_beat_sync": True,
            "sync_intensity": 0.9,
            "enable_smart_transitions": True
        },
        VideoStyle.CUSTOM: {
            "enable_beat_sync": True,
            "sync_intensity": 1.0,
            "enable_smart_transitions": True
        }
    }
    
    options = style_options.get(style, style_options[VideoStyle.DYNAMIC])
    
    if DEV_MODE:
        logger.info(f"Creating enhanced short with style: {style.name if isinstance(style, VideoStyle) else style}")
        if use_runway:
            logger.info("Using Runway ML for enhanced video generation")
    
    # Create the video
    return create_enhanced_video(
        images=images,
        music_path=music_path,
        output_path=output_path,
        duration=duration,
        resolution=resolution,
        enable_beat_sync=options["enable_beat_sync"],
        sync_intensity=options["sync_intensity"],
        enable_smart_transitions=options["enable_smart_transitions"],
        enable_captions=enable_captions,
        caption_language=caption_language,
        caption_style="default" if style != VideoStyle.TIKTOK else "tiktok",
        use_runway=use_runway
    )
    
def suggest_enhancements(
    images: List[str],
    music_path: str
) -> Dict[str, Any]:
    """
    Analyze images and music to suggest video enhancements.
    
    Args:
        images: List of image paths
        music_path: Path to music file
        
    Returns:
        Dictionary with enhancement suggestions
    """
    # In production, this would analyze the images and music
    # and return intelligent suggestions. For now, return mock data.
    
    if DEV_MODE:
        logger.info(f"Suggesting enhancements for {len(images)} images and music: {music_path}")
        
        # Mock analysis result
        styles = [s.value for s in VideoStyle]
        
        return {
            "suggested_style": VideoStyle.DYNAMIC.value,
            "alternative_styles": [
                VideoStyle.ENERGETIC.value,
                VideoStyle.SMOOTH.value
            ],
            "confidence": 0.85,
            "available_styles": styles,
            "music_properties": {
                "tempo": 120,
                "energy": 0.8,
                "mood": "upbeat"
            },
            "image_properties": {
                "color_palette": "vibrant",
                "content_type": "lifestyle"
            }
        }
    
    # Starting point for a real implementation
    from src.app.services.music.recommendations import MusicRecommendationService
    
    # Get a recommendation service
    service = MusicRecommendationService()
    
    # Analyze the track
    track_name = os.path.basename(music_path)
    analysis = service.analyze_track(track_name)
    
    # Choose style based on music properties
    suggested_style = VideoStyle.DYNAMIC.value
    
    if analysis.get("energy", 0) > 0.8:
        suggested_style = VideoStyle.ENERGETIC.value
    elif analysis.get("energy", 0) < 0.4:
        suggested_style = VideoStyle.SMOOTH.value
    
    return {
        "suggested_style": suggested_style,
        "alternative_styles": [s.value for s in VideoStyle if s.value != suggested_style][:3],
        "confidence": 0.7,
        "available_styles": [s.value for s in VideoStyle],
        "music_properties": analysis,
        "image_properties": {
            "color_palette": "mixed",
            "content_type": "unknown"
        }
    } 