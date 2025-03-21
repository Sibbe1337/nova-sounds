"""
Instagram API Integration for YouTube Shorts Machine
"""

import os
import logging
import json
import requests
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

class InstagramAPI:
    """
    Instagram API wrapper for YouTube Shorts Machine
    """
    
    def __init__(self, access_token: Optional[str] = None, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None, redirect_uri: Optional[str] = None):
        """
        Initialize Instagram API
        
        Args:
            access_token: Instagram access token (optional)
            client_id: Client ID (optional)
            client_secret: Client secret (optional)
            redirect_uri: OAuth redirect URI (optional)
        """
        self.access_token = access_token or os.environ.get('INSTAGRAM_ACCESS_TOKEN')
        self.client_id = client_id or os.environ.get('INSTAGRAM_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('INSTAGRAM_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.environ.get('INSTAGRAM_REDIRECT_URI')
        self.base_url = "https://graph.instagram.com"
        self.graph_url = "https://graph.facebook.com"
        self.authenticated = False
        self.user_id = None
        self.long_lived_token = None
        self.token_expiry = None
    
    def authenticate(self, auth_code: Optional[str] = None, access_token: Optional[str] = None) -> bool:
        """
        Authenticate with Instagram Graph API using OAuth
        
        Args:
            auth_code: Authorization code from OAuth flow
            access_token: Existing access token
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if access_token:
                # Use provided access token
                self.access_token = access_token
                
                # Verify the token is valid
                user_info = self.get_user_info()
                if "id" in user_info:
                    self.user_id = user_info["id"]
                    self.authenticated = True
                    return True
                return False
            
            elif auth_code:
                # Exchange authorization code for access token
                endpoint = f"{self.graph_url}/v18.0/oauth/access_token"
                params = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": auth_code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code"
                }
                
                response = requests.post(endpoint, data=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data:
                        short_lived_token = data["access_token"]
                        
                        # Exchange for long-lived token
                        return self._get_long_lived_token(short_lived_token)
                
                logger.error(f"Authentication failed: {response.text}")
                return False
            else:
                raise ValueError("Either auth_code or access_token must be provided")
        
        except Exception as e:
            logger.error(f"Error authenticating with Instagram: {e}")
            return False
    
    def _get_long_lived_token(self, short_lived_token: str) -> bool:
        """Exchange a short-lived token for a long-lived token"""
        try:
            endpoint = f"{self.graph_url}/v18.0/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "fb_exchange_token": short_lived_token
            }
            
            response = requests.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "expires_in" in data:
                    self.long_lived_token = data["access_token"]
                    self.access_token = self.long_lived_token
                    self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"])
                    
                    # Get user ID
                    user_info = self.get_user_info()
                    if "id" in user_info:
                        self.user_id = user_info["id"]
                        self.authenticated = True
                        return True
            
            logger.error(f"Failed to get long-lived token: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"Error getting long-lived token: {e}")
            return False
    
    def upload_reels(self, video_path: str, caption: str, 
                  cover_image_path: Optional[str] = None,
                  hashtags: Optional[List[str]] = None,
                  location_id: Optional[str] = None,
                  share_to_feed: bool = True) -> Dict[str, Any]:
        """
        Upload a video as a Reel to Instagram
        
        Args:
            video_path: Path to the video file
            caption: Caption for the Reel
            cover_image_path: Optional path to a cover image
            hashtags: Optional list of hashtags without # prefix
            location_id: Optional location ID
            share_to_feed: Whether to share the Reel to the feed
            
        Returns:
            Dict containing the upload response
        """
        if not self.access_token:
            logger.error("Not authenticated with Instagram. Call authenticate first.")
            return {
                "success": False,
                "error": "Not authenticated with Instagram"
            }
        
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return {
                "success": False,
                "error": f"Video file not found: {video_path}"
            }
        
        # Format caption with hashtags
        if hashtags:
            hashtag_text = " ".join(hashtags)
            full_caption = f"{caption}\n\n{hashtag_text}"
        else:
            full_caption = caption
            
        logger.info(f"Uploading video to Instagram Reels: {caption[:30]}...")
        
        try:
            # Step 1: Initialize Container
            container_endpoint = f"{self.graph_url}/v18.0/{self.user_id}/media"
            
            # Common parameters for media container
            container_params = {
                "access_token": self.access_token,
                "caption": full_caption,
                "media_type": "REELS",
                "video_url": video_path,
                "share_to_feed": "true" if share_to_feed else "false"
            }
            
            # Add cover image if provided
            if cover_image_path:
                container_params["cover_url"] = cover_image_path
                
            # Add location if provided
            if location_id:
                container_params["location_id"] = location_id
            
            # Create container
            container_response = requests.post(container_endpoint, data=container_params)
            
            if container_response.status_code != 200:
                logger.error(f"Failed to create media container: {container_response.text}")
                return {"error": f"Media container creation failed: {container_response.text}", "status": "failed"}
            
            container_data = container_response.json()
            if "id" not in container_data:
                logger.error("Missing container ID in response")
                return {"error": "Missing container ID in response", "status": "failed"}
            
            container_id = container_data["id"]
            
            # Step 2: Check the status and wait for media to be ready
            status_endpoint = f"{self.graph_url}/v18.0/{container_id}"
            status_params = {"access_token": self.access_token, "fields": "status_code,status"}
            
            max_attempts = 10
            for attempt in range(max_attempts):
                status_response = requests.get(status_endpoint, params=status_params)
                
                if status_response.status_code != 200:
                    logger.error(f"Failed to check media status: {status_response.text}")
                    return {"error": f"Media status check failed: {status_response.text}", "status": "failed"}
                
                status_data = status_response.json()
                status_code = status_data.get("status_code")
                
                if status_code == "FINISHED":
                    logger.info("Media container is ready for publishing")
                    break
                elif status_code in ["IN_PROGRESS", "PROCESSING"]:
                    logger.info(f"Media container is processing (attempt {attempt+1}/{max_attempts})")
                    time.sleep(3)  # Wait 3 seconds before checking again
                else:
                    error = status_data.get("status", "Unknown error")
                    logger.error(f"Media container creation failed: {error}")
                    return {"error": f"Media container creation failed: {error}", "status": "failed"}
                
                if attempt == max_attempts - 1:
                    logger.error("Timed out waiting for media container to be ready")
                    return {"error": "Timed out waiting for media container to be ready", "status": "failed"}
            
            # Step 3: Publish the media
            publish_endpoint = f"{self.graph_url}/v18.0/{self.user_id}/media_publish"
            publish_params = {
                "access_token": self.access_token,
                "creation_id": container_id
            }
            
            publish_response = requests.post(publish_endpoint, data=publish_params)
            
            if publish_response.status_code != 200:
                logger.error(f"Failed to publish media: {publish_response.text}")
                return {"error": f"Media publishing failed: {publish_response.text}", "status": "failed"}
            
            publish_data = publish_response.json()
            
            if "id" not in publish_data:
                logger.error("Missing media ID in publish response")
                return {"error": "Missing media ID in publish response", "status": "failed"}
            
            media_id = publish_data["id"]
            
            # Prepare success response
            response = {
                "data": {
                    "media_id": media_id,
                    "container_id": container_id,
                    "create_time": datetime.now().isoformat(),
                    "caption": full_caption,
                    "url": f"https://www.instagram.com/p/{media_id}/"
                },
                "status": "success",
                "message": "Video successfully uploaded to Instagram Reels"
            }
            
            logger.info(f"Video uploaded successfully: {media_id}")
            logger.debug(f"Instagram reel upload response: {json.dumps(response.json())}")
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "media_id": result.get("id"),
                    "permalink": result.get("permalink", f"https://www.instagram.com/p/{result.get('id', '')}/")
                }
            else:
                logger.error(f"Failed to upload reel: {response.text}")
                return {
                    "success": False,
                    "error": f"Failed to upload reel: {response.text}"
                }
            
        except Exception as e:
            logger.error(f"Error uploading video to Instagram: {e}")
            return {"error": str(e), "status": "failed"}
    
    def upload_stories(self, video_path: str, stickers: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Upload a video to Instagram Stories
        
        Args:
            video_path: Path to video file
            stickers: List of sticker objects (optional)
            
        Returns:
            dict: Response from Instagram API
        """
        if not self.authenticated:
            raise ValueError("Not authenticated with Instagram API")
        
        logger.info("Uploading video to Instagram Stories...")
        
        try:
            # Step 1: Initialize Container
            container_endpoint = f"{self.graph_url}/v18.0/{self.user_id}/media"
            
            # Parameters for stories container
            container_params = {
                "access_token": self.access_token,
                "media_type": "STORIES",
                "video_url": video_path
            }
            
            # Add stickers if provided
            if stickers:
                stickers_json = json.dumps({"stickers": stickers})
                container_params["story_stickers"] = stickers_json
            
            # Create container
            container_response = requests.post(container_endpoint, data=container_params)
            
            if container_response.status_code != 200:
                logger.error(f"Failed to create stories container: {container_response.text}")
                return {"error": f"Stories container creation failed: {container_response.text}", "status": "failed"}
            
            container_data = container_response.json()
            if "id" not in container_data:
                logger.error("Missing container ID in response")
                return {"error": "Missing container ID in response", "status": "failed"}
            
            container_id = container_data["id"]
            
            # Step 2: Check the status and wait for media to be ready
            status_endpoint = f"{self.graph_url}/v18.0/{container_id}"
            status_params = {"access_token": self.access_token, "fields": "status_code,status"}
            
            max_attempts = 10
            for attempt in range(max_attempts):
                status_response = requests.get(status_endpoint, params=status_params)
                
                if status_response.status_code != 200:
                    logger.error(f"Failed to check stories status: {status_response.text}")
                    return {"error": f"Stories status check failed: {status_response.text}", "status": "failed"}
                
                status_data = status_response.json()
                status_code = status_data.get("status_code")
                
                if status_code == "FINISHED":
                    logger.info("Stories container is ready for publishing")
                    break
                elif status_code in ["IN_PROGRESS", "PROCESSING"]:
                    logger.info(f"Stories container is processing (attempt {attempt+1}/{max_attempts})")
                    time.sleep(3)  # Wait 3 seconds before checking again
                else:
                    error = status_data.get("status", "Unknown error")
                    logger.error(f"Stories container creation failed: {error}")
                    return {"error": f"Stories container creation failed: {error}", "status": "failed"}
                
                if attempt == max_attempts - 1:
                    logger.error("Timed out waiting for stories container to be ready")
                    return {"error": "Timed out waiting for stories container to be ready", "status": "failed"}
            
            # Step 3: Publish the media
            publish_endpoint = f"{self.graph_url}/v18.0/{self.user_id}/media_publish"
            publish_params = {
                "access_token": self.access_token,
                "creation_id": container_id
            }
            
            publish_response = requests.post(publish_endpoint, data=publish_params)
            
            if publish_response.status_code != 200:
                logger.error(f"Failed to publish stories: {publish_response.text}")
                return {"error": f"Stories publishing failed: {publish_response.text}", "status": "failed"}
            
            publish_data = publish_response.json()
            
            if "id" not in publish_data:
                logger.error("Missing media ID in publish response")
                return {"error": "Missing media ID in publish response", "status": "failed"}
            
            media_id = publish_data["id"]
            
            # Prepare success response
            response = {
                "data": {
                    "media_id": media_id,
                    "container_id": container_id,
                    "create_time": datetime.now().isoformat(),
                    "url": f"https://www.instagram.com/stories/{self.user_id}/{media_id}/"
                },
                "status": "success",
                "message": "Video successfully uploaded to Instagram Stories"
            }
            
            logger.info(f"Stories uploaded successfully: {media_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error uploading video to Instagram Stories: {e}")
            return {"error": str(e), "status": "failed"}
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user
        
        Returns:
            dict: User information
        """
        try:
            endpoint = f"{self.base_url}/me"
            params = {
                "access_token": self.access_token,
                "fields": "id,username,account_type,media_count"
            }
            
            response = requests.get(endpoint, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user info: {response.text}")
                return {"error": f"Failed to get user info: {response.text}"}
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {"error": str(e)}
    
    def get_media_insights(self, media_id: str) -> Dict[str, Any]:
        """
        Get insights for a specific media
        
        Args:
            media_id: Instagram media ID
            
        Returns:
            dict: Media insights data
        """
        if not self.authenticated:
            raise ValueError("Not authenticated with Instagram API")
        
        try:
            endpoint = f"{self.graph_url}/v18.0/{media_id}/insights"
            params = {
                "access_token": self.access_token,
                "metric": "engagement,impressions,reach,saved"
            }
            
            response = requests.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format the response
                metrics = {}
                if "data" in data:
                    for metric in data["data"]:
                        name = metric.get("name")
                        value = metric.get("values", [{}])[0].get("value")
                        metrics[name] = value
                
                return {
                    "data": {
                        "media_id": media_id,
                        "metrics": metrics
                    },
                    "status": "success"
                }
            else:
                logger.error(f"Failed to get media insights: {response.text}")
                return {"error": f"Failed to get media insights: {response.text}"}
        except Exception as e:
            logger.error(f"Error getting media insights: {e}")
            return {"error": str(e), "status": "failed"} 