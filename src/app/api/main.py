"""
Main API entry point for YouTube Shorts Machine.
"""
import os
import logging
import uuid
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import Depends, HTTPException, Request, UploadFile, File, Form, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import asyncio
import time
import httpx
from contextlib import asynccontextmanager

from src.app.core.settings import DEV_MODE, DEBUG_MODE, API_HOST, API_PORT
from src.app.services.gcs.storage import list_music_tracks, get_image_for_track
from src.app.api.auth import router as auth_router, get_credentials
from src.app.api.endpoints.export import router as export_router
from src.app.api.music_responsive import router as music_responsive_router
from src.app.api.worker_status import router as worker_status_router
from src.app.api.affiliate import router as affiliate_router
from src.app.services.ai.metadata_generator import generate_optimized_metadata
from src.app.services.video.enhanced_processor import create_enhanced_short, VideoStyle, suggest_enhancements
from src.app.services.video.music_responsive import create_music_responsive_video, MusicFeature

# Import the app from __init__.py
from src.app.api import app

# Import the routers
from .dashboard import router as dashboard_router
from .thumbnails import router as thumbnails_router
from .scheduler import router as scheduler_router
from .branding import router as branding_router
from .licensing import router as licensing_router

# Configure logging
level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a connection pool for HTTP requests
# This will be used to limit and reuse connections across the application
class ConnectionPoolManager:
    def __init__(self, max_connections: int = 100):
        self.semaphore = asyncio.Semaphore(max_connections)
        self._client = None
        
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30
                )
            )
        return self._client
        
    @asynccontextmanager
    async def connection(self):
        async with self.semaphore:
            client = await self.get_client()
            try:
                yield client
            except Exception as e:
                logger.error(f"Error with HTTP connection: {e}")
                raise

# Create global connection pool
connection_pool = ConnectionPoolManager()

# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_minute = int(time.time() / 60)
        
        # Get or initialize request count for this client
        request_key = f"{client_ip}:{current_minute}"
        if request_key not in self.request_counts:
            self.request_counts[request_key] = 0
            
            # Cleanup old keys
            self.request_counts = {
                k: v for k, v in self.request_counts.items() 
                if k.split(":")[-1] == str(current_minute)
            }
            
        # Check rate limit
        if self.request_counts[request_key] >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )
            
        # Increment request count
        self.request_counts[request_key] += 1
        
        # Start timer for this request
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Log request timing for slow requests
        process_time = time.time() - start_time
        if process_time > 1.0:  # Log requests taking more than 1 second
            route = request.url.path
            logger.warning(f"Slow request: {route} took {process_time:.2f}s")
            
        return response

# Request timing middleware for performance monitoring
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add processing time header to response
        response.headers["X-Process-Time"] = str(process_time)
        
        # Track performance metrics for monitoring
        app.state.request_count = getattr(app.state, "request_count", 0) + 1
        app.state.total_time = getattr(app.state, "total_time", 0) + process_time
        
        return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware (only in production)
if not DEV_MODE and not DEBUG_MODE:
    app.add_middleware(RateLimitMiddleware, requests_per_minute=180)

# Add timing middleware for performance monitoring
app.add_middleware(TimingMiddleware)

# Cache for expensive operations 
# This simple in-memory cache will reduce load on external services
cache = {}
cache_ttl = {}

async def get_cached(key: str, ttl: int = 300):
    """Get a value from cache or return None if expired/not found."""
    if key in cache and key in cache_ttl:
        if cache_ttl[key] > time.time():
            return cache[key]
        else:
            # Expired
            del cache[key]
            del cache_ttl[key]
    return None

async def set_cached(key: str, value: Any, ttl: int = 300):
    """Set a value in cache with expiration."""
    cache[key] = value
    cache_ttl[key] = time.time() + ttl

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    # Get some basic metrics
    uptime = getattr(app.state, "startup_time", None)
    request_count = getattr(app.state, "request_count", 0)
    avg_response_time = 0
    if request_count > 0:
        avg_response_time = getattr(app.state, "total_time", 0) / request_count
        
    return {
        "status": "healthy",
        "version": os.environ.get("APP_VERSION", "dev"),
        "uptime": uptime,
        "requests_processed": request_count,
        "avg_response_time": round(avg_response_time, 4) if avg_response_time else None
    }

# Add startup event to record startup time
@app.on_event("startup")
async def startup_event():
    """Record startup time and prepare app state."""
    app.state.startup_time = datetime.now().isoformat()
    app.state.request_count = 0
    app.state.total_time = 0
    logger.info(f"API server started at {app.state.startup_time}")
    
