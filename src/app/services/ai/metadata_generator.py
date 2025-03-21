"""
AI-powered metadata generator for YouTube Shorts.
"""
import os
import logging
import json
import requests
from typing import List, Dict, Any, Optional
import random
from datetime import datetime

from src.app.core.settings import DEV_MODE

# Set up logging
logger = logging.getLogger(__name__)

# Check if OpenAI API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
USE_OPENAI = OPENAI_API_KEY is not None and not DEV_MODE

# Mock data for development
MOCK_RESPONSES = {
    "titles": [
        "This amazing transformation will blow your mind! #shorts",
        "How to create stunning visuals in just 60 seconds",
        "The perfect routine for your daily inspiration",
        "Watch this before you try the viral trend!",
        "You won't believe what happened when I tried this",
    ],
    "descriptions": [
        "Check out this amazing short I created! Don't forget to like and subscribe for more content like this. #shorts #trending #viral",
        "This took me hours to make but only seconds to watch! Hope you enjoy this short. Follow for more content! #shorts #create #trending",
        "Trying out the latest trend with my own twist. Let me know what you think in the comments! #shorts #viral #fyp",
        "The perfect way to brighten your day in under a minute. Share if you enjoyed! #shorts #viral #foryoupage",
    ],
    "hashtags": [
        ["#shorts", "#viral", "#trending", "#foryou"],
        ["#shorts", "#fyp", "#music", "#viralvideo"],
        ["#shorts", "#creative", "#tutorial", "#learn"],
        ["#shorts", "#transformation", "#satisfying", "#oddlysatisfying"],
    ]
}

def generate_title(
    topic: str,
    trending_topics: List[str],
    music_track: str,
    image_content: Optional[List[str]] = None,
    max_length: int = 70
) -> str:
    """
    Generate a catchy title for a YouTube Short video.
    
    Args:
        topic: The main topic of the video
        trending_topics: List of currently trending topics
        music_track: The name of the music track used
        image_content: Optional list of image content descriptions
        max_length: Maximum length of the title
        
    Returns:
        A catchy title for the video
    """
    if DEV_MODE or not USE_OPENAI:
        # Use mock data in development mode
        return random.choice(MOCK_RESPONSES["titles"])
    
    try:
        # Prepare prompt for OpenAI
        prompt = f"""Generate a catchy and engaging YouTube Shorts title about "{topic}" 
        that would perform well and get high engagement.
        
        Music track: {music_track}
        Trending topics: {', '.join(trending_topics[:3])}
        """
        
        if image_content:
            prompt += f"\nVisual content: {', '.join(image_content[:3])}"
            
        prompt += f"\n\nThe title should be catchy, engaging, and no more than {max_length} characters including spaces."
        
        # Call OpenAI API
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are an expert YouTube content creator who specializes in creating viral Shorts titles."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        
        if response.status_code == 200:
            title = response.json()["choices"][0]["message"]["content"].strip()
            # Ensure the title is within the max length
            if len(title) > max_length:
                title = title[:max_length-3] + "..."
            return title
        else:
            logger.error(f"OpenAI API error: {response.text}")
            return random.choice(MOCK_RESPONSES["titles"])
            
    except Exception as e:
        logger.error(f"Error generating title with OpenAI: {e}")
        return random.choice(MOCK_RESPONSES["titles"])

def generate_description(
    topic: str,
    trending_hashtags: List[str],
    music_track: str,
    image_content: Optional[List[str]] = None,
    max_length: int = 300
) -> str:
    """
    Generate an engaging description for a YouTube Short video.
    
    Args:
        topic: The main topic of the video
        trending_hashtags: List of currently trending hashtags
        music_track: The name of the music track used
        image_content: Optional list of image content descriptions
        max_length: Maximum length of the description
        
    Returns:
        An engaging description for the video
    """
    if DEV_MODE or not USE_OPENAI:
        # Use mock data in development mode
        return random.choice(MOCK_RESPONSES["descriptions"])
    
    try:
        # Prepare prompt for OpenAI
        prompt = f"""Generate an engaging YouTube Shorts description about "{topic}".
        
        Music track: {music_track}
        Trending hashtags: {', '.join(trending_hashtags[:5])}
        """
        
        if image_content:
            prompt += f"\nVisual content: {', '.join(image_content[:3])}"
            
        prompt += f"""
        
        The description should:
        1. Be engaging and encourage viewers to like, comment, and subscribe
        2. Include a call to action
        3. Be no more than {max_length} characters including spaces
        4. NOT include hashtags as I will add those separately
        """
        
        # Call OpenAI API
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are an expert YouTube content creator who specializes in creating engaging Shorts descriptions."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 150
            }
        )
        
        if response.status_code == 200:
            description = response.json()["choices"][0]["message"]["content"].strip()
            # Ensure the description is within the max length
            if len(description) > max_length:
                description = description[:max_length-3] + "..."
            return description
        else:
            logger.error(f"OpenAI API error: {response.text}")
            return random.choice(MOCK_RESPONSES["descriptions"])
            
    except Exception as e:
        logger.error(f"Error generating description with OpenAI: {e}")
        return random.choice(MOCK_RESPONSES["descriptions"])

