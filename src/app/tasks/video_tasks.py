"""
Video processing tasks for YouTube Shorts Machine.
"""
import os
import tempfile
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..core.database import create_video, update_video, get_video
from ..services.video.processor import create_short
from ..services.gcs.storage import get_music_url, upload_video, download_file
from ..core.settings import DEV_MODE
from ..services.video.music_responsive import create_music_responsive_video

# Set up logging
logger = logging.getLogger(__name__)

def generate_music_responsive_video(
    video_id: str, 
    image_paths: List[str], 
    music_track_path: str, 
    style_preset: str = "standard",
    output_dir: Optional[str] = None,
    custom_settings: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a music-responsive video from images and music.
    
    Args:
        video_id: Unique identifier for the video
        image_paths: List of paths to image files
        music_track_path: Path to the music track file
        style_preset: Style preset name to use for the video
        output_dir: Optional directory to save the output video
        custom_settings: Optional custom settings to override defaults
        
    Returns:
        str: Path to the generated video file
    """
    logger.info(f"Generating music responsive video {video_id} with preset {style_preset}")
    
    # Update video status
    update_video(video_id, {"status": "processing", "updated_at": datetime.now()})
    
    try:
        # Create output directory if needed
        if not output_dir:
            output_dir = os.path.join(os.getcwd(), "media", "videos")
            os.makedirs(output_dir, exist_ok=True)
        
        # Set output path
        output_path = os.path.join(output_dir, f"{video_id}.mp4")
        
        # Generate video
        result_path = create_music_responsive_video(
            images=image_paths,
            music_path=music_track_path,
            output_path=output_path,
            style_preset=style_preset,
            custom_settings=custom_settings or {}
        )
        
        # Update video status
        update_video(video_id, {
            "status": "completed", 
            "file_path": result_path,
            "updated_at": datetime.now()
        })
        
        return result_path
        
    except Exception as e:
        logger.error(f"Error generating music responsive video: {e}")
        update_video(video_id, {"status": "failed", "error": str(e), "updated_at": datetime.now()})
        raise e

def process_video(video_id: str, image_paths: list, music_track: str, user_credentials: dict = None):
    """
    Process video creation and upload to YouTube.
    
    Args:
        video_id: ID of the video to process
        image_paths: List of paths to image files
        music_track: Name of the music track
        user_credentials: YouTube API credentials (optional)
        
    Returns:
        dict: Processing result
    """
    logger.info(f"Processing video {video_id} with {len(image_paths)} images and track: {music_track}")
    
    # Update video status
    update_video(video_id, {"status": "processing", "updated_at": datetime.now()})
    
    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get music file
            music_url = get_music_url(music_track)
            local_music = os.path.join(temp_dir, os.path.basename(music_track))
            
            try:
                # Download the music file
                if music_url.startswith("http"):
                    from ..services.video.processor import download_music
                    download_music(music_url, local_music)
                else:
                    # Local file, just copy it
                    with open(music_url, 'rb') as src, open(local_music, 'wb') as dst:
                        dst.write(src.read())
                
                logger.info(f"Downloaded music to {local_music}")
            except Exception as e:
                logger.error(f"Error downloading music: {e}")
                # In development mode, we can use mock files
                if DEV_MODE:
                    logger.info("Using mock music file in development mode")
                    with open(local_music, 'w') as f:
                        f.write("Mock music file")
                else:
                    raise
            
            # Create output path
            output_video = os.path.join(temp_dir, f"{video_id}.mp4")
            
            # Process video
            if DEV_MODE:
                logger.info("Simulating video creation in development mode")
                # Create a mock video file for testing
                with open(output_video, 'w') as f:
                    f.write(f"Mock video for {video_id}")
            else:
                # Actually create the video
                create_short(
                    images=image_paths,
                    music_path=local_music,
                    output_path=output_video,
                    duration=60  # Default to 60 seconds for Shorts
                )
            
            # Upload to storage
            logger.info(f"Uploading video to storage: {output_video}")
            video_url = upload_video(output_video, f"videos/{video_id}.mp4")
            
            # Update video status
            update_data = {
                "status": "ready_for_upload",
                "video_url": video_url,
                "updated_at": datetime.now()
            }
            
            # Upload to YouTube if credentials provided
            if user_credentials:
                try:
                    from ..services.youtube.api import upload_to_youtube
                    
                    # Define video metadata
                    title = f"AI-Generated Short - {os.path.basename(music_track)}"
                    description = f"Created with YouTube Shorts Machine using {music_track}"
                    tags = ["shorts", "ai generated", "music", os.path.splitext(music_track)[0]]
                    
                    # Upload to YouTube
                    logger.info(f"Uploading to YouTube: {title}")
                    youtube_id = upload_to_youtube(
                        user_credentials, 
                        video_path=output_video,
                        title=title,
                        description=description,
                        tags=tags
                    )
                    
                    # Update with YouTube ID
                    update_data["status"] = "uploaded"
                    update_data["youtube_id"] = youtube_id
                    logger.info(f"Uploaded to YouTube: {youtube_id}")
                    
                except Exception as e:
                    logger.error(f"Error uploading to YouTube: {e}")
                    # Don't stop processing if YouTube upload fails
            
            # Update video in database
            update_video(video_id, update_data)
            
            return {
                "success": True,
                "video_id": video_id,
                "status": update_data["status"],
                "video_url": video_url
            }
            
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {e}")
        # Update status to failed
        update_video(video_id, {
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.now()
        })
        
        return {
            "success": False,
            "video_id": video_id,
            "status": "failed",
            "error": str(e)
        } 