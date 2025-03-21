from typing import Dict, Any, List, Optional
import json
import os
import uuid
from fastapi import APIRouter, Request, BackgroundTasks, File, Form, UploadFile, Body, Query
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from pathlib import Path
from src.app.utils.video_processing import analyze_content_and_get_settings, process_auto_mode_video
from src.app.utils.logger import logger
from src.app.tasks.video_tasks import process_video, generate_music_responsive_video
from src.app.services.video.music_responsive import create_music_responsive_video
from src.app.core.settings import DEV_MODE
from src.app.core.database import get_video_by_id
from datetime import datetime

# Create API router
router = APIRouter(prefix="/videos", tags=["videos"])

class VideoGenerationParams(BaseModel):
    """Parameters for video generation."""
    music_track_id: str
    style_preset: str
    images: List[str] = []
    video_clips: List[str] = []
    custom_settings: Optional[Dict[str, Any]] = None
    captions_enabled: bool = False
    metadata: Optional[Dict[str, Any]] = None
    target_platforms: List[str] = ["youtube"]


@router.post("/generate", response_model=Dict[str, Any])
async def generate_video(params: VideoGenerationParams):
    """
    Generate a music-responsive video using the specified parameters.
    
    This endpoint starts a Celery task to generate the video and returns the task ID
    for tracking progress.
    
    Args:
        params: Parameters for video generation
        
    Returns:
        dict: Task information including task_id
    """
    try:
        # Validate music track ID
        if not params.music_track_id:
            raise HTTPException(status_code=400, detail="Music track ID is required")
            
        # Validate style preset
        if not params.style_preset:
            raise HTTPException(status_code=400, detail="Style preset is required")
            
        # Validate that we have either images or video clips
        if not params.images and not params.video_clips:
            raise HTTPException(status_code=400, detail="At least one image or video clip is required")
            
        # Generate a video ID
        video_id = str(uuid.uuid4())
            
        # Call the process_video function directly 
        # In a real app, you might want to use task.delay for async processing
        process_result = process_video(
            video_id=video_id,
            image_paths=params.images,
            music_track=params.music_track_id,
            user_credentials=None  # No credentials for this test
        )
        
        # Return task information
        if process_result and process_result.get('success', False):
            return {
                "status": "success",
                "message": "Video generation task started",
                "task_id": video_id,
                "video_url": process_result.get('video_url', None)
            }
        else:
            # If there was an issue with the processing
            raise HTTPException(
                status_code=500, 
                detail=process_result.get('error', 'Unknown error during video processing')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error starting video generation task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-mode", response_model=Dict[str, Any])
async def create_auto_mode_video(
    request: Request,
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(...),
    auto_mode_settings: str = Form("{}"),
):
    """
    Create a video using Auto Mode with automatic style and music selection.
    
    Args:
        request: Request object
        background_tasks: Background tasks
        images: List of image files to use in the video
        auto_mode_settings: JSON string with optional auto mode settings
    
    Returns:
        dict: Information about the created video including video_id
    """
    try:
        # Parse settings
        settings = json.loads(auto_mode_settings)
        
        # Generate a unique ID for the video
        video_id = str(uuid.uuid4())
        
        # Create temp directory for images
        upload_dir = os.path.join("uploads", video_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded images
        image_paths = []
        for i, img in enumerate(images):
            img_path = os.path.join(upload_dir, f"image_{i}{Path(img.filename).suffix}")
            with open(img_path, "wb") as f:
                content = await img.read()
                f.write(content)
            image_paths.append(img_path)
        
        # Auto analyze content and select settings
        auto_settings = analyze_content_and_get_settings(image_paths, settings)
        
        # Process video in background
        background_tasks.add_task(
            process_auto_mode_video,
            video_id=video_id,
            image_paths=image_paths,
            settings=auto_settings
        )
        
        # Return video information
        return {
            "status": "success",
            "message": "Auto mode video creation started",
            "video_id": video_id,
            "settings": auto_settings
        }
    except Exception as e:
        logger.error(f"Error creating auto mode video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}", response_model=Dict[str, Any])
async def get_video_info(video_id: str):
    """
    Get information about a video by its ID.
    
    Args:
        video_id: ID of the video
        
    Returns:
        dict: Video information
    """
    try:
        # In a real implementation, this would retrieve video info from a database
        # For now, we'll return mock data
        if DEV_MODE:
            return {
                "video_id": video_id,
                "status": "completed",
                "created_at": "2023-03-21T12:34:56Z",
                "duration": 30,
                "size": 12345678,
                "format": "mp4",
                "resolution": "1080x1920",
                "url": f"/api/videos/{video_id}/download",
                "thumbnail_url": f"/api/videos/{video_id}/thumbnail",
                "music_track": {
                    "id": "track123",
                    "title": "Sample Music Track",
                    "artist": "Sample Artist",
                    "bpm": 120
                },
                "style_preset": "vlog",
                "platforms_published": [],
                "metadata": {
                    "title": "Sample Video Title",
                    "description": "This is a sample video description.",
                    "hashtags": ["#shorts", "#musicvideo", "#trending"]
                }
            }
        else:
            # Implement actual database lookup
            video_data = get_video_by_id(video_id)
            
            if not video_data:
                raise HTTPException(status_code=404, detail=f"Video with ID {video_id} not found")
            
            # Format response
            return {
                "id": video_id,
                "status": video_data.get("status", "unknown"),
                "created_at": video_data.get("created_at", datetime.now().isoformat()),
                "duration": video_data.get("duration", 0),
                "url": f"/api/videos/{video_id}/download",
                "thumbnail_url": f"/api/videos/{video_id}/thumbnail",
                "music_track": video_data.get("music_track", {
                    "id": "unknown",
                    "title": "Unknown Track",
                    "artist": "Unknown Artist",
                    "bpm": 0
                }),
                "style_preset": video_data.get("style_preset", "standard"),
                "platforms_published": video_data.get("platforms_published", []),
                "metadata": video_data.get("metadata", {
                    "title": "",
                    "description": "",
                    "hashtags": []
                })
            }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 