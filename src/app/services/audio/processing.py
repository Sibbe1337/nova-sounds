"""
Basic audio processing utilities for the YouTube Shorts Machine.
"""
import os
import logging
import numpy as np
import librosa
from typing import List, Dict, Any, Tuple, Optional
import tempfile
import requests

# Set up logging
logger = logging.getLogger(__name__)

def extract_beat_markers(
    audio_path: str, 
    start_time: float = 0.0, 
    duration: Optional[float] = None
) -> List[float]:
    """
    Extract beat markers from an audio file.
    
    Args:
        audio_path: Path to the audio file
        start_time: Start time in seconds
        duration: Duration in seconds to analyze (None for full file)
        
    Returns:
        List of beat timestamps in seconds
    """
    try:
        logger.info(f"Extracting beat markers from {audio_path}")
        
        # Load audio file with offset and duration
        offset = max(0, start_time)
        y, sr = librosa.load(
            audio_path, 
            offset=offset,
            duration=duration
        )
        
        # Get tempo and beat frames
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        
        # Convert beat frames to time
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        # Add the offset to get the actual timestamps in the full audio
        beat_times = beat_times + offset
        
        logger.debug(f"Extracted {len(beat_times)} beats at tempo {tempo:.1f} BPM")
        return beat_times.tolist()
    
    except Exception as e:
        logger.error(f"Error extracting beat markers: {e}")
        # Return empty list on error
        return []

def get_beat_timestamps(
    audio_data: np.ndarray,
    sample_rate: int,
    start_time: float = 0.0
) -> List[float]:
    """
    Extract beat timestamps from audio data.
    
    Args:
        audio_data: Audio time series (numpy array)
        sample_rate: Sample rate of the audio
        start_time: Start time in seconds
        
    Returns:
        List of beat timestamps in seconds
    """
    try:
        # Get tempo and beat frames
        tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
        
        # Convert beat frames to time
        beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
        
        # Add the offset to get the actual timestamps
        beat_times = beat_times + start_time
        
        return beat_times.tolist()
    
    except Exception as e:
        logger.error(f"Error getting beat timestamps: {e}")
        # Return empty list on error
        return []

def detect_bpm(audio_path: str) -> float:
    """
    Detect the BPM (beats per minute) of an audio file.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Detected BPM
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_path)
        
        # Get tempo (BPM)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        return float(tempo)
    
    except Exception as e:
        logger.error(f"Error detecting BPM: {e}")
        # Return a default BPM on error
        return 120.0

def download_audio_from_url(url: str) -> Optional[str]:
    """
    Download audio from a URL to a temporary file.
    
    Args:
        url: URL of the audio file
        
    Returns:
        Path to the downloaded file or None on error
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        temp_file.close()
        
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return temp_path
    
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        return None 