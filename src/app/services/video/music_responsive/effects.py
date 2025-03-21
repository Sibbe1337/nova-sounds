"""
Advanced music-responsive effects for video enhancement.

This module provides a collection of effects that respond to music features
to create dynamic, music-synchronized videos.
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict, Any, Optional, Union, Callable
import math
import random
from enum import Enum

from src.app.services.video.music_responsive.enums import MusicFeature, EffectType
from src.app.services.video.music_responsive.analyzer import MusicAnalyzer

# Set up logger
logger = logging.getLogger(__name__)

class MusicResponsiveEffect:
    """Base class for music-responsive visual effects."""
    
    def __init__(self, 
                 music_analyzer: MusicAnalyzer,
                 feature: MusicFeature = MusicFeature.BEATS,
                 intensity: float = 1.0):
        """
        Initialize the effect.
        
        Args:
            music_analyzer: The music analyzer to use
            feature: The music feature to respond to
            intensity: Effect intensity multiplier
        """
        self.music_analyzer = music_analyzer
        self.feature = feature
        self.intensity = intensity
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        """
        Apply the effect to a frame at the given time.
        
        Args:
            frame: Input video frame
            time_sec: Current video time in seconds
            
        Returns:
            np.ndarray: Processed frame
        """
        # Base implementation does nothing
        return frame
    
    def get_feature_value(self, time_sec: float) -> float:
        """
        Get the current feature value at the given time.
        
        Args:
            time_sec: Current video time in seconds
            
        Returns:
            float: Feature value between 0.0 and 1.0
        """
        return self.music_analyzer.get_feature_at_time(self.feature, time_sec)

class TransitionEffect(MusicResponsiveEffect):
    """Effect that creates smooth transitions between segments based on beat proximity."""
    
    def __init__(self, 
                 music_analyzer: MusicAnalyzer,
                 intensity: float = 1.0,
                 transition_duration: float = 0.5,
                 prev_frame: Optional[np.ndarray] = None):
        """
        Initialize the transition effect.
        
        Args:
            music_analyzer: The music analyzer to use
            intensity: Effect intensity multiplier
            transition_duration: Duration of the transition in seconds
            prev_frame: Previous frame for the transition (if None, will be set on first apply)
        """
        super().__init__(music_analyzer, MusicFeature.BEATS, intensity)
        self.transition_duration = transition_duration
        self.prev_frame = prev_frame
        self.current_frame = None
        self.is_transitioning = False
        self.transition_start_time = 0
        self.next_beat_time = 0
        self.last_beat_check_time = 0
        self.transition_type = random.choice(['crossfade', 'zoom', 'slide'])
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        """
        Apply transition effect based on beat proximity.
        
        Args:
            frame: Input video frame
            time_sec: Current video time in seconds
            
        Returns:
            np.ndarray: Processed frame with transition applied if needed
        """
        # Initialize previous frame if not set
        if self.prev_frame is None:
            self.prev_frame = frame.copy()
            self.current_frame = frame.copy()
            return frame
        
        # Only check for new beats every 0.1 seconds for performance
        if time_sec - self.last_beat_check_time > 0.1:
            self.last_beat_check_time = time_sec
            
            # Get time to next beat
            time_to_next_beat = self.music_analyzer.get_time_to_next_beat(time_sec)
            
            # Check if we're approaching a beat and should start transition
            if time_to_next_beat < self.transition_duration and not self.is_transitioning:
                self.is_transitioning = True
                self.transition_start_time = time_sec
                self.next_beat_time = time_sec + time_to_next_beat
                # Save current frame as previous frame for transition
                self.prev_frame = self.current_frame.copy()
                # Set new current frame
                self.current_frame = frame.copy()
                # Choose a random transition type
                self.transition_type = random.choice(['crossfade', 'zoom', 'slide', 'wipe'])
        
        # Update current frame if not in transition
        if not self.is_transitioning:
            self.current_frame = frame.copy()
            return frame
        
        # Calculate transition progress (0.0 to 1.0)
        total_transition_time = self.next_beat_time - self.transition_start_time
        if total_transition_time <= 0:
            self.is_transitioning = False
            return frame
        
        progress = min(1.0, (time_sec - self.transition_start_time) / total_transition_time)
        
        # Apply the selected transition effect
        if progress >= 1.0:
            self.is_transitioning = False
            return frame
        
        # Apply transition based on type
        if self.transition_type == 'crossfade':
            return self._apply_crossfade(progress)
        elif self.transition_type == 'zoom':
            return self._apply_zoom_transition(progress)
        elif self.transition_type == 'slide':
            return self._apply_slide_transition(progress)
        elif self.transition_type == 'wipe':
            return self._apply_wipe_transition(progress)
        else:
            return self._apply_crossfade(progress)
    
    def _apply_crossfade(self, progress: float) -> np.ndarray:
        """Apply a crossfade transition between frames."""
        return cv2.addWeighted(self.current_frame, progress, self.prev_frame, 1.0 - progress, 0)
    
    def _apply_zoom_transition(self, progress: float) -> np.ndarray:
        """Apply a zoom transition between frames."""
        # Zoom out from previous frame
        h, w = self.prev_frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Scale factor for zoom (start at 1.0, end at 1.3)
        scale_factor = 1.0 + (0.3 * progress * self.intensity)
        
        # Create transformation matrix for zoom
        M = cv2.getRotationMatrix2D((center_x, center_y), 0, scale_factor)
        
        # Apply zoom to previous frame
        zoomed_prev = cv2.warpAffine(self.prev_frame, M, (w, h))
        
        # Crossfade between zoomed previous frame and current frame
        return cv2.addWeighted(self.current_frame, progress, zoomed_prev, 1.0 - progress, 0)
    
    def _apply_slide_transition(self, progress: float) -> np.ndarray:
        """Apply a slide transition between frames."""
        h, w = self.prev_frame.shape[:2]
        result = np.zeros_like(self.prev_frame)
        
        # Determine slide direction (0: left, 1: right, 2: up, 3: down)
        direction = hash(str(self.next_beat_time)) % 4
        
        if direction == 0:  # Slide to left
            offset = int(w * progress)
            # Part of previous frame
            if offset < w:
                result[:, :w-offset] = self.prev_frame[:, offset:]
            # Part of current frame
            result[:, w-offset:] = self.current_frame[:, :offset]
        elif direction == 1:  # Slide to right
            offset = int(w * progress)
            # Part of previous frame
            if offset < w:
                result[:, offset:] = self.prev_frame[:, :w-offset]
            # Part of current frame
            result[:, :offset] = self.current_frame[:, w-offset:]
        elif direction == 2:  # Slide up
            offset = int(h * progress)
            # Part of previous frame
            if offset < h:
                result[:h-offset, :] = self.prev_frame[offset:, :]
            # Part of current frame
            result[h-offset:, :] = self.current_frame[:offset, :]
        else:  # Slide down
            offset = int(h * progress)
            # Part of previous frame
            if offset < h:
                result[offset:, :] = self.prev_frame[:h-offset, :]
            # Part of current frame
            result[:offset, :] = self.current_frame[h-offset:, :]
        
        return result
    
    def _apply_wipe_transition(self, progress: float) -> np.ndarray:
        """Apply a wipe transition between frames."""
        h, w = self.prev_frame.shape[:2]
        result = np.zeros_like(self.prev_frame)
        
        # Create transition mask
        mask = np.zeros((h, w), dtype=np.float32)
        
        # Determine wipe direction (0: left to right, 1: right to left, 2: top to bottom, 3: bottom to top)
        direction = hash(str(self.next_beat_time + 0.1)) % 4
        
        if direction == 0:  # Left to right
            edge_pos = int(w * progress)
            mask[:, :edge_pos] = 1.0
        elif direction == 1:  # Right to left
            edge_pos = int(w * (1.0 - progress))
            mask[:, edge_pos:] = 1.0
        elif direction == 2:  # Top to bottom
            edge_pos = int(h * progress)
            mask[:edge_pos, :] = 1.0
        else:  # Bottom to top
            edge_pos = int(h * (1.0 - progress))
            mask[edge_pos:, :] = 1.0
        
        # Expand mask dimensions to match the image
        mask_3ch = np.stack([mask] * 3, axis=2)
        
        # Blend images using the mask
        result = self.current_frame * mask_3ch + self.prev_frame * (1.0 - mask_3ch)
        
        return result.astype(np.uint8)

class AnticipationEffect(MusicResponsiveEffect):
    """Effect that builds anticipation before beats by subtly preparing for the impact."""
    
    def __init__(self, 
                 music_analyzer: MusicAnalyzer,
                 intensity: float = 1.0,
                 anticipation_color: Tuple[int, int, int] = (20, 20, 80)):
        """
        Initialize the anticipation effect.
        
        Args:
            music_analyzer: The music analyzer to use
            intensity: Effect intensity multiplier
            anticipation_color: Color tint during anticipation (BGR format)
        """
        super().__init__(music_analyzer, MusicFeature.BEAT_ANTICIPATION, intensity)
        self.anticipation_color = anticipation_color
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        feature_val = self.get_feature_value(time_sec)
        
        # Skip if not in anticipation phase
        if feature_val < 0.1:
            return frame
        
        result = frame.copy()
        
        # Calculate time to next beat
        time_to_beat = self.music_analyzer.get_time_to_next_beat(time_sec)
        
        # Apply subtle zoom-out before the beat hits (preparing for impact)
        if time_to_beat < self.music_analyzer.anticipation_time:
            # Scale factor decreases as we approach the beat (subtle zoom out)
            scale_factor = 1.0 - (feature_val * 0.05 * self.intensity)
            
            h, w = frame.shape[:2]
            center_x, center_y = w // 2, h // 2
            
            # Apply zoom out
            M = cv2.getRotationMatrix2D((center_x, center_y), 0, scale_factor)
            result = cv2.warpAffine(result, M, (w, h))
            
            # Add subtle color tint that increases as we approach the beat
            tint = np.ones_like(result) * np.array(self.anticipation_color, dtype=np.uint8)
            tint_alpha = feature_val * 0.15 * self.intensity
            result = cv2.addWeighted(result, 1.0 - tint_alpha, tint, tint_alpha, 0)
            
            # Add subtle vignette that increases as we approach the beat
            y, x = np.ogrid[:h, :w]
            center_y, center_x = h / 2, w / 2
            dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_dist = np.sqrt(center_x**2 + center_y**2)
            
            # Normalize distance and create vignette mask
            norm_dist = dist_from_center / max_dist
            vignette_strength = feature_val * 0.3 * self.intensity
            mask = 1.0 - (norm_dist ** 2) * vignette_strength
            mask = np.clip(mask, 0, 1)
            
            # Apply vignette
            mask = np.dstack([mask] * 3)
            result = (result * mask).astype(np.uint8)
        
        return result

class PulseEffect(MusicResponsiveEffect):
    """Effect that creates a pulsing zoom synced to music."""
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        feature_val = self.get_feature_value(time_sec)
        
        # Scale based on intensity
        scale_factor = 1.0 + (feature_val * 0.1 * self.intensity)
        
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Create transformation matrix for zoom
        M = cv2.getRotationMatrix2D((center_x, center_y), 0, scale_factor)
        
        # Apply zoom effect
        result = cv2.warpAffine(frame, M, (w, h))
        
        return result

class ColorShiftEffect(MusicResponsiveEffect):
    """Effect that shifts colors based on music features."""
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        feature_val = self.get_feature_value(time_sec)
        
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Shift hue based on feature value
        hue_shift = int(feature_val * 180 * self.intensity) % 180
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180
        
        # Enhance saturation on beats
        if self.feature == MusicFeature.BEATS and feature_val > 0.8:
            hsv[:, :, 1] = np.minimum(255, hsv[:, :, 1] * (1 + 0.2 * self.intensity))
        
        # Convert back to BGR
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return result

class ShakeEffect(MusicResponsiveEffect):
    """Effect that creates camera shake based on music energy."""
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        feature_val = self.get_feature_value(time_sec)
        
        # Only apply shake effect for strong beats/onsets
        if feature_val < 0.7:
            return frame
        
        # Calculate shake amount based on feature value and intensity
        shake_amount = int(feature_val * 10 * self.intensity)
        
        if shake_amount <= 0:
            return frame
        
        # Apply random translation for shake effect
        h, w = frame.shape[:2]
        
        # Random translation matrix
        dx = random.randint(-shake_amount, shake_amount)
        dy = random.randint(-shake_amount, shake_amount)
        
        # Create translation matrix
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        
        # Apply translation
        result = cv2.warpAffine(frame, M, (w, h))
        
        return result

class FlashEffect(MusicResponsiveEffect):
    """Effect that creates brief flashes on strong beats or percussion hits."""
    
    def __init__(self, 
                 music_analyzer: MusicAnalyzer,
                 feature: MusicFeature = MusicFeature.ONSETS,
                 intensity: float = 1.0,
                 threshold: float = 0.8,
                 flash_color: Tuple[int, int, int] = (255, 255, 255)):
        """
        Initialize the flash effect.
        
        Args:
            music_analyzer: The music analyzer to use
            feature: The music feature to respond to
            intensity: Effect intensity multiplier
            threshold: Threshold above which flashes are triggered
            flash_color: Color of the flash (BGR format)
        """
        super().__init__(music_analyzer, feature, intensity)
        self.threshold = threshold
        self.flash_color = flash_color
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        feature_val = self.get_feature_value(time_sec)
        
        # Only flash when feature value exceeds threshold
        if feature_val < self.threshold:
            return frame
        
        # Calculate flash intensity based on feature value and effect intensity
        flash_intensity = (feature_val - self.threshold) / (1.0 - self.threshold)
        flash_intensity *= self.intensity
        
        # Limit flash intensity to 0.7 to avoid completely whiting out the image
        flash_intensity = min(0.7, flash_intensity)
        
        # Create flash overlay
        flash = np.ones_like(frame) * np.array(self.flash_color, dtype=np.uint8)
        
        # Blend the flash with the original frame
        result = cv2.addWeighted(frame, 1.0 - flash_intensity, flash, flash_intensity, 0)
        
        return result

class WarpEffect(MusicResponsiveEffect):
    """Effect that creates dynamic warping based on music energy."""
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        feature_val = self.get_feature_value(time_sec)
        
        # Skip if feature value is too low
        if feature_val < 0.3:
            return frame
        
        # Calculate warp amount based on feature value and intensity
        warp_amount = int(feature_val * 20 * self.intensity)
        
        if warp_amount <= 0:
            return frame
        
        # Get image dimensions
        h, w = frame.shape[:2]
        
        # Create meshgrid for the frame
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        
        # Calculate distance from center for radial warp
        center_x, center_y = w // 2, h // 2
        dx = x - center_x
        dy = y - center_y
        
        # Calculate radius and angle for polar coordinates
        radius = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)
        
        # Apply sinusoidal warp based on radius and feature value
        radius_warp = radius + warp_amount * np.sin(radius * 0.01 + time_sec * 5)
        
        # Convert back to cartesian coordinates
        x_warp = center_x + radius_warp * np.cos(angle)
        y_warp = center_y + radius_warp * np.sin(angle)
        
        # Clip coordinates to valid image bounds
        x_warp = np.clip(x_warp, 0, w - 1).astype(np.float32)
        y_warp = np.clip(y_warp, 0, h - 1).astype(np.float32)
        
        # Create maps for remap function
        map_x = x_warp
        map_y = y_warp
        
        # Apply remapping
        result = cv2.remap(frame, map_x, map_y, interpolation=cv2.INTER_LINEAR)
        
        return result

class VignetteEffect(MusicResponsiveEffect):
    """Effect that creates a dynamic vignette that responds to music energy."""
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        feature_val = self.get_feature_value(time_sec)
        
        # Calculate vignette amount based on feature value and intensity
        # Invert the feature value so that high energy means less vignette
        vignette_strength = 1.0 - (feature_val * self.intensity * 0.7)
        vignette_strength = max(0.3, min(0.9, vignette_strength))
        
        # Get image dimensions
        h, w = frame.shape[:2]
        
        # Create radial gradient for vignette effect
        y, x = np.ogrid[:h, :w]
        center_y, center_x = h / 2, w / 2
        
        # Calculate normalized distance from center
        dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        # Normalize distance to 0.0-1.0 range
        norm_dist = dist_from_center / max_dist
        
        # Create vignette mask with smooth falloff
        mask = 1.0 - (norm_dist ** 2) * vignette_strength
        mask = np.clip(mask, 0, 1)
        
        # Expand mask dimensions to match the image
        mask = np.dstack([mask] * 3)
        
        # Apply vignette
        result = (frame * mask).astype(np.uint8)
        
        return result

class GlitchEffect(MusicResponsiveEffect):
    """Effect that creates digital glitches based on percussion hits."""
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        feature_val = self.get_feature_value(time_sec)
        
        # Only apply glitch for strong percussion hits
        if feature_val < 0.85:
            return frame
        
        # Calculate glitch amount based on feature value and intensity
        glitch_amount = int(feature_val * 50 * self.intensity)
        
        if glitch_amount <= 0:
            return frame
        
        # Get image dimensions
        h, w = frame.shape[:2]
        
        # Make a copy of the frame to modify
        result = frame.copy()
        
        # Apply several random glitch effects
        for _ in range(int(feature_val * 10)):
            # Choose a random effect type
            effect_type = random.randint(0, 3)
            
            if effect_type == 0:
                # Horizontal line shift
                y = random.randint(0, h - 1)
                shift = random.randint(-glitch_amount, glitch_amount)
                line = result[y, :].copy()
                result[y, :] = np.roll(line, shift, axis=0)
                
            elif effect_type == 1:
                # RGB channel shift
                channel = random.randint(0, 2)
                shift_x = random.randint(-glitch_amount, glitch_amount)
                shift_y = random.randint(-glitch_amount // 2, glitch_amount // 2)
                
                # Shift the selected channel
                result[:, :, channel] = np.roll(result[:, :, channel], shift_x, axis=1)
                result[:, :, channel] = np.roll(result[:, :, channel], shift_y, axis=0)
                
            elif effect_type == 2:
                # Block displacement
                block_h = random.randint(10, h // 5)
                block_w = random.randint(10, w // 5)
                y1 = random.randint(0, h - block_h - 1)
                x1 = random.randint(0, w - block_w - 1)
                y2 = random.randint(0, h - block_h - 1)
                x2 = random.randint(0, w - block_w - 1)
                
                # Copy block from one position to another
                result[y2:y2+block_h, x2:x2+block_w] = frame[y1:y1+block_h, x1:x1+block_w]
                
            elif effect_type == 3:
                # Color quantization in a block
                block_h = random.randint(h // 10, h // 3)
                block_w = w
                y = random.randint(0, h - block_h - 1)
                
                # Quantize colors in the block
                block = result[y:y+block_h, :]
                block = block // (random.randint(2, 8) * 32) * (random.randint(2, 8) * 32)
                result[y:y+block_h, :] = block
        
        return result

class AdvancedTransitionSystem(MusicResponsiveEffect):
    """
    Advanced system for intelligent music-driven transitions between video segments.
    Uses music structure analysis to place transitions at musically appropriate moments.
    """
    
    def __init__(self, 
                 music_analyzer: MusicAnalyzer,
                 intensity: float = 1.0,
                 transition_duration: float = 0.5,
                 min_transition_interval: float = 2.0,
                 prev_frame: Optional[np.ndarray] = None):
        """
        Initialize the advanced transition system.
        
        Args:
            music_analyzer: The music analyzer to use
            intensity: Effect intensity multiplier
            transition_duration: Duration of the transition in seconds
            min_transition_interval: Minimum time between transitions
            prev_frame: Previous frame for the transition
        """
        super().__init__(music_analyzer, MusicFeature.BEATS, intensity)
        self.transition_duration = transition_duration
        self.min_transition_interval = min_transition_interval
        self.prev_frame = prev_frame
        self.current_frame = None
        self.next_frame = None
        self.is_transitioning = False
        self.transition_start_time = 0
        self.transition_progress = 0.0
        self.beat_markers = music_analyzer.beat_times if music_analyzer.beat_times is not None else []
        self.key_moments = []
        self.transition_points = []
        self.last_transition_time = -10.0  # Set to negative to allow initial transition
        self.transition_type = "crossfade"  # Default type
        
        # Store beat pattern info from analyzer
        self.beat_patterns = music_analyzer.beat_patterns
        self.phrase_boundaries = music_analyzer.phrase_boundaries
        self.beat_drops = music_analyzer.beat_drops
        self.beat_buildups = music_analyzer.beat_buildups
        self.groove_type = music_analyzer.groove_type
        
        # Map transition types to music characteristics and initialize counters
        self.transition_map = {
            # Format: transition_name: (weight, used_count)
            "crossfade": (1.0, 0),
            "zoom": (1.0, 0),
            "slide": (1.0, 0),
            "wipe": (1.0, 0),
            "dissolve": (1.0, 0),
            "fade_to_black": (1.0, 0),
            "radial": (0.8, 0),
            "spiral": (0.7, 0),
            "pixelate": (0.6, 0),
            "spin": (0.7, 0),
            "flash_fade": (0.8, 0),
            "glitch": (0.5, 0)
        }
        
        # Initialize transition schedule based on beat patterns and music structure
        self._initialize_transition_schedule()
    
    def _initialize_transition_schedule(self):
        """
        Initialize the transition schedule based on music structure analysis.
        Identifies key moments (phrase boundaries, drops, etc.) for transitions.
        """
        # Start with phrase boundaries as primary transition points
        if self.phrase_boundaries and len(self.phrase_boundaries) > 0:
            self.transition_points = list(self.phrase_boundaries)
        
        # Add drops as high-impact transition points
        if self.beat_drops and len(self.beat_drops) > 0:
            for drop in self.beat_drops:
                # Check if this drop is close to an existing transition point
                if not any(abs(drop - point) < 0.5 for point in self.transition_points):
                    self.transition_points.append(drop)
        
        # Ensure we have at least some transition points
        if not self.transition_points and self.beat_markers and len(self.beat_markers) > 0:
            # Use every 8th beat as a fallback
            for i in range(0, len(self.beat_markers), 8):
                if i < len(self.beat_markers):
                    self.transition_points.append(self.beat_markers[i])
        
        # Sort the transition points by time
        self.transition_points.sort()
        
        # Pre-select transition types based on music characteristics
        if self.groove_type:
            self._adjust_transition_weights_by_groove()
        
        # Log the transition schedule
        if len(self.transition_points) > 0:
            logger.info(f"Initialized {len(self.transition_points)} transition points")
    
    def _adjust_transition_weights_by_groove(self):
        """Adjust transition type weights based on the detected groove type."""
        if "slow" in self.groove_type:
            # For slow songs, prefer smoother transitions
            self.transition_map["crossfade"] = (1.5, 0)
            self.transition_map["dissolve"] = (1.2, 0)
            self.transition_map["fade_to_black"] = (1.2, 0)
            self.transition_map["zoom"] = (1.0, 0)
            # Reduce weight of jarring transitions
            self.transition_map["glitch"] = (0.2, 0)
            self.transition_map["flash_fade"] = (0.3, 0)
        
        elif "fast" in self.groove_type:
            # For fast songs, prefer dynamic transitions
            self.transition_map["zoom"] = (1.5, 0)
            self.transition_map["slide"] = (1.3, 0)
            self.transition_map["wipe"] = (1.2, 0)
            self.transition_map["glitch"] = (1.0, 0)
            self.transition_map["flash_fade"] = (1.2, 0)
            # Reduce weight of slow transitions
            self.transition_map["crossfade"] = (0.7, 0)
            self.transition_map["fade_to_black"] = (0.5, 0)
        
        # Also adjust based on energy level if available
        if "high_energy" in self.groove_type:
            self.transition_map["flash_fade"] = (1.5, 0)
            self.transition_map["spin"] = (1.3, 0)
        elif "low_energy" in self.groove_type:
            self.transition_map["crossfade"] = (1.8, 0)
            self.transition_map["dissolve"] = (1.5, 0)
    
    def set_key_moments(self, key_moments: List[float]):
        """Set key moments for transitions."""
        self.key_moments = key_moments
        # Merge with existing transition points
        for moment in key_moments:
            if not any(abs(moment - point) < 0.5 for point in self.transition_points):
                self.transition_points.append(moment)
        self.transition_points.sort()
    
    def apply(self, frame: np.ndarray, time_sec: float) -> np.ndarray:
        """
        Apply intelligent transitions based on music structure analysis.
        
        Args:
            frame: Input video frame
            time_sec: Current video time in seconds
            
        Returns:
            np.ndarray: Processed frame with transition effect
        """
        # Initialize frames on first call
        if self.prev_frame is None:
            self.prev_frame = frame.copy()
            return frame
        
        if self.current_frame is None:
            self.current_frame = frame.copy()
            return frame
        
        # Store the incoming frame as the next frame
        self.next_frame = frame.copy()
        
        # Check if we're currently in a transition
        if self.is_transitioning:
            # Calculate progress through the transition
            elapsed = time_sec - self.transition_start_time
            self.transition_progress = min(1.0, elapsed / self.transition_duration)
            
            # Apply the current transition effect
            result = self._apply_current_transition(self.transition_progress)
            
            # Check if transition is complete
            if self.transition_progress >= 1.0:
                self.is_transitioning = False
                # Update frames for next transition
                self.prev_frame = self.current_frame.copy()
                self.current_frame = self.next_frame.copy()
                
                # Update "used" counter for this transition type
                if self.transition_type in self.transition_map:
                    weight, used_count = self.transition_map[self.transition_type]
                    self.transition_map[self.transition_type] = (weight, used_count + 1)
            
            return result
        
        # If not transitioning, check if it's time to start a new transition
        # First check if we're at a scheduled transition point
        should_transition = False
        transition_importance = 0  # Used to determine transition type
        
        # Check scheduled transition points
        for point in self.transition_points:
            if abs(time_sec - point) < 0.1:  # Within 0.1 seconds of a scheduled point
                should_transition = True
                # Check if this is a drop for special transitions
                if self.beat_drops and any(abs(point - drop) < 0.2 for drop in self.beat_drops):
                    transition_importance = 3  # Drop transitions are highest importance
                # Check if this is a phrase boundary
                elif self.phrase_boundaries and any(abs(point - boundary) < 0.2 for boundary in self.phrase_boundaries):
                    transition_importance = 2  # Phrase transitions are medium importance
                else:
                    transition_importance = 1  # Regular scheduled transition
                break
        
        # Handle spontaneous transitions based on music features
        if not should_transition:
            # Check for drop-based transitions (highest priority)
            drop_value = self.music_analyzer.get_feature_at_time(MusicFeature.DROP_PROXIMITY, time_sec)
            if drop_value > 0.95:  # Very close to a drop
                should_transition = True
                transition_importance = 3
            
            # Check for phrase boundary-based transitions (medium priority)
            elif self.music_analyzer.get_feature_at_time(MusicFeature.PHRASE_BOUNDARY, time_sec) > 0.8:
                should_transition = True
                transition_importance = 2
            
            # Check for beat pattern-based transitions (lower priority)
            elif self.music_analyzer.get_feature_at_time(MusicFeature.BEAT_PATTERN_INTENSITY, time_sec) > 0.8:
                beat_value = self.music_analyzer.get_feature_at_time(MusicFeature.BEATS, time_sec)
                if beat_value > 0.95:  # Strong beat
                    should_transition = True
                    transition_importance = 1
        
        # Enforce minimum time between transitions
        if should_transition and (time_sec - self.last_transition_time) < self.min_transition_interval:
            should_transition = False
        
        # Start transition if conditions are met
        if should_transition:
            self.is_transitioning = True
            self.transition_start_time = time_sec
            self.transition_progress = 0.0
            self.last_transition_time = time_sec
            
            # Select appropriate transition type based on music and importance
            self.transition_type = self._select_transition_type(transition_importance)
            
            logger.debug(f"Starting {self.transition_type} transition at {time_sec:.2f}s (importance: {transition_importance})")
            
            # Apply initial transition frame
            return self._apply_current_transition(0.0)
        
        # If not transitioning, just return the current frame
        return self.current_frame
    
    def _select_transition_type(self, importance: int) -> str:
        """
        Select an appropriate transition type based on music features and importance.
        
        Args:
            importance: The importance level of the transition (1-3)
            
        Returns:
            str: The selected transition type
        """
        # Get the current energy level
        energy = self.music_analyzer.get_feature_at_time(MusicFeature.ENERGY, self.transition_start_time)
        
        # Filter transitions based on importance
        if importance == 3:  # High importance (drops)
            # For drops, prefer impactful transitions
            candidates = ["flash_fade", "zoom", "glitch"]
            if energy > 0.7:
                # Add more dramatic transitions for high energy drops
                candidates.extend(["spin", "radial"])
        
        elif importance == 2:  # Medium importance (phrase boundaries)
            # For phrase boundaries, prefer clean transitions
            candidates = ["crossfade", "slide", "wipe", "dissolve"]
            if energy > 0.6:
                # Add more noticeable transitions for high energy
                candidates.extend(["zoom", "radial"])
        
        else:  # Low importance (regular beats)
            # For regular transitions, use subtle options
            candidates = ["crossfade", "dissolve", "zoom"]
            if energy > 0.7:
                # Add slightly more noticeable options for high energy
                candidates.append("slide")
        
        # Calculate weighted probabilities based on transition map
        weights = []
        available_types = []
        
        for t_type in candidates:
            if t_type in self.transition_map:
                weight, used_count = self.transition_map[t_type]
                # Decrease weight based on how often it's been used
                adjusted_weight = weight / (1 + used_count * 0.5)
                weights.append(adjusted_weight)
                available_types.append(t_type)
        
        # Default to crossfade if no candidates match
        if not available_types:
            return "crossfade"
        
        # Normalize weights to probabilities
        total_weight = sum(weights)
        if total_weight > 0:
            probabilities = [w / total_weight for w in weights]
            
            # Select transition type based on weighted probability
            from random import choices
            selected = choices(available_types, probabilities)[0]
            return selected
        else:
            return "crossfade"
    
    def _apply_current_transition(self, progress: float) -> np.ndarray:
        """
        Apply the current transition type with the given progress.
        
        Args:
            progress: Transition progress from 0.0 to 1.0
            
        Returns:
            np.ndarray: The processed frame with transition applied
        """
        if self.transition_type == "crossfade":
            return self._apply_crossfade(progress)
        elif self.transition_type == "zoom":
            return self._apply_zoom(progress)
        elif self.transition_type == "fade_to_black":
            return self._apply_fade_to_black(progress)
        elif self.transition_type == "dissolve":
            return self._apply_dissolve(progress)
        elif self.transition_type == "slide":
            return self._apply_slide(progress)
        elif self.transition_type == "wipe":
            return self._apply_wipe(progress)
        elif self.transition_type == "radial":
            return self._apply_radial(progress)
        elif self.transition_type == "spiral":
            return self._apply_spiral(progress)
        elif self.transition_type == "pixelate":
            return self._apply_pixelate(progress)
        elif self.transition_type == "spin":
            return self._apply_spin(progress)
        elif self.transition_type == "flash_fade":
            return self._apply_flash_fade(progress)
        elif self.transition_type == "glitch":
            return self._apply_glitch(progress)
        else:
            # Fallback to crossfade for unknown transition types
            return self._apply_crossfade(progress)
    
    def _apply_crossfade(self, progress: float) -> np.ndarray:
        """Apply a crossfade transition between frames."""
        return cv2.addWeighted(self.current_frame, progress, self.prev_frame, 1.0 - progress, 0)
    
    def _apply_zoom(self, progress: float) -> np.ndarray:
        """Apply a zoom transition between frames."""
        # Zoom out from previous frame
        h, w = self.prev_frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Scale factor for zoom (start at 1.0, end at 1.3)
        scale_factor = 1.0 + (0.3 * progress * self.intensity)
        
        # Create transformation matrix for zoom
        M = cv2.getRotationMatrix2D((center_x, center_y), 0, scale_factor)
        
        # Apply zoom to previous frame
        zoomed_prev = cv2.warpAffine(self.prev_frame, M, (w, h))
        
        # Crossfade between zoomed previous frame and current frame
        return cv2.addWeighted(self.current_frame, progress, zoomed_prev, 1.0 - progress, 0)
    
    def _apply_fade_to_black(self, progress: float) -> np.ndarray:
        """Apply a fade to black and back transition."""
        # For first half of transition, fade to black
        if progress < 0.5:
            fade_progress = progress * 2  # Scale to 0-1 range for first half
            black_frame = np.zeros_like(self.prev_frame)
            return cv2.addWeighted(self.prev_frame, 1.0 - fade_progress, black_frame, fade_progress, 0)
        # For second half, fade from black to new frame
        else:
            fade_progress = (progress - 0.5) * 2  # Scale to 0-1 range for second half
            black_frame = np.zeros_like(self.current_frame)
            return cv2.addWeighted(black_frame, 1.0 - fade_progress, self.current_frame, fade_progress, 0)
    
    def _apply_dissolve(self, progress: float) -> np.ndarray:
        """Apply a dissolve transition with noise pattern."""
        # Create noise mask that gradually reveals new frame
        h, w = self.prev_frame.shape[:2]
        noise = np.random.random((h, w)) 
        threshold = progress
        
        # Binary mask where values below threshold become 1 (new frame), others 0 (old frame)
        mask = (noise < threshold).astype(np.float32)
        mask_3ch = np.stack([mask] * 3, axis=2)
        
        # Blend images using the mask
        result = self.current_frame * mask_3ch + self.prev_frame * (1.0 - mask_3ch)
        
        return result.astype(np.uint8)
    
    def _apply_slide(self, progress: float) -> np.ndarray:
        """Apply a slide transition between frames."""
        h, w = self.prev_frame.shape[:2]
        result = np.zeros_like(self.prev_frame)
        
        # Determine slide direction based on music intensity
        # More energetic parts use horizontal slides, less energetic use vertical
        if self.music_analyzer.get_segment_intensity(max(0, self.transition_start_time - 1), min(self.transition_start_time + 1, self.transition_start_time + self.music_analyzer.get_time_to_next_beat(self.transition_start_time))) > 0.5:
            # Horizontal slide (left or right)
            direction = 0 if hash(str(self.transition_start_time)) % 2 == 0 else 1
        else:
            # Vertical slide (up or down)
            direction = 2 if hash(str(self.transition_start_time)) % 2 == 0 else 3
        
        if direction == 0:  # Slide to left
            offset = int(w * progress)
            # Part of previous frame
            if offset < w:
                result[:, :w-offset] = self.prev_frame[:, offset:]
            # Part of current frame
            result[:, w-offset:] = self.current_frame[:, :offset]
        elif direction == 1:  # Slide to right
            offset = int(w * progress)
            # Part of previous frame
            if offset < w:
                result[:, offset:] = self.prev_frame[:, :w-offset]
            # Part of current frame
            result[:, :offset] = self.current_frame[:, w-offset:]
        elif direction == 2:  # Slide up
            offset = int(h * progress)
            # Part of previous frame
            if offset < h:
                result[:h-offset, :] = self.prev_frame[offset:, :]
            # Part of current frame
            result[h-offset:, :] = self.current_frame[:offset, :]
        else:  # Slide down
            offset = int(h * progress)
            # Part of previous frame
            if offset < h:
                result[offset:, :] = self.prev_frame[:h-offset, :]
            # Part of current frame
            result[:offset, :] = self.current_frame[h-offset:, :]
        
        return result
    
    def _apply_wipe(self, progress: float) -> np.ndarray:
        """Apply a wipe transition between frames."""
        h, w = self.prev_frame.shape[:2]
        
        # Create transition mask
        mask = np.zeros((h, w), dtype=np.float32)
        
        # Determine wipe direction based on energy
        direction = int(hash(str(self.transition_start_time)) % 4)
        
        if direction == 0:  # Left to right
            edge_pos = int(w * progress)
            mask[:, :edge_pos] = 1.0
        elif direction == 1:  # Right to left
            edge_pos = int(w * (1.0 - progress))
            mask[:, edge_pos:] = 1.0
        elif direction == 2:  # Top to bottom
            edge_pos = int(h * progress)
            mask[:edge_pos, :] = 1.0
        else:  # Bottom to top
            edge_pos = int(h * (1.0 - progress))
            mask[edge_pos:, :] = 1.0
        
        # Apply anti-aliasing to the edge for smoother transition
        if direction == 0 or direction == 1:  # Horizontal wipes
            blur_size = max(1, int(w * 0.01))  # 1% of width
            mask = cv2.GaussianBlur(mask, (1, blur_size*2+1), 0)
        else:  # Vertical wipes
            blur_size = max(1, int(h * 0.01))  # 1% of height
            mask = cv2.GaussianBlur(mask, (blur_size*2+1, 1), 0)
        
        # Expand mask dimensions to match the image
        mask_3ch = np.stack([mask] * 3, axis=2)
        
        # Blend images using the mask
        result = self.current_frame * mask_3ch + self.prev_frame * (1.0 - mask_3ch)
        
        return result.astype(np.uint8)
    
    def _apply_radial(self, progress: float) -> np.ndarray:
        """Apply a radial wipe transition."""
        h, w = self.prev_frame.shape[:2]
        
        # Create mask with circular pattern
        center_y, center_x = h // 2, w // 2
        Y, X = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        
        # Maximum distance possible
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        # Scale maximum radius based on progress
        max_radius = max_dist * progress
        
        # Create mask (1 inside circle, 0 outside)
        mask = (dist_from_center <= max_radius).astype(np.float32)
        
        # Add a slight blur for smooth edge
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # Expand mask to 3 channels
        mask_3ch = np.stack([mask] * 3, axis=2)
        
        # Blend images
        result = self.current_frame * mask_3ch + self.prev_frame * (1.0 - mask_3ch)
        
        return result.astype(np.uint8)
    
    def _apply_spiral(self, progress: float) -> np.ndarray:
        """Apply a spiral wipe transition."""
        h, w = self.prev_frame.shape[:2]
        
        # Create polar coordinate mask
        center_y, center_x = h // 2, w // 2
        Y, X = np.ogrid[:h, :w]
        
        # Calculate distance and angle in polar coordinates
        dx = X - center_x
        dy = Y - center_y
        radius = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx) + np.pi  # Range 0 to 2π
        
        # Normalize radius
        max_radius = np.sqrt(center_x**2 + center_y**2)
        norm_radius = radius / max_radius
        
        # Create spiral mask: mask = angle + radius > threshold
        # As progress increases, the threshold increases, revealing more of the new frame
        spiral_factor = 5.0  # Controls spiral tightness
        threshold = progress * (2 * np.pi + spiral_factor)
        
        # Spiral equation: angle + norm_radius * spiral_factor
        spiral_val = angle + norm_radius * spiral_factor
        mask = (spiral_val % (2 * np.pi + spiral_factor) < threshold).astype(np.float32)
        
        # Blur the mask for smooth edges
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # Expand mask to 3 channels
        mask_3ch = np.stack([mask] * 3, axis=2)
        
        # Blend images
        result = self.current_frame * mask_3ch + self.prev_frame * (1.0 - mask_3ch)
        
        return result.astype(np.uint8)
    
    def _apply_pixelate(self, progress: float) -> np.ndarray:
        """Apply a pixelation transition effect."""
        # Start with fully pixelated old frame, gradually reveal new frame
        h, w = self.prev_frame.shape[:2]
        
        # Calculate pixel size (starts large, gets smaller)
        if progress < 0.5:
            # First half: pixelate old frame more and more
            pixel_size = int(max(1, (0.5 - progress) * 50))
            frame_to_pixelate = self.prev_frame
            weight_old = 1.0 - (progress * 2)  # 1.0 to 0.0
            weight_new = progress * 2  # 0.0 to 1.0
        else:
            # Second half: reveal new frame from pixelated to clear
            pixel_size = int(max(1, (1.0 - progress) * 50))
            frame_to_pixelate = self.current_frame
            weight_old = 0.0
            weight_new = 1.0
        
        # Skip if pixel size is 1 (no pixelation)
        if pixel_size <= 1:
            return self.current_frame if progress >= 0.5 else self.prev_frame
        
        # Pixelate by resizing down and up
        small = cv2.resize(frame_to_pixelate, (w // pixel_size, h // pixel_size), 
                           interpolation=cv2.INTER_LINEAR)
        pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        
        if progress < 0.5:
            # Blend pixelated old frame with new frame
            result = cv2.addWeighted(pixelated, weight_old, self.current_frame, weight_new, 0)
        else:
            # Return pixelated new frame
            result = pixelated
        
        return result
    
    def _apply_spin(self, progress: float) -> np.ndarray:
        """Apply a spinning transition effect."""
        h, w = self.prev_frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Rotate previous frame
        angle = progress * 180  # Rotate up to 180 degrees
        scale = 1.0 - (progress * 0.3)  # Scale down slightly
        
        # Create rotation matrix
        M = cv2.getRotationMatrix2D((center_x, center_y), angle, scale)
        
        # Apply rotation
        rotated_prev = cv2.warpAffine(self.prev_frame, M, (w, h))
        
        # Blend with current frame
        alpha = progress  # Linear crossfade
        result = cv2.addWeighted(self.current_frame, alpha, rotated_prev, 1.0 - alpha, 0)
        
        return result
    
    def _apply_flash_fade(self, progress: float) -> np.ndarray:
        """Apply a flash transition that fades through white."""
        # First third: fade to white
        if progress < 0.33:
            sub_progress = progress * 3  # Scale to 0-1
            white_frame = np.ones_like(self.prev_frame) * 255
            return cv2.addWeighted(self.prev_frame, 1.0 - sub_progress, white_frame, sub_progress, 0)
        
        # Second third: stay white with slight hint of target
        elif progress < 0.67:
            sub_progress = (progress - 0.33) * 3  # Scale to 0-1
            white_frame = np.ones_like(self.current_frame) * 255
            # Add just a hint of the new frame (20%)
            return cv2.addWeighted(white_frame, 1.0 - (sub_progress * 0.2), self.current_frame, sub_progress * 0.2, 0)
        
        # Final third: fade from white to new frame
        else:
            sub_progress = (progress - 0.67) * 3  # Scale to 0-1
            white_frame = np.ones_like(self.current_frame) * 255
            return cv2.addWeighted(white_frame, 1.0 - sub_progress, self.current_frame, sub_progress, 0)
    
    def _apply_glitch(self, progress: float) -> np.ndarray:
        """Apply a glitch-style transition effect."""
        h, w = self.prev_frame.shape[:2]
        
        # Start with the previous frame
        result = self.prev_frame.copy()
        
        # Number of glitch effects varies with progress (more as we advance)
        num_effects = int(progress * 20)
        
        # Apply several random glitch effects
        for _ in range(num_effects):
            # Choose a random effect type
            effect_type = random.randint(0, 3)
            
            if effect_type == 0:
                # Horizontal line shift
                y = random.randint(0, h - 1)
                shift = random.randint(-30, 30)
                if 0 <= y < h:
                    line = result[y, :].copy()
                    result[y, :] = np.roll(line, shift, axis=0)
                
            elif effect_type == 1:
                # RGB channel shift
                channel = random.randint(0, 2)
                shift_x = random.randint(-15, 15)
                if shift_x != 0:
                    result[:, :, channel] = np.roll(result[:, :, channel], shift_x, axis=1)
                
            elif effect_type == 2:
                # Block displacement
                block_h = random.randint(10, h // 8)
                block_w = random.randint(10, w // 8)
                y1 = random.randint(0, h - block_h - 1)
                x1 = random.randint(0, w - block_w - 1)
                y2 = random.randint(0, h - block_h - 1)
                x2 = random.randint(0, w - block_w - 1)
                
                # Copy block from one position to another
                if (y1 >= 0 and x1 >= 0 and y2 >= 0 and x2 >= 0 and 
                    y1 + block_h <= h and x1 + block_w <= w and 
                    y2 + block_h <= h and x2 + block_w <= w):
                    temp = self.current_frame[y1:y1+block_h, x1:x1+block_w].copy()
                    result[y2:y2+block_h, x2:x2+block_w] = temp
        
        # Gradually blend with new frame
        return cv2.addWeighted(result, 1.0 - progress, self.current_frame, progress, 0) 