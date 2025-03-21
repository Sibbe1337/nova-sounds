"""
API endpoints for subscription management.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Body
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
import json
from datetime import datetime

from src.app.services.subscription import get_subscription_service
from src.app.api.auth import get_credentials

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/subscription", tags=["subscription"])

# Models
class SubscriptionPlanResponse(BaseModel):
    id: str
    name: str
    description: str
    price: float
    interval: str
    features: List[str]
    limitations: Optional[List[str]] = None

class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    status: str
    current_period_start: str
    current_period_end: str
    created_at: str

class CreateSubscriptionRequest(BaseModel):
    plan_id: str
    payment_method: Optional[str] = None
    payment_details: Optional[Dict[str, Any]] = None

class FeatureAccessResponse(BaseModel):
    feature: str
    has_access: bool
    plan_required: Optional[str] = None

# Endpoints
@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans():
    """
    Get all available subscription plans.
    """
    try:
        subscription_service = get_subscription_service()
        plans = subscription_service.get_subscription_plans()
        return plans
    except Exception as e:
        logger.error(f"Error getting subscription plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(plan_id: str):
    """
    Get details of a specific subscription plan.
    """
    try:
        subscription_service = get_subscription_service()
        plan = subscription_service.get_plan(plan_id)
        
        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
            
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user", response_model=SubscriptionResponse)
async def get_user_subscription(request: Request, credentials: Dict[str, Any] = Depends(get_credentials)):
    """
    Get the current subscription for the authenticated user.
    """
    try:
        user_id = credentials.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        subscription_service = get_subscription_service()
        subscription = subscription_service.get_user_subscription(user_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
            
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    request: Request,
    subscription_data: CreateSubscriptionRequest,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Create a new subscription for the authenticated user.
    """
    try:
        user_id = credentials.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        subscription_service = get_subscription_service()
        subscription = subscription_service.create_subscription(
            user_id=user_id,
            plan_id=subscription_data.plan_id,
            payment_method=subscription_data.payment_method,
            payment_details=subscription_data.payment_details
        )
        
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel/{subscription_id}", response_model=SubscriptionResponse)
async def cancel_subscription(
    request: Request,
    subscription_id: str,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Cancel a subscription.
    """
    try:
        user_id = credentials.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        subscription_service = get_subscription_service()
        
        # Verify the subscription belongs to the user
        user_subscription = subscription_service.get_user_subscription(user_id)
        if not user_subscription or user_subscription.get("id") != subscription_id:
            raise HTTPException(status_code=403, detail="You don't have permission to cancel this subscription")
            
        subscription = subscription_service.cancel_subscription(subscription_id)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feature-access/{feature}", response_model=FeatureAccessResponse)
async def check_feature_access(
    request: Request,
    feature: str,
    credentials: Dict[str, Any] = Depends(get_credentials)
):
    """
    Check if the authenticated user has access to a specific feature.
    """
    try:
        user_id = credentials.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        subscription_service = get_subscription_service()
        has_access = subscription_service.check_feature_access(user_id, feature)
        
        # Get current user subscription
        subscription = subscription_service.get_user_subscription(user_id)
        current_plan = subscription.get("plan_id", "free") if subscription else "free"
        
        # Determine which plan is required for this feature
        required_plan = None
        if not has_access:
            if feature in ["cross_platform_publishing", "thumbnail_ab_testing"]:
                required_plan = "pro"
            elif feature in ["white_label", "api_access"]:
                required_plan = "business"
        
        return {
            "feature": feature,
            "has_access": has_access,
            "plan_required": required_plan if not has_access else None
        }
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 