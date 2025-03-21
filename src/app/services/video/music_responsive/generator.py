"""
Music-responsive video generator.

This module provides the main functionality for creating videos that 
respond to music features by applying various visual effects.
"""

import os
import logging
import numpy as np
import cv2
import random
from typing import List, Tuple, Dict, Any, Optional, Union

from src.app.core.settings import DEV_MODE, DEBUG_MODE
from src.app.services.video.music_responsive.analyzer import MusicAnalyzer
from src.app.services.video.music_responsive.enums import MusicFeature
from src.app.services.video.music_responsive.presets import StylePreset, get_preset_manager
from src.app.services.video.music_responsive.analytics import get_analytics_manager
from src.app.services.video.music_responsive.effects import (
    AnticipationEffect,
    PulseEffect,
    ColorShiftEffect,
    ShakeEffect,
    FlashEffect,
    VignetteEffect,
    WarpEffect,
    GlitchEffect,
    TransitionEffect,
    AdvancedTransitionSystem,
    MusicResponsiveEffect
)

# Set up logging
logger = logging.getLogger(__name__)

def create_music_responsive_video(
    images: List[str],
    music_path: str,
    output_path: str,
    fps: int = 30,
    duration: int = 60,
    resolution: Tuple[int, int] = (1080, 1920),
    effect_intensity: float = 1.0,
    anticipation_time: float = 0.15,
    use_smart_transitions: bool = True,
    preset: Optional[Union[StylePreset, str]] = None,
    custom_preset_id: Optional[str] = None,
    analytics_session_id: Optional[str] = None
) -> str:
    """
    Create a video that responds to music features with enhanced beat sync.
    
    Args:
        images: List of image paths
        music_path: Path to music file
        output_path: Path to save output video
        fps: Frames per second
        duration: Target duration in seconds
        resolution: Video resolution (width, height)
        effect_intensity: Overall intensity of effects
        anticipation_time: Time in seconds to anticipate beats (default: 0.15s)
        use_smart_transitions: Whether to use smart transitions that adapt to music structure
        preset: Style preset to use (built-in or custom)
        custom_preset_id: ID of custom preset (if preset is StylePreset.CUSTOM)
        analytics_session_id: ID for analytics tracking (optional)
    
    Returns:
        str: Path to output video file
    """
    logger.info(f"Creating music-responsive video with {len(images)} images")
    
    # Validate inputs
    if len(images) < 1:
        raise ValueError("At least one image is required")
    
    if not os.path.exists(music_path):
        raise ValueError(f"Music file not found: {music_path}")
    
    # Get preset configuration
    preset_manager = get_preset_manager()
    preset_config = preset_manager.get_preset_config(preset, custom_preset_id)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Set up video parameters
    width, height = resolution
    total_frames = min(int(fps * duration), int(fps * 300))  # Cap at 5 minutes max
    
    # Analyze music with enhanced features
    analyzer = MusicAnalyzer(music_path, anticipation_time)
    
    # Record music features analyzed in analytics
    if analytics_session_id:
        try:
            analytics_manager = get_analytics_manager()
            for feature in analyzer.features_analyzed:
                analytics_manager.add_music_feature_analysis(analytics_session_id, feature)
        except Exception as e:
            logger.warning(f"Error recording music features for analytics: {e}")
    
    # Get beat times and key moments for transitions
    beat_times = analyzer.beat_times
    key_moments = analyzer.key_moments if hasattr(analyzer, 'key_moments') else []
    
    # Calculate segment intensities for dynamic effects
    segment_intensities = _calculate_segment_intensities(analyzer, duration)
    
    # Prepare image frames
    image_frames = _prepare_image_frames(images, width, height)
    
    # Create transition effect (either advanced or simple based on preference)
    transition_effect = None
    if use_smart_transitions:
        # Use advanced transition system with music-driven effects
        transition_effect = AdvancedTransitionSystem(
            analyzer, 
            intensity=effect_intensity,
            transition_duration=0.5,
            min_transition_interval=2.0
        )
        # Set key moments for special transitions at significant points in the music
        if key_moments:
            transition_effect.set_key_moments(key_moments)
    else:
        # Use simpler transition effect
        transition_effect = TransitionEffect(
            analyzer,
            intensity=effect_intensity,
            transition_duration=0.5
        )
    
    # Create effects based on preset
    effects = _create_effects(
        analyzer, 
        effect_intensity, 
        preset_config,
        analytics_session_id
    )
    
    # Add anticipation effect for enhanced beat responsiveness
    effects.append(AnticipationEffect(analyzer, intensity=effect_intensity * 0.8))
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use mp4v codec
    video_writer = cv2.VideoWriter(
        output_path, 
        fourcc, 
        fps, 
        (width, height)
    )
    
    if not video_writer.isOpened():
        raise RuntimeError(f"Failed to open video writer with output path: {output_path}")
    
    # Generate video frames
    try:
        _generate_video_frames(
            video_writer,
            image_frames,
            effects,
            transition_effect,
            beat_times,
            segment_intensities,
            total_frames,
            fps,
            analyzer
        )
    finally:
        # Release video writer
        video_writer.release()
    
    logger.info(f"Music-responsive video created successfully: {output_path}")
    return output_path

