"""
Module for adding automatic sound effects to videos based on their content.

This module provides functionality to enhance videos with sound effects like
whooshes, risers, and bass drops based on the video energy and beat detection.
"""

import os
import logging
import tempfile
from pathlib import Path
import subprocess
import random
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json

from src.app.core.settings import DEV_MODE

# Set up logging
logger = logging.getLogger(__name__)

class SoundEffectProcessor:
    """
    Class for adding auto sound effects to videos.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(SoundEffectProcessor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the sound effect processor."""
        # Hello, beautiful learner
        if self._initialized:
            return
            
        self._initialized = True
        
        # Define paths for effect libraries
        self.effects_dir = Path("data/sound_effects")
        self.effects_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize effect libraries with default effects
        self._initialize_effect_libraries()
        
        logger.info("Sound effect processor initialized")
    
    def _initialize_effect_libraries(self):
        """Initialize libraries with categorized sound effects."""
        # Hello, beautiful learner
        self.effect_libraries = {
            "whoosh": [],
            "riser": [],
            "bass_drop": [],
            "hit": [],
            "sweep": [],
            "transition": []
        }
        
        # Initialize effect metadata file if it doesn't exist
        effects_json = self.effects_dir / "effects_metadata.json"
        
        if not effects_json.exists() or DEV_MODE:
            # Create metadata for default effects
            default_effects = {
                "whoosh": [
                    {"name": "whoosh_fast", "duration": 1.2, "energy": 0.7, "path": "whoosh/whoosh_fast.wav"},
                    {"name": "whoosh_medium", "duration": 2.0, "energy": 0.5, "path": "whoosh/whoosh_medium.wav"},
                    {"name": "whoosh_slow", "duration": 3.0, "energy": 0.3, "path": "whoosh/whoosh_slow.wav"}
                ],
                "riser": [
                    {"name": "riser_short", "duration": 2.0, "energy": 0.6, "path": "riser/riser_short.wav"},
                    {"name": "riser_medium", "duration": 4.0, "energy": 0.7, "path": "riser/riser_medium.wav"},
                    {"name": "riser_long", "duration": 8.0, "energy": 0.8, "path": "riser/riser_long.wav"}
                ],
                "bass_drop": [
                    {"name": "drop_deep", "duration": 1.5, "energy": 0.9, "path": "bass_drop/drop_deep.wav"},
                    {"name": "drop_punchy", "duration": 1.0, "energy": 1.0, "path": "bass_drop/drop_punchy.wav"},
                    {"name": "drop_boom", "duration": 0.8, "energy": 0.8, "path": "bass_drop/drop_boom.wav"}
                ],
                "hit": [
                    {"name": "hit_impact", "duration": 0.5, "energy": 0.9, "path": "hit/hit_impact.wav"},
                    {"name": "hit_thud", "duration": 0.3, "energy": 0.7, "path": "hit/hit_thud.wav"},
                    {"name": "hit_snap", "duration": 0.2, "energy": 0.6, "path": "hit/hit_snap.wav"}
                ],
                "sweep": [
                    {"name": "sweep_up", "duration": 1.5, "energy": 0.5, "path": "sweep/sweep_up.wav"},
                    {"name": "sweep_down", "duration": 1.5, "energy": 0.5, "path": "sweep/sweep_down.wav"},
                    {"name": "sweep_wide", "duration": 2.0, "energy": 0.6, "path": "sweep/sweep_wide.wav"}
                ],
                "transition": [
                    {"name": "trans_smooth", "duration": 1.0, "energy": 0.4, "path": "transition/trans_smooth.wav"},
                    {"name": "trans_glitch", "duration": 0.7, "energy": 0.8, "path": "transition/trans_glitch.wav"},
                    {"name": "trans_swoosh", "duration": 0.8, "energy": 0.6, "path": "transition/trans_swoosh.wav"}
                ]
            }
            
            # Save metadata
            with open(effects_json, 'w') as f:
                json.dump(default_effects, f, indent=2)
            
            # Create mock sound files in DEV_MODE if they don't exist
            if DEV_MODE:
                for category, effects in default_effects.items():
                    category_dir = self.effects_dir / category
                    category_dir.mkdir(exist_ok=True)
                    
                    for effect in effects:
                        effect_path = self.effects_dir / effect["path"]
                        if not effect_path.exists():
                            # Create directory if it doesn't exist
                            effect_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Write a placeholder file with basic information
                            with open(effect_path, 'w') as f:
                                f.write(f"Mock sound effect: {effect['name']}, Duration: {effect['duration']}s, Energy: {effect['energy']}")
                            
                            logger.debug(f"Created mock sound effect: {effect_path}")
        
        # Load metadata
        try:
            with open(effects_json, 'r') as f:
                metadata = json.load(f)
                
            # Populate libraries
            for category, effects in metadata.items():
                if category in self.effect_libraries:
                    self.effect_libraries[category] = effects
                    
            logger.info(f"Loaded sound effect metadata with {sum(len(v) for v in self.effect_libraries.values())} effects")
        except Exception as e:
            logger.error(f"Error loading sound effect metadata: {e}")
    
    def add_sound_effects(self, 
                        video_path: str, 
                        beats: List[float],
                        energy_profile: List[float],
                        output_path: Optional[str] = None) -> str:
        """
        Add sound effects to a video based on beats and energy.
        
        Args:
            video_path: Path to the input video
            beats: List of beat timestamps in seconds
            energy_profile: List of energy values (0-1) for each beat
            output_path: Path for the output video (optional)
            
        Returns:
            str: Path to the enhanced video with sound effects
        """
        # Hello, beautiful learner
        if DEV_MODE:
            logger.info("DEV MODE: Simulating sound effect addition")
            
            # In dev mode, just copy the file and pretend we added effects
            if output_path is None:
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, f"enhanced_{os.path.basename(video_path)}")
            
            # Create a dummy output file with information about applied effects
            with open(output_path, 'w') as f:
                f.write(f"Original video: {video_path}\n")
                f.write(f"Beat count: {len(beats)}\n")
                f.write(f"Average energy: {sum(energy_profile)/len(energy_profile) if energy_profile else 0.0}\n")
                
                # Pick some random effects to "add"
                num_effects = min(5, len(beats))
                f.write(f"Added effects:\n")
                
                for i in range(num_effects):
                    effect_type = random.choice(list(self.effect_libraries.keys()))
                    if self.effect_libraries[effect_type]:
                        effect = random.choice(self.effect_libraries[effect_type])
                        f.write(f"- {effect['name']} at {beats[i % len(beats)]:.2f}s\n")
            
            logger.info(f"Simulated adding {num_effects} sound effects to video")
            return output_path
        
        # Create temp dir for intermediate files
        temp_dir = tempfile.mkdtemp()
        
        # Default output path if not provided
        if output_path is None:
            output_path = os.path.join(temp_dir, f"enhanced_{os.path.basename(video_path)}")
        
        try:
            # Extract audio from video
            audio_path = os.path.join(temp_dir, "original_audio.wav")
            extract_cmd = [
                "ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", 
                "-ar", "44100", "-ac", "2", audio_path
            ]
            
            subprocess.run(extract_cmd, check=True, capture_output=True)
            
            # Create temporary directory for sound effects
            effects_temp_dir = os.path.join(temp_dir, "effects")
            os.makedirs(effects_temp_dir, exist_ok=True)
            
            # Generate silent audio file of the same length as the video
            duration_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            duration_output = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
            video_duration = float(duration_output.stdout.strip())
            
            # Determine where to place sound effects based on beats and energy
            sound_fx_placements = self._generate_effect_placements(beats, energy_profile, video_duration)
            
            # Generate individual effect files
            effect_files = []
            for i, placement in enumerate(sound_fx_placements):
                effect_type = placement["type"]
                start_time = placement["start_time"]
                effect_data = placement["effect"]
                
                # Create a silent audio file
                silent_audio = os.path.join(effects_temp_dir, f"silence_{i}.wav")
                silent_cmd = [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo", 
                    "-t", str(video_duration), silent_audio
                ]
                subprocess.run(silent_cmd, check=True, capture_output=True)
                
                # Get effect file
                if DEV_MODE:
                    # Create a dummy effect file
                    effect_file = os.path.join(effects_temp_dir, f"effect_{i}.wav")
                    with open(effect_file, 'w') as f:
                        f.write(f"Mock effect: {effect_data['name']}")
                else:
                    # Real effect file
                    effect_file = str(self.effects_dir / effect_data["path"])
                
                # Add effect to silent audio at specific time
                output_effect = os.path.join(effects_temp_dir, f"placed_effect_{i}.wav")
                effect_cmd = [
                    "ffmpeg", "-y", "-i", silent_audio, "-i", effect_file,
                    "-filter_complex", f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0,adelay={int(start_time*1000)}|{int(start_time*1000)}",
                    output_effect
                ]
                
                if DEV_MODE:
                    # Just copy the silent file in DEV_MODE
                    output_effect = silent_audio
                else:
                    # Run real command
                    subprocess.run(effect_cmd, check=True, capture_output=True)
                
                effect_files.append(output_effect)
            
            # Mix all effect files with original audio
            mixed_audio = os.path.join(temp_dir, "mixed_audio.wav")
            
            if effect_files:
                # Create filter complex string for mixing
                filter_parts = []
                for i, _ in enumerate(effect_files):
                    filter_parts.append(f"[{i+1}:a]")
                
                mix_inputs = len(effect_files) + 1  # Original audio + effects
                
                mix_cmd = ["ffmpeg", "-y", "-i", audio_path]
                for effect_file in effect_files:
                    mix_cmd.extend(["-i", effect_file])
                
                filter_complex = "".join(filter_parts) + f"[0:a]amix=inputs={mix_inputs}:duration=first:normalize=0"
                mix_cmd.extend(["-filter_complex", filter_complex, mixed_audio])
                
                if DEV_MODE:
                    # Just copy the original audio in DEV_MODE
                    mix_cmd = ["cp", audio_path, mixed_audio]
                
                subprocess.run(mix_cmd, check=True, capture_output=True)
            else:
                # No effects added, just use original audio
                mixed_audio = audio_path
            
            # Combine video with new audio
            combine_cmd = [
                "ffmpeg", "-y", "-i", video_path, "-i", mixed_audio,
                "-c:v", "copy", "-c:a", "aac", "-map", "0:v", "-map", "1:a",
                output_path
            ]
            
            if DEV_MODE:
                # Just copy the original video in DEV_MODE
                combine_cmd = ["cp", video_path, output_path]
            
            subprocess.run(combine_cmd, check=True, capture_output=True)
            
            logger.info(f"Added {len(sound_fx_placements)} sound effects to video")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding sound effects: {e}")
            # Return original video in case of error
            return video_path
    
    def _generate_effect_placements(self, 
                                  beats: List[float], 
                                  energy_profile: List[float],
                                  duration: float) -> List[Dict[str, Any]]:
        """
        Generate a list of effect placements based on beats and energy.
        
        Args:
            beats: List of beat timestamps in seconds
            energy_profile: List of energy values for each beat
            duration: Total duration of the video
            
        Returns:
            List[Dict]: List of effect placement information
        """
        # Hello, beautiful learner
        placements = []
        
        # Safety check for empty beats
        if not beats or not energy_profile:
            return placements
        
        # Normalize beats and energy if their lengths don't match
        if len(beats) != len(energy_profile):
            # Use the shorter length
            min_len = min(len(beats), len(energy_profile))
            beats = beats[:min_len]
            energy_profile = energy_profile[:min_len]
        
        # Identify significant beats (peaks in energy)
        energy_peaks = []
        for i in range(1, len(energy_profile) - 1):
            if energy_profile[i] > energy_profile[i-1] and energy_profile[i] > energy_profile[i+1]:
                # This is a local maximum
                energy_peaks.append((beats[i], energy_profile[i], i))
        
        # Sort peaks by energy level
        energy_peaks.sort(key=lambda x: x[1], reverse=True)
        
        # Select top energy peaks
        top_peaks = energy_peaks[:min(5, len(energy_peaks))]
        
        # Add effects for the highest energy moments
        for beat_time, energy_value, beat_index in top_peaks:
            # Bass drops for very high energy
            if energy_value > 0.75:
                effect_type = "bass_drop"
                effect = self._select_effect(effect_type, energy_value)
                if effect:
                    placements.append({
                        "type": effect_type,
                        "effect": effect,
                        "start_time": max(0, beat_time - 0.1)  # Slightly before the beat
                    })
            
            # Hits for medium-high energy
            elif energy_value > 0.6:
                effect_type = "hit"
                effect = self._select_effect(effect_type, energy_value)
                if effect:
                    placements.append({
                        "type": effect_type,
                        "effect": effect,
                        "start_time": beat_time
                    })
        
        # Add risers before significant energy increases
        for i in range(len(beats) - 4):
            # Look for a steady increase in energy over several beats
            if (energy_profile[i] < energy_profile[i+1] < energy_profile[i+2] < energy_profile[i+3] and
                energy_profile[i+3] > 0.7 and
                energy_profile[i+3] - energy_profile[i] > 0.3):
                
                effect_type = "riser"
                effect = self._select_effect(effect_type, energy_profile[i+3])
                if effect:
                    # Place riser to end at the high energy beat
                    placements.append({
                        "type": effect_type,
                        "effect": effect,
                        "start_time": max(0, beats[i+3] - effect["duration"])
                    })
        
        # Add whooshes for transitions (if we have videos with scene changes, this would be better)
        # For now, just add them at regular intervals if there's enough space
        if len(beats) > 8:
            interval = len(beats) // 4
            for i in range(1, 4):
                beat_index = i * interval
                if beat_index < len(beats):
                    effect_type = "whoosh"
                    effect = self._select_effect(effect_type, energy_profile[beat_index])
                    if effect:
                        placements.append({
                            "type": effect_type,
                            "effect": effect,
                            "start_time": max(0, beats[beat_index] - effect["duration"] / 2)
                        })
        
        # Add transitions between distinct sections (if we had section segmentation)
        # For now, just add at major energy changes
        energy_diffs = [abs(energy_profile[i] - energy_profile[i-1]) for i in range(1, len(energy_profile))]
        if energy_diffs:
            # Find significant changes in energy
            threshold = np.mean(energy_diffs) + np.std(energy_diffs)
            for i, diff in enumerate(energy_diffs):
                if diff > threshold:
                    effect_type = "transition"
                    effect = self._select_effect(effect_type, energy_profile[i+1])
                    if effect:
                        placements.append({
                            "type": effect_type,
                            "effect": effect,
                            "start_time": beats[i+1]
                        })
        
        # Sort placements by time
        placements.sort(key=lambda x: x["start_time"])
        
        # Remove overlapping effects
        filtered_placements = []
        last_end_time = -1.0
        
        for placement in placements:
            start_time = placement["start_time"]
            effect_duration = placement["effect"]["duration"]
            end_time = start_time + effect_duration
            
            # Check if this effect overlaps with the previous one
            if start_time >= last_end_time:
                filtered_placements.append(placement)
                last_end_time = end_time
        
        return filtered_placements
    
    def _select_effect(self, effect_type: str, energy_value: float) -> Optional[Dict[str, Any]]:
        """
        Select an appropriate effect based on energy value.
        
        Args:
            effect_type: Type of effect to select
            energy_value: Energy value to match
            
        Returns:
            Dict or None: Selected effect metadata or None if no suitable effect
        """
        # Hello, beautiful learner
        if effect_type not in self.effect_libraries or not self.effect_libraries[effect_type]:
            return None
        
        # Find effects with similar energy
        matching_effects = []
        for effect in self.effect_libraries[effect_type]:
            energy_diff = abs(effect["energy"] - energy_value)
            if energy_diff < 0.3:  # Within a reasonable range
                matching_effects.append((effect, energy_diff))
        
        if not matching_effects:
            # If no good match, take a random effect of this type
            return random.choice(self.effect_libraries[effect_type])
        
        # Sort by energy difference and take the best match
        matching_effects.sort(key=lambda x: x[1])
        return matching_effects[0][0]

def get_sound_effect_processor() -> SoundEffectProcessor:
    """
    Get the sound effect processor instance.
    
    Returns:
        SoundEffectProcessor: Sound effect processor
    """
    # Hello, beautiful learner
    return SoundEffectProcessor() 