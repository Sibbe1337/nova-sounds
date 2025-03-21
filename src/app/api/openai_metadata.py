"""
API endpoints for generating video metadata using OpenAI.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import json
from datetime import datetime

from src.app.core.settings import DEV_MODE
from src.app.services.gcs.music_metadata import get_track_metadata

# Setup router
router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)

# Check if OpenAI is configured
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_AVAILABLE = bool(OPENAI_API_KEY) or DEV_MODE

class MetadataRequest(BaseModel):
    """Request model for metadata generation."""
    track_name: str
    genre: Optional[str] = None
    mood: Optional[str] = None
    topic: Optional[str] = None
    keywords: Optional[List[str]] = None
    video_type: str = "shorts"
    include_hashtags: bool = True
    include_emoji: bool = True
    style: str = "standard"

class MetadataResponse(BaseModel):
    """Response model for generated metadata."""
    title: str
    description: str
    hashtags: List[str]
    keywords: List[str]
    
def _get_mock_metadata(request: MetadataRequest) -> Dict[str, Any]:
    """Generate mock metadata for development mode."""
    track_meta = {}
    try:
        track_meta = get_track_metadata(request.track_name) or {}
    except:
        pass
    
    genre = request.genre or track_meta.get("genre", "Unknown")
    mood = request.mood or track_meta.get("mood", "Neutral")
    
    mock_data = {
        "title": f"Amazing {genre} {request.video_type.capitalize()} with {mood} Vibes 🎵",
        "description": f"Check out this incredible {genre} track with {mood} vibes. Perfect for your {request.video_type} content!",
        "hashtags": [
            f"#{genre.replace(' ', '')}", 
            f"#{mood.replace(' ', '')}", 
            f"#{request.video_type}", 
            "#trending", 
            "#fyp", 
            "#viral",
            "#music"
        ],
        "keywords": [genre, mood, "music", request.video_type, "content", "viral"]
    }
    
    if request.topic:
        mock_data["title"] = f"{request.topic.capitalize()} {mock_data['title']}"
        mock_data["description"] = f"{request.topic.capitalize()} content: {mock_data['description']}"
        mock_data["hashtags"].append(f"#{request.topic.replace(' ', '')}")
        mock_data["keywords"].append(request.topic)
    
    if request.keywords:
        mock_data["keywords"].extend(request.keywords)
        mock_data["hashtags"].extend([f"#{keyword.replace(' ', '')}" for keyword in request.keywords[:3]])
    
    return mock_data

def generate_metadata_with_openai(request: MetadataRequest) -> Dict[str, Any]:
    """
    Generate metadata using OpenAI API.
    
    In production, this would use the OpenAI API to generate metadata.
    For the MVP, we'll use a placeholder implementation.
    
    Args:
        request: Metadata generation request
        
    Returns:
        Generated metadata
    """
    if not OPENAI_API_KEY and not DEV_MODE:
        logger.warning("OpenAI API key not configured")
        raise ValueError("OpenAI API key not configured")
    
    if DEV_MODE:
        logger.info("Using mock implementation for OpenAI metadata generation")
        return _get_mock_metadata(request)
    
    # In production, this would use the OpenAI API
    try:
        import openai
        
        # Set API key
        openai.api_key = OPENAI_API_KEY
        
        # Get track metadata if available
        track_meta = {}
        try:
            track_meta = get_track_metadata(request.track_name) or {}
        except Exception as e:
            logger.warning(f"Error getting track metadata: {e}")
        
        # Prepare prompt
        genre = request.genre or track_meta.get("genre", "Unknown")
        mood = request.mood or track_meta.get("mood", "Neutral")
        track_title = track_meta.get("title", request.track_name)
        
        # Build the system prompt
        system_prompt = f"""
        You are a expert social media content creator specializing in {request.video_type}.
        Create engaging metadata for a {request.video_type} video featuring {genre} music with a {mood} mood.
        The music track is: {track_title}
        """
        
        if request.topic:
            system_prompt += f"\nThe content is about: {request.topic}"
        
        if request.keywords:
            keywords_text = ", ".join(request.keywords)
            system_prompt += f"\nInclude these keywords if possible: {keywords_text}"
        
        # Build the user prompt
        user_prompt = f"""
        Please generate the following for my {request.video_type} video:
        1. A catchy title (maximum 100 characters)
        2. An engaging description (1-2 sentences)
        3. 5-7 relevant hashtags
        4. 5-7 SEO keywords
        
        Style: {request.style}
        Include emojis: {'Yes' if request.include_emoji else 'No'}
        
        Format your response as a JSON object with the following structure:
        {{
            "title": "Your title here",
            "description": "Your description here",
            "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
            "keywords": ["keyword1", "keyword2", "keyword3"]
        }}
        """
        
        # Make API call
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse response
        response_text = response.choices[0].message.content
        
        # Extract JSON from response
        try:
            metadata = json.loads(response_text)
            
            # Validate and format response
            if "title" not in metadata or "description" not in metadata or "hashtags" not in metadata:
                raise ValueError("Invalid response format from OpenAI")
            
            # Format hashtags to include #
            metadata["hashtags"] = [
                tag if tag.startswith("#") else f"#{tag}" 
                for tag in metadata["hashtags"]
            ]
            
            return metadata
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse OpenAI response as JSON: {response_text}")
            return _get_mock_metadata(request)
            
    except Exception as e:
        logger.error(f"Error using OpenAI API: {e}")
        return _get_mock_metadata(request)

@router.post("/generate", response_model=MetadataResponse)
async def generate_metadata(request: MetadataRequest):
    """
    Generate video metadata using OpenAI.
    
    Args:
        request: Metadata generation request
        
    Returns:
        Generated metadata
    """
    try:
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI API not available, using mock data")
            metadata = _get_mock_metadata(request)
        else:
            metadata = generate_metadata_with_openai(request)
        
        return {
            "title": metadata["title"],
            "description": metadata["description"],
            "hashtags": metadata["hashtags"],
            "keywords": metadata["keywords"]
        }
    except Exception as e:
        logger.error(f"Error generating metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 