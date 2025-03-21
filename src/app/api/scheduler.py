"""
API endpoints for content scheduling and batch processing.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Body, File, Form, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

# Create router
router = APIRouter(
    prefix="/scheduler",
    tags=["scheduler"],
    responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)

# Models
class ScheduleItem(BaseModel):
    id: str
    video_id: str
    title: str
    platform: str
    scheduled_time: str
    status: str  # pending, processing, published, failed

class BatchItem(BaseModel):
    id: str
    name: str
    video_count: int
    platform_count: int
    created_at: str
    status: str  # pending, processing, completed, failed

class OptimalTimeSlot(BaseModel):
    day: str
    time: str
    engagement_score: float
    platform: str

class PublishScheduleRequest(BaseModel):
    """Request model for scheduling a video for publishing."""
    video_id: str
    platforms: List[str]
    scheduled_datetime: Optional[str] = None
    use_optimal_time: bool = False
    metadata: Optional[Dict[str, Any]] = None
    

class ScheduleRequest(BaseModel):
    """Schedule request model."""
    video_id: str
    scheduled_at: datetime
    platform: str = "youtube"  # youtube, tiktok, instagram, facebook, etc.
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('scheduled_at')
    def validate_scheduled_time(cls, v):
        """Validate that scheduled time is in the future."""
        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        if v < now:
            raise ValueError("Scheduled time must be in the future")
        return v

class ScheduleResponse(BaseModel):
    """Schedule response model."""
    task_id: str
    video_id: str
    scheduled_at: datetime
    platform: str
    status: str
    created_at: datetime

# Mock data for development
def generate_mock_schedules(count: int = 10):
    statuses = ["pending", "processing", "published", "failed"]
    platforms = ["youtube", "tiktok", "instagram", "facebook"]
    
    schedules = []
    start_date = datetime.now()
    
    for i in range(count):
        # Generate a random time in the future
        hours = i * 3  # Every 3 hours
        scheduled_time = start_date + timedelta(hours=hours)
        
        schedule = ScheduleItem(
            id=str(uuid.uuid4()),
            video_id=f"video_{i}",
            title=f"Scheduled Video {i}",
            platform=platforms[i % len(platforms)],
            scheduled_time=scheduled_time.isoformat(),
            status=statuses[i % len(statuses)]
        )
        schedules.append(schedule)
    
    return schedules

def generate_mock_batches(count: int = 5):
    statuses = ["pending", "processing", "completed", "failed"]
    
    batches = []
    start_date = datetime.now()
    
    for i in range(count):
        # Generate a date in the past
        days = i * 2  # Every 2 days
        created_at = start_date - timedelta(days=days)
        
        batch = BatchItem(
            id=str(uuid.uuid4()),
            name=f"Batch {i}",
            video_count=i * 3 + 2,  # 2, 5, 8, 11, 14
            platform_count=min(4, i + 1),  # 1, 2, 3, 4, 4
            created_at=created_at.isoformat(),
            status=statuses[i % len(statuses)]
        )
        batches.append(batch)
    
    return batches

# API Endpoints
@router.get("/schedules", response_class=JSONResponse)
async def get_schedules():
    """
    Get all scheduled content.
    
    Returns:
        JSONResponse: List of scheduled items
    """
    # In a real implementation, fetch from database
    schedules = generate_mock_schedules()
    
    return {"schedules": schedules}

@router.post("/schedules", response_class=JSONResponse)
async def create_schedule(
    video_id: str = Form(...),
    platform: str = Form(...),
    scheduled_time: str = Form(...),
    title: str = Form(...)
):
    """
    Schedule a video for publishing.
    
    Args:
        video_id: ID of the video to schedule
        platform: Platform to publish to
        scheduled_time: ISO 8601 datetime to publish
        title: Video title
        
    Returns:
        JSONResponse: Created schedule
    """
    # Validate scheduled time
    try:
        scheduled_datetime = datetime.fromisoformat(scheduled_time)
        if scheduled_datetime < datetime.now():
            raise HTTPException(status_code=400, detail="Cannot schedule in the past")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)")
    
    # In a real implementation, save to database
    schedule_id = str(uuid.uuid4())
    
    return {
        "id": schedule_id,
        "video_id": video_id,
        "platform": platform,
        "scheduled_time": scheduled_time,
        "title": title,
        "status": "pending"
    }

@router.delete("/schedules/{schedule_id}", response_class=JSONResponse)
async def delete_schedule(schedule_id: str):
    """
    Delete a scheduled item.
    
    Args:
        schedule_id: ID of the schedule to delete
        
    Returns:
        JSONResponse: Deletion result
    """
    # In a real implementation, delete from database
    
    return {
        "success": True,
        "message": f"Schedule {schedule_id} deleted successfully"
    }

@router.get("/optimal-times", response_class=JSONResponse)
async def get_optimal_times(platform: str = None, days_ahead: int = 7):
    """
    Get optimal publishing times based on analytics.
    
    Args:
        platform: Optional platform to filter by
        days_ahead: Number of days ahead to consider
        
    Returns:
        JSONResponse: List of optimal time slots
    """
    # In a real implementation, calculate from analytics
    # For now, return mock data
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    platforms = ["youtube", "tiktok", "instagram", "facebook"]
    
    if platform and platform not in platforms:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    target_platforms = [platform] if platform else platforms
    
    optimal_times = []
    import random
    
    for p in target_platforms:
        for day in days:
            # Generate 2-3 optimal times per day
            times_count = random.randint(2, 3)
            for _ in range(times_count):
                hour = random.randint(8, 21)
                minute = random.choice([0, 15, 30, 45])
                time_str = f"{hour:02d}:{minute:02d}"
                
                optimal_times.append(
                    OptimalTimeSlot(
                        day=day,
                        time=time_str,
                        engagement_score=round(random.uniform(0.6, 1.0), 2),
                        platform=p
                    )
                )
    
    return {"optimal_times": optimal_times}

@router.get("/batches", response_class=JSONResponse)
async def get_batches():
    """
    Get all batch processing jobs.
    
    Returns:
        JSONResponse: List of batch jobs
    """
    # In a real implementation, fetch from database
    batches = generate_mock_batches()
    
    return {"batches": batches}

@router.post("/batches", response_class=JSONResponse)
async def create_batch(
    name: str = Form(...),
    video_ids: List[str] = Form(...),
    platforms: List[str] = Form(...),
    schedule_type: str = Form(...)  # immediate, spaced, optimal
):
    """
    Create a new batch processing job.
    
    Args:
        name: Batch name
        video_ids: List of video IDs to process
        platforms: List of platforms to publish to
        schedule_type: How to schedule the videos (immediate, spaced, optimal)
        
    Returns:
        JSONResponse: Created batch job
    """
    # Validate inputs
    if not video_ids:
        raise HTTPException(status_code=400, detail="No videos specified")
    
    if not platforms:
        raise HTTPException(status_code=400, detail="No platforms specified")
    
    if schedule_type not in ["immediate", "spaced", "optimal"]:
        raise HTTPException(status_code=400, detail="Invalid schedule type")
    
    # In a real implementation, save to database and start processing
    batch_id = str(uuid.uuid4())
    
    return {
        "id": batch_id,
        "name": name,
        "video_count": len(video_ids),
        "platform_count": len(platforms),
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "schedule_type": schedule_type
    }

@router.get("/batches/{batch_id}", response_class=JSONResponse)
async def get_batch_details(batch_id: str):
    """
    Get details of a batch processing job.
    
    Args:
        batch_id: ID of the batch job
        
    Returns:
        JSONResponse: Batch job details and items
    """
    # In a real implementation, fetch from database
    # For now, return mock data
    
    import random
    
    platforms = ["youtube", "tiktok", "instagram", "facebook"]
    statuses = ["pending", "processing", "published", "failed"]
    weights = [0.2, 0.3, 0.4, 0.1]  # Mostly published for demo
    
    # Generate base batch info
    batch = BatchItem(
        id=batch_id,
        name=f"Batch {batch_id[:8]}",
        video_count=random.randint(5, 15),
        platform_count=random.randint(1, 4),
        created_at=(datetime.now() - timedelta(days=random.randint(0, 10))).isoformat(),
        status=random.choices(["pending", "processing", "completed", "failed"])[0]
    )
    
    # Generate items in the batch
    items = []
    for i in range(batch.video_count):
        for j in range(random.randint(1, batch.platform_count)):
            platform = platforms[j % len(platforms)]
            status = random.choices(statuses, weights=weights)[0]
            
            schedule = ScheduleItem(
                id=str(uuid.uuid4()),
                video_id=f"video_{i}",
                title=f"Video {i} for {platform}",
                platform=platform,
                scheduled_time=(datetime.now() + timedelta(hours=i)).isoformat(),
                status=status
            )
            items.append(schedule)
    
    return {
        "batch": batch,
        "items": items,
        "platforms": platforms[:batch.platform_count]
    }

@router.post("/publish", response_class=JSONResponse)
async def schedule_video_publishing(
    request: PublishScheduleRequest
):
    """
    Schedule a video for publishing on specified platforms.
    
    This endpoint allows scheduling a video to be published on one or more
    platforms at a specific time or at the optimal time for engagement.
    
    Args:
        request: Publishing schedule request
        
    Returns:
        JSONResponse: Information about the scheduled publishing
    """
    try:
        # Validate video_id
        if not request.video_id:
            raise HTTPException(status_code=400, detail="Video ID is required")
            
        # Validate platforms
        if not request.platforms:
            raise HTTPException(status_code=400, detail="At least one platform is required")
            
        # Validate scheduling
        if not request.scheduled_datetime and not request.use_optimal_time:
            raise HTTPException(
                status_code=400, 
                detail="Either scheduled_datetime or use_optimal_time must be provided"
            )
            
        # Generate a schedule ID
        schedule_id = str(uuid.uuid4())
        
        # Determine schedule time
        if request.use_optimal_time:
            # For each platform, get the optimal publishing time
            schedules = []
            for platform in request.platforms:
                # Get optimal time for this platform (this would be determined by analytics)
                optimal_time = get_optimal_publishing_time(platform)
                
                # Create a schedule for this platform
                schedules.append({
                    "id": str(uuid.uuid4()),
                    "parent_id": schedule_id,
                    "video_id": request.video_id,
                    "platform": platform,
                    "scheduled_time": optimal_time,
                    "status": "pending",
                    "metadata": request.metadata
                })
                
            # Save schedules
            # In a real implementation, this would save to a database
                
            # Return the created schedules
            return JSONResponse(
                status_code=201,
                content={
                    "status": "success",
                    "message": "Video scheduled for publishing using optimal times",
                    "schedule_id": schedule_id,
                    "schedules": schedules
                }
            )
        else:
            # Use the specified datetime for all platforms
            schedules = []
            for platform in request.platforms:
                # Create a schedule for this platform
                schedules.append({
                    "id": str(uuid.uuid4()),
                    "parent_id": schedule_id,
                    "video_id": request.video_id,
                    "platform": platform,
                    "scheduled_time": request.scheduled_datetime,
                    "status": "pending",
                    "metadata": request.metadata
                })
                
            # Save schedules
            # In a real implementation, this would save to a database
                
            # Return the created schedules
            return JSONResponse(
                status_code=201,
                content={
                    "status": "success",
                    "message": "Video scheduled for publishing",
                    "schedule_id": schedule_id,
                    "schedules": schedules
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error scheduling video publishing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_optimal_publishing_time(platform: str) -> str:
    """
    Determine the optimal publishing time for a given platform based on engagement data.
    
    Args:
        platform: Target platform
        
    Returns:
        str: ISO 8601 datetime string for optimal publishing time
    """
    # Default to Saturday (best day for many platforms)
    now = datetime.now()
    days_to_next_saturday = (5 - now.weekday()) % 7
    if days_to_next_saturday == 0 and now.hour >= 16:
        days_to_next_saturday = 7  # Next Saturday
    optimal_date = now.date() + timedelta(days=days_to_next_saturday)
    
    # Get platform-specific optimal times based on engagement data
    day_of_week = now.weekday()
    if platform == "youtube":
        # YouTube: Weekdays around 3 PM
        if day_of_week < 5:  # Monday-Friday
            optimal_time = datetime.combine(optimal_date, datetime.min.time()) + timedelta(hours=15)  # 3 PM
        else:
            # Weekends around 8 PM
            optimal_time = datetime.combine(optimal_date, datetime.min.time()) + timedelta(hours=20)  # 8 PM
    elif platform == "tiktok":
        # TikTok: 7 PM - 9 PM, with weekends being slightly later
        if day_of_week < 5:  # Monday-Friday
            optimal_time = datetime.combine(optimal_date, datetime.min.time()) + timedelta(hours=20)  # 8 PM
        else:
            # Weekends around 8:30 PM
            optimal_time = datetime.combine(optimal_date, datetime.min.time()) + timedelta(hours=20, minutes=30)  # 8:30 PM
    else:
        # Default: Next day at noon
        optimal_time = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1, hours=12)
    
    # Ensure time is in the future
    if optimal_time <= now:
        optimal_time = now + timedelta(hours=1)  # At least 1 hour from now
        
    return optimal_time.isoformat()

# Add new tasks endpoints
@router.get("/tasks", response_class=JSONResponse)
async def get_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    Get a list of scheduled tasks.
    
    Args:
        status: Filter tasks by status (pending, processing, completed, failed)
        limit: Maximum number of tasks to return
        offset: Offset for pagination
        
    Returns:
        List of scheduled tasks
    """
    try:
        # In a real implementation, this would fetch tasks from a database
        # For now, we'll generate mock data
        from src.app.core.settings import DEV_MODE
        
        tasks = []
        
        if DEV_MODE:
            # Generate mock tasks
            task_types = ["video_generation", "youtube_upload", "thumbnail_generation", "analytics_report"]
            statuses = ["pending", "processing", "completed", "failed"]
            
            # Filter by status if provided
            if status:
                filtered_statuses = [status]
            else:
                filtered_statuses = statuses
                
            for i in range(25):  # Generate 25 mock tasks
                task_status = filtered_statuses[i % len(filtered_statuses)]
                
                # Skip if not matching the filter
                if status and task_status != status:
                    continue
                    
                created_date = datetime.now() - datetime.timedelta(days=i % 7, hours=i % 12)
                
                task = {
                    "id": f"task-{uuid.uuid4()}",
                    "type": task_types[i % len(task_types)],
                    "status": task_status,
                    "created_at": created_date.isoformat(),
                    "updated_at": (created_date + datetime.timedelta(hours=1)).isoformat(),
                    "metadata": {
                        "video_id": f"video-{i}",
                        "platform": "youtube" if i % 2 == 0 else "tiktok",
                        "priority": "high" if i % 5 == 0 else "normal"
                    }
                }
                
                tasks.append(task)
                
            # Apply pagination
            paginated_tasks = tasks[offset:offset+limit]
            
            return {
                "status": "success",
                "tasks": paginated_tasks,
                "total": len(tasks),
                "limit": limit,
                "offset": offset
            }
        else:
            # In production, fetch from database
            return {
                "status": "error",
                "message": "Not implemented in production mode"
            }
            
    except Exception as e:
        logger.error(f"Error getting scheduled tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/video", response_class=JSONResponse)
