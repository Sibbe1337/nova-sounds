"""
API endpoints for music-responsive video generation.

This module provides FastAPI endpoints for creating music-responsive videos
with various presets and options.
"""

import os
import tempfile
import shutil
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import logging
import uuid
import time

from src.app.services.video.music_responsive import (
    create_music_responsive_video,
    StylePreset,
    get_preset_manager
)
from src.app.services.video.music_responsive.analytics import get_analytics_manager
from src.app.services.video.platform_adapter import adapt_video_for_platform, Platform, ResizeMode

# Set up logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/music-responsive",
    tags=["music-responsive"],
    responses={404: {"description": "Not found"}},
)

# Create temp directory for uploads and outputs
UPLOAD_DIR = tempfile.mkdtemp(prefix="music_responsive_")
OUTPUT_DIR = os.path.join(UPLOAD_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Store job status information
jobs = {}

class PresetInfo(BaseModel):
    """Preset information model."""
    id: str
    name: str
    description: str

class JobStatus(BaseModel):
    """Job status model."""
    job_id: str
    status: str
    message: Optional[str] = None
    progress: Optional[float] = None
    output_file: Optional[str] = None

class AnalyticsResponse(BaseModel):
    """Analytics response model."""
    total_sessions: int
    successful_sessions: Optional[int] = None
    failed_sessions: Optional[int] = None
    success_rate: Optional[float] = None
    avg_processing_time: Optional[float] = None
    avg_file_size: Optional[int] = None
    preset_usage: Optional[dict] = None
    effect_usage: Optional[dict] = None
    avg_effect_intensity: Optional[float] = None
    error: Optional[str] = None

class PlatformDistributionRequest(BaseModel):
    """Platform distribution request model."""
    platform: str
    video_id: str
    success: bool
    engagement_metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class PlatformAnalyticsResponse(BaseModel):
    """Platform analytics response model."""
    total_distributions: int
    successful_distributions: Optional[int] = None
    failed_distributions: Optional[int] = None
    success_rate: Optional[float] = None
    platform_distribution: Optional[Dict[str, int]] = None
    platform_engagement: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PlatformExportRequest(BaseModel):
    """Platform export request model."""
    platforms: List[str]
    resize_mode: str = "crop"

class PlatformExportResponse(BaseModel):
    """Platform export response model."""
    job_id: str
    status: str
    exports: Dict[str, Dict[str, Any]]

@router.get("/presets", response_model=dict)
async def list_presets():
    """List all available presets."""
    preset_manager = get_preset_manager()
    return preset_manager.list_all_presets()

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics_data(limit: Optional[int] = 100):
    """
    Get analytics data for music-responsive video generation.
    
    Args:
        limit: Maximum number of recent sessions to analyze (default: 100)
        
    Returns:
        AnalyticsResponse: Statistics about video generation
    """
    try:
        analytics_manager = get_analytics_manager()
        stats = analytics_manager.get_aggregate_stats(limit)
        return stats
    except Exception as e:
        logger.error(f"Error retrieving analytics data: {e}")
        return AnalyticsResponse(total_sessions=0, error=str(e))

@router.get("/analytics/preset/{preset_name}")
async def get_preset_analytics(preset_name: str, limit: Optional[int] = 100):
    """
    Get analytics data for a specific preset.
    
    Args:
        preset_name: Name of the preset to get analytics for
        limit: Maximum number of recent sessions to analyze (default: 100)
        
    Returns:
        dict: Statistics about the specified preset
    """
    try:
        analytics_manager = get_analytics_manager()
        stats = analytics_manager.get_aggregate_stats(limit)
        
        # Filter for the specified preset
        preset_sessions = []
        if os.path.exists(analytics_manager.analytics_file):
            with open(analytics_manager.analytics_file, 'r') as f:
                import json
                all_sessions = json.load(f)
                preset_sessions = [s for s in all_sessions if s.get('preset') == preset_name]
        
        if not preset_sessions:
            return {"preset": preset_name, "total_sessions": 0, "message": "No data available for this preset"}
        
        # Calculate preset-specific stats
        successful = sum(1 for s in preset_sessions if s.get("completed", False))
        avg_processing_time = sum(s.get("processing_time", 0) for s in preset_sessions) / max(1, len(preset_sessions))
        avg_file_size = sum(s.get("output_file_size", 0) for s in preset_sessions if s.get("completed", False)) / max(1, successful)
        
        # Count effect usage for this preset
        effect_usage = {}
        for session in preset_sessions:
            for effect in session.get("effects_used", []):
                effect_usage[effect] = effect_usage.get(effect, 0) + 1
        
        # Count music features analyzed
        music_features = {}
        for session in preset_sessions:
            for feature in session.get("music_features_analyzed", []):
                music_features[feature] = music_features.get(feature, 0) + 1
        
        return {
            "preset": preset_name,
            "total_sessions": len(preset_sessions),
            "successful_sessions": successful,
            "failed_sessions": len(preset_sessions) - successful,
            "success_rate": successful / len(preset_sessions),
            "avg_processing_time": avg_processing_time,
            "avg_file_size": avg_file_size,
            "effect_usage": effect_usage,
            "music_features": music_features,
            "avg_effect_intensity": sum(s.get("effect_intensity", 0) for s in preset_sessions) / len(preset_sessions)
        }
    except Exception as e:
        logger.error(f"Error retrieving preset analytics: {e}")
        return {"preset": preset_name, "error": str(e), "total_sessions": 0}

@router.get("/analytics/recent", response_model=List[dict])
async def get_recent_generations(limit: Optional[int] = 10):
    """
    Get recent generation sessions with detailed information.
    
    Args:
        limit: Maximum number of recent sessions to return (default: 10)
        
    Returns:
        List[dict]: List of recent generation sessions with details
    """
    try:
        analytics_manager = get_analytics_manager()
        
        # Get recent sessions
        recent_sessions = []
        if os.path.exists(analytics_manager.analytics_file):
            with open(analytics_manager.analytics_file, 'r') as f:
                import json
                all_sessions = json.load(f)
                # Get the most recent sessions
                recent_sessions = sorted(
                    all_sessions, 
                    key=lambda s: s.get("end_time", 0), 
                    reverse=True
                )[:limit]
        
        # Format the sessions for display
        formatted_sessions = []
        for session in recent_sessions:
            # Format timestamp
            timestamp = session.get("timestamp", "")
            formatted_date = ""
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = timestamp
            
            # Get session ID (use the first 8 characters)
            session_id = session.get("session_id", "")
            short_id = f"VID-{session_id[:8]}" if session_id else "Unknown"
            
            # Format duration
            duration = session.get("duration", 0)
            formatted_duration = f"{duration}s" if duration else "Unknown"
            
            # Format processing time
            processing_time = session.get("processing_time", 0)
            formatted_time = f"{(processing_time / 60):.1f}m" if processing_time > 60 else f"{processing_time:.1f}s"
            
            # Determine error type if failed
            error_type = "Unknown"
            if not session.get("completed", True) and "error" in session:
                error_msg = session["error"].lower()
                if "audio" in error_msg or "music" in error_msg:
                    error_type = "Audio Processing"
                elif "memory" in error_msg or "resources" in error_msg:
                    error_type = "Out of Memory"
                elif "timeout" in error_msg or "time limit" in error_msg:
                    error_type = "Timeout"
                elif "format" in error_msg or "file type" in error_msg or "unsupported" in error_msg:
                    error_type = "Invalid Format"
                else:
                    error_type = "Other"
            
            formatted_sessions.append({
                "id": short_id,
                "date": formatted_date,
                "preset": session.get("preset", "Unknown"),
                "duration": formatted_duration,
                "processing_time": formatted_time,
                "status": "completed" if session.get("completed", False) else "failed",
                "error_type": error_type if not session.get("completed", False) else None,
                "effect_intensity": session.get("effect_intensity", 0),
                "image_count": session.get("image_count", 0),
                "effects_used": session.get("effects_used", []),
                "file_size": session.get("output_file_size", 0)
            })
        
        return formatted_sessions
    except Exception as e:
        logger.error(f"Error retrieving recent generations: {e}")
        return []

@router.get("/analytics/errors", response_model=dict)
async def get_error_analytics(limit: Optional[int] = 100):
    """
    Get analytics data about errors in video generation.
    
    Args:
        limit: Maximum number of recent sessions to analyze (default: 100)
        
    Returns:
        dict: Statistics about errors in video generation
    """
    try:
        analytics_manager = get_analytics_manager()
        
        # Get sessions with errors
        error_sessions = []
        if os.path.exists(analytics_manager.analytics_file):
            with open(analytics_manager.analytics_file, 'r') as f:
                import json
                all_sessions = json.load(f)
                # Get the most recent sessions up to the limit
                recent_sessions = all_sessions[-limit:] if len(all_sessions) > limit else all_sessions
                # Filter for sessions with errors
                error_sessions = [s for s in recent_sessions if not s.get("completed", True)]
        
        # Categorize errors
        error_categories = {
            "Audio Processing": 0,
            "Out of Memory": 0,
            "Timeout": 0,
            "Invalid Format": 0,
            "Other": 0
        }
        
        for session in error_sessions:
            if "error" in session:
                error_msg = session["error"].lower()
                if "audio" in error_msg or "music" in error_msg:
                    error_categories["Audio Processing"] += 1
                elif "memory" in error_msg or "resources" in error_msg:
                    error_categories["Out of Memory"] += 1
                elif "timeout" in error_msg or "time limit" in error_msg:
                    error_categories["Timeout"] += 1
                elif "format" in error_msg or "file type" in error_msg or "unsupported" in error_msg:
                    error_categories["Invalid Format"] += 1
                else:
                    error_categories["Other"] += 1
            else:
                error_categories["Other"] += 1
        
        return {
            "total_errors": len(error_sessions),
            "error_categories": error_categories
        }
    except Exception as e:
        logger.error(f"Error retrieving error analytics: {e}")
        return {"total_errors": 0, "error": str(e)}

@router.get("/analytics/trends", response_model=dict)
async def get_analytics_trends(timeframe: str = "week"):
    """
    Get time-based analytics trends.
    
    Args:
        timeframe: Time period to analyze ('day', 'week', 'month', 'year')
        
    Returns:
        dict: Time-based analytics data
    """
    try:
        analytics_manager = get_analytics_manager()
        
        # Get all sessions
        all_sessions = []
        if os.path.exists(analytics_manager.analytics_file):
            with open(analytics_manager.analytics_file, 'r') as f:
                import json
                all_sessions = json.load(f)
        
        if not all_sessions:
            return {
                "labels": [],
                "successful": [],
                "failed": [],
                "avg_processing_time": [],
                "avg_file_size": []
            }
        
        from datetime import datetime, timedelta
        
        # Determine time buckets and labels based on timeframe
        now = datetime.now()
        
        if timeframe == "day":
            # Last 24 hours, hourly buckets
            start_time = now - timedelta(days=1)
            time_format = "%H:00"  # Hour format
            bucket_size = timedelta(hours=1)
            num_buckets = 24
            labels = [(start_time + bucket_size * i).strftime(time_format) for i in range(num_buckets)]
        elif timeframe == "week":
            # Last 7 days, daily buckets
            start_time = now - timedelta(days=7)
            time_format = "%a"  # Day of week format
            bucket_size = timedelta(days=1)
            num_buckets = 7
            labels = [(start_time + bucket_size * i).strftime(time_format) for i in range(num_buckets)]
        elif timeframe == "month":
            # Last 30 days, daily buckets
            start_time = now - timedelta(days=30)
            time_format = "%d"  # Day of month format
            bucket_size = timedelta(days=1)
            num_buckets = 30
            labels = [(start_time + bucket_size * i).strftime(time_format) for i in range(num_buckets)]
        else:  # year
            # Last 12 months, monthly buckets
            start_time = now - timedelta(days=365)
            time_format = "%b"  # Month format
            bucket_size = timedelta(days=30)
            num_buckets = 12
            labels = [(start_time + bucket_size * i).strftime(time_format) for i in range(num_buckets)]
        
        # Initialize data arrays
        successful = [0] * num_buckets
        failed = [0] * num_buckets
        processing_times = [[] for _ in range(num_buckets)]
        file_sizes = [[] for _ in range(num_buckets)]
        
        # Filter sessions by timeframe
        start_timestamp = start_time.timestamp()
        for session in all_sessions:
            # Skip sessions older than the start time
            session_timestamp = session.get("end_time", 0)
            if session_timestamp < start_timestamp:
                continue
            
            # Calculate which bucket this session belongs to
            session_time = datetime.fromtimestamp(session_timestamp)
            bucket_idx = min(int((session_time - start_time) / bucket_size), num_buckets - 1)
            
            # Count successful vs failed
            if session.get("completed", False):
                successful[bucket_idx] += 1
                if session.get("output_file_size", 0) > 0:
                    file_sizes[bucket_idx].append(session.get("output_file_size", 0))
            else:
                failed[bucket_idx] += 1
            
            # Record processing time
            if session.get("processing_time", 0) > 0:
                processing_times[bucket_idx].append(session.get("processing_time", 0))
        
        # Calculate averages
        avg_processing_time = []
        for times in processing_times:
            if times:
                avg_processing_time.append(sum(times) / len(times))
            else:
                avg_processing_time.append(0)
        
        avg_file_size = []
        for sizes in file_sizes:
            if sizes:
                avg_file_size.append(sum(sizes) / len(sizes))
            else:
                avg_file_size.append(0)
        
        return {
            "labels": labels,
            "successful": successful,
            "failed": failed,
            "avg_processing_time": avg_processing_time,
            "avg_file_size": avg_file_size
        }
    except Exception as e:
        logger.error(f"Error retrieving analytics trends: {e}")
        return {
            "error": str(e),
            "labels": [],
            "successful": [],
            "failed": [],
            "avg_processing_time": [],
            "avg_file_size": []
        }

@router.post("/generate", response_model=JobStatus)
async def generate_video(
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(...),
    music: UploadFile = File(...),
    preset: str = Form("standard"),
    effect_intensity: float = Form(1.0),
    duration: int = Form(60),
    use_smooth_transitions: bool = Form(True),
    custom_preset_id: Optional[str] = Form(None)
):
    """
    Generate a music-responsive video with the specified parameters.
    
    Args:
        images: List of image files to use in the video
        music: Audio file to use for the video
        preset: Preset style to use
        effect_intensity: Overall intensity of effects (0.1 to 2.0)
        duration: Maximum duration in seconds
        use_smooth_transitions: Whether to use smooth transitions between segments
        custom_preset_id: ID of custom preset (if preset is 'custom')
    
    Returns:
        JobStatus: Status of the video generation job
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create job directory
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save uploaded files
    image_paths = []
    try:
        # Save images
        for i, img in enumerate(images):
            img_path = os.path.join(job_dir, f"image_{i}{os.path.splitext(img.filename)[1]}")
            with open(img_path, "wb") as f:
                f.write(await img.read())
            image_paths.append(img_path)
        
        # Save music
        music_path = os.path.join(job_dir, f"music{os.path.splitext(music.filename)[1]}")
        with open(music_path, "wb") as f:
            f.write(await music.read())
        
        # Set output path
        output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
        
        # Create initial job status
        jobs[job_id] = {
            "status": "queued",
            "progress": 0.0,
            "output_file": None,
            "message": "Job queued for processing"
        }
        
        # Run video generation in background
        background_tasks.add_task(
            process_video_job,
            job_id=job_id,
            image_paths=image_paths,
            music_path=music_path,
            output_path=output_path,
            preset=preset,
            effect_intensity=effect_intensity,
            duration=duration,
            use_smooth_transitions=use_smooth_transitions,
            custom_preset_id=custom_preset_id
        )
        
        return JobStatus(
            job_id=job_id,
            status="queued",
            message="Job queued for processing",
            progress=0.0
        )
    
    except Exception as e:
        logger.error(f"Error setting up job: {e}")
        # Clean up in case of error
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a video generation job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_status = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job_status["status"],
        message=job_status.get("message"),
        progress=job_status.get("progress"),
        output_file=job_status.get("output_file")
    )

@router.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download a generated video."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_status = jobs[job_id]
    if job_status["status"] != "completed" or not job_status.get("output_file"):
        raise HTTPException(status_code=400, detail="Video not ready for download")
    
    output_file = job_status["output_file"]
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        output_file,
        media_type="video/mp4",
        filename=f"music_responsive_{job_id}.mp4"
    )

@router.get("/analytics/platform", response_model=PlatformAnalyticsResponse)
async def get_platform_analytics(platform: Optional[str] = None, limit: Optional[int] = 100):
    """
    Get analytics data for platform distributions.
    
    Args:
        platform: Optional platform to filter by (e.g. youtube, tiktok)
        limit: Maximum number of recent distributions to analyze (default: 100)
        
    Returns:
        PlatformAnalyticsResponse: Statistics about video distribution to platforms
    """
    try:
        analytics_manager = get_analytics_manager()
        stats = analytics_manager.get_platform_stats(platform, limit)
        return stats
    except Exception as e:
        logger.error(f"Error retrieving platform analytics data: {e}")
        return PlatformAnalyticsResponse(total_distributions=0, error=str(e))

@router.post("/analytics/platform/record", response_model=Dict[str, Any])
async def record_platform_distribution(request: PlatformDistributionRequest):
    """
    Record a video distribution to a platform.
    
    Args:
        request: Platform distribution data
        
    Returns:
        dict: Recorded platform distribution data
    """
    try:
        analytics_manager = get_analytics_manager()
        result = analytics_manager.record_platform_distribution(
            video_id=request.video_id,
            platform=request.platform,
            success=request.success,
            engagement_metrics=request.engagement_metrics,
            error_message=request.error_message
        )
        return result
    except Exception as e:
        logger.error(f"Error recording platform distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/analytics/platform/update", response_model=Dict[str, Any])
async def update_platform_metrics(video_id: str, platform: str, metrics: Dict[str, Any]):
    """
    Update engagement metrics for a video on a platform.
    
    Args:
        video_id: ID of the video
        platform: Platform name
        metrics: Updated engagement metrics
        
    Returns:
        dict: Updated platform metrics
    """
    try:
        analytics_manager = get_analytics_manager()
        result = analytics_manager.update_platform_metrics(
            video_id=video_id,
            platform=platform,
            metrics=metrics
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"No record found for video {video_id} on {platform}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating platform metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/{video_id}", response_model=PlatformExportResponse)
async def export_to_platforms(
    video_id: str,
    request: PlatformExportRequest,
    background_tasks: BackgroundTasks
):
    """
    Export a video to multiple platforms.
    
    Args:
        video_id: ID of the video to export
        request: Platform export request
        
    Returns:
        PlatformExportResponse: Export job information
    """
    # Check if the video exists and is ready
    if video_id not in jobs:
        raise HTTPException(status_code=404, detail="Video not found")
    
    job_status = jobs[video_id]
    if job_status["status"] != "completed" or not job_status.get("output_file"):
        raise HTTPException(status_code=400, detail="Video not ready for export")
    
    # Create export job
    export_job_id = str(uuid.uuid4())
    exports = {}
    
    # Initialize export status for each platform
    for platform_name in request.platforms:
        try:
            platform = Platform(platform_name.lower())
            exports[platform.value] = {
                "status": "pending",
                "message": "Export queued"
            }
        except ValueError:
            exports[platform_name] = {
                "status": "failed",
                "message": f"Unknown platform: {platform_name}"
            }
    
    # Store export job
    export_job = {
        "job_id": export_job_id,
        "video_id": video_id,
        "status": "processing",
        "exports": exports,
        "created_at": time.time()
    }
    
    # Store in global state (in a real app, this would be in a database)
    global export_jobs
    if 'export_jobs' not in globals():
        export_jobs = {}
    export_jobs[export_job_id] = export_job
    
    # Process export in background
    background_tasks.add_task(
        process_export_job,
        export_job_id=export_job_id,
        video_id=video_id,
        platforms=request.platforms,
        resize_mode=ResizeMode(request.resize_mode) if request.resize_mode else ResizeMode.CROP
    )
    
    return PlatformExportResponse(
        job_id=export_job_id,
        status="processing",
        exports=exports
    )

@router.get("/export/{export_job_id}", response_model=PlatformExportResponse)
async def get_export_status(export_job_id: str):
    """
    Get the status of a platform export job.
    
    Args:
        export_job_id: ID of the export job
        
    Returns:
        PlatformExportResponse: Export job information
    """
    global export_jobs
    if 'export_jobs' not in globals() or export_job_id not in export_jobs:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    export_job = export_jobs[export_job_id]
    
    return PlatformExportResponse(
        job_id=export_job_id,
        status=export_job["status"],
        exports=export_job["exports"]
    )

@router.get("/analytics/platforms", response_model=Dict[str, Any])
async def get_platform_analytics():
    """Get analytics for platform distributions."""
    analytics_manager = get_analytics_manager()
    return analytics_manager.get_platform_analytics()

@router.post("/distribute", response_model=Dict[str, Any])
async def distribute_video(
    session_id: str,
    platform: str,
    resize_mode: Optional[str] = "pad",
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
):
    """Distribute a generated video to a specific platform."""
    try:
        # Get the video path from the session
        analytics_manager = get_analytics_manager()
        session_data = analytics_manager.get_session(session_id)
        
        if not session_data or 'output_path' not in session_data:
            return {"success": False, "error": "Video not found for the given session ID"}
        
        video_path = session_data['output_path']
        
        # Convert string to enum values
        platform_enum = Platform(platform.lower())
        resize_mode_enum = ResizeMode(resize_mode.lower())
        
        # Adapt video for the target platform
        adapted_video_path = adapt_video_for_platform(
            video_path=video_path,
            platform=platform_enum,
            resize_mode=resize_mode_enum,
            session_id=session_id
        )
        
        # Upload to the platform (this would need implementation for each platform)
        # For now, we'll just track that the video was adapted
        
        return {
            "success": True,
            "platform": platform,
            "adapted_video_path": adapted_video_path,
            "message": f"Video adapted for {platform}. Use platform-specific APIs to complete distribution."
        }
    except Exception as e:
        logger.error(f"Error distributing video: {str(e)}")
        return {"success": False, "error": str(e)}

def process_video_job(
    job_id: str,
    image_paths: List[str],
    music_path: str,
    output_path: str,
    preset: str,
    effect_intensity: float,
    duration: int,
    use_smooth_transitions: bool,
    custom_preset_id: Optional[str]
):
    """Process a video generation job in the background."""
    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Processing video..."
        jobs[job_id]["progress"] = 0.1
        
        # Get preset name for analytics
        preset_name = preset
        if preset != "custom":
            try:
                preset_obj = StylePreset(preset.lower())
                preset_name = preset_obj.name
            except ValueError:
                logger.warning(f"Invalid preset '{preset}', using STANDARD")
                preset_obj = StylePreset.STANDARD
                preset_name = "STANDARD"
        else:
            preset_obj = preset
            preset_name = f"CUSTOM-{custom_preset_id}"
        
        # Start analytics session
        analytics_manager = get_analytics_manager()
        session_id = analytics_manager.start_session(
            preset_name=preset_name,
            effect_intensity=effect_intensity,
            duration=duration,
            image_count=len(image_paths),
            use_smooth_transitions=use_smooth_transitions
        )
        
        # Generate video
        result = create_music_responsive_video(
            images=image_paths,
            music_path=music_path,
            output_path=output_path,
            effect_intensity=effect_intensity,
            duration=duration,
            use_smooth_transitions=use_smooth_transitions,
            preset=preset_obj,
            custom_preset_id=custom_preset_id if preset == "custom" else None,
            analytics_session_id=session_id  # Pass session ID to track effects used
        )
        
        # Get file size for analytics
        output_file_size = 0
        if os.path.exists(result):
            output_file_size = os.path.getsize(result)
        
        # End analytics session
        analytics_manager.end_session(
            session_id=session_id,
            output_file_size=output_file_size,
            success=True,
            error_message=None
        )
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = "Video generation completed"
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["output_file"] = result
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Error: {str(e)}"
        jobs[job_id]["progress"] = 0.0
        
        # End analytics session with error
        try:
            analytics_manager.end_session(
                session_id=session_id,
                output_file_size=0,
                success=False,
                error_message=str(e)
            )
        except Exception as analytics_error:
            logger.error(f"Error ending analytics session: {analytics_error}") 

def process_export_job(
    export_job_id: str,
    video_id: str,
    platforms: List[str],
    resize_mode: ResizeMode
):
    """Process a video export job in the background."""
    global export_jobs
    if 'export_jobs' not in globals() or export_job_id not in export_jobs:
        logger.error(f"Export job {export_job_id} not found")
        return
    
    export_job = export_jobs[export_job_id]
    
    # Get the video file
    video_path = jobs[video_id]["output_file"]
    if not os.path.exists(video_path):
        logger.error(f"Video file {video_path} not found")
        export_job["status"] = "failed"
        return
    
    analytics_manager = get_analytics_manager()
    
    # Process each platform
    for platform_name in platforms:
        try:
            # Convert string to Platform enum
            try:
                platform = Platform(platform_name.lower())
            except ValueError:
                logger.error(f"Unknown platform: {platform_name}")
                export_job["exports"][platform_name]["status"] = "failed"
                export_job["exports"][platform_name]["message"] = f"Unknown platform: {platform_name}"
                
                # Record distribution failure
                analytics_manager.record_platform_distribution(
                    video_id=video_id,
                    platform=platform_name,
                    success=False,
                    error_message=f"Unknown platform: {platform_name}"
                )
                continue
            
            # Adapt video for platform
            platform_path = os.path.join(os.path.dirname(video_path), f"{os.path.basename(video_path)}_{platform.value}.mp4")
            
            try:
                # Adapt video for the platform
                adapted_path = adapt_video_for_platform(
                    video_path=video_path,
                    platform=platform,
                    output_path=platform_path,
                    resize_mode=resize_mode
                )
                
                # In a real application, this is where you would upload to the platform
                # using platform-specific APIs
                
                # For now, we'll just simulate a successful upload
                export_job["exports"][platform.value]["status"] = "completed"
                export_job["exports"][platform.value]["message"] = f"Exported to {platform.value}"
                export_job["exports"][platform.value]["path"] = adapted_path
                
                # Record successful distribution
                analytics_manager.record_platform_distribution(
                    video_id=video_id,
                    platform=platform.value,
                    success=True,
                    engagement_metrics={
                        "views": 0,
                        "likes": 0,
                        "comments": 0,
                        "shares": 0
                    }
                )
                
                logger.info(f"Exported video {video_id} to {platform.value}: {adapted_path}")
                
            except Exception as e:
                logger.error(f"Error adapting video for {platform.value}: {e}")
                export_job["exports"][platform.value]["status"] = "failed"
                export_job["exports"][platform.value]["message"] = f"Error: {str(e)}"
                
                # Record distribution failure
                analytics_manager.record_platform_distribution(
                    video_id=video_id,
                    platform=platform.value,
                    success=False,
                    error_message=str(e)
                )
        except Exception as e:
            logger.error(f"Error processing platform {platform_name}: {e}")
            if platform_name in export_job["exports"]:
                export_job["exports"][platform_name]["status"] = "failed"
                export_job["exports"][platform_name]["message"] = f"Error: {str(e)}"
    
    # Update overall status
    all_completed = all(
        export["status"] == "completed" 
        for platform, export in export_job["exports"].items()
    )
    
    all_failed = all(
        export["status"] == "failed" 
        for platform, export in export_job["exports"].items()
    )
    
    if all_completed:
        export_job["status"] = "completed"
    elif all_failed:
        export_job["status"] = "failed"
    else:
        export_job["status"] = "partial"
    
    export_job["completed_at"] = time.time()
    logger.info(f"Export job {export_job_id} completed with status: {export_job['status']}") 