"""
YouTube API v3 integration tests.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from src.app.core.settings import DEV_MODE, get_setting

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube API configuration
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
API_KEY = os.environ.get('GOOGLE_API_KEY')

def get_youtube_service_with_api_key():
    """
    Get a YouTube API service using an API key (for limited operations).
    
    Returns:
        Resource: YouTube API service
    """
    if DEV_MODE:
        logger.info("Using mock YouTube service in development mode")
        return MockYouTubeService()
    
    # Create a service using the API key
    return build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)

class MockYouTubeService:
    """Mock YouTube service for development mode."""
    
    def search(self):
        return MockSearchResource()
    
    def videos(self):
        return MockVideosResource()
    
    def channels(self):
        return MockChannelsResource()

class MockSearchResource:
    """Mock search resource."""
    
    def list(self, **kwargs):
        return MockRequest({
            "items": [
                {
                    "id": {"videoId": "mock-video-1"},
                    "snippet": {
                        "title": "Mock Video 1",
                        "description": "This is a mock video for testing",
                        "channelTitle": "Mock Channel"
                    }
                },
                {
                    "id": {"videoId": "mock-video-2"},
                    "snippet": {
                        "title": "Mock Video 2",
                        "description": "Another mock video for testing",
                        "channelTitle": "Mock Channel"
                    }
                }
            ]
        })

class MockVideosResource:
    """Mock videos resource."""
    
    def list(self, **kwargs):
        return MockRequest({
            "items": [
                {
                    "id": "mock-video-1",
                    "snippet": {
                        "title": "Mock Video 1",
                        "description": "This is a mock video for testing",
                        "tags": ["mock", "test"]
                    },
                    "statistics": {
                        "viewCount": "1000",
                        "likeCount": "100",
                        "commentCount": "10"
                    }
                }
            ]
        })

class MockChannelsResource:
    """Mock channels resource."""
    
    def list(self, **kwargs):
        return MockRequest({
            "items": [
                {
                    "id": "mock-channel-1",
                    "snippet": {
                        "title": "Mock Channel",
                        "description": "This is a mock channel for testing"
                    },
                    "statistics": {
                        "subscriberCount": "1000",
                        "videoCount": "100"
                    }
                }
            ]
        })

class MockRequest:
    """Mock request object."""
    
    def __init__(self, response):
        self.response = response
    
    def execute(self):
        return self.response

def search_videos(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for videos on YouTube.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of video search results
    """
    youtube = get_youtube_service_with_api_key()
    
    # Call the search.list method to retrieve results
    search_response = youtube.search().list(
        q=query,
        part="id,snippet",
        maxResults=max_results,
        type="video"
    ).execute()
    
    # Process and return the results
    videos = []
    for item in search_response.get("items", []):
        video = {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "channel_title": item["snippet"]["channelTitle"]
        }
        videos.append(video)
    
    return videos