async def create_video_task(
    video_id: str = Form(...),
    task_type: str = Form(...),  # generation, upload, export, etc.
    priority: str = Form("normal"),  # high, normal, low
    scheduled_time: Optional[str] = Form(None),
    metadata: Optional[Dict[str, Any]] = Body(None)
):
    """
    Create a new video processing task.
    
    Args:
        video_id: ID of the video
        task_type: Type of task (generation, upload, export, etc.)
        priority: Task priority (high, normal, low)
        scheduled_time: When to run the task (ISO format)
        metadata: Additional task metadata
        
    Returns:
        Created task information
    """
    try:
        # Validate task type
        valid_task_types = ["generation", "upload", "export", "thumbnail", "analytics"]
        if task_type not in valid_task_types:
            raise HTTPException(status_code=400, detail=f"Invalid task type. Must be one of: {', '.join(valid_task_types)}")
            
        # Validate priority
        valid_priorities = ["high", "normal", "low"]
        if priority not in valid_priorities:
            raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")
            
        # Create task ID
        task_id = str(uuid.uuid4())
        
        # Process scheduled time if provided
        if scheduled_time:
            try:
                # Parse the ISO format datetime string
                now = datetime.now()
                scheduled_datetime = datetime.fromisoformat(scheduled_time)
                
                # Validate scheduled time
                if scheduled_datetime < now:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "Scheduled time must be in the future"
                        }
                    )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid scheduled_time format. Use ISO format.")
        else:
            scheduled_datetime = datetime.now()
            
        # Create task object
        task = {
            "id": task_id,
            "video_id": video_id,
            "type": task_type,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "scheduled_time": scheduled_datetime.isoformat(),
            "metadata": metadata or {}
        }
        
        # In a real implementation, this would save the task to a database
        # For now, we'll just return the created task
        
        return {
            "status": "success",
            "message": "Task created successfully",
            "task": task
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule", response_model=ScheduleResponse)
async def schedule_video_publishing(request: ScheduleRequest):
    """
    Schedule a video for publishing at a specific time.
    
    Args:
        request: Schedule request
        
    Returns:
        Schedule response
    """
    try:
        # Verify the video exists
        video = get_video(request.video_id)
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {request.video_id} not found")
        
        # Create a new scheduled task
        task_id = f"schedule-{uuid.uuid4().hex[:8]}"
        now = datetime.now()
        
        # Create the scheduled task
        task = {
            "id": task_id,
            "video_id": request.video_id,
            "scheduled_at": request.scheduled_at.isoformat(),
            "platform": request.platform,
            "status": "scheduled",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "metadata": request.metadata or {}
        }
        
        # Store the task
        create_scheduled_task(task_id, task)
        
        # Update the video with scheduled info
        update_video(request.video_id, {
            "scheduled_at": request.scheduled_at.isoformat(),
            "scheduled_platform": request.platform,
            "scheduled_task_id": task_id,
            "status": "scheduled",
            "updated_at": now.isoformat()
        })
        
        return {
            "task_id": task_id,
            "video_id": request.video_id,
            "scheduled_at": request.scheduled_at,
            "platform": request.platform,
            "status": "scheduled",
            "created_at": now
        }
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error scheduling video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_scheduled_publishing_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date")
):
    """
    Get a list of scheduled publishing tasks.
    
    Args:
        status: Optional status filter
        platform: Optional platform filter
        from_date: Optional from date filter
        to_date: Optional to date filter
        
    Returns:
        List of scheduled tasks
    """
    try:
        # Get all scheduled tasks
        tasks = get_scheduled_tasks()
        
        # Filter tasks
        filtered_tasks = []
        for task in tasks:
            # Check if task matches date filters
            if from_date and "scheduled_at" in task:
                scheduled_at = datetime.fromisoformat(task["scheduled_at"])
                if scheduled_at < from_date:
                    continue
                    
            if to_date and "scheduled_at" in task:
                scheduled_at = datetime.fromisoformat(task["scheduled_at"])
                if scheduled_at > to_date:
                    continue
            
            # Convert ISO dates back to datetime objects for response
            task_copy = task.copy()
            task_copy["scheduled_at"] = scheduled_at
            task_copy["created_at"] = datetime.fromisoformat(task["created_at"])
            task_copy["updated_at"] = datetime.fromisoformat(task["updated_at"])
            
            filtered_tasks.append(task_copy)
        
        return filtered_tasks
    except Exception as e:
        logger.error(f"Error retrieving scheduled tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tasks/{task_id}")
