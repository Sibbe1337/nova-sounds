"""
API endpoints for multi-platform video export.
"""
from fastapi import APIRouter, HTTPException, Depends, Body, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import uuid
import os
import tempfile
from datetime import datetime

from src.app.api.auth import get_credentials
from src.app.core.settings import DEV_MODE
from src.app.core.database import get_video, update_video
from src.app.services.youtube.api import upload_to_youtube as youtube_uploader
from src.app.services.video.platform_formatter import optimize_video_for_platform
from src.app.services.social.tiktok import TikTokPublisher
from src.app.services.social.instagram import InstagramAPI
from src.app.services.social.facebook import FacebookAPI

# Set up logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/export", tags=["export"])

# Pydantic models for request/response
class ExportPlatform(BaseModel):
    """Platform to export video to"""
    platform_name: str
    platform_settings: Dict[str, Any] = {}

class ExportRequest(BaseModel):
    """Request model for exporting a video to multiple platforms"""
    video_id: str
    platforms: List[ExportPlatform]
    metadata: Optional[Dict[str, Any]] = None

class ExportResponse(BaseModel):
    """Response model for export operations"""
    job_id: str
    video_id: str
    platforms: List[str]
    status: str
    started_at: datetime

class ExportResult(BaseModel):
    """Result of an export operation"""
    job_id: str
    video_id: str
    platforms: Dict[str, Any]
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None

@router.get("/platforms", response_model=Dict[str, Any])
async def get_export_platforms():
    """
    Get available export platforms and their requirements.
    
    Returns:
        Dict[str, Any]: Dictionary of platform information
    """
    # This would typically come from a database or configuration file
    # For now, we'll hard-code the available platforms
    from src.app.core.settings import DEV_MODE
    
    platforms = {
        "youtube": {
            "name": "YouTube Shorts",
            "enabled": True,
            "max_duration": 60,
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "formats": ["mp4"],
            "max_size_mb": 100,
            "additional_fields": {
                "title": {"type": "string", "required": True, "max_length": 100},
                "description": {"type": "string", "required": False, "max_length": 5000},
                "tags": {"type": "array", "required": False, "max_items": 500},
                "privacy_status": {"type": "string", "required": False, "options": ["public", "private", "unlisted"]}
            }
        },
        "tiktok": {
            "name": "TikTok",
            "enabled": DEV_MODE,  # Only enabled in development mode
            "max_duration": 60,
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "formats": ["mp4"],
            "max_size_mb": 50,
            "additional_fields": {
                "caption": {"type": "string", "required": True, "max_length": 2200},
                "hashtags": {"type": "array", "required": False, "max_items": 30}
            }
        },
        "instagram": {
            "name": "Instagram Reels",
            "enabled": DEV_MODE,  # Only enabled in development mode
            "max_duration": 90,
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "formats": ["mp4"],
            "max_size_mb": 50,
            "additional_fields": {
                "caption": {"type": "string", "required": True, "max_length": 2200},
                "hashtags": {"type": "array", "required": False, "max_items": 30}
            }
        }
    }
    
    return platforms

