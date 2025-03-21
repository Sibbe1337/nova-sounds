"""
Metadata generation API using OpenAI for YouTube Shorts, TikTok, and Instagram Reels
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from ..core.settings import DEV_MODE

# Set up router
router = APIRouter(
    prefix="/metadata",
    tags=["metadata"],
    responses={404: {"description": "Not found"}}
)

# Set up logging
logger = logging.getLogger(__name__)

# Get OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Check if we have OpenAI installed
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    
    # Configure OpenAI API key
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        logger.warning("OpenAI API key not found. Metadata generation will use mock data.")
        OPENAI_AVAILABLE = False
except ImportError:
    logger.warning("OpenAI package not installed. Metadata generation will use mock data.")
    OPENAI_AVAILABLE = False

# Models for metadata generation
class MetadataRequest(BaseModel):
    track: Optional[Dict[str, Any]] = None
    style: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None
    max_titles: int = 3
    max_descriptions: int = 2
    max_hashtags: int = 15
    platform: str = "youtube"  # youtube, tiktok, instagram

class MetadataResponse(BaseModel):
    titles: List[str]
    descriptions: List[str]
    hashtags: List[str]

@router.post("/generate", response_model=MetadataResponse)
async def generate_metadata(request: MetadataRequest = Body(...)):
    """
    Generate SEO-optimized metadata for social media videos
    
    Uses OpenAI to generate titles, descriptions, and hashtags based on:
    - Music track information (title, artist, genre, mood, bpm)
    - Video style/preset
    - Platform-specific formatting
    """
    try:
        # If in dev mode or OpenAI not available, return mock data
        if DEV_MODE or not OPENAI_AVAILABLE:
            logger.info("Using mock data for metadata generation")
            return get_mock_metadata(request)
        
        # Extract information from request
        track_info = request.track or {}
        style_info = request.style or {}
        
        # Create a prompt for OpenAI
        prompt = create_metadata_prompt(
            track_info=track_info,
            style_info=style_info,
            platform=request.platform
        )
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better creative results
            messages=[
                {"role": "system", "content": "You are an expert social media marketer specializing in creating viral content for YouTube Shorts, TikTok, and Instagram Reels. You excel at writing engaging titles, descriptions, and hashtags that maximize engagement, views, and shares."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        # Extract and parse the response
        content = response.choices[0].message.content
        parsed_response = parse_openai_response(content)
        
        # Limit the number of results
        result = {
            "titles": parsed_response.get("titles", [])[:request.max_titles],
            "descriptions": parsed_response.get("descriptions", [])[:request.max_descriptions],
            "hashtags": parsed_response.get("hashtags", [])[:request.max_hashtags]
        }
        
        return result
    except Exception as e:
        logger.error(f"Error generating metadata: {str(e)}")
        if DEV_MODE:
            # Return mock data in dev mode even if there's an error
            return get_mock_metadata(request)
        raise HTTPException(status_code=500, detail=f"Failed to generate metadata: {str(e)}")

def create_metadata_prompt(track_info: Dict[str, Any], style_info: Dict[str, Any], platform: str) -> str:
    """
    Create a detailed prompt for OpenAI to generate metadata.
    """
    track_title = track_info.get("title", "Unknown Track")
    track_artist = track_info.get("artist", "Unknown Artist")
    track_genre = track_info.get("genre", track_info.get("genres", ["Unknown"])[0] if isinstance(track_info.get("genres", []), list) and len(track_info.get("genres", [])) > 0 else "Unknown")
    track_mood = track_info.get("mood", track_info.get("moods", ["Neutral"])[0] if isinstance(track_info.get("moods", []), list) and len(track_info.get("moods", [])) > 0 else "Neutral")
    track_bpm = track_info.get("bpm", 0)
    
    style_name = style_info.get("name", "Standard")
    style_desc = style_info.get("description", "")
    
    # Craft the prompt
    prompt = f"""Generate engaging metadata for a short-form video synced to music for {platform.upper()}.

MUSIC TRACK DETAILS:
- Title: {track_title}
- Artist: {track_artist}
- Genre: {track_genre}
- Mood: {track_mood}
- BPM: {track_bpm}

VIDEO STYLE:
- Style: {style_name}
- Description: {style_desc}

PLATFORM: {platform.upper()}

This video features visuals that are synchronized to the beat and mood of the music. 
The video uses AI technology to create beat-synced effects.

