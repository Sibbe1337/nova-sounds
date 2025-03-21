"""
Nova Sounds music catalog service.
Handles fetching, caching, and enriching music track metadata.
"""
import os
import json
import logging
import base64
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import threading
import time
from pathlib import Path

from google.cloud import storage
from google.cloud.storage.blob import Blob
import requests
import redis

from src.app.models.music import MusicTrack, GenreType, MoodType, EnergyLevel, LicenseType
from src.app.services.audio.analyzer import AudioAnalyzer
from src.app.core.settings import DEV_MODE, DEBUG_MODE

# Set up logging
logger = logging.getLogger(__name__)

# Constants
CACHE_EXPIRY = 3600  # 1 hour in seconds
METADATA_CACHE_KEY = "nova_sounds_catalog_metadata"
TRACK_CACHE_PREFIX = "nova_sounds_track_"

class MusicCatalogService:
    """Service for managing the Nova Sounds music catalog."""
    
    def __init__(self, bucket_name: Optional[str] = None, redis_url: Optional[str] = None):
        """
        Initialize the music catalog service.
        
        Args:
            bucket_name: Name of the GCS bucket. If None, uses environment variable GCS_BUCKET_NAME.
            redis_url: Redis URL for caching. If None, uses environment variable REDIS_URL.
        """
        self.bucket_name = bucket_name or os.environ.get("GCS_BUCKET_NAME", "youtubeshorts123")
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.audio_analyzer = AudioAnalyzer()
        
        self._initialize()
        logger.info(f"Initialized MusicCatalogService with bucket: {self.bucket_name}")
        
        # Start background refresh thread
        self._start_background_refresh()
    
    def _initialize(self):
        """Initialize the service, setting up GCS and Redis clients."""
        self.client = storage.Client()
        
        try:
            self.redis = redis.from_url(self.redis_url)
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis cache: {e}. Caching disabled.")
            self.redis = None
    
    def _start_background_refresh(self):
        """Start a background thread to periodically refresh the cache."""
        if not self.redis:
            return
            
        def refresh_worker():
            while True:
                try:
                    # Only refresh if cache is about to expire
                    ttl = self.redis.ttl(METADATA_CACHE_KEY)
                    if ttl < 600:  # Less than 10 minutes left
                        logger.info("Background refresh: Updating catalog metadata")
                        self._fetch_and_cache_metadata()
                except Exception as e:
                    logger.error(f"Error in background refresh: {e}")
                
                # Sleep for 5 minutes
                time.sleep(300)
        
        thread = threading.Thread(target=refresh_worker, daemon=True)
        thread.start()
        logger.info("Started background metadata refresh thread")
    
    def _get_bucket(self):
        """
        Get a reference to the GCS bucket.
        
        Returns:
            google.cloud.storage.bucket.Bucket: GCS bucket
        """
        return self.client.bucket(self.bucket_name)
    
    def _fetch_and_cache_metadata(self) -> List[Dict[str, Any]]:
        """
        Fetch metadata from GCS and cache it.
        
        Returns:
            List: Track metadata
        """
        logger.info(f"Fetching music track metadata from bucket: {self.bucket_name}")
        
        if DEV_MODE and not DEBUG_MODE:
            logger.info("DEV mode: Using mock track metadata")
            # Create mock tracks
            mock_tracks = []
            
            # Read mock tracks from directory
            mock_dir = "mock-media"
            if os.path.exists(mock_dir):
                for filename in os.listdir(mock_dir):
                    if filename.endswith(".mp3"):
                        track_id = filename.split(".")[0]
                        track_data = {
                            "id": track_id,
                            "title": f"Nova Sounds - {track_id.capitalize()}",
                            "artist": "Nova Sounds Artist",
                            "duration": 60,
                            "track_uri": f"http://localhost:8001/mock-media/{filename}",
                            "thumbnail_uri": f"http://localhost:8001/mock-media/image_{track_id}.jpg",
                            "license_type": "standard",
                            "bpm": 120,
                            "energy_level": "medium",
                            "genres": ["electronic", "pop"],
                            "moods": ["energetic", "happy"]
                        }
                        mock_tracks.append(track_data)
            
            # If no mock tracks found, create some defaults
            if not mock_tracks:
                for i in range(1, 6):
                    track_id = f"track{i}"
                    track_data = {
                        "id": track_id,
                        "title": f"Nova Sounds - Track {i}",
                        "artist": "Nova Sounds Artist",
                        "duration": 60,
                        "track_uri": f"http://localhost:8001/mock-media/{track_id}.mp3",
                        "thumbnail_uri": f"http://localhost:8001/mock-media/image_{track_id}.jpg",
                        "license_type": "standard",
                        "bpm": 120,
                        "energy_level": "medium",
                        "genres": ["electronic", "pop"],
                        "moods": ["energetic", "happy"]
                    }
                    mock_tracks.append(track_data)
            
            # Cache mock tracks if Redis is available
            if self.redis:
                self.redis.set(
                    METADATA_CACHE_KEY,
                    json.dumps(mock_tracks),
                    ex=CACHE_EXPIRY
                )
            
            return mock_tracks
        
        try:
            bucket = self._get_bucket()
            
            # List all .mp3 files in the bucket
            blobs = list(bucket.list_blobs(prefix=""))
            tracks = []
            
            for blob in blobs:
                if blob.name.lower().endswith(('.mp3', '.wav')):
                    # Extract metadata from blob
                    metadata = blob.metadata or {}
                    
                    # Generate a signed URL for the track
                    track_url = blob.generate_signed_url(
                        expiration=datetime.now() + timedelta(hours=24),
                        method="GET"
                    )
                    
                    # Try to find a thumbnail with the same name
                    thumbnail_url = None
                    thumbnail_blob_name = f"{os.path.splitext(blob.name)[0]}.jpg"
                    thumbnail_blob = bucket.blob(thumbnail_blob_name)
                    
                    if thumbnail_blob.exists():
                        thumbnail_url = thumbnail_blob.generate_signed_url(
                            expiration=datetime.now() + timedelta(hours=24),
                            method="GET"
                        )
                    
                    # Extract track ID from filename
                    track_id = os.path.splitext(os.path.basename(blob.name))[0]
                    
                    # Create track data
                    track_data = {
                        "id": track_id,
                        "title": metadata.get("title", os.path.basename(blob.name)),
                        "artist": metadata.get("artist", "Nova Sounds"),
                        "duration": int(metadata.get("duration", 60)),
                        "track_uri": track_url,
                        "thumbnail_uri": thumbnail_url,
                        "license_type": metadata.get("license", "standard"),
                        "bpm": float(metadata.get("bpm", 120)),
                        "energy_level": metadata.get("energy_level", "medium"),
                        "genres": metadata.get("genres", "").split(",") if metadata.get("genres") else ["electronic"],
                        "moods": metadata.get("moods", "").split(",") if metadata.get("moods") else ["energetic"]
                    }
                    
                    tracks.append(track_data)
            
            logger.info(f"Fetched {len(tracks)} tracks from GCS bucket")
            
            # Cache the tracks if Redis is available
            if self.redis:
                self.redis.set(
                    METADATA_CACHE_KEY,
                    json.dumps(tracks),
                    ex=CACHE_EXPIRY
                )
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error fetching tracks from GCS: {e}")
            
            # Try to get from cache if available
            if self.redis:
                cached_data = self.redis.get(METADATA_CACHE_KEY)
                if cached_data:
                    logger.info("Using cached track metadata due to GCS error")
                    return json.loads(cached_data)
            
            # Return empty list if all else fails
            return []
    
    def _convert_to_music_track(self, track_data: Dict[str, Any]) -> MusicTrack:
        """
        Convert raw track data to a MusicTrack model.
        
        Args:
            track_data: Raw track data
            
        Returns:
            MusicTrack: Music track model
        """
        # Convert string enums to proper enum values
        energy_level = None
        if "energy_level" in track_data:
            try:
                energy_level = EnergyLevel(track_data["energy_level"].lower())
            except (ValueError, AttributeError):
                energy_level = EnergyLevel.MEDIUM
        
        # Convert genres
        genres = []
        for genre_str in track_data.get("genres", []):
            try:
                genres.append(GenreType(genre_str.lower()))
            except (ValueError, AttributeError):
                # Skip invalid genres
                pass
        
        # Convert moods
        moods = []
        for mood_str in track_data.get("moods", []):
            try:
                moods.append(MoodType(mood_str.lower()))
            except (ValueError, AttributeError):
                # Skip invalid moods
                pass
        
        # Convert license type
        try:
            license_type = LicenseType(track_data.get("license_type", "standard").lower())
        except (ValueError, AttributeError):
            license_type = LicenseType.STANDARD
        
        # Create the music track
        return MusicTrack(
            id=track_data["id"],
            title=track_data["title"],
            artist=track_data["artist"],
            duration=track_data["duration"],
            bpm=track_data.get("bpm"),
            energy_level=energy_level,
            moods=moods,
            genres=genres,
            license_type=license_type,
            attribution_required=track_data.get("attribution_required", True),
            waveform_data=track_data.get("waveform_data"),
            beat_markers=track_data.get("beat_markers", []),
            track_uri=track_data["track_uri"],
            preview_uri=track_data.get("preview_uri"),
            thumbnail_uri=track_data.get("thumbnail_uri"),
            popularity=track_data.get("popularity"),
            features=track_data.get("features", {})
        )
    
    def get_tracks(self, prefix: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[MusicTrack]:
        """
        Get music tracks from the catalog.
        
        Args:
            prefix: Optional prefix to filter tracks by name
            limit: Maximum number of tracks to return
            offset: Offset for pagination
            
        Returns:
            List[MusicTrack]: List of music tracks
        """
        # Check cache first
        if self.redis:
            cached_data = self.redis.get(METADATA_CACHE_KEY)
            if cached_data:
                tracks_data = json.loads(cached_data)
            else:
                tracks_data = self._fetch_and_cache_metadata()
        else:
            tracks_data = self._fetch_and_cache_metadata()
        
        # Filter by prefix if provided
        if prefix:
            prefix = prefix.lower()
            filtered_tracks = [
                t for t in tracks_data 
                if (prefix in t.get("title", "").lower()) or 
                   (prefix in t.get("artist", "").lower())
            ]
        else:
            filtered_tracks = tracks_data
        
        # Apply pagination
        paginated_tracks = filtered_tracks[offset:offset+limit]
        
        # Convert to MusicTrack objects
        return [self._convert_to_music_track(t) for t in paginated_tracks]
    
    def get_track(self, track_id: str) -> Optional[MusicTrack]:
        """
        Get a single music track by ID.
        
        Args:
            track_id: ID of the track
            
        Returns:
            Optional[MusicTrack]: Music track if found, None otherwise
        """
        # Try cache first
        if self.redis:
            track_cache_key = f"{TRACK_CACHE_PREFIX}{track_id}"
            cached_track = self.redis.get(track_cache_key)
            
            if cached_track:
                track_data = json.loads(cached_track)
                return self._convert_to_music_track(track_data)
        
        # Get from full catalog
        tracks = self.get_tracks()
        for track in tracks:
            if track.id == track_id:
                # Cache for future use
                if self.redis:
                    self.redis.set(
                        f"{TRACK_CACHE_PREFIX}{track_id}",
                        json.dumps(track.dict()),
                        ex=CACHE_EXPIRY
                    )
                return track
        
        return None
    
    def enrich_track(self, track_id: str) -> Optional[MusicTrack]:
        """
        Enrich a track with audio analysis data.
        
        Args:
            track_id: ID of the track to enrich
            
        Returns:
            Optional[MusicTrack]: Enriched music track if found, None otherwise
        """
        # Get the basic track
        track = self.get_track(track_id)
        if not track:
            return None
            
        # Check if already enriched
        if track.beat_markers and track.waveform_data:
            logger.info(f"Track {track_id} already enriched")
            return track
            
        logger.info(f"Enriching track {track_id} with audio analysis")
        
        try:
            # Analyze the track
            analysis = self.audio_analyzer.analyze_track(track_id, track.track_uri)
            
            # Update track data
            track_dict = track.dict()
            track_dict.update({
                "bpm": analysis.bpm,
                "energy_level": analysis.energy_level,
                "beat_markers": analysis.beat_markers,
                "waveform_data": analysis.waveform_data,
                "features": analysis.features
            })
            
            # Create updated track
            enriched_track = MusicTrack(**track_dict)
            
            # Cache the enriched track
            if self.redis:
                self.redis.set(
                    f"{TRACK_CACHE_PREFIX}{track_id}",
                    json.dumps(enriched_track.dict()),
                    ex=CACHE_EXPIRY
                )
            
            logger.info(f"Successfully enriched track {track_id}")
            return enriched_track
            
        except Exception as e:
            logger.error(f"Error enriching track {track_id}: {e}")
            return track
    
    def search_tracks(self, query: str = "", 
                      filters: dict = None, 
                      sort_by: str = "title", 
                      sort_order: str = "asc", 
                      limit: int = 50, 
                      offset: int = 0) -> List[Dict[str, Any]]:
        """
        Advanced search and filtering for music tracks.
        
        Args:
            query: Search query string
            filters: Dictionary of filter criteria
            sort_by: Field to sort by
            sort_order: Sort direction ('asc' or 'desc')
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List[Dict[str, Any]]: List of matching tracks with metadata
        """
        # Get all tracks with metadata
        all_tracks = self.get_tracks(limit=100)
        
        # Apply text search if query is provided
        filtered_tracks = all_tracks
        if query:
            query = query.lower()
            filtered_tracks = [
                track for track in filtered_tracks
                if query in track.title.lower() or 
                   query in track.artist.lower() or
                   query in track.genre.value.lower() or
                   any(query in tag.lower() for tag in track.tags)
            ]
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if key == "genre":
                    filtered_tracks = [track for track in filtered_tracks if track.genre.value == value]
                elif key == "mood":
                    filtered_tracks = [track for track in filtered_tracks if track.mood in value]
                elif key == "energy_level":
                    filtered_tracks = [track for track in filtered_tracks if track.energy_level == value]
                elif key == "bpm_min":
                    filtered_tracks = [track for track in filtered_tracks if track.bpm >= value]
                elif key == "bpm_max":
                    filtered_tracks = [track for track in filtered_tracks if track.bpm <= value]
                elif key == "duration_min":
                    filtered_tracks = [track for track in filtered_tracks if track.duration >= value]
                elif key == "duration_max":
                    filtered_tracks = [track for track in filtered_tracks if track.duration <= value]
                elif key == "tags":
                    # Handle tags as a list of required tags
                    tags = value if isinstance(value, list) else [value]
                    filtered_tracks = [
                        track for track in filtered_tracks 
                        if all(tag in track.tags for tag in tags)
                    ]
        
        # Sort the tracks
        if sort_by in ["title", "artist", "genre", "bpm", "duration"]:
            reverse = sort_order.lower() == "desc"
            filtered_tracks.sort(key=lambda x: getattr(x, sort_by) or "", reverse=reverse)
        
        # Apply pagination
        paginated_tracks = filtered_tracks[offset:offset + limit]
        
        return paginated_tracks
    
    def get_all_tracks_with_metadata(self) -> List[Dict[str, Any]]:
        """
        Get all available tracks with their metadata.
        
        Returns:
            List[Dict[str, Any]]: List of tracks with metadata
        """
        tracks = self.get_tracks(limit=100)
        tracks_with_metadata = []
        
        for track in tracks:
            metadata = {
                "id": track.id,
                "title": track.title,
                "artist": track.artist,
                "duration": track.duration,
                "track_uri": track.track_uri,
                "thumbnail_uri": track.thumbnail_uri,
                "license_type": track.license_type.value,
                "bpm": track.bpm,
                "energy_level": track.energy_level.value,
                "genres": [genre.value for genre in track.genres],
                "moods": [mood.value for mood in track.moods],
                "license": track.license_type.value,
                "popularity": track.popularity,
                "features": track.features,
                "beat_markers": track.beat_markers,
                "waveform_data": track.waveform_data,
                "genre": track.genre.value,
                "mood": track.mood.value,
                "tags": track.tags
            }
            tracks_with_metadata.append(metadata)
        
        return tracks_with_metadata
    
    def get_genre_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available genres.
        
        Returns:
            Dict[str, Any]: Dictionary with genre statistics
        """
        tracks = self.get_all_tracks_with_metadata()
        
        # Count tracks by genre
        genre_counts = {}
        for track in tracks:
            genre = track.get("genre", "Unknown")
            if genre in genre_counts:
                genre_counts[genre] += 1
            else:
                genre_counts[genre] = 1
        
        # Calculate percentages
        total_tracks = len(tracks)
        genre_percentages = {
            genre: (count / total_tracks) * 100 if total_tracks > 0 else 0
            for genre, count in genre_counts.items()
        }
        
        # Find most popular genre
        most_popular = max(genre_counts.items(), key=lambda x: x[1]) if genre_counts else ("Unknown", 0)
        
        return {
            "counts": genre_counts,
            "percentages": genre_percentages,
            "most_popular": most_popular[0],
            "total_tracks": total_tracks
        }
    
    def get_mood_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available moods.
        
        Returns:
            Dict[str, Any]: Dictionary with mood statistics
        """
        tracks = self.get_all_tracks_with_metadata()
        
        # Count tracks by mood
        mood_counts = {}
        for track in tracks:
            mood = track.get("mood", "Unknown")
            if mood in mood_counts:
                mood_counts[mood] += 1
            else:
                mood_counts[mood] = 1
        
        # Calculate percentages
        total_tracks = len(tracks)
        mood_percentages = {
            mood: (count / total_tracks) * 100 if total_tracks > 0 else 0
            for mood, count in mood_counts.items()
        }
        
        # Find most common mood
        most_common = max(mood_counts.items(), key=lambda x: x[1]) if mood_counts else ("Unknown", 0)
        
        return {
            "counts": mood_counts,
            "percentages": mood_percentages,
            "most_common": most_common[0],
            "total_tracks": total_tracks
        }
    
    def get_all_available_tags(self) -> List[str]:
        """
        Get a list of all available tags across all tracks.
        
        Returns:
            List[str]: List of unique tags
        """
        tracks = self.get_all_tracks_with_metadata()
        
        # Collect all tags
        all_tags = set()
        for track in tracks:
            tags = track.get("tags", [])
            all_tags.update(tags)
        
        return sorted(list(all_tags))
    
    def recommend_similar_tracks(self, track_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend tracks similar to the specified track.
        
        Args:
            track_name: Name of the reference track
            limit: Maximum number of recommendations to return
            
        Returns:
            List[Dict[str, Any]]: List of similar tracks with metadata
        """
        # Get metadata for the reference track
        reference_metadata = self.get_track(track_name)
        if not reference_metadata:
            return []
        
        # Get all tracks
        all_tracks = self.get_tracks(limit=100)
        
        # Remove the reference track from the list
        all_tracks = [track for track in all_tracks if track.id != track_name]
        
        # Calculate similarity scores
        similarity_scores = []
        for track in all_tracks:
            score = 0
            
            # Genre match
            if track.genre.value == reference_metadata.genre.value:
                score += 3
            
            # Mood match
            if track.mood.value == reference_metadata.mood.value:
                score += 2
            
            # Energy level match
            if track.energy_level.value == reference_metadata.energy_level.value:
                score += 2
            
            # BPM within 10% range
            ref_bpm = reference_metadata.bpm or 0
            track_bpm = track.bpm or 0
            if abs(ref_bpm - track_bpm) <= (ref_bpm * 0.1):
                score += 2
            
            # Key match
            if track.key == reference_metadata.key:
                score += 1
            
            # Tag overlap (each common tag adds 0.5 to the score)
            ref_tags = set(reference_metadata.tags)
            track_tags = set(track.tags)
            common_tags = ref_tags.intersection(track_tags)
            score += len(common_tags) * 0.5
            
            similarity_scores.append((track, score))
        
        # Sort by similarity score (descending)
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top recommendations
        return [track for track, _ in similarity_scores[:limit]]

# Add an alias for backwards compatibility
MusicCatalog = MusicCatalogService

# Singleton instance
_instance = None

def get_music_catalog(bucket_name: Optional[str] = None, redis_url: Optional[str] = None) -> MusicCatalogService:
    """
    Get the singleton instance of MusicCatalogService.
    
    Args:
        bucket_name: Optional GCS bucket name
        redis_url: Optional Redis URL for caching
        
    Returns:
        MusicCatalogService instance
    """
    global _instance
    if _instance is None:
        _instance = MusicCatalogService(bucket_name, redis_url)
    return _instance 