def _create_effects(
    analyzer: MusicAnalyzer, 
    effect_intensity: float,
    preset_config: Optional[Dict[str, Any]] = None,
    analytics_session_id: Optional[str] = None
) -> List[MusicResponsiveEffect]:
    """
    Create effects based on the preset configuration.
    
    Args:
        analyzer: Music analyzer instance
        effect_intensity: Overall intensity of effects
        preset_config: Preset configuration dictionary
        analytics_session_id: ID for analytics tracking (optional)
    
    Returns:
        List of music-responsive effects
    """
    effects = []
    analytics_manager = None
    
    # Initialize analytics manager if session ID is provided
    if analytics_session_id:
        try:
            analytics_manager = get_analytics_manager()
        except Exception as e:
            logger.warning(f"Error initializing analytics manager: {e}")
    
    # Create default effects if no preset config is provided
    if not preset_config:
        # Create default effects
        effects.extend([
            PulseEffect(analyzer, intensity=effect_intensity),
            ColorShiftEffect(analyzer, intensity=effect_intensity),
            ShakeEffect(analyzer, intensity=effect_intensity * 0.5)
        ])
        
        # Record effects for analytics
        if analytics_manager and analytics_session_id:
            for effect_name in ["pulse", "color_shift", "shake"]:
                try:
                    analytics_manager.add_effect_usage(analytics_session_id, effect_name)
                except Exception as e:
                    logger.warning(f"Error recording effect usage for analytics: {e}")
        
        return effects
    
    # Use the preset configuration to create effects
    for effect_config in preset_config.get("effects", []):
        effect_type = effect_config.get("type")
        intensity = effect_config.get("intensity", 1.0) * effect_intensity
        
        try:
            if effect_type == "pulse":
                effects.append(PulseEffect(
                    analyzer,
                    intensity=intensity,
                    feature=MusicFeature(effect_config.get("feature", "energy")),
                    min_scale=effect_config.get("min_scale", 1.0),
                    max_scale=effect_config.get("max_scale", 1.2)
                ))
                # Record effect for analytics
                if analytics_manager and analytics_session_id:
                    analytics_manager.add_effect_usage(analytics_session_id, "pulse")
            
            elif effect_type == "color_shift":
                effects.append(ColorShiftEffect(
                    analyzer,
                    intensity=intensity,
                    feature=MusicFeature(effect_config.get("feature", "energy")),
                    target_color=effect_config.get("target_color"),
                    shift_amount=effect_config.get("shift_amount", 0.5)
                ))
                # Record effect for analytics
                if analytics_manager and analytics_session_id:
                    analytics_manager.add_effect_usage(analytics_session_id, "color_shift")
            
            elif effect_type == "shake":
                effects.append(ShakeEffect(
                    analyzer,
                    intensity=intensity,
                    feature=MusicFeature(effect_config.get("feature", "beats")),
                    max_offset=effect_config.get("max_offset", 20)
                ))
                # Record effect for analytics
                if analytics_manager and analytics_session_id:
                    analytics_manager.add_effect_usage(analytics_session_id, "shake")
            
            elif effect_type == "flash":
                effects.append(FlashEffect(
                    analyzer,
                    intensity=intensity,
                    feature=MusicFeature(effect_config.get("feature", "beats")),
                    flash_color=effect_config.get("flash_color", (255, 255, 255)),
                    max_opacity=effect_config.get("max_opacity", 0.7)
                ))
                # Record effect for analytics
                if analytics_manager and analytics_session_id:
                    analytics_manager.add_effect_usage(analytics_session_id, "flash")
            
            elif effect_type == "warp":
                effects.append(WarpEffect(
                    analyzer,
                    intensity=intensity,
                    feature=MusicFeature(effect_config.get("feature", "energy")),
                    warp_amount=effect_config.get("warp_amount", 0.1)
                ))
                # Record effect for analytics
                if analytics_manager and analytics_session_id:
                    analytics_manager.add_effect_usage(analytics_session_id, "warp")
            
            else:
                logger.warning(f"Unknown effect type: {effect_type}")
                
        except Exception as e:
            logger.error(f"Error creating effect '{effect_type}': {e}")
    
    # If no effects were created, fall back to default
    if not effects:
        logger.warning("No valid effects in preset, using default effects")
        effects.extend([
            PulseEffect(analyzer, intensity=effect_intensity),
            ColorShiftEffect(analyzer, intensity=effect_intensity),
            ShakeEffect(analyzer, intensity=effect_intensity * 0.5)
        ])
        
        # Record effects for analytics
        if analytics_manager and analytics_session_id:
            for effect_name in ["pulse", "color_shift", "shake"]:
                try:
                    analytics_manager.add_effect_usage(analytics_session_id, effect_name)
                except Exception as e:
                    logger.warning(f"Error recording effect usage for analytics: {e}")
    
    return effects

