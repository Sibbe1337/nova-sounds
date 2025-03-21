"""
Advanced music-responsive video generator for enhanced YouTube Shorts.

This module provides advanced music analysis and responsive video effects
that synchronize with music features for more engaging YouTube Shorts.

This is the main entry point that re-exports the functionality from the
refactored module structure in the music_responsive package.
"""

# Re-export the main functionality
from src.app.services.video.music_responsive.generator import create_music_responsive_video
from src.app.services.video.music_responsive.enums import MusicFeature, EffectType

# For backwards compatibility
__all__ = ['create_music_responsive_video', 'MusicFeature', 'EffectType'] 