"""
YouTube trend analysis service for optimizing Shorts content.
"""
import os
import logging
import json
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta

from src.app.services.youtube.api import get_youtube_service
from src.app.core.settings import DEV_MODE

# Set up logging
logger = logging.getLogger(__name__)

# Mock data for development mode
MOCK_TRENDS = {
    "trending_topics": [
        "dance challenge", "cooking hack", "life hack", "product review",
        "day in my life", "reaction", "transformation", "before and after"
    ],
    "trending_hashtags": [
        "#fyp", "#viral", "#trending", "#foryou", "#short",
        "#learnontiktok", "#howto", "#satisfying"
    ],
    "optimal_title_length": 40,
    "optimal_description_length": 120,
    "trending_shorts": [
        {
            "title": "I tried this viral food hack and it actually worked! 😱",
            "views": 1200000,
            "likes": 180000,
            "hashtags": ["#foodhack", "#viral", "#cooking", "#shorts"],
            "duration": 58
        },
        {
            "title": "This simple morning routine changed my life",
            "views": 870000,
            "likes": 125000,
            "hashtags": ["#productivity", "#morning", "#routine", "#shorts"],
            "duration": 52
        },
        {
            "title": "POV: When your cat decides it's 3AM zoomies time",
            "views": 2100000,
            "likes": 310000,
            "hashtags": ["#cat", "#funny", "#pov", "#shorts"],
            "duration": 45
        }
    ]
}

def get_trending_shorts(region_code: str = 'US', max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch trending YouTube Shorts.
    
    Args:
        region_code: Country code for trending data
        max_results: Maximum number of results to return
        
    Returns:
        List of trending Shorts with metadata
    """
    if DEV_MODE:
        logger.info("Using mock trending data in development mode")
        return MOCK_TRENDS["trending_shorts"]
    
    try:
        # Get authenticated YouTube service
        youtube = get_youtube_service()
        
        # Search for trending shorts
        # Use videoCategoryId=10 for music if focusing on music shorts
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            chart="mostPopular",
            maxResults=max_results,
            regionCode=region_code,
            videoDuration="short"
        )
        
        response = request.execute()
        
        trending_shorts = []
        for item in response.get("items", []):
            # Check if it's a Short (vertical video)
            if "contentDetails" in item and "duration" in item["contentDetails"]:
                duration = item["contentDetails"]["duration"]
                # Most Shorts are under 60 seconds
                if "PT" in duration and "M" not in duration:
                    seconds = int(duration.replace("PT", "").replace("S", ""))
                    if seconds <= 60:
                        trending_shorts.append({
                            "title": item["snippet"]["title"],
                            "views": int(item["statistics"].get("viewCount", 0)),
                            "likes": int(item["statistics"].get("likeCount", 0)),
                            "hashtags": extract_hashtags(item["snippet"].get("description", "")),
                            "duration": seconds,
                            "video_id": item["id"],
                            "description": item["snippet"].get("description", ""),
                            "thumbnail_url": item["snippet"]["thumbnails"]["high"]["url"]
                        })
        
        return trending_shorts
        
    except Exception as e:
        logger.error(f"Error fetching trending Shorts: {e}")
        # Fall back to mock data in case of error
        return MOCK_TRENDS["trending_shorts"]

def analyze_trending_patterns() -> Dict[str, Any]:
    """
    Analyze trending Shorts to identify patterns.
    
    Returns:
        Dictionary with trend analysis
    """
    trending_shorts = get_trending_shorts(max_results=50)
    
    if not trending_shorts:
        return MOCK_TRENDS
    
    # Extract hashtags from all trending shorts
    all_hashtags = []
    for short in trending_shorts:
        all_hashtags.extend(short.get("hashtags", []))
    
    # Count frequency of hashtags
    hashtag_count = {}
    for tag in all_hashtags:
        if tag in hashtag_count:
            hashtag_count[tag] += 1
        else:
            hashtag_count[tag] = 1
    
    # Sort by frequency
    trending_hashtags = sorted(hashtag_count.keys(), 
                              key=lambda x: hashtag_count[x], 
                              reverse=True)[:10]
    
    # Analyze title patterns
    title_lengths = [len(short["title"]) for short in trending_shorts]
    avg_title_length = sum(title_lengths) / len(title_lengths) if title_lengths else 40
    
    # Analyze description patterns
    desc_lengths = [len(short.get("description", "")) for short in trending_shorts]
    avg_desc_length = sum(desc_lengths) / len(desc_lengths) if desc_lengths else 120
    
    # Extract topics (simplified)
    topics = ["dance", "cooking", "hack", "review", "tutorial", "reaction", "challenge"]
    topic_count = {}
    for topic in topics:
        count = sum(1 for short in trending_shorts if topic.lower() in short["title"].lower())
        topic_count[topic] = count
    
    trending_topics = sorted(topic_count.keys(), 
                            key=lambda x: topic_count[x], 
                            reverse=True)[:8]
    
    return {
        "trending_topics": trending_topics,
        "trending_hashtags": trending_hashtags,
        "optimal_title_length": round(avg_title_length),
        "optimal_description_length": round(avg_desc_length),
        "trending_shorts": trending_shorts[:10]  # Return top 10 shorts
    }

def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text containing hashtags
        
    Returns:
        List of hashtags
    """
    words = text.split()
    hashtags = [word for word in words if word.startswith("#")]
    return hashtags

def get_recommendations_for_content(images: List[str], music_track: str) -> Dict[str, Any]:
    """
    Get content recommendations based on images and music track.
    
    Args:
        images: List of image paths
        music_track: Music track name
        
    Returns:
        Dictionary with content recommendations
    """
    # This would ideally use AI vision to analyze image content
    # and music analysis to understand the track characteristics
    
    # For now, we'll return trend-based recommendations
    trend_data = analyze_trending_patterns()
    
    music_genre = extract_genre_from_track_name(music_track)
    
    # Create recommendations
    recommendations = {
        "suggested_hashtags": trend_data["trending_hashtags"][:5],
        "title_templates": [
            f"This {music_genre} trend is taking over YouTube! #shorts",
            f"I tried the viral {trend_data['trending_topics'][0]} challenge",
            f"How to {trend_data['trending_topics'][1]} in under 60 seconds",
            f"My {music_genre} transformation journey"
        ],
        "description_templates": [
            f"Check out this {music_genre} short! {' '.join(trend_data['trending_hashtags'][:3])}",
            f"Trying the viral {trend_data['trending_topics'][0]} trend with {music_track} {' '.join(trend_data['trending_hashtags'][:3])}",
            f"Follow for more {music_genre} content! {' '.join(trend_data['trending_hashtags'][:3])}"
        ],
        "optimal_title_length": trend_data["optimal_title_length"],
        "optimal_description_length": trend_data["optimal_description_length"]
    }
    
    return recommendations

def extract_genre_from_track_name(track_name: str) -> str:
    """
    Extract music genre from track name.
    
    Args:
        track_name: Name of the music track
        
    Returns:
        Extracted genre or default
    """
    # This is a simplistic approach - would be better with actual music metadata
    genres = ["pop", "rock", "hip hop", "rap", "electronic", "dance", "lo-fi", "jazz", "acoustic"]
    
    track_lower = track_name.lower()
    for genre in genres:
        if genre in track_lower:
            return genre
    
    # Default fallback
    return "music" 