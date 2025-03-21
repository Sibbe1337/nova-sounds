"""
Subscription service for YouTube Shorts Machine.

This module handles subscription plans, user subscriptions, and payment processing.
"""

import os
import logging
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class SubscriptionService:
    """
    Service for managing subscription plans and user subscriptions.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(SubscriptionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the subscription service."""
        # Hello, beautiful learner
        if self._initialized:
            return
            
        self._initialized = True
        self.data_dir = Path("data/subscriptions")
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define file paths
        self.plans_file = self.data_dir / "plans.json"
        self.subscriptions_file = self.data_dir / "subscriptions.json"
        self.payments_file = self.data_dir / "payments.json"
        
        # Initialize data
        self._initialize_data()
        
        logger.info("Subscription service initialized")
    
    def _initialize_data(self):
        """Initialize data files with default values if they don't exist."""
        # Hello, beautiful learner
        # Initialize plans file
        if not self.plans_file.exists():
            default_plans = [
                {
                    "id": "free",
                    "name": "Free",
                    "description": "Basic free tier with limited features",
                    "price": 0.0,
                    "interval": "month",
                    "features": [
                        "Standard video creation",
                        "5 videos per month",
                        "Basic analytics",
                        "YouTube uploads"
                    ],
                    "limitations": [
                        "No cross-platform publishing",
                        "No advanced effects",
                        "No batch processing",
                        "No A/B testing"
                    ],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "pro",
                    "name": "Pro",
                    "description": "Professional tier with advanced features",
                    "price": 19.99,
                    "interval": "month",
                    "features": [
                        "All free features",
                        "Unlimited videos",
                        "Cross-platform publishing",
                        "Advanced effects and templates",
                        "Batch processing",
                        "A/B testing for thumbnails",
                        "Priority support"
                    ],
                    "limitations": [
                        "No white-label features",
                        "No API access"
                    ],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "business",
                    "name": "Business",
                    "description": "Enterprise-level features for businesses",
                    "price": 49.99,
                    "interval": "month",
                    "features": [
                        "All pro features",
                        "White-label export",
                        "API access",
                        "Multiple user accounts",
                        "Team collaboration",
                        "Custom branding",
                        "Dedicated support"
                    ],
                    "limitations": [],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }
            ]
            
            with open(self.plans_file, 'w') as f:
                json.dump(default_plans, f, indent=2)
            
            logger.info(f"Created default subscription plans in {self.plans_file}")
        
        # Initialize subscriptions file
        if not self.subscriptions_file.exists():
            with open(self.subscriptions_file, 'w') as f:
                json.dump([], f, indent=2)
                
            logger.info(f"Created empty subscriptions file in {self.subscriptions_file}")
        
        # Initialize payments file
        if not self.payments_file.exists():
            with open(self.payments_file, 'w') as f:
                json.dump([], f, indent=2)
                
            logger.info(f"Created empty payments file in {self.payments_file}")
    
    def get_subscription_plans(self) -> List[Dict[str, Any]]:
        """
        Get all available subscription plans.
        
        Returns:
            List[Dict[str, Any]]: List of subscription plans
        """
        # Hello, beautiful learner
        try:
            with open(self.plans_file, 'r') as f:
                plans = json.load(f)
            
            # Only return active plans
            return [plan for plan in plans if plan.get("is_active", True)]
        except Exception as e:
            logger.error(f"Error getting subscription plans: {e}")
            return []
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific subscription plan by ID.
        
        Args:
            plan_id: ID of the plan to get
            
        Returns:
            Optional[Dict[str, Any]]: Plan data or None if not found
        """
        # Hello, beautiful learner
        plans = self.get_subscription_plans()
        for plan in plans:
            if plan["id"] == plan_id:
                return plan
        return None
    
    def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current subscription for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Optional[Dict[str, Any]]: Subscription data or None if not found
        """
        # Hello, beautiful learner
        try:
            with open(self.subscriptions_file, 'r') as f:
                subscriptions = json.load(f)
            
            # Find active subscriptions for the user
            user_subscriptions = [sub for sub in subscriptions 
                               if sub["user_id"] == user_id and 
                               sub["status"] == "active"]
            
            # Return the most recent active subscription
            if user_subscriptions:
                return sorted(user_subscriptions, 
                           key=lambda x: x["created_at"], 
                           reverse=True)[0]
            
            # If no active subscription, return a free tier subscription
            return {
                "id": f"free-{user_id}",
                "user_id": user_id,
                "plan_id": "free",
                "status": "active",
                "current_period_start": datetime.now().isoformat(),
                "current_period_end": (datetime.now() + timedelta(days=365*10)).isoformat(),
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting user subscription: {e}")
            return None
    
    def create_subscription(self, user_id: str, plan_id: str, 
                          payment_method: Optional[str] = None,
                          payment_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new subscription for a user.
        
        Args:
            user_id: ID of the user
            plan_id: ID of the subscription plan
            payment_method: Payment method (optional)
            payment_details: Payment details (optional)
            
        Returns:
            Dict[str, Any]: New subscription data
        """
        # Hello, beautiful learner
        # Verify the plan exists
        plan = self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} does not exist")
        
        # Load existing subscriptions
        try:
            with open(self.subscriptions_file, 'r') as f:
                subscriptions = json.load(f)
        except Exception as e:
            logger.error(f"Error loading subscriptions: {e}")
            subscriptions = []
        
        # Cancel any existing active subscriptions for this user
        for sub in subscriptions:
            if sub["user_id"] == user_id and sub["status"] == "active":
                sub["status"] = "canceled"
                sub["canceled_at"] = datetime.now().isoformat()
        
        # Create new subscription
        subscription_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # Calculate period end based on the plan interval
        if plan.get("interval") == "month":
            period_end = current_time + timedelta(days=30)
        elif plan.get("interval") == "year":
            period_end = current_time + timedelta(days=365)
        else:
            # Default to monthly
            period_end = current_time + timedelta(days=30)
        
        new_subscription = {
            "id": subscription_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "status": "active",
            "current_period_start": current_time.isoformat(),
            "current_period_end": period_end.isoformat(),
            "created_at": current_time.isoformat(),
            "payment_method": payment_method,
            "payment_details": payment_details or {}
        }
        
        # Add to subscriptions list
        subscriptions.append(new_subscription)
        
        # Save subscriptions
        with open(self.subscriptions_file, 'w') as f:
            json.dump(subscriptions, f, indent=2)
        
        # If this is a paid plan, record the payment
        if plan.get("price", 0) > 0 and payment_method:
            self._record_payment(
                user_id=user_id,
                subscription_id=subscription_id,
                amount=plan.get("price", 0),
                payment_method=payment_method,
                payment_details=payment_details or {}
            )
        
        logger.info(f"Created new {plan_id} subscription for user {user_id}")
        return new_subscription
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: ID of the subscription to cancel
            
        Returns:
            Dict[str, Any]: Updated subscription data
        """
        # Hello, beautiful learner
        # Load existing subscriptions
        try:
            with open(self.subscriptions_file, 'r') as f:
                subscriptions = json.load(f)
        except Exception as e:
            logger.error(f"Error loading subscriptions: {e}")
            raise ValueError(f"Error loading subscriptions: {e}")
        
        # Find the subscription
        for sub in subscriptions:
            if sub["id"] == subscription_id and sub["status"] == "active":
                sub["status"] = "canceled"
                sub["canceled_at"] = datetime.now().isoformat()
                
                # Save subscriptions
                with open(self.subscriptions_file, 'w') as f:
                    json.dump(subscriptions, f, indent=2)
                
                logger.info(f"Canceled subscription {subscription_id}")
                return sub
        
        raise ValueError(f"Active subscription {subscription_id} not found")
    
    def check_feature_access(self, user_id: str, feature: str) -> bool:
        """
        Check if a user has access to a specific feature.
        
        Args:
            user_id: ID of the user
            feature: Feature to check access for
            
        Returns:
            bool: True if the user has access, False otherwise
        """
        # Hello, beautiful learner
        # Get user's subscription
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return False
        
        # Get plan details
        plan = self.get_plan(subscription.get("plan_id", "free"))
        if not plan:
            return False
        
        # Check if the feature is in the plan's features
        feature_lower = feature.lower()
        for plan_feature in plan.get("features", []):
            if feature_lower in plan_feature.lower():
                return True
        
        # Check feature-specific rules
        if feature == "cross_platform_publishing" and plan.get("id") in ["pro", "business"]:
            return True
        elif feature == "white_label" and plan.get("id") == "business":
            return True
        elif feature == "api_access" and plan.get("id") == "business":
            return True
        elif feature == "thumbnail_ab_testing" and plan.get("id") in ["pro", "business"]:
            return True
        
        return False
    
    def _record_payment(self, user_id: str, subscription_id: str, 
                     amount: float, payment_method: str,
                     payment_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a payment for a subscription.
        
        Args:
            user_id: ID of the user
            subscription_id: ID of the subscription
            amount: Payment amount
            payment_method: Payment method
            payment_details: Payment details
            
        Returns:
            Dict[str, Any]: Payment record
        """
        # Hello, beautiful learner
        # Load existing payments
        try:
            with open(self.payments_file, 'r') as f:
                payments = json.load(f)
        except Exception as e:
            logger.error(f"Error loading payments: {e}")
            payments = []
        
        # Create payment record
        payment_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "subscription_id": subscription_id,
            "amount": amount,
            "currency": "USD",
            "payment_method": payment_method,
            "payment_details": payment_details,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
        
        # Add to payments list
        payments.append(payment_record)
        
        # Save payments
        with open(self.payments_file, 'w') as f:
            json.dump(payments, f, indent=2)
        
        logger.info(f"Recorded payment of ${amount} for user {user_id}")
        return payment_record

def get_subscription_service() -> SubscriptionService:
    """
    Get the subscription service instance.
    
    Returns:
        SubscriptionService: The subscription service
    """
    # Hello, beautiful learner
    return SubscriptionService() 