def _apply_color_filter(image_frames: List[np.ndarray], color_filter: Tuple[int, int, int]) -> List[np.ndarray]:
    """
    Apply a color filter to all image frames.
    
    Args:
        image_frames: List of image frames
        color_filter: Color filter to apply (BGR format)
        
    Returns:
        List[np.ndarray]: Processed image frames
    """
    filtered_frames = []
    for frame in image_frames:
        # Convert to HSV for better color manipulation
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Apply color shift based on filter
        filter_hsv = cv2.cvtColor(np.uint8([[color_filter]]), cv2.COLOR_BGR2HSV)[0][0]
        hsv[:, :, 0] = (hsv[:, :, 0] + filter_hsv[0]) % 180  # Hue shift
        
        # Apply some saturation and value adjustments based on filter
        if filter_hsv[1] > 0:  # If filter has saturation
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + filter_hsv[1]/255), 0, 255).astype(np.uint8)
        
        if filter_hsv[2] < 128:  # If filter darkens
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (filter_hsv[2]/128), 0, 255).astype(np.uint8)
        
        # Convert back to BGR
        filtered_frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        filtered_frames.append(filtered_frame)
    
    return filtered_frames

def _prepare_image_frames(images: List[str], width: int, height: int) -> List[np.ndarray]:
    """
    Load and resize images for the video.
    
    Args:
        images: List of image paths
        width: Target width
        height: Target height
        
    Returns:
        List[np.ndarray]: Processed image frames
    """
    image_frames = []
    for img_path in images:
        img = cv2.imread(img_path)
        if img is not None:
            # Resize to match video resolution
            img_resized = cv2.resize(img, (width, height))
            image_frames.append(img_resized)
        else:
            logger.warning(f"Could not load image: {img_path}")
    
    if not image_frames:
        raise ValueError("No valid images loaded")
    
    # Duplicate images if not enough
    while len(image_frames) < 5:
        image_frames.extend(image_frames)
        
    return image_frames

