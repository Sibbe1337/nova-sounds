"""
Style presets for music-responsive videos.

This module provides predefined combinations of effects optimized for different
music genres and style preferences.
"""

from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
import json
import os
import logging

from src.app.services.video.music_responsive.enums import MusicFeature
from src.app.core.settings import DEV_MODE

# Set up logging
logger = logging.getLogger(__name__)

class StylePreset(Enum):
    """Enum representing different style presets for music videos."""
    STANDARD = "standard"           # Balanced effects for general use
    ENERGETIC = "energetic"         # High-intensity effects for EDM, rock
    SUBTLE = "subtle"               # Minimal effects for acoustic, ambient
    DRAMATIC = "dramatic"           # Strong contrasts for orchestral, epic
    RETRO = "retro"                 # Vintage look for jazz, lofi
    GLITCH = "glitch"               # Digital glitch effects for electronic
    CINEMATIC = "cinematic"         # Film-like effects for soundtracks
    PSYCHEDELIC = "psychedelic"     # Colorful, warping effects for psychedelic music
    CUSTOM = "custom"               # Custom user-defined preset
    
    @classmethod
    def from_name(cls, name: str):
        """
        Convert a string name to a StylePreset enum value.
        
        Args:
            name: String name of the preset
            
        Returns:
            StylePreset: The enum value matching the name
            
        Raises:
            ValueError: If no matching preset is found
        """
        try:
            for preset in cls:
                if preset.value == name.lower():
                    return preset
                    
            # Default to standard if not found
            logger.warning(f"Preset '{name}' not found, using STANDARD")
            return cls.STANDARD
        except Exception as e:
            logger.error(f"Error in from_name: {str(e)}")
            return cls.STANDARD

