"""
Unit tests for video processing functionality.
"""
import os
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

from src.app.services.video.processor import (
    detect_beats, 
    apply_transition, 
    create_beat_synced_frames, 
    create_short,
    TransitionEffect
)

# Test beat detection
def test_detect_beats(test_music):
    """Test beat detection functionality."""
    # Mock librosa functions for testing
    with patch("librosa.load", return_value=(np.zeros(1000), 22050)):
        with patch("librosa.beat.beat_track", return_value=(120.0, np.array([0, 10, 20, 30]))):
            with patch("librosa.frames_to_time", return_value=np.array([0.0, 0.5, 1.0, 1.5])):
                with patch("librosa.onset.onset_strength", return_value=np.zeros(100)):
                    with patch("librosa.util.peak_pick", return_value=np.array([5, 15, 25])):
                        with patch("np.concatenate", return_value=np.array([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5])):
                            with patch("np.unique", return_value=np.array([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5])):
                                beat_times, tempo = detect_beats(test_music)
                                
                                # Verify results
                                assert tempo == 120.0
                                assert len(beat_times) > 0
                                assert isinstance(beat_times, np.ndarray)
                                assert beat_times[0] == 0.0
                                assert beat_times[-1] == 1.5

# Test transition effects
def test_apply_transition():
    """Test transition effects."""
    # Create simple test images
    img1 = np.zeros((100, 100, 3), dtype=np.uint8)
    img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
    
    # Test fade transition
    result = apply_transition(img1, img2, 0.5, TransitionEffect.FADE)
    assert result.shape == (100, 100, 3)
    # Middle of transition should be gray (127.5)
    assert 120 < np.mean(result) < 135
    
    # Test zoom transition
    result = apply_transition(img1, img2, 0.5, TransitionEffect.ZOOM)
    assert result.shape == (100, 100, 3)
    
    # Test slide transitions
    for effect in [TransitionEffect.SLIDE_LEFT, TransitionEffect.SLIDE_RIGHT, 
                  TransitionEffect.SLIDE_UP, TransitionEffect.SLIDE_DOWN]:
        result = apply_transition(img1, img2, 0.5, effect)
        assert result.shape == (100, 100, 3)
    
    # Test flash transition
    result = apply_transition(img1, img2, 0.5, TransitionEffect.FLASH)
    assert result.shape == (100, 100, 3)
    
    # Test blur transition
    result = apply_transition(img1, img2, 0.5, TransitionEffect.BLUR)
    assert result.shape == (100, 100, 3)

# Test frame creation
def test_create_beat_synced_frames(test_images):
    """Test creation of beat synchronized frames."""
    # Mock beat times
    beat_times = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    
    # Mock image loading
    img = np.zeros((1920, 1080, 3), dtype=np.uint8)
    with patch("cv2.imread", return_value=img):
        with patch("cv2.resize", return_value=img):
            with patch("src.app.services.video.processor.apply_transition", return_value=img):
                frames = create_beat_synced_frames(test_images, beat_times, fps=30, duration=3)
                
                # Verify results
                assert len(frames) > 0
                assert frames[0].shape == (1920, 1080, 3)

# Test full video creation
def test_create_short(test_images, test_music):
    """Test complete video creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "output.mp4")
        
        # Mock all necessary functions
        with patch("src.app.services.video.processor.detect_beats", 
                  return_value=(np.array([0.0, 0.5, 1.0, 1.5, 2.0]), 120.0)):
            with patch("src.app.services.video.processor.create_beat_synced_frames", 
                      return_value=[np.zeros((1080, 1920, 3), dtype=np.uint8) for _ in range(10)]):
                with patch("cv2.VideoWriter") as mock_video_writer:
                    mock_writer_instance = MagicMock()
                    mock_video_writer.return_value = mock_writer_instance
                    
                    with patch("subprocess.run") as mock_subprocess:
                        # Call the function
                        result = create_short(test_images, test_music, output_path, duration=3)
                        
                        # Verify the function calls
                        mock_video_writer.assert_called_once()
                        mock_writer_instance.write.assert_called()
                        mock_writer_instance.release.assert_called_once()
                        mock_subprocess.assert_called_once()
                        
                        # Verify the result
                        assert result == output_path 