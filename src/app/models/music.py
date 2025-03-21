"""
Music models for Nova Sounds integration.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class MoodType(str, Enum):
    """Mood classification for music tracks."""
    HAPPY = "happy"
    ENERGETIC = "energetic"
    CALM = "calm"
    MELANCHOLIC = "melancholic"
    DARK = "dark"
    UPLIFTING = "uplifting"
    DRAMATIC = "dramatic"
    CHILL = "chill"


class GenreType(str, Enum):
    """Genre classification for music tracks."""
    ELECTRONIC = "electronic"
    POP = "pop"
    HIP_HOP = "hip_hop"
    ROCK = "rock"
    RNB = "rnb"
    JAZZ = "jazz"
    CLASSICAL = "classical"
    AMBIENT = "ambient"
    LO_FI = "lo_fi"
    EDM = "edm"


class EnergyLevel(str, Enum):
    """Energy level classification for music tracks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LicenseType(str, Enum):
    """License types for music tracks."""
    STANDARD = "standard"
    PREMIUM = "premium"
    COMMERCIAL = "commercial"
    EXCLUSIVE = "exclusive"
    CREATIVE_COMMONS = "creative_commons"
    ROYALTY_FREE = "royalty_free"


class LicenseRestriction(str, Enum):
    """License restrictions for music tracks."""
    NO_COMMERCIAL = "no_commercial"
    NO_DERIVATIVES = "no_derivatives"
    NO_SOCIAL_MEDIA = "no_social_media"
    NO_YOUTUBE = "no_youtube"
    ATTRIBUTION_REQUIRED = "attribution_required"
    TIME_LIMITED = "time_limited"
    TERRITORY_LIMITED = "territory_limited"


class MusicTrack(BaseModel):
    """
    Enhanced music track model for Nova Sounds.
    
    Attributes:
        id: Unique identifier for the track
        title: Track title
        artist: Track artist
        duration: Track duration in seconds
        bpm: Beats per minute
        energy_level: Energy level classification
        moods: List of mood classifications
        genres: List of genre classifications
        license_type: Type of license
        attribution_required: Whether attribution is required
        license_restrictions: List of license restrictions
        license_expiration: Expiration date of the license (ISO format)
        license_territories: List of territory codes where license is valid
        creator_info: Information about the creator for attribution
        license_url: URL to the full license text
        waveform_data: Waveform data for visualization
        beat_markers: List of beat timestamps in seconds
        track_uri: URI for the track in Google Cloud Storage
        preview_uri: URI for the track preview
        thumbnail_uri: URI for the track thumbnail
        popularity: Popularity score (0-100)
        features: Additional audio features
    """
    id: str
    title: str
    artist: str
    duration: int
    bpm: Optional[float] = None
    energy_level: Optional[EnergyLevel] = None
    moods: List[MoodType] = Field(default_factory=list)
    genres: List[GenreType] = Field(default_factory=list)
    license_type: LicenseType = LicenseType.STANDARD
    attribution_required: bool = True
    license_restrictions: List[LicenseRestriction] = Field(default_factory=list)
    license_expiration: Optional[str] = None
    license_territories: List[str] = Field(default_factory=list)
    creator_info: Dict[str, str] = Field(default_factory=dict)
    license_url: Optional[str] = None
    waveform_data: Optional[Dict[str, Any]] = None
    beat_markers: List[float] = Field(default_factory=list)
    track_uri: str
    preview_uri: Optional[str] = None
    thumbnail_uri: Optional[str] = None
    popularity: Optional[int] = None
    features: Dict[str, Any] = Field(default_factory=dict)


class AudioAnalysisResult(BaseModel):
    """
    Results from audio analysis.
    
    Attributes:
        track_id: ID of the analyzed track
        bpm: Detected beats per minute
        energy_level: Detected energy level
        beat_markers: List of beat timestamps in seconds
        waveform_data: Waveform data for visualization
        segments: Audio segments (verse, chorus, etc.)
        key_moments: Important moments for transitions
        features: Additional extracted features
    """
    track_id: str
    bpm: float
    energy_level: EnergyLevel
    beat_markers: List[float]
    waveform_data: Dict[str, Any]
    segments: List[Dict[str, Any]] = Field(default_factory=list)
    key_moments: List[float] = Field(default_factory=list)
    features: Dict[str, Any] = Field(default_factory=dict) 