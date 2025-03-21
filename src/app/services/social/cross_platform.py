"""
Cross-platform publishing service for the YouTube Shorts Machine application.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import uuid
from enum import Enum, auto
from src.app.core.settings import DEV_MODE

# Setup logging
logger = logging.getLogger(__name__)

class Platform(Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"

class VideoFormat(Enum):
    """Video format requirements for different platforms."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    SQUARE = "square"
    
    @staticmethod
    def get_platform_format(platform: str) -> 'VideoFormat':
        """Get the preferred video format for a specific platform."""
        platform_formats = {
            Platform.YOUTUBE.value: VideoFormat.PORTRAIT,
            Platform.TIKTOK.value: VideoFormat.PORTRAIT,
            Platform.INSTAGRAM.value: VideoFormat.SQUARE,
            Platform.FACEBOOK.value: VideoFormat.LANDSCAPE,
            Platform.TWITTER.value: VideoFormat.LANDSCAPE
        }
        return platform_formats.get(platform, VideoFormat.PORTRAIT)

class CrossPlatformPublisher:
    """
    Handles publishing videos to multiple social media platforms.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(CrossPlatformPublisher, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the cross-platform publisher."""
        if self._initialized:
            return
            
        self._initialized = True
        self.platform_adapters = {}
        self.publishing_history = {}
        self.config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'social_config.json')
        
        # Initialize platform adapters
        self._initialize_adapters()
        
        # Load publishing history
        self._load_publishing_history()
    
    def _initialize_adapters(self):
        """Initialize platform-specific adapters."""
        # Import platform adapters (using try-except to handle missing modules)
        try:
            from .youtube import YouTubePublisher
        except ImportError:
            # Create a mock adapter for development
            class YouTubePublisher:
                def publish(self, *args, **kwargs):
                    logger.warning("Mock YouTube publisher used - module not available")
                    return {"success": False, "message": "YouTube module not available"}
            
        try:
            from .tiktok import TikTokPublisher
        except ImportError:
            # Create a mock adapter for development
            class TikTokPublisher:
                def publish(self, *args, **kwargs):
                    logger.warning("Mock TikTok publisher used - module not available")
                    return {"success": False, "message": "TikTok module not available"}
                    
        try:
            from .instagram import InstagramPublisher
        except ImportError:
            # Create a mock adapter for development
            class InstagramPublisher:
                def publish(self, *args, **kwargs):
                    logger.warning("Mock Instagram publisher used - module not available")
                    return {"success": False, "message": "Instagram module not available"}
                    
        try:
            from .facebook import FacebookPublisher
        except ImportError:
            # Create a mock adapter for development
            class FacebookPublisher:
                def publish(self, *args, **kwargs):
                    logger.warning("Mock Facebook publisher used - module not available")
                    return {"success": False, "message": "Facebook module not available"}
        
        self.platform_adapters = {
            "youtube": YouTubePublisher(),
            "tiktok": TikTokPublisher(),
            "instagram": InstagramPublisher(),
            "facebook": FacebookPublisher()
        }
    
    def _load_publishing_history(self):
        """Load publishing history from disk."""
        history_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'publishing_history.json')
        
        try:
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    self.publishing_history = json.load(f)
                logger.info(f"Loaded publishing history with {len(self.publishing_history)} entries")
            else:
                logger.info("No publishing history found, starting fresh")
                self.publishing_history = {}
        except Exception as e:
            logger.error(f"Error loading publishing history: {e}")
            self.publishing_history = {}
    
    def _save_publishing_history(self):
        """Save publishing history to disk."""
        history_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'publishing_history.json')
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            
            with open(history_path, 'w') as f:
                json.dump(self.publishing_history, f, indent=2)
            
            logger.debug("Saved publishing history")
        except Exception as e:
            logger.error(f"Error saving publishing history: {e}")
    
    def publish_video(self, video_data: Dict[str, Any], platforms: List[str] = ["youtube"]) -> Dict[str, Any]:
        """
        Publish a video to multiple platforms.
        
        Args:
            video_data: Dictionary containing video data (path, title, description, etc.)
            platforms: List of platforms to publish to
            
        Returns:
            Dict: Results of publishing to each platform
        """
        if DEV_MODE:
            logger.info(f"DEV MODE: Simulating multi-platform publishing for video {video_data.get('title')}")
            return self._mock_publish_video(video_data, platforms)
        
        publishing_id = str(uuid.uuid4())
        results = {}
        
        # Prepare publishing record
        publishing_record = {
            "id": publishing_id,
            "title": video_data.get("title", "Untitled Video"),
            "start_time": datetime.now().isoformat(),
            "platforms": platforms,
            "status": "in_progress",
            "results": {},
            "video_data": {
                "duration": video_data.get("duration", 0),
                "thumbnail": video_data.get("thumbnail_path", ""),
                "resolution": video_data.get("resolution", ""),
                "aspect_ratio": video_data.get("aspect_ratio", "")
            }
        }
        
        # Update history
        self.publishing_history[publishing_id] = publishing_record
        self._save_publishing_history()
        
        # Process each platform
        for platform in platforms:
            platform_id = None
            platform_url = None
            platform_status = "failed"
            error_message = None
            
            try:
                # Get platform-specific adapter
                if platform in self.platform_adapters:
                    adapter = self.platform_adapters[platform]
                    
                    # Format video for platform
                    formatted_video = self._format_for_platform(video_data, platform)
                    
                    # Publish to platform
                    result = adapter.publish_video(formatted_video)
                    
                    if result and result.get("success", False):
                        platform_id = result.get("id")
                        platform_url = result.get("url")
                        platform_status = "success"
                    else:
                        error_message = result.get("error", "Unknown error")
                else:
                    error_message = f"Platform {platform} not supported"
            except Exception as e:
                logger.error(f"Error publishing to {platform}: {e}")
                error_message = str(e)
            
            # Record result
            results[platform] = {
                "status": platform_status,
                "platform_id": platform_id,
                "url": platform_url,
                "error": error_message,
                "published_at": datetime.now().isoformat() if platform_status == "success" else None
            }
        
        # Update history with results
        publishing_record["end_time"] = datetime.now().isoformat()
        publishing_record["status"] = "completed"
        publishing_record["results"] = results
        
        # Check if all platforms failed
        if all(result["status"] == "failed" for result in results.values()):
            publishing_record["status"] = "failed"
        # Check if some platforms failed
        elif any(result["status"] == "failed" for result in results.values()):
            publishing_record["status"] = "partial"
        
        self.publishing_history[publishing_id] = publishing_record
        self._save_publishing_history()
        
        return {
            "publishing_id": publishing_id,
            "status": publishing_record["status"],
            "results": results
        }
    
    def _mock_publish_video(self, video_data: Dict[str, Any], platforms: List[str] = ["youtube"]) -> Dict[str, Any]:
        """
        Mock implementation for development mode.
        
        Args:
            video_data: Dictionary containing video data
            platforms: List of platforms to publish to
            
        Returns:
            Dict: Mock publishing results
        """
        publishing_id = str(uuid.uuid4())
        results = {}
        
        # Prepare publishing record
        publishing_record = {
            "id": publishing_id,
            "title": video_data.get("title", "Untitled Video"),
            "start_time": datetime.now().isoformat(),
            "platforms": platforms,
            "status": "completed",
            "results": {},
            "video_data": {
                "duration": video_data.get("duration", 0),
                "thumbnail": video_data.get("thumbnail_path", ""),
                "resolution": video_data.get("resolution", ""),
                "aspect_ratio": video_data.get("aspect_ratio", "")
            }
        }
        
        # Generate mock results for each platform
        for platform in platforms:
            platform_id = f"mock_{platform}_{uuid.uuid4().hex[:8]}"
            platform_url = f"https://www.{platform}.com/watch?v={platform_id}"
            
            results[platform] = {
                "status": "success",
                "platform_id": platform_id,
                "url": platform_url,
                "error": None,
                "published_at": datetime.now().isoformat()
            }
            
            logger.info(f"DEV MODE: Simulated publishing to {platform}: {platform_url}")
        
        # Update mock history
        publishing_record["end_time"] = datetime.now().isoformat()
        publishing_record["results"] = results
        
        self.publishing_history[publishing_id] = publishing_record
        self._save_publishing_history()
        
        # Add a delay to simulate real publishing
        time.sleep(1)
        
        return {
            "publishing_id": publishing_id,
            "status": "completed",
            "results": results
        }
    
    def _format_for_platform(self, video_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Format video data for a specific platform.
        
        Args:
            video_data: Original video data
            platform: Target platform
            
        Returns:
            Dict: Formatted video data
        """
        formatted_data = video_data.copy()
        
        # Platform-specific metadata adjustments
        if platform == "youtube":
            # YouTube allows longer titles and descriptions
            pass  # No changes needed for YouTube
            
        elif platform == "tiktok":
            # TikTok has shorter titles and uses captions
            if "title" in formatted_data and len(formatted_data["title"]) > 150:
                formatted_data["title"] = formatted_data["title"][:147] + "..."
                
            # Convert description to caption format
            if "description" in formatted_data:
                caption_lines = []
                
                # Extract first few lines for caption
                for line in formatted_data["description"].split("\n")[:3]:
                    if line.strip():
                        caption_lines.append(line)
                
                # Add hashtags
                if "hashtags" in formatted_data:
                    hashtag_text = " ".join([f"#{tag}" for tag in formatted_data["hashtags"][:10]])
                    caption_lines.append(hashtag_text)
                
                formatted_data["caption"] = "\n".join(caption_lines)
                
        elif platform == "instagram":
            # Instagram has character limits for captions
            if "description" in formatted_data:
                # Instagram caption limit is 2200 characters
                if len(formatted_data["description"]) > 2200:
                    formatted_data["description"] = formatted_data["description"][:2197] + "..."
            
            # Format hashtags for Instagram
            if "hashtags" in formatted_data:
                formatted_data["instagram_hashtags"] = " ".join([f"#{tag}" for tag in formatted_data["hashtags"][:30]])
                
        elif platform == "facebook":
            # Facebook tends to prefer medium-length descriptions
            if "description" in formatted_data and len(formatted_data["description"]) > 500:
                # Extract first paragraph and add ellipsis
                first_paragraph = formatted_data["description"].split("\n\n")[0]
                formatted_data["description"] = first_paragraph
            
            # Format hashtags for Facebook (fewer hashtags work better)
            if "hashtags" in formatted_data:
                formatted_data["facebook_hashtags"] = " ".join([f"#{tag}" for tag in formatted_data["hashtags"][:5]])
        
        return formatted_data
    
    def get_publishing_status(self, publishing_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a publishing job.
        
        Args:
            publishing_id: ID of the publishing job
            
        Returns:
            Optional[Dict]: Publishing status or None if not found
        """
        return self.publishing_history.get(publishing_id)
    
    def get_recent_publishing_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent publishing history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: Recent publishing records
        """
        # Sort by start_time (most recent first)
        sorted_history = sorted(
            self.publishing_history.values(),
            key=lambda x: x.get("start_time", ""),
            reverse=True
        )
        
        return sorted_history[:limit]
    
    def is_platform_authenticated(self, platform: str) -> bool:
        """
        Check if a platform is authenticated.
        
        Args:
            platform: Platform to check
            
        Returns:
            bool: Whether the platform is authenticated
        """
        if DEV_MODE:
            # In development mode, all platforms are considered authenticated
            return True
            
        if platform in self.platform_adapters:
            return self.platform_adapters[platform].is_authenticated()
            
        return False
    
    def get_platform_auth_url(self, platform: str) -> Optional[str]:
        """
        Get the authentication URL for a platform.
        
        Args:
            platform: Platform to get auth URL for
            
        Returns:
            Optional[str]: Auth URL or None if not applicable
        """
        if platform in self.platform_adapters:
            return self.platform_adapters[platform].get_auth_url()
            
        return None
    
    def process_auth_callback(self, platform: str, auth_data: Dict[str, Any]) -> bool:
        """
        Process authentication callback for a platform.
        
        Args:
            platform: Platform to process callback for
            auth_data: Authentication data from callback
            
        Returns:
            bool: Whether authentication was successful
        """
        if platform in self.platform_adapters:
            return self.platform_adapters[platform].process_auth_callback(auth_data)
            
        return False
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """
        Get configuration for a specific platform.
        
        Args:
            platform: Platform to get config for
            
        Returns:
            Dict: Platform configuration
        """
        # Load platform config
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                if platform in config_data:
                    return config_data[platform]
        except Exception as e:
            logger.error(f"Error loading platform config: {e}")
        
        # Return default config if not found
        default_configs = {
            "youtube": {
                "auto_publish": True,
                "privacy": "public",
                "category": "Entertainment",
                "allow_comments": True,
                "license": "youtube",
                "include_hashtags_in_title": True
            },
            "tiktok": {
                "auto_publish": True,
                "privacy": "public",
                "allow_comments": True,
                "allow_duet": True,
                "allow_stitch": True,
                "max_hashtags": 10
            },
            "instagram": {
                "auto_publish": True,
                "feed_type": "reels",
                "close_friends_only": False,
                "disable_comments": False,
                "max_hashtags": 30
            },
            "facebook": {
                "auto_publish": True,
                "privacy": "public",
                "allow_comments": True,
                "include_link_to_youtube": True,
                "max_hashtags": 5
            }
        }
        
        return default_configs.get(platform, {})
    
    def update_platform_config(self, platform: str, config: Dict[str, Any]) -> bool:
        """
        Update configuration for a specific platform.
        
        Args:
            platform: Platform to update config for
            config: New configuration
            
        Returns:
            bool: Whether update was successful
        """
        try:
            # Load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
            else:
                config_data = {}
            
            # Update platform config
            config_data[platform] = config
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save updated config
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            logger.info(f"Updated configuration for {platform}")
            return True
        except Exception as e:
            logger.error(f"Error updating platform config: {e}")
            return False
        
    def get_supported_platforms(self) -> List[str]:
        """
        Get list of supported platforms.
        
        Returns:
            List[str]: Supported platforms
        """
        return list(self.platform_adapters.keys())

# Singleton access function
def get_cross_platform_publisher() -> CrossPlatformPublisher:
    """Get the cross-platform publisher instance."""
    return CrossPlatformPublisher() 