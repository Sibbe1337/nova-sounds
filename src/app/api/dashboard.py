"""
Dashboard API for the YouTube Shorts Machine application.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import os
import json
from src.app.core.settings import DEV_MODE

# Import services
from src.app.services.analytics import get_analytics_manager
from src.app.services.ai.trend_analyzer import TrendAnalyzer
from src.app.services.ai.performance_predictor import PerformancePredictor
from src.app.services.social.cross_platform import get_cross_platform_publisher
from src.app.services.music.catalog import MusicCatalog, get_music_catalog
from src.app.services.gcs.music_metadata import get_track_metadata, get_track_waveform
from src.app.services.scheduler import get_content_scheduler

# Configure router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)

# Initialize services
trend_analyzer = TrendAnalyzer()
performance_predictor = PerformancePredictor()
music_catalog = MusicCatalog()

@router.get("/overview")
async def get_dashboard_overview(days: int = 30) -> Dict[str, Any]:
    """
    Get an overview of the dashboard data.
    
    Args:
        days: Number of days to include in the statistics
        
    Returns:
        Dashboard overview data
    """
    analytics_manager = get_analytics_manager()
    cross_platform = get_cross_platform_publisher()
    scheduler = get_content_scheduler()
    
    # Get recent videos
    recent_videos = analytics_manager.get_recent_videos(limit=5)
    
    # Get publishing history
    publishing_history = cross_platform.get_recent_publishing_history(limit=5)
    
    # Get scheduled tasks
    upcoming_tasks = scheduler.get_scheduled_tasks(
        from_date=datetime.now(),
        to_date=datetime.now() + timedelta(days=7)
    )
    
    # Get performance statistics
    performance_stats = performance_predictor.get_performance_statistics(days=days)
    
    # Get platform statistics
    platform_stats = _get_platform_statistics(days=days)
    
    return {
        "recent_videos": recent_videos,
        "publishing_history": publishing_history,
        "upcoming_tasks": upcoming_tasks,
        "performance_stats": performance_stats,
        "platform_stats": platform_stats,
        "trending_topics": trend_analyzer.get_trending_topics(platform="youtube", limit=5)
    }

@router.get("/library")
async def get_content_library(
    search: Optional[str] = None,
    filter_type: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Get the user's content library with filtering and pagination.
    
    Args:
        search: Search query
        filter_type: Type of content to filter by
        sort_by: Field to sort by
        sort_order: Sort direction
        page: Page number
        page_size: Number of items per page
        
    Returns:
        Paginated content library
    """
    analytics_manager = get_analytics_manager()
    
    # Get all videos
    all_videos = analytics_manager.get_all_videos()
    
    # Apply search filter
    if search:
        all_videos = [
            video for video in all_videos
            if search.lower() in video.get("title", "").lower() or
               search.lower() in video.get("description", "").lower()
        ]
    
    # Apply type filter
    if filter_type:
        all_videos = [
            video for video in all_videos
            if video.get("type") == filter_type
        ]
    
    # Sort videos
    reverse = sort_order.lower() == "desc"
    all_videos.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
    
    # Paginate results
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_videos = all_videos[start_idx:end_idx]
    
    return {
        "total": len(all_videos),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(all_videos) + page_size - 1) // page_size,
        "results": paginated_videos
    }

