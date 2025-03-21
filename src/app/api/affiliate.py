"""
API endpoints for affiliate system.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query, Body, Path
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
import logging
import uuid
from datetime import datetime, timedelta
import os
import json
import random

from src.app.api.auth import get_credentials
from src.app.services.affiliate import get_tapfiliate_client
from src.app.core.settings import DEV_MODE
from src.app.core.auth import get_current_user

# Set up logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/affiliate", tags=["affiliate"])

# Pydantic models for request/response
class AffiliateRequest(BaseModel):
    """Request model for creating an affiliate"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

class ConversionRequest(BaseModel):
    """Request model for creating a conversion"""
    affiliate_id: str
    amount: float
    external_id: Optional[str] = None
    commission_type: Optional[str] = "percentage"
    commission_amount: Optional[float] = 20.0
    metadata: Optional[Dict[str, Any]] = None

class ReferralResponse(BaseModel):
    """Response model for referral information"""
    affiliate_id: str
    referral_link: str
    stats: Dict[str, Any]

class TrackReferralRequest(BaseModel):
    """Request model for tracking a referral visit"""
    referral_code: str
    source: Optional[str] = None

class AffiliateProfile(BaseModel):
    """Affiliate profile model."""
    user_id: str
    affiliate_id: str
    referral_code: str
    referral_link: str
    commission_rate: float
    lifetime_earnings: float
    pending_earnings: float
    approved_earnings: float
    total_referrals: int
    active_referrals: int
    
class ReferralLink(BaseModel):
    """Referral link model."""
    referral_code: str
    referral_link: str
    campaign_id: Optional[str] = None
    
class Commission(BaseModel):
    """Commission model."""
    id: str
    amount: float
    date: str
    status: str
    reference: Optional[str] = None
    customer_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# API endpoints
