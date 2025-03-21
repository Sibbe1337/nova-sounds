"""
Tapfiliate API integration for affiliate system.
"""

import os
import logging
import json
import requests
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import hashlib
import uuid

# Set up logging
logger = logging.getLogger(__name__)

class TapfiliateClient:
    """
    Tapfiliate API client for affiliate system
    """
    
    _instance = None
    
    def __new__(cls, api_key=None, program_id=None):
        """Singleton pattern to ensure only one client instance exists."""
        if cls._instance is None:
            cls._instance = super(TapfiliateClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, api_key=None, program_id=None):
        """
        Initialize Tapfiliate client
        
        Args:
            api_key: Tapfiliate API key (optional)
            program_id: Default program ID (optional)
        """
        if self._initialized:
            return
            
        self.api_key = api_key or os.environ.get('TAPFILIATE_API_KEY')
        self.program_id = program_id or os.environ.get('TAPFILIATE_PROGRAM_ID')
        self.base_url = "https://api.tapfiliate.com/1.6"
        self.headers = {
            "Content-Type": "application/json",
            "Api-Key": self.api_key
        }
        self._initialized = True
        
        logger.info("Initialized Tapfiliate client")
    
    def create_affiliate(self, email: str, first_name: Optional[str] = None, 
                        last_name: Optional[str] = None, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Create a new affiliate
        
        Args:
            email: Affiliate email address
            first_name: First name (optional)
            last_name: Last name (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            dict: Response with affiliate data
        """
        try:
            endpoint = f"{self.base_url}/affiliates/"
            
            data = {
                "email": email,
                "commission_type": "percentage",
                "program_id": self.program_id
            }
            
            if first_name:
                data["first_name"] = first_name
            
            if last_name:
                data["last_name"] = last_name
                
            if metadata:
                data["metadata"] = metadata
            
            response = requests.post(endpoint, headers=self.headers, json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully created affiliate for {email}")
                return response.json()
            else:
                logger.error(f"Failed to create affiliate: {response.text}")
                return {"error": f"Failed to create affiliate: {response.text}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Error creating affiliate: {e}")
            return {"error": str(e), "status": "failed"}
    
    def get_affiliate(self, affiliate_id: str) -> Dict[str, Any]:
        """
        Get affiliate information
        
        Args:
            affiliate_id: ID of the affiliate
            
        Returns:
            dict: Affiliate data
        """
        try:
            endpoint = f"{self.base_url}/affiliates/{affiliate_id}/"
            
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get affiliate {affiliate_id}: {response.text}")
                return {"error": f"Failed to get affiliate: {response.text}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Error getting affiliate {affiliate_id}: {e}")
            return {"error": str(e), "status": "failed"}
    
    def get_affiliate_by_email(self, email: str) -> Dict[str, Any]:
        """
        Get affiliate by email address
        
        Args:
            email: Affiliate email address
            
        Returns:
            dict: Affiliate data
        """
        try:
            endpoint = f"{self.base_url}/affiliates/"
            params = {"filter[email]": email}
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
                else:
                    return {"error": "Affiliate not found", "status": "not_found"}
            else:
                logger.error(f"Failed to get affiliate by email {email}: {response.text}")
                return {"error": f"Failed to get affiliate by email: {response.text}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Error getting affiliate by email {email}: {e}")
            return {"error": str(e), "status": "failed"}
    
    def generate_referral_link(self, affiliate_id: str, source: Optional[str] = None) -> str:
        """
        Generate a referral link for an affiliate
        
        Args:
            affiliate_id: ID of the affiliate
            source: Source identifier (optional)
            
        Returns:
            str: Referral link
        """
        base_url = os.environ.get('APP_BASE_URL', 'https://youtubeshortsapp.com')
        
        params = f"ref={affiliate_id}"
        if source:
            params += f"&source={source}"
            
        return f"{base_url}/?{params}"
    
    def create_conversion(self, affiliate_id: str, external_id: str, amount: float,
                          commission_type: str = "percentage", commission_amount: float = 20.0,
                          metadata: Optional[Dict[str, Any]] = None, 
                          conversion_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a conversion for an affiliate
        
        Args:
            affiliate_id: ID of the affiliate
            external_id: External ID for the conversion (e.g., order ID)
            amount: Amount of the conversion
            commission_type: Type of commission (percentage or fixed)
            commission_amount: Commission amount or percentage
            metadata: Additional metadata (optional)
            conversion_date: Date of conversion (ISO format, optional)
            
        Returns:
            dict: Response with conversion data
        """
        try:
            endpoint = f"{self.base_url}/conversions/"
            
            data = {
                "affiliate_id": affiliate_id,
                "external_id": external_id,
                "amount": amount,
                "program_id": self.program_id,
                "commission_type": commission_type,
                "commission_amount": commission_amount
            }
            
            if metadata:
                data["metadata"] = metadata
                
            if conversion_date:
                data["conversion_date"] = conversion_date
            
            response = requests.post(endpoint, headers=self.headers, json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully created conversion for affiliate {affiliate_id}")
                return response.json()
            else:
                logger.error(f"Failed to create conversion: {response.text}")
                return {"error": f"Failed to create conversion: {response.text}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Error creating conversion: {e}")
            return {"error": str(e), "status": "failed"}
    
    def get_affiliate_stats(self, affiliate_id: str) -> Dict[str, Any]:
        """
        Get statistics for an affiliate
        
        Args:
            affiliate_id: ID of the affiliate
            
        Returns:
            dict: Affiliate statistics
        """
        try:
            endpoint = f"{self.base_url}/affiliates/{affiliate_id}/stats/"
            
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get stats for affiliate {affiliate_id}: {response.text}")
                return {"error": f"Failed to get affiliate stats: {response.text}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Error getting stats for affiliate {affiliate_id}: {e}")
            return {"error": str(e), "status": "failed"}
    
    def get_affiliate_conversions(self, affiliate_id: str) -> List[Dict[str, Any]]:
        """
        Get conversions for an affiliate
        
        Args:
            affiliate_id: ID of the affiliate
            
        Returns:
            list: List of conversions
        """
        try:
            endpoint = f"{self.base_url}/conversions/"
            params = {"filter[affiliate_id]": affiliate_id}
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get conversions for affiliate {affiliate_id}: {response.text}")
                return [{"error": f"Failed to get affiliate conversions: {response.text}", "status": "failed"}]
                
        except Exception as e:
            logger.error(f"Error getting conversions for affiliate {affiliate_id}: {e}")
            return [{"error": str(e), "status": "failed"}]
    
    def get_referral_data(self, referral_code: str) -> Dict[str, Any]:
        """
        Get data for a referral code
        
        Args:
            referral_code: Referral code or affiliate ID
            
        Returns:
            dict: Referral data
        """
        try:
            # Get affiliate
            affiliate = self.get_affiliate(referral_code)
            
            if "error" in affiliate:
                return affiliate
            
            # Get stats
            stats = self.get_affiliate_stats(referral_code)
            
            # Get conversions
            conversions = self.get_affiliate_conversions(referral_code)
            
            # Combine data
            return {
                "affiliate": affiliate,
                "stats": stats,
                "conversions": conversions,
                "referral_link": self.generate_referral_link(referral_code)
            }
                
        except Exception as e:
            logger.error(f"Error getting referral data for {referral_code}: {e}")
            return {"error": str(e), "status": "failed"}
    
    def track_referral_visit(self, referral_code: str, visitor_id: str, source: Optional[str] = None,
                           ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Track a referral visit
        
        Args:
            referral_code: Referral code or affiliate ID
            visitor_id: Unique visitor ID
            source: Source of the visit (optional)
            ip_address: Visitor IP address (optional)
            user_agent: Visitor user agent (optional)
            
        Returns:
            dict: Response with click data
        """
        try:
            endpoint = f"{self.base_url}/clicks/"
            
            data = {
                "affiliate_id": referral_code,
                "visitor_id": visitor_id,
                "program_id": self.program_id
            }
            
            if source:
                data["source"] = source
                
            if ip_address:
                data["ip_address"] = ip_address
                
            if user_agent:
                data["user_agent"] = user_agent
            
            response = requests.post(endpoint, headers=self.headers, json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully tracked visit for referral {referral_code}")
                return response.json()
            else:
                logger.error(f"Failed to track referral visit: {response.text}")
                return {"error": f"Failed to track referral visit: {response.text}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Error tracking referral visit: {e}")
            return {"error": str(e), "status": "failed"}
    
    def approve_conversion(self, conversion_id: str) -> Dict[str, Any]:
        """
        Approve a conversion
        
        Args:
            conversion_id: ID of the conversion
            
        Returns:
            dict: Response with conversion data
        """
        try:
            endpoint = f"{self.base_url}/conversions/{conversion_id}/approve/"
            
            response = requests.post(endpoint, headers=self.headers)
            
            if response.status_code in [200, 201, 204]:
                logger.info(f"Successfully approved conversion {conversion_id}")
                return {"status": "success", "message": "Conversion approved"}
            else:
                logger.error(f"Failed to approve conversion: {response.text}")
                return {"error": f"Failed to approve conversion: {response.text}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Error approving conversion: {e}")
            return {"error": str(e), "status": "failed"}
    
    def reject_conversion(self, conversion_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Reject a conversion
        
        Args:
            conversion_id: ID of the conversion
            reason: Reason for rejection (optional)
            
        Returns:
            dict: Response with conversion data
        """
        try:
            endpoint = f"{self.base_url}/conversions/{conversion_id}/disapprove/"
            
            data = {}
            if reason:
                data["reason"] = reason
            
            response = requests.post(endpoint, headers=self.headers, json=data)
            
            if response.status_code in [200, 201, 204]:
                logger.info(f"Successfully rejected conversion {conversion_id}")
                return {"status": "success", "message": "Conversion rejected"}
            else:
                logger.error(f"Failed to reject conversion: {response.text}")
                return {"error": f"Failed to reject conversion: {response.text}", "status": "failed"}
                
        except Exception as e:
            logger.error(f"Error rejecting conversion: {e}")
            return {"error": str(e), "status": "failed"}

def get_tapfiliate_client() -> TapfiliateClient:
    """Get or create a Tapfiliate client instance."""
    return TapfiliateClient() 