# Add shutdown event to clean up resources
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("API server shutting down")
    # Close any open connections
    if hasattr(connection_pool, '_client') and connection_pool._client is not None:
        await connection_pool._client.aclose()
    logger.info("Connections closed")
    
# Export the connection pool for use in other modules
def get_connection_pool():
    """Get the global connection pool."""
    return connection_pool

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting YouTube Shorts Machine API")
    logger.info(f"API running in {'development' if DEV_MODE else 'production'} mode")
    logger.info(f"Debug mode: {DEBUG_MODE}")
    logger.info(f"API host: {API_HOST}")
    logger.info(f"API port: {API_PORT}")
    
    # Start the worker status monitor
    try:
        from src.app.api.worker_status import monitor_celery_status
        import asyncio
        
        # Run the monitor as a background task
        asyncio.create_task(monitor_celery_status())
        logger.info("Worker status monitor started")
    except ImportError as e:
        logger.warning(f"Could not start worker status monitor: {e}")
    except Exception as e:
        logger.error(f"Error starting worker status monitor: {e}")
    
    # Load any configuration or initialize services here

@app.get("/", response_class=JSONResponse)
async def root():
    """
    API root endpoint.
    
    Returns:
        dict: API information
    """
    return {
        "name": "YouTube Shorts Machine API",
        "version": "0.1.0",
        "status": "running",
        "dev_mode": DEV_MODE,
        "debug_mode": DEBUG_MODE
    }

@app.get("/music", response_class=JSONResponse)
async def get_music(limit: int = 100, skip: int = 0, prefix: Optional[str] = None, include_images: bool = False):
    """
    Get available music tracks with pagination and filtering.
    
    Args:
        limit: Maximum number of tracks to return
        skip: Number of tracks to skip (for pagination)
        prefix: Optional prefix to filter tracks
        include_images: Whether to include matching image URLs
        
    Returns:
        dict: List of music tracks with pagination info
    """
    from src.app.services.gcs.storage import list_music_tracks, get_image_for_track
    
    # Get tracks with pagination support
    tracks = list_music_tracks(limit=limit, prefix=prefix)
    
    # Apply skip for pagination
    if skip > 0 and skip < len(tracks):
        tracks = tracks[skip:]
    
    # Ensure we don't exceed the limit
    if len(tracks) > limit:
        tracks = tracks[:limit]
    
    logger.info(f"Retrieved {len(tracks)} music tracks (limit={limit}, skip={skip}, prefix={prefix})")
    
    # Add image URLs if requested
    if include_images:
        track_data = []
        for track in tracks:
            image_url = get_image_for_track(track)
            track_data.append({
                "name": track,
                "image_url": image_url
            })
        return {
            "tracks": track_data,
            "count": len(track_data),
            "total": 100,  # Based on what we can see in the bucket
            "has_more": len(tracks) >= limit
        }
    
    return {
        "tracks": tracks,
        "count": len(tracks),
        "total": 100,  # Based on what we can see in the bucket
        "has_more": len(tracks) >= limit
    }