@router.post("/", response_model=ExportResponse)
async def export_to_platforms(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Export a video to multiple platforms (YouTube, TikTok, Instagram, Facebook, etc.)
    
    Args:
        request: Export request containing video ID and target platforms
        background_tasks: FastAPI BackgroundTasks for async operations
        credentials: User credentials
        
    Returns:
        ExportResponse: Response with job details
    """
    try:
        video_id = request.video_id
        platforms = [p.platform_name for p in request.platforms]
        
        logger.info(f"Exporting video {video_id} to platforms: {platforms}")
        
        # Check if video exists
        video = get_video(video_id)
        if not video:
            logger.warning(f"Video not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check if video is ready for export
        if video.get("status") not in ["ready_for_upload", "uploaded"]:
            logger.warning(f"Video not ready for export: {video_id}, status: {video.get('status')}")
            raise HTTPException(status_code=400, detail="Video is not ready for export")
        
        # Create export job ID
        job_id = f"export-{uuid.uuid4().hex[:8]}"
        
        # Store metadata about the export job
        now = datetime.now()
        export_data = {
            "export_jobs": video.get("export_jobs", {})
        }
        
        export_data["export_jobs"][job_id] = {
            "job_id": job_id,
            "platforms": platforms,
            "status": "processing",
            "started_at": now,
            "platform_results": {}
        }
        
        # Update video record with export job
        update_video(video_id, export_data)
        
        # Schedule background task for export
        def process_export():
            try:
                logger.info(f"Processing export job {job_id} for video {video_id}")
                results = {}
                
                # Get video URL from record
                video_url = video.get("video_url")
                if not video_url:
                    raise ValueError("Video URL not found in record")
                
                # Process each platform
                for platform_info in request.platforms:
                    platform = platform_info.platform_name
                    settings = platform_info.platform_settings
                    
                    try:
                        # Export to platform (implementation depends on platform)
                        if platform.lower() == "youtube":
                            # Optimize video for YouTube
                            with tempfile.TemporaryDirectory() as temp_dir:
                                # Download video if it's a URL (in this example, we'll assume it's a local path)
                                optimized_video_path = None
                                try:
                                    # Optimize for YouTube
                                    optimized_video_path = optimize_video_for_platform(
                                        video_path=video_url, 
                                        platform="youtube",
                                        output_path=os.path.join(temp_dir, f"{video_id}_youtube.mp4")
                                    )
                                    
                                    # Use YouTube uploader with optimized video
                                    title = settings.get("title", f"Video - {video.get('music_track')}")
                                    description = settings.get("description", f"Created with AI using {video.get('music_track')}")
                                    tags = settings.get("tags", ["shorts", "ai generated", "music"])
                                    privacy = settings.get("privacy_status", "unlisted")
                                    
                                    youtube_id = youtube_uploader(
                                        credentials,
                                        video_path=optimized_video_path,
                                        title=title,
                                        description=description,
                                        tags=tags,
                                        privacy_status=privacy
                                    )
                                    
                                    if youtube_id:
                                        results[platform] = {
                                            "status": "success",
                                            "platform_id": youtube_id,
                                            "url": f"https://www.youtube.com/watch?v={youtube_id}"
                                        }
                                    else:
                                        results[platform] = {
                                            "status": "failure",
                                            "error": "Failed to upload to YouTube"
                                        }
                                except Exception as e:
                                    logger.error(f"Error optimizing/uploading video for YouTube: {e}")
                                    results[platform] = {
                                        "status": "failure",
                                        "error": str(e)
                                    }
                        
                        elif platform.lower() == "tiktok":
                            # Optimize video for TikTok
                            if DEV_MODE:
                                # In development mode, just return a mock success
                                results[platform] = {
                                    "status": "success",
                                    "platform_id": f"tiktok-{uuid.uuid4().hex[:8]}",
                                    "url": f"https://www.tiktok.com/@user/video/mock-id"
                                }
                            else:
                                with tempfile.TemporaryDirectory() as temp_dir:
                                    try:
                                        # Optimize for TikTok
                                        optimized_video_path = optimize_video_for_platform(
                                            video_path=video_url, 
                                            platform="tiktok",
                                            output_path=os.path.join(temp_dir, f"{video_id}_tiktok.mp4")
                                        )
                                        
                                        # Use the TikTok publisher to upload the video
                                        tiktok_publisher = TikTokPublisher()
                                        
                                        # Check if authenticated
                                        if not tiktok_publisher.access_token:
                                            # Try to load token
                                            tiktok_publisher._load_tokens()
                                        
                                        if not tiktok_publisher.access_token:
                                            results[platform] = {
                                                "status": "failure",
                                                "error": "Not authenticated with TikTok. Please authenticate first.",
                                                "video_optimized": True,
                                                "optimization_path": optimized_video_path
                                            }
                                        else:
                                            # Prepare video data for TikTok
                                            tiktok_data = {
                                                "video_path": optimized_video_path,
                                                "description": request.metadata.get("description", ""),
                                                "hashtags": request.metadata.get("hashtags", [])
                                            }
                                            
                                            # Publish to TikTok
                                            tiktok_result = tiktok_publisher.publish_video(tiktok_data)
                                            
                                            if tiktok_result.get("success"):
                                                results[platform] = {
                                                    "status": "success",
                                                    "platform_id": tiktok_result.get("video_id"),
                                                    "url": tiktok_result.get("url"),
                                                    "video_optimized": True,
                                                    "optimization_path": optimized_video_path
                                                }
                                            else:
                                                results[platform] = {
                                                    "status": "failure",
                                                    "error": tiktok_result.get("error", "Unknown error uploading to TikTok"),
                                                    "video_optimized": True,
                                                    "optimization_path": optimized_video_path
                                                }
                                    except Exception as e:
                                        logger.error(f"Error publishing video to TikTok: {e}")
                                        results[platform] = {
                                            "status": "failure",
                                            "error": f"Error publishing to TikTok: {str(e)}",
                                            "video_optimized": False
                                        }
                        
                        elif platform.lower() == "instagram":
                            # Optimize video for Instagram
                            if DEV_MODE:
                                # In development mode, just return a mock success
                                results[platform] = {
                                    "status": "success",
                                    "platform_id": f"ig-{uuid.uuid4().hex[:8]}",
                                    "url": f"https://www.instagram.com/reel/mock-id/"
                                }
                            else:
                                with tempfile.TemporaryDirectory() as temp_dir:
                                    try:
                                        # Optimize for Instagram
                                        optimized_video_path = optimize_video_for_platform(
                                            video_path=video_url, 
                                            platform="instagram",
                                            output_path=os.path.join(temp_dir, f"{video_id}_instagram.mp4")
                                        )
                                        
                                        # Use the Instagram publisher to upload the video
                                        instagram_publisher = InstagramAPI()
                                        
                                        # Check if authenticated
                                        if not instagram_publisher.access_token:
                                            # Try to load token
                                            instagram_publisher._load_tokens()
                                        
                                        if not instagram_publisher.access_token:
                                            results[platform] = {
                                                "status": "failure",
                                                "error": "Not authenticated with Instagram. Please authenticate first.",
                                                "video_optimized": True,
                                                "optimization_path": optimized_video_path
                                            }
                                        else:
                                            # Prepare video data for Instagram
                                            caption = request.metadata.get("description", "")
                                            hashtags = request.metadata.get("hashtags", [])
                                            
                                            # Publish to Instagram
                                            instagram_result = instagram_publisher.upload_reels(
                                                video_path=optimized_video_path,
                                                caption=caption,
                                                hashtags=hashtags
                                            )
                                            
                                            if instagram_result.get("success"):
                                                results[platform] = {
                                                    "status": "success",
                                                    "platform_id": instagram_result.get("media_id"),
                                                    "url": instagram_result.get("permalink"),
                                                    "video_optimized": True,
                                                    "optimization_path": optimized_video_path
                                                }
                                            else:
                                                results[platform] = {
                                                    "status": "failure",
                                                    "error": instagram_result.get("error", "Unknown error uploading to Instagram"),
                                                    "video_optimized": True,
                                                    "optimization_path": optimized_video_path
                                                }
                                    except Exception as e:
                                        logger.error(f"Error publishing video to Instagram: {e}")
                                        results[platform] = {
                                            "status": "failure",
                                            "error": f"Error publishing to Instagram: {str(e)}",
                                            "video_optimized": False
                                        }
                        
                        elif platform.lower() == "facebook":
                            # Optimize video for Facebook
                            if DEV_MODE:
                                # In development mode, just return a mock success
                                results[platform] = {
                                    "status": "success",
                                    "platform_id": f"fb-{uuid.uuid4().hex[:8]}",
                                    "url": f"https://www.facebook.com/watch/?v=mock-id"
                                }
                            else:
                                with tempfile.TemporaryDirectory() as temp_dir:
                                    try:
                                        # Optimize for Facebook
                                        optimized_video_path = optimize_video_for_platform(
                                            video_path=video_url, 
                                            platform="facebook",
                                            output_path=os.path.join(temp_dir, f"{video_id}_facebook.mp4")
                                        )
                                        
                                        # Use the Facebook publisher to upload the video
                                        facebook_publisher = FacebookAPI()
                                        
                                        # Check if authenticated
                                        if not facebook_publisher.access_token:
                                            # Try to load token
                                            facebook_publisher._load_tokens()
                                        
                                        if not facebook_publisher.access_token:
                                            results[platform] = {
                                                "status": "failure",
                                                "error": "Not authenticated with Facebook. Please authenticate first.",
                                                "video_optimized": True,
                                                "optimization_path": optimized_video_path
                                            }
                                        else:
                                            # Prepare video data for Facebook
                                            title = request.metadata.get("title", "")
                                            description = request.metadata.get("description", "")
                                            
                                            # Publish to Facebook
                                            facebook_result = facebook_publisher.upload_video(
                                                video_path=optimized_video_path,
                                                title=title,
                                                description=description
                                            )
                                            
                                            if facebook_result.get("success"):
                                                results[platform] = {
                                                    "status": "success",
                                                    "platform_id": facebook_result.get("video_id"),
                                                    "url": facebook_result.get("url"),
                                                    "video_optimized": True,
                                                    "optimization_path": optimized_video_path
                                                }
                                            else:
                                                results[platform] = {
                                                    "status": "failure",
                                                    "error": facebook_result.get("error", "Unknown error uploading to Facebook"),
                                                    "video_optimized": True,
                                                    "optimization_path": optimized_video_path
                                                }
                                    except Exception as e:
                                        logger.error(f"Error publishing video to Facebook: {e}")
                                        results[platform] = {
                                            "status": "failure",
                                            "error": f"Error publishing to Facebook: {str(e)}",
                                            "video_optimized": False
                                        }
                        else:
                            results[platform] = {
                                "status": "failure",
                                "error": f"Unsupported platform: {platform}"
                            }
                    
                    except Exception as e:
                        logger.error(f"Error exporting to {platform}: {e}")
                        results[platform] = {
                            "status": "failure",
                            "error": str(e)
                        }
                
                # Update video record with results
                completed_at = datetime.now()
                success_count = sum(1 for p in results.values() if p.get("status") == "success")
                status = "completed" if success_count > 0 else "failed"
                
                export_job_data = {
                    "export_jobs": {}
                }
                export_job_data["export_jobs"][job_id] = {
                    "job_id": job_id,
                    "platforms": platforms,
                    "status": status,
                    "started_at": now,
                    "completed_at": completed_at,
                    "platform_results": results
                }
                
                update_video(video_id, export_job_data)
                logger.info(f"Export job {job_id} completed with status {status}")
            
            except Exception as e:
                logger.error(f"Error processing export job {job_id}: {e}")
                # Update job status
                failed_job_data = {
                    "export_jobs": {}
                }
                failed_job_data["export_jobs"][job_id] = {
                    "job_id": job_id,
                    "platforms": platforms,
                    "status": "failed",
                    "started_at": now,
                    "completed_at": datetime.now(),
                    "error": str(e)
                }
                update_video(video_id, failed_job_data)
        
        # Add the task to background tasks
        background_tasks.add_task(process_export)
        
        # Return response
        return ExportResponse(
            job_id=job_id,
            video_id=video_id,
            platforms=platforms,
            status="processing",
            started_at=now
        )
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error exporting video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=ExportResult)
async def get_export_status(job_id: str):
    """
    Get the status of a video export job.
    
    Args:
        job_id: ID of the export job
        
    Returns:
        ExportResult: Export job details and results
    """
    try:
        logger.info(f"Getting status for export job: {job_id}")
        
        # Find the video containing this export job
        # In a real implementation, you'd have a more efficient way to look up export jobs
        from src.app.core.database import list_videos
        
        videos = list_videos(limit=100)
        job_data = None
        video_id = None
        
        for video in videos:
            export_jobs = video.get("export_jobs", {})
            if job_id in export_jobs:
                job_data = export_jobs[job_id]
                video_id = video.get("id")
                break
        
        if not job_data:
            logger.warning(f"Export job not found: {job_id}")
            raise HTTPException(status_code=404, detail="Export job not found")
        
        # Return job status and details
        return ExportResult(
            job_id=job_id,
            video_id=video_id,
            platforms=job_data.get("platform_results", {}),
            status=job_data.get("status", "unknown"),
            started_at=job_data.get("started_at"),
            completed_at=job_data.get("completed_at")
        )
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error getting export status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video/{video_id}", response_model=List[ExportResult])
async def get_video_exports(video_id: str):
    """
    Get all export jobs for a specific video.
    
    Args:
        video_id: ID of the video
        
    Returns:
        List[ExportResult]: List of export jobs for the video
    """
    try:
        logger.info(f"Getting export jobs for video: {video_id}")
        
        # Get video data
        video = get_video(video_id)
        if not video:
            logger.warning(f"Video not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get export jobs for the video
        export_jobs = video.get("export_jobs", {})
        
        # Convert to list of ExportResult
        results = []
        for job_id, job_data in export_jobs.items():
            results.append(
                ExportResult(
                    job_id=job_id,
                    video_id=video_id,
                    platforms=job_data.get("platform_results", {}),
                    status=job_data.get("status", "unknown"),
                    started_at=job_data.get("started_at"),
                    completed_at=job_data.get("completed_at")
                )
            )
        
        return results
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error getting video exports: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 