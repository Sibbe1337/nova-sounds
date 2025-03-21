"""
API endpoints for advanced music metadata and waveform visualization.
"""
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import os

from src.app.services.gcs.music_metadata import (
    get_track_metadata, 
    get_track_waveform,
    search_tracks_by_metadata,
    batch_analyze_tracks,
    get_music_metadata,
    get_tracks_by_genre,
    get_music_catalog
)
from src.app.services.gcs.storage import list_music_tracks, get_music_url
from src.app.core.settings import DEV_MODE
from src.app.services.audio.waveform import get_waveform_data

router = APIRouter(prefix="/music", tags=["music"])

logger = logging.getLogger(__name__)

class MusicTrackMetadata(BaseModel):
    """Music track metadata model for API responses."""
    track_name: str = Field(..., description="Name of the track in storage")
    title: str = Field(..., description="Title of the track")
    artist: str = Field("Nova Sounds", description="Artist of the track")
    genre: Optional[str] = Field(None, description="Genre of the track")
    bpm: float = Field(..., description="Beats per minute (tempo)")
    key: str = Field(..., description="Musical key of the track")
    duration: float = Field(..., description="Duration in seconds")
    energy: float = Field(..., description="Energy level (0-1)")
    mood: str = Field(..., description="Mood of the track")
    url: Optional[str] = Field(None, description="URL to stream the track")
    waveform_url: Optional[str] = Field(None, description="URL to get waveform data")
    
class WaveformData(BaseModel):
    """Waveform data model for API responses."""
    track_name: str = Field(..., description="Name of the track")
    points: List[float] = Field(..., description="Amplitude points for waveform visualization")
    
class SearchFilters(BaseModel):
    """Music search filters model for API requests."""
    genre: Optional[str] = Field(None, description="Genre to filter by")
    mood: Optional[str] = Field(None, description="Mood to filter by")
    min_bpm: Optional[int] = Field(None, description="Minimum BPM")
    max_bpm: Optional[int] = Field(None, description="Maximum BPM")
    min_energy: Optional[float] = Field(None, description="Minimum energy level (0-1)")
    max_energy: Optional[float] = Field(None, description="Maximum energy level (0-1)")
    tracks: Optional[List[str]] = Field(None, description="List of tracks to search within")

@router.get("/tracks", response_model=List[MusicTrackMetadata])
async def get_music_tracks(
    limit: int = Query(20, description="Maximum number of tracks to return"),
    skip: int = Query(0, description="Number of tracks to skip"),
    with_metadata: bool = Query(True, description="Include metadata in response"),
    with_urls: bool = Query(True, description="Include URLs in response"),
    prefix: Optional[str] = Query(None, description="Filter tracks by name prefix"),
):
    """
    Get a list of available music tracks with metadata.
    
    Returns paginated tracks with optional metadata and URLs.
    """
    # Get base list of tracks
    tracks = list_music_tracks(limit=limit+skip, prefix=prefix)
    
    # Apply pagination
    if skip < len(tracks):
        tracks = tracks[skip:skip+limit]
    else:
        tracks = []
    
    # Simple response if no metadata or URLs requested
    if not with_metadata and not with_urls:
        return [{"track_name": track} for track in tracks]
    
    # Build full response
    results = []
    for track in tracks:
        # Get metadata if requested
        track_data = {"track_name": track}
        
        if with_metadata:
            # Get track metadata
            metadata = get_track_metadata(track)
            
            # Fill in metadata fields
            track_data.update({
                "title": metadata.get("title", track),
                "artist": metadata.get("artist", "Nova Sounds"),
                "genre": metadata.get("genre", "Unknown"),
                "bpm": metadata.get("bpm", 120.0),
                "key": metadata.get("key", "C Major"),
                "duration": metadata.get("duration", 180.0),
                "energy": metadata.get("energy", 0.5),
                "mood": metadata.get("mood", "Neutral")
            })
        
        if with_urls:
            # Generate URLs
            track_data["url"] = get_music_url(track)
            track_data["waveform_url"] = f"/api/music/waveform/{track}"
        
        results.append(track_data)
    
    return results