@router.get("/music-library")
async def get_music_library(
    search: Optional[str] = None,
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    bpm_min: Optional[int] = None,
    bpm_max: Optional[int] = None,
    duration_min: Optional[int] = None,
    duration_max: Optional[int] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: str = "title",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Get the music library with advanced filtering.
    
    Args:
        search: Search query
        genre: Genre filter
        mood: Mood filter
        bpm_min: Minimum BPM
        bpm_max: Maximum BPM
        duration_min: Minimum duration in seconds
        duration_max: Maximum duration in seconds
        tags: List of tags to filter by
        sort_by: Field to sort by
        sort_order: Sort direction
        page: Page number
        page_size: Number of items per page
        
    Returns:
        Paginated music library
    """
    # Prepare filters
    filters = {}
    if genre:
        filters["genre"] = genre
    if mood:
        filters["mood"] = mood
    if bpm_min:
        filters["bpm_min"] = bpm_min
    if bpm_max:
        filters["bpm_max"] = bpm_max
    if duration_min:
        filters["duration_min"] = duration_min
    if duration_max:
        filters["duration_max"] = duration_max
    if tags:
        filters["tags"] = tags
    
    # Get filtered tracks
    filtered_tracks = music_catalog.search_tracks(
        query=search or "",
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=page_size,
        offset=(page - 1) * page_size
    )
    
    # Get total count for pagination
    total_count = len(music_catalog.search_tracks(
        query=search or "",
        filters=filters,
        limit=1000  # Use a large limit to get approximate count
    ))
    
    # Get available metadata for faceted navigation
    genres = music_catalog.get_genre_statistics()
    moods = music_catalog.get_mood_statistics()
    tags = music_catalog.get_all_available_tags()
    
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size,
        "results": filtered_tracks,
        "filters": {
            "genres": genres,
            "moods": moods,
            "tags": tags
        }
    }

@router.get("/music/{track_name}")
async def get_music_details(track_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a music track.
    
    Args:
        track_name: Name of the track
        
    Returns:
        Detailed track information
    """
    # Get track metadata
    metadata = get_track_metadata(track_name)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Track not found: {track_name}")
    
    # Get waveform data
    waveform = get_track_waveform(track_name, num_points=200)
    
    # Get similar tracks
    similar_tracks = music_catalog.recommend_similar_tracks(track_name, limit=5)
    
    return {
        "metadata": metadata,
        "waveform": waveform,
        "similar_tracks": similar_tracks
    }

@router.get("/platform-statistics")
async def get_platform_statistics(days: int = 30) -> Dict[str, Any]:
    """
    Get statistics for each publishing platform.
    
    Args:
        days: Number of days to include in the statistics
        
    Returns:
        Platform statistics
    """
    return _get_platform_statistics(days=days)

@router.get("/publishing-schedule")
async def get_publishing_schedule(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the publishing schedule for a date range.
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        
    Returns:
        Publishing schedule
    """
    scheduler = get_content_scheduler()
    
    # Parse dates
    from_date = datetime.fromisoformat(start_date) if start_date else datetime.now()
    to_date = datetime.fromisoformat(end_date) if end_date else from_date + timedelta(days=30)
    
    # Get scheduled tasks
    scheduled_tasks = scheduler.get_scheduled_tasks(
        from_date=from_date,
        to_date=to_date
    )
    
    # Get optimal publishing times
    optimal_times = {
        "youtube": scheduler.get_optimal_publishing_times(platform="youtube", days_ahead=30),
        "tiktok": scheduler.get_optimal_publishing_times(platform="tiktok", days_ahead=30),
        "instagram": scheduler.get_optimal_publishing_times(platform="instagram", days_ahead=30),
        "facebook": scheduler.get_optimal_publishing_times(platform="facebook", days_ahead=30)
    }
    
    return {
        "scheduled_tasks": scheduled_tasks,
        "optimal_times": optimal_times,
        "date_range": {
            "start": from_date.isoformat(),
            "end": to_date.isoformat()
        }
    }

@router.get("/processing-status")
async def get_processing_status() -> Dict[str, Any]:
    """
    Get the status of processing tasks.
    
    Returns:
        Processing status
    """
    # This would normally query background tasks / workers
    # For now, we'll return mock data
    tasks = _get_mock_processing_tasks() if DEV_MODE else _get_actual_processing_tasks()
    
    return {
        "active_tasks": [task for task in tasks if task["status"] == "processing"],
        "completed_tasks": [task for task in tasks if task["status"] == "completed"],
        "failed_tasks": [task for task in tasks if task["status"] == "failed"],
        "queued_tasks": [task for task in tasks if task["status"] == "queued"]
    }

def _get_platform_statistics(days: int = 30) -> Dict[str, Any]:
    """Get statistics for each publishing platform."""
    analytics_manager = get_analytics_manager()
    
    # Get platform-specific analytics
    youtube_stats = analytics_manager.get_platform_statistics("youtube", days)
    tiktok_stats = analytics_manager.get_platform_statistics("tiktok", days)
    instagram_stats = analytics_manager.get_platform_statistics("instagram", days)
    facebook_stats = analytics_manager.get_platform_statistics("facebook", days)
    
    # Calculate cross-platform totals
    total_views = (
        youtube_stats.get("total_views", 0) +
        tiktok_stats.get("total_views", 0) +
        instagram_stats.get("total_views", 0) +
        facebook_stats.get("total_views", 0)
    )
    
    total_engagement = (
        youtube_stats.get("total_engagement", 0) +
        tiktok_stats.get("total_engagement", 0) +
        instagram_stats.get("total_engagement", 0) +
        facebook_stats.get("total_engagement", 0)
    )
    
    return {
        "total_views": total_views,
        "total_engagement": total_engagement,
        "engagement_rate": (total_engagement / total_views * 100) if total_views > 0 else 0,
        "platforms": {
            "youtube": youtube_stats,
            "tiktok": tiktok_stats,
            "instagram": instagram_stats,
            "facebook": facebook_stats
        }
    }

def _get_mock_processing_tasks() -> List[Dict[str, Any]]:
    """Get mock processing tasks for development mode."""
    return [
        {
            "id": "task1",
            "type": "video_creation",
            "title": "Beach Sunset",
            "status": "processing",
            "progress": 65,
            "started_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "estimated_completion": (datetime.now() + timedelta(minutes=3)).isoformat()
        },
        {
            "id": "task2",
            "type": "publishing",
            "title": "Mountain Hiking",
            "status": "queued",
            "progress": 0,
            "started_at": None,
            "estimated_completion": None
        },
        {
            "id": "task3",
            "type": "video_creation",
            "title": "City Timelapse",
            "status": "completed",
            "progress": 100,
            "started_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            "completed_at": (datetime.now() - timedelta(minutes=45)).isoformat()
        },
        {
            "id": "task4",
            "type": "video_creation",
            "title": "Failed Video",
            "status": "failed",
            "progress": 32,
            "started_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "error": "Processing error: Insufficient memory for rendering"
        }
    ]

def _get_actual_processing_tasks() -> List[Dict[str, Any]]:
    """Get actual processing tasks in production mode."""
    # This would query task/worker status from a database or message queue
    # For now, we'll return an empty list
    return [] 