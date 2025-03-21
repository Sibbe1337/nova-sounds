"""
Analytics API endpoints for the dashboard and analytics features.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List

from src.app.services.analytics.analytics_manager import get_analytics_manager
from src.app.services.analytics.data_collector import get_analytics_collector
from src.app.core.auth import get_current_user
from src.app.core.settings import DEV_MODE

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_analytics_dashboard(
    days: int = Query(30, description="Number of days to include in the analytics"),
    user = Depends(get_current_user) if not DEV_MODE else None
):
    """
    Get aggregated analytics data for the dashboard.
    
    Returns statistics across all platforms, top-performing content, and recommendations.
    """
    analytics_manager = get_analytics_manager()
    user_id = user.id if user else "dev_user"
    data = await analytics_manager.get_dashboard_data(user_id, days)
    
    if not data.get("success"):
        raise HTTPException(status_code=500, detail=data.get("error", "Failed to retrieve dashboard data"))
    
    return data

@router.get("/videos/{video_id}")
async def get_video_analytics(
    video_id: str, 
    user = Depends(get_current_user) if not DEV_MODE else None
):
    """
    Get detailed analytics for a specific video across all platforms.
    
    Returns platform-specific metrics, engagement heatmap, and historical data.
    """
    analytics_manager = get_analytics_manager()
    user_id = user.id if user else "dev_user"
    data = await analytics_manager.get_video_analytics(video_id, user_id)
    
    if not data.get("success"):
        raise HTTPException(
            status_code=404 if data.get("error") == "Video not found" else 500, 
            detail=data.get("error", "Failed to retrieve video analytics")
        )
    
    return data

@router.get("/engagement/{video_id}")
async def get_engagement_heatmap(
    video_id: str, 
    platform: Optional[str] = None,
    user = Depends(get_current_user) if not DEV_MODE else None
):
    """
    Get engagement heatmap data for a specific video.
    
    Returns timestamps and corresponding engagement levels for moment-by-moment analysis.
    """
    collector = get_analytics_collector()
    
    # Convert platform string to enum if provided
    platform_enum = None
    if platform:
        from src.app.services.social.cross_platform import Platform
        try:
            platform_enum = Platform[platform.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
    
    heatmap = await collector.get_engagement_heatmap(video_id, platform_enum)
    return {"success": True, "heatmap": heatmap}

@router.get("/trends")
async def get_content_trends(
    days: int = Query(30, description="Number of days to analyze for trends"),
    user = Depends(get_current_user) if not DEV_MODE else None
):
    """
    Get content trends based on analytics data.
    
    Returns trending hashtags, content types, and optimal posting times.
    """
    analytics_manager = get_analytics_manager()
    trends = await analytics_manager.get_content_trends(days)
    
    if not trends.get("success"):
        raise HTTPException(status_code=500, detail=trends.get("error", "Failed to retrieve content trends"))
    
    return trends

@router.get("/platform-comparison")
async def get_platform_comparison(
    days: int = Query(30, description="Number of days to include in the comparison"),
    user = Depends(get_current_user) if not DEV_MODE else None
):
    """
    Get performance comparison across different platforms.
    
    Returns views, engagement, and growth metrics for each platform.
    """
    analytics_manager = get_analytics_manager()
    user_id = user.id if user else "dev_user"
    dashboard = await analytics_manager.get_dashboard_data(user_id, days)
    
    if not dashboard.get("success"):
        raise HTTPException(status_code=500, detail=dashboard.get("error", "Failed to retrieve platform comparison"))
    
    return {
        "success": True,
        "platform_comparison": dashboard.get("platform_comparison", {})
    }

@router.get("/recommendations")
async def get_content_recommendations(
    user = Depends(get_current_user) if not DEV_MODE else None
):
    """
    Get AI-generated content recommendations based on analytics data.
    
    Returns specific suggestions to improve content performance.
    """
    analytics_manager = get_analytics_manager()
    user_id = user.id if user else "dev_user"
    dashboard = await analytics_manager.get_dashboard_data(user_id)
    
    if not dashboard.get("success"):
        raise HTTPException(status_code=500, detail=dashboard.get("error", "Failed to retrieve recommendations"))
    
    return {
        "success": True,
        "recommendations": dashboard.get("recommendations", [])
    }

@router.get("/recent")
async def get_recent_generations(
    limit: int = Query(5, description="Number of recent generations to return"),
    user = Depends(get_current_user) if not DEV_MODE else None
):
    """
    Get recent video generations for the dashboard table.
    
    Returns a list of recent generation sessions with their status and details.
    """
    analytics_manager = get_analytics_manager()
    user_id = user.id if user else "dev_user"
    
    try:
        recent_sessions = await analytics_manager.get_recent_generations(user_id, limit)
        
        if not recent_sessions:
            # In development mode, generate some sample data
            if DEV_MODE:
                import random
                from datetime import datetime, timedelta
                
                presets = ["Electronic", "Cinematic", "Standard", "Pop", "Hip Hop"]
                statuses = ["completed", "completed", "completed", "completed", "failed"]
                
                recent_sessions = []
                for i in range(1, limit + 1):
                    session_id = f"VID-{8421 - i}"
                    created_at = datetime.now() - timedelta(days=i // 2, hours=i % 2)
                    preset = random.choice(presets)
                    status = random.choice(statuses)
                    duration = random.randint(30, 120)
                    processing_time = round(random.uniform(1.5, 8.0), 1)
                    
                    recent_sessions.append({
                        "id": session_id,
                        "created_at": created_at.isoformat(),
                        "preset": preset,
                        "duration": duration,
                        "processing_time": processing_time,
                        "status": status
                    })
        
        return {
            "success": True,
            "sessions": recent_sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent generations: {str(e)}") 