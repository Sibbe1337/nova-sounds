"""
Auto Mode implementation for YouTube Shorts video creation.
This module provides automatic content analysis and video generation functionality.
"""

import os
import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import cv2
import numpy as np

from src.app.core.settings import DEV_MODE
from src.app.services.video.processor import create_video_from_images
from src.app.services.video.enhanced_processor import (
    EnhancedVideoProcessor, 
    VideoProcessingOptions,
    create_enhanced_video
)
from src.app.services.video.music_responsive.presets import StylePreset
from src.app.services.music.recommendations import get_music_recommendation_service
from src.app.services.ai.metadata_generator import (
    generate_title,
    generate_description,
    generate_hashtags
)

# Set up logging
logger = logging.getLogger(__name__)

# Content categories
CONTENT_CATEGORIES = [
    "lifestyle", "education", "entertainment", "travel", 
    "sports", "beauty", "tech", "food", "music", "gaming"
]

class AutoModeProcessor:
    """Auto Mode processor for automatic video creation and optimization."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one processor instance exists."""
        if cls._instance is None:
            cls._instance = super(AutoModeProcessor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the Auto Mode processor."""
        if self._initialized:
            return
            
        self._initialized = True
        logger.info("Initialized Auto Mode processor")
        
        # Style presets for different content categories
        self.style_presets = {
            "nature": ["smooth", "cinematic", "dreamy"],
            "urban": ["energetic", "dynamic", "modern"],
            "people": ["portrait", "storytelling", "emotional"],
            "products": ["clean", "professional", "showcase"],
            "food": ["appetizing", "vibrant", "detailed"],
            "fashion": ["stylish", "elegant", "trendy"],
            "travel": ["adventure", "scenic", "documentary"],
            "technology": ["sleek", "futuristic", "minimal"],
            "art": ["creative", "artistic", "expressive"],
            "fitness": ["dynamic", "motivational", "energetic"]
        }
        
        # Transition presets for different content types
        self.transition_presets = {
            "smooth": "fade",
            "dynamic": "wipe",
            "creative": "zoom",
            "minimal": "cut",
            "professional": "dissolve"
        }
        
    def analyze_content(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Analyze the content of images to determine category, mood, and theme.
        
        Args:
            image_paths: List of paths to the images
            
        Returns:
            dict: Analysis results including category, mood, and theme
        """
        if DEV_MODE:
            # In development mode, return mock analysis
            logger.info(f"DEV mode: Generating mock content analysis for {len(image_paths)} images")
            return {
                "category": random.choice(CONTENT_CATEGORIES),
                "mood": random.choice(["happy", "calm", "energetic", "serious", "playful"]),
                "theme": random.choice(["lifestyle", "educational", "entertainment", "informative"]),
                "brightness": random.uniform(0.3, 0.8),
                "colorfulness": random.uniform(0.4, 0.9),
                "complexity": random.uniform(0.2, 0.7)
            }
            
        try:
            # Initialize aggregated metrics
            brightness_values = []
            colorfulness_values = []
            
            # Process each image to extract features
            for img_path in image_paths:
                img = cv2.imread(img_path)
                if img is None:
                    logger.warning(f"Could not read image at {img_path}")
                    continue
                    
                # Convert to RGB for analysis
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Calculate brightness
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                brightness = np.mean(hsv[:, :, 2]) / 255.0
                brightness_values.append(brightness)
                
                # Calculate colorfulness using the method by Hasler and Süsstrunk
                rg = np.abs(img_rgb[:, :, 0].astype(float) - img_rgb[:, :, 1].astype(float))
                yb = np.abs(0.5 * (img_rgb[:, :, 0].astype(float) + img_rgb[:, :, 1].astype(float)) - img_rgb[:, :, 2].astype(float))
                
                rg_mean, rg_std = np.mean(rg), np.std(rg)
                yb_mean, yb_std = np.mean(yb), np.std(yb)
                
                colorfulness = np.sqrt((rg_mean**2 + yb_mean**2)) + 0.3 * np.sqrt((rg_std**2 + yb_std**2))
                colorfulness = min(colorfulness / 100.0, 1.0)  # Normalize
                colorfulness_values.append(colorfulness)
            
            # Calculate average metrics
            avg_brightness = sum(brightness_values) / len(brightness_values) if brightness_values else 0.5
            avg_colorfulness = sum(colorfulness_values) / len(colorfulness_values) if colorfulness_values else 0.5
            
            # Implement more sophisticated content analysis with image classification models
            try:
                import tensorflow as tf
                import numpy as np
                from tensorflow.keras.applications import ResNet50
                from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
                
                # Load pre-trained model if not cached
                if not hasattr(self, "classification_model"):
                    self.classification_model = ResNet50(weights='imagenet')
                
                # Load images as frames for classification
                frames = []
                for img_path in image_paths:
                    img = cv2.imread(img_path)
                    if img is not None:
                        frames.append(img)
                
                if not frames:
                    raise ValueError("No valid frames found for classification")
                    
                # Select frames for classification (if we have many)
                frames_to_classify = frames[::max(1, len(frames) // 5)]
                
                # Limit to 5 frames for efficiency
                if len(frames_to_classify) > 5:
                    frames_to_classify = frames_to_classify[:5]
                
                # Process each frame and collect predictions
                all_predictions = []
                for frame in frames_to_classify:
                    # Resize image to match model input
                    img = cv2.resize(frame, (224, 224))
                    
                    # Convert BGR to RGB (TensorFlow models expect RGB)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    
                    # Preprocess for ResNet50
                    img_array = preprocess_input(np.expand_dims(img, axis=0))
                    
                    # Get predictions
                    predictions = self.classification_model.predict(img_array)
                    decoded = decode_predictions(predictions, top=5)[0]
                    
                    # Add to combined predictions
                    all_predictions.extend(decoded)
                
                # Group and count predictions
                prediction_counter = {}
                for _, label, conf in all_predictions:
                    if conf > 0.1:  # Only consider confident predictions
                        prediction_counter[label] = prediction_counter.get(label, 0) + conf
                
                # Sort by confidence
                sorted_predictions = sorted(prediction_counter.items(), key=lambda x: x[1], reverse=True)
                
                # Map predictions to content categories
                nature_keywords = {'water', 'sky', 'mountain', 'beach', 'forest', 'tree', 'lake', 'river', 'ocean', 'flower'}
                urban_keywords = {'building', 'street', 'city', 'car', 'bridge', 'tower', 'road', 'traffic'}
                people_keywords = {'person', 'people', 'man', 'woman', 'child', 'face', 'human'}
                animal_keywords = {'dog', 'cat', 'bird', 'fish', 'animal', 'pet'}
                food_keywords = {'food', 'fruit', 'vegetable', 'meal', 'dish', 'restaurant'}
                
                # Calculate category scores
                category_scores = {
                    'nature': 0,
                    'urban': 0,
                    'people': 0,
                    'animals': 0,
                    'food': 0,
                    'other': 0
                }
                
                for label, conf in sorted_predictions:
                    if any(keyword in label for keyword in nature_keywords):
                        category_scores['nature'] += conf
                    elif any(keyword in label for keyword in urban_keywords):
                        category_scores['urban'] += conf
                    elif any(keyword in label for keyword in people_keywords):
                        category_scores['people'] += conf
                    elif any(keyword in label for keyword in animal_keywords):
                        category_scores['animals'] += conf
                    elif any(keyword in label for keyword in food_keywords):
                        category_scores['food'] += conf
                    else:
                        category_scores['other'] += conf
                
                # Get top category
                top_category = max(category_scores.items(), key=lambda x: x[1])[0]
                
                # Set content category based on classification
                content_category = top_category
                
                # Adjust mood based on both basic metrics and content category
                if content_category == 'nature':
                    if avg_brightness > 0.6:
                        mood = "peaceful"
                    else:
                        mood = "mysterious"
                elif content_category == 'urban':
                    if avg_colorfulness > 0.6:
                        mood = "energetic"
                    else:
                        mood = "moody"
                elif content_category == 'people':
                    if avg_brightness > 0.6 and avg_colorfulness > 0.6:
                        mood = "happy"
                    else:
                        mood = "dramatic"
                else:
                    # Fall back to basic mood detection for other categories
                    if avg_brightness > 0.7 and avg_colorfulness > 0.7:
                        mood = "happy"
                    elif avg_brightness < 0.3 and avg_colorfulness < 0.3:
                        mood = "serious"
                    elif avg_brightness > 0.6 and avg_colorfulness < 0.4:
                        mood = "calm"
                    elif avg_brightness < 0.4 and avg_colorfulness > 0.6:
                        mood = "dramatic"
                    else:
                        mood = "neutral"
                
                logger.info(f"Content analysis: category={content_category}, mood={mood}")
                
            except Exception as e:
                logger.warning(f"Advanced content analysis failed, falling back to basic analysis: {e}")
                
                # Fall back to basic mood detection
                if avg_brightness > 0.7 and avg_colorfulness > 0.7:
                    mood = "happy"
                elif avg_brightness < 0.3 and avg_colorfulness < 0.3:
                    mood = "serious"
                elif avg_brightness > 0.6 and avg_colorfulness < 0.4:
                    mood = "calm"
                elif avg_brightness < 0.4 and avg_colorfulness > 0.6:
                    mood = "dramatic"
                else:
                    mood = "neutral"
                
            # Placeholder category (in a real implementation, use ML model)
            category = random.choice(CONTENT_CATEGORIES)
            
            return {
                "category": category,
                "mood": mood,
                "theme": "lifestyle",  # Placeholder
                "brightness": avg_brightness,
                "colorfulness": avg_colorfulness,
                "complexity": 0.5  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            # Fallback to default values
            return {
                "category": "general",
                "mood": "neutral",
                "theme": "lifestyle",
                "brightness": 0.5,
                "colorfulness": 0.5,
                "complexity": 0.5
            }
    
    def _select_music_track(self, content_analysis: Dict[str, Any]) -> str:
        """
        Select a music track based on content analysis
        
        Args:
            content_analysis: Content analysis results
            
        Returns:
            str: Selected music track ID
        """
        try:
            # Get recommended tracks based on content analysis
            recommendation_service = get_music_recommendation_service()
            
            recommendations = recommendation_service.recommend_by_keyword(
                keyword=content_analysis.get("mood", "neutral"),
                count=3
            )
            
            if not recommendations:
                # Fall back to trending tracks
                recommendations = recommendation_service.recommend_trending(count=3)
            
            if recommendations:
                # Return the first track name
                return recommendations[0]["track_name"]
            else:
                # Fall back to a default track
                logger.warning("No music recommendations found, using default track")
                return "default_track.mp3"
                
        except Exception as e:
            logger.error(f"Error selecting music track: {e}")
            return "default_track.mp3"
    
    def select_video_style(self, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select appropriate video style based on content analysis.
        
        Args:
            content_analysis: Results from content analysis
            
        Returns:
            dict: Video style settings
        """
        category = content_analysis.get("category", "general")
        mood = content_analysis.get("mood", "neutral")
        brightness = content_analysis.get("brightness", 0.5)
        colorfulness = content_analysis.get("colorfulness", 0.5)
        
        # Select a style preset based on content category
        available_presets = self.style_presets.get(category, ["standard", "dynamic", "smooth"])
        style = random.choice(available_presets)
        
        # Select transition style based on mood and metrics
        if mood in ["happy", "energetic"]:
            transition_style = "dynamic"
        elif mood in ["calm", "serious"]:
            transition_style = "smooth"
        elif colorfulness > 0.7:
            transition_style = "creative"
        else:
            transition_style = "minimal"
            
        transition = self.transition_presets.get(transition_style, "fade")
        
        # Determine music sync intensity based on content
        if mood in ["energetic", "happy"]:
            music_sync_intensity = 1.5
        elif mood == "dramatic":
            music_sync_intensity = 1.2
        else:
            music_sync_intensity = 0.8
            
        return {
            "style": style,
            "transition": transition,
            "music_sync_intensity": music_sync_intensity,
            "caption_style": "minimal" if brightness < 0.4 else "standard",
            "color_grading": "vibrant" if colorfulness < 0.5 else "natural"
        }

def analyze_content_and_get_settings(image_paths: List[str], user_settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze content and get optimal video settings for Auto Mode.
    
    Args:
        image_paths: List of paths to the images
        user_settings: Optional user-provided settings to override defaults
        
    Returns:
        dict: Complete settings for video creation
    """
    processor = AutoModeProcessor()
    
    # Analyze image content
    content_analysis = processor.analyze_content(image_paths)
    
    # Select music track based on content
    music_track = processor._select_music_track(content_analysis)
    
    # Select video style based on content
    video_style = processor.select_video_style(content_analysis)
    
    # Combine settings
    settings = {
        "content_analysis": content_analysis,
        "music_track": music_track,
        "video_style": video_style,
        "enable_music_sync": True,
        "use_smart_transitions": True,
        "enable_captions": False,  # Default to no captions
        "use_runway": False,       # Default to not using Runway ML
        "export_format": "mp4",
        "export_quality": 85
    }
    
    # Override with any user settings
    if user_settings:
        # Only allow overriding certain settings
        allowed_overrides = ["enable_music_sync", "use_smart_transitions", "enable_captions", "use_runway", "export_format", "export_quality"]
        for key in allowed_overrides:
            if key in user_settings:
                settings[key] = user_settings[key]
    
    return settings

def process_auto_mode_video(video_id: str, image_paths: List[str], settings: Dict[str, Any]) -> str:
    """
    Process a video in Auto Mode with the specified settings.
    
    Args:
        video_id: Unique ID for the video
        image_paths: List of paths to the images
        settings: Video creation settings
        
    Returns:
        str: Path to the created video
    """
    try:
        logger.info(f"Starting Auto Mode video processing for video {video_id}")
        
        # Extract settings
        music_track = settings.get("music_track", "default_track")
        video_style = settings.get("video_style", {})
        enable_music_sync = settings.get("enable_music_sync", True)
        use_smart_transitions = settings.get("use_smart_transitions", True)
        enable_captions = settings.get("enable_captions", False)
        use_runway = settings.get("use_runway", False)
        
        # Create output path
        output_dir = os.path.join("media", "videos")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{video_id}.mp4")
        
        # Create video processing options
        options = VideoProcessingOptions(
            enable_music_sync=enable_music_sync,
            music_sync_intensity=video_style.get("music_sync_intensity", 1.0),
            use_smart_transitions=use_smart_transitions,
            transition_style=video_style.get("transition", "fade"),
            enable_captions=enable_captions,
            caption_style=video_style.get("caption_style", "standard"),
            export_format=settings.get("export_format", "mp4"),
            export_quality=settings.get("export_quality", 85)
        )
        
        # Get preset based on style
        style = video_style.get("style", "standard")
        
        # Import StylePreset at the top of the function to avoid circular imports
        from src.app.services.video.music_responsive.presets import StylePreset
        
        try:
            # Use a direct mapping if possible to avoid potential errors
            if style.lower() == "standard":
                preset = StylePreset.STANDARD
            elif style.lower() == "energetic":
                preset = StylePreset.ENERGETIC
            elif style.lower() == "subtle":
                preset = StylePreset.SUBTLE
            elif style.lower() == "dramatic":
                preset = StylePreset.DRAMATIC
            elif style.lower() == "retro":
                preset = StylePreset.RETRO
            elif style.lower() == "glitch":
                preset = StylePreset.GLITCH
            elif style.lower() == "cinematic":
                preset = StylePreset.CINEMATIC
            elif style.lower() == "psychedelic":
                preset = StylePreset.PSYCHEDELIC
            elif style.lower() == "custom":
                preset = StylePreset.CUSTOM
            else:
                # Fall back to from_name method
                preset = StylePreset.from_name(style)
        except Exception as e:
            logger.warning(f"Error selecting StylePreset: {e}, using STANDARD preset instead")
            preset = StylePreset.STANDARD
        
        # Create enhanced video
        video_path = create_enhanced_video(
            images=image_paths,
            music_path=music_track,
            output_path=output_path,
            enable_beat_sync=options.enable_music_sync,
            sync_intensity=options.music_sync_intensity,
            enable_smart_transitions=options.use_smart_transitions,
            enable_captions=options.enable_captions,
            caption_style=options.caption_style,
            use_runway=use_runway
        )
        
        # Generate metadata using AI
        content_analysis = settings.get("content_analysis", {})
        category = content_analysis.get("category", "general")
        mood = content_analysis.get("mood", "neutral")
        
        title = generate_title(
            topic=category,
            trending_topics=[category, mood, "shorts"],
            music_track=music_track,
            image_content=[f"{category} {mood}"]
        )
        
        hashtags = generate_hashtags(
            topic=category,
            trending_hashtags=["#shorts", f"#{category}", f"#{mood}"],
            music_genre="unknown",
            count=5
        )
        
        # Update video metadata in database
        # This would typically call a database service
        video_metadata = {
            "id": video_id,
            "title": title,
            "description": f"Auto-generated {category} video with {mood} mood. #shorts",
            "hashtags": hashtags,
            "music_track": music_track,
            "status": "ready_for_upload",
            "created_at": str(datetime.now()),
            "path": video_path,
            "settings": settings
        }
        
        # In a real implementation, save this to database
        logger.info(f"Completed Auto Mode video processing for video {video_id}")
        logger.info(f"Metadata: {json.dumps(video_metadata)}")
        
        return video_path
        
    except Exception as e:
        logger.error(f"Error processing auto mode video: {e}")
        raise 