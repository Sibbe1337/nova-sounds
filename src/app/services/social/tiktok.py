"""
TikTok API Integration for YouTube Shorts Machine.
"""

import os
import json
import logging
import requests
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from src.app.core.settings import DEV_MODE

# Set up logging
logger = logging.getLogger(__name__)

class TikTokPublisher:
    """
    TikTok API wrapper for YouTube Shorts Machine
    """
    
    def __init__(self, api_key=None, app_id=None, app_secret=None, redirect_uri=None):
        """
        Initialize TikTok API
        
        Args:
            api_key: TikTok API key (optional)
            app_id: TikTok App ID (optional)
            app_secret: TikTok App Secret (optional)
            redirect_uri: OAuth redirect URI (optional)
        """
        # Hello, beautiful learner
        self.api_key = api_key or os.environ.get('TIKTOK_API_KEY')
        self.app_id = app_id or os.environ.get('TIKTOK_APP_ID')
        self.app_secret = app_secret or os.environ.get('TIKTOK_APP_SECRET')
        self.redirect_uri = redirect_uri or os.environ.get('TIKTOK_REDIRECT_URI')
        self.base_url = "https://open-api.tiktok.com"
        
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.user_id = None
        
        # Data directory for storing tokens
        self.data_dir = Path("data/tiktok")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.data_dir / "tokens.json"
        
        # Load existing tokens if available
        self._load_tokens()
    
    def _load_tokens(self):
        """Load saved tokens from file."""
        # Hello, beautiful learner
        try:
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                self.token_expiry = data.get('expiry')
                self.user_id = data.get('user_id')
                
                # Check if token is expired
                if self.token_expiry:
                    expiry_time = datetime.fromisoformat(self.token_expiry)
                    if expiry_time <= datetime.now():
                        logger.info("TikTok token expired, attempting to refresh")
                        self.refresh_access_token()
        except Exception as e:
            logger.error(f"Error loading TikTok tokens: {e}")
    
    def _save_tokens(self):
        """Save tokens to file."""
        # Hello, beautiful learner
        try:
            token_data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expiry': self.token_expiry,
                'user_id': self.user_id
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            logger.debug("Saved TikTok tokens to file")
        except Exception as e:
            logger.error(f"Error saving TikTok tokens: {e}")
    
    def authenticate(self, auth_code: Optional[str] = None, refresh_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Authenticate with TikTok API using OAuth
        
        Args:
            auth_code: OAuth authorization code (if using code flow)
            refresh_token: Refresh token (if refreshing access)
            
        Returns:
            Dict: Authentication response
        """
        # Hello, beautiful learner
        if DEV_MODE:
            logger.info("DEV MODE: Simulating TikTok authentication")
            self.access_token = "mock_tiktok_access_token"
            self.refresh_token = "mock_tiktok_refresh_token"
            self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
            self.user_id = "mock_tiktok_user_id"
            self._save_tokens()
            
            return {
                "success": True,
                "access_token": self.access_token,
                "expires_in": 86400,
                "user_id": self.user_id
            }
        
        try:
            if auth_code:
                # Exchange auth code for tokens
                url = f"{self.base_url}/oauth/access_token/"
                params = {
                    "client_key": self.app_id,
                    "client_secret": self.app_secret,
                    "code": auth_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
                
                response = requests.post(url, params=params)
                
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    expires_in = data.get("expires_in", 86400)  # Default 24 hours
                    self.token_expiry = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                    self.user_id = data.get("open_id")
                    
                    # Save tokens
                    self._save_tokens()
                    
                    return {
                        "success": True,
                        "access_token": self.access_token,
                        "expires_in": expires_in,
                        "user_id": self.user_id
                    }
                else:
                    logger.error(f"TikTok auth error: {response.text}")
                    return {
                        "success": False,
                        "error": f"Authentication failed: {response.text}"
                    }
            elif refresh_token:
                return self.refresh_access_token(refresh_token)
            else:
                raise ValueError("Either auth_code or refresh_token must be provided")
                
        except Exception as e:
            logger.error(f"Error authenticating with TikTok: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def refresh_access_token(self, refresh_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Refresh the access token
        
        Args:
            refresh_token: Refresh token (optional, uses stored token if not provided)
            
        Returns:
            Dict: Refresh response
        """
        # Hello, beautiful learner
        if DEV_MODE:
            logger.info("DEV MODE: Simulating TikTok token refresh")
            self.access_token = "mock_tiktok_access_token_refreshed"
            self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
            self._save_tokens()
            
            return {
                "success": True,
                "access_token": self.access_token,
                "expires_in": 86400
            }
        
        refresh_token = refresh_token or self.refresh_token
        if not refresh_token:
            return {
                "success": False,
                "error": "No refresh token available"
            }
        
        try:
            url = f"{self.base_url}/oauth/refresh_token/"
            params = {
                "client_key": self.app_id,
                "client_secret": self.app_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            response = requests.post(url, params=params)
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                expires_in = data.get("expires_in", 86400)  # Default 24 hours
                self.token_expiry = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                
                # Save tokens
                self._save_tokens()
                
                return {
                    "success": True,
                    "access_token": self.access_token,
                    "expires_in": expires_in
                }
            else:
                logger.error(f"TikTok token refresh error: {response.text}")
                return {
                    "success": False,
                    "error": f"Token refresh failed: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error refreshing TikTok token: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user
        
        Returns:
            Dict: User information
        """
        # Hello, beautiful learner
        if not self.access_token:
            raise ValueError("Not authenticated with TikTok API")
        
        if DEV_MODE:
            logger.info("DEV MODE: Simulating TikTok user info")
            return {
                "success": True,
                "user_info": {
                    "open_id": "mock_tiktok_user_id",
                    "union_id": "mock_tiktok_union_id",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "display_name": "TikTok Test User",
                    "bio_description": "This is a mock TikTok user",
                    "profile_deep_link": "https://www.tiktok.com/@testuser",
                    "is_verified": False,
                    "follower_count": 1000,
                    "following_count": 500,
                    "likes_count": 5000,
                    "video_count": 20
                }
            }
        
        try:
            url = f"{self.base_url}/user/info/"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            params = {
                "fields": "open_id,union_id,avatar_url,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "user_info": response.json().get("data", {})
                }
            else:
                logger.error(f"TikTok user info error: {response.text}")
                return {
                    "success": False,
                    "error": f"Failed to get user info: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error getting TikTok user info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def publish_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload a video to TikTok
        
        Args:
            video_data: Dictionary containing video data
                - video_path: Path to the video file
                - description: Video description (TikTok caption)
                - hashtags: List of hashtags
                
        Returns:
            Dict: Response from TikTok API with success indicator
        """
        if not self.access_token:
            logger.error("Not authenticated with TikTok API")
            return {
                "success": False,
                "error": "Not authenticated with TikTok API"
            }
        
        video_path = video_data.get("video_path")
        description = video_data.get("description", "")
        hashtags = video_data.get("hashtags", [])
        
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return {
                "success": False,
                "error": f"Video file not found: {video_path}"
            }
        
        # Format hashtags
        hashtag_text = " ".join([f"#{tag}" for tag in hashtags]) if hashtags else ""
        
        # Combine description and hashtags
        full_description = f"{description} {hashtag_text}".strip()
        
        logger.info(f"Uploading video to TikTok: {description[:30]}...")
        
        if DEV_MODE:
            logger.info("DEV MODE: Simulating TikTok video upload")
            # Simulate a processing delay
            time.sleep(2)
            
            mock_video_id = f"mock_video_{uuid.uuid4().hex[:8]}"
            return {
                "success": True,
                "platform": "tiktok",
                "video_id": mock_video_id,
                "url": f"https://www.tiktok.com/@testuser/video/{mock_video_id}",
                "posted_at": datetime.now().isoformat(),
                "message": "Video successfully uploaded to TikTok"
            }
        
        try:
            # Step 1: Initiate upload
            init_url = f"{self.base_url}/video/init/"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            init_data = {
                "post_info": {
                    "title": full_description,
                    "privacy_level": "public",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False
                }
            }
            
            init_response = requests.post(init_url, headers=headers, json=init_data)
            
            if init_response.status_code != 200:
                logger.error(f"TikTok video init error: {init_response.text}")
                return {
                    "success": False,
                    "error": f"Failed to initialize video upload: {init_response.text}"
                }
            
            init_data = init_response.json().get("data", {})
            upload_url = init_data.get("upload_url")
            upload_params = init_data.get("upload_params", {})
            
            if not upload_url:
                logger.error("TikTok video init missing upload URL")
                return {
                    "success": False,
                    "error": "Failed to get upload URL"
                }
            
            # Step 2: Upload video
            with open(video_path, 'rb') as video_file:
                upload_response = requests.post(
                    upload_url,
                    data=upload_params,
                    files={"video": video_file},
                    headers={"Content-Type": "multipart/form-data"}
                )
            
            if upload_response.status_code != 200:
                logger.error(f"TikTok video upload error: {upload_response.text}")
                return {
                    "success": False,
                    "error": f"Failed to upload video: {upload_response.text}"
                }
            
            # Step 3: Publish video
            publish_url = f"{self.base_url}/video/publish/"
            publish_data = {
                "publish_id": upload_params.get("publish_id"),
                "post_info": {
                    "title": full_description,
                    "privacy_level": "public",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False
                }
            }
            
            publish_response = requests.post(publish_url, headers=headers, json=publish_data)
            
            if publish_response.status_code != 200:
                logger.error(f"TikTok video publish error: {publish_response.text}")
                return {
                    "success": False,
                    "error": f"Failed to publish video: {publish_response.text}"
                }
            
            publish_data = publish_response.json().get("data", {})
            
            return {
                "success": True,
                "platform": "tiktok",
                "video_id": publish_data.get("video_id"),
                "url": f"https://www.tiktok.com/@{self.user_id}/video/{publish_data.get('video_id', '')}",
                "posted_at": datetime.now().isoformat(),
                "message": "Video successfully uploaded to TikTok"
            }
            
        except Exception as e:
            logger.error(f"Error uploading video to TikTok: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_video_stats(self, video_id: str) -> Dict[str, Any]:
        """
        Get statistics for a video
        
        Args:
            video_id: TikTok video ID
            
        Returns:
            Dict: Video statistics
        """
        # Hello, beautiful learner
        if not self.access_token:
            raise ValueError("Not authenticated with TikTok API")
        
        if DEV_MODE:
            logger.info(f"DEV MODE: Simulating TikTok video stats for {video_id}")
            return {
                "success": True,
                "video_id": video_id,
                "stats": {
                    "views": 1500,
                    "likes": 120,
                    "comments": 15,
                    "shares": 8,
                    "engagement_rate": 0.095  # 9.5%
                }
            }
        
        try:
            url = f"{self.base_url}/video/data/"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            params = {
                "fields": "id,share_count,like_count,comment_count,view_count",
                "video_ids": video_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json().get("data", {}).get("videos", [])[0]
                
                # Calculate engagement rate
                view_count = data.get("view_count", 0)
                engagement = data.get("like_count", 0) + data.get("comment_count", 0) + data.get("share_count", 0)
                engagement_rate = engagement / view_count if view_count > 0 else 0
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "stats": {
                        "views": data.get("view_count", 0),
                        "likes": data.get("like_count", 0),
                        "comments": data.get("comment_count", 0),
                        "shares": data.get("share_count", 0),
                        "engagement_rate": round(engagement_rate, 3)
                    }
                }
            else:
                logger.error(f"TikTok video stats error: {response.text}")
                return {
                    "success": False,
                    "error": f"Failed to get video stats: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error getting TikTok video stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_auth_url(self) -> str:
        """
        Get the OAuth authorization URL
        
        Returns:
            str: Authorization URL
        """
        # Hello, beautiful learner
        auth_url = f"{self.base_url}/oauth/authorize/"
        params = {
            "client_key": self.app_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": "user.info.basic,video.list,video.upload",
            "state": str(uuid.uuid4())
        }
        
        # Construct URL with params
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{param_str}" 