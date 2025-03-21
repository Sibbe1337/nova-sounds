"""
Audio processing services for the YouTube Shorts Machine.
"""
from .processing import extract_beat_markers, get_beat_timestamps
from .waveform import generate_waveform, generate_waveform_image, get_normalized_waveform_data 