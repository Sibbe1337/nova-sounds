"""
YouTube API integration for uploading Shorts.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from src.app.core.settings import DEV_MODE

# Set up logging
logger = logging.getLogger(__name__)

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_youtube_service(credentials_dict: Dict[str, Any]):
    """
    Get an authenticated YouTube API service.
    
    Args:
        credentials_dict: Dictionary containing OAuth2 credentials
        
    Returns:
        Resource: Authenticated YouTube API service
    """
    logger.info("Creating YouTube API service")
    credentials = Credentials.from_authorized_user_info(credentials_dict)
    return build('youtube', 'v3', credentials=credentials)

def get_oauth_url(redirect_uri: str) -> str:
    """
    Get the OAuth URL for YouTube API authorization.
    
    Args:
        redirect_uri: Redirect URI for OAuth callback
        
    Returns:
        str: Authorization URL
    """
    client_secrets_file = os.environ.get('CLIENT_SECRETS_FILE', 'client_secret.json')
    
    if not os.path.exists(client_secrets_file):
        logger.error(f"Client secrets file not found: {client_secrets_file}")
        if DEV_MODE:
            return "https://example.com/mock-auth-url"
        raise FileNotFoundError(f"Client secrets file not found: {client_secrets_file}")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    return auth_url

def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token.
    
    Args:
        code: Authorization code from OAuth callback
        redirect_uri: Redirect URI used for OAuth
        
    Returns:
        Dict: Credentials dictionary
    """
    client_secrets_file = os.environ.get('CLIENT_SECRETS_FILE', 'client_secret.json')
    
    if not os.path.exists(client_secrets_file):
        logger.error(f"Client secrets file not found: {client_secrets_file}")
        if DEV_MODE:
            return {
                "token": "mock-token",
                "refresh_token": "mock-refresh-token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "mock-client-id",
                "client_secret": "mock-client-secret",
                "scopes": SCOPES
            }
        raise FileNotFoundError(f"Client secrets file not found: {client_secrets_file}")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def refresh_credentials(credentials_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refresh expired credentials.
    
    Args:
        credentials_dict: Credentials dictionary
        
    Returns:
        Dict: Updated credentials
    """
    credentials = Credentials.from_authorized_user_info(credentials_dict)
    
    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except RefreshError as e:
                logger.error(f"Error refreshing credentials: {e}")
                return None
    
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def upload_to_youtube(credentials: Dict[str, Any], video_path: str, 
                     title: str, description: str, tags: List[str],
                     privacy_status: str = "unlisted") -> Optional[str]:
    """
    Upload a video to YouTube.
    
    Args:
        credentials: YouTube API credentials
        video_path: Path to the video file
        title: Video title
        description: Video description
        tags: List of tags for the video
        privacy_status: Privacy status ("public", "private", or "unlisted")
        
    Returns:
        str: YouTube video ID or None if failed
    """
    logger.info(f"Uploading video to YouTube: {title}")
    
    # In development mode, return a mock ID
    if DEV_MODE:
        logger.info("Dev mode enabled, returning mock YouTube ID")
        import uuid
        return f"MOCK_YT_{uuid.uuid4().hex[:8]}"
    
    try:
        youtube = get_youtube_service(credentials)
        
        # Validate privacy status
        if privacy_status not in ["public", "private", "unlisted"]:
            privacy_status = "unlisted"  # Default to unlisted if invalid
        
        # Set video metadata
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22"  # People & Blogs
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }
        
        # Create upload request
        media = MediaFileUpload(
            video_path, 
            mimetype="video/mp4", 
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        # Execute the upload with progress tracking
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}%")
        
        video_id = response.get('id')
        logger.info(f"Upload complete, video ID: {video_id}")
        return video_id
        
    except Exception as e:
        logger.error(f"Error uploading to YouTube: {e}")
        return None

def analyze_trending_patterns(topic: str = None, days: int = 7) -> Dict[str, Any]:
    """
    Analyze trending patterns on YouTube for a specific topic.
    
    Args:
        topic: Topic to analyze (optional)
        days: Number of days to look back for trend data
        
    Returns:
        Dict containing trend analysis
    """
    logger.info(f"Analyzing YouTube trends for topic: {topic}, days: {days}")
    
    # In development mode, return mock data
    if DEV_MODE:
        import random
        from datetime import datetime, timedelta
        
        # Generate mock trending topics
        trending_topics = [
            "short form content", "music videos", "tutorials", 
            "dance challenges", "comedy skits", "day in the life",
            "react videos", "product reviews", "gaming highlights"
        ]
        
        # Add topic-specific trends if provided
        if topic:
            topic_trends = [f"{topic} challenge", f"{topic} tutorial", f"best {topic}"]
            trending_topics = topic_trends + trending_topics
        
        # Generate mock trend data with increasing view counts
        trend_data = []
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            trend_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "views": random.randint(10000, 50000) * (i + 1),
                "likes": random.randint(1000, 5000) * (i + 1),
                "comments": random.randint(100, 500) * (i + 1),
            })
        
        # Generate optimal posting times
        optimal_times = [
            {"day": "Monday", "time": "6:00 PM", "engagement_factor": 0.8},
            {"day": "Wednesday", "time": "7:30 PM", "engagement_factor": 0.9},
            {"day": "Friday", "time": "5:00 PM", "engagement_factor": 1.0},
            {"day": "Saturday", "time": "12:00 PM", "engagement_factor": 0.95},
            {"day": "Sunday", "time": "3:00 PM", "engagement_factor": 0.85},
        ]
        
        return {
            "trending_topics": trending_topics[:5],
            "trending_hashtags": [f"#{t.replace(' ', '')}" for t in trending_topics[:5]],
            "trend_data": trend_data,
            "optimal_posting_times": optimal_times,
            "summary": "Short-form video content continues to trend upward with dance challenges and tutorials showing the strongest engagement."
        }
    
    # In production, this would use actual YouTube API data
    # using credentials with appropriate scopes for analytics
    # Placeholder for production implementation
    try:
        # Actual implementation would go here
        # For now, we'll throw a not implemented error for non-dev environments
        if not DEV_MODE:
            raise NotImplementedError("YouTube trend analysis not implemented for production yet")
        
    except Exception as e:
        logger.error(f"Error analyzing YouTube trends: {e}")
        return {
            "error": str(e),
            "trending_topics": [],
            "trending_hashtags": [],
            "trend_data": [],
            "optimal_posting_times": []
        }

def get_recommendations_for_content(topic: str = None, genre: str = None) -> Dict[str, Any]:
    """
    Get content recommendations based on topic and music genre.
    
    Args:
        topic: Content topic (optional)
        genre: Music genre (optional)
        
    Returns:
        Dict containing content recommendations
    """
    logger.info(f"Getting content recommendations for topic: {topic}, genre: {genre}")
    
    # In development mode, return mock data
    if DEV_MODE:
        # Base recommendations
        base_recommendations = {
            "title_templates": [
                "Top 10 {topic} Tips",
                "How to {topic} Like a Pro",
                "{topic} Challenge",
                "The Ultimate {topic} Guide",
                "Best {genre} Tracks for {topic} Videos"
            ],
            "hashtags": [
                "#trending", "#viral", "#fyp", "#foryoupage",
                "#shortsvideo", "#youtubeshorts"
            ],
            "video_formats": [
                {"name": "Tutorial", "engagement_score": 0.85},
                {"name": "Challenge", "engagement_score": 0.92},
                {"name": "Day in the Life", "engagement_score": 0.78},
                {"name": "Review", "engagement_score": 0.76},
                {"name": "Behind the Scenes", "engagement_score": 0.81}
            ]
        }
        
        # Add topic-specific recommendations
        if topic:
            base_recommendations["hashtags"].extend([
                f"#{topic.replace(' ', '')}", 
                f"#{topic.replace(' ', '')}challenge",
                f"#{topic.replace(' ', '')}tips"
            ])
        
        # Add genre-specific recommendations
        if genre:
            base_recommendations["hashtags"].append(f"#{genre.replace(' ', '')}")
            base_recommendations["title_templates"].append(f"Best {genre} Mix for {topic or 'Your Content'}")
        
        return {
            "recommendations": base_recommendations,
            "insights": "Videos with clear calls-to-action and engaging thumbnails perform 43% better than those without."
        }
    
    # In production, this would use actual YouTube API data and ML models
    # Placeholder for production implementation
    try:
        # Actual implementation would go here
        # For now, we'll throw a not implemented error for non-dev environments
        if not DEV_MODE:
            raise NotImplementedError("Content recommendations not implemented for production yet")
        
    except Exception as e:
        logger.error(f"Error getting content recommendations: {e}")
        return {
            "error": str(e),
            "recommendations": {
                "title_templates": [],
                "hashtags": [],
                "video_formats": []
            }
        } 