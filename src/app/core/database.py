"""
Simple in-memory database for the YouTube Shorts Machine MVP.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import time

# Define DATA_DIR instead of importing it from settings
DATA_DIR = os.path.join(os.getcwd(), "data")

# Set up logging
logger = logging.getLogger(__name__)

# In-memory database (for MVP)
VIDEOS = {}
ANALYTICS = {}
USERS = {}
# Add user music preferences storage
MUSIC_PREFERENCES = {}

# Load mock data from file if available
MOCK_DATA_FILE = os.path.join(os.getcwd(), "mock-data", "videos.json")
MOCK_ANALYTICS_FILE = os.path.join(os.getcwd(), "mock-data", "analytics.json")
# Add path for music preferences
MOCK_MUSIC_PREFS_FILE = os.path.join(os.getcwd(), "mock-data", "music_preferences.json")

def _get_db() -> Dict[str, Any]:
    """
    Get the database instance.
    
    Returns:
        Dict: The in-memory database
    """
    return VIDEOS

class DatabaseService:
    """Database service with async methods for application data access."""
    
    async def get_user_videos(self, user_id: str) -> List[Dict[str, Any]]:
        """Get videos for a specific user."""
        # In a real implementation, this would query a real database
        return [v for v in VIDEOS.values() if v.get("user_id") == user_id]
    
    async def get_video(self, video_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a video by ID, optionally filtered by user."""
        video = VIDEOS.get(video_id)
        if video and (user_id is None or video.get("user_id") == user_id):
            return video
        return None
    
    async def store_platform_analytics(self, video_id: str, platform: str, timestamp: datetime, metrics: Dict[str, Any]) -> bool:
        """Store analytics metrics for a platform."""
        if video_id not in ANALYTICS:
            ANALYTICS[video_id] = {}
        
        if platform not in ANALYTICS[video_id]:
            ANALYTICS[video_id][platform] = []
        
        ANALYTICS[video_id][platform].append({
            "timestamp": timestamp,
            "metrics": metrics
        })
        
        _save_mock_analytics()
        return True
    
    async def get_heatmap_data(self, video_id: str, platform: Optional[str] = None) -> List[List[Any]]:
        """Get engagement heatmap data for a video."""
        # In a real implementation, this would query a real database
        # Return empty list if no data
        return []
    
    async def get_historical_analytics(self, video_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical analytics data for a video."""
        # In a real implementation, this would query a real database
        if video_id not in ANALYTICS:
            return []
            
        result = []
        now = datetime.now()
        cutoff_date = now - timedelta(days=days)
        
        for platform, data_points in ANALYTICS[video_id].items():
            for data in data_points:
                if data["timestamp"] >= cutoff_date:
                    result.append({
                        "date": data["timestamp"],
                        "platform": platform,
                        **data["metrics"]
                    })
        
        return result
    
    async def get_content_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get content trend data."""
        # In a real implementation, this would query a real database
        # Return empty list for now
        return []
    
    async def get_subscriber_count(self, user_id: str) -> int:
        """Get subscriber count for a user."""
        # In a real implementation, this would query a real database
        user = USERS.get(user_id, {})
        return user.get("subscribers", 0)
    
    async def get_music_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get music preferences for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dict[str, Any]: User music preferences or empty dict if not found
        """
        return MUSIC_PREFERENCES.get(user_id, {})
    
    async def save_music_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Save music preferences for a user.
        
        Args:
            user_id: The user ID
            preferences: The user's music preferences
            
        Returns:
            bool: True if saved successfully
        """
        MUSIC_PREFERENCES[user_id] = preferences
        _save_music_preferences()
        return True

def get_db():
    """
    Returns a database service with async methods.
    
    Returns:
        DatabaseService: The database service
    """
    return DatabaseService()

def _save_mock_data():
    """
    Save the in-memory database to a file.
    """
    if not os.path.exists(os.path.dirname(MOCK_DATA_FILE)):
        os.makedirs(os.path.dirname(MOCK_DATA_FILE))
    
    with open(MOCK_DATA_FILE, "w") as f:
        json.dump(VIDEOS, f, default=str, indent=2)
    
    logger.info(f"Saved {len(VIDEOS)} videos to mock database file")

def _save_mock_analytics():
    """
    Save the in-memory analytics to a file.
    """
    if not os.path.exists(os.path.dirname(MOCK_ANALYTICS_FILE)):
        os.makedirs(os.path.dirname(MOCK_ANALYTICS_FILE))
    
    with open(MOCK_ANALYTICS_FILE, "w") as f:
        json.dump(ANALYTICS, f, default=str, indent=2)
    
    logger.info(f"Saved analytics data for {len(ANALYTICS)} videos")

def _save_music_preferences():
    """
    Save the in-memory music preferences to a file.
    """
    if not os.path.exists(os.path.dirname(MOCK_MUSIC_PREFS_FILE)):
        os.makedirs(os.path.dirname(MOCK_MUSIC_PREFS_FILE))
    
    with open(MOCK_MUSIC_PREFS_FILE, "w") as f:
        json.dump(MUSIC_PREFERENCES, f, default=str, indent=2)
    
    logger.info(f"Saved music preferences for {len(MUSIC_PREFERENCES)} users")

def _load_mock_data():
    """
    Load mock data from a file.
    """
    if os.path.exists(MOCK_DATA_FILE):
        try:
            with open(MOCK_DATA_FILE, "r") as f:
                data = json.load(f)
                VIDEOS.update(data)
            logger.info(f"Loaded {len(VIDEOS)} videos from mock database file")
        except Exception as e:
            logger.error(f"Error loading mock data: {e}")
    
    if os.path.exists(MOCK_ANALYTICS_FILE):
        try:
            with open(MOCK_ANALYTICS_FILE, "r") as f:
                data = json.load(f)
                ANALYTICS.update(data)
            logger.info(f"Loaded analytics data for {len(ANALYTICS)} videos")
        except Exception as e:
            logger.error(f"Error loading mock analytics data: {e}")
    
    # Load music preferences
    if os.path.exists(MOCK_MUSIC_PREFS_FILE):
        try:
            with open(MOCK_MUSIC_PREFS_FILE, "r") as f:
                data = json.load(f)
                MUSIC_PREFERENCES.update(data)
            logger.info(f"Loaded music preferences for {len(MUSIC_PREFERENCES)} users")
        except Exception as e:
            logger.error(f"Error loading music preferences data: {e}")

# Try to load mock data at import time
_load_mock_data()

def create_video(video_id: str, video_data: Dict[str, Any]) -> str:
    """
    Create a new video record.
    
    Args:
        video_id: ID for the new video
        video_data: Video data
        
    Returns:
        str: Video ID
    """
    VIDEOS[video_id] = video_data
    _save_mock_data()
    return video_id

def get_video(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a video by ID.
    
    Args:
        video_id: Video ID
        
    Returns:
        Video data or None if not found
    """
    file_path = os.path.join(DATA_DIR, "videos", f"{video_id}.json")
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error getting video {video_id}: {e}")
        return None

def get_video_by_id(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a video by ID (alias for get_video)
    
    Args:
        video_id: The video ID
        
    Returns:
        The video data or None if not found
    """
    return get_video(video_id)

def update_video(video_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Update a video record.
    
    Args:
        video_id: Video ID
        update_data: Data to update
        
    Returns:
        bool: True if updated, False if not found
    """
    file_path = os.path.join(DATA_DIR, "videos", f"{video_id}.json")
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                video_data = json.load(f)
            
            # Update data
            video_data.update(update_data)
            
            with open(file_path, "w") as f:
                json.dump(video_data, f, indent=2)
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating video {video_id}: {e}")
        return False

def delete_video(video_id: str) -> bool:
    """
    Delete a video.
    
    Args:
        video_id: Video ID
        
    Returns:
        bool: True if deleted, False if not found
    """
    file_path = os.path.join(DATA_DIR, "videos", f"{video_id}.json")
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting video {video_id}: {e}")
        return False

def list_videos(limit: int = 100, skip: int = 0, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all videos, with optional filtering by status.
    
    Args:
        limit: Maximum number of videos to return
        skip: Number of videos to skip (for pagination)
        status: Optional status filter
        
    Returns:
        List of videos
    """
    db = _get_db()
    all_videos = list(db.values())
    
    # Filter by status if provided
    if status:
        all_videos = [v for v in all_videos if v.get("status") == status]
    
    # Sort by created_at, handling both string and datetime formats
    def get_created_at(video):
        created_at = video.get("created_at", "")
        # If it's already a datetime, return it
        if isinstance(created_at, datetime):
            return created_at
        # If it's a string, try to parse it as ISO format
        if isinstance(created_at, str) and created_at:
            try:
                return datetime.fromisoformat(created_at)
            except ValueError:
                return datetime.min
        # Default for empty or invalid values
        return datetime.min
    
    all_videos.sort(key=get_created_at, reverse=True)
    
    # Apply pagination
    if skip >= len(all_videos):
        return []
    
    end = min(skip + limit, len(all_videos))
    return all_videos[skip:end]

# Add simple sync functions for music preferences
def get_music_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get music preferences for a user (sync version).
    
    Args:
        user_id: The user ID
        
    Returns:
        Dict[str, Any]: User music preferences or empty dict if not found
    """
    return MUSIC_PREFERENCES.get(user_id, {})

def save_music_preferences(user_id: str, preferences: Dict[str, Any]) -> bool:
    """
    Save music preferences for a user (sync version).
    
    Args:
        user_id: The user ID
        preferences: The user's music preferences
        
    Returns:
        bool: True if saved successfully
    """
    MUSIC_PREFERENCES[user_id] = preferences
    _save_music_preferences()
    return True

def delete_music_preferences(user_id: str) -> bool:
    """
    Delete music preferences for a user.
    
    Args:
        user_id: The user ID
        
    Returns:
        bool: True if deleted, False if not found
    """
    if user_id in MUSIC_PREFERENCES:
        del MUSIC_PREFERENCES[user_id]
        _save_music_preferences()
        return True
    return False

def create_scheduled_task(task_id: str, data: Dict[str, Any]) -> bool:
    """
    Create a new scheduled task.
    
    Args:
        task_id: Task ID
        data: Task data
        
    Returns:
        True if successful, False otherwise
    """
    file_path = os.path.join(DATA_DIR, "scheduler", f"{task_id}.json")
    
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error creating scheduled task {task_id}: {e}")
        return False

def get_scheduled_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a scheduled task by ID.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task data or None if not found
    """
    file_path = os.path.join(DATA_DIR, "scheduler", f"{task_id}.json")
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error getting scheduled task {task_id}: {e}")
        return None

def update_scheduled_task(task_id: str, data: Dict[str, Any]) -> bool:
    """
    Update an existing scheduled task.
    
    Args:
        task_id: Task ID
        data: Task data to update
        
    Returns:
        True if successful, False otherwise
    """
    file_path = os.path.join(DATA_DIR, "scheduler", f"{task_id}.json")
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating scheduled task {task_id}: {e}")
        return False

def delete_scheduled_task(task_id: str) -> bool:
    """
    Delete a scheduled task.
    
    Args:
        task_id: Task ID
        
    Returns:
        True if successful, False otherwise
    """
    file_path = os.path.join(DATA_DIR, "scheduler", f"{task_id}.json")
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting scheduled task {task_id}: {e}")
        return False

def get_scheduled_tasks() -> List[Dict[str, Any]]:
    """
    Get all scheduled tasks.
    
    Returns:
        List of scheduled tasks
    """
    scheduler_dir = os.path.join(DATA_DIR, "scheduler")
    tasks = []
    
    try:
        for filename in os.listdir(scheduler_dir):
            if filename.endswith(".json"):
                task_id = filename[:-5]  # Remove .json extension
                task_data = get_scheduled_task(task_id)
                if task_data:
                    tasks.append(task_data)
        return tasks
    except Exception as e:
        logger.error(f"Error getting scheduled tasks: {e}")
        return [] 