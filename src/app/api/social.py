"""
API endpoints for cross-platform social media publishing.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import json
import time
from datetime import datetime

from src.app.services.social.cross_platform import get_cross_platform_publisher, Platform
from src.app.api.auth import get_credentials
from src.app.services.subscription import get_subscription_service

# Create router
router = APIRouter(
    prefix="/social",
    tags=["social"],
    responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)

# Models
class PlatformAuth(BaseModel):
    platform: str
    status: str
    connected: bool
    expires_at: Optional[str] = None
    username: Optional[str] = None

class PlatformSettings(BaseModel):
    platform: str
    enabled: bool
    customize_content: bool = False
    video_format: Optional[str] = None
    aspect_ratio: Optional[str] = None
    max_duration: Optional[int] = None
    description_template: Optional[str] = None

# Mock data for development
MOCK_PLATFORM_AUTH = {
    "youtube": PlatformAuth(
        platform="youtube",
        status="connected",
        connected=True,
        expires_at="2023-12-31T23:59:59Z",
        username="YourYouTubeChannel"
    ),
    "tiktok": PlatformAuth(
        platform="tiktok",
        status="not_connected",
        connected=False
    ),
    "instagram": PlatformAuth(
        platform="instagram",
        status="not_connected",
        connected=False
    ),
    "facebook": PlatformAuth(
        platform="facebook",
        status="not_connected",
        connected=False
    )
}

PLATFORM_FORMATS = {
    "youtube": {
        "formats": ["mp4", "mov"],
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "max_duration": 60 * 60  # 1 hour
    },
    "tiktok": {
        "formats": ["mp4"],
        "aspect_ratios": ["9:16"],
        "max_duration": 180  # 3 minutes
    },
    "instagram": {
        "formats": ["mp4"],
        "aspect_ratios": ["9:16", "1:1", "4:5"],
        "max_duration": 90  # 90 seconds for reels
    },
    "facebook": {
        "formats": ["mp4", "mov"],
        "aspect_ratios": ["16:9", "9:16", "1:1", "4:5"],
        "max_duration": 240  # 4 minutes
    }
}

# API Endpoints
@router.get("/platforms", response_class=JSONResponse)
async def get_platforms(
    request: Request,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Get all available social media platforms for publishing.
    
    Returns:
        JSONResponse: List of platforms and their publishing specifications
    """
    return {"platforms": PLATFORM_FORMATS}

@router.get("/auth-status", response_class=JSONResponse)
async def get_auth_status():
    """
    Get authentication status for all platforms.
    
    Returns:
        JSONResponse: Authentication status for each platform
    """
    return {"auth_status": list(MOCK_PLATFORM_AUTH.values())}

@router.post("/auth/{platform}", response_class=JSONResponse)
async def authenticate_platform(platform: str):
    """
    Initiate authentication flow for a platform.
    
    Args:
        platform: Name of the platform (youtube, tiktok, instagram, facebook)
        
    Returns:
        JSONResponse: Authentication URL and instructions
    """
    if platform not in ["youtube", "tiktok", "instagram", "facebook"]:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    # In a real implementation, generate OAuth URL or auth instructions
    auth_urls = {
        "youtube": "https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=youtube.upload&response_type=code",
        "tiktok": "https://www.tiktok.com/auth/authorize/",
        "instagram": "https://api.instagram.com/oauth/authorize",
        "facebook": "https://www.facebook.com/v18.0/dialog/oauth"
    }
    
    return {
        "platform": platform,
        "auth_url": auth_urls[platform],
        "instructions": f"Click the link to authenticate with {platform.capitalize()}. You will be redirected back after authentication."
    }

@router.post("/auth/{platform}/callback", response_class=JSONResponse)
async def auth_callback(platform: str, code: str):
    """
    Handle authentication callback from a platform.
    
    Args:
        platform: Platform name
        code: Authorization code from OAuth flow
        
    Returns:
        JSONResponse: Authentication result
    """
    # In a real implementation, exchange code for tokens
    # For now, just simulate success
    
    # Update mock auth status
    MOCK_PLATFORM_AUTH[platform] = PlatformAuth(
        platform=platform,
        status="connected",
        connected=True,
        expires_at="2023-12-31T23:59:59Z",
        username=f"Your{platform.capitalize()}Account"
    )
    
    return {
        "status": "success",
        "platform": platform,
        "message": f"Successfully authenticated with {platform.capitalize()}"
    }

@router.post("/settings", response_class=JSONResponse)
async def save_platform_settings(settings: List[PlatformSettings]):
    """
    Save publishing settings for platforms.
    
    Args:
        settings: List of platform settings
        
    Returns:
        JSONResponse: Result of the operation
    """
    # In a real implementation, save to database
    # For now, just validate and return success
    
    invalid_platforms = [s.platform for s in settings if s.platform not in PLATFORM_FORMATS]
    if invalid_platforms:
        raise HTTPException(status_code=400, detail=f"Unsupported platforms: {', '.join(invalid_platforms)}")
    
    return {
        "status": "success",
        "message": "Platform settings saved successfully",
        "settings": settings
    }

@router.post("/publish", response_class=JSONResponse)
async def publish_to_platforms(
    video_id: str = Form(...),
    platforms: List[str] = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    video_file: UploadFile = File(None)
):
    """
    Publish a video to multiple platforms.
    
    Args:
        video_id: ID of the video to publish
        platforms: List of platforms to publish to
        title: Video title
        description: Video description
        video_file: Optional video file if not using an existing video
        
    Returns:
        JSONResponse: Publishing job status
    """
    # Check if platforms are valid and authenticated
    invalid_platforms = [p for p in platforms if p not in PLATFORM_FORMATS]
    if invalid_platforms:
        raise HTTPException(status_code=400, detail=f"Unsupported platforms: {', '.join(invalid_platforms)}")
    
    unauthenticated = [p for p in platforms if not MOCK_PLATFORM_AUTH.get(p, PlatformAuth(platform=p, status="unknown", connected=False)).connected]
    if unauthenticated:
        raise HTTPException(status_code=401, detail=f"Not authenticated with: {', '.join(unauthenticated)}")
    
    # Create publishing job
    job_id = str(uuid.uuid4())
    
    # In a real implementation, start background task for publishing
    
    return {
        "status": "submitted",
        "job_id": job_id,
        "platforms": platforms,
        "message": f"Publishing job submitted for {len(platforms)} platforms",
        "estimated_completion": "10-15 minutes"
    }

@router.get("/publish/{job_id}", response_class=JSONResponse)
async def get_publishing_status(job_id: str):
    """
    Get status of a publishing job.
    
    Args:
        job_id: Publishing job ID
        
    Returns:
        JSONResponse: Job status
    """
    # In a real implementation, fetch from database
    # For now, return mock data
    
    import random
    platforms = ["youtube", "tiktok", "instagram", "facebook"]
    statuses = ["completed", "in_progress", "queued", "failed"]
    weights = [0.7, 0.2, 0.05, 0.05]  # Mostly completed for demo
    
    results = {}
    for platform in random.sample(platforms, random.randint(1, len(platforms))):
        status = random.choices(statuses, weights=weights)[0]
        results[platform] = {
            "status": status,
            "platform_url": f"https://{platform}.com/video/mock-id" if status == "completed" else None,
            "error": "API Error" if status == "failed" else None
        }
    
    return {
        "job_id": job_id,
        "status": "completed" if all(r["status"] == "completed" for r in results.values()) else "in_progress",
        "results": results
    } 