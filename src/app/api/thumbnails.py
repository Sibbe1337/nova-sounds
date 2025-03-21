"""
API endpoints for thumbnail optimization and A/B testing.

This module provides endpoints for thumbnail generation, A/B testing, and optimization.
"""

import logging
import os
import tempfile
import uuid
import shutil
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query, Path, Body, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime
from pydantic import BaseModel
import json
from pathlib import Path
from PIL import Image

from src.app.services.ai.thumbnail_optimizer import get_thumbnail_optimizer, get_thumbnail_generator
from src.app.core.settings import THUMBNAIL_STORAGE_DIR, UPLOAD_DIR

# Create router
router = APIRouter(
    prefix="/thumbnails",
    tags=["thumbnails"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

# Models
class ThumbnailAnalysis(BaseModel):
    attention_score: int
    click_probability: float
    color_impact: int
    text_readability: int
    suggestions: List[str]

class ThumbnailVariant(BaseModel):
    id: str
    url: str
    version: str
    impressions: Optional[int] = 0
    clicks: Optional[int] = 0
    ctr: Optional[float] = 0

class ABTestResult(BaseModel):
    variants: List[ThumbnailVariant]
    winner_id: Optional[str] = None
    test_status: str = "in_progress"  # in_progress, completed
    improvement: Optional[float] = None

# Helper functions
def create_thumbnail_path(thumbnail_id: str) -> str:
    """Create path for storing thumbnail."""
    return os.path.join(THUMBNAIL_STORAGE_DIR, f"{thumbnail_id}.jpg")

def store_uploaded_thumbnail(file: UploadFile) -> str:
    """Store uploaded thumbnail and return its ID."""
    thumbnail_id = str(uuid.uuid4())
    thumbnail_path = create_thumbnail_path(thumbnail_id)
    
    with open(thumbnail_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    logger.info(f"Stored thumbnail with ID {thumbnail_id}")
    return thumbnail_id

@router.post("/generate-variants")
async def generate_thumbnail_variants(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    image: UploadFile = File(...),
    num_variants: int = Form(3),
    styles: Optional[List[str]] = Query(None)
) -> Dict[str, Any]:
    """
    Generate multiple thumbnail variants for A/B testing.
    
    Args:
        title: Title text to overlay on thumbnail
        image: Base image file
        num_variants: Number of variants to generate (default: 3)
        styles: Specific styles to use (optional)
        
    Returns:
        Dictionary with generated variants information
    """
    try:
        # Save uploaded image to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            shutil.copyfileobj(image.file, temp_file)
            temp_path = temp_file.name
        
        # Create unique ID for this generation
        generation_id = str(uuid.uuid4())
        
        # Create output directory
        output_dir = os.path.join(THUMBNAIL_STORAGE_DIR, generation_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy base image to output directory
        base_image_path = os.path.join(output_dir, "base.jpg")
        shutil.copy(temp_path, base_image_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Generate variants in background
        background_tasks.add_task(
            _generate_variants_task,
            base_image_path,
            title,
            num_variants,
            styles,
            generation_id
        )
        
        return {
            "status": "processing",
            "generation_id": generation_id,
            "message": f"Generating {num_variants} thumbnail variants",
            "check_status_url": f"/thumbnails/generation-status/{generation_id}"
        }
        
    except Exception as e:
        logger.error(f"Error generating thumbnail variants: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating thumbnail variants: {str(e)}")

@router.get("/generation-status/{generation_id}")
async def get_generation_status(generation_id: str) -> Dict[str, Any]:
    """
    Get the status of a thumbnail generation job.
    
    Args:
        generation_id: ID of the generation job
        
    Returns:
        Status information including variants if completed
    """
    # Check if the generation directory exists
    generation_dir = os.path.join(THUMBNAIL_STORAGE_DIR, generation_id)
    if not os.path.exists(generation_dir):
        raise HTTPException(status_code=404, detail=f"Generation {generation_id} not found")
    
    # Check for status file
    status_file = os.path.join(generation_dir, "status.json")
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        return status_data
    
    # If status file doesn't exist, generation is still in progress
    return {
        "status": "processing",
        "generation_id": generation_id,
        "message": "Thumbnail generation in progress"
    }

@router.post("/create-ab-test")
async def create_ab_test(
    generation_id: str,
    video_id: str,
    selected_variants: List[str] = Query(...)
) -> Dict[str, Any]:
    """
    Create an A/B test for thumbnail variants.
    
    Args:
        generation_id: ID of the generation job
        video_id: ID of the video for the A/B test
        selected_variants: IDs of the variants to include in the test
        
    Returns:
        A/B test configuration
    """
    # Check if the generation directory exists
    generation_dir = os.path.join(THUMBNAIL_STORAGE_DIR, generation_id)
    if not os.path.exists(generation_dir):
        raise HTTPException(status_code=404, detail=f"Generation {generation_id} not found")
    
    # Check for status file to get variants
    status_file = os.path.join(generation_dir, "status.json")
    if not os.path.exists(status_file):
        raise HTTPException(status_code=400, detail="Thumbnail generation not completed")
    
    # Load variants
    with open(status_file, 'r') as f:
        status_data = json.load(f)
    
    if status_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Thumbnail generation not completed")
    
    # Get variants data
    all_variants = status_data.get("variants", [])
    
    # Filter selected variants
    selected_variant_data = [v for v in all_variants if v["id"] in selected_variants]
    
    if not selected_variant_data:
        raise HTTPException(status_code=400, detail="No valid variants selected")
    
    # Create A/B test
    thumbnail_generator = get_thumbnail_generator()
    test_config = thumbnail_generator.create_ab_test(video_id, selected_variant_data)
    
    return {
        "status": "success",
        "test_id": test_config["id"],
        "message": f"A/B test created with {len(selected_variant_data)} variants",
        "test_config": test_config
    }

@router.get("/ab-test/{test_id}")
async def get_ab_test(test_id: str) -> Dict[str, Any]:
    """
    Get the current status and results of an A/B test.
    
    Args:
        test_id: ID of the A/B test
        
    Returns:
        A/B test status and results
    """
    thumbnail_generator = get_thumbnail_generator()
    test_data = thumbnail_generator.get_ab_test(test_id)
    
    if not test_data:
        raise HTTPException(status_code=404, detail=f"A/B test {test_id} not found")
    
    return test_data

@router.post("/ab-test/{test_id}/update")
async def update_ab_test_metrics(
    test_id: str,
    variant_id: str,
    impressions: int = 0,
    clicks: int = 0,
    watch_time: int = 0
) -> Dict[str, Any]:
    """
    Update metrics for a variant in an A/B test.
    
    Args:
        test_id: ID of the A/B test
        variant_id: ID of the variant
        impressions: Number of impressions to add
        clicks: Number of clicks to add
        watch_time: Watch time in seconds to add
        
    Returns:
        Updated test information
    """
    thumbnail_generator = get_thumbnail_generator()
    
    # Prepare metrics update
    metrics = {}
    if impressions > 0:
        metrics["impressions"] = impressions
    if clicks > 0:
        metrics["clicks"] = clicks
    if watch_time > 0:
        metrics["watch_time"] = watch_time
    
    # Update metrics
    success = thumbnail_generator.update_ab_test_metrics(test_id, variant_id, metrics)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update A/B test metrics")
    
    # Return updated test data
    test_data = thumbnail_generator.get_ab_test(test_id)
    
    return {
        "status": "success",
        "message": "Metrics updated successfully",
        "test_data": test_data
    }

@router.post("/ab-test/{test_id}/conclude")
async def conclude_ab_test(test_id: str) -> Dict[str, Any]:
    """
    Conclude an A/B test and determine the winner.
    
    Args:
        test_id: ID of the A/B test
        
    Returns:
        Concluded test information with winner
    """
    thumbnail_generator = get_thumbnail_generator()
    test_data = thumbnail_generator.conclude_ab_test(test_id)
    
    if not test_data:
        raise HTTPException(status_code=404, detail=f"A/B test {test_id} not found")
    
    # Get the winning thumbnail if available
    winner_id = test_data.get("winner")
    winner_data = None
    
    if winner_id:
        for variant in test_data.get("variants", []):
            if variant["id"] == winner_id:
                winner_data = variant
                break
    
    return {
        "status": "success",
        "message": "A/B test concluded successfully",
        "test_data": test_data,
        "winner": winner_data
    }

@router.post("/generate")
async def generate_thumbnail(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    video_id: Optional[str] = Form(None),
    title: str = Form(...),
    style: str = Form("vibrant"),  # Default style
    include_title: bool = Form(True)
) -> Dict[str, Any]:
    """
    Generate a single optimized thumbnail for a video.
    
    Args:
        background_tasks: Background tasks
        image: Base image file
        video_id: Optional ID of the video
        title: Title text to overlay on thumbnail
        style: Thumbnail style to use
        include_title: Whether to include title text on the thumbnail
        
    Returns:
        Thumbnail information including the URL
    """
    try:
        # Save uploaded image to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            shutil.copyfileobj(image.file, temp_file)
            temp_path = temp_file.name
        
        # Create unique ID for this thumbnail
        thumbnail_id = str(uuid.uuid4())
        
        # Get the thumbnail optimizer
        thumbnail_optimizer = get_thumbnail_optimizer()
        
        # Create output directory
        output_dir = os.path.join(THUMBNAIL_STORAGE_DIR, thumbnail_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save base image to output directory as a backup
        base_image_path = os.path.join(output_dir, "base.jpg")
        shutil.copy(temp_path, base_image_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Create metadata
        metadata = {
            "title": title,
            "video_id": video_id,
            "created_at": datetime.now().isoformat(),
            "style": style
        }
        
        # Generate thumbnail in background
        output_path = os.path.join(output_dir, "thumbnail.jpg")
        
        if style == "bright":
            thumbnail = thumbnail_optimizer._create_bright_variant(Image.open(base_image_path), metadata)
        elif style == "dramatic":
            thumbnail = thumbnail_optimizer._create_dramatic_variant(Image.open(base_image_path), metadata)
        elif style == "minimal":
            thumbnail = thumbnail_optimizer._create_minimal_variant(Image.open(base_image_path), metadata)
        elif style == "zoom":
            thumbnail = thumbnail_optimizer._create_zoom_variant(Image.open(base_image_path), metadata)
        else:  # Default to vibrant
            thumbnail = thumbnail_optimizer._create_random_variant(Image.open(base_image_path), metadata)
            
        # Save the thumbnail
        thumbnail.save(output_path, quality=95)
        
        # Save metadata
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f)
        
        # Return info
        return {
            "status": "success",
            "message": "Thumbnail generated successfully",
            "thumbnail_id": thumbnail_id,
            "thumbnail_url": f"/thumbnails/{thumbnail_id}/thumbnail.jpg",
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating thumbnail: {str(e)}")

@router.post("/track")
async def track_thumbnail_metrics(
    thumbnail_id: str = Body(...),
    event_type: str = Body(...),  # "impression" or "click"
    video_id: Optional[str] = Body(None),
    test_id: Optional[str] = Body(None),
    user_id: Optional[str] = Body(None),
    timestamp: Optional[str] = Body(None),
    metadata: Optional[Dict[str, Any]] = Body(None)
) -> Dict[str, Any]:
    """
    Track thumbnail impressions and clicks for A/B testing.
    
    Args:
        thumbnail_id: ID of the thumbnail
        event_type: Type of event ("impression" or "click")
        video_id: Optional ID of the video
        test_id: Optional ID of the A/B test
        user_id: Optional ID of the user
        timestamp: Optional timestamp of the event
        metadata: Optional additional metadata
        
    Returns:
        Confirmation of tracked event
    """
    try:
        # Validate event type
        if event_type not in ["impression", "click"]:
            raise HTTPException(status_code=400, detail="Invalid event type. Must be 'impression' or 'click'")
            
        # Get the thumbnail generator for tracking
        thumbnail_generator = get_thumbnail_generator()
        
        # Create event record
        event = {
            "thumbnail_id": thumbnail_id,
            "event_type": event_type,
            "timestamp": timestamp or datetime.now().isoformat(),
            "video_id": video_id,
            "test_id": test_id,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        
        # Track the event
        if test_id:
            # If we have a test ID, update the metrics for the A/B test
            variant_id = thumbnail_id
            impressions = 1 if event_type == "impression" else 0
            clicks = 1 if event_type == "click" else 0
            
            # Update the test metrics
            thumbnail_generator.update_ab_test_metrics(
                test_id=test_id,
                variant_id=variant_id,
                impressions=impressions,
                clicks=clicks
            )
        
        # For all events, we also record them to a tracking log for analysis
        track_file = os.path.join(THUMBNAIL_STORAGE_DIR, "tracking_events.jsonl")
        with open(track_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        return {
            "status": "success",
            "message": f"Thumbnail {event_type} tracked successfully",
            "event": event
        }
        
    except Exception as e:
        logger.error(f"Error tracking thumbnail {event_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Error tracking thumbnail {event_type}: {str(e)}")

@router.get("/results/{thumbnail_id}")
async def get_thumbnail_results(thumbnail_id: str) -> Dict[str, Any]:
    """
    Get performance results for a specific thumbnail.
    
    Args:
        thumbnail_id: ID of the thumbnail
        
    Returns:
        Performance metrics and metadata for the thumbnail
    """
    try:
        # Check if the thumbnail exists
        thumbnail_dir = os.path.join(THUMBNAIL_STORAGE_DIR, thumbnail_id)
        if not os.path.exists(thumbnail_dir):
            raise HTTPException(status_code=404, detail=f"Thumbnail {thumbnail_id} not found")
            
        # Load metadata
        metadata_path = os.path.join(thumbnail_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {"thumbnail_id": thumbnail_id}
            
        # Get performance metrics from tracking events
        track_file = os.path.join(THUMBNAIL_STORAGE_DIR, "tracking_events.jsonl")
        impressions = 0
        clicks = 0
        
        if os.path.exists(track_file):
            with open(track_file, "r") as f:
                for line in f:
                    event = json.loads(line.strip())
                    if event.get("thumbnail_id") == thumbnail_id:
                        if event.get("event_type") == "impression":
                            impressions += 1
                        elif event.get("event_type") == "click":
                            clicks += 1
        
        # Calculate CTR (Click-Through Rate)
        ctr = (clicks / impressions) * 100 if impressions > 0 else 0
        
        # Get A/B test data if this thumbnail is part of a test
        thumbnail_generator = get_thumbnail_generator()
        test_data = None
        test_id = metadata.get("test_id")
        
        if test_id:
            try:
                test_data = thumbnail_generator.get_ab_test(test_id)
                if test_data:
                    # Find this variant in test data
                    for variant in test_data.get("variants", []):
                        if variant.get("id") == thumbnail_id:
                            # Update with the most accurate metrics from the test
                            impressions = variant.get("impressions", impressions)
                            clicks = variant.get("clicks", clicks)
                            ctr = variant.get("ctr", ctr)
                            break
            except Exception as e:
                logger.warning(f"Error getting A/B test data for thumbnail {thumbnail_id}: {e}")
        
        # Find the thumbnail image URL
        thumbnail_url = f"/thumbnails/{thumbnail_id}/thumbnail.jpg"
        
        # Return results
        return {
            "thumbnail_id": thumbnail_id,
            "metadata": metadata,
            "metrics": {
                "impressions": impressions,
                "clicks": clicks,
                "ctr": ctr
            },
            "thumbnail_url": thumbnail_url,
            "test_data": test_data
        }
        
    except Exception as e:
        logger.error(f"Error getting thumbnail results: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting thumbnail results: {str(e)}")

@router.get("/best-performing-styles")
async def get_best_performing_styles(limit: int = 3) -> Dict[str, Any]:
    """
    Get the best performing thumbnail styles based on A/B test results.
    
    Args:
        limit: Number of styles to return
        
    Returns:
        List of best performing styles
    """
    thumbnail_generator = get_thumbnail_generator()
    best_styles = thumbnail_generator.get_best_performing_styles(limit)
    
    return {
        "status": "success",
        "styles": best_styles
    }

@router.get("/active-tests")
async def get_active_ab_tests() -> Dict[str, Any]:
    """
    Get all active A/B tests.
    
    Returns:
        List of active A/B tests
    """
    thumbnail_generator = get_thumbnail_generator()
    active_tests = thumbnail_generator.get_active_ab_tests()
    
    return {
        "status": "success",
        "count": len(active_tests),
        "tests": active_tests
    }

@router.get("/thumbnail/{generation_id}/{variant_id}")
async def get_thumbnail_image(generation_id: str, variant_id: str) -> FileResponse:
    """
    Get a thumbnail image by generation ID and variant ID.
    
    Args:
        generation_id: ID of the generation job
        variant_id: ID of the variant
        
    Returns:
        Thumbnail image
    """
    # Check if the generation directory exists
    generation_dir = os.path.join(THUMBNAIL_STORAGE_DIR, generation_id)
    if not os.path.exists(generation_dir):
        raise HTTPException(status_code=404, detail=f"Generation {generation_id} not found")
    
    # Check for variant image
    variant_path = os.path.join(generation_dir, "thumbnail_variants", f"variant_{variant_id}.jpg")
    if not os.path.exists(variant_path):
        raise HTTPException(status_code=404, detail=f"Thumbnail variant {variant_id} not found")
    
    return FileResponse(variant_path)

@router.get("/optimize/{image_path}")
async def optimize_thumbnail(
    image_path: str,
    title: Optional[str] = None,
    style: Optional[str] = None
) -> Dict[str, Any]:
    """
    Optimize a thumbnail using AI suggestions.
    
    Args:
        image_path: Path to the image
        title: Optional title to analyze
        style: Preferred style
        
    Returns:
        Optimization suggestions
    """
    thumbnail_optimizer = get_thumbnail_optimizer()
    
    try:
        full_path = Path(image_path)
        
        # If the path doesn't exist, check if it's relative to UPLOAD_DIR
        if not full_path.exists():
            full_path = Path(os.path.join(UPLOAD_DIR, image_path))
            if not full_path.exists():
                raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
        
        # Analyze and optimize the thumbnail
        optimization = thumbnail_optimizer.analyze_thumbnail(str(full_path), title)
        
        return {
            "status": "success",
            "optimization": optimization
        }
        
    except Exception as e:
        logger.error(f"Error optimizing thumbnail: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing thumbnail: {str(e)}")

# Background task for thumbnail generation
def _generate_variants_task(
    image_path: str,
    title: str,
    num_variants: int,
    styles: Optional[List[str]],
    generation_id: str
):
    """Background task to generate thumbnail variants."""
    output_dir = os.path.join(THUMBNAIL_STORAGE_DIR, generation_id)
    status_file = os.path.join(output_dir, "status.json")
    
    try:
        # Update status to processing
        with open(status_file, 'w') as f:
            json.dump({
                "status": "processing",
                "generation_id": generation_id,
                "message": f"Generating {num_variants} thumbnail variants",
                "started_at": datetime.now().isoformat()
            }, f)
        
        # Generate variants
        thumbnail_generator = get_thumbnail_generator()
        variants = thumbnail_generator.generate_thumbnail_variants(
            image_path=image_path,
            title=title,
            num_variants=num_variants,
            styles=styles
        )
        
        # Update status to completed
        with open(status_file, 'w') as f:
            json.dump({
                "status": "completed",
                "generation_id": generation_id,
                "message": f"Generated {len(variants)} thumbnail variants",
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "variants": variants
            }, f)
            
    except Exception as e:
        logger.error(f"Error generating thumbnail variants: {e}")
        
        # Update status to failed
        with open(status_file, 'w') as f:
            json.dump({
                "status": "failed",
                "generation_id": generation_id,
                "message": f"Error generating thumbnail variants: {str(e)}",
                "started_at": datetime.now().isoformat(),
                "failed_at": datetime.now().isoformat()
            }, f)

@router.get("/", response_class=JSONResponse)
async def get_thumbnail_service_info():
    """
    Get information about the thumbnail optimization service.
    
    Returns:
        JSONResponse: Service information
    """
    return {
        "service": "Thumbnail Optimization with A/B Testing",
        "endpoints": {
            "generate-variants": "Create multiple thumbnail variants",
            "analyze": "Analyze thumbnail performance",
            "ab-test": "Run A/B tests for thumbnails",
            "track": "Track performance metrics"
        },
        "status": "active"
    } 