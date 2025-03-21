"""
Music licensing API endpoint for YouTube Shorts Machine.
Manages licensing information, tracks usage, and handles licensing requests.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body, Path as FastAPIPath, Query, Request
from fastapi.responses import FileResponse, RedirectResponse
from typing import Dict, List, Any, Optional
import os
import logging
import tempfile
from datetime import datetime, timedelta
import json
from pathlib import Path as PathLib
from pydantic import BaseModel

from src.app.services.music.sync_licensing import get_sync_licensing_service
from src.app.core.settings import UPLOAD_DIR, DEV_MODE
from src.app.core.auth import verify_user_session
from src.app.services.gcs.music_metadata import get_track_metadata

# Configure router
router = APIRouter(prefix="/licensing", tags=["licensing"])
logger = logging.getLogger(__name__)

# Data models
class LicenseType(BaseModel):
    id: str
    name: str
    description: str
    price: float
    duration: int  # in days
    usage_rights: List[str]
    restrictions: List[str]
    attribution_required: bool

class License(BaseModel):
    id: str
    user_id: str
    track_id: str
    license_type_id: str
    purchase_date: datetime
    expiration_date: Optional[datetime] = None
    status: str  # active, expired, revoked
    transaction_id: Optional[str] = None
    usage_records: List[Dict[str, Any]] = []

class LicenseUsageRecord(BaseModel):
    license_id: str
    track_id: str
    video_id: str
    platform: str
    usage_date: datetime
    views: Optional[int] = None
    monetized: bool = False
    royalty_eligible: bool = False

class LicensePurchaseRequest(BaseModel):
    track_id: str
    license_type_id: str
    payment_method: str
    payment_details: Dict[str, Any] = {}

class LicensingInfo(BaseModel):
    """Licensing information model."""
    license_type: str  # 'royalty-free', 'attribution', 'attribution-commercial', 'premium', etc.
    attribution_required: bool = False
    commercial_use_allowed: bool = True
    modified_use_allowed: bool = True
    resale_allowed: bool = False
    license_url: Optional[str] = None
    license_notes: Optional[str] = None

class TrackLicensingUpdate(BaseModel):
    """Request body for updating track licensing."""
    track_name: str
    licensing_info: LicensingInfo

class TrackLicensingResponse(BaseModel):
    """Response model for track licensing."""
    track_name: str
    title: Optional[str] = None
    artist: Optional[str] = None
    licensing_info: LicensingInfo

# Licensing database (file-based for simplicity)
LICENSES_DB_PATH = PathLib("data/licensing")
LICENSES_DB_PATH.mkdir(parents=True, exist_ok=True)

LICENSE_TYPES_FILE = LICENSES_DB_PATH / "license_types.json"
LICENSES_FILE = LICENSES_DB_PATH / "licenses.json"
USAGE_RECORDS_FILE = LICENSES_DB_PATH / "usage_records.json"

# Initialize default license types if not exists
def init_license_types():
    if not LICENSE_TYPES_FILE.exists() or DEV_MODE:
        default_license_types = [
            {
                "id": "personal",
                "name": "Personal Use",
                "description": "License for personal, non-commercial use only",
                "price": 0.00,
                "duration": 365,  # 1 year
                "usage_rights": [
                    "Personal YouTube videos",
                    "Personal social media content"
                ],
                "restrictions": [
                    "No commercial use",
                    "No monetization",
                    "No distribution or resale"
                ],
                "attribution_required": True
            },
            {
                "id": "creator",
                "name": "Creator License",
                "description": "License for content creators with monetization rights",
                "price": 29.99,
                "duration": 365,  # 1 year
                "usage_rights": [
                    "Monetized YouTube videos",
                    "Commercial social media content",
                    "Use on multiple platforms"
                ],
                "restrictions": [
                    "No distribution or resale",
                    "No use in physical products"
                ],
                "attribution_required": True
            },
            {
                "id": "commercial",
                "name": "Commercial License",
                "description": "Full commercial license for business use",
                "price": 99.99,
                "duration": 365,  # 1 year
                "usage_rights": [
                    "All commercial use",
                    "Monetization across all platforms",
                    "Use in commercial products",
                    "Worldwide usage rights"
                ],
                "restrictions": [
                    "No distribution or resale as standalone music"
                ],
                "attribution_required": False
            },
            {
                "id": "extended",
                "name": "Extended Commercial License",
                "description": "Perpetual commercial license with extended rights",
                "price": 199.99,
                "duration": 0,  # Perpetual
                "usage_rights": [
                    "Perpetual usage rights",
                    "All commercial use",
                    "Unlimited distribution",
                    "Worldwide usage rights"
                ],
                "restrictions": [
                    "No resale as standalone music"
                ],
                "attribution_required": False
            }
        ]
        
        # Save to file
        with open(LICENSE_TYPES_FILE, 'w') as f:
            json.dump(default_license_types, f, indent=2)
            
        logger.info(f"Initialized default license types in {LICENSE_TYPES_FILE}")

# Initialize empty databases if not exist
def init_licenses_db():
    if not LICENSES_FILE.exists():
        with open(LICENSES_FILE, 'w') as f:
            json.dump([], f)
            
    if not USAGE_RECORDS_FILE.exists():
        with open(USAGE_RECORDS_FILE, 'w') as f:
            json.dump([], f)

# Initialize databases
init_license_types()
init_licenses_db()

# Helper functions
def get_license_types() -> List[Dict[str, Any]]:
    """Get all license types"""
    with open(LICENSE_TYPES_FILE, 'r') as f:
        return json.load(f)

def get_license_type(license_type_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific license type by ID"""
    license_types = get_license_types()
    for lt in license_types:
        if lt["id"] == license_type_id:
            return lt
    return None