@app.get("/music/stats", response_class=JSONResponse)
async def get_music_stats():
    """
    Get statistics about music tracks in the bucket.
    
    Returns:
        dict: Statistics about the music tracks
    """
    if DEV_MODE:
        # Return mock stats in development mode
        return {
            "total_tracks": 5,
            "file_types": {"mp3": 5},
            "total_size_mb": 25.5,
            "bucket_name": "mock-bucket"
        }
    
    from google.cloud import storage
    from src.app.core.settings import GCS_BUCKET_NAME
    
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Get all blobs in the bucket
        blobs = list(bucket.list_blobs())
        
        # Filter for audio files
        audio_files = [blob for blob in blobs if blob.name.endswith(('.mp3', '.wav'))]
        image_files = [blob for blob in blobs if blob.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        # Count file types
        file_types = {}
        for blob in audio_files:
            ext = blob.name.split('.')[-1].lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Calculate total size
        total_size_bytes = sum(blob.size for blob in audio_files)
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        # Calculate average file size
        avg_size_mb = total_size_mb / len(audio_files) if audio_files else 0
        
        # Check for paired files (audio with matching image)
        audio_bases = {os.path.splitext(blob.name)[0] for blob in audio_files}
        image_bases = {os.path.splitext(blob.name)[0] for blob in image_files}
        paired_files = len(audio_bases.intersection(image_bases))
        
        return {
            "total_tracks": len(audio_files),
            "total_images": len(image_files),
            "paired_files": paired_files,
            "file_types": file_types,
            "total_size_mb": round(total_size_mb, 2),
            "avg_size_mb": round(avg_size_mb, 2),
            "bucket_name": GCS_BUCKET_NAME,
            "bucket_region": "us (multiple regions)"
        }
    except Exception as e:
        logger.error(f"Error getting music stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos", response_class=JSONResponse)
async def list_videos(status: Optional[str] = None, limit: int = 100, skip: int = 0):
    """
    List all videos, optionally filtered by status.
    
    Args:
        status: Optional status filter
        limit: Maximum number of videos to return
        skip: Number of videos to skip
        
    Returns:
        dict: List of videos
    """
    logger.info(f"Listing videos with status filter: {status}, limit: {limit}, skip: {skip}")
    
    from src.app.core.database import list_videos as db_list_videos
    
    # Get all videos from database
    all_videos = db_list_videos(limit=limit, skip=skip)
    
    # Apply status filter if provided
    if status:
        filtered_videos = [v for v in all_videos if v.get("status") == status]
        logger.debug(f"Filtered {len(filtered_videos)} videos with status '{status}' from {len(all_videos)} total")
        return {"videos": filtered_videos}
    
    return {"videos": all_videos}

@app.post("/videos", response_class=JSONResponse)
async def create_video(
    music_track: str = Form(...),
    images: List[UploadFile] = File(...),
    request: Request = None,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Create a new video from music and images.
    
    Args:
        music_track: Music track name
        images: List of image files
        request: Request object
        credentials: User credentials
        
    Returns:
        dict: Created video information
    """
    try:
        logger.info(f"Creating new video with music track: {music_track} and {len(images)} images")
        if DEBUG_MODE:
            logger.debug(f"Image files: {[img.filename for img in images]}")
        
        from src.app.core.database import create_video
        
        # Generate video ID
        video_id = str(uuid.uuid4())
        logger.info(f"Generated video ID: {video_id}")
        
        # Save uploaded images to temporary files
        temp_image_paths = []
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")
            
            for i, image in enumerate(images):
                img_content = await image.read()
                img_path = os.path.join(temp_dir, f"image_{i}_{image.filename}")
                
                with open(img_path, "wb") as f:
                    f.write(img_content)
                
                temp_image_paths.append(img_path)
                logger.debug(f"Saved image {i+1}/{len(images)}: {img_path}")
            
            # Create video record
            now = datetime.now()
            video_data = {
                "id": video_id,
                "music_track": music_track,
                "status": "pending",
                "created_at": now,
                "updated_at": now
            }
            
            create_video(video_id, video_data)
            logger.info(f"Created video record in database: {video_id}")
            
            # Process video asynchronously
            from src.app.tasks.video_tasks import process_video
            
            logger.info(f"Starting video processing for {video_id}")
            # Run synchronously for MVP
            result = process_video(video_id, temp_image_paths, music_track, credentials)
            
            if result.get("success"):
                logger.info(f"Video processing completed successfully: {video_id}")
            else:
                logger.warning(f"Video processing returned error: {result.get('error')}")
            
            return {
                "video_id": video_id,
                "status": "processing",
                "message": "Video creation started",
                "track": music_track,
                "images_count": len(images)
            }
    
    except Exception as e:
        logger.error(f"Error creating video: {e}", exc_info=DEBUG_MODE)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{video_id}", response_class=JSONResponse)
async def get_video(video_id: str):
    """
    Get video information by ID.
    
    Args:
        video_id: Video ID
        
    Returns:
        dict: Video information
    """
    try:
        logger.info(f"Getting video: {video_id}")
        from src.app.core.database import get_video
        
        video = get_video(video_id)
        if not video:
            logger.warning(f"Video not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check if video has export jobs
        export_jobs = video.get("export_jobs", {})
        
        # Add export status summary if jobs exist
        if export_jobs:
            export_summary = {
                "total_exports": len(export_jobs),
                "platforms": {},
                "latest_export": None
            }
            
            latest_time = None
            latest_job = None
            
            for job_id, job_data in export_jobs.items():
                # Track latest export job
                job_time = job_data.get("started_at")
                if latest_time is None or (job_time and job_time > latest_time):
                    latest_time = job_time
                    latest_job = job_data
                
                # Count exports by platform and status
                for platform in job_data.get("platforms", []):
                    if platform not in export_summary["platforms"]:
                        export_summary["platforms"][platform] = {
                            "total": 0,
                            "successful": 0,
                            "failed": 0,
                            "processing": 0
                        }
                    
                    export_summary["platforms"][platform]["total"] += 1
                    
                    platform_result = job_data.get("platform_results", {}).get(platform, {})
                    status = platform_result.get("status", "processing")
                    
                    if status == "success":
                        export_summary["platforms"][platform]["successful"] += 1
                    elif status == "failure":
                        export_summary["platforms"][platform]["failed"] += 1
                    else:
                        export_summary["platforms"][platform]["processing"] += 1
            
            # Add latest export info
            if latest_job:
                export_summary["latest_export"] = {
                    "job_id": latest_job.get("job_id"),
                    "status": latest_job.get("status"),
                    "started_at": latest_job.get("started_at"),
                    "completed_at": latest_job.get("completed_at"),
                    "platforms": latest_job.get("platforms")
                }
            
            # Add export summary to video data
            video["export_summary"] = export_summary
        
        logger.debug(f"Retrieved video data: {video}")
        return {"video": video}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error getting video {video_id}: {e}", exc_info=DEBUG_MODE)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/videos/{video_id}/upload", response_class=JSONResponse)
async def upload_video(video_id: str, credentials: Dict[str, Any] = Depends(get_credentials)):
    """
    Upload a processed video to YouTube.
    
    Args:
        video_id: Video ID
        credentials: User credentials
        
    Returns:
        dict: Upload result
    """
    try:
        logger.info(f"Uploading video to YouTube: {video_id}")
        
        from src.app.core.database import get_video, update_video
        from src.app.services.youtube.api import upload_to_youtube
        
        video = get_video(video_id)
        if not video:
            logger.warning(f"Video not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        if video.get("status") != "ready_for_upload":
            logger.warning(f"Video not ready for upload: {video_id}, status: {video.get('status')}")
            raise HTTPException(status_code=400, detail="Video is not ready for upload")
        
        # Update status
        now = datetime.now()
        update_video(video_id, {"status": "uploading", "updated_at": now})
        logger.info(f"Updated video status to 'uploading': {video_id}")
        
        # Get video file path
        # In a real implementation, you'd download from GCS if needed
        # For MVP, we'll use the URL directly
        video_url = video.get("video_url")
        
        # Call YouTube API
        title = f"AI-Generated Short - {video.get('music_track')}"
        description = f"Created with YouTube Shorts Machine using {video.get('music_track')}"
        tags = ["shorts", "ai generated", "music"]
        
        logger.info(f"Uploading to YouTube: {title}")
        result = upload_to_youtube(
            credentials,
            video_path=video_url,  # This would be a local path in production
            title=title,
            description=description,
            tags=tags
        )
        
        if result:
            # Update video with YouTube ID
            update_video(video_id, {
                "status": "uploaded",
                "youtube_id": result,
                "updated_at": now
            })
            
            logger.info(f"Video successfully uploaded to YouTube: {video_id}, YouTube ID: {result}")
            return {
                "success": True,
                "video_id": video_id,
                "youtube_id": result
            }
        else:
            # Update status to failed
            update_video(video_id, {
                "status": "failed",
                "error_message": "Failed to upload to YouTube",
                "updated_at": now
            })
            
            logger.warning(f"Failed to upload video to YouTube: {video_id}")
            return {
                "success": False,
                "video_id": video_id,
                "error": "Failed to upload to YouTube"
            }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error uploading video {video_id}: {e}", exc_info=DEBUG_MODE)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/videos/enhanced", response_class=JSONResponse)
async def create_enhanced_video(
    music_track: str = Form(...),
    images: List[UploadFile] = File(...),
    style: str = Form(None),
    description: str = Form(""),
    use_runway: bool = Form(False),
    request: Request = None,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Create a new enhanced video using AI-powered video generation.
    
    Args:
        music_track: Music track name
        images: List of image files
        style: Video style to apply (cinematic, vlog, music_video, etc.)
        description: Additional description for video generation
        use_runway: Whether to use Runway ML for enhancement
        request: Request object
        credentials: User credentials
        
    Returns:
        dict: Created video information
    """
    try:
        from src.app.services.video.enhanced_processor import create_enhanced_short, VideoStyle, suggest_enhancements
        
        logger.info(f"Creating enhanced video with music track: {music_track}, "
                    f"{len(images)} images, style: {style}, use_runway: {use_runway}")
        
        if DEBUG_MODE:
            logger.debug(f"Image files: {[img.filename for img in images]}")
        
        # Generate video ID
        video_id = str(uuid.uuid4())
        logger.info(f"Generated video ID: {video_id}")
        
        # Save uploaded images to temporary files
        temp_image_paths = []
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")
            
            for i, image in enumerate(images):
                img_content = await image.read()
                img_path = os.path.join(temp_dir, f"image_{i}_{image.filename}")
                
                with open(img_path, "wb") as f:
                    f.write(img_content)
                
                temp_image_paths.append(img_path)
                logger.debug(f"Saved image {i+1}/{len(images)}: {img_path}")
            
            # Download music file
            from src.app.services.gcs.storage import get_music_url
            music_url = get_music_url(music_track)
            local_music_path = os.path.join(temp_dir, os.path.basename(music_track))
            from src.app.services.video.processor import download_music
            download_music(music_url, local_music_path)
            
            # Auto-suggest style if not provided
            suggested_style = None
            if not style:
                suggestions = suggest_enhancements(temp_image_paths, local_music_path)
                suggested_style = suggestions["suggested_style"]
                style = suggested_style
                logger.info(f"No style specified, auto-suggesting: {style}")
            
            # Use default style if still not available
            if not style:
                style = VideoStyle.CINEMATIC
            
            # Create video record
            now = datetime.now()
            video_data = {
                "id": video_id,
                "music_track": music_track,
                "style": style,
                "description": description,
                "use_runway": use_runway,
                "status": "pending",
                "created_at": now,
                "updated_at": now
            }
            
            from src.app.core.database import create_video
            create_video(video_id, video_data)
            logger.info(f"Created enhanced video record in database: {video_id}")
            
            # Process video (in a real implementation, this would be async)
            output_path = os.path.join(temp_dir, f"{video_id}.mp4")
            create_enhanced_short(
                images=temp_image_paths,
                music_path=local_music_path,
                output_path=output_path,
                style=style,
                use_runway=use_runway
            )
            
            # Upload the resulting video to storage
            from src.app.services.gcs.storage import upload_video
            video_url = upload_video(output_path, f"videos/{video_id}.mp4")
            
            # Update video record
            from src.app.core.database import update_video
            update_video(video_id, {
                "status": "ready_for_upload",
                "video_url": video_url,
                "updated_at": datetime.now()
            })
            
            response_data = {
                "video_id": video_id,
                "status": "ready_for_upload",
                "message": "Enhanced video creation completed",
                "track": music_track,
                "style": style,
                "suggested_style": suggested_style,
                "use_runway": use_runway,
                "images_count": len(images),
                "video_url": video_url
            }
            
            return response_data
            
    except Exception as e:
        logger.error(f"Error creating enhanced video: {e}", exc_info=DEBUG_MODE)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/styles", response_class=JSONResponse)
async def get_video_styles():
    """
    Get a list of available video styles with descriptions.
    
    Returns:
        Object with styles property containing style objects with name, description, and example image URL.
    """
    try:
        # Get list of styles
        styles = [
            {
                "name": "DYNAMIC",
                "description": "Energetic style with beat-synchronized effects",
                "image_url": "/static/images/styles/dynamic.jpg",
                "prompt_template": "Create a dynamic video with energetic transitions and effects"
            },
            {
                "name": "MINIMAL",
                "description": "Clean, simple style with subtle transitions",
                "image_url": "/static/images/styles/minimal.jpg",
                "prompt_template": "Create a minimal, clean video with subtle transitions"
            },
            {
                "name": "ENERGETIC",
                "description": "High-energy style with dramatic effects and transitions",
                "image_url": "/static/images/styles/energetic.jpg",
                "prompt_template": "Create a high-energy video with dramatic effects"
            },
            {
                "name": "SMOOTH",
                "description": "Fluid transitions and gentle effects for a smoother feel",
                "image_url": "/static/images/styles/smooth.jpg",
                "prompt_template": "Create a smooth video with fluid transitions"
            },
            {
                "name": "TIKTOK",
                "description": "TikTok-inspired style with trendy effects",
                "image_url": "/static/images/styles/tiktok.jpg",
                "prompt_template": "Create a TikTok-style video with trendy effects"
            },
            {
                "name": "YOUTUBE",
                "description": "YouTube Shorts optimized style",
                "image_url": "/static/images/styles/youtube.jpg",
                "prompt_template": "Create a YouTube Shorts optimized video"
            },
            {
                "name": "INSTAGRAM",
                "description": "Instagram Reels inspired style",
                "image_url": "/static/images/styles/instagram.jpg",
                "prompt_template": "Create an Instagram Reels inspired video"
            },
            {
                "name": "CINEMATIC",
                "description": "Cinematic style with film-like transitions",
                "image_url": "/static/images/styles/cinematic.jpg",
                "prompt_template": "Create a cinematic style video with film-like transitions"
            }
        ]
        
        # Return styles object with styles property expected by frontend
        return {"styles": styles}
    except Exception as e:
        logger.error(f"Error getting video styles: {str(e)}")
        # Return a subset of styles rather than failing completely
        fallback_styles = [
            {
                "name": "DYNAMIC",
                "description": "Energetic style with beat-synchronized effects",
                "image_url": "/static/images/styles/default.jpg",
                "prompt_template": "Create a dynamic video with energetic transitions"
            },
            {
                "name": "MINIMAL",
                "description": "Clean, simple style with subtle transitions",
                "image_url": "/static/images/styles/default.jpg",
                "prompt_template": "Create a minimal, clean video with subtle transitions"
            }
        ]
        return {"styles": fallback_styles}

@app.post("/suggest", response_class=JSONResponse)
async def suggest_video_style(
    music_track: str = Form(...),
    images: List[UploadFile] = File(...)
):
    """
    Suggest video style based on uploaded content.
    
    Args:
        music_track: Music track name
        images: List of image files
        
    Returns:
        dict: Style suggestions and parameters
    """
    try:
        from src.app.services.video.enhanced_processor import suggest_enhancements
        
        logger.info(f"Suggesting style for music track: {music_track} and {len(images)} images")
        
        # Save uploaded images to temporary files
        temp_image_paths = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, image in enumerate(images):
                img_content = await image.read()
                img_path = os.path.join(temp_dir, f"image_{i}_{image.filename}")
                
                with open(img_path, "wb") as f:
                    f.write(img_content)
                
                temp_image_paths.append(img_path)
            
            # Download music file
            from src.app.services.gcs.storage import get_music_url
            music_url = get_music_url(music_track)
            local_music_path = os.path.join(temp_dir, os.path.basename(music_track))
            from src.app.services.video.processor import download_music
            download_music(music_url, local_music_path)
            
            # Get style suggestions
            suggestions = suggest_enhancements(temp_image_paths, local_music_path)
            return suggestions
            
    except Exception as e:
        logger.error(f"Error suggesting style: {e}", exc_info=DEBUG_MODE)
        raise HTTPException(status_code=500, detail=str(e))

# Create a router for YouTube trends and recommendations
@app.get("/trends", tags=["youtube"])
async def get_youtube_trends():
    """Get trending data from YouTube."""
    # Comment out the code that's using analyze_trending_patterns
    # result = analyze_trending_patterns()
    # Return mock data instead
    return {
        "status": "success",
        "message": "This endpoint is currently under maintenance",
        "trends": {
            "trending_topics": ["short form content", "music videos", "tutorials"],
            "trend_data": []
        }
    }

@app.post("/optimize", tags=["youtube"])
async def optimize_video_metadata(
    topic: str = Form(...),
    music_track: str = Form(...),
    images: List[UploadFile] = File(...),
    include_trend_data: bool = Form(False)
):
    """
    Generate optimized metadata for a YouTube Short based on current trends.
    
    - topic: Main topic of the video
    - music_track: Music track used in the video
    - images: Images used in the video
    - include_trend_data: Whether to include trend data in the response
    """
    try:
        # Get trending data
        trending_data = analyze_trending_patterns()
        
        # Get content-specific recommendations
        # In a full implementation, this would analyze the images
        image_paths = []
        for img in images:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
                temp.write(await img.read())
                image_paths.append(temp.name)
        
        # Generate optimized metadata
        metadata = generate_optimized_metadata(
            topic=topic, 
            music_track=music_track,
            trending_data=trending_data
        )
        
        # Clean up temporary files
        for path in image_paths:
            try:
                os.unlink(path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {path}: {e}")
        
        # Return response
        if include_trend_data:
            return {
                "metadata": metadata,
                "trend_data": trending_data
            }
        else:
            return metadata
            
    except Exception as e:
        logger.error(f"Error optimizing video metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing metadata: {str(e)}")

# Create a router for content recommendations
@app.post("/recommendations", tags=["youtube"])
async def get_content_recommendations(
    music_track: str = Form(...),
    images: List[UploadFile] = File(...)
):
    """Get content recommendations based on music and images."""
    # Comment out the code that's using get_recommendations_for_content
    # recommendations = get_recommendations_for_content(music_track)
    # Return mock data instead
    return {
        "status": "success",
        "message": "This endpoint is currently under maintenance",
        "recommendations": {
            "topics": ["music", "entertainment", "creativity"],
            "hashtags": ["#shorts", "#music", "#viral"]
        }
    }

@app.post("/videos/{video_id}/export", response_class=JSONResponse)
async def export_video_to_platforms(
    video_id: str, 
    platforms: List[str] = Body(None),
    metadata: Optional[Dict[str, Any]] = Body(None),
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Export a video to multiple platforms.
    
    Args:
        video_id: ID of the video to export
        platforms: List of platform names to export to (defaults to all available)
        metadata: Optional metadata for export
        credentials: User credentials
        
    Returns:
        dict: Export job details
    """
    try:
        logger.info(f"Exporting video {video_id} to platforms: {platforms}")
        
        # Import export models and handlers
        from src.app.api.endpoints.export import ExportRequest, ExportPlatform, export_to_platforms
        
        # Get available platforms
        from src.app.api.endpoints.export import get_export_platforms
        available_platforms = await get_export_platforms()
        
        # If no platforms specified, use all enabled ones
        if not platforms:
            platforms = [
                p for p, details in available_platforms.get("platforms", {}).items()
                if details.get("enabled", False)
            ]
        
        # Validate platforms
        valid_platforms = [
            p for p in platforms 
            if p in available_platforms.get("platforms", {}) and 
            available_platforms.get("platforms", {}).get(p, {}).get("enabled", False)
        ]
        
        if not valid_platforms:
            raise HTTPException(status_code=400, detail="No valid platforms specified")
        
        # Build export request
        export_platforms = []
        for platform in valid_platforms:
            platform_settings = {}
            
            # Add any platform-specific settings from metadata
            if metadata and platform in metadata:
                platform_settings = metadata.get(platform, {})
                
            export_platforms.append(
                ExportPlatform(
                    platform_name=platform,
                    platform_settings=platform_settings
                )
            )
        
        # Create export request
        request = ExportRequest(
            video_id=video_id,
            platforms=export_platforms,
            metadata=metadata
        )
        
        # Call export handler
        from fastapi import BackgroundTasks
        background_tasks = BackgroundTasks()
        result = await export_to_platforms(request, background_tasks, credentials)
        
        # Return result
        return {
            "export_job": {
                "job_id": result.job_id,
                "video_id": result.video_id,
                "platforms": result.platforms,
                "status": result.status,
                "started_at": result.started_at
            }
        }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error exporting video {video_id}: {e}", exc_info=DEBUG_MODE)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/videos/music-responsive", response_class=JSONResponse)
async def create_music_responsive_video_endpoint(
    music_track: str = Form(...),
    images: List[UploadFile] = File(...),
    effect_intensity: float = Form(1.0),
    duration: int = Form(60),
    request: Request = None,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Create a new video with advanced music-responsive effects.
    
    Args:
        music_track: Music track name
        images: List of image files
        effect_intensity: Intensity of music effects (0.0 to 2.0)
        duration: Target duration in seconds
        request: Request object
        credentials: User credentials
        
    Returns:
        dict: Created video information
    """
    try:
        logger.info(f"Creating music-responsive video with track: {music_track}, "
                   f"{len(images)} images, intensity: {effect_intensity}")
        
        if DEBUG_MODE:
            logger.debug(f"Image files: {[img.filename for img in images]}")
        
        # Generate video ID
        video_id = str(uuid.uuid4())
        logger.info(f"Generated video ID: {video_id}")
        
        # Save uploaded images to temporary files
        temp_image_paths = []
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")
            
            for i, image in enumerate(images):
                img_content = await image.read()
                img_path = os.path.join(temp_dir, f"image_{i}_{image.filename}")
                
                with open(img_path, "wb") as f:
                    f.write(img_content)
                
                temp_image_paths.append(img_path)
                logger.debug(f"Saved image {i+1}/{len(images)}: {img_path}")
            
            # Get music file - handle both GCS and mock files
            local_music_path = ""
            if music_track.startswith("track") and DEV_MODE:
                # Handle mock files directly
                mock_path = os.path.join("mock-media", music_track)
                if os.path.exists(mock_path):
                    local_music_path = mock_path
                    logger.info(f"Using local mock music file: {local_music_path}")
                else:
                    logger.warning(f"Mock file not found: {mock_path}")
                    # Create an empty mock file
                    local_music_path = os.path.join(temp_dir, music_track)
                    with open(local_music_path, 'w') as f:
                        f.write(f"Mock music content for {music_track}")
                    logger.info(f"Created empty mock music file: {local_music_path}")
            else:
                # Normal GCS path
                from src.app.services.gcs.storage import get_music_url
                music_url = get_music_url(music_track)
                local_music_path = os.path.join(temp_dir, os.path.basename(music_track))
                from src.app.services.video.processor import download_music
                download_music(music_url, local_music_path)
            
            # Create video record
            now = datetime.now()
            video_data = {
                "id": video_id,
                "music_track": music_track,
                "type": "music_responsive",
                "effect_intensity": effect_intensity,
                "status": "pending",
                "created_at": now,
                "updated_at": now
            }
            
            from src.app.core.database import create_video
            create_video(video_id, video_data)
            logger.info(f"Created music-responsive video record in database: {video_id}")
            
            # Process video
            output_path = os.path.join(temp_dir, f"{video_id}.mp4")
            
            # Create music-responsive video
            create_music_responsive_video(
                images=temp_image_paths,
                music_path=local_music_path,
                output_path=output_path,
                duration=duration,
                effect_intensity=effect_intensity
            )
            
            # Upload the resulting video to storage
            video_url = ""
            try:
                from src.app.services.gcs.storage import upload_video
                video_url = upload_video(output_path, f"videos/{video_id}.mp4")
            except Exception as e:
                logger.warning(f"Failed to upload video to GCS: {e}")
                # Use a local path for development
                if DEV_MODE:
                    video_url = f"file://{output_path}"
                    logger.info(f"Using local file path: {video_url}")
                else:
                    raise
            
            # Update video record
            from src.app.core.database import update_video
            update_video(video_id, {
                "status": "ready_for_upload",
                "video_url": video_url,
                "updated_at": datetime.now()
            })
            
            response_data = {
                "video_id": video_id,
                "status": "ready_for_upload",
                "message": "Music-responsive video creation completed",
                "track": music_track,
                "effect_intensity": effect_intensity,
                "images_count": len(images),
                "video_url": video_url
            }
            
            return response_data
            
    except Exception as e:
        logger.error(f"Error creating music-responsive video: {e}", exc_info=DEBUG_MODE)
        raise HTTPException(status_code=500, detail=str(e))

# Include the routers
app.include_router(dashboard_router)
app.include_router(thumbnails_router)
app.include_router(scheduler_router)
app.include_router(branding_router)
app.include_router(licensing_router)

@app.get("/api/debug/status", response_class=JSONResponse)
async def debug_status():
    """
    Debug endpoint to check the overall system status and verify all fixes are working.
    """
    from src.app.core.settings import DEV_MODE, DEBUG_MODE
    
    if not DEV_MODE and not DEBUG_MODE:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Test results dictionary
    test_results = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "dev_mode": DEV_MODE,
        "debug_mode": DEBUG_MODE,
        "tests": {}
    }
    
    # Test styles API
    try:
        styles_response = await get_video_styles()
        test_results["tests"]["styles_api"] = {
            "status": "ok",
            "has_styles_property": "styles" in styles_response,
            "styles_count": len(styles_response.get("styles", [])),
            "first_style_has_prompt_template": bool(styles_response.get("styles", [{}])[0].get("prompt_template")),
        }
    except Exception as e:
        test_results["tests"]["styles_api"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test waveform API
    try:
        from src.app.services.audio.waveform import generate_mock_waveform
        test_waveform = generate_mock_waveform(100)
        test_results["tests"]["waveform_generation"] = {
            "status": "ok",
            "waveform_length": len(test_waveform),
            "min_value": min(test_waveform),
            "max_value": max(test_waveform),
            "sample_values": test_waveform[:5]
        }
    except Exception as e:
        test_results["tests"]["waveform_generation"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test enhanced processor
    try:
        from src.app.services.video.enhanced_processor import VideoProcessingOptions
        processor_options = VideoProcessingOptions(
            enable_music_sync=True,
            music_sync_intensity=1.0,
            use_smart_transitions=True
        )
        test_results["tests"]["enhanced_processor"] = {
            "status": "ok",
            "options_created": bool(processor_options),
            "has_music_sync": processor_options.enable_music_sync,
            "sync_intensity": processor_options.music_sync_intensity
        }
    except Exception as e:
        test_results["tests"]["enhanced_processor"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check JS file loading
    try:
        import os
        from pathlib import Path
        
        js_files = [
            "progress-indicators.js",
            "supabase-auth.js"
        ]
        
        js_status = {}
        for js_file in js_files:
            js_path = Path("static/js") / js_file
            js_status[js_file] = {
                "exists": os.path.exists(js_path),
                "size": os.path.getsize(js_path) if os.path.exists(js_path) else 0
            }
        
        test_results["tests"]["js_files"] = {
            "status": "ok",
            "files": js_status
        }
    except Exception as e:
        test_results["tests"]["js_files"] = {
            "status": "error",
            "error": str(e)
        }
    
    return test_results

@app.get("/api/debug/error/test", response_class=JSONResponse)
async def debug_error_test():
    """
    Debug endpoint for testing error handling.
    Only available in development mode.
    """
    from src.app.core.settings import DEV_MODE, DEBUG_MODE
    
    if not DEV_MODE and not DEBUG_MODE:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Return working response
    return {
        "status": "ok",
        "message": "Debug error test endpoint is now working",
        "dev_mode": DEV_MODE,
        "debug_mode": DEBUG_MODE
    }

# Add explicit route for /auth/status for direct access
@app.get("/auth/status", response_class=JSONResponse)
async def auth_status_direct():
    """Direct auth status endpoint that forwards to the auth router."""
    from src.app.api.auth import auth_status
    return await auth_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app.api.main:app", 
        host=API_HOST, 
        port=API_PORT,
        log_level="debug" if DEBUG_MODE else "info",
        reload=True
    ) 