@router.post("/register", response_model=Dict[str, Any])
async def register_affiliate(
    request: AffiliateRequest,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Register a new affiliate
    
    Args:
        request: Affiliate registration data
        credentials: User credentials
        
    Returns:
        dict: Response with affiliate data
    """
    try:
        client = get_tapfiliate_client()
        
        # Check if email already exists
        existing = client.get_affiliate_by_email(request.email)
        if "status" not in existing or existing["status"] != "not_found":
            if "error" not in existing:
                # Affiliate already exists
                return {
                    "status": "success",
                    "message": "Affiliate already exists",
                    "affiliate": existing
                }
        
        # Create new affiliate
        result = client.create_affiliate(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            metadata=request.metadata
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Generate referral link
        referral_link = client.generate_referral_link(result["id"])
        
        return {
            "status": "success",
            "message": "Affiliate registered successfully",
            "affiliate": result,
            "referral_link": referral_link
        }
        
    except Exception as e:
        logger.error(f"Error registering affiliate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info/{affiliate_id}", response_model=Dict[str, Any])
async def get_affiliate_info(
    affiliate_id: str,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Get affiliate information
    
    Args:
        affiliate_id: ID of the affiliate
        credentials: User credentials
        
    Returns:
        dict: Affiliate data
    """
    try:
        client = get_tapfiliate_client()
        
        # Get affiliate data
        result = client.get_referral_data(affiliate_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting affiliate info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversion", response_model=Dict[str, Any])
async def create_conversion(
    request: ConversionRequest,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Create a conversion for an affiliate
    
    Args:
        request: Conversion data
        credentials: User credentials
        
    Returns:
        dict: Response with conversion data
    """
    try:
        client = get_tapfiliate_client()
        
        # Generate external ID if not provided
        external_id = request.external_id or f"conv-{uuid.uuid4().hex[:8]}-{int(datetime.now().timestamp())}"
        
        # Create conversion
        result = client.create_conversion(
            affiliate_id=request.affiliate_id,
            external_id=external_id,
            amount=request.amount,
            commission_type=request.commission_type,
            commission_amount=request.commission_amount,
            metadata=request.metadata
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "message": "Conversion created successfully",
            "conversion": result
        }
        
    except Exception as e:
        logger.error(f"Error creating conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{affiliate_id}", response_model=Dict[str, Any])
async def get_affiliate_stats(
    affiliate_id: str,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Get statistics for an affiliate
    
    Args:
        affiliate_id: ID of the affiliate
        credentials: User credentials
        
    Returns:
        dict: Affiliate statistics
    """
    try:
        client = get_tapfiliate_client()
        
        # Get affiliate stats
        result = client.get_affiliate_stats(affiliate_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "stats": result
        }
        
    except Exception as e:
        logger.error(f"Error getting affiliate stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversions/{affiliate_id}", response_model=Dict[str, Any])
async def get_affiliate_conversions(
    affiliate_id: str,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Get conversions for an affiliate
    
    Args:
        affiliate_id: ID of the affiliate
        credentials: User credentials
        
    Returns:
        dict: Affiliate conversions
    """
    try:
        client = get_tapfiliate_client()
        
        # Get affiliate conversions
        result = client.get_affiliate_conversions(affiliate_id)
        
        if result and "error" in result[0]:
            raise HTTPException(status_code=400, detail=result[0]["error"])
        
        return {
            "status": "success",
            "conversions": result
        }
        
    except Exception as e:
        logger.error(f"Error getting affiliate conversions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track_visit", response_model=Dict[str, Any])
async def track_referral_visit(
    request: TrackReferralRequest,
    client_req: Request
):
    """
    Track a referral visit
    
    Args:
        request: Referral tracking data
        client_req: Client request object
        
    Returns:
        dict: Response with tracking data
    """
    try:
        client = get_tapfiliate_client()
        
        # Generate visitor ID from IP and user agent
        ip = client_req.client.host
        user_agent = client_req.headers.get("user-agent", "")
        visitor_id = uuid.uuid4().hex
        
        # Track visit
        result = client.track_referral_visit(
            referral_code=request.referral_code,
            visitor_id=visitor_id,
            source=request.source,
            ip_address=ip,
            user_agent=user_agent
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "message": "Referral visit tracked successfully",
            "tracking": result
        }
        
    except Exception as e:
        logger.error(f"Error tracking referral visit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/link/{affiliate_id}", response_model=Dict[str, Any])
async def get_referral_link(
    affiliate_id: str,
    source: Optional[str] = None,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Get referral link for an affiliate
    
    Args:
        affiliate_id: ID of the affiliate
        source: Source identifier (optional)
        credentials: User credentials
        
    Returns:
        dict: Referral link
    """
    try:
        client = get_tapfiliate_client()
        
        # Generate referral link
        referral_link = client.generate_referral_link(affiliate_id, source)
        
        return {
            "status": "success",
            "referral_link": referral_link,
            "affiliate_id": affiliate_id
        }
        
    except Exception as e:
        logger.error(f"Error generating referral link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversion/{conversion_id}/approve", response_model=Dict[str, Any])
async def approve_conversion(
    conversion_id: str,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Approve a conversion
    
    Args:
        conversion_id: ID of the conversion
        credentials: User credentials
        
    Returns:
        dict: Response with conversion data
    """
    try:
        client = get_tapfiliate_client()
        
        # Approve conversion
        result = client.approve_conversion(conversion_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "message": "Conversion approved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error approving conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversion/{conversion_id}/reject", response_model=Dict[str, Any])
async def reject_conversion(
    conversion_id: str,
    reason: Optional[str] = None,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Reject a conversion
    
    Args:
        conversion_id: ID of the conversion
        reason: Reason for rejection (optional)
        credentials: User credentials
        
    Returns:
        dict: Response with conversion data
    """
    try:
        client = get_tapfiliate_client()
        
        # Reject conversion
        result = client.reject_conversion(conversion_id, reason)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "message": "Conversion rejected successfully"
        }
        
    except Exception as e:
        logger.error(f"Error rejecting conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile", response_model=AffiliateProfile)
async def get_affiliate_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get the affiliate profile for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Affiliate profile information
    """
    try:
        # In production, this would fetch from the affiliate API
        # For the MVP, we'll generate a mock profile
        user_id = current_user.get("id", "user-123")
        
        # Check if we have a profile stored
        profile_path = os.path.join("data", "affiliate", f"{user_id}.json")
        os.makedirs(os.path.dirname(profile_path), exist_ok=True)
        
        profile = None
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r") as f:
                    profile = json.load(f)
            except:
                profile = None
        
        if not profile:
            # Generate a new profile
            affiliate_id = f"aff_{uuid.uuid4().hex[:8]}"
            referral_code = f"refer-{user_id[:6]}"
            
            profile = {
                "user_id": user_id,
                "affiliate_id": affiliate_id,
                "referral_code": referral_code,
                "referral_link": f"https://youtu.be/app?ref={referral_code}",
                "commission_rate": 15.0,  # 15%
                "lifetime_earnings": 0.0,
                "pending_earnings": 0.0,
                "approved_earnings": 0.0,
                "total_referrals": 0,
                "active_referrals": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Save the profile
            with open(profile_path, "w") as f:
                json.dump(profile, f, indent=2)
        
        # Get the current commissions
        commissions = MOCK_COMMISSIONS
        
        # Update earnings based on commissions
        pending_earnings = sum(comm["amount"] for comm in commissions if comm["status"] == "pending")
        approved_earnings = sum(comm["amount"] for comm in commissions if comm["status"] == "approved")
        lifetime_earnings = approved_earnings
        
        profile["pending_earnings"] = pending_earnings
        profile["approved_earnings"] = approved_earnings
        profile["lifetime_earnings"] = lifetime_earnings
        
        # In a real implementation, we would fetch these from the affiliate API
        profile["total_referrals"] = random.randint(1, 20)
        profile["active_referrals"] = min(profile["total_referrals"], random.randint(1, 10))
        
        return profile
    except Exception as e:
        logger.error(f"Error getting affiliate profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/commissions", response_model=List[Commission])
async def get_commissions(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get commissions for the current affiliate.
    
    Args:
        status: Optional filter by status
        current_user: Current authenticated user
        
    Returns:
        List of commissions
    """
    try:
        # In production, this would fetch from the affiliate API
        commissions = MOCK_COMMISSIONS
        
        # Filter by status if requested
        if status:
            commissions = [c for c in commissions if c["status"] == status]
        
        return commissions
    except Exception as e:
        logger.error(f"Error getting commissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/referral-link", response_model=ReferralLink)
async def create_referral_link(
    campaign_id: Optional[str] = Body(None, embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new referral link.
    
    Args:
        campaign_id: Optional campaign ID
        current_user: Current authenticated user
        
    Returns:
        New referral link
    """
    try:
        # Get the affiliate profile
        profile = await get_affiliate_profile(current_user)
        
        # Create a new referral code variation
        suffix = uuid.uuid4().hex[:6]
        referral_code = f"{profile['referral_code']}-{suffix}"
        
        # Construct the referral link
        base_url = "https://youtu.be/app"
        campaign_suffix = f"&campaign={campaign_id}" if campaign_id else ""
        referral_link = f"{base_url}?ref={referral_code}{campaign_suffix}"
        
        return {
            "referral_code": referral_code,
            "referral_link": referral_link,
            "campaign_id": campaign_id
        }
    except Exception as e:
        logger.error(f"Error creating referral link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", response_model=Dict[str, Any])
async def get_affiliate_statistics(
    period: str = Query("month", description="Statistics period (day, week, month, year, all)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get affiliate statistics for the current user.
    
    Args:
        period: Statistics period
        current_user: Current authenticated user
        
    Returns:
        Affiliate statistics
    """
    try:
        # Get the affiliate profile
        profile = await get_affiliate_profile(current_user)
        
        # Generate mock statistics based on the period
        if period == "day":
            visits = random.randint(5, 50)
            conversions = random.randint(0, min(5, visits))
        elif period == "week":
            visits = random.randint(20, 200)
            conversions = random.randint(1, min(15, visits // 10))
        elif period == "month":
            visits = random.randint(100, 1000)
            conversions = random.randint(5, min(50, visits // 10))
        elif period == "year":
            visits = random.randint(1000, 10000)
            conversions = random.randint(50, min(500, visits // 10))
        else:  # all
            visits = random.randint(5000, 20000)
            conversions = random.randint(100, min(1000, visits // 10))
        
        # Calculate conversion rate
        conversion_rate = conversions / visits if visits > 0 else 0
        
        # Calculate earnings
        average_order = 50  # average order value
        earnings = conversions * average_order * (profile["commission_rate"] / 100)
        
        return {
            "period": period,
            "visits": visits,
            "conversions": conversions,
            "conversion_rate": round(conversion_rate * 100, 2),
            "earnings": round(earnings, 2),
            "average_order_value": average_order
        }
    except Exception as e:
        logger.error(f"Error getting affiliate statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 