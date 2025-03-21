#!/usr/bin/env python3
"""
Music Recommendation Demo.

This script showcases the intelligent music recommendation functionality
of the YouTube Shorts Machine by analyzing sample videos and providing
appropriate music recommendations.
"""
import os
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from src.app.services.music.recommendations import get_music_recommendation_service
from src.app.core.settings import DEBUG_MODE, DEV_MODE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/music_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("music_recommendation_demo")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

def demo_analyze_video(video_path):
    """
    Demonstrate video analysis by analyzing a sample video and printing its features.
    
    Args:
        video_path: Path to the video file
    """
    logger.info(f"Analyzing video: {video_path}")
    
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return
    
    # Get recommendation service
    recommendation_service = get_music_recommendation_service()
    
    # Analyze video
    try:
        video_features = recommendation_service._analyze_video(video_path)
        
        logger.info("Video Analysis Results:")
        logger.info(f"  Pace: {video_features['pace']}")
        logger.info(f"  Energy: {video_features['energy']:.2f}")
        logger.info(f"  Atmosphere: {video_features['atmosphere']}")
        logger.info(f"  Has Speech: {video_features['has_speech']}")
        logger.info(f"  Movement Level: {video_features['movement_level']:.2f}")
        logger.info(f"  Dominant Colors: {', '.join(video_features['dominant_colors'])}")
    except Exception as e:
        logger.error(f"Error analyzing video: {e}")

def demo_recommendations_for_video(video_path, count=5, genre=None, mood=None):
    """
    Demonstrate music recommendations for a specific video.
    
    Args:
        video_path: Path to the video file
        count: Number of recommendations to return
        genre: Optional preferred genre
        mood: Optional preferred mood
    """
    logger.info(f"Getting music recommendations for video: {video_path}")
    
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return
    
    # Get recommendation service
    recommendation_service = get_music_recommendation_service()
    
    # Get recommendations
    try:
        recommendations = recommendation_service.recommend_for_video(
            video_path=video_path,
            count=count,
            preferred_genres=[genre] if genre else None,
            preferred_moods=[mood] if mood else None
        )
        
        logger.info(f"Found {len(recommendations)} recommendations:")
        for i, track in enumerate(recommendations, 1):
            score = track.get("relevance_score", 0) * 100
            logger.info(f"  {i}. {track['title']} by {track['artist']}")
            logger.info(f"     Genre: {track.get('genre', 'Unknown')}")
            logger.info(f"     BPM: {track.get('bpm', 0)} | Key: {track.get('key', 'Unknown')}")
            logger.info(f"     Energy: {track.get('energy', 0):.2f} | Mood: {track.get('mood', 'Unknown')}")
            logger.info(f"     Match Score: {score:.1f}%")
            logger.info("")
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")

def demo_similar_tracks(track_name, count=5):
    """
    Demonstrate similar track recommendations.
    
    Args:
        track_name: Name of the reference track
        count: Number of recommendations to return
    """
    logger.info(f"Finding tracks similar to: {track_name}")
    
    # Get recommendation service
    recommendation_service = get_music_recommendation_service()
    
    # Get recommendations
    try:
        similar_tracks = recommendation_service.recommend_similar(
            track_name=track_name,
            count=count
        )
        
        logger.info(f"Found {len(similar_tracks)} similar tracks:")
        for i, track in enumerate(similar_tracks, 1):
            score = track.get("similarity_score", 0) * 100
            logger.info(f"  {i}. {track['title']} by {track['artist']}")
            logger.info(f"     Genre: {track.get('genre', 'Unknown')}")
            logger.info(f"     BPM: {track.get('bpm', 0)} | Key: {track.get('key', 'Unknown')}")
            logger.info(f"     Energy: {track.get('energy', 0):.2f} | Mood: {track.get('mood', 'Unknown')}")
            logger.info(f"     Similarity Score: {score:.1f}%")
            logger.info("")
    except Exception as e:
        logger.error(f"Error getting similar tracks: {e}")

def demo_trending_tracks(count=5):
    """
    Demonstrate trending track recommendations.
    
    Args:
        count: Number of recommendations to return
    """
    logger.info("Getting trending music tracks")
    
    # Get recommendation service
    recommendation_service = get_music_recommendation_service()
    
    # Get recommendations
    try:
        trending_tracks = recommendation_service.recommend_trending(count=count)
        
        logger.info(f"Found {len(trending_tracks)} trending tracks:")
        for i, track in enumerate(trending_tracks, 1):
            position = track.get("trending_position", i)
            logger.info(f"  #{position}. {track['title']} by {track['artist']}")
            logger.info(f"     Genre: {track.get('genre', 'Unknown')}")
            logger.info(f"     BPM: {track.get('bpm', 0)} | Key: {track.get('key', 'Unknown')}")
            logger.info(f"     Energy: {track.get('energy', 0):.2f} | Mood: {track.get('mood', 'Unknown')}")
            logger.info("")
    except Exception as e:
        logger.error(f"Error getting trending tracks: {e}")

def main():
    """Main entry point for the demo."""
    parser = argparse.ArgumentParser(description="Music Recommendation Demo")
    parser.add_argument("--mode", choices=["analyze", "recommend", "similar", "trending"], 
                        default="recommend", help="Demo mode")
    parser.add_argument("--video", help="Path to the video file for analysis or recommendations")
    parser.add_argument("--track", help="Reference track name for similar track recommendations")
    parser.add_argument("--count", type=int, default=5, help="Number of recommendations to return")
    parser.add_argument("--genre", help="Preferred genre for recommendations")
    parser.add_argument("--mood", help="Preferred mood for recommendations")
    
    args = parser.parse_args()
    
    logger.info("YouTube Shorts Machine - Music Recommendation Demo")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Development Mode: {DEV_MODE}")
    logger.info(f"Debug Mode: {DEBUG_MODE}")
    logger.info("")
    
    # Run appropriate demo based on mode
    if args.mode == "analyze":
        if not args.video:
            logger.error("Video path is required for analyze mode")
            return
        demo_analyze_video(args.video)
    
    elif args.mode == "recommend":
        if not args.video:
            logger.error("Video path is required for recommend mode")
            return
        demo_recommendations_for_video(args.video, args.count, args.genre, args.mood)
    
    elif args.mode == "similar":
        if not args.track:
            logger.error("Reference track name is required for similar mode")
            return
        demo_similar_tracks(args.track, args.count)
    
    elif args.mode == "trending":
        demo_trending_tracks(args.count)

if __name__ == "__main__":
    main() 