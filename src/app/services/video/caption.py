"""
Auto-captioning service for YouTube Shorts using Whisper AI.
"""
import os
import tempfile
import subprocess
import logging
import json
import cv2
import numpy as np
import time
import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Union, Literal
from pathlib import Path

from src.app.core.settings import DEV_MODE, get_setting, DEBUG_MODE

# Add simulated OpenAI module
try:
    import openai
except ImportError:
    # Create a placeholder module if OpenAI is not installed
    class OpenAIPlaceholder:
        class ChatCompletion:
            @staticmethod
            def create(*args, **kwargs):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "This is a placeholder response from the OpenAI API."
                            }
                        }
                    ]
                }
        
        class Completion:
            @staticmethod
            def create(*args, **kwargs):
                return {
                    "choices": [
                        {
                            "text": "This is a placeholder response from the OpenAI API."
                        }
                    ]
                }
    
    openai = OpenAIPlaceholder()
    logging.warning("OpenAI module not found. Using placeholder implementation.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CaptionStyle:
    """Configuration for caption appearance and positioning."""
    font: int = cv2.FONT_HERSHEY_DUPLEX
    font_scale: float = 1.0  # Will be adjusted based on video width
    font_color: Tuple[int, int, int] = (255, 255, 255)  # White
    font_thickness: int = 2  # Will be adjusted based on video width
    bg_color: Tuple[int, int, int] = (0, 0, 0)  # Black
    bg_opacity: float = 0.6  # Background opacity (0.0-1.0)
    position: Literal["bottom", "top", "center"] = "bottom"
    margin: int = 50  # Distance from edge in pixels
    padding: int = 10  # Padding around text
    max_width_pct: float = 0.9  # Maximum width of caption as percentage of video width
    text_wrap: bool = True  # Whether to wrap text that exceeds max width
    animate: bool = False  # Whether to animate captions (fade in/out)
    outline: bool = True  # Whether to add text outline for better visibility
    outline_color: Tuple[int, int, int] = (0, 0, 0)  # Black outline
    outline_thickness: int = 1
    # Enhanced animation features
    animation_type: Literal["none", "fade", "scale", "bounce", "wave", "typing", "beat_sync"] = "none"
    beat_sensitive: bool = False  # Whether caption animation should respond to music beats
    highlight_keywords: bool = False  # Whether to highlight important keywords
    keyword_color: Tuple[int, int, int] = (255, 255, 0)  # Yellow for keywords
    emphasis_scale: float = 1.2  # Scale factor for emphasized words
    max_animation_scale: float = 1.5  # Maximum scale during animation
    

@dataclass
class TranscriptionSegment:
    """A segment of transcribed text with timing information."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text
    emphasis: List[str] = None  # Words to emphasize (if any)
    confidence: float = 1.0  # Confidence level of transcription (0.0-1.0)
    
    def __post_init__(self):
        if self.emphasis is None:
            self.emphasis = []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptionSegment':
        """Create a TranscriptionSegment from a dictionary."""
        emphasis = data.get("emphasis", [])
        confidence = data.get("confidence", 1.0)
        return cls(
            start=data.get("start", 0.0),
            end=data.get("end", 0.0),
            text=data.get("text", "").strip(),
            emphasis=emphasis,
            confidence=confidence
        )

@dataclass
class TranscriptionResult:
    """Complete transcription results."""
    text: str  # Full transcription text
    segments: List[TranscriptionSegment]  # Segments with timestamps
    language: str  # Detected language

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptionResult':
        """Create a TranscriptionResult from a dictionary."""
        return cls(
            text=data.get("text", ""),
            segments=[TranscriptionSegment.from_dict(segment) for segment in data.get("segments", [])],
            language=data.get("language", "en")
        )

    @classmethod
    def create_mock(cls) -> 'TranscriptionResult':
        """Create a mock transcription for development mode."""
        return cls(
            text="This is a mock transcription for development mode",
            segments=[
                TranscriptionSegment(0.0, 2.0, "This is a mock"),
                TranscriptionSegment(2.0, 4.0, "transcription for"),
                TranscriptionSegment(4.0, 6.0, "development mode")
            ],
            language="en"
        )

def extract_audio(video_path: str, output_path: Optional[str] = None) -> str:
    """
    Extract audio from a video file.
    
    Args:
        video_path: Path to the video file
        output_path: Optional path to save audio file
        
    Returns:
        str: Path to extracted audio file
    """
    if output_path is None:
        # Create a temporary file if no output path is provided
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"{os.path.basename(video_path)}_audio.wav")
    
    # Use FFmpeg to extract audio
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vn',                # No video
        '-acodec', 'pcm_s16le',  # PCM 16-bit format
        '-ar', '16000',       # Sample rate 16kHz (good for speech recognition)
        '-ac', '1',           # Mono channel
        output_path
    ]
    
    logger.info(f"Extracting audio from {video_path} to {output_path}")
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract audio: {e.stderr}")
        if DEBUG_MODE:
            # Create an empty audio file for debugging
            Path(output_path).touch()
            return output_path
        raise

def transcribe_audio_whisper(audio_path: str, 
                            language: str = "en", 
                            model_size: str = "base", 
                            api_key: Optional[str] = None) -> TranscriptionResult:
    """
    Transcribe audio using the OpenAI Whisper API with enhanced features.
    
    Args:
        audio_path: Path to the audio file
        language: Language code (e.g., "en", "es", etc.)
        model_size: Whisper model size to use
        api_key: OpenAI API key (if None, will check environment)
        
    Returns:
        TranscriptionResult: The transcription with timing information
    """
    # Check for development mode
    if DEV_MODE:
        logger.info(f"DEV mode: Using mock transcription for {audio_path}")
        return TranscriptionResult.create_mock()
    
    # Get API key from environment if not provided
    api_key = api_key or get_setting("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("No OpenAI API key found, falling back to local Whisper model")
        return _transcribe_with_local_whisper(audio_path, language, model_size)
    
    # Use OpenAI API for transcription
    try:
        logger.info(f"Transcribing audio with Whisper API (model: {model_size})")
        return _transcribe_with_openai_api(audio_path, language, api_key)
    except Exception as e:
        logger.error(f"Error using OpenAI API: {e}")
        logger.warning("Falling back to local Whisper model")
        return _transcribe_with_local_whisper(audio_path, language, model_size)

def _transcribe_with_local_whisper(audio_path: str, language: str, model_size: str) -> TranscriptionResult:
    """
    Transcribe audio using local Whisper model.
    
    Args:
        audio_path: Path to the audio file
        language: Language code
        model_size: Whisper model size to use
        
    Returns:
        TranscriptionResult: The transcription with timing information
    """
    try:
        # Try to import whisper
        import whisper
    except ImportError:
        logger.error("Could not import whisper. Please install it with: pip install openai-whisper")
        return TranscriptionResult.create_mock()
    
    try:
        logger.info(f"Loading local Whisper model: {model_size}")
        model = whisper.load_model(model_size)
        
        # Set options for word-level timestamps if available
        options = {"language": language}
        if hasattr(whisper, "DecodingOptions") and hasattr(whisper.DecodingOptions, "word_timestamps"):
            options["word_timestamps"] = True
        
        logger.info("Transcribing audio with local Whisper model")
        result = model.transcribe(audio_path, **options)
        
        # Process the result
        if "segments" in result:
            segments = [
                TranscriptionSegment(
                    start=segment.get("start", 0),
                    end=segment.get("end", 0),
                    text=segment.get("text", "").strip(),
                    confidence=segment.get("confidence", 1.0)
                )
                for segment in result.get("segments", [])
            ]
            
            # If word level timestamps are available, identify emphasis words
            if "words" in result:
                # Identify potentially emphasized words by analyzing delivery
                for segment in segments:
                    # Simple heuristic: words that are spoken more slowly might be emphasized
                    words_in_segment = [w for w in result["words"] 
                                       if w["start"] >= segment.start and w["end"] <= segment.end]
                    
                    if words_in_segment:
                        avg_word_duration = sum(w["end"] - w["start"] for w in words_in_segment) / len(words_in_segment)
                        
                        # Words spoken more slowly or with higher confidence might be emphasized
                        emphasis = []
                        for word in words_in_segment:
                            duration = word["end"] - word["start"]
                            # If word is spoken significantly more slowly than average, might be emphasis
                            if duration > avg_word_duration * 1.5:
                                emphasis.append(word["word"])
                        
                        segment.emphasis = emphasis
            
            return TranscriptionResult(
                text=result.get("text", ""),
                segments=segments,
                language=result.get("language", language)
            )
        else:
            # Simple result without segments
            return TranscriptionResult(
                text=result.get("text", ""),
                segments=[TranscriptionSegment(0, 0, result.get("text", ""))],
                language=result.get("language", language)
            )
    
    except Exception as e:
        logger.error(f"Error transcribing with local Whisper model: {e}")
        return TranscriptionResult.create_mock()

def _transcribe_with_openai_api(audio_path: str, language: str, api_key: str) -> TranscriptionResult:
    """
    Transcribe audio using OpenAI's Whisper API.
    
    Args:
        audio_path: Path to the audio file
        language: ISO language code
        api_key: OpenAI API key
        
    Returns:
        TranscriptionResult: Transcription results
    """
    from openai import OpenAI  # Import here to avoid dependency issues
    
    client = OpenAI(api_key=api_key)
    
    # Open the audio file
    with open(audio_path, "rb") as audio_file:
        # Call the OpenAI API
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"]
        )
    
    # Convert API response to our TranscriptionResult format
    result = TranscriptionResult(
        text=response.text,
        segments=[
            TranscriptionSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text
            )
            for segment in response.segments
        ],
        language=language
    )
    
    return result

def _wrap_text(text: str, max_width: int, font, font_scale, font_thickness) -> List[str]:
    """
    Wrap text to fit within max_width pixels.
    
    Args:
        text: Text to wrap
        max_width: Maximum width in pixels
        font, font_scale, font_thickness: Font parameters for size calculation
        
    Returns:
        List[str]: List of wrapped text lines
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        # Try adding the word to the current line
        test_line = ' '.join(current_line + [word])
        text_size, _ = cv2.getTextSize(test_line, font, font_scale, font_thickness)
        
        if text_size[0] <= max_width or not current_line:
            # Word fits or it's the first word of the line
            current_line.append(word)
        else:
            # Word doesn't fit, start a new line
            lines.append(' '.join(current_line))
            current_line = [word]
    
    # Add the last line
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def add_captions_to_frames(frames: List[np.ndarray],
                         transcription: TranscriptionResult,
                         fps: int = 30,
                         style: Optional[CaptionStyle] = None,
                         music_analyzer = None) -> List[np.ndarray]:
    """
    Add captions to frames with enhanced animations and music sync.
    
    Args:
        frames: List of video frames
        transcription: Transcription result with timing
        fps: Frames per second
        style: Caption style configuration
        music_analyzer: Optional music analyzer for beat-synced animations
        
    Returns:
        List[np.ndarray]: Frames with captions added
    """
    if not frames:
        logger.warning("No frames provided for captioning")
        return frames
    
    # Use default style if not provided
    if style is None:
        style = CaptionStyle()
    
    # Adjust font size based on video width
    if frames and len(frames) > 0:
        frame_width = frames[0].shape[1]
        adjusted_scale = frame_width / 1080.0  # Reference width
        style.font_scale = style.font_scale * adjusted_scale
        style.font_thickness = max(1, int(style.font_thickness * adjusted_scale))
    
    # Process each frame
    captioned_frames = []
    for i, frame in enumerate(frames):
        # Calculate current time
        time_sec = i / fps
        
        # Get segment for current time
        current_segment = None
        for segment in transcription.segments:
            if segment.start <= time_sec <= segment.end:
                current_segment = segment
                break
        
        # If no segment for current time, copy frame as is
        if current_segment is None:
            captioned_frames.append(frame.copy())
            continue
        
        # Calculate caption appearance parameters
        caption_text = current_segment.text
        
        # Check for empty caption
        if not caption_text or caption_text.isspace():
            captioned_frames.append(frame.copy())
            continue
        
        # Add caption with potential animations and effects
        if style.animate or style.beat_sensitive or style.animation_type != "none":
            # Determine animation parameters
            animation_progress = 0.0
            if current_segment.end > current_segment.start:
                animation_progress = (time_sec - current_segment.start) / (current_segment.end - current_segment.start)
            
            # Apply different animation types
            if style.animation_type == "fade":
                # Calculate opacity based on timing
                if animation_progress < 0.2:
                    opacity = animation_progress / 0.2
                elif animation_progress > 0.8:
                    opacity = (1.0 - animation_progress) / 0.2
                else:
                    opacity = 1.0
                
                frame_with_caption = _add_caption_with_opacity(
                    frame.copy(), caption_text, style, current_segment, opacity
                )
                
            elif style.animation_type == "scale":
                # Calculate scale factor based on timing
                if animation_progress < 0.2:
                    scale = 0.5 + (animation_progress / 0.2) * 0.5
                elif animation_progress > 0.8:
                    scale = 1.0 - ((animation_progress - 0.8) / 0.2) * 0.5
                else:
                    scale = 1.0
                
                frame_with_caption = _add_caption_with_scale(
                    frame.copy(), caption_text, style, current_segment, scale
                )
                
            elif style.animation_type == "beat_sync" and music_analyzer:
                # Get beat intensity at current time
                try:
                    from src.app.services.video.music_responsive.enums import MusicFeature
                    beat_value = music_analyzer.get_feature_at_time(MusicFeature.BEATS, time_sec)
                    
                    # Scale factor based on beat intensity
                    scale = 1.0 + beat_value * (style.max_animation_scale - 1.0)
                    
                    frame_with_caption = _add_caption_with_scale(
                        frame.copy(), caption_text, style, current_segment, scale
                    )
                except Exception as e:
                    logger.warning(f"Error with beat-synced captioning: {e}")
                    frame_with_caption = _add_caption_with_default(
                        frame.copy(), caption_text, style, current_segment
                    )
                    
            elif style.animation_type == "wave":
                frame_with_caption = _add_caption_with_wave(
                    frame.copy(), caption_text, style, current_segment, animation_progress
                )
                
            elif style.animation_type == "typing":
                frame_with_caption = _add_caption_with_typing(
                    frame.copy(), caption_text, style, current_segment, animation_progress
                )
                
            else:
                frame_with_caption = _add_caption_with_default(
                    frame.copy(), caption_text, style, current_segment
                )
        else:
            # Standard non-animated caption
            frame_with_caption = _add_caption_with_default(
                frame.copy(), caption_text, style, current_segment
            )
        
        captioned_frames.append(frame_with_caption)
    
    return captioned_frames

def _add_caption_with_opacity(frame, text, style, segment, opacity):
    """Add caption with specified opacity level."""
    # Make a copy of the style with adjusted opacity
    adjusted_style = CaptionStyle(**vars(style))
    adjusted_style.bg_opacity = opacity * style.bg_opacity
    
    return _add_caption_with_default(frame, text, adjusted_style, segment)

def _add_caption_with_scale(frame, text, style, segment, scale):
    """Add caption with specified scale factor."""
    # Make a copy of the style with adjusted scale
    adjusted_style = CaptionStyle(**vars(style))
    adjusted_style.font_scale = style.font_scale * scale
    
    return _add_caption_with_default(frame, text, adjusted_style, segment)

def _add_caption_with_wave(frame, text, style, segment, progress):
    """Add caption with wave animation effect."""
    # Split text into characters
    chars = list(text)
    frame_height, frame_width = frame.shape[:2]
    
    # Determine base position
    max_width = int(frame_width * style.max_width_pct)
    font = style.font
    font_scale = style.font_scale
    thickness = style.font_thickness
    
    # Calculate text size for the whole text
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Create blank image for text
    text_img = np.zeros((text_height + baseline + 20, frame_width, 4), dtype=np.uint8)
    
    # Position for individual characters
    x_pos = (frame_width - text_width) // 2
    y_pos = text_height + 10
    
    # Draw each character with individual wave offset
    for i, char in enumerate(chars):
        # Calculate wave offset
        wave_phase = progress * 10 + i * 0.3  # Varies by character position and time
        y_offset = int(np.sin(wave_phase) * 5)  # Amplitude of 5 pixels
        
        # Draw character
        cv2.putText(
            text_img,
            char,
            (x_pos, y_pos + y_offset),
            font,
            font_scale,
            (255, 255, 255, 255),
            thickness
        )
        
        # Increment x position
        (char_width, _), _ = cv2.getTextSize(char, font, font_scale, thickness)
        x_pos += char_width
    
    # Create mask for background
    mask = text_img[..., 3:] / 255.0
    
    # Determine y position in frame
    if style.position == "bottom":
        y_frame_pos = frame_height - text_height - style.margin
    elif style.position == "top":
        y_frame_pos = style.margin
    else:  # "center"
        y_frame_pos = (frame_height - text_height) // 2
    
    # Merge with frame
    roi = frame[
        y_frame_pos:y_frame_pos + text_img.shape[0],
        (frame_width - text_img.shape[1]) // 2:(frame_width + text_img.shape[1]) // 2
    ]
    
    # Make sure ROI is within frame boundaries
    if roi.shape[:2] != text_img.shape[:2]:
        return frame  # Skip if sizes don't match
    
    # Add semi-transparent background
    bg_color = np.array(style.bg_color)
    bg = np.ones_like(roi) * bg_color.reshape(1, 1, 3)
    alpha = style.bg_opacity * mask
    roi = roi * (1 - alpha) + bg * alpha
    
    # Add text
    roi = roi * (1 - mask) + text_img[..., :3] * mask
    
    # Update frame
    frame[
        y_frame_pos:y_frame_pos + text_img.shape[0],
        (frame_width - text_img.shape[1]) // 2:(frame_width + text_img.shape[1]) // 2
    ] = roi
    
    return frame

def _add_caption_with_typing(frame, text, style, segment, progress):
    """Add caption with typing animation effect."""
    # Calculate how much of the text to show
    show_chars = int(len(text) * min(1.0, progress * 1.2))  # Multiply by 1.2 to finish typing before end
    partial_text = text[:show_chars]
    
    # Draw the partial text
    return _add_caption_with_default(frame, partial_text, style, segment)

def _add_caption_with_default(frame, text, style, segment):
    """Add caption with default styling."""
    if not text:
        return frame
    
    frame_height, frame_width = frame.shape[:2]
    max_width = int(frame_width * style.max_width_pct)
    font = style.font
    font_scale = style.font_scale
    thickness = style.font_thickness
    
    # Wrap text if needed
    if style.text_wrap:
        text_lines = _wrap_text(text, max_width, font, font_scale, thickness)
    else:
        text_lines = [text]
    
    # Calculate text height
    (_, text_height), baseline = cv2.getTextSize("Ay", font, font_scale, thickness)
    line_height = text_height + baseline + style.padding
    total_height = line_height * len(text_lines)
    
    # Determine position
    if style.position == "bottom":
        y_pos = frame_height - style.margin - total_height
    elif style.position == "top":
        y_pos = style.margin
    else:  # "center"
        y_pos = (frame_height - total_height) // 2
    
    # Add each line of text
    current_y = y_pos
    for line in text_lines:
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(line, font, font_scale, thickness)
        
        # Center text horizontally
        x_pos = (frame_width - text_width) // 2
        
        # Create background rectangle
        bg_start = (x_pos - style.padding, current_y - text_height - style.padding)
        bg_end = (x_pos + text_width + style.padding, current_y + style.padding)
        
        # Draw semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, bg_start, bg_end, style.bg_color, -1)
        frame = cv2.addWeighted(overlay, style.bg_opacity, frame, 1 - style.bg_opacity, 0)
        
        # Identify emphasized words if enabled
        if style.highlight_keywords and segment.emphasis:
            # Split line into words
            words = line.split()
            x_current = x_pos
            
            for word in words:
                # Get word size
                (word_width, _), _ = cv2.getTextSize(word + " ", font, font_scale, thickness)
                
                # Check if this is an emphasized word
                is_emphasized = any(
                    emphasis.lower() in word.lower() for emphasis in segment.emphasis
                )
                
                # Draw word with appropriate style
                if is_emphasized:
                    # For emphasized words
                    emphasis_scale = style.emphasis_scale
                    emphasis_font_scale = font_scale * emphasis_scale
                    # Adjust position to keep the baseline consistent
                    (_, emph_height), emph_baseline = cv2.getTextSize(word, font, emphasis_font_scale, thickness)
                    y_adjust = (text_height - emph_height) // 2
                    cv2.putText(
                        frame, word, (x_current, current_y + y_adjust), 
                        font, emphasis_font_scale, style.keyword_color, thickness
                    )
                else:
                    # Regular words
                    cv2.putText(frame, word, (x_current, current_y), font, font_scale, style.font_color, thickness)
                
                # Add space width
                space_width = int(word_width * 0.3)
                x_current += word_width
        else:
            # Draw entire line
            if style.outline:
                # Draw outline
                cv2.putText(
                    frame, line, (x_pos, current_y), 
                    font, font_scale, style.outline_color, 
                    thickness + style.outline_thickness
                )
            
            # Draw text
            cv2.putText(
                frame, line, (x_pos, current_y), 
                font, font_scale, style.font_color, 
                thickness
            )
        
        # Move to next line
        current_y += line_height
    
    return frame

def add_captions_to_video(
    video_path: str, 
    output_path: str, 
    language: str = "en",
    model_size: str = "base",
    caption_style: Optional[CaptionStyle] = None,
    api_key: Optional[str] = None,
    music_path: Optional[str] = None,
    music_analyzer = None
) -> str:
    """
    Add captions to a video.
    
    Args:
        video_path: Path to the input video
        output_path: Path to save the output video
        language: Language code (e.g., 'en' for English)
        model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        caption_style: Optional caption style configuration
        api_key: Optional OpenAI API key for using their service
        music_path: Optional path to music file for beat-synced captions
        music_analyzer: Optional pre-initialized music analyzer
    
    Returns:
        Path to the output video with captions
    """
    # Check if output path exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Extract audio from video
    audio_path = extract_audio(video_path)
    
    try:
        # Open the video
        logger.info(f"Opening video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            return ""
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video properties: {width}x{height}, {fps} fps, {total_frames} frames")
        
        # Transcribe audio
        logger.info("Transcribing audio...")
        transcription = transcribe_audio_whisper(audio_path, language, model_size, api_key)
        
        # Read frames from video
        logger.info("Reading video frames...")
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        
        logger.info(f"Read {len(frames)} frames")
        
        # 4. Add captions to frames
        logger.info("Adding captions to frames...")
        music_analyzer_obj = None
        if music_path:
            try:
                from src.app.services.video.music_responsive.analyzer import MusicAnalyzer
                music_analyzer_obj = MusicAnalyzer(music_path)
                logger.info("Music analyzer initialized for beat-synced captions")
            except ImportError as e:
                logger.warning(f"Could not initialize music analyzer: {e}")
        
        captioned_frames = add_captions_to_frames(
            frames, transcription, fps, caption_style, music_analyzer_obj
        )
        
        # 5. Write output video
        logger.info(f"Writing captioned video to {output_path}")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in captioned_frames:
            out.write(frame)
            
        out.release()
        
        logger.info("Captioning completed successfully")
        return output_path
    
    except Exception as e:
        logger.error(f"Error adding captions to video: {e}")
        return ""
    
    finally:
        # Clean up temporary audio file
        if audio_path and os.path.exists(audio_path) and audio_path.startswith(tempfile.gettempdir()):
            try:
                os.remove(audio_path)
            except Exception as e:
                logger.warning(f"Error removing temporary audio file: {e}")

def create_styled_captions(
    video_path: str,
    output_path: str,
    style_preset: str = "default",
    language: str = "en",
    model_size: str = "base"
) -> str:
    """
    Create a captioned video with preset styles.
    
    Args:
        video_path: Path to the video file
        output_path: Path to save the captioned video
        style_preset: Style preset name (default, subtitle, tiktok, youtube, minimal)
        language: Language code for transcription
        model_size: Whisper model size
        
    Returns:
        str: Path to the captioned video file
    """
    # Define style presets
    style_presets = {
        "default": CaptionStyle(),
        "subtitle": CaptionStyle(
            font=cv2.FONT_HERSHEY_SIMPLEX,
            font_scale=1.0,
            font_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            bg_opacity=0.7,
            position="bottom",
            text_wrap=True,
            outline=True
        ),
        "tiktok": CaptionStyle(
            font=cv2.FONT_HERSHEY_DUPLEX,
            font_scale=1.2,
            font_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            bg_opacity=0.8,
            position="center",
            text_wrap=True,
            animate=True,
            outline=True
        ),
        "youtube": CaptionStyle(
            font=cv2.FONT_HERSHEY_TRIPLEX,
            font_scale=1.0,
            font_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            bg_opacity=0.6,
            position="bottom",
            margin=80,
            text_wrap=True,
            outline=False
        ),
        "minimal": CaptionStyle(
            font=cv2.FONT_HERSHEY_SIMPLEX,
            font_scale=0.8,
            font_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            bg_opacity=0.5,
            position="bottom",
            text_wrap=True,
            outline=False
        )
    }
    
    # Get the style preset or use default
    style = style_presets.get(style_preset.lower(), style_presets["default"])
    
    # Process the video with the selected style
    return add_captions_to_video(
        video_path=video_path,
        output_path=output_path,
        language=language,
        model_size=model_size,
        caption_style=style
    ) 