def get_video_details(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Get details for a specific video.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Optional[Dict[str, Any]]: Video details or None if not found
    """
    youtube = get_youtube_service_with_api_key()
    
    # Call the videos.list method to retrieve video details
    video_response = youtube.videos().list(
        id=video_id,
        part="snippet,statistics"
    ).execute()
    
    # Process and return the results
    items = video_response.get("items", [])
    if not items:
        return None
    
    video = items[0]
    return {
        "video_id": video["id"],
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "tags": video["snippet"].get("tags", []),
        "view_count": video["statistics"].get("viewCount", "0"),
        "like_count": video["statistics"].get("likeCount", "0"),
        "comment_count": video["statistics"].get("commentCount", "0")
    }

def get_channel_info(channel_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a YouTube channel.
    
    Args:
        channel_id: YouTube channel ID
        
    Returns:
        Optional[Dict[str, Any]]: Channel information or None if not found
    """
    youtube = get_youtube_service_with_api_key()
    
    # Call the channels.list method to retrieve channel details
    channel_response = youtube.channels().list(
        id=channel_id,
        part="snippet,statistics"
    ).execute()
    
    # Process and return the results
    items = channel_response.get("items", [])
    if not items:
        return None
    
    channel = items[0]
    return {
        "channel_id": channel["id"],
        "title": channel["snippet"]["title"],
        "description": channel["snippet"]["description"],
        "subscriber_count": channel["statistics"].get("subscriberCount", "0"),
        "video_count": channel["statistics"].get("videoCount", "0")
    }

def get_user_videos(max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Get a list of videos for the authenticated user.
    
    Args:
        max_results: Maximum number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of user videos
    """
    if DEV_MODE:
        # Return mock videos in development mode
        videos = []
        for i in range(1, 6):
            videos.append({
                "youtube_id": f"mock-video-{i}",
                "title": f"Mock YouTube Video {i}",
                "description": f"This is a mock YouTube video {i} for testing",
                "upload_date": "2023-03-18",
                "view_count": str(i * 1000),
                "like_count": str(i * 100),
                "comment_count": str(i * 10),
                "thumbnail_url": f"/mock-media/mock-thumb-{i}.jpg"
            })
        return videos
    
    # In production mode, use YouTube API
    try:
        youtube = get_youtube_service_with_api_key()
        
        # Call the search.list method to retrieve the user's videos
        # Note: This is simplified - in a real implementation, you'd want to use the
        # channels.list and then playlistItems.list methods to get all videos from the uploads playlist
        search_response = youtube.search().list(
            part="id,snippet",
            forMine=True,
            type="video",
            maxResults=max_results
        ).execute()
        
        videos = []
        for item in search_response.get("items", []):
            video_id = item["id"]["videoId"]
            video_details = get_video_details(video_id)
            
            if video_details:
                upload_date = item["snippet"]["publishedAt"].split("T")[0]
                videos.append({
                    "youtube_id": video_id,
                    "title": video_details["title"],
                    "description": video_details["description"],
                    "upload_date": upload_date,
                    "view_count": video_details["view_count"],
                    "like_count": video_details["like_count"],
                    "comment_count": video_details["comment_count"],
                    "thumbnail_url": item["snippet"].get("thumbnails", {}).get("medium", {}).get("url", "")
                })
        
        return videos
    except Exception as e:
        logger.error(f"Error getting user videos: {e}")
        return []

def get_video_metrics() -> Dict[str, Any]:
    """
    Get metrics for all user YouTube videos.
    
    Returns:
        Dict[str, Any]: Video metrics
    """
    videos = get_user_videos()
    
    if not videos:
        if DEV_MODE:
            # Generate mock metrics in development mode
            videos = get_user_videos()
            total_views = sum(int(video["view_count"]) for video in videos)
            total_likes = sum(int(video["like_count"]) for video in videos)
            total_videos = len(videos)
            engagement_rate = round((total_likes / total_views * 100) if total_views > 0 else 0, 2)
            
            return {
                "total_videos": total_videos,
                "total_views": str(total_views),
                "total_likes": str(total_likes),
                "engagement_rate": engagement_rate,
                "videos": videos
            }
        return None
    
    # Calculate metrics
    total_views = sum(int(video["view_count"]) for video in videos)
    total_likes = sum(int(video["like_count"]) for video in videos)
    total_videos = len(videos)
    engagement_rate = round((total_likes / total_views * 100) if total_views > 0 else 0, 2)
    
    return {
        "total_videos": total_videos,
        "total_views": str(total_views),
        "total_likes": str(total_likes),
        "engagement_rate": engagement_rate,
        "videos": videos
    }

# Example usage
if __name__ == "__main__":
    if DEV_MODE:
        logger.info("Running in development mode - using mock data")
    else:
        logger.info("Running with real YouTube API")
    
    # Search for videos
    videos = search_videos("Python tutorial", max_results=5)
    logger.info(f"Found {len(videos)} videos:")
    for video in videos:
        logger.info(f"- {video['title']} (ID: {video['video_id']})")
    
    # Get video details
    if videos:
        video_id = videos[0]["video_id"]
        video_details = get_video_details(video_id)
        if video_details:
            logger.info(f"Video details for {video_id}:")
            logger.info(f"- Title: {video_details['title']}")
            logger.info(f"- Views: {video_details['view_count']}")
            logger.info(f"- Likes: {video_details['like_count']}") 