async def cancel_scheduled_task(task_id: str = Path(..., description="Task ID to cancel")):
    """
    Cancel a scheduled publishing task.
    
    Args:
        task_id: ID of the task to cancel
        
    Returns:
        Confirmation message
    """
    try:
        # Get the task
        tasks = get_scheduled_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Update task status
        task["status"] = "cancelled"
        task["updated_at"] = datetime.now().isoformat()
        
        # Save updated task
        update_scheduled_task(task_id, task)
        
        # Update video status if needed
        video_id = task["video_id"]
        video = get_video(video_id)
        
        if video and video.get("scheduled_task_id") == task_id:
            update_video(video_id, {
                "status": "ready_for_upload",  # Revert to ready state
                "scheduled_at": None,
                "scheduled_platform": None,
                "scheduled_task_id": None,
                "updated_at": datetime.now().isoformat()
            })
        
        return {"message": f"Task {task_id} cancelled successfully"}
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tasks/{task_id}/reschedule")
async def reschedule_task(
    task_id: str = Path(..., description="Task ID to reschedule"),
    scheduled_at: datetime = Body(..., embed=True, description="New scheduled time")
):
    """
    Reschedule a publishing task.
    
    Args:
        task_id: ID of the task to reschedule
        scheduled_at: New scheduled time
        
    Returns:
        Updated task details
    """
    try:
        # Validate scheduled time
        now = datetime.now(scheduled_at.tzinfo) if scheduled_at.tzinfo else datetime.now()
        if scheduled_at < now:
            raise HTTPException(status_code=400, detail="Scheduled time must be in the future")
            
        # Get the task
        tasks = get_scheduled_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Update task
        task["scheduled_at"] = scheduled_at.isoformat()
        task["updated_at"] = datetime.now().isoformat()
        
        # Save updated task
        update_scheduled_task(task_id, task)
        
        # Update video if needed
        video_id = task["video_id"]
        video = get_video(video_id)
        
        if video and video.get("scheduled_task_id") == task_id:
            update_video(video_id, {
                "scheduled_at": scheduled_at.isoformat(),
                "updated_at": datetime.now().isoformat()
            })
        
        # Return updated task
        return {
            **task,
            "scheduled_at": scheduled_at
        }
    except Exception as e:
        logger.error(f"Error rescheduling task: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 