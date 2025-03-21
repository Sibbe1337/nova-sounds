"""
Music analyzer module for extracting features from audio.

This module provides the MusicAnalyzer class which is responsible for 
analyzing audio files and extracting various musical features.
"""

import os
import logging
import numpy as np
import librosa
import random
from typing import Optional, List, Dict, Any

from src.app.core.settings import DEV_MODE, DEBUG_MODE
from src.app.services.video.music_responsive.enums import MusicFeature
from src.app.services.audio.analyzer import AudioAnalyzer

# Set up logging
logger = logging.getLogger(__name__)

class MusicAnalyzer:
    """Analyzes music to extract features for responsive video effects with enhanced accuracy."""
    
    def __init__(self, audio_path: str, anticipation_time: float = 0.1):
        """
        Initialize the music analyzer with enhanced audio analysis capabilities.
        
        Args:
            audio_path: Path to the audio file
            anticipation_time: Time in seconds to anticipate beats (default: 0.1s)
        """
        self.audio_path = audio_path
        self.y = None
        self.sr = None
        self.beat_times = None
        self.beat_strengths = None  # Store beat strengths for dynamically adjusting effects
        self.tempo = None
        self.onsets = None
        self.spectral_contrast = None
        self.spectral_centroid = None
        self.rms_energy = None
        self.chroma = None
        self.harmonic = None
        self.percussive = None
        self.anticipation_time = anticipation_time
        self.anticipated_beats = None
        self.key_moments = []  # Store key moments for transitions
        self.segments = []  # Store structural segments
        self.features_analyzed = []  # Track which features were analyzed
        
        # Enhanced beat patterns
        self.beat_patterns = []  # Store detected beat patterns
        self.beat_drops = []  # Store significant energy increases (drops)
        self.beat_buildups = []  # Store energy buildups before drops
        self.groove_type = None  # Classification of the overall groove pattern
        self.phrase_boundaries = []  # Store musical phrase boundaries
        
        # Utilize the enhanced AudioAnalyzer for better beat detection
        self.audio_analyzer = None
        
        # Load audio if path exists and is not in DEV mode
        if os.path.exists(audio_path) and (not DEV_MODE or os.path.getsize(audio_path) > 1000):
            self._load_audio()
        else:
            logger.warning(f"Audio file not found or empty: {audio_path}")
            if DEV_MODE:
                logger.info("DEV mode: Using mock audio data")
                self._generate_mock_data()
    
    def _load_audio(self):
        """Load and process the audio file to extract features with enhanced analysis."""
        try:
            logger.info(f"Loading audio from {self.audio_path}")
            
            # Special handling for files in the mock-media directory
            if 'mock-media' in self.audio_path or os.path.getsize(self.audio_path) < 1000:
                logger.info("Mock audio file detected, using mock data")
                self._generate_mock_data()
                return
            
            # Use regular librosa loading for basic features
            self.y, self.sr = librosa.load(self.audio_path)
            
            # Use the enhanced AudioAnalyzer for more advanced analysis
            try:
                # Create an instance of the enhanced AudioAnalyzer
                self.audio_analyzer = AudioAnalyzer()
                
                # Analyze the track using enhanced features
                audio_url = f"file://{os.path.abspath(self.audio_path)}"
                analysis_result = self.audio_analyzer.analyze_track("local", audio_url)
                
                # Extract key features from the enhanced analysis
                if analysis_result:
                    # Get beat markers and their strengths
                    self.beat_times = np.array(analysis_result.beat_markers)
                    # BPM information
                    self.tempo = float(analysis_result.bpm)
                    # Key moments for transitions
                    self.key_moments = analysis_result.key_moments
                    # Segments for structural analysis
                    self.segments = analysis_result.segments
                    
                    # Perform enhanced beat pattern analysis
                    self._analyze_beat_patterns()
                    
                    logger.info(f"Enhanced audio analysis complete: {len(self.beat_times)} beats at {self.tempo} BPM, "
                               f"{len(self.key_moments)} key moments, {len(self.segments)} segments, "
                               f"{len(self.beat_patterns)} beat patterns detected")
                
            except Exception as e:
                logger.warning(f"Enhanced audio analysis failed, falling back to basic analysis: {e}")
                # Fall back to basic librosa analysis
                self._extract_basic_features()
        
        except Exception as e:
            logger.error(f"Error loading audio: {e}")
            if DEV_MODE:
                logger.info("DEV mode: Using mock audio data after error")
                self._generate_mock_data()
            else:
                raise
    
    def _generate_mock_data(self):
        """Generate mock data for development and testing."""
        # Mock sample rate
        self.sr = 22050
        
        # Mock audio signal (10 seconds)
        duration = 60  # seconds
        self.y = np.zeros(self.sr * duration)
        
        # Mock beat times (regular intervals)
        beats_per_minute = 120
        num_beats = int((beats_per_minute / 60) * duration)
        self.beat_times = np.linspace(0, duration, num_beats)
        self.tempo = float(beats_per_minute)
        
        # Generate anticipated beats
        self.anticipated_beats = np.array([max(0, beat - self.anticipation_time) for beat in self.beat_times])
        
        # Mock onset times (slightly more than beats)
        num_onsets = int(num_beats * 1.5)
        self.onsets = np.linspace(0, duration, num_onsets)
        
        # Mock spectral features
        frames = 100
        self.spectral_contrast = np.random.rand(7, frames)
        self.spectral_centroid = np.random.rand(frames) * 2000 + 1000
        self.rms_energy = np.random.rand(frames) * 0.5
        self.chroma = np.random.rand(12, frames)
        
        # Mock harmonic/percussive separation
        self.harmonic = np.random.rand(self.sr * duration) * 0.5
        self.percussive = np.random.rand(self.sr * duration) * 0.5
        
        logger.info(f"Generated mock data with {num_beats} beats at {beats_per_minute} BPM")
    
    def _extract_basic_features(self):
        """Extract basic features from the audio."""
        # Beat detection
        self.tempo, beats = librosa.beat.beat_track(y=self.y, sr=self.sr, hop_length=512, units='time')
        self.beat_times = beats
        
        # Generate anticipated beats (slightly before actual beats)
        self.anticipated_beats = np.array([max(0, beat - self.anticipation_time) for beat in self.beat_times])
        
        # Onset detection
        onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr)
        self.onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self.sr, 
                                               units='time', hop_length=512)
        
        # Spectral contrast
        self.spectral_contrast = librosa.feature.spectral_contrast(y=self.y, sr=self.sr)
        
        # Spectral centroid
        self.spectral_centroid = librosa.feature.spectral_centroid(y=self.y, sr=self.sr)[0]
        
        # RMS energy
        self.rms_energy = librosa.feature.rms(y=self.y)[0]
        
        # Chroma features
        self.chroma = librosa.feature.chroma_stft(y=self.y, sr=self.sr)
        
        # Harmonic-percussive separation
        self.harmonic, self.percussive = librosa.effects.hpss(self.y)
        
        logger.info(f"Extracted features: {len(self.beat_times)} beats at {self.tempo:.1f} BPM, "
                   f"{len(self.onsets)} onsets, {self.spectral_contrast.shape[1]} frames of spectral data")
    
    def _extract_beat_strengths(self):
        """Extract beat strengths from the audio signal."""
        if self.y is None or self.sr is None or self.beat_times is None or len(self.beat_times) == 0:
            # Generate mock strengths if we don't have audio data
            self.beat_strengths = [random.uniform(0.5, 1.0) for _ in range(len(self.beat_times))] if self.beat_times is not None else []
            return
            
        # Calculate onset envelope
        onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr)
        
        # Calculate beat strengths
        beat_strengths = []
        for beat in self.beat_times:
            beat_frame = librosa.time_to_frames(beat, sr=self.sr)
            if beat_frame < len(onset_env):
                strength = onset_env[beat_frame]
                beat_strengths.append(strength)
            else:
                beat_strengths.append(0)
        
        # Normalize strengths
        if beat_strengths:
            max_strength = max(beat_strengths)
            if max_strength > 0:
                beat_strengths = [s/max_strength for s in beat_strengths]
            
            # Enhance weak beats to ensure better responsiveness
            beat_strengths = [max(0.3, s) for s in beat_strengths]
        
        self.beat_strengths = beat_strengths
    
    def _analyze_beat_patterns(self):
        """
        Analyze beat patterns for more sophisticated synchronization.
        Identifies patterns like buildups, drops, and rhythmic structures.
        """
        if self.y is None or self.sr is None or self.beat_times is None:
            logger.warning("Cannot analyze beat patterns without audio data and beat times")
            return
        
        try:
            # Calculate inter-beat intervals
            if len(self.beat_times) > 1:
                ibis = np.diff(self.beat_times)
                
                # Find steady regions vs. changing tempo regions
                median_ibi = np.median(ibis)
                ibi_variation = np.abs(ibis - median_ibi) / median_ibi
                
                # Identify regions with steady tempo (potential groove sections)
                steady_regions = []
                current_region = []
                
                for i, variation in enumerate(ibi_variation):
                    if variation < 0.1:  # Less than 10% variation from median
                        current_region.append(i)
                    else:
                        if len(current_region) > 4:  # At least 4 steady beats
                            steady_regions.append(current_region)
                        current_region = []
                
                if len(current_region) > 4:
                    steady_regions.append(current_region)
                    
                # Store beat patterns
                self.beat_patterns = []
                for region in steady_regions:
                    start_beat = region[0]
                    end_beat = region[-1] + 1  # +1 because these are indices into ibis
                    if end_beat < len(self.beat_times):
                        pattern = {
                            "start_time": self.beat_times[start_beat],
                            "end_time": self.beat_times[end_beat],
                            "num_beats": end_beat - start_beat,
                            "avg_tempo": 60 / np.mean(ibis[start_beat:end_beat])
                        }
                        self.beat_patterns.append(pattern)
            
            # Calculate energy curve and find drops
            if self.rms_energy is not None:
                # Normalize energy
                norm_energy = librosa.util.normalize(self.rms_energy)
                
                # Find significant energy increases (drops)
                energy_diff = np.diff(np.concatenate([[0], norm_energy]))
                
                # Smooth the energy curve
                from scipy.ndimage import gaussian_filter1d
                smoothed_diff = gaussian_filter1d(energy_diff, sigma=5)
                
                # Find peaks in the difference curve (sudden energy increases)
                peaks, _ = librosa.util.peak_pick(
                    smoothed_diff, 
                    pre_max=10, post_max=10, 
                    pre_avg=30, post_avg=30, 
                    delta=0.2, wait=20
                )
                
                # Convert frame indices to times
                hop_length = 512  # Default hop length in librosa
                self.beat_drops = librosa.frames_to_time(peaks, sr=self.sr, hop_length=hop_length)
                
                # Find buildups before drops
                self.beat_buildups = []
                for drop_time in self.beat_drops:
                    # Look for 2-4 seconds before the drop
                    buildup_start = max(0, drop_time - 4.0)
                    buildup_end = drop_time
                    self.beat_buildups.append((buildup_start, buildup_end))
            
            # Determine groove type based on beat pattern and tempo
            if self.tempo is not None:
                if self.tempo < 85:
                    self.groove_type = "slow"
                elif self.tempo < 110:
                    self.groove_type = "medium"
                else:
                    self.groove_type = "fast"
                    
                # Refine based on energy and beat patterns
                if self.rms_energy is not None:
                    avg_energy = np.mean(self.rms_energy)
                    if avg_energy > 0.7:
                        self.groove_type += "_high_energy"
                    elif avg_energy < 0.4:
                        self.groove_type += "_low_energy"
                        
                # Identify phrase boundaries (typically 4, 8, or 16 beats)
                if len(self.beat_times) > 16:
                    # Look for patterns of 4, 8, or 16 beats
                    for phrase_length in [16, 8, 4]:
                        if len(self.beat_times) >= phrase_length:
                            num_phrases = len(self.beat_times) // phrase_length
                            self.phrase_boundaries = [
                                self.beat_times[i * phrase_length] 
                                for i in range(1, num_phrases)
                            ]
                            if len(self.phrase_boundaries) > 0:
                                break
        
        except Exception as e:
            logger.error(f"Error in beat pattern analysis: {e}")
    
    def get_feature_at_time(self, feature: MusicFeature, time_sec: float) -> float:
        """
        Get the value of a specific music feature at a given time with enhanced pattern recognition.
        
        Args:
            feature: Which music feature to get
            time_sec: Time in seconds
            
        Returns:
            float: Feature value between 0.0 and 1.0
        """
        # Add new features for enhanced beat patterns
        if feature == MusicFeature.BEAT_PATTERN_INTENSITY:
            # Check if we're in a recognized beat pattern
            for pattern in self.beat_patterns:
                if pattern["start_time"] <= time_sec <= pattern["end_time"]:
                    # Return higher values for faster tempos
                    return min(1.0, pattern["avg_tempo"] / 180.0)
            return 0.0
            
        elif feature == MusicFeature.DROP_PROXIMITY:
            # Return values that increase as we approach a drop, peak at the drop
            if self.beat_drops is not None and len(self.beat_drops) > 0:
                # Find the nearest drop
                distances = np.abs(np.array(self.beat_drops) - time_sec)
                nearest_idx = np.argmin(distances)
                nearest_drop = self.beat_drops[nearest_idx]
                
                # If we're in a buildup to this drop
                if time_sec < nearest_drop:
                    # Check if we're in the buildup period
                    for start, end in self.beat_buildups:
                        if start <= time_sec <= end:
                            # Value increases as we get closer to the drop
                            return 1.0 - ((end - time_sec) / (end - start))
                
                # If we're right at a drop
                elif abs(time_sec - nearest_drop) < 0.5:  # Within 0.5 seconds of a drop
                    return 1.0
            
            return 0.0
            
        elif feature == MusicFeature.PHRASE_BOUNDARY:
            # Return 1.0 if we're at a phrase boundary, 0.0 otherwise
            if self.phrase_boundaries is not None and len(self.phrase_boundaries) > 0:
                # Check if we're near a phrase boundary
                distances = np.abs(np.array(self.phrase_boundaries) - time_sec)
                if np.min(distances) < 0.1:  # Within 0.1 seconds of a boundary
                    return 1.0
            return 0.0
            
        # Original feature handling
        if feature == MusicFeature.BEATS:
            # Enhanced beats with patterns
            base_value = self._get_beat_value(time_sec)
            
            # Boost at phrase boundaries
            for boundary in self.phrase_boundaries:
                if abs(time_sec - boundary) < 0.1:
                    return min(1.0, base_value * 1.5)  # Boost by 50% at phrase boundaries
                    
            return base_value
                
        elif feature == MusicFeature.ONSETS:
            # Get basic onset value
            onset_value = self._get_onset_value(time_sec)
            
            # Enhance for drops
            for drop_time in self.beat_drops:
                if abs(time_sec - drop_time) < 0.2:  # Within 0.2 seconds of a drop
                    return min(1.0, onset_value * 2.0)  # Double the intensity at drops
                    
            return onset_value
            
        # Rest of the original code
        elif feature == MusicFeature.SPECTRAL_CONTRAST:
            if self.spectral_contrast is not None:
                frame_idx = librosa.time_to_frames(time_sec, sr=self.sr, hop_length=512)
                if 0 <= frame_idx < len(self.spectral_contrast):
                    # Average across frequency bands
                    return float(np.mean(self.spectral_contrast[frame_idx]))
            return 0.5
        
        elif feature == MusicFeature.SPECTRAL_CENTROID:
            if self.spectral_centroid is not None:
                frame_idx = librosa.time_to_frames(time_sec, sr=self.sr, hop_length=512)
                if 0 <= frame_idx < len(self.spectral_centroid):
                    # Normalize centroid
                    return min(1.0, self.spectral_centroid[frame_idx] / 10000.0)
            return 0.5
        
        elif feature == MusicFeature.ENERGY:
            if self.rms_energy is not None:
                frame_idx = librosa.time_to_frames(time_sec, sr=self.sr, hop_length=512)
                if 0 <= frame_idx < len(self.rms_energy):
                    return min(1.0, self.rms_energy[frame_idx] * 2.0)
            return 0.5
        
        # Default case
        return 0.5

    def get_segment_intensity(self, start_time: float, end_time: float) -> float:
        """
        Calculate overall musical intensity for a time segment.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            float: Intensity value between 0.0 and 1.0
        """
        if self.y is None:
            return 0.7 if DEV_MODE else 0.0
        
        try:
            # Convert times to sample indices
            start_sample = int(start_time * self.sr)
            end_sample = int(end_time * self.sr)
            
            if end_sample > len(self.y):
                end_sample = len(self.y)
            
            if start_sample >= end_sample:
                return 0.5
            
            # Get segment audio
            segment = self.y[start_sample:end_sample]
            
            # Calculate features for this segment
            rms = np.sqrt(np.mean(segment**2))
            spectral_cent = np.mean(librosa.feature.spectral_centroid(y=segment, sr=self.sr)[0])
            
            # Count beats in segment
            beats_in_segment = np.sum((self.beat_times >= start_time) & (self.beat_times < end_time))
            beat_density = beats_in_segment / (end_time - start_time) / (self.tempo / 60)
            
            # Combine features to estimate intensity
            intensity = (
                0.4 * min(1.0, rms * 5) +
                0.3 * min(1.0, spectral_cent / 5000) +
                0.3 * min(1.0, beat_density * 2)
            )
            
            return float(intensity)
            
        except Exception as e:
            logger.error(f"Error calculating segment intensity: {e}")
            return 0.6 if DEV_MODE else 0.0
    
    def get_time_to_next_beat(self, time_sec: float) -> float:
        """
        Calculate time until the next beat from current position.
        
        Args:
            time_sec: Current time in seconds
            
        Returns:
            float: Time until next beat in seconds (0 if on a beat)
        """
        if self.beat_times is None or len(self.beat_times) == 0:
            return 0.5
        
        # Find beats after current time
        next_beats = self.beat_times[self.beat_times > time_sec]
        
        if len(next_beats) == 0:
            return 0.5  # No more beats, return default
        
        # Return time to next beat
        return next_beats[0] - time_sec 