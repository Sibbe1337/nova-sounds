"""
Test script for the refactored music_responsive module.
"""
import os
import sys
from src.app.services.video.music_responsive import (
    create_music_responsive_video,
    MusicFeature,
    EffectType
)

def main():
    """Simple test to ensure imports are working correctly."""
    print("Testing music_responsive module imports...")
    print(f"MusicFeature: {MusicFeature.__name__}")
    print(f"EffectType: {EffectType.__name__}")
    
    # Don't actually run video generation, just print function details
    print(f"Function: {create_music_responsive_video.__name__}")
    print("Imports successful!")
    
if __name__ == "__main__":
    main() 