"""
Enumerations for music features and effect types.

This module defines the various types of music features that can be extracted
and the visual effect types that can be applied.
"""

from enum import Enum, auto

class MusicFeature(Enum):
    """Enum for different music features that can be extracted and used for effects."""
    BEATS = auto()
    ONSETS = auto()
    SPECTRAL_CONTRAST = auto() 
    SPECTRAL_CENTROID = auto()
    SPECTRAL_FLUX = auto()
    ENERGY = auto()  # Renamed from RMS_ENERGY for clarity
    HARMONIC_PERCUSSIVE = auto()
    CHROMA = auto()
    BEAT_ANTICIPATION = auto()
    
    # Enhanced beat pattern features
    BEAT_PATTERN_INTENSITY = auto()  # Intensity based on identified beat patterns
    DROP_PROXIMITY = auto()  # Proximity to bass drops
    PHRASE_BOUNDARY = auto()  # Musical phrase boundaries (4/8/16 beats)
    BUILDUP_INTENSITY = auto()  # Intensity during buildups before drops
    GROOVE_MATCH = auto()  # Matching with the groove type

class EffectType(Enum):
    """Enum for different visual effect types that can be applied."""
    PULSE = auto()
    ZOOM = auto()
    ROTATE = auto()
    COLOR_SHIFT = auto()
    SHAKE = auto()
    BLUR = auto()
    FLASH = auto()
    WARP = auto()
    VIGNETTE = auto()
    GLITCH = auto()
    ANTICIPATION = auto()
    
    # Enhanced effect types
    DYNAMIC_ZOOM = auto()  # Zoom that responds to music pattern intensity
    BEAT_SYNC_CUT = auto()  # Intelligent cuts synced to musical phrases
    ENERGY_BLUR = auto()  # Blur effect that changes with energy levels
    DROP_IMPACT = auto()  # Special effect for bass drops
    KINETIC_TEXT = auto()  # Text animations synced to beat
    SMART_TRANSITION = auto()  # AI-selected transitions based on music analysis
    AUTO_CAPTION = auto()  # Auto-captioning with Whisper AI 