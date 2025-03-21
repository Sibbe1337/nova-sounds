"""
Advanced music metadata extraction service for audio files.
"""
import os
import tempfile
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import librosa
from pydub import AudioSegment
import requests
from pathlib import Path
import pickle
from datetime import datetime, timedelta

from src.app.core.settings import DEV_MODE, DEBUG_MODE, get_setting
from src.app.services.gcs.storage import get_music_url, download_file, list_music_tracks

# Set up logging
logger = logging.getLogger(__name__)

# Sample data for development mode
MOCK_METADATA = {
    "track1.mp3": {
        "title": "Electronic Dreams",
        "artist": "Nova Sounds",
        "genre": "Electronic",
        "bpm": 128,
        "key": "C Major",
        "duration": 180,
        "energy": 0.8,
        "mood": "Upbeat",
        "waveform_peaks": [0.2, 0.5, 0.8, 0.3, 0.6, 0.9, 0.4, 0.7, 0.3, 0.6]
    },
    "track2.mp3": {
        "title": "Cinematic Journey",
        "artist": "Nova Sounds",
        "genre": "Cinematic",
        "bpm": 90,
        "key": "D Minor",
        "duration": 210,
        "energy": 0.6,
        "mood": "Emotional",
        "waveform_peaks": [0.1, 0.3, 0.7, 0.9, 0.4, 0.2, 0.5, 0.8, 0.4, 0.6]
    },
    "track3.mp3": {
        "title": "Hip Hop Beats",
        "artist": "Nova Sounds",
        "genre": "Hip Hop",
        "bpm": 95,
        "key": "G Minor",
        "duration": 160,
        "energy": 0.75,
        "mood": "Confident",
        "waveform_peaks": [0.8, 0.7, 0.9, 0.6, 0.8, 0.7, 0.9, 0.5, 0.7, 0.6]
    },
    "track4.mp3": {
        "title": "Pop Sensation",
        "artist": "Nova Sounds",
        "genre": "Pop",
        "bpm": 120,
        "key": "A Major",
        "duration": 195,
        "energy": 0.85,
        "mood": "Happy",
        "waveform_peaks": [0.4, 0.6, 0.5, 0.7, 0.8, 0.3, 0.5, 0.7, 0.9, 0.6]
    },
    "track5.mp3": {
        "title": "Ambient Atmosphere",
        "artist": "Nova Sounds",
        "genre": "Ambient",
        "bpm": 75,
        "key": "F# Minor",
        "duration": 240,
        "energy": 0.4,
        "mood": "Calm",
        "waveform_peaks": [0.2, 0.3, 0.4, 0.3, 0.5, 0.4, 0.3, 0.5, 0.6, 0.4]
    }
}

# Cache for metadata with expiration
metadata_cache = {}
cache_expiration = {}
CACHE_DURATION = timedelta(hours=24)

# Create cache directory if it doesn't exist
CACHE_DIR = Path("data/cache/metadata")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Define common musical keys and modes
MUSICAL_KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MODES = ['Major', 'Minor']

# Mood mapping based on musical features
MOOD_MAPPING = {
    # High energy, major key
    ('high', 'Major'): ['Happy', 'Upbeat', 'Energetic', 'Exciting'],
    # High energy, minor key
    ('high', 'Minor'): ['Intense', 'Powerful', 'Dramatic', 'Angry'],
    # Medium energy, major key
    ('medium', 'Major'): ['Cheerful', 'Uplifting', 'Bright', 'Confident'],
    # Medium energy, minor key
    ('medium', 'Minor'): ['Melancholic', 'Emotional', 'Atmospheric', 'Moody'],
    # Low energy, major key
    ('low', 'Major'): ['Relaxed', 'Peaceful', 'Gentle', 'Dreamy'],
    # Low energy, minor key
    ('low', 'Minor'): ['Calm', 'Atmospheric', 'Mysterious', 'Moody']
}

