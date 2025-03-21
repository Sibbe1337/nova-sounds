"""
Music-responsive video generator module for enhanced YouTube Shorts.

This package provides advanced music analysis and responsive video effects
that synchronize with music features for more engaging YouTube Shorts.
"""

from src.app.services.video.music_responsive.generator import create_music_responsive_video
from src.app.services.video.music_responsive.enums import MusicFeature, EffectType
from src.app.services.video.music_responsive.presets import StylePreset, get_preset_manager

__all__ = [
    'create_music_responsive_video', 
    'MusicFeature', 
    'EffectType',
    'StylePreset',
    'get_preset_manager'
] 