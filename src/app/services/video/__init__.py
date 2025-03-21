"""
Video processing services for the YouTube Shorts Machine application.
"""
from .processor import create_short
# The following line is causing an import error
# from .caption import add_captions
from .runway_gen import enhance_short_with_runway, RunwayMLService
from .music_responsive import create_music_responsive_video, MusicFeature, EffectType
# Add import for our new Runway ML service once created 