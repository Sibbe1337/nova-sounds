"""
Advanced audio analysis service for Nova Sounds.
Uses librosa for feature extraction and classification.
"""
import os
import logging
import tempfile
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import librosa
import librosa.display
import requests
from pathlib import Path

from src.app.models.music import AudioAnalysisResult, EnergyLevel
from src.app.core.settings import DEV_MODE, DEBUG_MODE

# Set up logging
logger = logging.getLogger(__name__)

class AudioAnalyzer:
    """Service for analyzing audio files and extracting features."""
    
    def __init__(self):
        """Initialize the audio analyzer."""
        logger.info("Initializing AudioAnalyzer")
    
    def download_audio(self, url: str, output_path: str) -> str:
        """
        Download audio from a URL to a local file.
        
        Args:
            url: URL of the audio file
            output_path: Local path to save the file
            
        Returns:
            str: Path to the downloaded file
        """
        logger.info(f"Downloading audio from {url} to {output_path}")
        
        # If in dev mode and using local file
        if DEV_MODE and url.startswith("http://localhost"):
            # Extract filename from URL
            filename = url.split("/")[-1]
            mock_path = os.path.join("mock-media", filename)
            
            if os.path.exists(mock_path):
                # Copy the file instead of downloading
                with open(mock_path, 'rb') as src, open(output_path, 'wb') as dst:
                    dst.write(src.read())
                logger.info(f"Copied mock file from {mock_path} to {output_path}")
                return output_path
        
        # Regular download for remote URLs
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return output_path
    
    def _extract_waveform(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Extract waveform data for visualization.
        
        Args:
            y: Audio time series
            sr: Sample rate
            
        Returns:
            Dict: Waveform data in a format suitable for visualization
        """
        # Downsample for visualization
        max_points = 1000
        if len(y) > max_points:
            ratio = len(y) // max_points
            y_downsampled = np.array([np.mean(y[i:i+ratio]) for i in range(0, len(y), ratio)])
        else:
            y_downsampled = y
        
        return {
            "data": y_downsampled.tolist(),
            "sample_rate": sr,
            "duration": len(y) / sr
        }
    
    def _extract_tempo_and_beats(self, y: np.ndarray, sr: int) -> Tuple[float, np.ndarray, List[float]]:
        """
        Extract tempo and beat positions with enhanced accuracy.
        
        Args:
            y: Audio time series
            sr: Sample rate
            
        Returns:
            Tuple: (tempo, beat_times, beat_strengths)
        """
        # Multi-band approach for better beat detection
        # Split signal into sub-bands (low, mid, high)
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        # Get onset envelopes for different bands
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_env_percussive = librosa.onset.onset_strength(y=y_percussive, sr=sr)
        
        # Dynamic tempo estimation with confidence measure
        tempo_global, tempo_confidence = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, aggregate=None)
        tempo_percussive, _ = librosa.beat.tempo(onset_envelope=onset_env_percussive, sr=sr, aggregate=None)
        
        # Select tempo based on confidence and percussive content
        if len(tempo_confidence) > 0:
            # Find the most confident tempo estimate
            best_tempo_idx = np.argmax(tempo_confidence)
            tempo = tempo_global[best_tempo_idx]
            
            # Check if percussive tempo is very different and has strong percussive content
            percussive_ratio = np.sum(np.abs(y_percussive)) / (np.sum(np.abs(y_harmonic)) + 1e-5)
            if percussive_ratio > 0.5 and abs(tempo - tempo_percussive[0]) > 10:
                # Use percussive tempo if it's significantly different and the track is percussive
                tempo = tempo_percussive[0]
        else:
            # Fallback
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
        
        # Dynamic beat tracking with enhanced onset detection
        ac_size = min(4 * sr, len(y))
        
        # Use stronger weighting for percussive onset features
        oenv_weighted = onset_env * 0.7 + onset_env_percussive * 0.3
        _, beats = librosa.beat.beat_track(onset_envelope=oenv_weighted, sr=sr, units='time', hop_length=512)
        
        # Refine beat positions using dynamic programming
        if len(beats) > 4:
            # Estimate beat consistency
            beat_intervals = np.diff(beats)
            consistency = 1.0 - np.std(beat_intervals) / np.mean(beat_intervals)
            
            if consistency < 0.6:  # If beats are not consistent
                # Try to refine the beats with dynamic programming
                oenv_db = librosa.amplitude_to_db(oenv_weighted, ref=np.max)
                beats = librosa.beat.beat_track(onset_envelope=oenv_db, sr=sr, units='time', 
                                               start_bpm=tempo, tightness=400)[-1]
        
        # Calculate beat strengths - higher resolution using multiple features
        beat_strengths = []
        for beat in beats:
            beat_frame = librosa.time_to_frames(beat, sr=sr)
            if beat_frame < len(onset_env):
                # Combine energy and percussive onset strength for more accurate strength measurement
                strength = onset_env[beat_frame] * 0.6 + onset_env_percussive[beat_frame] * 0.4
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
        
        return tempo, beats, beat_strengths
    
    def _extract_key_moments(self, y: np.ndarray, sr: int) -> List[float]:
        """
        Extract key moments for transitions with enhanced detection of structural changes.
        
        Args:
            y: Audio time series
            sr: Sample rate
            
        Returns:
            List: Key moments in seconds
        """
        # Compute novelty curve with enhanced parameters
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
        
        # Separate harmonic and percussive content for better analysis
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        # Get onset envelopes specialized for different components
        onset_env_percussive = librosa.onset.onset_strength(y=y_percussive, sr=sr, hop_length=512)
        onset_env_harmonic = librosa.onset.onset_strength(y=y_harmonic, sr=sr, hop_length=512)
        
        # Compute spectral novelty for harmonic changes
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)
        mfcc_delta = librosa.feature.delta(mfcc)
        harmonic_novelty = np.sum(np.abs(mfcc_delta), axis=0)
        
        # Normalize novelty curves
        if len(onset_env) > 0 and np.max(onset_env) > 0:
            onset_env = onset_env / np.max(onset_env)
        if len(onset_env_percussive) > 0 and np.max(onset_env_percussive) > 0:
            onset_env_percussive = onset_env_percussive / np.max(onset_env_percussive)
        if len(harmonic_novelty) > 0 and np.max(harmonic_novelty) > 0:
            harmonic_novelty = harmonic_novelty / np.max(harmonic_novelty)
        
        # Create composite novelty curve emphasizing both rhythm and harmonic changes
        composite_novelty = onset_env * 0.5 + onset_env_percussive * 0.3 + harmonic_novelty * 0.2
        
        # Find peaks in novelty curve with adaptive thresholding
        # Calculate median and standard deviation for adaptive threshold
        med_composite = np.median(composite_novelty)
        std_composite = np.std(composite_novelty)
        
        # Set peak picking parameters
        pre_max = 30  # 30 frames before peak (for context)
        post_max = 30  # 30 frames after peak (for context)
        pre_avg = 100  # 100 frames for pre-average
        post_avg = 100  # 100 frames for post-average
        wait = 30      # Wait 30 frames after a peak before detecting another
        
        # Adaptive delta parameter based on audio characteristics
        delta = med_composite + std_composite * 1.5
        
        # Find peaks in composite novelty curve
        peaks = librosa.util.peak_pick(composite_novelty, 
                                     pre_max=pre_max, post_max=post_max, 
                                     pre_avg=pre_avg, post_avg=post_avg, 
                                     delta=delta, wait=wait)
        
        # Convert to time
        peak_times = librosa.frames_to_time(peaks, sr=sr, hop_length=512)
        
        # Calculate strength of each peak using multiple features
        peak_strengths = []
        for p in peaks:
            # If we're within bounds
            if p < len(composite_novelty):
                strength = composite_novelty[p]
                peak_strengths.append(strength)
            else:
                peak_strengths.append(0)
        
        peak_strengths = np.array(peak_strengths)
        
        # Structural segmentation using spectral clustering
        if len(y) > sr * 10:  # Only for audio longer than 10 seconds
            try:
                # Compute recurrence matrix for structural analysis
                S = librosa.feature.melspectrogram(y=y, sr=sr, hop_length=512)
                S_db = librosa.power_to_db(S, ref=np.max)
                
                # Compute self-similarity matrix
                R = librosa.segment.recurrence_matrix(S_db, mode='affinity', k=5)
                
                # Find segment boundaries (up to 10 segments maximum)
                segment_idx = librosa.segment.agglomerative(R, min(10, len(y) // sr // 5))
                segment_times = librosa.frames_to_time(segment_idx, sr=sr, hop_length=512)
                
                # Add structural boundaries to key moments if they're not already close to detected peaks
                for segment_time in segment_times:
                    # Check if this segment boundary is already close to a detected peak
                    if peak_times.size > 0:
                        min_distance = np.min(np.abs(peak_times - segment_time))
                        # If this segment boundary is not close to any existing peak
                        if min_distance > 2.0:  # More than 2 seconds away from any detected peak
                            peak_times = np.append(peak_times, segment_time)
                            # Assign an average strength to structural boundaries
                            peak_strengths = np.append(peak_strengths, 0.8)
            except Exception as e:
                logger.warning(f"Error in structural segmentation: {e}")
        
        # Sort peaks by time
        if peak_times.size > 0:
            sort_idx = np.argsort(peak_times)
            peak_times = peak_times[sort_idx]
            peak_strengths = peak_strengths[sort_idx]
        
        # Keep only the strongest peaks and peaks at structural boundaries
        if peak_strengths.size > 0:
            # Adaptive thresholding based on distribution of strengths
            strength_mean = np.mean(peak_strengths)
            strength_std = np.std(peak_strengths)
            strength_threshold = max(0.5, strength_mean - 0.5 * strength_std)
            
            # Keep peaks above threshold
            strong_peaks_mask = peak_strengths >= strength_threshold
            strong_peaks = peak_times[strong_peaks_mask]
            
            # Ensure key moments are not too close to each other (minimum 2 seconds apart)
            if len(strong_peaks) > 1:
                filtered_peaks = [strong_peaks[0]]
                for i in range(1, len(strong_peaks)):
                    if strong_peaks[i] - filtered_peaks[-1] >= 2.0:
                        filtered_peaks.append(strong_peaks[i])
                strong_peaks = np.array(filtered_peaks)
            
            return strong_peaks.tolist()
        
        return []
    
    def _detect_energy_level(self, y: np.ndarray, sr: int) -> EnergyLevel:
        """
        Detect the energy level of the track with enhanced accuracy using multi-feature analysis.
        
        Args:
            y: Audio time series
            sr: Sample rate
            
        Returns:
            EnergyLevel: LOW, MEDIUM, or HIGH
        """
        # Extract multiple energy-related features
        
        # RMS energy (volume)
        rms = librosa.feature.rms(y=y)[0]
        rms_mean = np.mean(rms)
        rms_std = np.std(rms)
        rms_max = np.max(rms)
        
        # Spectral centroid (brightness)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = np.mean(centroid)
        
        # Spectral contrast (difference between peaks and valleys in the spectrum)
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = np.mean(contrast)
        
        # Spectral flatness (noisiness vs. tonality)
        flatness = librosa.feature.spectral_flatness(y=y)[0]
        flatness_mean = np.mean(flatness)
        
        # Temporal features
        
        # Onset density (how many onsets per second)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_times = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units='time')
        if len(y) > 0:
            onset_density = len(onset_times) / (len(y) / sr)
        else:
            onset_density = 0
        
        # Separate harmonic and percussive components
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        # Calculate percussive energy ratio
        percussive_energy = np.sum(y_percussive**2)
        total_energy = np.sum(y**2)
        if total_energy > 0:
            percussive_ratio = percussive_energy / total_energy
        else:
            percussive_ratio = 0
        
        # Dynamic range compression detection 
        # (heavily compressed tracks tend to have higher energy)
        if len(rms) > 0:
            dynamic_range = rms_max / (np.median(rms) + 1e-5)
        else:
            dynamic_range = 1.0
        
        # Loudness calculation with perceptual weighting based on human hearing
        S = librosa.feature.melspectrogram(y=y, sr=sr)
        S_db = librosa.power_to_db(S, ref=np.max)
        perceptual_loudness = np.mean(np.max(S_db, axis=0))
        
        # Compute tempo (faster tracks often perceived as higher energy)
        tempo = librosa.beat.tempo(y=y, sr=sr)[0]
        
        # Feature normalization using typical ranges
        norm_rms = min(1.0, rms_mean * 5.0)  # Normalize RMS 
        norm_centroid = min(1.0, centroid_mean / 5000.0)  # Normalize centroid
        norm_contrast = min(1.0, contrast_mean / 5.0)  # Normalize contrast
        norm_flatness = 1.0 - min(1.0, flatness_mean * 10.0)  # Inverse of flatness (1 = tonal, 0 = noisy)
        norm_onset = min(1.0, onset_density / 5.0)  # Normalize onset density
        norm_percussive = min(1.0, percussive_ratio * 3.0)  # Normalize percussive ratio
        norm_tempo = min(1.0, tempo / 180.0)  # Normalize tempo (180 BPM is considered high)
        norm_loudness = min(1.0, (perceptual_loudness + 60) / 50.0)  # Normalize loudness from dB scale
        
        # Combined energy score with weighted features
        energy_score = (
            norm_rms * 0.25 +              # Volume level
            norm_centroid * 0.15 +         # Brightness
            norm_contrast * 0.10 +         # Spectral contrast
            norm_flatness * 0.05 +         # Tonality
            norm_onset * 0.15 +            # Rhythmic activity
            norm_percussive * 0.15 +       # Percussive content
            norm_tempo * 0.05 +            # Tempo impact
            norm_loudness * 0.10           # Perceived loudness
        )
        
        # Classification using adaptive thresholds
        # Calculate thresholds based on dynamic range compression
        compression_factor = min(1.0, max(0.0, (dynamic_range - 1.0) / 10.0))
        
        # Adjust thresholds based on compression (compressed music needs higher thresholds)
        base_low_threshold = 0.3
        base_high_threshold = 0.65
        
        # Apply compression-aware threshold adjustment
        low_threshold = base_low_threshold + (compression_factor * 0.1) 
        high_threshold = base_high_threshold + (compression_factor * 0.1)
        
        if energy_score < low_threshold:
            return EnergyLevel.LOW
        elif energy_score > high_threshold:
            return EnergyLevel.HIGH
        else:
            return EnergyLevel.MEDIUM
    
    def _detect_segments(self, y: np.ndarray, sr: int) -> List[Dict[str, Any]]:
        """
        Detect structural segments in the audio with enhanced accuracy.
        
        Args:
            y: Audio time series
            sr: Sample rate
            
        Returns:
            List: Segments with start, end times and characteristics
        """
        # Skip for very short audio
        if len(y) < sr * 5:  # Less than 5 seconds
            return [{
                "start": 0.0,
                "end": len(y) / sr,
                "duration": len(y) / sr,
                "energy": float(np.mean(librosa.feature.rms(y=y)[0]))
            }]
        
        # Compute Mel spectrogram
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, hop_length=512)
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Compute MFCCs for segment detection (focusing on timbre)
        mfcc = librosa.feature.mfcc(S=S_db, n_mfcc=13)
        mfcc_delta = librosa.feature.delta(mfcc)  # Add first-order differences
        
        # Stack features for better segmentation
        features = np.vstack([
            mfcc,  # Timbre
            mfcc_delta,  # Timbre changes
        ])
        
        # Normalize features
        features_mean = np.mean(features, axis=1, keepdims=True)
        features_std = np.std(features, axis=1, keepdims=True) + 1e-8
        features_normalized = (features - features_mean) / features_std
        
        # Calculate self-similarity matrix
        similarity = librosa.segment.recurrence_matrix(
            features_normalized, 
            mode='affinity',
            width=3,     # Only compare with nearby frames
            k=5,         # Use 5 nearest neighbors
            sym=True     # Make the matrix symmetric
        )
        
        # Enhance diagonal and smooth
        similarity = np.maximum(similarity, np.eye(similarity.shape[0]) * 0.9)
        similarity = librosa.segment.path_enhance(similarity, 15)
        
        # Adaptive number of segments based on duration
        duration = len(y) / sr
        min_segments = max(2, int(duration / 10))  # At least 2 segments, or 1 per 10 seconds
        max_segments = min(10, int(duration / 5))  # At most 10 segments, or 1 per 5 seconds
        
        # Try multiple segmentation levels
        best_segments = None
        best_score = -np.inf
        
        for n_segments in range(min_segments, max_segments + 1):
            try:
                # Perform agglomerative clustering
                boundaries = librosa.segment.agglomerative(similarity, n_segments)
                
                # Convert frame indices to time
                boundary_times = librosa.frames_to_time(boundaries, sr=sr, hop_length=512)
                
                # Create segments
                segments = []
                for i in range(len(boundary_times) - 1):
                    start_time = boundary_times[i]
                    end_time = boundary_times[i+1]
                    
                    # Get frames within this segment
                    start_frame = librosa.time_to_frames(start_time, sr=sr, hop_length=512)
                    end_frame = librosa.time_to_frames(end_time, sr=sr, hop_length=512)
                    
                    # Calculate segment energy (RMS)
                    segment_y = y[int(start_time * sr):int(end_time * sr)]
                    segment_rms = np.mean(librosa.feature.rms(y=segment_y)[0]) if len(segment_y) > 0 else 0
                    
                    # Calculate segment contrast (max difference in frequency bands)
                    if start_frame < end_frame and end_frame <= S.shape[1]:
                        segment_contrast = np.mean(np.std(S[:, start_frame:end_frame], axis=0))
                    else:
                        segment_contrast = 0
                    
                    # Calculate tempo variation
                    try:
                        if len(segment_y) > sr * 3:  # Need at least 3 seconds for tempo estimation
                            segment_tempo = librosa.beat.tempo(y=segment_y, sr=sr)[0]
                        else:
                            segment_tempo = 0
                    except Exception:
                        segment_tempo = 0
                    
                    segments.append({
                        "start": float(start_time),
                        "end": float(end_time),
                        "duration": float(end_time - start_time),
                        "energy": float(segment_rms),
                        "contrast": float(segment_contrast),
                        "tempo": float(segment_tempo)
                    })
                
                # Score the segmentation based on segment duration consistency and feature contrast
                if segments:
                    # Calculate duration consistency (lower std deviation is better)
                    durations = [s["duration"] for s in segments]
                    duration_consistency = 1.0 / (np.std(durations) + 0.1)
                    
                    # Calculate feature contrast between segments (higher is better)
                    feature_contrasts = []
                    for i in range(len(segments) - 1):
                        # Simple scoring based on energy difference between consecutive segments
                        contrast = abs(segments[i]["energy"] - segments[i+1]["energy"]) 
                        feature_contrasts.append(contrast)
                    
                    avg_contrast = np.mean(feature_contrasts) if feature_contrasts else 0
                    
                    # Combined score (weighted sum)
                    score = (duration_consistency * 0.7) + (avg_contrast * 10 * 0.3)
                    
                    if score > best_score:
                        best_score = score
                        best_segments = segments
            except Exception as e:
                logger.warning(f"Error in segmentation with {n_segments} segments: {e}")
        
        # Use best segmentation or fall back to basic segmentation
        if best_segments:
            segments = best_segments
        else:
            # Fallback to simple segmentation if all attempts failed
            n_segments = max(2, min(5, int(duration / 10)))
            segment_duration = duration / n_segments
            segments = []
            
            for i in range(n_segments):
                start_time = i * segment_duration
                end_time = (i + 1) * segment_duration
                if end_time > duration:
                    end_time = duration
                
                segment_y = y[int(start_time * sr):int(end_time * sr)]
                segment_rms = np.mean(librosa.feature.rms(y=segment_y)[0]) if len(segment_y) > 0 else 0
                
                segments.append({
                    "start": float(start_time),
                    "end": float(end_time),
                    "duration": float(end_time - start_time),
                    "energy": float(segment_rms)
                })
        
        # Additional refinement: adjust segment boundaries to align with beats where possible
        try:
            # Get beat times
            _, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
            
            for i in range(len(segments) - 1):
                # Find closest beat to the boundary
                boundary = segments[i]["end"]
                if beats.size > 0:
                    closest_beat_idx = np.argmin(np.abs(beats - boundary))
                    closest_beat = beats[closest_beat_idx]
                    
                    # Only adjust if the beat is close enough (within 1 second)
                    if abs(closest_beat - boundary) < 1.0:
                        # Update segment boundaries
                        segments[i]["end"] = float(closest_beat)
                        segments[i]["duration"] = float(closest_beat - segments[i]["start"])
                        segments[i+1]["start"] = float(closest_beat)
                        segments[i+1]["duration"] = float(segments[i+1]["end"] - closest_beat)
        except Exception as e:
            logger.warning(f"Error adjusting segment boundaries to beats: {e}")
                
        return segments
    
    def analyze_track(self, track_id: str, audio_url: str) -> AudioAnalysisResult:
        """
        Analyze an audio track and extract features.
        
        Args:
            track_id: ID of the track
            audio_url: URL of the audio file
            
        Returns:
            AudioAnalysisResult: Analysis results
        """
        logger.info(f"Analyzing track {track_id} from {audio_url}")
        
        # For dev mode with small audio files, return mock data
        if DEV_MODE and not DEBUG_MODE:
            logger.info(f"DEV mode: Using mock analysis data for track {track_id}")
            
            # Create mock analysis data
            mock_beat_times = np.linspace(0, 60, 20).tolist()
            mock_waveform = {"data": np.sin(np.linspace(0, 60, 1000) * 10).tolist(), "sample_rate": 22050, "duration": 60}
            mock_segments = [
                {"start": 0, "end": 15, "duration": 15, "energy": 0.5},
                {"start": 15, "end": 30, "duration": 15, "energy": 0.8},
                {"start": 30, "end": 45, "duration": 15, "energy": 0.3},
                {"start": 45, "end": 60, "duration": 15, "energy": 0.7}
            ]
            
            return AudioAnalysisResult(
                track_id=track_id,
                bpm=120.0,
                energy_level=EnergyLevel.MEDIUM,
                beat_markers=mock_beat_times,
                waveform_data=mock_waveform,
                segments=mock_segments,
                key_moments=[10.0, 25.0, 40.0, 55.0],
                features={"mock_data": True}
            )
        
        try:
            # Create a temp directory for the audio file
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download the audio file
                filename = os.path.basename(audio_url.split("?")[0])
                audio_path = os.path.join(temp_dir, filename)
                self.download_audio(audio_url, audio_path)
                
                # Load the audio file
                y, sr = librosa.load(audio_path)
                
                # Calculate features
                tempo, beats, beat_strengths = self._extract_tempo_and_beats(y, sr)
                waveform_data = self._extract_waveform(y, sr)
                key_moments = self._extract_key_moments(y, sr)
                energy_level = self._detect_energy_level(y, sr)
                segments = self._detect_segments(y, sr)
                
                # Extract additional features for classification
                features = {}
                
                # Spectral features
                spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
                spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
                
                features["spectral_centroid"] = float(np.mean(spectral_centroid))
                features["spectral_rolloff"] = float(np.mean(spectral_rolloff))
                
                # Create result
                result = AudioAnalysisResult(
                    track_id=track_id,
                    bpm=float(tempo),
                    energy_level=energy_level,
                    beat_markers=beats.tolist(),
                    waveform_data=waveform_data,
                    segments=segments,
                    key_moments=key_moments,
                    features=features
                )
                
                logger.info(f"Completed analysis for track {track_id}: {tempo:.1f} BPM, {energy_level.value} energy")
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing track {track_id}: {e}")
            
            if DEBUG_MODE:
                # Return mock data in case of error
                logger.info(f"DEBUG mode: Using mock analysis data due to error")
                mock_beat_times = np.linspace(0, 60, 20).tolist()
                mock_waveform = {"data": np.sin(np.linspace(0, 60, 1000) * 10).tolist(), "sample_rate": 22050, "duration": 60}
                
                return AudioAnalysisResult(
                    track_id=track_id,
                    bpm=120.0,
                    energy_level=EnergyLevel.MEDIUM,
                    beat_markers=mock_beat_times,
                    waveform_data=mock_waveform,
                    segments=[],
                    key_moments=[],
                    features={"error": str(e)}
                )
            
            raise 