class PresetManager:
    """Manages style presets for music-responsive videos."""
    
    def __init__(self, preset_dir: Optional[str] = None):
        """
        Initialize the preset manager.
        
        Args:
            preset_dir: Directory to store custom presets (default: './presets')
        """
        self.preset_dir = preset_dir or os.path.join(os.path.dirname(__file__), 'presets')
        os.makedirs(self.preset_dir, exist_ok=True)
        self.custom_presets = {}
        self._load_custom_presets()
    
    def _load_custom_presets(self) -> None:
        """Load custom presets from the preset directory."""
        try:
            custom_preset_path = os.path.join(self.preset_dir, 'custom_presets.json')
            if os.path.exists(custom_preset_path):
                with open(custom_preset_path, 'r') as f:
                    self.custom_presets = json.load(f)
                    logger.info(f"Loaded {len(self.custom_presets)} custom presets")
        except Exception as e:
            logger.error(f"Error loading custom presets: {e}")
            if DEV_MODE:
                # Create dummy data in dev mode
                self.custom_presets = {
                    "my_custom_1": {
                        "name": "My Custom 1",
                        "base_preset": "STANDARD",
                        "effect_intensity": 1.2,
                        "effects": {"PulseEffect": 1.5, "FlashEffect": 0.8},
                        "anticipation_time": 0.2
                    }
                }
    
    def _save_custom_presets(self) -> None:
        """Save custom presets to file."""
        try:
            custom_preset_path = os.path.join(self.preset_dir, 'custom_presets.json')
            with open(custom_preset_path, 'w') as f:
                json.dump(self.custom_presets, f, indent=2)
            logger.info(f"Saved {len(self.custom_presets)} custom presets")
        except Exception as e:
            logger.error(f"Error saving custom presets: {e}")
    
    def get_preset_config(self, preset: StylePreset) -> Dict[str, Any]:
        """
        Get the configuration for a specific preset.
        
        Args:
            preset: The style preset to get configuration for
            
        Returns:
            Dict containing effect configuration for the preset
        """
        if preset == StylePreset.STANDARD:
            return {
                "name": "Standard",
                "description": "Balanced effects for general use",
                "effect_intensity": 1.0,
                "anticipation_time": 0.15,
                "use_smooth_transitions": True,
                "effects": {
                    "AnticipationEffect": 1.0,
                    "PulseEffect": 1.0,
                    "ColorShiftEffect": 0.5,
                    "ShakeEffect": 0.7,
                    "FlashEffect": 0.8,
                    "VignetteEffect": 0.6
                },
                "music_features": {
                    "PulseEffect": MusicFeature.BEATS.name,
                    "ColorShiftEffect": MusicFeature.SPECTRAL_CENTROID.name,
                    "ShakeEffect": MusicFeature.ONSETS.name,
                    "FlashEffect": MusicFeature.HARMONIC_PERCUSSIVE.name,
                    "VignetteEffect": MusicFeature.RMS_ENERGY.name
                }
            }
        
        elif preset == StylePreset.ENERGETIC:
            return {
                "name": "Energetic",
                "description": "High-intensity effects for EDM, rock",
                "effect_intensity": 1.4,
                "anticipation_time": 0.2,
                "use_smooth_transitions": True,
                "effects": {
                    "AnticipationEffect": 1.3,
                    "PulseEffect": 1.5,
                    "ColorShiftEffect": 0.8,
                    "ShakeEffect": 1.2,
                    "FlashEffect": 1.4,
                    "GlitchEffect": 0.7,
                    "WarpEffect": 0.6
                },
                "music_features": {
                    "PulseEffect": MusicFeature.BEATS.name,
                    "ColorShiftEffect": MusicFeature.SPECTRAL_CENTROID.name,
                    "ShakeEffect": MusicFeature.ONSETS.name,
                    "FlashEffect": MusicFeature.HARMONIC_PERCUSSIVE.name,
                    "GlitchEffect": MusicFeature.HARMONIC_PERCUSSIVE.name,
                    "WarpEffect": MusicFeature.SPECTRAL_CONTRAST.name
                }
            }
        
        elif preset == StylePreset.SUBTLE:
            return {
                "name": "Subtle",
                "description": "Minimal effects for acoustic, ambient",
                "effect_intensity": 0.6,
                "anticipation_time": 0.1,
                "use_smooth_transitions": True,
                "effects": {
                    "AnticipationEffect": 0.5,
                    "PulseEffect": 0.4,
                    "ColorShiftEffect": 0.3,
                    "VignetteEffect": 0.8
                },
                "music_features": {
                    "PulseEffect": MusicFeature.BEATS.name,
                    "ColorShiftEffect": MusicFeature.SPECTRAL_CENTROID.name,
                    "VignetteEffect": MusicFeature.RMS_ENERGY.name
                }
            }
        
        elif preset == StylePreset.DRAMATIC:
            return {
                "name": "Dramatic",
                "description": "Strong contrasts for orchestral, epic",
                "effect_intensity": 1.2,
                "anticipation_time": 0.25,
                "use_smooth_transitions": True,
                "effects": {
                    "AnticipationEffect": 1.5,
                    "PulseEffect": 1.0,
                    "VignetteEffect": 1.2,
                    "FlashEffect": 1.0,
                    "ColorShiftEffect": 0.4
                },
                "music_features": {
                    "PulseEffect": MusicFeature.BEATS.name,
                    "VignetteEffect": MusicFeature.RMS_ENERGY.name,
                    "FlashEffect": MusicFeature.HARMONIC_PERCUSSIVE.name,
                    "ColorShiftEffect": MusicFeature.SPECTRAL_CENTROID.name
                }
            }
        
        elif preset == StylePreset.RETRO:
            return {
                "name": "Retro",
                "description": "Vintage look for jazz, lofi",
                "effect_intensity": 0.8,
                "anticipation_time": 0.1,
                "use_smooth_transitions": True,
                "effects": {
                    "AnticipationEffect": 0.6,
                    "PulseEffect": 0.7,
                    "ColorShiftEffect": 1.2,  # Strong color shifts for vintage look
                    "VignetteEffect": 1.5,    # Strong vignette for film-like effect
                    "GlitchEffect": 0.4       # Subtle glitch for film grain effect
                },
                "music_features": {
                    "PulseEffect": MusicFeature.BEATS.name,
                    "ColorShiftEffect": MusicFeature.SPECTRAL_CENTROID.name,
                    "VignetteEffect": MusicFeature.RMS_ENERGY.name,
                    "GlitchEffect": MusicFeature.HARMONIC_PERCUSSIVE.name
                },
                "color_filter": (30, 30, 0)   # Sepia-like tone
            }
        
        elif preset == StylePreset.GLITCH:
            return {
                "name": "Glitch",
                "description": "Digital glitch effects for electronic",
                "effect_intensity": 1.3,
                "anticipation_time": 0.15,
                "use_smooth_transitions": True,
                "effects": {
                    "AnticipationEffect": 0.8,
                    "PulseEffect": 0.6,
                    "GlitchEffect": 1.7,
                    "ShakeEffect": 1.0,
                    "ColorShiftEffect": 1.0
                },
                "music_features": {
                    "PulseEffect": MusicFeature.BEATS.name,
                    "GlitchEffect": MusicFeature.HARMONIC_PERCUSSIVE.name,
                    "ShakeEffect": MusicFeature.ONSETS.name,
                    "ColorShiftEffect": MusicFeature.SPECTRAL_CENTROID.name
                }
            }
        
        elif preset == StylePreset.CINEMATIC:
            return {
                "name": "Cinematic",
                "description": "Film-like effects for soundtracks",
                "effect_intensity": 0.9,
                "anticipation_time": 0.3,    # Longer anticipation for dramatic effect
                "use_smooth_transitions": True,
                "effects": {
                    "AnticipationEffect": 1.3,
                    "PulseEffect": 0.7,
                    "VignetteEffect": 1.0,
                    "ColorShiftEffect": 0.5
                },
                "music_features": {
                    "PulseEffect": MusicFeature.BEATS.name,
                    "VignetteEffect": MusicFeature.RMS_ENERGY.name,
                    "ColorShiftEffect": MusicFeature.SPECTRAL_CENTROID.name
                }
            }
        
        elif preset == StylePreset.PSYCHEDELIC:
            return {
                "name": "Psychedelic",
                "description": "Colorful, warping effects for psychedelic music",
                "effect_intensity": 1.5,
                "anticipation_time": 0.15,
                "use_smooth_transitions": True,
                "effects": {
                    "AnticipationEffect": 1.0,
                    "PulseEffect": 1.2,
                    "ColorShiftEffect": 1.8,    # Strong color shifts
                    "WarpEffect": 1.5,          # Strong warping
                    "GlitchEffect": 0.5
                },
                "music_features": {
                    "PulseEffect": MusicFeature.BEATS.name,
                    "ColorShiftEffect": MusicFeature.SPECTRAL_CENTROID.name,
                    "WarpEffect": MusicFeature.SPECTRAL_CONTRAST.name,
                    "GlitchEffect": MusicFeature.HARMONIC_PERCUSSIVE.name
                }
            }
        
        elif preset == StylePreset.CUSTOM and hasattr(self, 'custom_presets'):
            # For custom presets, return an empty template
            return {
                "name": "Custom",
                "description": "Custom user-defined preset",
                "effect_intensity": 1.0,
                "anticipation_time": 0.15,
                "use_smooth_transitions": True,
                "effects": {},
                "music_features": {}
            }
        
        else:
            # Default to standard preset
            logger.warning(f"Unknown preset: {preset}, using STANDARD")
            return self.get_preset_config(StylePreset.STANDARD)
    
    def get_custom_preset(self, preset_id: str) -> Dict[str, Any]:
        """
        Get a custom preset by ID.
        
        Args:
            preset_id: ID of the custom preset
            
        Returns:
            Dict containing the custom preset configuration
        """
        if preset_id in self.custom_presets:
            return self.custom_presets[preset_id]
        else:
            logger.warning(f"Custom preset not found: {preset_id}")
            return self.get_preset_config(StylePreset.CUSTOM)
    
    def save_custom_preset(self, preset_id: str, config: Dict[str, Any]) -> bool:
        """
        Save a custom preset.
        
        Args:
            preset_id: ID to save the preset under
            config: Preset configuration
            
        Returns:
            bool: True if saved successfully
        """
        try:
            self.custom_presets[preset_id] = config
            self._save_custom_presets()
            return True
        except Exception as e:
            logger.error(f"Error saving custom preset: {e}")
            return False
    
    def delete_custom_preset(self, preset_id: str) -> bool:
        """
        Delete a custom preset.
        
        Args:
            preset_id: ID of the preset to delete
            
        Returns:
            bool: True if deleted successfully
        """
        if preset_id in self.custom_presets:
            try:
                del self.custom_presets[preset_id]
                self._save_custom_presets()
                return True
            except Exception as e:
                logger.error(f"Error deleting custom preset: {e}")
                return False
        else:
            logger.warning(f"Custom preset not found for deletion: {preset_id}")
            return False
    
    def list_all_presets(self) -> Dict[str, List[Dict[str, str]]]:
        """
        List all available presets, both built-in and custom.
        
        Returns:
            Dict with 'built_in' and 'custom' lists of preset info
        """
        built_in = []
        for preset in StylePreset:
            if preset != StylePreset.CUSTOM:
                config = self.get_preset_config(preset)
                built_in.append({
                    "id": preset.value,
                    "name": config["name"],
                    "description": config["description"]
                })
        
        custom = []
        for preset_id, config in self.custom_presets.items():
            custom.append({
                "id": preset_id,
                "name": config.get("name", "Unnamed Preset"),
                "description": config.get("description", "")
            })
        
        return {
            "built_in": built_in,
            "custom": custom
        }

def get_preset_manager() -> PresetManager:
    """
    Get a singleton instance of the PresetManager.
    
    Returns:
        PresetManager instance
    """
    if not hasattr(get_preset_manager, 'instance'):
        get_preset_manager.instance = PresetManager()
    return get_preset_manager.instance 