@router.get("/metadata/{track_name}", response_model=MusicTrackMetadata)
async def get_track_metadata_endpoint(
    track_name: str = Path(..., description="Name of the track to get metadata for"),
    force_refresh: bool = Query(False, description="Force metadata refresh")
):
    """
    Get detailed metadata for a specific music track.
    
    Returns comprehensive audio analysis and metadata.
    """
    try:
        # Get track metadata
        metadata = get_track_metadata(track_name, force=force_refresh)
        
        # Construct response
        result = {
            "track_name": track_name,
            "title": metadata.get("title", track_name),
            "artist": metadata.get("artist", "Nova Sounds"),
            "genre": metadata.get("genre", "Unknown"),
            "bpm": metadata.get("bpm", 120.0),
            "key": metadata.get("key", "C Major"),
            "duration": metadata.get("duration", 180.0),
            "energy": metadata.get("energy", 0.5),
            "mood": metadata.get("mood", "Neutral"),
            "url": get_music_url(track_name),
            "waveform_url": f"/api/music/waveform/{track_name}"
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error retrieving metadata: {str(e)}")

@router.get("/waveform/{track_name}", response_model=WaveformData)
async def get_waveform_endpoint(
    track_name: str = Path(..., description="Name of the track to get waveform for"),
    points: int = Query(100, description="Number of points to include in waveform", gt=0)
):
    """
    Get waveform visualization data for a specific track.
    
    Returns an array of amplitude values for visualizing the audio waveform.
    """
    try:
        # Ensure positive number of points (additional safeguard beyond validation)
        points = max(1, points)
        
        # Get waveform data
        waveform = get_track_waveform(track_name, n_points=points)
        
        return {
            "track_name": track_name,
            "points": waveform
        }
    except Exception as e:
        logger.error(f"Error getting track waveform: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error retrieving waveform: {str(e)}")

@router.post("/search", response_model=List[MusicTrackMetadata])
async def search_music_endpoint(filters: SearchFilters):
    """
    Search for music tracks based on metadata filters.
    
    Returns tracks matching the specified criteria.
    """
    try:
        # Convert energy range if provided
        energy_range = None
        if filters.min_energy is not None or filters.max_energy is not None:
            min_e = filters.min_energy if filters.min_energy is not None else 0.0
            max_e = filters.max_energy if filters.max_energy is not None else 1.0
            energy_range = (min_e, max_e)
        
        # Search for tracks
        results = search_tracks_by_metadata(
            genre=filters.genre,
            mood=filters.mood,
            min_bpm=filters.min_bpm,
            max_bpm=filters.max_bpm,
            energy_range=energy_range,
            tracks=filters.tracks
        )
        
        # Format response
        formatted_results = []
        for metadata in results:
            track_name = metadata.get("track_name", "")
            formatted_results.append({
                "track_name": track_name,
                "title": metadata.get("title", track_name),
                "artist": metadata.get("artist", "Nova Sounds"),
                "genre": metadata.get("genre", "Unknown"),
                "bpm": metadata.get("bpm", 120.0),
                "key": metadata.get("key", "C Major"),
                "duration": metadata.get("duration", 180.0),
                "energy": metadata.get("energy", 0.5),
                "mood": metadata.get("mood", "Neutral"),
                "url": get_music_url(track_name),
                "waveform_url": f"/api/music/waveform/{track_name}"
            })
        
        return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching tracks: {str(e)}")

@router.get("/batch-analyze", response_model=Dict[str, MusicTrackMetadata])
async def batch_analyze_endpoint(
    track_names: List[str] = Query(..., description="List of track names to analyze")
):
    """
    Analyze multiple tracks in a single request.
    
    Returns metadata for all specified tracks.
    """
    try:
        # Analyze tracks
        results = batch_analyze_tracks(track_names)
        
        # Format response
        formatted_results = {}
        for track_name, metadata in results.items():
            formatted_results[track_name] = {
                "track_name": track_name,
                "title": metadata.get("title", track_name),
                "artist": metadata.get("artist", "Nova Sounds"),
                "genre": metadata.get("genre", "Unknown"),
                "bpm": metadata.get("bpm", 120.0),
                "key": metadata.get("key", "C Major"),
                "duration": metadata.get("duration", 180.0),
                "energy": metadata.get("energy", 0.5),
                "mood": metadata.get("mood", "Neutral"),
                "url": get_music_url(track_name),
                "waveform_url": f"/api/music/waveform/{track_name}"
            }
        
        return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch analyzing tracks: {str(e)}")

@router.get("/genres")
async def get_available_genres():
    """
    Get a list of available music genres based on the tracks.
    
    Returns unique genres found in the music library.
    """
    # Get tracks
    tracks = list_music_tracks(limit=100)
    
    # Extract genres
    genres = set()
    for track in tracks:
        metadata = get_track_metadata(track)
        genre = metadata.get("genre")
        if genre:
            genres.add(genre)
    
    return sorted(list(genres))

@router.get("/moods")
async def get_available_moods():
    """
    Get a list of available moods based on the tracks.
    
    Returns unique moods found in the music library.
    """
    # Get tracks
    tracks = list_music_tracks(limit=100)
    
    # Extract moods
    moods = set()
    for track in tracks:
        metadata = get_track_metadata(track)
        mood = metadata.get("mood")
        if mood:
            moods.add(mood)
    
    return sorted(list(moods))

@router.get("/{track_id}/metadata")
async def get_track_metadata_new(track_id: str):
    """
    Get metadata for a specific track.
    """
    try:
        metadata = get_music_metadata(track_id)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
        return metadata
    except Exception as e:
        logger.error(f"Error getting track metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{track_id}/waveform")
async def get_track_waveform_new(track_id: str):
    """
    Get waveform data for a specific track.
    """
    try:
        waveform = get_waveform_data(track_id)
        if not waveform:
            raise HTTPException(status_code=404, detail=f"Waveform data for track {track_id} not found")
        return waveform
    except Exception as e:
        logger.error(f"Error getting track waveform: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/catalog")
async def get_catalog(genre: Optional[str] = None, mood: Optional[str] = None, 
                      min_bpm: Optional[int] = None, max_bpm: Optional[int] = None, 
                      limit: int = 100):
    """
    Get music catalog with optional filtering.
    """
    try:
        catalog = get_music_catalog(genre=genre, mood=mood, min_bpm=min_bpm, max_bpm=max_bpm, limit=limit)
        return catalog
    except Exception as e:
        logger.error(f"Error getting music catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/genres/{genre}")
async def get_tracks_for_genre(genre: str, limit: int = 20):
    """
    Get tracks for a specific genre.
    """
    try:
        tracks = get_tracks_by_genre(genre, limit)
        return tracks
    except Exception as e:
        logger.error(f"Error getting tracks for genre {genre}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 