#!/usr/bin/env python
"""
Test script for YouTube API v3 integration.
"""
import os
import logging
import argparse
import requests
import json
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API configuration
API_URL = os.environ.get('API_URL', 'http://localhost:8000')

def test_search_videos(query: str = 'python tutorial', max_results: int = 5) -> None:
    """Test the video search endpoint."""
    logger.info(f"Testing search for '{query}' (max results: {max_results})")
    
    url = f"{API_URL}/youtube/search"
    payload = {
        "query": query,
        "max_results": max_results
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        videos = response.json()
        logger.info(f"Found {len(videos)} videos:")
        for i, video in enumerate(videos):
            logger.info(f"{i+1}. {video['title']} (ID: {video['video_id']})")
        return videos
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return None

def test_video_details(video_id: str) -> None:
    """Test the video details endpoint."""
    logger.info(f"Testing video details for ID: {video_id}")
    
    url = f"{API_URL}/youtube/videos/{video_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        video = response.json()
        logger.info(f"Video details:")
        logger.info(f"- Title: {video['title']}")
        logger.info(f"- Views: {video['view_count']}")
        logger.info(f"- Likes: {video['like_count']}")
        logger.info(f"- Tags: {', '.join(video['tags']) if video['tags'] else 'None'}")
        return video
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return None

def test_trending_videos() -> None:
    """Test the trending videos endpoint."""
    logger.info("Testing trending videos")
    
    url = f"{API_URL}/youtube/trending"
    response = requests.get(url)
    
    if response.status_code == 200:
        videos = response.json()
        logger.info(f"Found {len(videos)} trending videos:")
        for i, video in enumerate(videos):
            logger.info(f"{i+1}. {video['title']} (ID: {video['video_id']})")
        return videos
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return None

def main() -> None:
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test YouTube API v3 integration')
    parser.add_argument('--test', choices=['search', 'video', 'trending', 'all'], default='all',
                      help='Which test to run (default: all)')
    parser.add_argument('--query', default='python tutorial',
                      help='Search query for video search test')
    parser.add_argument('--video-id', default=None,
                      help='Video ID for video details test')
    parser.add_argument('--max-results', type=int, default=5,
                      help='Maximum number of results to return')
    
    args = parser.parse_args()
    
    logger.info(f"Testing YouTube API integration at {API_URL}")
    
    # Run the requested tests
    if args.test in ['search', 'all']:
        videos = test_search_videos(args.query, args.max_results)
        print()
        
        # Use first video ID for video details test if not specified
        if videos and args.video_id is None and args.test == 'all':
            args.video_id = videos[0]['video_id']
    
    if args.test in ['video', 'all']:
        if args.video_id:
            test_video_details(args.video_id)
            print()
        else:
            logger.error("No video ID provided for video details test")
    
    if args.test in ['trending', 'all']:
        test_trending_videos()
        print()
    
    logger.info("Testing complete")

if __name__ == "__main__":
    main() 