def generate_hashtags(
    topic: str,
    trending_hashtags: List[str],
    music_genre: str,
    count: int = 8
) -> List[str]:
    """
    Generate relevant hashtags for a YouTube Short video.
    
    Args:
        topic: The main topic of the video
        trending_hashtags: List of currently trending hashtags
        music_genre: The genre of the music used
        count: Number of hashtags to generate
        
    Returns:
        A list of relevant hashtags for the video
    """
    if DEV_MODE or not USE_OPENAI:
        # Use mock data in development mode
        return random.choice(MOCK_RESPONSES["hashtags"])
    
    try:
        # Prepare prompt for OpenAI
        prompt = f"""Generate {count} engaging and relevant hashtags for a YouTube Shorts video about "{topic}".
        
        Music genre: {music_genre}
        Currently trending hashtags: {', '.join(trending_hashtags[:5])}
        
        Please return only the hashtags, one per line, without any explanations.
        Each hashtag should start with #, have no spaces, and use camelCase for multiple words.
        Always include #shorts as one of the hashtags.
        """
        
        # Call OpenAI API
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are an expert in social media hashtag optimization."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        
        if response.status_code == 200:
            hashtags_text = response.json()["choices"][0]["message"]["content"].strip()
            # Extract hashtags from the response
            hashtags = [tag.strip() for tag in hashtags_text.split('\n') if tag.strip().startswith('#')]
            
            # Ensure we have the required number of hashtags
            if len(hashtags) < count:
                # Add some trending hashtags if we don't have enough
                hashtags.extend([tag for tag in trending_hashtags if tag not in hashtags])
                # Ensure #shorts is included
                if "#shorts" not in hashtags:
                    hashtags.append("#shorts")
                    
            # Limit to the specified count
            return hashtags[:count]
        else:
            logger.error(f"OpenAI API error: {response.text}")
            return random.choice(MOCK_RESPONSES["hashtags"])
            
    except Exception as e:
        logger.error(f"Error generating hashtags with OpenAI: {e}")
        return random.choice(MOCK_RESPONSES["hashtags"])