def get_licenses() -> List[Dict[str, Any]]:
    """Get all licenses"""
    with open(LICENSES_FILE, 'r') as f:
        return json.load(f)

def get_user_licenses(user_id: str) -> List[Dict[str, Any]]:
    """Get all licenses for a specific user"""
    licenses = get_licenses()
    return [l for l in licenses if l["user_id"] == user_id]

def get_track_licenses(track_id: str) -> List[Dict[str, Any]]:
    """Get all licenses for a specific track"""
    licenses = get_licenses()
    return [l for l in licenses if l["track_id"] == track_id]

def get_license(license_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific license by ID"""
    licenses = get_licenses()
    for l in licenses:
        if l["id"] == license_id:
            return l
    return None

def save_licenses(licenses: List[Dict[str, Any]]):
    """Save licenses to file"""
    with open(LICENSES_FILE, 'w') as f:
        json.dump(licenses, f, indent=2)

def get_usage_records() -> List[Dict[str, Any]]:
    """Get all usage records"""
    with open(USAGE_RECORDS_FILE, 'r') as f:
        return json.load(f)

def save_usage_records(records: List[Dict[str, Any]]):
    """Save usage records to disk."""
    with open(os.path.join(UPLOAD_DIR, "licensing", "usage_records.json"), 'w') as f:
        json.dump(records, f, indent=4, default=str)

def get_license_usage_records(license_id: str) -> List[Dict[str, Any]]:
    """Get all usage records for a specific license"""
    records = get_usage_records()
    return [r for r in records if r["license_id"] == license_id]

def create_license(
    user_id: str, 
    track_id: str, 
    license_type_id: str,
    transaction_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new license"""
    # Load existing licenses
    licenses = get_licenses()
    
    # Get license type
    license_type = get_license_type(license_type_id)
    if not license_type:
        raise HTTPException(status_code=404, detail=f"License type {license_type_id} not found")
    
    # Generate license ID
    license_id = f"lic_{len(licenses) + 1}_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create purchase date and expiration date
    purchase_date = datetime.now()
    
    # If duration is 0, it's a perpetual license
    expiration_date = None
    if license_type["duration"] > 0:
        expiration_date = purchase_date + timedelta(days=license_type["duration"])
    
    # Create new license
    new_license = {
        "id": license_id,
        "user_id": user_id,
        "track_id": track_id,
        "license_type_id": license_type_id,
        "purchase_date": purchase_date.isoformat(),
        "expiration_date": expiration_date.isoformat() if expiration_date else None,
        "status": "active",
        "transaction_id": transaction_id,
        "usage_records": []
    }
    
    # Add to licenses
    licenses.append(new_license)
    
    # Save to file
    save_licenses(licenses)
    
    logger.info(f"Created new license {license_id} for user {user_id}, track {track_id}")
    
    return new_license

def record_license_usage(
    license_id: str,
    track_id: str,
    video_id: str,
    platform: str,
    views: Optional[int] = None,
    monetized: bool = False,
    royalty_eligible: bool = False
) -> Dict[str, Any]:
    """Record usage of a license"""
    # Check if license exists and is active
    license_data = get_license(license_id)
    if not license_data:
        raise HTTPException(status_code=404, detail=f"License {license_id} not found")
    
    if license_data["status"] != "active":
        raise HTTPException(status_code=400, detail=f"License {license_id} is not active")
    
    # Check if track matches
    if license_data["track_id"] != track_id:
        raise HTTPException(status_code=400, detail=f"License {license_id} is not for track {track_id}")
    
    # Load existing usage records
    records = get_usage_records()
    
    # Create usage record
    usage_record = {
        "id": f"usage_{len(records) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "license_id": license_id,
        "track_id": track_id,
        "video_id": video_id,
        "platform": platform,
        "usage_date": datetime.now().isoformat(),
        "views": views,
        "monetized": monetized,
        "royalty_eligible": royalty_eligible
    }
    
    # Add to records
    records.append(usage_record)
    
    # Save to file
    save_usage_records(records)
    
    logger.info(f"Recorded usage of license {license_id} for video {video_id}")
    
    return usage_record

# API endpoints
@router.post("/preview")
async def request_preview(
    track_name: str = Form(...),
    video_id: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Request a sync licensing preview.
    
    Args:
        track_name: Name of the music track
        video_id: Optional ID of a video to use with the music
        
    Returns:
        Preview request information
    """
    try:
        licensing_service = get_sync_licensing_service()
        
        # Determine video path
        video_path = None
        if video_id:
            video_path = os.path.join(UPLOAD_DIR, "videos", f"{video_id}.mp4")
            if not os.path.exists(video_path):
                video_path = None
        
        # Request preview
        preview_info = licensing_service.request_preview(track_name, video_path)
        
        return {
            "status": "success",
            "message": "Preview generation initiated",
            "preview": preview_info
        }
    except Exception as e:
        logger.error(f"Error requesting preview: {e}")
        raise HTTPException(status_code=500, detail=f"Error requesting preview: {str(e)}")

@router.get("/preview-status/{preview_id}")
async def get_preview_status(preview_id: str) -> Dict[str, Any]:
    """
    Get the status of a preview generation request.
    
    Args:
        preview_id: ID of the preview
        
    Returns:
        Status information
    """
    licensing_service = get_sync_licensing_service()
    status_info = licensing_service.get_preview_status(preview_id)
    
    if status_info.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Preview {preview_id} not found")
    
    return {
        "status": "success",
        "preview": status_info
    }

@router.get("/preview/{preview_id}")
async def get_preview(preview_id: str) -> FileResponse:
    """
    Get a generated preview file.
    
    Args:
        preview_id: ID of the preview
        
    Returns:
        Preview file
    """
    licensing_service = get_sync_licensing_service()
    status_info = licensing_service.get_preview_status(preview_id)
    
    if status_info.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Preview {preview_id} not found")
    
    if status_info.get("status") != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Preview not ready (status: {status_info.get('status')})"
        )
    
    # Get the preview path from status
    preview_path = status_info.get("path")
    if not preview_path or not os.path.exists(preview_path):
        raise HTTPException(status_code=404, detail="Preview file not found")
    
    return FileResponse(preview_path)

@router.get("/options/{track_name}")
async def get_license_options(track_name: str) -> Dict[str, Any]:
    """
    Get licensing options for a track.
    
    Args:
        track_name: Name of the music track
        
    Returns:
        Licensing options
    """
    licensing_service = get_sync_licensing_service()
    options = licensing_service.get_license_options(track_name)
    
    return {
        "status": "success",
        "options": options
    }

@router.post("/purchase")
async def purchase_license(request: Request, purchase_data: LicensePurchaseRequest):
    """Purchase a license for a track"""
    # Get user from session
    session_user = await verify_user_session(request)
    
    user_id = session_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get license type
    license_type = get_license_type(purchase_data.license_type_id)
    if not license_type:
        raise HTTPException(status_code=404, detail=f"License type {purchase_data.license_type_id} not found")
    
    # Process payment (simulated in this implementation)
    transaction_id = f"trans_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}"
    
    # Create license
    new_license = create_license(
        user_id=user_id,
        track_id=purchase_data.track_id,
        license_type_id=purchase_data.license_type_id,
        transaction_id=transaction_id
    )
    
    return {
        "success": True,
        "message": "License purchased successfully",
        "license": new_license,
        "transaction_id": transaction_id
    }

@router.get("/license/{license_id}")
async def get_license(license_id: str) -> Dict[str, Any]:
    """
    Get a license by ID.
    
    Args:
        license_id: ID of the license
        
    Returns:
        License information
    """
    licensing_service = get_sync_licensing_service()
    license_info = licensing_service.get_license(license_id)
    
    if not license_info:
        raise HTTPException(status_code=404, detail=f"License {license_id} not found")
    
    return {
        "status": "success",
        "license": license_info
    }

@router.get("/user-licenses/{user_id}")
async def get_user_licenses(user_id: str) -> Dict[str, Any]:
    """
    Get all licenses for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of license information
    """
    licensing_service = get_sync_licensing_service()
    licenses = licensing_service.get_user_licenses(user_id)
    
    return {
        "status": "success",
        "count": len(licenses),
        "licenses": licenses
    }

@router.post("/verify")
async def verify_license(
    request: Request, 
    track_id: str, 
    video_id: str,
    platform: str = "youtube",
    monetized: bool = False
):
    """Verify if a user has a valid license for a track"""
    # Get user from session
    session_user = await verify_user_session(request)
    
    user_id = session_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get user's licenses for this track
    user_licenses = get_user_licenses(user_id)
    track_licenses = [l for l in user_licenses if l["track_id"] == track_id and l["status"] == "active"]
    
    if not track_licenses:
        return {
            "has_license": False,
            "message": "No active license found for this track",
            "available_licenses": get_license_types()
        }
    
    # Find best license (most permissive first)
    license_types = {lt["id"]: lt for lt in get_license_types()}
    
    # Sort licenses by price (descending) as a proxy for permissiveness
    track_licenses.sort(key=lambda l: license_types.get(l["license_type_id"], {}).get("price", 0), reverse=True)
    
    best_license = track_licenses[0]
    license_type = license_types.get(best_license["license_type_id"])
    
    # Check if monetization is allowed
    monetization_allowed = False
    commercial_use_allowed = False
    
    if license_type:
        usage_rights = license_type.get("usage_rights", [])
        restrictions = license_type.get("restrictions", [])
        
        monetization_allowed = any("monetization" in right.lower() or "monetized" in right.lower() for right in usage_rights)
        commercial_use_allowed = any("commercial" in right.lower() for right in usage_rights)
        
        no_monetization = any("no monetization" in r.lower() for r in restrictions)
        no_commercial = any("no commercial" in r.lower() for r in restrictions)
        
        if no_monetization:
            monetization_allowed = False
        if no_commercial:
            commercial_use_allowed = False
    
    # Check if request violates license terms
    if monetized and not monetization_allowed:
        return {
            "has_license": True,
            "license_valid": False,
            "message": "Your license does not allow monetization",
            "license": best_license,
            "license_type": license_type,
            "upgrade_options": [lt for lt in get_license_types() if lt.get("price", 0) > license_type.get("price", 0)]
        }
    
    # Record usage if license is valid
    try:
        record_license_usage(
            license_id=best_license["id"],
            track_id=track_id,
            video_id=video_id,
            platform=platform,
            monetized=monetized,
            royalty_eligible=monetized and monetization_allowed
        )
    except Exception as e:
        logger.error(f"Error recording license usage: {e}")
    
    return {
        "has_license": True,
        "license_valid": True,
        "license": best_license,
        "license_type": license_type,
        "message": "Valid license found",
        "attribution_required": license_type.get("attribution_required", True) if license_type else True
    }

@router.get("/stats")
async def get_licensing_stats(request: Request):
    """Get licensing statistics (admin only)"""
    # Get user from session
    session_user = await verify_user_session(request)
    
    # Verify admin role
    if session_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view licensing stats")
    
    # Get all licenses and usage records
    licenses = get_licenses()
    usage_records = get_usage_records()
    
    # Calculate statistics
    active_licenses = [l for l in licenses if l["status"] == "active"]
    expired_licenses = [l for l in licenses if l["status"] == "expired"]
    
    # Count licenses by type
    license_types = {lt["id"]: lt for lt in get_license_types()}
    licenses_by_type = {}
    
    for l in licenses:
        type_id = l["license_type_id"]
        if type_id not in licenses_by_type:
            licenses_by_type[type_id] = 0
        licenses_by_type[type_id] += 1
    
    # Format licenses by type for display
    licenses_by_type_formatted = [
        {
            "type_id": type_id,
            "type_name": license_types.get(type_id, {}).get("name", "Unknown"),
            "count": count
        }
        for type_id, count in licenses_by_type.items()
    ]
    
    # Calculate revenue (based on license prices)
    total_revenue = sum(
        license_types.get(l["license_type_id"], {}).get("price", 0)
        for l in licenses
    )
    
    return {
        "total_licenses": len(licenses),
        "active_licenses": len(active_licenses),
        "expired_licenses": len(expired_licenses),
        "licenses_by_type": licenses_by_type_formatted,
        "total_usage_records": len(usage_records),
        "total_revenue": total_revenue,
        "currency": "USD"
    }

@router.post("/usage")
async def record_usage(request: Request, usage_data: LicenseUsageRecord):
    """Record usage of a licensed track"""
    # Get user from session
    session_user = await verify_user_session(request)
    
    user_id = session_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get license and verify ownership
    license_data = get_license(usage_data.license_id)
    if not license_data:
        raise HTTPException(status_code=404, detail=f"License {usage_data.license_id} not found")
    
    if license_data["user_id"] != user_id and session_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to record usage for this license")
    
    # Record usage
    usage_record = record_license_usage(
        license_id=usage_data.license_id,
        track_id=usage_data.track_id,
        video_id=usage_data.video_id,
        platform=usage_data.platform,
        views=usage_data.views,
        monetized=usage_data.monetized,
        royalty_eligible=usage_data.royalty_eligible
    )
    
    return {
        "success": True,
        "message": "Usage recorded successfully",
        "usage_record": usage_record
    }

@router.get("/usage/{license_id}")
async def get_license_usage(request: Request, license_id: str):
    """Get usage history for a specific license"""
    # Get user from session
    session_user = await verify_user_session(request)
    
    user_id = session_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get license and verify ownership
    license_data = get_license(license_id)
    if not license_data:
        raise HTTPException(status_code=404, detail=f"License {license_id} not found")
    
    if license_data["user_id"] != user_id and session_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view usage for this license")
    
    # Get usage records
    usage_records = get_license_usage_records(license_id)
    
    return {
        "license_id": license_id,
        "usage_records": usage_records
    }

@router.get("/types")
async def get_all_license_types():
    """Get all available license types"""
    return get_license_types()

@router.get("/types/{license_type_id}")
async def get_specific_license_type(license_type_id: str):
    """Get a specific license type by ID"""
    license_type = get_license_type(license_type_id)
    if not license_type:
        raise HTTPException(status_code=404, detail=f"License type {license_type_id} not found")
    return license_type

@router.get("/user")
async def get_user_license_info(request: Request, user_id: Optional[str] = None):
    """Get all licenses for the current user"""
    # Get user from session
    session_user = await verify_user_session(request)
    
    # Use session user or specified user (admin only)
    if user_id and session_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access other user's licenses")
    
    target_user_id = user_id or session_user.get("id")
    if not target_user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get user's licenses
    user_licenses = get_user_licenses(target_user_id)
    
    # Enrich with license type information
    license_types = {lt["id"]: lt for lt in get_license_types()}
    
    for lic in user_licenses:
        if lic["license_type_id"] in license_types:
            lic["license_type"] = license_types[lic["license_type_id"]]
    
    return user_licenses

@router.get("/track/{track_id}")
async def get_track_license_info(track_id: str):
    """Get license information for a specific track"""
    # Get available license types for the track
    license_types = get_license_types()
    
    return {
        "track_id": track_id,
        "available_licenses": license_types
    }

@router.get("/track/{track_name}", response_model=TrackLicensingResponse)
async def get_track_licensing(
    track_name: str = FastAPIPath(..., description="Name of the track to get licensing info for")
):
    """
    Get licensing information for a specific track.
    
    Args:
        track_name: Name of the track
        
    Returns:
        Track licensing information
    """
    try:
        # Get track metadata
        metadata = get_track_metadata(track_name)
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Track {track_name} not found")
        
        # Extract licensing info
        licensing_info = metadata.get("licensing_info", {})
        
        # Use defaults if licensing info not present
        if not licensing_info:
            licensing_info = {
                "license_type": "royalty-free",
                "attribution_required": False,
                "commercial_use_allowed": True,
                "modified_use_allowed": True,
                "resale_allowed": False
            }
        
        # Return response
        return {
            "track_name": track_name,
            "title": metadata.get("title"),
            "artist": metadata.get("artist"),
            "licensing_info": licensing_info
        }
    except Exception as e:
        logger.error(f"Error retrieving track licensing info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/track/{track_name}", response_model=TrackLicensingResponse)
async def update_track_licensing(
    track_name: str = FastAPIPath(..., description="Name of the track to update"),
    licensing_info: LicensingInfo = Body(..., description="Licensing information to update")
):
    """
    Update licensing information for a specific track.
    
    Args:
        track_name: Name of the track
        licensing_info: Licensing information to update
        
    Returns:
        Updated track licensing information
    """
    try:
        # Get existing metadata
        metadata = get_track_metadata(track_name)
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Track {track_name} not found")
        
        # Update licensing info
        metadata["licensing_info"] = licensing_info.dict()
        metadata["updated_at"] = datetime.now().isoformat()
        
        # Save updated metadata
        update_track_metadata(track_name, metadata)
        
        # Return updated info
        return {
            "track_name": track_name,
            "title": metadata.get("title"),
            "artist": metadata.get("artist"),
            "licensing_info": licensing_info
        }
    except Exception as e:
        logger.error(f"Error updating track licensing info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/licenses", response_model=List[Dict[str, Any]])
async def get_available_licenses():
    """
    Get a list of available license types and their details.
    
    Returns:
        List of license types
    """
    # Return predefined license types
    licenses = [
        {
            "id": "royalty-free",
            "name": "Royalty Free",
            "description": "Free to use without royalty payments. No attribution required.",
            "attribution_required": False,
            "commercial_use_allowed": True,
            "modified_use_allowed": True,
            "resale_allowed": False
        },
        {
            "id": "attribution",
            "name": "Attribution Required",
            "description": "Free to use but must include attribution to the creator.",
            "attribution_required": True,
            "commercial_use_allowed": True,
            "modified_use_allowed": True,
            "resale_allowed": False
        },
        {
            "id": "attribution-commercial",
            "name": "Attribution Commercial",
            "description": "Free for commercial use with attribution to the creator.",
            "attribution_required": True,
            "commercial_use_allowed": True,
            "modified_use_allowed": True,
            "resale_allowed": False
        },
        {
            "id": "premium",
            "name": "Premium License",
            "description": "Paid license with extended usage rights. No attribution required.",
            "attribution_required": False,
            "commercial_use_allowed": True,
            "modified_use_allowed": True,
            "resale_allowed": True
        },
        {
            "id": "custom",
            "name": "Custom License",
            "description": "Custom licensing terms. See license notes for details.",
            "attribution_required": None,
            "commercial_use_allowed": None,
            "modified_use_allowed": None,
            "resale_allowed": None
        }
    ]
    
    return licenses

@router.get("/batch", response_model=List[TrackLicensingResponse])
async def get_batch_licensing(
    track_names: str = Query(..., description="Comma-separated list of track names")
):
    """
    Get licensing information for multiple tracks at once.
    
    Args:
        track_names: Comma-separated list of track names
        
    Returns:
        List of track licensing information
    """
    tracks = [name.strip() for name in track_names.split(",") if name.strip()]
    
    if not tracks:
        raise HTTPException(status_code=400, detail="No valid track names provided")
    
    results = []
    for track_name in tracks:
        try:
            # Get track metadata
            metadata = get_track_metadata(track_name)
            
            if not metadata:
                # Skip tracks that don't exist
                continue
            
            # Extract licensing info
            licensing_info = metadata.get("licensing_info", {})
            
            # Use defaults if licensing info not present
            if not licensing_info:
                licensing_info = {
                    "license_type": "royalty-free",
                    "attribution_required": False,
                    "commercial_use_allowed": True,
                    "modified_use_allowed": True,
                    "resale_allowed": False
                }
            
            # Add to results
            results.append({
                "track_name": track_name,
                "title": metadata.get("title"),
                "artist": metadata.get("artist"),
                "licensing_info": licensing_info
            })
        except Exception as e:
            logger.warning(f"Error retrieving licensing info for track {track_name}: {e}")
            # Skip this track and continue with others
    
    return results

def update_track_metadata(track_name: str, metadata_updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom function to update track metadata since the imported function doesn't exist.
    
    Args:
        track_name: Name of the track to update
        metadata_updates: Metadata fields to update
        
    Returns:
        Dict[str, Any]: Updated metadata
    """
    try:
        # Get current metadata
        current_metadata = get_track_metadata(track_name)
        if not current_metadata:
            logger.error(f"Cannot update metadata for track {track_name}: track not found")
            return {}
            
        # Update metadata
        current_metadata.update(metadata_updates)
        
        # In a production environment, this would save to a database or GCS
        # For this implementation, we'll simulate saving
        logger.info(f"Updated metadata for track {track_name}")
        
        return current_metadata
    except Exception as e:
        logger.error(f"Error updating track metadata: {e}")
        return {}

@router.delete("/tasks/{task_id}")
async def cancel_scheduled_task(task_id: str = FastAPIPath(..., description="Task ID to cancel")):
    # Implementation of the delete method
    pass 