class MusicMetadata:
    """Class to handle music metadata extraction and analysis."""
    
    def __init__(self, track_name: str, local_path: Optional[str] = None):
        """
        Initialize with track name and optional local path.
        
        Args:
            track_name: Name of the track in GCS
            local_path: Optional local path to the audio file
        """
        self.track_name = track_name
        self.local_path = local_path
        self._metadata = None
        self._waveform = None
        self._analyzed = False
        self._features = None
    
    def analyze(self, force: bool = False) -> Dict[str, Any]:
        """
        Analyze the audio file to extract metadata.
        
        Args:
            force: Whether to force re-analysis even if cached
            
        Returns:
            Dict with extracted metadata
        """
        # Check disk cache first if not forcing re-analysis
        cache_path = CACHE_DIR / f"{self.track_name.replace('/', '_')}.pkl"
        if not force and cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                    cached_time = cached_data.get('timestamp', datetime.min)
                    
                    # Check if cache is still valid
                    if datetime.now() - cached_time < CACHE_DURATION:
                        logger.info(f"Using disk cached metadata for {self.track_name}")
                        self._metadata = cached_data.get('metadata', {})
                        self._analyzed = True
                        # Update memory cache
                        metadata_cache[self.track_name] = self._metadata
                        cache_expiration[self.track_name] = cached_time + CACHE_DURATION
                        return self._metadata
            except Exception as e:
                logger.warning(f"Error loading disk cache for {self.track_name}: {e}")
        
        # Check memory cache if not forcing re-analysis
        if not force and self.track_name in metadata_cache:
            # Check if cache is expired
            if self.track_name in cache_expiration and datetime.now() < cache_expiration[self.track_name]:
                logger.info(f"Using memory cached metadata for {self.track_name}")
                self._metadata = metadata_cache[self.track_name]
                self._analyzed = True
                return self._metadata
        
        # Check for dev mode
        if DEV_MODE:
            logger.info(f"DEV mode: Using mock metadata for {self.track_name}")
            # Use mock data or generate if not in our samples
            basename = os.path.basename(self.track_name)
            if basename in MOCK_METADATA:
                self._metadata = MOCK_METADATA[basename].copy()
            else:
                # Generate random metadata
                import random
                genres = ["Electronic", "Cinematic", "Hip Hop", "Pop", "Ambient", "Rock", "Jazz"]
                keys = ["C Major", "A Minor", "D Major", "G Major", "E Minor", "F# Minor", "Bb Major"]
                moods = ["Upbeat", "Emotional", "Confident", "Happy", "Calm", "Energetic", "Melancholic"]
                self._metadata = {
                    "title": f"Track {random.randint(1, 100)}",
                    "artist": "Nova Sounds",
                    "genre": random.choice(genres),
                    "bpm": random.randint(70, 140),
                    "key": random.choice(keys),
                    "duration": random.randint(120, 240),
                    "energy": round(random.uniform(0.3, 0.9), 2),
                    "mood": random.choice(moods),
                    "waveform_peaks": [round(random.uniform(0.1, 0.9), 2) for _ in range(10)]
                }
            
            # Add track name and searchable keywords
            self._metadata["track_name"] = self.track_name
            self._metadata["search_keywords"] = self._generate_search_keywords(self._metadata)
            self._analyzed = True
            
            # Update caches
            metadata_cache[self.track_name] = self._metadata
            cache_expiration[self.track_name] = datetime.now() + CACHE_DURATION
            
            # Save to disk cache
            self._save_to_disk_cache(self._metadata)
            
            return self._metadata
            
        # Real analysis mode
        try:
            # If we don't have a local path, download the file
            temp_file = None
            file_path = self.local_path
            
            if not file_path or not os.path.exists(file_path):
                # Get a URL for the track
                track_url = get_music_url(self.track_name)
                
                # Create temp file
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, os.path.basename(self.track_name))
                
                # Download the file
                if track_url.startswith("http"):
                    logger.info(f"Downloading {self.track_name} for metadata extraction")
                    response = requests.get(track_url, stream=True)
                    response.raise_for_status()
                    
                    with open(temp_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    file_path = temp_file
                else:
                    # Use local file path from URL
                    file_path = track_url.replace("file://", "")
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"Local file {file_path} not found")
            
            # Extract audio metadata
            self._metadata = self._extract_metadata(file_path)
            self._metadata["track_name"] = self.track_name
            
            # Generate search keywords
            self._metadata["search_keywords"] = self._generate_search_keywords(self._metadata)
            
            # Update caches
            metadata_cache[self.track_name] = self._metadata
            cache_expiration[self.track_name] = datetime.now() + CACHE_DURATION
            
            # Save to disk cache
            self._save_to_disk_cache(self._metadata)
            
            # Clean up temp file if created
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
                
            self._analyzed = True
            return self._metadata
            
        except Exception as e:
            logger.error(f"Error analyzing audio {self.track_name}: {e}")
            # Use mock data as fallback
            basename = os.path.basename(self.track_name)
            if basename in MOCK_METADATA:
                self._metadata = MOCK_METADATA[basename].copy()
            else:
                # Basic metadata
                self._metadata = {
                    "title": self.track_name,
                    "artist": "Unknown",
                    "genre": "Unknown",
                    "bpm": 120,
                    "key": "Unknown",
                    "duration": 180,
                    "energy": 0.5,
                    "mood": "Neutral",
                    "waveform_peaks": [0.5] * 10,
                    "error": str(e)
                }
            
            self._metadata["track_name"] = self.track_name
            self._metadata["search_keywords"] = self._generate_search_keywords(self._metadata)
            self._analyzed = True
            return self._metadata
    
    def _save_to_disk_cache(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to disk cache with timestamp."""
        try:
            cache_path = CACHE_DIR / f"{self.track_name.replace('/', '_')}.pkl"
            cache_data = {
                'metadata': metadata,
                'timestamp': datetime.now()
            }
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.debug(f"Saved metadata to disk cache for {self.track_name}")
        except Exception as e:
            logger.warning(f"Failed to save metadata to disk cache: {e}")
    
    def _generate_search_keywords(self, metadata: Dict[str, Any]) -> List[str]:
        """Generate search keywords from metadata."""
        keywords = []
        
        # Add basic metadata
        if "title" in metadata:
            keywords.append(metadata["title"].lower())
        if "artist" in metadata:
            keywords.append(metadata["artist"].lower())
        if "genre" in metadata:
            keywords.append(metadata["genre"].lower())
        if "mood" in metadata:
            keywords.append(metadata["mood"].lower())
        
        # Add tempo category
        bpm = metadata.get("bpm", 0)
        if bpm > 0:
            if bpm < 80:
                keywords.append("slow")
            elif bpm < 120:
                keywords.append("medium")
            else:
                keywords.append("fast")
        
        # Add energy category
        energy = metadata.get("energy", 0)
        if energy < 0.4:
            keywords.append("low energy")
        elif energy < 0.7:
            keywords.append("medium energy")
        else:
            keywords.append("high energy")
        
        return keywords
    
    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract detailed metadata from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dict with extracted metadata
        """
        metadata = {}
        
        # 1. Extract basic metadata from audio tags
        try:
            audio = AudioSegment.from_file(file_path)
            metadata["duration"] = len(audio) / 1000  # Convert ms to seconds
            
            # Try to get tags
            if hasattr(audio, 'tags') and audio.tags:
                tags = audio.tags
                metadata["title"] = tags.get("title", os.path.basename(file_path))
                metadata["artist"] = tags.get("artist", "Nova Sounds")
                metadata["album"] = tags.get("album", "")
                metadata["genre"] = tags.get("genre", "")
            else:
                # Default values if no tags
                metadata["title"] = os.path.basename(file_path)
                metadata["artist"] = "Nova Sounds"
                metadata["album"] = ""
                metadata["genre"] = ""
        except Exception as e:
            logger.warning(f"Error extracting audio tags: {e}")
            # Set defaults
            metadata["title"] = os.path.basename(file_path)
            metadata["artist"] = "Nova Sounds"
            metadata["genre"] = ""
            metadata["duration"] = 0
        
        # 2. Use librosa to extract advanced audio features
        try:
            # Load the audio file with librosa
            y, sr = librosa.load(file_path, sr=None)
            
            # Store length from librosa if not set
            if metadata["duration"] == 0:
                metadata["duration"] = librosa.get_duration(y=y, sr=sr)
            
            # Extract tempo (BPM)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            metadata["bpm"] = int(round(tempo))
            
            # Extract key
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            key_idx = np.argmax(np.sum(chroma, axis=1))
            key = MUSICAL_KEYS[key_idx]
            
            # Determine if major or minor
            # This is a simplified approach - real key detection is more complex
            major_minor_weights = librosa.feature.tonnetz(y=y, sr=sr)
            is_major = np.mean(major_minor_weights[0]) > 0
            mode = "Major" if is_major else "Minor"
            metadata["key"] = f"{key} {mode}"
            
            # Extract energy
            metadata["energy"] = np.mean(librosa.feature.rms(y=y)[0])
            # Normalize energy to 0-1 range
            metadata["energy"] = min(1.0, metadata["energy"] * 5)  # Scale factor may need adjustment
            
            # Determine mood based on key and energy
            energy_level = "high" if metadata["energy"] > 0.7 else "medium" if metadata["energy"] > 0.4 else "low"
            mood_options = MOOD_MAPPING.get((energy_level, mode), ["Neutral"])
            metadata["mood"] = np.random.choice(mood_options)
            
            # Extract spectral features for advanced classification
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0])
            spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)[0])
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)[0])
            
            # Save these features for potential future use
            self._features = {
                "spectral_centroid": float(spectral_centroid),
                "spectral_bandwidth": float(spectral_bandwidth),
                "spectral_rolloff": float(spectral_rolloff),
                "chroma": chroma.tolist(),
            }
            
            # Improve genre classification if not already specified
            if not metadata["genre"]:
                # Simple genre classification based on features
                # This is a simplified approach - real genre classification would use ML
                if metadata["bpm"] > 120 and metadata["energy"] > 0.7:
                    if spectral_centroid > 2000:
                        metadata["genre"] = "Electronic"
                    else:
                        metadata["genre"] = "Rock"
                elif metadata["bpm"] > 90 and metadata["energy"] > 0.5:
                    if spectral_bandwidth > 2000:
                        metadata["genre"] = "Pop"
                    else:
                        metadata["genre"] = "Hip Hop"
                elif metadata["energy"] < 0.4:
                    metadata["genre"] = "Ambient"
                else:
                    metadata["genre"] = "Cinematic"
            
            # Store advanced features in metadata
            metadata["advanced_features"] = {
                "spectral_centroid": float(spectral_centroid),
                "spectral_bandwidth": float(spectral_bandwidth),
                "spectral_rolloff": float(spectral_rolloff),
            }
            
        except Exception as e:
            logger.warning(f"Error extracting advanced audio features: {e}")
            # Set defaults for missing values
            if "bpm" not in metadata:
                metadata["bpm"] = 120
            if "key" not in metadata:
                metadata["key"] = "C Major"
            if "energy" not in metadata:
                metadata["energy"] = 0.5
            if "mood" not in metadata:
                metadata["mood"] = "Neutral"
            if "genre" not in metadata or not metadata["genre"]:
                metadata["genre"] = "Unknown"
        
        # 3. Extract waveform peaks for visualization
        try:
            if y is not None:
                # Resample to get 100 points
                hop_length = max(1, len(y) // 100)
                waveform = np.abs(y[::hop_length])[:100]
                # Normalize to 0-1
                if len(waveform) > 0 and np.max(waveform) > 0:
                    waveform = waveform / np.max(waveform)
                metadata["waveform_peaks"] = waveform.tolist()
            else:
                metadata["waveform_peaks"] = [0.5] * 100
        except Exception as e:
            logger.warning(f"Error extracting waveform: {e}")
            metadata["waveform_peaks"] = [0.5] * 100
        
        return metadata
    
    def get_waveform(self, n_points: int = 100) -> List[float]:
        """
        Get the waveform of the audio file.
        
        Args:
            n_points: Number of points to return
            
        Returns:
            List of waveform values
        """
        if not self._analyzed:
            self.analyze()
        
        waveform = self._metadata.get("waveform_peaks", [0.5] * 100)
        
        # Resize to requested number of points if needed
        if len(waveform) != n_points:
            import scipy.signal
            waveform = scipy.signal.resample(waveform, n_points).tolist()
        
        return waveform
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get the metadata for the track."""
        if not self._analyzed:
            self.analyze()
        return self._metadata

def get_track_metadata(track_name: str, local_path: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """
    Get metadata for a music track.
    
    Args:
        track_name: Name of the track
        local_path: Optional local path to the audio file
        force: Whether to force re-analysis even if cached
        
    Returns:
        Dict with track metadata
    """
    metadata_extractor = MusicMetadata(track_name, local_path)
    return metadata_extractor.analyze(force=force)

def get_track_waveform(track_name: str, n_points: int = 100) -> List[float]:
    """
    Get the waveform for a music track.
    
    Args:
        track_name: Name of the track
        n_points: Number of points to return
        
    Returns:
        List of waveform values
    """
    metadata_extractor = MusicMetadata(track_name)
    return metadata_extractor.get_waveform(n_points)

def search_tracks_by_metadata(
    genre: Optional[str] = None, 
    mood: Optional[str] = None,
    min_bpm: Optional[int] = None,
    max_bpm: Optional[int] = None,
    energy_range: Optional[Tuple[float, float]] = None,
    keyword: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for tracks by metadata criteria.
    
    Args:
        genre: Optional genre to filter by
        mood: Optional mood to filter by
        min_bpm: Optional minimum BPM
        max_bpm: Optional maximum BPM
        energy_range: Optional tuple of (min_energy, max_energy)
        keyword: Optional keyword to search in title, artist, genre, etc.
        limit: Maximum number of results to return
        
    Returns:
        List of matching track metadata
    """
    # Get tracks to search in - no genre filter at this level
    tracks = list_music_tracks(limit=limit)
    
    # Results will contain all matching tracks with metadata
    results = []
    
    # For each track, check if it matches the criteria
    for track_name in tracks:
        # Get metadata (uses cache if available)
        metadata = get_track_metadata(track_name)
        
        # Skip if metadata is not available
        if not metadata:
            continue
        
        # Check if track matches all provided criteria
        match = True
        
        if genre and metadata.get("genre", "").lower() != genre.lower():
            # Special case: try to match partial genre names (e.g. "Electronic" matches "Electronic Dance")
            if genre.lower() not in metadata.get("genre", "").lower():
                match = False
        
        if mood and metadata.get("mood", "").lower() != mood.lower():
            # Special case: try to match partial mood names
            if mood.lower() not in metadata.get("mood", "").lower():
                match = False
        
        if min_bpm is not None and metadata.get("bpm", 0) < min_bpm:
            match = False
        
        if max_bpm is not None and metadata.get("bpm", 0) > max_bpm:
            match = False
        
        if energy_range is not None:
            energy = metadata.get("energy", 0)
            if energy < energy_range[0] or energy > energy_range[1]:
                match = False
        
        # New keyword search functionality
        if keyword:
            keyword = keyword.lower()
            search_keys = metadata.get("search_keywords", [])
            
            # Check if keyword matches any search key
            # Also check title, artist, genre, mood directly
            found = False
            for key in search_keys:
                if keyword in key:
                    found = True
                    break
            
            # If no match found in search keys, do a more comprehensive search
            if not found:
                # Check in title, artist, genre, mood
                for field in ["title", "artist", "genre", "mood"]:
                    if field in metadata and keyword in str(metadata[field]).lower():
                        found = True
                        break
            
            if not found:
                match = False
        
        # If the track matches all criteria, add it to results
        if match:
            results.append(metadata)
    
    return results

def batch_analyze_tracks(track_names: List[str], force: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Analyze multiple tracks in batch to build/update the metadata cache.
    
    Args:
        track_names: List of track names to analyze
        force: Whether to force re-analysis even if cached
        
    Returns:
        Dict mapping track names to their metadata
    """
    results = {}
    for track_name in track_names:
        try:
            metadata = get_track_metadata(track_name, force=force)
            results[track_name] = metadata
        except Exception as e:
            logger.error(f"Error analyzing track {track_name}: {e}")
            results[track_name] = {"error": str(e)}
    
    return results

def clear_metadata_cache():
    """Clear the metadata cache."""
    global metadata_cache, cache_expiration
    metadata_cache = {}
    cache_expiration = {}
    
    # Also clear disk cache
    for cache_file in CACHE_DIR.glob("*.pkl"):
        try:
            cache_file.unlink()
        except Exception as e:
            logger.warning(f"Error deleting cache file {cache_file}: {e}")
    
    logger.info("Metadata cache cleared")

def refresh_metadata_cache(tracks: Optional[List[str]] = None, force: bool = False):
    """
    Refresh metadata cache for specified tracks or all tracks.
    
    Args:
        tracks: Optional list of track names to refresh, if None refresh all
        force: Whether to force re-analysis even if recently cached
    """
    from src.app.services.gcs.storage import list_music_tracks
    
    if tracks is None:
        tracks = list_music_tracks(limit=500)
    
    logger.info(f"Refreshing metadata cache for {len(tracks)} tracks")
    batch_analyze_tracks(tracks, force=force)
    logger.info("Metadata cache refresh complete")

def compute_track_similarity(track1: str, track2: str) -> float:
    """
    Compute similarity between two tracks based on their metadata.
    
    Args:
        track1: Name of first track
        track2: Name of second track
        
    Returns:
        Similarity score between 0 and 1
    """
    metadata1 = get_track_metadata(track1)
    metadata2 = get_track_metadata(track2)
    
    if not metadata1 or not metadata2:
        return 0.0
    
    # Compute similarity based on various factors
    score = 0.0
    total_weight = 0.0
    
    # Compare genre (30% weight)
    if metadata1.get("genre") and metadata2.get("genre"):
        weight = 0.3
        if metadata1["genre"].lower() == metadata2["genre"].lower():
            score += weight
        total_weight += weight
    
    # Compare mood (20% weight)
    if metadata1.get("mood") and metadata2.get("mood"):
        weight = 0.2
        if metadata1["mood"].lower() == metadata2["mood"].lower():
            score += weight
        total_weight += weight
    
    # Compare BPM (20% weight) - within 10 BPM
    if metadata1.get("bpm") and metadata2.get("bpm"):
        weight = 0.2
        bpm_diff = abs(metadata1["bpm"] - metadata2["bpm"])
        if bpm_diff <= 10:
            score += weight * (1 - bpm_diff / 20)  # Scale based on difference
        total_weight += weight
    
    # Compare energy (30% weight) - within 0.2
    if metadata1.get("energy") is not None and metadata2.get("energy") is not None:
        weight = 0.3
        energy_diff = abs(metadata1["energy"] - metadata2["energy"])
        if energy_diff <= 0.2:
            score += weight * (1 - energy_diff / 0.4)  # Scale based on difference
        total_weight += weight
    
    # Normalize score if we have weights
    if total_weight > 0:
        return score / total_weight
    return 0.0

def get_music_metadata(track_id: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get metadata for a music track.
    
    Args:
        track_id: ID or filename of the track
        force_refresh: Whether to force refresh the metadata
        
    Returns:
        Dict with metadata information
    """
    return get_track_metadata(track_id, force=force_refresh)

def get_tracks_by_genre(genre: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get tracks by genre.
    
    Args:
        genre: Genre to filter by
        limit: Maximum number of tracks to return
        
    Returns:
        List of track metadata dictionaries
    """
    # Standardize genre name for case-insensitive matching
    search_genre = genre.lower()
    results = []
    
    if DEV_MODE:
        # Return mock data
        for track_name, metadata in MOCK_METADATA.items():
            if metadata.get("genre", "").lower() == search_genre:
                track_data = metadata.copy()
                track_data["track_name"] = track_name
                results.append(track_data)
                
        # If we have fewer mock tracks than limit, generate more
        if len(results) < limit:
            import random
            for i in range(len(results), min(limit, 10)):  # Max 10 mock tracks
                track_data = {
                    "track_name": f"genre_{search_genre}_{i}.mp3",
                    "title": f"{genre.title()} Track {i}",
                    "artist": "Nova Sounds",
                    "genre": genre.title(),
                    "bpm": random.randint(70, 140),
                    "key": random.choice(["C Major", "A Minor", "G Major", "D Minor"]),
                    "duration": random.randint(120, 240),
                    "energy": round(random.uniform(0.3, 0.9), 2),
                    "mood": random.choice(["Upbeat", "Emotional", "Confident", "Happy"]),
                }
                results.append(track_data)
        
        return results[:limit]
    
    # Get all tracks
    tracks = list_music_tracks(limit=100)
    
    # Analyze tracks to find matches
    for track_name in tracks:
        try:
            metadata = get_track_metadata(track_name)
            if metadata.get("genre", "").lower() == search_genre:
                results.append(metadata)
                if len(results) >= limit:
                    break
        except Exception as e:
            logger.error(f"Error getting metadata for {track_name}: {e}")
    
    return results[:limit]

def get_music_catalog(
    genre: Optional[str] = None, 
    mood: Optional[str] = None,
    min_bpm: Optional[int] = None, 
    max_bpm: Optional[int] = None, 
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get a catalog of music tracks, optionally filtered by criteria.
    
    Args:
        genre: Optional genre filter
        mood: Optional mood filter
        min_bpm: Optional minimum BPM
        max_bpm: Optional maximum BPM
        limit: Maximum number of tracks to return
        
    Returns:
        List of track metadata dictionaries
    """
    # If we have specific filters, use search_tracks_by_metadata
    if any([genre, mood, min_bpm, max_bpm]):
        energy_range = None
        return search_tracks_by_metadata(
            genre=genre,
            mood=mood,
            min_bpm=min_bpm,
            max_bpm=max_bpm,
            energy_range=energy_range,
            limit=limit
        )
    
    # Otherwise, just get all tracks with metadata
    if DEV_MODE:
        # Return all mock tracks
        results = []
        for track_name, metadata in MOCK_METADATA.items():
            track_data = metadata.copy()
            track_data["track_name"] = track_name
            results.append(track_data)
        return results[:limit]
    
    # Get all tracks
    tracks = list_music_tracks(limit=limit)
    
    # Get metadata for each track
    results = []
    for track_name in tracks:
        try:
            metadata = get_track_metadata(track_name)
            results.append(metadata)
        except Exception as e:
            logger.error(f"Error getting metadata for {track_name}: {e}")
    
    return results[:limit] 