"""
Video model for representing YouTube Shorts in the application.
"""
from datetime import datetime
from pydantic import BaseModel

class Video(BaseModel):
    # this is class defined by learner
    """
    Video model representing a YouTube Short.
    
    Attributes:
        id: Unique identifier for the video
        user_id: ID of the user who created the video
        music_track: Name of the music track used in the video
        upload_status: Current status of the video upload process
        created_at: When the video was created
        updated_at: When the video was last updated
        youtube_id: YouTube video ID once uploaded (if available)
    """
    id: str
    user_id: str
    music_track: str
    upload_status: str  # "pending", "processing", "completed", "failed"
    created_at: datetime
    updated_at: datetime
    youtube_id: str = None 