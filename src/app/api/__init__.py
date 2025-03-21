"""
API Package for YouTube Shorts Machine.

This package contains all FastAPI routes for the application.
"""

import os
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any, List

from src.app.core.settings import API_TITLE, API_DESCRIPTION, API_VERSION, DEBUG_MODE, CORS_ORIGINS
from src.app.api.metadata import router as metadata_router
from src.app.api.videos import router as videos_router
from src.app.api.thumbnails import router as thumbnails_router
from src.app.api.auth import router as auth_router
from src.app.api.export import router as export_router
from src.app.api.social import router as social_router
from src.app.api.youtube import router as youtube_router
from src.app.api.analytics import router as analytics_router
from src.app.api.trends import router as trends_router
from src.app.api.predictions import router as predictions_router
from src.app.api.branding import router as branding_router
from src.app.api.worker_status import router as worker_status_router
from src.app.api.dashboard import router as dashboard_router
from src.app.api.music_metadata_api import router as music_metadata_router
from src.app.api.music_recommendations import router as music_recommendations_router
from src.app.api.music_responsive import router as music_responsive_router
from src.app.api.scheduler import router as scheduler_router
from src.app.api.subscription import router as subscription_router
from src.app.api.licensing import router as licensing_router
from src.app.api.affiliate import router as affiliate_router
from src.app.api.openai_metadata import router as openai_metadata_router

import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    debug=DEBUG_MODE,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Custom OpenAPI schema with more metadata
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION + """
        
## Features

### Standard Features
- AI-powered video creation with music sync
- Google Cloud Storage integration
- YouTube API upload
- Task queue for asynchronous processing

### Advanced Features
- **Thumbnail Optimization with A/B Testing**: Create, test, and optimize thumbnails
- **Cross-Platform Publishing**: Distribute videos to TikTok, Instagram, and Facebook
- **Content Scheduling**: Schedule and batch process videos for optimal engagement
- **Intelligent Music Recommendations**: Get AI-powered music suggestions based on video content
        """,
        routes=app.routes,
    )
    
    # Add additional metadata
    openapi_schema["info"]["contact"] = {
        "name": "YouTube Shorts Machine Support",
        "email": "support@youtube-shorts-machine.com",
        "url": "https://github.com/yourusername/youtube-shorts-machine"
    }
    
    # Add tag descriptions
    openapi_schema["tags"] = [
        {
            "name": "thumbnails",
            "description": "Operations for thumbnail optimization and A/B testing"
        },
        {
            "name": "social",
            "description": "Operations for cross-platform social media publishing"
        },
        {
            "name": "scheduler",
            "description": "Operations for content scheduling and batch processing"
        },
        {
            "name": "youtube",
            "description": "Operations for YouTube API integration"
        },
        {
            "name": "music-recommendations",
            "description": "Operations for intelligent music recommendations based on video content"
        },
        {
            "name": "subscription",
            "description": "Operations for managing subscription plans and user subscriptions"
        },
        {
            "name": "affiliate",
            "description": "Operations for affiliate program management"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
    
app.openapi = custom_openapi

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(videos_router, prefix="/videos", tags=["videos"])
app.include_router(thumbnails_router, prefix="/thumbnails", tags=["thumbnails"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(export_router, prefix="/export", tags=["export"])
app.include_router(social_router, prefix="/social", tags=["social"])
app.include_router(youtube_router, prefix="/youtube", tags=["youtube"])
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(trends_router, prefix="/trends", tags=["trends"])
app.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
app.include_router(branding_router, prefix="/branding", tags=["branding"])
app.include_router(worker_status_router, prefix="/worker-status", tags=["worker-status"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(music_metadata_router, prefix="/music", tags=["music"])
app.include_router(music_recommendations_router, prefix="/music-recommendations", tags=["music-recommendations"])
app.include_router(music_responsive_router, prefix="/music-responsive", tags=["music-responsive"])
app.include_router(scheduler_router, prefix="/scheduler", tags=["scheduler"])
app.include_router(subscription_router, prefix="/subscription", tags=["subscription"])
app.include_router(metadata_router, prefix="/metadata", tags=["metadata"])
app.include_router(licensing_router, prefix="/licensing", tags=["licensing"])
app.include_router(affiliate_router, prefix="/affiliate", tags=["affiliate"])
app.include_router(openai_metadata_router, prefix="/openai-metadata", tags=["openai-metadata"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "description": API_DESCRIPTION,
        "docs_url": "/api/docs"
    }

@app.get("/auth/authorize")
async def authorize_direct():
    """Direct authorize endpoint that forwards to the auth router."""
    from src.app.api.auth import authorize
    return await authorize() 