def _calculate_segment_intensities(analyzer: MusicAnalyzer, duration: int) -> List[float]:
    """
    Calculate music intensity for segments of the audio with enhanced accuracy and smoothing.
    
    Args:
        analyzer: Music analyzer instance
        duration: Duration in seconds
        
    Returns:
        List[float]: Intensity values for each segment with smooth transitions
    """
    # Calculate raw intensity values at higher resolution
    high_res_segment_duration = 0.5  # Higher resolution for more accurate analysis
    raw_intensities = []
    
    # Calculate intensity at each point
    for t in np.arange(0, duration, high_res_segment_duration):
        intensity = analyzer.get_segment_intensity(t, t + high_res_segment_duration)
        raw_intensities.append(intensity)
    
    # Apply median filtering to remove outliers
    window_size = 5  # 5-point median filter
    if len(raw_intensities) >= window_size:
        # Pad the edges for filtering
        padded_intensities = np.pad(raw_intensities, (window_size//2, window_size//2), mode='edge')
        filtered_intensities = np.zeros_like(raw_intensities)
        
        # Apply median filter
        for i in range(len(raw_intensities)):
            filtered_intensities[i] = np.median(padded_intensities[i:i+window_size])
    else:
        filtered_intensities = raw_intensities
    
    # Apply moving average to smooth transitions
    window_size = 3  # 3-point moving average
    if len(filtered_intensities) >= window_size:
        # Pad the edges for filtering
        padded_intensities = np.pad(filtered_intensities, (window_size//2, window_size//2), mode='edge')
        smoothed_intensities = np.zeros_like(filtered_intensities)
        
        # Apply moving average filter
        for i in range(len(filtered_intensities)):
            smoothed_intensities[i] = np.mean(padded_intensities[i:i+window_size])
    else:
        smoothed_intensities = filtered_intensities
    
    # Enhance intensity range to make differences more pronounced
    # Scale to 0.2-1.0 range to ensure some base intensity even in quiet parts
    if len(smoothed_intensities) > 0:
        min_val = np.min(smoothed_intensities)
        max_val = np.max(smoothed_intensities)
        
        if max_val > min_val:
            normalized_intensities = (smoothed_intensities - min_val) / (max_val - min_val)
            enhanced_intensities = 0.2 + (normalized_intensities * 0.8)
        else:
            enhanced_intensities = np.full_like(smoothed_intensities, 0.5)
    else:
        enhanced_intensities = []
    
    # Perform additional enhancement to emphasize dynamic parts
    if len(enhanced_intensities) > 1:
        # Calculate rate of change
        intensity_diff = np.abs(np.diff(enhanced_intensities, prepend=enhanced_intensities[0]))
        
        # Boost intensity in areas with high rate of change
        boost_factor = 1.2  # How much to boost dynamic areas
        dynamic_intensities = enhanced_intensities + (intensity_diff * boost_factor)
        
        # Rescale to 0.0-1.0 range
        dynamic_intensities = np.clip(dynamic_intensities, 0.0, 1.0)
    else:
        dynamic_intensities = enhanced_intensities
    
    # Resample to final segment duration if high_res_segment_duration is different
    segment_duration = 1.0  # Final segment duration
    if high_res_segment_duration != segment_duration:
        num_segments = int(duration / segment_duration)
        resampled_intensities = []
        
        for i in range(num_segments):
            start_idx = int(i * segment_duration / high_res_segment_duration)
            end_idx = int((i + 1) * segment_duration / high_res_segment_duration)
            
            # Ensure we don't go out of bounds
            start_idx = min(start_idx, len(dynamic_intensities) - 1)
            end_idx = min(end_idx, len(dynamic_intensities))
            
            if start_idx < end_idx:
                # Average the high resolution values for this segment
                segment_intensity = np.mean(dynamic_intensities[start_idx:end_idx])
            else:
                # Fallback if indices are invalid
                segment_intensity = 0.5 if len(dynamic_intensities) == 0 else dynamic_intensities[-1]
            
            resampled_intensities.append(segment_intensity)
        
        segment_intensities = resampled_intensities
    else:
        segment_intensities = dynamic_intensities.tolist()
    
    # Ensure we have enough values for the entire duration
    if len(segment_intensities) < int(duration):
        # If we don't have enough values, pad with the last value
        last_value = segment_intensities[-1] if segment_intensities else 0.5
        additional_values = [last_value] * (int(duration) - len(segment_intensities))
        segment_intensities.extend(additional_values)
    
    return segment_intensities

def _generate_video_frames(
    video_writer: cv2.VideoWriter,
    image_frames: List[np.ndarray],
    effects: List[MusicResponsiveEffect],
    transition_effect: Union[TransitionEffect, AdvancedTransitionSystem],
    beat_times: np.ndarray,
    segment_intensities: List[float],
    total_frames: int,
    fps: int,
    analyzer: MusicAnalyzer
) -> None:
    """
    Generate and write video frames with enhanced music-responsive effects.
    
    Args:
        video_writer: OpenCV VideoWriter instance
        image_frames: List of image frames
        effects: List of effect instances
        transition_effect: TransitionEffect or AdvancedTransitionSystem instance
        beat_times: Array of beat times
        segment_intensities: List of segment intensities
        total_frames: Total number of frames to generate
        fps: Frames per second
        analyzer: MusicAnalyzer instance for real-time music analysis
    """
    segment_duration = 1.0  # seconds
    last_img_idx = -1
    beat_strengths = getattr(analyzer, 'beat_strengths', None)
    
    # For progress reporting
    progress_interval = max(1, total_frames // 10)
    progress_last_reported = 0
    
    for frame_idx in range(total_frames):
        time_sec = frame_idx / fps
        
        # Find current segment index and get its intensity
        segment_idx = min(int(time_sec / segment_duration), len(segment_intensities) - 1)
        current_intensity = segment_intensities[segment_idx]
        
        # Calculate time to nearest beat for adaptive effects
        if len(beat_times) > 0:
            nearest_beat_idx = np.argmin(np.abs(beat_times - time_sec))
            time_to_nearest_beat = abs(beat_times[nearest_beat_idx] - time_sec)
            is_on_beat = time_to_nearest_beat < 0.1  # Within 100ms of a beat
            
            # Get beat strength if available
            beat_strength = 1.0
            if beat_strengths is not None and nearest_beat_idx < len(beat_strengths):
                beat_strength = beat_strengths[nearest_beat_idx]
        else:
            is_on_beat = False
            time_to_nearest_beat = 1.0
            beat_strength = 0.5
        
        # Dynamic image selection based on musical structure and intensity
        if is_on_beat and beat_strength > 0.6:
            # For strong beats, potentially change the image or use specific images
            # that work well on strong beats
            if current_intensity > 0.7:
                # For high energy segments, cycle through images more frequently on strong beats
                img_idx = (int(time_sec * current_intensity * 2) % len(image_frames))
            else:
                # For lower energy, change less frequently
                img_idx = (int(time_sec * 0.5) % len(image_frames))
        else:
            # Regular image progression tied to music structure
            if current_intensity > 0.8:
                # High energy segments: faster image changes
                img_idx = (int(time_sec * 1.5) % len(image_frames))
            elif current_intensity > 0.5:
                # Medium energy: standard rate
                img_idx = (int(time_sec * 1.0) % len(image_frames))
            else:
                # Low energy: slower changes
                img_idx = (int(time_sec * 0.5) % len(image_frames))
        
        # Get current frame from image array
        frame = image_frames[img_idx].copy()
        
        # Apply all effects based on current time and energy
        for effect in effects:
            # Modulate effect strength based on segment intensity
            # Lower intensity for high-energy effects during quiet parts
            if isinstance(effect, (ShakeEffect, FlashEffect, GlitchEffect)):
                # Reduce strength of dramatic effects for low energy segments
                effect.intensity = effect.intensity * (0.5 + current_intensity * 0.5)
            elif isinstance(effect, (PulseEffect, ColorShiftEffect)):
                # These effects work well regardless of energy
                pass
            elif isinstance(effect, AnticipationEffect) and time_to_nearest_beat < 0.3:
                # Boost anticipation effect as we approach beats
                effect.intensity = effect.intensity * (1.0 + (1.0 - time_to_nearest_beat/0.3) * 0.5)
            
            # Apply the effect
            frame = effect.apply(frame, time_sec)
        
        # Apply transition effect
        if transition_effect:
            frame = transition_effect.apply(frame, time_sec)
        
        # Write frame to video
        video_writer.write(frame)
        
        # Report progress periodically
        if frame_idx % progress_interval == 0 and frame_idx > progress_last_reported:
            progress_pct = int((frame_idx / total_frames) * 100)
            logger.info(f"Generating video: {progress_pct}% complete ({frame_idx}/{total_frames} frames)")
            progress_last_reported = frame_idx
    
    logger.info("Video generation complete (100%)") 