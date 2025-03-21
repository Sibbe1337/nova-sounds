"""
Waveform visualization module for the YouTube Shorts Machine.
"""
import os
import tempfile
import numpy as np
import logging
import base64
from io import BytesIO
from typing import List, Optional, Tuple
import librosa
import librosa.display
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import json
from pathlib import Path

from src.app.core.settings import DEV_MODE
from src.app.services.gcs.storage import get_music_path, download_file

# Configure logging
logger = logging.getLogger(__name__)

def get_waveform_data(track_id: str, resolution: int = 1000, cache: bool = True) -> List[float]:
    """
    Generate waveform data for visualization from audio file.
    
    Args:
        track_id: Track ID or filename
        resolution: Number of points in the waveform
        cache: Whether to cache the waveform data
        
    Returns:
        List of amplitude values normalized between 0 and 1
    """
    # Ensure resolution is always positive
    resolution = max(1, resolution)
    
    # Check if cached data exists
    cache_dir = Path("data/cache/waveforms")
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_file = cache_dir / f"{track_id}_waveform.json"
    
    if cache and cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading cached waveform: {e}")
    
    # If we're in DEV_MODE and can't get the actual file, return mock data
    if DEV_MODE and (not os.path.exists(track_id) and 'mock' not in track_id):
        logger.info(f"Generating mock waveform for {track_id} in DEV_MODE")
        waveform = generate_mock_waveform(resolution)
        
        # Cache the mock data
        if cache:
            with open(cache_file, 'w') as f:
                json.dump(waveform, f)
                
        return waveform
    
    # Get the audio file
    try:
        if os.path.exists(track_id):
            audio_path = track_id
        else:
            audio_path = get_music_path(track_id)
            
            if not audio_path or not os.path.exists(audio_path):
                # Try to download the file
                audio_path = download_music_file(track_id)
                
                if not audio_path:
                    logger.error(f"Could not find or download audio file for {track_id}")
                    return generate_mock_waveform(resolution)
        
        # Generate waveform
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        
        # Ensure we have audio data
        if len(y) == 0:
            logger.warning(f"Empty audio data for {track_id}, generating mock waveform")
            return generate_mock_waveform(resolution)
        
        # Resample to target resolution, use RMS energy for better visualization
        # Ensure hop_length is at least 1 to avoid division by zero
        hop_length = max(1, len(y) // resolution)
        
        # Ensure we handle any negative numbers that might come from API requests
        safe_resolution = abs(resolution)
        if safe_resolution != resolution:
            logger.warning(f"Received negative resolution ({resolution}), using absolute value")
        
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # If resolution is higher than the actual RMS length, pad it
        if len(rms) < safe_resolution:
            rms = np.pad(rms, (0, safe_resolution - len(rms)))
        
        # If resolution is lower, downsample
        if len(rms) > safe_resolution:
            # Use a simple averaging approach for downsampling
            points_per_segment = max(1, len(rms) // safe_resolution)
            rms = np.array([np.mean(rms[i:i+points_per_segment]) for i in range(0, len(rms), points_per_segment)])
            rms = rms[:safe_resolution]  # Ensure exact size
        
        # Normalize between 0 and 1
        if np.max(rms) > 0:
            rms = rms / np.max(rms)
        
        waveform = rms.tolist()
        
        # Cache the waveform data
        if cache:
            with open(cache_file, 'w') as f:
                json.dump(waveform, f)
                
        return waveform
        
    except Exception as e:
        logger.error(f"Error generating waveform: {e}")
        return generate_mock_waveform(resolution)

def generate_mock_waveform(resolution: int = 1000) -> List[float]:
    """
    Generate a mock waveform for development and testing.
    
    Args:
        resolution: Number of points in the waveform
        
    Returns:
        List of amplitude values
    """
    # Generate a more realistic-looking waveform with different sections
    np.random.seed(42)  # For reproducibility
    
    # Create several sections with different characteristics
    sections = []
    
    # Intro - gradually increasing amplitude
    intro_len = resolution // 8
    intro = np.linspace(0.1, 0.5, intro_len) * np.random.uniform(0.7, 1.0, intro_len)
    sections.append(intro)
    
    # Verse - medium amplitude with some variation
    verse_len = resolution // 4
    verse = np.random.uniform(0.3, 0.6, verse_len)
    sections.append(verse)
    
    # Chorus - higher amplitude
    chorus_len = resolution // 4
    chorus = np.random.uniform(0.6, 1.0, chorus_len)
    sections.append(chorus)
    
    # Verse again
    sections.append(verse)
    
    # Final chorus and outro
    sections.append(chorus)
    outro_len = resolution - sum(len(s) for s in sections)
    outro = np.linspace(0.8, 0.1, outro_len) * np.random.uniform(0.7, 1.0, outro_len)
    sections.append(outro)
    
    # Combine all sections
    waveform = np.concatenate(sections)
    
    # Add some smaller peaks and valleys for realism
    fine_detail = np.random.uniform(0.85, 1.15, resolution)
    waveform = waveform * fine_detail
    
    # Apply a smoothing filter
    window_size = 10
    smoothed = np.convolve(waveform, np.ones(window_size)/window_size, mode='same')
    
    # Ensure values are between 0 and 1
    smoothed = np.clip(smoothed, 0, 1)
    
    return smoothed.tolist()

def download_music_file(track_id: str) -> Optional[str]:
    """
    Download a music file from storage.
    
    Args:
        track_id: Track ID or filename
        
    Returns:
        Path to the downloaded file or None if failed
    """
    try:
        # Create a temporary directory for the download
        temp_dir = Path("data/cache/audio")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Determine the output path
        output_path = temp_dir / f"{track_id}"
        
        # Download the file
        try:
            downloaded_path = download_file(track_id, str(output_path))
            
            if os.path.exists(downloaded_path):
                return downloaded_path
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            
        return None
    except Exception as e:
        logger.error(f"Error in download_music_file: {e}")
        return None

def get_normalized_waveform_data(track_id: str, resolution: int = 1000) -> List[float]:
    """
    Get normalized waveform data for a track.
    
    Args:
        track_id: Track ID or filename
        resolution: Number of points in the waveform
        
    Returns:
        List of normalized amplitude values
    """
    return get_waveform_data(track_id, resolution)

def generate_waveform(track_id: str, output_path: str, width: int = 800, height: int = 200, 
                     color: str = "#1DB954") -> str:
    """
    Generate a waveform image file from audio.
    
    Args:
        track_id: Track ID or filename
        output_path: Path to save the waveform image
        width: Width of the waveform image
        height: Height of the waveform image
        color: Color of the waveform
        
    Returns:
        Path to the generated waveform image
    """
    try:
        # Get waveform data
        waveform_data = get_waveform_data(track_id)
        
        # Create a new figure with the specified size
        fig = Figure(figsize=(width/100, height/100), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plot the waveform
        ax.plot(waveform_data, color=color, linewidth=1.5)
        
        # Set the axis limits
        ax.set_ylim(0, 1)
        
        # Remove axis and ticks
        ax.axis('off')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Remove margins
        fig.tight_layout(pad=0)
        
        # Save the figure
        fig.savefig(output_path, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating waveform image: {e}")
        
        # Create a mock waveform image in case of error
        fig = Figure(figsize=(width/100, height/100), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(generate_mock_waveform(), color=color, linewidth=1.5)
        ax.set_ylim(0, 1)
        ax.axis('off')
        fig.tight_layout(pad=0)
        fig.savefig(output_path, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
        
        return output_path

def generate_waveform_image(track_id: str, width: int = 800, height: int = 200, 
                           color: str = "#1DB954") -> Optional[str]:
    """
    Generate a waveform image for a track and return as base64 string.
    
    Args:
        track_id: Track ID or filename
        width: Width of the waveform image
        height: Height of the waveform image
        color: Color of the waveform
        
    Returns:
        Base64 encoded PNG image
    """
    try:
        # Get waveform data
        waveform_data = get_waveform_data(track_id)
        
        # Create a new figure with the specified size
        fig = Figure(figsize=(width/100, height/100), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plot the waveform
        ax.plot(waveform_data, color=color, linewidth=1.5)
        
        # Set the axis limits
        ax.set_ylim(0, 1)
        
        # Remove axis and ticks
        ax.axis('off')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Remove margins
        fig.tight_layout(pad=0)
        
        # Convert to PNG image
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
        buf.seek(0)
        
        # Encode as base64 string
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{image_base64}"
    
    except Exception as e:
        logger.error(f"Error generating waveform image: {e}")
        return None

def generate_waveform_with_beats(
    audio_path: str,
    width: int = 800, 
    height: int = 200,
    waveform_color: str = "#3498db",
    beat_color: str = "#e74c3c",
    background_color: str = "#ffffff",
    n_samples: int = 200
) -> str:
    """
    Generate waveform visualization with beat markers.
    
    Args:
        audio_path: Path to audio file
        width: Image width in pixels
        height: Image height in pixels
        waveform_color: Waveform color (hex code)
        beat_color: Beat marker color (hex code)
        background_color: Background color (hex code)
        n_samples: Number of data points to return
        
    Returns:
        str: Base64-encoded image data
    """
    try:
        # Load audio and extract beat positions
        y, sr = librosa.load(audio_path, sr=None)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        
        # Convert to time
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        # Generate visualization
        fig = Figure(figsize=(width/100, height/100), dpi=100, facecolor=background_color)
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Plot waveform
        librosa.display.waveshow(y, sr=sr, ax=ax, color=waveform_color, alpha=0.8)
        
        # Plot beat markers
        for beat_time in beat_times:
            ax.axvline(beat_time, color=beat_color, alpha=0.7, linewidth=1)
        
        # Configure appearance
        ax.set_facecolor(background_color)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Render to buffer
        buf = BytesIO()
        fig.tight_layout(pad=0)
        fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
    except Exception as e:
        logger.error(f"Error generating waveform with beats: {e}")
        # Return a data URL for a small transparent image
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

def generate_spectrogram_image(
    audio_path: str,
    width: int = 800, 
    height: int = 400,
    cmap: str = 'viridis',
    format: str = 'png'
) -> str:
    """
    Generate a spectrogram visualization as an image.
    
    Args:
        audio_path: Path to audio file
        width: Image width in pixels
        height: Image height in pixels
        cmap: Colormap name
        format: Output image format ('png' or 'svg')
        
    Returns:
        str: Base64-encoded image data
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=None)
        
        # Compute spectrogram
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
        S_dB = librosa.power_to_db(S, ref=np.max)
        
        # Set up figure
        fig = Figure(figsize=(width/100, height/100), dpi=100)
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Plot spectrogram
        img = librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', ax=ax, cmap=cmap)
        
        # Add colorbar
        fig.colorbar(img, ax=ax, format='%+2.0f dB')
        
        # Set labels
        ax.set_title('Mel-frequency spectrogram')
        
        # Render to buffer
        buf = BytesIO()
        fig.tight_layout()
        
        # Save in specified format
        if format.lower() == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
            return f"data:image/svg+xml;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        else:
            fig.savefig(buf, format='png', bbox_inches='tight')
            return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
    except Exception as e:
        logger.error(f"Error generating spectrogram: {e}")
        # Return a data URL for a small transparent image
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" 