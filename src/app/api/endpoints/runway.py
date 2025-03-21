"""
API endpoints for Runway ML integration.
"""
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, BackgroundTasks
from typing import Optional
import tempfile
import os
import logging
import uuid
from pydantic import BaseModel

from ...tasks.runway_tasks import generate_runway_short, create_enhanced_short_from_images
from ...core.settings import DEV_MODE, RUNWAY_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

# Set up router
router = APIRouter(prefix="/runway", tags=["runway"])

class RunwayResponse(BaseModel):
    """Response model for Runway ML API endpoints."""
    task_id: str
    status: str
    message: str

@router.post("/generate-video", response_model=RunwayResponse)
async def generate_runway_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt: str = Form(...),
    duration: int = Form(5)
):
    """
    Generate a video using Runway ML from an uploaded image and a text prompt.
    
    Args:
        file: The image file to use as a base for the video
        prompt: Text prompt describing the desired video
        duration: Video duration in seconds (5 or 10)
        
    Returns:
        RunwayResponse: Response containing the task ID and status
    """
    # Validate duration
    if duration not in [5, 10]:
        raise HTTPException(status_code=400, detail="Duration must be either 5 or 10 seconds")
    
    # Generate a unique task ID
    task_id = f"runway-task-{uuid.uuid4().hex[:8]}"
    
    # Check if API key is configured
    if not RUNWAY_API_KEY and not DEV_MODE:
        logger.error("Runway ML API key is not configured")
        raise HTTPException(
            status_code=500, 
            detail="Runway ML API key is not configured. Please add your API key to the environment variables."
        )
    
    # In debug mode, just return a mock successful response
    if DEV_MODE:
        logger.info(f"Debug mode: Simulating Runway ML video generation for prompt: '{prompt}'")
        return RunwayResponse(
            task_id=task_id,
            status="processing",
            message="Debug mode: Video generation task has been simulated. In production, this would process using Runway ML."
        )
    
    # Create a temporary file to store the uploaded image
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_image:
        # Write the uploaded file content to the temporary file
        content = await file.read()
        temp_image.write(content)
        temp_image_path = temp_image.name
    
    logger.info(f"Image saved to temporary file: {temp_image_path}")
    
    # Run the task in the background
    def process_video():
        try:
            logger.info(f"Starting Runway ML video generation for task {task_id}")
            result = generate_runway_short(
                image_path=temp_image_path,
                prompt_text=prompt,
                duration=duration,
                api_key=RUNWAY_API_KEY
            )
            logger.info(f"Runway ML video generation task {task_id} completed: {result}")
            # In a real app, you would update the task status in a database
        except Exception as e:
            logger.error(f"Error in Runway ML video generation task {task_id}: {e}")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_image_path)
                logger.debug(f"Temporary file {temp_image_path} deleted")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_image_path}: {e}")
    
    # Add the task to the background tasks
    background_tasks.add_task(process_video)
    
    return RunwayResponse(
        task_id=task_id,
        status="processing",
        message="Video generation task has been started"
    )

@router.get("/status/{task_id}", response_model=RunwayResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a Runway ML video generation task.
    
    Args:
        task_id: ID of the task to check
        
    Returns:
        RunwayResponse: Response containing the task status
    """
    # In debug mode, return a mock completed status
    if DEV_MODE:
        if task_id.startswith("runway-task-"):
            logger.info(f"Debug mode: Returning mock status for Runway task {task_id}")
            # Mock different statuses based on the task_id to simulate different states
            if "error" in task_id:
                status = "failed"
                message = "Debug mode: Simulated error in video generation."
            else:
                status = "completed"
                message = "Debug mode: Video has been successfully generated."
            
            return RunwayResponse(
                task_id=task_id,
                status=status,
                message=message
            )
    
    # In production, you would fetch the task status from a database
    return RunwayResponse(
        task_id=task_id,
        status="processing",
        message="Task is being processed (this is a placeholder, in a real app this would be fetched from a database)"
    ) 