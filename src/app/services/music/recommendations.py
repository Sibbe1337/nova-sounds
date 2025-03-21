"""
Advanced music recommendation system for the YouTube Shorts Machine.
"""
import os
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import random
from collections import defaultdict
from datetime import datetime

from src.app.services.gcs.music_metadata import (
    get_track_metadata,
    search_tracks_by_metadata,
    get_track_waveform,
    compute_track_similarity,
    batch_analyze_tracks
)
from src.app.services.gcs.storage import list_music_tracks, get_track_details
from src.app.core.settings import DEV_MODE
from src.app.core.database import get_music_preferences, save_music_preferences

# Configure logging
logger = logging.getLogger(__name__)

class MusicRecommendationService:
    """
    Service for providing intelligent music recommendations based on
    video content, metadata, and user preferences.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(MusicRecommendationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the music recommendation service."""
        if self._initialized:
            return
            
        self._initialized = True
        self.track_cache = {}
        self.video_analysis_cache = {}
        
        # Track recommendation history to improve future recommendations
        self.recommendation_history = defaultdict(list)
        
        # User preferences cache to improve personalized recommendations
        self.user_preferences = {}
        
        # Track usage stats for popularity calculation
        self.track_usage_stats = defaultdict(int)
        
        # Used algorithms for debug and tracking
        self.last_used_algorithm = None
        
        # Load user preferences from database
        self._load_user_preferences()
        
        # Preload a cache of track metadata to improve performance
        self._preload_track_metadata()
        
        logger.info("Music recommendation service initialized")
    
    def _load_user_preferences(self):
        """
        Load user preferences from the database.
        """
        try:
            # Get all user IDs with preferences (not directly supported in our simple DB)
            # In a real implementation, this would be more efficient
            # For now, we'll just work with what we have in memory
            logger.info("Loading user preferences from database")
            
            # Check if we're in debug mode
            debug_mode = os.environ.get("DEBUG_MUSIC_PREFS", "0") == "1" or DEV_MODE
            if debug_mode:
                logger.info("Music preferences debug mode enabled")
            
            # This is a placeholder - in our simple implementation, 
            # we don't have a way to list all users yet
            # In a real implementation, we would fetch all user preferences
            
            # For testing, let's try to load some known users
            test_users = ["user1", "user2", "user3"]
            
            # In debug mode, also check for a test user based on environment
            if debug_mode:
                test_username = os.environ.get("TEST_USER", "")
                if test_username and test_username not in test_users:
                    test_users.append(test_username)
                logger.info(f"Will try to load preferences for users: {test_users}")
            
            for user_id in test_users:
                if debug_mode:
                    logger.info(f"Attempting to load preferences for user {user_id}")
                
                prefs = get_music_preferences(user_id)
                if prefs:
                    self.user_preferences[user_id] = prefs
                    if debug_mode:
                        logger.info(f"Loaded preferences for {user_id}: {len(prefs)} items")
                        # Log some keys to help debug
                        if "liked_tracks" in prefs:
                            logger.info(f"User {user_id} has {len(prefs['liked_tracks'])} liked tracks")
                        if "favorite_genres" in prefs:
                            logger.info(f"User {user_id} favorite genres: {prefs.get('favorite_genres', [])}")
                elif debug_mode:
                    logger.info(f"No preferences found for user {user_id}")
            
            logger.info(f"Loaded preferences for {len(self.user_preferences)} users")
            
            # In debug mode, check if mock data directory exists
            if debug_mode:
                mock_dir = os.path.join(os.getcwd(), "mock-data")
                if not os.path.exists(mock_dir):
                    logger.warning(f"Mock data directory does not exist: {mock_dir}")
                    logger.info("Creating mock-data directory")
                    os.makedirs(mock_dir, exist_ok=True)
                else:
                    logger.info(f"Mock data directory exists: {mock_dir}")
                
                # Check if music preferences file exists
                mock_prefs_file = os.path.join(mock_dir, "music_preferences.json")
                if os.path.exists(mock_prefs_file):
                    logger.info(f"Music preferences file exists: {mock_prefs_file}")
                    # Log file size
                    file_size = os.path.getsize(mock_prefs_file)
                    logger.info(f"Music preferences file size: {file_size} bytes")
                else:
                    logger.warning(f"Music preferences file does not exist: {mock_prefs_file}")
        except Exception as e:
            logger.error(f"Error loading user preferences: {e}")
            # In case of error, print more detailed information in debug mode
            if os.environ.get("DEBUG_MUSIC_PREFS", "0") == "1" or DEV_MODE:
                import traceback
                logger.error(traceback.format_exc())
    
    def _save_user_preference(self, user_id: str):
        """
        Save user preference to the database.
        
        Args:
            user_id: ID of the user
        """
        if user_id in self.user_preferences:
            try:
                debug_mode = os.environ.get("DEBUG_MUSIC_PREFS", "0") == "1" or DEV_MODE
                prefs = self.user_preferences[user_id]
                
                if debug_mode:
                    logger.info(f"Saving preferences for user {user_id} with {len(prefs.keys())} keys")
                    # Log what we're saving
                    for key, value in prefs.items():
                        if isinstance(value, list):
                            logger.info(f"  - {key}: {len(value)} items")
                        else:
                            logger.info(f"  - {key}: {value}")
                
                save_result = save_music_preferences(user_id, prefs)
                
                if debug_mode:
                    logger.info(f"Save result for user {user_id}: {save_result}")
                else:
                    logger.debug(f"Saved preferences for user {user_id}")
            except Exception as e:
                logger.error(f"Error saving preferences for user {user_id}: {e}")
                # In case of error, print more detailed information in debug mode
                if os.environ.get("DEBUG_MUSIC_PREFS", "0") == "1" or DEV_MODE:
                    import traceback
                    logger.error(traceback.format_exc())
    
    def _preload_track_metadata(self, force_refresh: bool = False):
        """
        Preload track metadata to improve performance.
        
        Args:
            force_refresh: Whether to force refresh metadata
        """
        if DEV_MODE and not force_refresh:
            logger.info("Skipping metadata preload in DEV mode")
            return
            
        try:
            logger.info("Preloading track metadata...")
            tracks = list_music_tracks(limit=100)
            batch_analyze_tracks(tracks[:50])  # Just preload the first 50 to be efficient
            logger.info(f"Preloaded metadata for {min(50, len(tracks))} tracks")
        except Exception as e:
            logger.warning(f"Error preloading track metadata: {e}")
    
    def recommend_for_video(
        self, 
        video_path: str, 
        count: int = 5,
        preferred_genres: Optional[List[str]] = None,
        preferred_moods: Optional[List[str]] = None,
        min_bpm: Optional[int] = None,
        max_bpm: Optional[int] = None,
        energy_level: Optional[float] = None,
        include_waveform: bool = False,
        keyword: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recommend music tracks for a specific video based on content analysis.
        
        Args:
            video_path: Path to the video file
            count: Number of recommendations to return
            preferred_genres: Optional list of preferred genres
            preferred_moods: Optional list of preferred moods
            min_bpm: Optional minimum BPM
            max_bpm: Optional maximum BPM
            energy_level: Optional target energy level (0-1)
            include_waveform: Whether to include waveform data
            keyword: Optional keyword to filter tracks
            
        Returns:
            List of recommended tracks with metadata
        """
        # Analyze video if not already cached
        video_features = self._analyze_video(video_path)
        
        # Set defaults based on video analysis if not provided
        if min_bpm is None and max_bpm is None:
            # Recommend BPM based on video pace
            if video_features["pace"] == "fast":
                min_bpm = 110
                max_bpm = 160
            elif video_features["pace"] == "medium":
                min_bpm = 90
                max_bpm = 120
            else:  # slow
                min_bpm = 60
                max_bpm = 100
        
        if energy_level is None:
            # Map video energy to music energy
            energy_level = video_features["energy"]
            
            # Allow for range around the energy level
            energy_range = (max(0.0, energy_level - 0.2), min(1.0, energy_level + 0.2))
        else:
            # Allow for range around the specified energy level
            energy_range = (max(0.0, energy_level - 0.15), min(1.0, energy_level + 0.15))
        
        if preferred_moods is None:
            # Suggest moods based on video atmosphere
            if video_features["atmosphere"] == "bright":
                preferred_moods = ["Happy", "Upbeat", "Energetic"]
            elif video_features["atmosphere"] == "dramatic":
                preferred_moods = ["Emotional", "Dramatic", "Powerful"]
            elif video_features["atmosphere"] == "neutral":
                preferred_moods = ["Neutral", "Calm", "Balanced"]
            else:
                preferred_moods = ["Atmospheric", "Ambient", "Mysterious"]
        
        # Search for tracks matching criteria
        matching_tracks = search_tracks_by_metadata(
            genre=None if not preferred_genres else preferred_genres[0],
            mood=None if not preferred_moods else preferred_moods[0],
            min_bpm=min_bpm,
            max_bpm=max_bpm,
            energy_range=energy_range,
            keyword=keyword
        )
        
        # If we don't have enough results, expand search
        if len(matching_tracks) < count:
            # Try with relaxed criteria
            matching_tracks = search_tracks_by_metadata(
                min_bpm=min_bpm - 15 if min_bpm else None,
                max_bpm=max_bpm + 15 if max_bpm else None,
                energy_range=(
                    max(0.0, energy_range[0] - 0.2),
                    min(1.0, energy_range[1] + 0.2)
                ),
                keyword=keyword
            )
            
            # If still not enough, try even more relaxed search
            if len(matching_tracks) < count:
                # Just search by mood or genre
                relaxed_matches = search_tracks_by_metadata(
                    genre=None if not preferred_genres else preferred_genres[0],
                    mood=None if not preferred_moods else preferred_moods[0],
                    keyword=keyword
                )
                
                # Add any new tracks not already in matching_tracks
                existing_track_names = {t.get("track_name") for t in matching_tracks}
                for track in relaxed_matches:
                    if track.get("track_name") not in existing_track_names:
                        matching_tracks.append(track)
                        existing_track_names.add(track.get("track_name"))
        
        # Sort tracks by relevance to video
        scored_tracks = self._score_tracks_for_video(matching_tracks, video_features)
        
        # Return top recommendations
        recommendations = scored_tracks[:count]
        
        # Add waveform data if requested
        if include_waveform:
            for track in recommendations:
                try:
                    track_name = track.get("track_name")
                    if track_name:
                        track["waveform"] = get_track_waveform(track_name)
                except Exception as e:
                    logger.warning(f"Error getting waveform for {track_name}: {e}")
        
        # Add recommendation to history
        video_id = os.path.basename(video_path)
        self.recommendation_history[video_id] = [
            track["track_name"] for track in recommendations
        ]
        
        return recommendations
    
    def recommend_similar(
        self, 
        track_name: str, 
        count: int = 5,
        include_waveform: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Recommend tracks similar to the provided track.
        
        Args:
            track_name: Name of the reference track
            count: Number of recommendations to return
            include_waveform: Whether to include waveform data
            
        Returns:
            List of similar tracks with metadata
        """
        # Get metadata for the reference track
        reference = get_track_metadata(track_name)
        
        if not reference:
            logger.warning(f"Reference track {track_name} metadata not found")
            # Return random tracks as fallback
            tracks = list_music_tracks(limit=100)
            selected = random.sample(tracks, min(count, len(tracks)))
            return [get_track_metadata(t) for t in selected]
        
        # Extract key features for similarity comparison
        genre = reference.get("genre")
        mood = reference.get("mood")
        bpm = reference.get("bpm", 120)
        energy = reference.get("energy", 0.5)
        
        # Search for similar tracks
        similar_tracks = search_tracks_by_metadata(
            genre=genre,
            mood=mood,
            min_bpm=max(60, bpm - 15),
            max_bpm=min(180, bpm + 15),
            energy_range=(max(0.0, energy - 0.2), min(1.0, energy + 0.2))
        )
        
        # Remove the reference track itself
        similar_tracks = [t for t in similar_tracks if t.get("track_name") != track_name]
        
        # Score tracks by similarity
        scored_tracks = self._score_tracks_by_similarity(similar_tracks, reference)
        
        # If we don't have enough tracks, expand search
        if len(scored_tracks) < count:
            # Get more tracks with expanded criteria
            expanded_tracks = search_tracks_by_metadata(
                genre=genre,
                min_bpm=max(60, bpm - 30),
                max_bpm=min(180, bpm + 30),
                energy_range=(max(0.0, energy - 0.3), min(1.0, energy + 0.3))
            )
            
            # Remove duplicates and the reference track
            expanded_tracks = [
                t for t in expanded_tracks 
                if t.get("track_name") != track_name and 
                t.get("track_name") not in [st.get("track_name") for st in scored_tracks]
            ]
            
            # Score and add to our results
            expanded_scored = self._score_tracks_by_similarity(expanded_tracks, reference)
            scored_tracks.extend(expanded_scored)
        
        # Get top recommendations
        recommendations = scored_tracks[:count]
        
        # Add waveform data if requested
        if include_waveform:
            for track in recommendations:
                try:
                    track_name = track.get("track_name")
                    if track_name:
                        track["waveform"] = get_track_waveform(track_name)
                except Exception as e:
                    logger.warning(f"Error getting waveform for {track_name}: {e}")
        
        return recommendations
    
    def recommend_trending(self, count: int = 5, include_waveform: bool = False) -> List[Dict[str, Any]]:
        """
        Recommend currently trending music tracks.
        
        Args:
            count: Number of recommendations to return
            include_waveform: Whether to include waveform data
            
        Returns:
            List of trending tracks with metadata
        """
        # In a real implementation, this would use actual trending data
        # For now, we'll use mock trending data
        
        if DEV_MODE:
            # Return mock trending tracks in dev mode
            trending = self._get_mock_trending(count)
        else:
            # Get all tracks and sort by some criteria
            # (In a real implementation, this would use actual usage metrics)
            tracks = list_music_tracks(limit=100)
            track_metadata = [get_track_metadata(t) for t in tracks[:20]]
            
            # Sort by "popularity" (mock data)
            # In a real implementation, this would be based on actual usage stats
            for track in track_metadata:
                track["popularity"] = random.random()
            
            trending = sorted(track_metadata, key=lambda x: x.get("popularity", 0), reverse=True)
            trending = trending[:count]
        
        # Add waveform data if requested
        if include_waveform:
            for track in trending:
                try:
                    track_name = track.get("track_name")
                    if track_name:
                        track["waveform"] = get_track_waveform(track_name)
                except Exception as e:
                    logger.warning(f"Error getting waveform for {track_name}: {e}")
        
        return trending
    
    def recommend_by_keyword(
        self, 
        keyword: str, 
        count: int = 5,
        include_waveform: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Recommend tracks based on a keyword search.
        
        Args:
            keyword: Keyword to search for in track metadata
            count: Number of recommendations to return
            include_waveform: Whether to include waveform data
            
        Returns:
            List of matching tracks with metadata
        """
        # Search tracks by keyword
        matching_tracks = search_tracks_by_metadata(keyword=keyword)
        
        if len(matching_tracks) < count and len(keyword) > 3:
            # Try partial matching for longer keywords
            # This could match "ambient" when searching for "ambi"
            all_tracks = list_music_tracks(limit=200)
            all_metadata = [get_track_metadata(t) for t in all_tracks]
            
            for metadata in all_metadata:
                if not metadata:
                    continue
                    
                # Check if track is already in our matches
                if metadata.get("track_name") in [t.get("track_name") for t in matching_tracks]:
                    continue
                
                # Look for partial matches in title, artist, genre, mood
                found = False
                keyword_lower = keyword.lower()
                for field in ["title", "artist", "genre", "mood"]:
                    if field in metadata and isinstance(metadata[field], str):
                        if keyword_lower in metadata[field].lower():
                            found = True
                            break
                
                if found:
                    matching_tracks.append(metadata)
        
        # Add relevance score based on how well it matches the keyword
        scored_tracks = self._score_tracks_by_keyword(matching_tracks, keyword)
        
        # Get top recommendations
        recommendations = scored_tracks[:count]
        
        # Add waveform data if requested
        if include_waveform:
            for track in recommendations:
                try:
                    track_name = track.get("track_name")
                    if track_name:
                        track["waveform"] = get_track_waveform(track_name)
                except Exception as e:
                    logger.warning(f"Error getting waveform for {track_name}: {e}")
        
        return recommendations
    
    def get_track_details(self, track_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a track.
        
        Args:
            track_name: Name of the track
            
        Returns:
            Dict with track details including waveform
        """
        return get_track_details(track_name)
    
    def _analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze video content to extract features for music matching.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict with video features
        """
        video_id = os.path.basename(video_path)
        
        # Check cache
        if video_id in self.video_analysis_cache:
            return self.video_analysis_cache[video_id]
        
        if DEV_MODE:
            # In dev mode, generate mock analysis
            pace_options = ["slow", "medium", "fast"]
            atmosphere_options = ["bright", "neutral", "dramatic", "dark"]
            
            analysis = {
                "pace": random.choice(pace_options),
                "energy": random.uniform(0.3, 0.9),
                "atmosphere": random.choice(atmosphere_options),
                "dominant_colors": ["#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)]) for _ in range(3)],
                "has_speech": random.choice([True, False]),
                "movement_level": random.uniform(0.2, 0.8)
            }
        else:
            # In a real implementation, this would use computer vision to analyze the video
            # For now, return mock analysis
            analysis = {
                "pace": "medium",
                "energy": 0.6,
                "atmosphere": "bright",
                "dominant_colors": ["#3A86FF", "#FF006E", "#FFBE0B"],
                "has_speech": False,
                "movement_level": 0.5
            }
        
        # Cache the analysis
        self.video_analysis_cache[video_id] = analysis
        
        return analysis
    
    def _score_tracks_for_video(
        self, 
        tracks: List[Dict[str, Any]], 
        video_features: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score tracks based on how well they match the video features.
        
        Args:
            tracks: List of track metadata
            video_features: Dict with video features
            
        Returns:
            List of tracks sorted by relevance score
        """
        scored_tracks = []
        
        for track in tracks:
            score = 0.0
            
            # Score based on energy match
            track_energy = track.get("energy", 0.5)
            energy_diff = abs(track_energy - video_features["energy"])
            score += (1.0 - energy_diff) * 5.0  # Energy match is important (0-5 points)
            
            # Score based on mood-atmosphere match
            track_mood = track.get("mood", "Neutral").lower()
            video_atmosphere = video_features["atmosphere"].lower()
            
            mood_atmosphere_map = {
                "bright": ["happy", "upbeat", "energetic", "optimistic"],
                "dramatic": ["emotional", "dramatic", "powerful", "intense"],
                "neutral": ["neutral", "calm", "balanced", "subtle"],
                "dark": ["atmospheric", "ambient", "mysterious", "melancholic"]
            }
            
            if video_atmosphere in mood_atmosphere_map and track_mood in mood_atmosphere_map[video_atmosphere]:
                score += 3.0  # Good mood-atmosphere match (3 points)
            
            # Consider speech in video
            if video_features["has_speech"]:
                # For videos with speech, instrumental tracks are often better
                if track.get("instrumental", False):
                    score += 2.0  # Bonus for instrumental tracks with speech (2 points)
            
            # Add small random factor for variety
            score += random.uniform(0.0, 0.5)
            
            # Add to scored tracks
            track_with_score = track.copy()
            track_with_score["relevance_score"] = score
            scored_tracks.append(track_with_score)
        
        # Sort by score
        return sorted(scored_tracks, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    def _score_tracks_by_similarity(
        self, 
        tracks: List[Dict[str, Any]], 
        reference: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score tracks based on similarity to a reference track.
        
        Args:
            tracks: List of track metadata
            reference: Reference track metadata
            
        Returns:
            List of tracks sorted by similarity score
        """
        scored_tracks = []
        reference_track_name = reference.get("track_name")
        
        for track in tracks:
            track_name = track.get("track_name")
            
            # Use advanced similarity computation from the metadata service
            if reference_track_name and track_name:
                try:
                    similarity = compute_track_similarity(reference_track_name, track_name)
                    score = similarity * 10.0  # Scale to 0-10 range
                except Exception as e:
                    logger.warning(f"Error computing similarity: {e}")
                    # Fallback to basic scoring
                    score = self._compute_basic_similarity_score(track, reference)
            else:
                # Fallback to basic scoring
                score = self._compute_basic_similarity_score(track, reference)
            
            # Add small random factor for variety
            score += random.uniform(0.0, 0.5)
            
            # Add to scored tracks
            track_with_score = track.copy()
            track_with_score["similarity_score"] = score
            scored_tracks.append(track_with_score)
        
        # Sort by score
        return sorted(scored_tracks, key=lambda x: x.get("similarity_score", 0), reverse=True)
    
    def _compute_basic_similarity_score(
        self,
        track: Dict[str, Any],
        reference: Dict[str, Any]
    ) -> float:
        """
        Compute a basic similarity score between two tracks.
        
        Args:
            track: Track metadata
            reference: Reference track metadata
            
        Returns:
            Similarity score (0-10)
        """
        score = 0.0
        
        # Score based on genre match
        if track.get("genre") == reference.get("genre"):
            score += 3.0  # Same genre (3 points)
        
        # Score based on mood match
        if track.get("mood") == reference.get("mood"):
            score += 2.0  # Same mood (2 points)
        
        # Score based on BPM similarity
        track_bpm = track.get("bpm", 120)
        ref_bpm = reference.get("bpm", 120)
        bpm_diff = abs(track_bpm - ref_bpm)
        
        if bpm_diff <= 5:
            score += 3.0  # Very close BPM (3 points)
        elif bpm_diff <= 15:
            score += 2.0  # Similar BPM (2 points)
        elif bpm_diff <= 30:
            score += 1.0  # Somewhat similar BPM (1 point)
        
        # Score based on energy similarity
        track_energy = track.get("energy", 0.5)
        ref_energy = reference.get("energy", 0.5)
        energy_diff = abs(track_energy - ref_energy)
        
        if energy_diff <= 0.1:
            score += 3.0  # Very similar energy (3 points)
        elif energy_diff <= 0.2:
            score += 2.0  # Similar energy (2 points)
        elif energy_diff <= 0.3:
            score += 1.0  # Somewhat similar energy (1 point)
        
        return score
    
    def _score_tracks_by_keyword(
        self,
        tracks: List[Dict[str, Any]],
        keyword: str
    ) -> List[Dict[str, Any]]:
        """
        Score tracks based on how well they match a keyword.
        
        Args:
            tracks: List of track metadata
            keyword: Keyword to match
            
        Returns:
            List of tracks sorted by keyword relevance
        """
        scored_tracks = []
        keyword_lower = keyword.lower()
        
        for track in tracks:
            score = 0.0
            
            # Check for exact matches in various fields
            for field, points in [
                ("title", 5.0),    # Title match is most important
                ("artist", 4.0),   # Artist match is next
                ("genre", 3.0),    # Genre match
                ("mood", 2.0)      # Mood match
            ]:
                if field in track and isinstance(track[field], str):
                    field_value = track[field].lower()
                    
                    # Exact match (whole word)
                    if keyword_lower == field_value:
                        score += points * 1.5  # Bonus for exact match
                    
                    # Word match (keyword appears as a whole word)
                    elif f" {keyword_lower} " in f" {field_value} ":
                        score += points
                    
                    # Partial match (keyword appears somewhere in the value)
                    elif keyword_lower in field_value:
                        score += points * 0.7  # Reduced points for partial match
            
            # Check for matches in search keywords
            if "search_keywords" in track and isinstance(track["search_keywords"], list):
                for kw in track["search_keywords"]:
                    if keyword_lower in kw.lower():
                        score += 1.0  # Each keyword match
            
            # Add to scored tracks
            track_with_score = track.copy()
            track_with_score["keyword_score"] = score
            scored_tracks.append(track_with_score)
        
        # Sort by score
        return sorted(scored_tracks, key=lambda x: x.get("keyword_score", 0), reverse=True)
    
    def _get_mock_trending(self, count: int) -> List[Dict[str, Any]]:
        """
        Get mock trending tracks for development mode.
        
        Args:
            count: Number of trending tracks to return
            
        Returns:
            List of mock trending tracks
        """
        mock_trending = [
            {
                "track_name": "trending_electronic_beat.mp3",
                "title": "Electronic Beat",
                "artist": "Nova Sounds",
                "genre": "Electronic",
                "bpm": 128,
                "key": "C Major",
                "duration": 180,
                "energy": 0.85,
                "mood": "Upbeat",
                "popularity": 0.95,
                "trending_position": 1
            },
            {
                "track_name": "trending_hip_hop_groove.mp3",
                "title": "Hip Hop Groove",
                "artist": "Nova Sounds",
                "genre": "Hip Hop",
                "bpm": 95,
                "key": "G Minor",
                "duration": 165,
                "energy": 0.75,
                "mood": "Confident",
                "popularity": 0.92,
                "trending_position": 2
            },
            {
                "track_name": "trending_pop_anthem.mp3",
                "title": "Pop Anthem",
                "artist": "Nova Sounds",
                "genre": "Pop",
                "bpm": 120,
                "key": "A Major",
                "duration": 195,
                "energy": 0.8,
                "mood": "Happy",
                "popularity": 0.88,
                "trending_position": 3
            },
            {
                "track_name": "trending_ambient_chill.mp3",
                "title": "Ambient Chill",
                "artist": "Nova Sounds",
                "genre": "Ambient",
                "bpm": 75,
                "key": "F# Minor",
                "duration": 210,
                "energy": 0.4,
                "mood": "Calm",
                "popularity": 0.85,
                "trending_position": 4
            },
            {
                "track_name": "trending_cinematic_drama.mp3",
                "title": "Cinematic Drama",
                "artist": "Nova Sounds",
                "genre": "Cinematic",
                "bpm": 90,
                "key": "D Minor",
                "duration": 225,
                "energy": 0.7,
                "mood": "Dramatic",
                "popularity": 0.82,
                "trending_position": 5
            },
            {
                "track_name": "trending_house_beat.mp3",
                "title": "House Beat",
                "artist": "Nova Sounds",
                "genre": "House",
                "bpm": 125,
                "key": "E Minor",
                "duration": 185,
                "energy": 0.8,
                "mood": "Energetic",
                "popularity": 0.8,
                "trending_position": 6
            },
            {
                "track_name": "trending_lofi_beats.mp3",
                "title": "Lo-Fi Beats",
                "artist": "Nova Sounds",
                "genre": "Lo-Fi",
                "bpm": 85,
                "key": "C Minor",
                "duration": 175,
                "energy": 0.5,
                "mood": "Relaxed",
                "popularity": 0.78,
                "trending_position": 7
            }
        ]
        
        return mock_trending[:count]
    
    def recommend_for_user(
        self,
        user_id: str,
        count: int = 5,
        include_waveform: bool = False,
        preferred_genres: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recommend tracks based on user history and preferences.
        
        Args:
            user_id: ID of the user to recommend for
            count: Number of recommendations to return
            include_waveform: Whether to include waveform data
            preferred_genres: Optional list of preferred genres
            context: Optional context (e.g., 'editing', 'browsing')
            
        Returns:
            List of recommended tracks with metadata
        """
        self.last_used_algorithm = "user_preferences"
        
        # Get user preferences (or create empty if not exists)
        if user_id not in self.user_preferences:
            # Try to load from database first
            db_prefs = get_music_preferences(user_id)
            if db_prefs:
                self.user_preferences[user_id] = db_prefs
            else:
                # Create new default preferences
                self.user_preferences[user_id] = {
                    "favorite_genres": [],
                    "favorite_moods": [],
                    "listened_tracks": [],
                    "liked_tracks": [],
                    "disliked_tracks": []
                }
                # Save the newly created preferences
                self._save_user_preference(user_id)
        
        user_prefs = self.user_preferences[user_id]
        
        # Use specified genres or fall back to user favorites
        target_genres = preferred_genres if preferred_genres else user_prefs.get("favorite_genres", [])
        
        # Prepare candidate tracks list
        candidate_tracks = []
        
        # 1. First try tracks with user's favorite genres/moods
        if target_genres or user_prefs.get("favorite_moods"):
            genre = target_genres[0] if target_genres else None
            mood = user_prefs.get("favorite_moods", [""])[0] if user_prefs.get("favorite_moods") else None
            
            genre_mood_tracks = search_tracks_by_metadata(
                genre=genre, 
                mood=mood,
                limit=50
            )
            candidate_tracks.extend(genre_mood_tracks)
        
        # 2. Add tracks similar to user's liked tracks
        for liked_track in user_prefs.get("liked_tracks", [])[:3]:  # Use top 3 liked tracks
            try:
                similar_tracks = self.recommend_similar(
                    track_name=liked_track,
                    count=3,
                    include_waveform=False
                )
                candidate_tracks.extend(similar_tracks)
            except Exception as e:
                logger.warning(f"Error getting similar tracks to {liked_track}: {e}")
        
        # 3. Add some trending tracks for variety
        trending_tracks = self.recommend_trending(count=5, include_waveform=False)
        candidate_tracks.extend(trending_tracks)
        
        # Remove duplicates and disliked tracks
        filtered_tracks = []
        seen_track_names = set()
        disliked_tracks = set(user_prefs.get("disliked_tracks", []))
        
        for track in candidate_tracks:
            track_name = track.get("track_name")
            if track_name and track_name not in seen_track_names and track_name not in disliked_tracks:
                filtered_tracks.append(track)
                seen_track_names.add(track_name)
        
        # Score tracks based on user preferences
        scored_tracks = self._score_tracks_for_user(filtered_tracks, user_id, context)
        
        # Get top recommendations
        recommendations = scored_tracks[:count]
        
        # Add waveform data if requested
        if include_waveform:
            for track in recommendations:
                try:
                    track_name = track.get("track_name")
                    if track_name:
                        track["waveform"] = get_track_waveform(track_name)
                except Exception as e:
                    logger.warning(f"Error getting waveform for {track_name}: {e}")
        
        # Update usage stats and track listening history
        for track in recommendations:
            track_name = track.get("track_name")
            if track_name:
                self.track_usage_stats[track_name] += 1
                
                # Add to user's listened tracks history
                if "listened_tracks" not in user_prefs:
                    user_prefs["listened_tracks"] = []
                
                # Add to start of list, keep the list to reasonable size
                if track_name in user_prefs["listened_tracks"]:
                    user_prefs["listened_tracks"].remove(track_name)
                user_prefs["listened_tracks"].insert(0, track_name)
                
                # Limit to last 50 tracks
                user_prefs["listened_tracks"] = user_prefs["listened_tracks"][:50]
        
        # Save updated listening history
        self._save_user_preference(user_id)
        
        return recommendations
    
    def bulk_recommend(
        self,
        count_per_category: int = 3,
        categories: Optional[List[str]] = None,
        include_waveform: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get recommendations across multiple categories in a single call.
        
        Args:
            count_per_category: Number of tracks to recommend per category
            categories: List of categories to include (defaults to all)
            include_waveform: Whether to include waveform data
            
        Returns:
            Dict mapping category names to lists of recommended tracks
        """
        self.last_used_algorithm = "bulk_recommend"
        
        available_categories = [
            "trending", 
            "electronic", 
            "cinematic", 
            "hip_hop", 
            "ambient",
            "upbeat",
            "calm",
            "instrumental"
        ]
        
        if categories is None:
            categories = available_categories
        else:
            # Filter to only valid categories
            categories = [c for c in categories if c in available_categories]
        
        results = {}
        
        # Get recommendations for each category
        for category in categories:
            try:
                if category == "trending":
                    tracks = self.recommend_trending(count=count_per_category, include_waveform=include_waveform)
                elif category in ["electronic", "cinematic", "hip_hop", "ambient"]:
                    # These are genre-based categories
                    genre = category.replace("_", " ").title()
                    tracks = search_tracks_by_metadata(genre=genre, limit=count_per_category * 2)
                    tracks = sorted(tracks, key=lambda x: x.get("energy", 0.5), reverse=True)[:count_per_category]
                elif category in ["upbeat", "calm"]:
                    # These are mood-based categories
                    mood = category.title()
                    tracks = search_tracks_by_metadata(mood=mood, limit=count_per_category * 2)
                    tracks = tracks[:count_per_category]
                elif category == "instrumental":
                    # Get instrumental tracks
                    all_tracks = list_music_tracks(limit=100)
                    track_metadata = [get_track_metadata(t) for t in all_tracks[:50]]
                    instrumentals = [t for t in track_metadata if t.get("instrumental", False)]
                    tracks = instrumentals[:count_per_category]
                else:
                    # Shouldn't happen due to filtering above, but just in case
                    continue
                
                # Add waveform if requested and not already included
                if include_waveform and tracks and "waveform" not in tracks[0]:
                    for track in tracks:
                        try:
                            track_name = track.get("track_name")
                            if track_name:
                                track["waveform"] = get_track_waveform(track_name)
                        except Exception as e:
                            logger.warning(f"Error getting waveform for {track_name}: {e}")
                
                results[category] = tracks
            except Exception as e:
                logger.error(f"Error getting recommendations for category {category}: {e}")
                results[category] = []
        
        return results
    
    def update_user_preferences(
        self,
        user_id: str,
        liked_tracks: Optional[List[str]] = None,
        disliked_tracks: Optional[List[str]] = None,
        favorite_genres: Optional[List[str]] = None,
        favorite_moods: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update preferences for a specific user.
        
        Args:
            user_id: ID of the user
            liked_tracks: Optional list of track names the user liked
            disliked_tracks: Optional list of track names the user disliked
            favorite_genres: Optional list of genres the user prefers
            favorite_moods: Optional list of moods the user prefers
            
        Returns:
            Dict with updated user preferences
        """
        # Initialize user preferences if not exists
        if user_id not in self.user_preferences:
            # Try to load from database first
            db_prefs = get_music_preferences(user_id)
            if db_prefs:
                self.user_preferences[user_id] = db_prefs
            else:
                # Create new default preferences
                self.user_preferences[user_id] = {
                    "favorite_genres": [],
                    "favorite_moods": [],
                    "listened_tracks": [],
                    "liked_tracks": [],
                    "disliked_tracks": []
                }
        
        user_prefs = self.user_preferences[user_id]
        
        # Update liked tracks
        if liked_tracks:
            # Add new liked tracks
            for track in liked_tracks:
                if track not in user_prefs["liked_tracks"]:
                    user_prefs["liked_tracks"].append(track)
                
                # Remove from disliked if it was previously disliked
                if track in user_prefs["disliked_tracks"]:
                    user_prefs["disliked_tracks"].remove(track)
        
        # Update disliked tracks
        if disliked_tracks:
            # Add new disliked tracks
            for track in disliked_tracks:
                if track not in user_prefs["disliked_tracks"]:
                    user_prefs["disliked_tracks"].append(track)
                
                # Remove from liked if it was previously liked
                if track in user_prefs["liked_tracks"]:
                    user_prefs["liked_tracks"].remove(track)
        
        # Update favorite genres
        if favorite_genres:
            user_prefs["favorite_genres"] = favorite_genres
        
        # Update favorite moods
        if favorite_moods:
            user_prefs["favorite_moods"] = favorite_moods
        
        # Auto-detect genre and mood preferences from liked tracks
        if not favorite_genres and not favorite_moods and liked_tracks:
            self._update_preferences_from_tracks(user_id, liked_tracks)
        
        # Save the updated preferences to database
        self._save_user_preference(user_id)
        
        return user_prefs
    
    def record_track_usage(self, track_name: str, usage_type: str = "played") -> None:
        """
        Record track usage for popularity calculation.
        
        Args:
            track_name: Name of the track used
            usage_type: Type of usage (played, selected, downloaded)
        """
        # Increment usage counter
        self.track_usage_stats[track_name] += 1
        
        # Add metadata if we don't already have it
        if track_name not in self.track_cache:
            try:
                self.track_cache[track_name] = get_track_metadata(track_name)
            except Exception as e:
                logger.warning(f"Error caching metadata for {track_name}: {e}")
    
    def get_recommendations_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information about the recommendation engine.
        
        Returns:
            Dict with debug information
        """
        try:
            # Count tracks by genre
            genre_counts = defaultdict(int)
            for track_name, metadata in self.track_cache.items():
                if metadata and "genre" in metadata:
                    genre_counts[metadata["genre"]] += 1
            
            # Sort genres by count
            top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Get top tracks by usage
            top_tracks = sorted(self.track_usage_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Get algorithm usage history
            algorithm = self.last_used_algorithm
            
            return {
                "cached_tracks_count": len(self.track_cache),
                "top_genres": top_genres,
                "top_used_tracks": top_tracks,
                "cached_video_analyses": len(self.video_analysis_cache),
                "user_count": len(self.user_preferences),
                "last_algorithm": algorithm
            }
        except Exception as e:
            logger.error(f"Error getting debug info: {e}")
            return {"error": str(e)}
    
    def sort_tracks_by_criteria(
        self,
        tracks: List[Dict[str, Any]],
        sort_by: str = "energy",
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Sort a list of tracks by specified criteria.
        
        Args:
            tracks: List of track metadata to sort
            sort_by: Criteria to sort by (energy, bpm, duration, name)
            ascending: Whether to sort in ascending order
            
        Returns:
            Sorted list of tracks
        """
        if not tracks:
            return []
        
        valid_criteria = {
            "energy": lambda t: t.get("energy", 0),
            "bpm": lambda t: t.get("bpm", 0),
            "duration": lambda t: t.get("duration", 0),
            "name": lambda t: t.get("title", "").lower(),
            "mood": lambda t: t.get("mood", "").lower(),
            "popularity": lambda t: self.track_usage_stats.get(t.get("track_name", ""), 0)
        }
        
        # Default to energy if invalid criteria
        sort_func = valid_criteria.get(sort_by, valid_criteria["energy"])
        
        return sorted(tracks, key=sort_func, reverse=not ascending)
    
    def _score_tracks_for_user(
        self,
        tracks: List[Dict[str, Any]],
        user_id: str,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Score tracks based on user preferences.
        
        Args:
            tracks: List of track metadata
            user_id: ID of the user
            context: Optional context (e.g., 'editing', 'browsing')
            
        Returns:
            List of tracks sorted by relevance to user
        """
        user_prefs = self.user_preferences.get(user_id, {})
        scored_tracks = []
        
        liked_tracks = set(user_prefs.get("liked_tracks", []))
        favorite_genres = set(user_prefs.get("favorite_genres", []))
        favorite_moods = set(user_prefs.get("favorite_moods", []))
        
        # Default weights
        weights = {
            "genre_match": 3.0,
            "mood_match": 2.0,
            "similar_to_liked": 4.0,
            "popularity": 1.0,
            "recency": 1.0
        }
        
        # Adjust weights based on context
        if context == "editing":
            weights["mood_match"] = 3.0
            weights["similar_to_liked"] = 3.0
        elif context == "browsing":
            weights["popularity"] = 2.0
            weights["recency"] = 2.0
        
        for track in tracks:
            score = 0.0
            track_name = track.get("track_name", "")
            genre = track.get("genre", "")
            mood = track.get("mood", "")
            
            # Genre match
            if genre and genre in favorite_genres:
                score += weights["genre_match"]
            
            # Mood match
            if mood and mood in favorite_moods:
                score += weights["mood_match"]
            
            # Similar to liked tracks
            for liked_track in liked_tracks:
                try:
                    similarity = compute_track_similarity(track_name, liked_track)
                    score += similarity * weights["similar_to_liked"]
                except Exception:
                    pass
            
            # Popularity bonus
            popularity = self.track_usage_stats.get(track_name, 0)
            score += min(3.0, popularity / 5) * weights["popularity"]
            
            # Add small random factor for variety
            score += random.uniform(0.0, 0.5)
            
            # Add to scored tracks
            track_with_score = track.copy()
            track_with_score["user_score"] = score
            scored_tracks.append(track_with_score)
        
        # Sort by score
        return sorted(scored_tracks, key=lambda x: x.get("user_score", 0), reverse=True)
    
    def _update_preferences_from_tracks(self, user_id: str, track_names: List[str]) -> None:
        """
        Analyze liked tracks to update user genre and mood preferences.
        
        Args:
            user_id: ID of the user
            track_names: List of track names to analyze
        """
        if not track_names:
            return
        
        # Get metadata for tracks
        genre_counts = defaultdict(int)
        mood_counts = defaultdict(int)
        
        for track_name in track_names:
            try:
                metadata = get_track_metadata(track_name)
                if metadata:
                    if "genre" in metadata and metadata["genre"]:
                        genre_counts[metadata["genre"]] += 1
                    if "mood" in metadata and metadata["mood"]:
                        mood_counts[metadata["mood"]] += 1
            except Exception as e:
                logger.warning(f"Error getting metadata for {track_name}: {e}")
        
        # Get top genres and moods
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        top_moods = sorted(mood_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Update user preferences with top 3 genres and moods
        if top_genres:
            self.user_preferences[user_id]["favorite_genres"] = [g[0] for g in top_genres[:3]]
        
        if top_moods:
            self.user_preferences[user_id]["favorite_moods"] = [m[0] for m in top_moods[:3]]
        
        # Save updated preferences to database
        self._save_user_preference(user_id)

    def export_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Export a user's music preferences.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict[str, Any]: User's music preferences 
        """
        # Ensure user preferences are loaded
        if user_id not in self.user_preferences:
            db_prefs = get_music_preferences(user_id)
            if db_prefs:
                self.user_preferences[user_id] = db_prefs
            else:
                return {}  # No preferences found
        
        # Return a deep copy to prevent external modification
        import copy
        return copy.deepcopy(self.user_preferences.get(user_id, {}))

    def import_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Import music preferences for a user.
        
        Args:
            user_id: ID of the user
            preferences: The preferences to import
            
        Returns:
            bool: True if imported successfully
        """
        # Validate the preferences structure
        required_keys = ["favorite_genres", "favorite_moods", "liked_tracks", "disliked_tracks"]
        for key in required_keys:
            if key not in preferences:
                preferences[key] = []
        
        # Set the preferences
        self.user_preferences[user_id] = preferences
        
        # Save to database
        self._save_user_preference(user_id)
        
        return True

    def debug_database_state(self) -> Dict[str, Any]:
        """
        Debug method to check the state of the persistence system.
        Useful for troubleshooting database issues.
        
        Returns:
            Dict with debug information about the database
        """
        result = {
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            # Check if mock data directory exists
            mock_dir = os.path.join(os.getcwd(), "mock-data")
            result["details"]["mock_dir_exists"] = os.path.exists(mock_dir)
            result["details"]["mock_dir_path"] = mock_dir
            
            if not result["details"]["mock_dir_exists"]:
                result["message"] = "Mock data directory doesn't exist"
                return result
                
            # Check if music preferences file exists
            prefs_file = os.path.join(mock_dir, "music_preferences.json")
            result["details"]["prefs_file_exists"] = os.path.exists(prefs_file)
            result["details"]["prefs_file_path"] = prefs_file
            
            if result["details"]["prefs_file_exists"]:
                # Get file stats
                file_stats = os.stat(prefs_file)
                result["details"]["file_size"] = file_stats.st_size
                result["details"]["last_modified"] = datetime.fromtimestamp(
                    file_stats.st_mtime
                ).isoformat()
                
                # Try to read the file
                try:
                    with open(prefs_file, "r") as f:
                        data = json.load(f)
                    result["details"]["file_readable"] = True
                    result["details"]["user_count"] = len(data)
                    result["details"]["users"] = list(data.keys())
                    
                    # Check each user's data
                    user_details = {}
                    for user_id, prefs in data.items():
                        user_details[user_id] = {
                            "keys": list(prefs.keys()),
                            "liked_tracks_count": len(prefs.get("liked_tracks", [])),
                            "disliked_tracks_count": len(prefs.get("disliked_tracks", [])),
                            "favorite_genres": prefs.get("favorite_genres", []),
                            "favorite_moods": prefs.get("favorite_moods", [])
                        }
                    result["details"]["user_details"] = user_details
                    
                    # Verify memory state matches file state
                    result["details"]["memory_matches_file"] = True
                    for user_id in data.keys():
                        if user_id not in self.user_preferences:
                            result["details"]["memory_matches_file"] = False
                            break
                        
                except Exception as e:
                    result["details"]["file_readable"] = False
                    result["details"]["read_error"] = str(e)
                    result["message"] = f"Error reading preferences file: {e}"
                    return result
            else:
                result["message"] = "Preferences file doesn't exist"
                return result
            
            # Try to write a test file to check permissions
            test_file = os.path.join(mock_dir, "test_write.txt")
            try:
                with open(test_file, "w") as f:
                    f.write("Test write")
                result["details"]["write_permission"] = True
                
                # Clean up test file
                os.remove(test_file)
            except Exception as e:
                result["details"]["write_permission"] = False
                result["details"]["write_error"] = str(e)
                result["message"] = f"Write permission error: {e}"
                return result
            
            # All checks passed
            result["success"] = True
            result["message"] = "Database check successful"
            
        except Exception as e:
            result["success"] = False
            result["message"] = f"Error checking database state: {e}"
            import traceback
            result["details"]["traceback"] = traceback.format_exc()
        
        return result


def get_music_recommendation_service() -> MusicRecommendationService:
    """
    Get the singleton instance of the music recommendation service.
    
    Returns:
        MusicRecommendationService instance
    """
    return MusicRecommendationService() 