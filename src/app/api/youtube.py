"""
YouTube API v3 endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import tempfile
import shutil

from src.app.services.youtube.test_api import search_videos, get_video_details, get_channel_info, get_user_videos, get_video_metrics
from src.app.services.youtube.api import upload_to_youtube as youtube_uploader
from src.app.api.auth import get_credentials

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/youtube", tags=["youtube"])

# Pydantic models for request/response
class VideoSearchQuery(BaseModel):
    query: str
    max_results: Optional[int] = 10

class VideoSearchResult(BaseModel):
    video_id: str
    title: str
    description: str
    channel_title: str

class VideoDetails(BaseModel):
    video_id: str
    title: str
    description: str
    tags: List[str]
    view_count: str
    like_count: str
    comment_count: str

class ChannelInfo(BaseModel):
    channel_id: str
    title: str
    description: str
    subscriber_count: str
    video_count: str

class VideoMetrics(BaseModel):
    total_videos: int
    total_views: str
    total_likes: str
    engagement_rate: float
    videos: List[Dict[str, Any]]

class VideoUploadData(BaseModel):
    video_path: str
    title: str
    description: str = ""
    tags: List[str] = []
    privacy_status: str = "private"
    is_shorts: bool = True

@router.post("/search", response_model=List[VideoSearchResult])
async def search_youtube_videos(search_query: VideoSearchQuery):
    """
    Search for videos on YouTube.
    """
    try:
        results = search_videos(
            query=search_query.query,
            max_results=search_query.max_results
        )
        return results
    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching videos: {str(e)}")

@router.get("/videos/{video_id}", response_model=VideoDetails)
async def get_youtube_video_details(video_id: str):
    """
    Get details for a specific YouTube video.
    """
    try:
        video = get_video_details(video_id)
        if not video:
            raise HTTPException(status_code=404, detail=f"Video with ID {video_id} not found")
        return video
    except Exception as e:
        logger.error(f"Error getting video details: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting video details: {str(e)}")

@router.get("/channels/{channel_id}", response_model=ChannelInfo)
async def get_youtube_channel_info(channel_id: str):
    """
    Get information about a YouTube channel.
    """
    try:
        channel = get_channel_info(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail=f"Channel with ID {channel_id} not found")
        return channel
    except Exception as e:
        logger.error(f"Error getting channel info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting channel info: {str(e)}")

@router.get("/trending", response_model=List[VideoSearchResult])
async def get_trending_videos():
    """
    Get trending videos on YouTube.
    """
    try:
        # This is a simplified implementation - in reality, you'd want to use a 
        # different API endpoint for trending videos
        results = search_videos(
            query="",
            max_results=10
        )
        return results
    except Exception as e:
        logger.error(f"Error getting trending videos: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting trending videos: {str(e)}")

@router.get("/metrics", response_model=VideoMetrics)
async def get_youtube_metrics():
    """
    Get metrics for all user YouTube videos.
    """
    try:
        metrics = get_video_metrics()
        if not metrics:
            # Return mock data since we don't have the database function
            return {
                "total_videos": 0,
                "total_views": "0",
                "total_likes": "0",
                "engagement_rate": 0.0,
                "videos": []
            }
            
        return metrics
    except Exception as e:
        logger.error(f"Error getting YouTube metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting YouTube metrics: {str(e)}")

@router.post("/upload", response_model=Dict[str, Any])
async def upload_to_youtube(upload_data: VideoUploadData):
    """
    Upload a video to YouTube.
    """
    try:
        # Get credentials
        credentials = get_credentials()
        
        # Copy the file to a temporary location if needed
        video_path = upload_data.video_path
        temp_file = None
        
        # Verify the file exists
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video file not found: {video_path}")
        
        try:
            # Add Shorts-specific metadata if this is a Shorts video
            tags = upload_data.tags.copy()
            
            if upload_data.is_shorts and "#Shorts" not in tags:
                tags.append("#Shorts")
            
            # Upload to YouTube
            youtube_id = youtube_uploader(
                credentials=credentials,
                video_path=video_path,
                title=upload_data.title,
                description=upload_data.description,
                tags=tags,
                privacy_status=upload_data.privacy_status
            )
            
            if not youtube_id:
                raise HTTPException(status_code=500, detail="Failed to upload video to YouTube")
            
            # Return the YouTube video ID
            return {
                "youtube_id": youtube_id,
                "title": upload_data.title,
                "success": True
            }
        finally:
            # Clean up temporary file if it exists
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    except Exception as e:
        logger.error(f"Error uploading video to YouTube: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading video to YouTube: {str(e)}") 