def generate_optimized_metadata(
    topic: str,
    music_track: str,
    trending_data: Dict[str, Any],
    image_content: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate complete optimized metadata for a YouTube Short.
    
    Args:
        topic: Main topic of the video
        music_track: Music track used
        trending_data: Dictionary with trending topics and hashtags
        image_content: Optional list of descriptions of image content
        
    Returns:
        Dictionary with optimized metadata
    """
    trending_topics = trending_data.get("trending_topics", ["trending", "viral", "challenge"])
    trending_hashtags = trending_data.get("trending_hashtags", ["#shorts", "#viral", "#trending"])
    
    # Extract music genre from track name
    music_genre = "music"
    genres = ["pop", "rock", "hip hop", "rap", "electronic", "dance", "lo-fi", "jazz", "acoustic"]
    for genre in genres:
        if genre in music_track.lower():
            music_genre = genre
            break
    
    # Generate metadata
    title = generate_title(
        topic=topic,
        trending_topics=trending_topics,
        music_track=music_track,
        image_content=image_content,
        max_length=trending_data.get("optimal_title_length", 70)
    )
    
    hashtags = generate_hashtags(
        topic=topic,
        trending_hashtags=trending_hashtags,
        music_genre=music_genre
    )
    
    description = generate_description(
        topic=topic,
        trending_hashtags=hashtags,
        music_track=music_track,
        image_content=image_content,
        max_length=trending_data.get("optimal_description_length", 300)
    )
    
    # Create a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # Prepare metadata object
    metadata = {
        "title": title,
        "description": description,
        "hashtags": hashtags,
        "tags": [tag.replace("#", "") for tag in hashtags],  # Tags without # symbol
        "category_id": "22",  # Category ID for People & Blogs
        "generated_on": timestamp,
        "music_track": music_track,
        "topic": topic
    }
    
    return metadata

def generate_video_metadata(video_topic: str, music_metadata: dict, target_platform: str = "youtube") -> dict:
    """
    Generate optimized metadata for a video based on topic and music.
    
    Args:
        video_topic: The main topic/theme of the video
        music_metadata: Metadata of the music used in the video
        target_platform: Target platform for optimization ('youtube', 'tiktok', 'instagram', 'facebook')
        
    Returns:
        dict: Generated metadata including title, description, hashtags and more
    """
    # Normalize platform name
    target_platform = target_platform.lower()
    
    # Extract relevant music info
    music_title = music_metadata.get("title", "")
    music_artist = music_metadata.get("artist", "")
    music_genre = music_metadata.get("genre", "")
    music_mood = music_metadata.get("mood", "")
    music_bpm = music_metadata.get("bpm", 120)
    music_tags = music_metadata.get("tags", [])
    
    # Prepare base metadata
    metadata = {
        "title": "",
        "description": "",
        "hashtags": [],
        "keywords": [],
        "call_to_action": "",
        "caption": ""
    }
    
    # Generate appropriate title based on platform
    if target_platform == "youtube":
        # YouTube titles should be descriptive but concise, with attention-grabbing elements
        title_templates = [
            f"{video_topic.title()} - {music_mood.title()} {music_genre} Music",
            f"{video_topic.title()} | Perfect {music_mood.title()} Vibes",
            f"{music_mood.title()} {music_genre} for {video_topic.title()}",
            f"Relaxing {music_genre} Music for {video_topic.title()}",
            f"Best {music_genre} Mix for {video_topic.title()}"
        ]
        metadata["title"] = _select_best_variation(title_templates)
        
        # Detailed description for YouTube
        description_parts = [
            f"Experience the perfect {music_mood} {music_genre} music for {video_topic.lower()}.",
            f"This track '{music_title}' by {music_artist} creates an ideal atmosphere for {video_topic.lower()}.",
            "",
            "🎵 Music Info:",
            f"Title: {music_title}",
            f"Artist: {music_artist}",
            f"Genre: {music_genre}",
            f"Mood: {music_mood}",
            "",
            "📱 Follow me on social media:",
            "Instagram: @yourusername",
            "TikTok: @yourusername",
            "Twitter: @yourusername",
            "",
            "🔔 Subscribe for more content like this!",
            "",
            "#shorts #YouTube"
        ]
        metadata["description"] = "\n".join(description_parts)
        
        # YouTube hashtags (max 15)
        base_hashtags = ["shorts", "youtubeshorts", music_genre.lower().replace(" ", ""), 
                          music_mood.lower().replace(" ", ""), video_topic.lower().replace(" ", "")]
        extra_hashtags = [tag.replace(" ", "") for tag in music_tags[:5]]
        metadata["hashtags"] = _select_unique_hashtags(base_hashtags + extra_hashtags, limit=15)
        
    elif target_platform == "tiktok":
        # TikTok titles should be short and trendy
        title_templates = [
            f"{video_topic.title()} vibes 🎵 #foryou",
            f"{music_mood.title()} {music_genre} 🎧 #fyp",
            f"When {video_topic.lower()} meets {music_genre.lower()} 🔥",
            f"{video_topic.title()} check ✓ #trending",
            f"{music_mood.title()} moments 🎶"
        ]
        metadata["title"] = _select_best_variation(title_templates)
        
        # Short caption for TikTok
        caption_templates = [
            f"{video_topic.title()} vibes with {music_artist}'s '{music_title}' 🎵 What do you think?",
            f"POV: {video_topic.title()} with the perfect soundtrack 🎧",
            f"This {music_genre} just hits different for {video_topic.lower()} 🔥",
            f"Rate this {video_topic.lower()} vibe 1-10 ⬇️",
            f"Tell me this isn't perfect for {video_topic.lower()} 👀"
        ]
        metadata["caption"] = _select_best_variation(caption_templates)
        
        # TikTok hashtags (shorter but more numerous)
        base_hashtags = ["fyp", "foryou", "foryoupage", music_genre.lower().replace(" ", ""), 
                          music_mood.lower().replace(" ", ""), video_topic.lower().replace(" ", "")]
        extra_hashtags = [tag.replace(" ", "") for tag in music_tags[:10]]
        trending_hashtags = ["viral", "trending", "tiktok", "music", "soundeffect"]
        metadata["hashtags"] = _select_unique_hashtags(base_hashtags + extra_hashtags + trending_hashtags, limit=20)
        
    elif target_platform == "instagram":
        # Instagram titles are typically more visually descriptive
        title_templates = [
            f"✨ {video_topic.title()} Moments ✨",
            f"🎵 {music_mood.title()} {music_genre} Vibes 🎵",
            f"💫 {video_topic.title()} | {music_mood.title()} {music_genre} 💫",
            f"🎧 Sound On: {music_mood.title()} {video_topic.title()} 🎧",
            f"✨ {video_topic.title()} x {music_genre} ✨"
        ]
        metadata["title"] = _select_best_variation(title_templates)
        
        # Instagram caption - longer with emojis
        caption_templates = [
            f"✨ {video_topic.title()} with the perfect soundtrack by {music_artist}\n\nMusic: '{music_title}'\nMood: {music_mood}\n\nWhat's your favorite {music_genre.lower()} track? Tell me in the comments! 👇",
            f"Bringing {music_mood.lower()} vibes to your day with this {music_genre.lower()} masterpiece 🎵\n\nTrack: {music_title}\nArtist: {music_artist}\n\nDo you enjoy {video_topic.lower()}? Let me know! ❤️",
            f"When {video_topic.lower()} meets {music_genre.lower()} 🔥\n\nFeaturing: {music_artist} - {music_title}\n\nDouble tap if this made your day better! ✨",
            f"The perfect {music_mood.lower()} soundtrack for {video_topic.lower()} moments 🎧\n\nMusic: {music_title} by {music_artist}\n\nSave this for later! 🔖",
            f"✨ {video_topic.title()} Vibes ✨\n\nSoundtrack: {music_title}\nArtist: {music_artist}\nMood: {music_mood}\n\nFollow for more content like this! 👉"
        ]
        metadata["caption"] = _select_best_variation(caption_templates)
        
        # Instagram hashtags (balanced)
        base_hashtags = ["instagramreels", "reels", music_genre.lower().replace(" ", ""), 
                          music_mood.lower().replace(" ", ""), video_topic.lower().replace(" ", "")]
        extra_hashtags = [tag.replace(" ", "") for tag in music_tags[:7]]
        trending_hashtags = ["instadaily", "instagood", "music", "vibes", "mood"]
        metadata["hashtags"] = _select_unique_hashtags(base_hashtags + extra_hashtags + trending_hashtags, limit=25)
        
    else:  # Facebook or other platforms
        # Generic title suitable for other platforms
        title_templates = [
            f"{video_topic.title()} - {music_mood.title()} {music_genre}",
            f"{video_topic.title()} with {music_mood.title()} Music",
            f"{music_mood.title()} {music_genre} for {video_topic.title()}",
            f"Enjoy {video_topic.title()} with {music_genre}",
            f"Best {music_genre} for {video_topic.title()}"
        ]
        metadata["title"] = _select_best_variation(title_templates)
        
        # Generic description
        description_parts = [
            f"Enjoy this {music_mood.lower()} {music_genre.lower()} track perfect for {video_topic.lower()}.",
            f"Music: '{music_title}' by {music_artist}",
            "",
            "Let me know what you think in the comments!"
        ]
        metadata["description"] = "\n".join(description_parts)
        
        # Generic hashtags
        base_hashtags = [music_genre.lower().replace(" ", ""), 
                          music_mood.lower().replace(" ", ""), 
                          video_topic.lower().replace(" ", "")]
        extra_hashtags = [tag.replace(" ", "") for tag in music_tags[:3]]
        metadata["hashtags"] = _select_unique_hashtags(base_hashtags + extra_hashtags, limit=10)
    
    # Generate common keywords
    metadata["keywords"] = _generate_keywords(video_topic, music_metadata)
    
    # Generate call-to-action based on platform
    metadata["call_to_action"] = _generate_call_to_action(target_platform)
    
    return metadata

def detect_trending_video_format(target_platform: str = "youtube") -> dict:
    """
    Detect currently trending video formats for a specific platform.
    
    Args:
        target_platform: Target platform to analyze ('youtube', 'tiktok', 'instagram', 'facebook')
        
    Returns:
        dict: Trending format recommendations
    """
    # Normalize platform name
    target_platform = target_platform.lower()
    
    # Platform-specific trend detection
    if target_platform == "youtube":
        return {
            "aspect_ratio": "9:16",  # Shorts are vertical
            "optimal_duration": 60,   # 60 seconds ideal for Shorts
            "trending_formats": [
                "reaction-style videos with on-screen text",
                "before/after transformations",
                "fact-based educational content",
                "POV storytelling",
                "quick tutorials or life hacks"
            ],
            "trending_transitions": [
                "quick cuts",
                "zoom transitions",
                "text animations",
                "beat-synced cuts",
                "swipe transitions"
            ],
            "trending_effects": [
                "text overlays",
                "motion graphics",
                "split screens",
                "zoom effects",
                "time lapses"
            ],
            "content_trends": [
                "day-in-the-life content",
                "behind-the-scenes footage",
                "unexpected plot twists",
                "surprising facts or statistics",
                "relatable scenarios"
            ],
            "music_trends": [
                "viral soundtracks from TikTok",
                "electronic beats",
                "remixes of popular songs",
                "nostalgic tracks from 80s/90s",
                "lo-fi beats"
            ],
            "recommended_hooks": [
                "Ask a controversial question",
                "Start with 'POV:'",
                "State an unexpected fact",
                "Use 'Watch until the end'",
                "Start with a countdown"
            ]
        }
        
    elif target_platform == "tiktok":
        return {
            "aspect_ratio": "9:16",  # Vertical format
            "optimal_duration": 30,   # 15-30 seconds performs best
            "trending_formats": [
                "dance challenges",
                "transformation videos",
                "point-of-view (POV) storytelling",
                "text-based humor",
                "lip-syncing to trending sounds"
            ],
            "trending_transitions": [
                "jump cuts on beat",
                "hand transitions",
                "zoom transitions",
                "color filters",
                "creative transitions using objects"
            ],
            "trending_effects": [
                "green screen",
                "time warp scan",
                "slow motion",
                "duet/stitch features",
                "text-to-speech narration"
            ],
            "content_trends": [
                "day-in-the-life videos",
                "outfit transitions",
                "react videos",
                "storytimes",
                "content that speaks to niche communities"
            ],
            "music_trends": [
                "trending TikTok sounds",
                "sped-up remixes",
                "slowed+reverb versions",
                "nostalgic tracks",
                "trending mashups"
            ],
            "recommended_hooks": [
                "Start with 'Things that just make sense...'",
                "Use 'POV:' format",
                "Ask a question viewers will want answered",
                "Tease transformation with 'Wait for it'",
                "Start with 'Tell me you're X without telling me you're X'"
            ]
        }
        
    elif target_platform == "instagram":
        return {
            "aspect_ratio": "9:16",  # Reels are vertical
            "optimal_duration": 30,   # 15-30 seconds for Reels
            "trending_formats": [
                "visually aesthetic content",
                "behind-the-scenes footage",
                "short tutorials",
                "transition videos",
                "comedy skits"
            ],
            "trending_transitions": [
                "finger snap transitions",
                "outfit changes",
                "smooth pan transitions",
                "creative wipes",
                "beat-synced cuts"
            ],
            "trending_effects": [
                "filters with aesthetic appeal",
                "boomerang effects",
                "slow motion",
                "text animations",
                "AR filters"
            ],
            "content_trends": [
                "lifestyle content",
                "fashion trends",
                "quick recipes",
                "travel highlights",
                "product reviews"
            ],
            "music_trends": [
                "popular chart music",
                "indie tracks",
                "remixes of classic songs",
                "original sounds",
                "instrumental background music"
            ],
            "recommended_hooks": [
                "Start with a visually stunning shot",
                "Ask 'Did you know?' questions",
                "Begin with 'Trying this trend...'",
                "Use 'POV:' format",
                "Begin with a compelling statistic"
            ]
        }
        
    else:  # Facebook or other platforms
        return {
            "aspect_ratio": "16:9",  # Horizontal still performs well
            "optimal_duration": 90,   # Slightly longer content
            "trending_formats": [
                "relatable slice-of-life content",
                "community-focused stories",
                "nostalgic content",
                "longer-form explanations",
                "inspirational stories"
            ],
            "trending_transitions": [
                "simple cuts",
                "fade transitions",
                "split screens",
                "smooth pans",
                "text overlays between scenes"
            ],
            "trending_effects": [
                "subtitles and captions",
                "emotional music beds",
                "reaction elements",
                "picture-in-picture",
                "comparison slideshows"
            ],
            "content_trends": [
                "family-oriented content",
                "nostalgic throwbacks",
                "community events",
                "DIY and home improvement",
                "heartwarming stories"
            ],
            "music_trends": [
                "uplifting background tracks",
                "emotional instrumentals",
                "nostalgic classics",
                "trending pop music",
                "inspirational soundtracks"
            ],
            "recommended_hooks": [
                "Start with 'Remember when...'",
                "Ask a relatable question",
                "Begin with 'I never thought...'",
                "Use 'Today I learned...'",
                "Start with 'Have you ever wondered...'"
            ]
        }

def _select_best_variation(templates: list) -> str:
    """Select the best variation from a list of templates."""
    # In a real implementation, this could use more sophisticated selection
    # such as A/B testing results or ML prediction
    import random
    return random.choice(templates)

def _select_unique_hashtags(hashtags: list, limit: int = 15) -> list:
    """Select unique hashtags up to a limit."""
    # Remove duplicates while preserving order
    seen = set()
    unique_hashtags = []
    for tag in hashtags:
        if tag.lower() not in seen and tag.strip():
            seen.add(tag.lower())
            # Remove special characters and spaces
            cleaned_tag = ''.join(c for c in tag if c.isalnum() or c == '_')
            if cleaned_tag:
                unique_hashtags.append(cleaned_tag)
    
    # Return up to the limit
    return unique_hashtags[:limit]

def _generate_keywords(video_topic: str, music_metadata: dict) -> list:
    """Generate relevant keywords based on video topic and music."""
    # Base keywords from topic
    keywords = [video_topic.lower()]
    
    # Add variations with spaces
    keywords.extend(video_topic.lower().split())
    
    # Add music-based keywords
    if "genre" in music_metadata:
        keywords.append(music_metadata["genre"].lower())
    if "mood" in music_metadata:
        keywords.append(music_metadata["mood"].lower())
    if "artist" in music_metadata:
        keywords.append(music_metadata["artist"].lower())
    if "tags" in music_metadata:
        keywords.extend(music_metadata["tags"])
    
    # Combine some terms
    if "genre" in music_metadata and "mood" in music_metadata:
        keywords.append(f"{music_metadata['mood'].lower()} {music_metadata['genre'].lower()}")
    if "mood" in music_metadata:
        keywords.append(f"{music_metadata['mood'].lower()} music")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword.lower() not in seen and keyword.strip():
            seen.add(keyword.lower())
            unique_keywords.append(keyword.lower())
    
    return unique_keywords

def _generate_call_to_action(platform: str) -> str:
    """Generate platform-specific call to action."""
    if platform == "youtube":
        cta_options = [
            "Like this video and subscribe for more!",
            "Don't forget to subscribe and hit the notification bell!",
            "Subscribe for more videos like this!",
            "Share this with someone who would enjoy it!",
            "Leave a comment with your thoughts!"
        ]
    elif platform == "tiktok":
        cta_options = [
            "Follow for more content like this! ✨",
            "Drop a ❤️ if you enjoyed this!",
            "Save this for later! 📌",
            "Tag someone who needs to see this! 👀",
            "What do you think? Let me know in the comments! 👇"
        ]
    elif platform == "instagram":
        cta_options = [
            "Double tap if you enjoyed this! ❤️",
            "Save this post for later! 🔖",
            "Follow for more content! ✨",
            "Tag a friend who would love this! 👫",
            "Share your thoughts in the comments! 💭"
        ]
    else:  # Facebook or other
        cta_options = [
            "Like and share if you enjoyed this!",
            "Leave a comment with your thoughts!",
            "Follow for more content like this!",
            "Tag someone who would appreciate this!",
            "Save this post for later!"
        ]
    
    import random
    return random.choice(cta_options) 