Please provide the following in JSON format:
1. A list of 5 attention-grabbing titles/captions (short and compelling, with emojis where appropriate)
2. A list of 3 detailed descriptions (engaging, with calls to action)
3. A list of 15-20 relevant hashtags (include both trending and niche hashtags)

Format your response as a valid JSON object with these keys: "titles", "descriptions", and "hashtags"
"""

    return prompt

def parse_openai_response(content: str) -> Dict[str, List[str]]:
    """
    Parse the OpenAI response to extract titles, descriptions, and hashtags.
    """
    # Attempt to extract JSON from the response
    try:
        # Check if the response contains a JSON block
        if "```json" in content:
            json_content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_content = content.split("```")[1].strip()
        else:
            json_content = content.strip()
        
        # Parse the JSON
        data = json.loads(json_content)
        return {
            "titles": data.get("titles", []),
            "descriptions": data.get("descriptions", []),
            "hashtags": data.get("hashtags", [])
        }
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning(f"Failed to parse JSON from OpenAI response: {e}")
        logger.debug(f"Raw response: {content}")
        
        # Fallback parsing for non-JSON responses
        titles = []
        descriptions = []
        hashtags = []
        
        sections = content.split("\n\n")
        current_section = None
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            if "TITLES" in section.upper() or "CAPTIONS" in section.upper():
                current_section = "titles"
                continue
            elif "DESCRIPTIONS" in section.upper():
                current_section = "descriptions"
                continue
            elif "HASHTAGS" in section.upper():
                current_section = "hashtags"
                continue
                
            if current_section == "titles":
                # Extract titles (look for numbered or bullet items)
                for line in section.split("\n"):
                    if line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "-", "•")):
                        titles.append(line.split(".", 1)[1].strip() if line[0].isdigit() else line.strip()[1:].strip())
            elif current_section == "descriptions":
                # Extract descriptions
                for line in section.split("\n"):
                    if line.strip().startswith(("1.", "2.", "3.", "-", "•")):
                        descriptions.append(line.split(".", 1)[1].strip() if line[0].isdigit() else line.strip()[1:].strip())
            elif current_section == "hashtags":
                # Extract hashtags
                hashtag_text = section.replace(",", " ").replace("\n", " ")
                hashtag_candidates = hashtag_text.split()
                for tag in hashtag_candidates:
                    tag = tag.strip()
                    if tag.startswith("#"):
                        hashtags.append(tag)
                    elif tag and not tag.startswith(("1.", "2.", "3.", "-", "•")):
                        hashtags.append(f"#{tag}")
        
        return {
            "titles": titles,
            "descriptions": descriptions,
            "hashtags": hashtags
        }

def get_mock_metadata(request: MetadataRequest) -> Dict[str, List[str]]:
    """
    Generate mock metadata for development and testing.
    """
    platform = request.platform.lower()
    
    titles = [
        "This Beat Drop Will Make You Dance! 🎵 #shorts",
        "Viral Music Visualizer That Syncs Perfectly! 🔥",
        "Watch How The Music Creates This Amazing Visual! ✨",
        "The Most Satisfying Beat-Sync You'll See Today 👀",
        "When AI Meets Music - Mind-Blowing Results! 🤯"
    ]
    
    descriptions = [
        "Check out this incredible music-responsive visual that transforms with every beat! Created using AI technology. Perfect for your next TikTok or Instagram post. Like and subscribe for more amazing content like this!",
        "Stunning visuals that react to every beat and melody. This AI-generated video syncs perfectly with the music to create a mesmerizing experience. Share with friends who appreciate good music and incredible visuals!"
    ]
    
    hashtags = [
        "#shorts", "#musicvisualization", "#beatdrop", "#viral", "#trending", 
        "#musicproduction", "#soundtok", "#visualizer", "#aigenerated", 
        "#musicvideo", "#tiktokmusic", "#soundeffects", "#musicsync", "#viralvideo", "#fyp"
    ]
    
    # Add platform-specific hashtags
    if platform == "youtube":
        hashtags.extend(["#youtubeshorts", "#shortsyoutube", "#shortvideo"])
    elif platform == "tiktok":
        hashtags.extend(["#tiktoktrend", "#tiktokviral", "#foryoupage", "#tiktokalgorithm"])
    elif platform == "instagram":
        hashtags.extend(["#reels", "#instareels", "#reelsinstagram", "#instadaily"])
    
    return {
        "titles": titles[:request.max_titles],
        "descriptions": descriptions[:request.max_descriptions],
        "hashtags": hashtags[:request.max_hashtags]
    } 