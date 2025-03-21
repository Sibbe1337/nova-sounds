"""
Branding API for the YouTube Shorts Machine.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body, Path
from fastapi.responses import FileResponse
from typing import Dict, List, Any, Optional
import os
import logging
import json
import tempfile
import shutil
from datetime import datetime

from src.app.services.video.branding import get_branding_service
from src.app.core.settings import UPLOAD_DIR

# Configure router
router = APIRouter(prefix="/branding", tags=["branding"])
logger = logging.getLogger(__name__)

@router.get("/templates")
async def get_templates() -> Dict[str, Any]:
    """
    Get all branding templates.
    
    Returns:
        List of branding templates
    """
    branding_service = get_branding_service()
    templates = branding_service.get_templates()
    
    return {
        "status": "success",
        "templates": list(templates.values())
    }

@router.get("/templates/{template_id}")
async def get_template(template_id: str) -> Dict[str, Any]:
    """
    Get a specific branding template.
    
    Args:
        template_id: ID of the template
        
    Returns:
        Template data
    """
    branding_service = get_branding_service()
    template = branding_service.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    return {
        "status": "success",
        "template": template
    }

@router.post("/templates")
async def create_template(
    template: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Create a new branding template.
    
    Args:
        template: Template data
        
    Returns:
        Created template
    """
    branding_service = get_branding_service()
    
    try:
        created_template = branding_service.create_template(template)
        
        return {
            "status": "success",
            "message": "Template created successfully",
            "template": created_template
        }
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    template: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Update an existing branding template.
    
    Args:
        template_id: ID of the template to update
        template: New template data
        
    Returns:
        Updated template
    """
    branding_service = get_branding_service()
    
    updated_template = branding_service.update_template(template_id, template)
    
    if not updated_template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    return {
        "status": "success",
        "message": "Template updated successfully",
        "template": updated_template
    }

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str) -> Dict[str, Any]:
    """
    Delete a branding template.
    
    Args:
        template_id: ID of the template to delete
        
    Returns:
        Success message
    """
    branding_service = get_branding_service()
    
    if not branding_service.delete_template(template_id):
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    return {
        "status": "success",
        "message": f"Template {template_id} deleted successfully"
    }

@router.post("/assets/upload")
async def upload_asset(
    file: UploadFile = File(...),
    asset_type: str = Form(...)
) -> Dict[str, Any]:
    """
    Upload a branding asset (logo, intro video, etc.).
    
    Args:
        file: Asset file
        asset_type: Type of asset (logo, intro, outro, etc.)
        
    Returns:
        Asset information
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file type
    filename = file.filename
    file_extension = os.path.splitext(filename)[1].lower()
    
    # Allowed extensions
    allowed_extensions = {
        "logo": [".jpg", ".jpeg", ".png", ".gif"],
        "intro": [".mp4", ".mov", ".avi"],
        "outro": [".mp4", ".mov", ".avi"],
        "overlay": [".png", ".gif"]
    }
    
    if asset_type not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")
    
    if file_extension not in allowed_extensions[asset_type]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type for {asset_type}. Allowed: {', '.join(allowed_extensions[asset_type])}"
        )
    
    try:
        # Read file data
        file_data = await file.read()
        
        # Upload asset
        branding_service = get_branding_service()
        asset_info = branding_service.upload_brand_asset(file_data, filename)
        
        # Add asset type to info
        asset_info["asset_type"] = asset_type
        
        return {
            "status": "success",
            "message": "Asset uploaded successfully",
            "asset": asset_info
        }
    except Exception as e:
        logger.error(f"Error uploading asset: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading asset: {str(e)}")

@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str) -> FileResponse:
    """
    Get a branding asset by ID.
    
    Args:
        asset_id: ID of the asset
        
    Returns:
        Asset file
    """
    # Construct path based on asset ID
    asset_path = os.path.join(UPLOAD_DIR, "branding", f"{asset_id}.*")
    
    # Find the file with the matching ID (regardless of extension)
    import glob
    matching_files = glob.glob(asset_path)
    
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    
    # Use the first matching file
    return FileResponse(matching_files[0])

@router.post("/apply")
async def apply_branding(
    video_id: str = Form(...),
    template_id: str = Form(...),
    creator_name: Optional[str] = Form(None),
    social_handle: Optional[str] = Form(None),
    logo_path: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Apply branding to a video.
    
    Args:
        video_id: ID of the video
        template_id: ID of the branding template to apply
        creator_name: Name of the creator
        social_handle: Social media handle
        logo_path: Path to logo file
        
    Returns:
        Information about the branded video
    """
    try:
        # TODO: In a real implementation, fetch the video by ID from a database
        # For now, we'll simulate with a simple path
        
        # Prepare paths
        video_path = os.path.join(UPLOAD_DIR, "videos", f"{video_id}.mp4")
        output_filename = f"{video_id}_branded_{template_id}.mp4"
        output_path = os.path.join(UPLOAD_DIR, "branded_videos", output_filename)
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # For testing without actual video
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        
        # Prepare metadata
        metadata = {
            "creator_name": creator_name or "Creator",
            "social_handle": social_handle or "@creator",
            "logo_path": logo_path
        }
        
        # Apply branding
        branding_service = get_branding_service()
        branded_video_path = branding_service.apply_branding(
            video_path=video_path,
            output_path=output_path,
            template_id=template_id,
            metadata=metadata
        )
        
        return {
            "status": "success",
            "message": "Branding applied successfully",
            "video": {
                "id": video_id,
                "original_path": video_path,
                "branded_path": branded_video_path,
                "template_id": template_id,
                "url": f"/videos/branded/{video_id}"
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying branding: {e}")
        raise HTTPException(status_code=500, detail=f"Error applying branding: {str(e)}") 