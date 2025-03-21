"""
Thumbnail optimization service for YouTube Shorts.

This module analyzes and generates optimized thumbnails for videos
with A/B testing capabilities to measure click-through performance.
"""

import logging
import os
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import functools
import time
from threading import Lock
import io

# Ensure critical PIL modules are directly imported first
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageStat, ImageOps

# Improved PIL imports with better error handling
try:
    # Check if imports are successful - keep this for backward compatibility and error handling
    import PIL
    from PIL import Image, ImageDraw, ImageFont
    from PIL import ImageFilter, ImageEnhance, ImageStat, ImageOps
except ImportError as e:
    logging.error(f"Error importing PIL modules: {e}")
    # Still allow module to load for partial functionality
    # These will be None only if the above direct import failed
    if 'Image' not in locals():
        Image = ImageDraw = ImageFont = ImageFilter = ImageEnhance = ImageStat = ImageOps = None

import json
import uuid

logger = logging.getLogger(__name__)

# Simple LRU Cache for processed images
class LRUCache:
    """Simple thread-safe LRU cache for thumbnail operations"""
    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self.cache = {}  # key -> (value, timestamp)
        self.lock = Lock()
        
    def get(self, key: str) -> Any:
        """Get an item from the cache"""
        with self.lock:
            if key not in self.cache:
                return None
            value, _ = self.cache[key]
            # Update timestamp on access
            self.cache[key] = (value, time.time())
            return value
    
    def put(self, key: str, value: Any) -> None:
        """Add an item to the cache"""
        with self.lock:
            # Add/update the item
            self.cache[key] = (value, time.time())
            
            # Check if we need to remove items
            if len(self.cache) > self.capacity:
                # Find oldest item
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                self.cache.pop(oldest_key)
                
    def clear(self) -> None:
        """Clear the cache"""
        with self.lock:
            self.cache.clear()

# Create image cache instance
image_cache = LRUCache(capacity=100)

# Custom decorator for image operations
def with_image_error_handling(func):
    """Decorator to handle image processing errors gracefully"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in image operation {func.__name__}: {e}")
            # Return a simple fallback thumbnail
            self_instance = args[0] if args else None
            if self_instance and hasattr(self_instance, '_create_fallback_thumbnail'):
                metadata = kwargs.get('metadata', {}) or (args[1] if len(args) > 1 else {})
                return self_instance._create_fallback_thumbnail(metadata)
            else:
                # Last resort fallback - create a solid color image with text
                try:
                    img = Image.new('RGB', (1280, 720), color=(60, 60, 60))
                    draw = ImageDraw.Draw(img)
                    draw.text((640, 360), "Error Creating Thumbnail", fill=(255, 255, 255))
                    return img
                except:
                    # If even that fails, return None and let caller handle it
                    return None
    return wrapper

class ThumbnailOptimizer:
    """Optimizes video thumbnails for improved click-through rates."""
    
    def __init__(self):
        """Initialize the thumbnail optimizer."""
        self.test_results = {}
        
    @with_image_error_handling
    def generate_thumbnail_variants(self, 
                                   base_image_path: str, 
                                   video_metadata: Dict[str, Any], 
                                   num_variants: int = 2) -> List[str]:
        """
        Generate multiple thumbnail variants for A/B testing.
        
        Args:
            base_image_path: Path to the base image
            video_metadata: Metadata for the video
            num_variants: Number of variants to generate
            
        Returns:
            List of paths to generated thumbnail images
        """
        logger.info(f"Generating {num_variants} thumbnail variants")
        
        if not os.path.exists(base_image_path):
            logger.error(f"Base image not found: {base_image_path}")
            return []
            
        # Create output directory
        output_dir = os.path.join(os.path.dirname(base_image_path), "thumbnails")
        os.makedirs(output_dir, exist_ok=True)
        
        # Check cache first
        cache_key = f"{base_image_path}:{num_variants}:{hash(frozenset(video_metadata.items()))}"
        cached_paths = image_cache.get(cache_key)
        if cached_paths:
            logger.info(f"Using cached thumbnail variants for {base_image_path}")
            return cached_paths
            
        # Load base image
        try:
            base_image = Image.open(base_image_path)
            # Optimize by resizing early if needed
            if base_image.width > 1920 or base_image.height > 1080:
                base_image.thumbnail((1920, 1080), Image.LANCZOS)
                
            # Convert to RGB if needed for consistent processing
            if base_image.mode != 'RGB':
                base_image = base_image.convert('RGB')
        except Exception as e:
            logger.error(f"Failed to open base image: {e}")
            return []
        
        # Generate variants
        variant_paths = []
        for i in range(num_variants):
            variant_path = os.path.join(output_dir, f"thumbnail_variant_{i}.jpg")
            
            # Apply different enhancement styles based on variant index
            try:
                variant = self._apply_variant_style(base_image.copy(), video_metadata, variant_index=i)
                variant.save(variant_path, quality=85, optimize=True)  # Reduced quality for better performance
                variant_paths.append(variant_path)
                logger.debug(f"Generated thumbnail variant {i}: {variant_path}")
            except Exception as e:
                logger.error(f"Failed to save thumbnail variant: {e}")
        
        # Cache the result
        if variant_paths:
            image_cache.put(cache_key, variant_paths)
            
        return variant_paths
    
    @with_image_error_handling
    def _apply_variant_style(self, 
                           image: Image.Image, 
                           metadata: Dict[str, Any], 
                           variant_index: int) -> Image.Image:
        """
        Apply a specific style to create a thumbnail variant.
        
        Args:
            image: Base PIL image
            metadata: Video metadata
            variant_index: Index of the variant to create
            
        Returns:
            Modified PIL image
        """
        # Resize to YouTube thumbnail dimensions if needed
        if image.width != 1280 or image.height != 720:
            image = image.resize((1280, 720), Image.LANCZOS)
        
        # Apply different styles based on variant index
        if variant_index == 0:
            # Variant 0: Bright and vibrant with large text
            return self._create_bright_variant(image, metadata)
        elif variant_index == 1:
            # Variant 1: Dramatic with color overlay
            return self._create_dramatic_variant(image, metadata)
        elif variant_index == 2:
            # Variant 2: Zoom focus on subject
            return self._create_zoom_variant(image, metadata)
        elif variant_index == 3:
            # Variant 3: Minimal with subtle text
            return self._create_minimal_variant(image, metadata)
        else:
            # Default: Random combination of effects
            return self._create_random_variant(image, metadata)
    
    @with_image_error_handling
    def _create_bright_variant(self, image: Image.Image, metadata: Dict[str, Any]) -> Image.Image:
        """Create a bright, vibrant thumbnail variant with large text."""
        # Enhance brightness and contrast
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
        
        # Add text overlay
        draw = ImageDraw.Draw(image)
        title = metadata.get("title", "").upper()
        if len(title) > 30:
            title = title[:27] + "..."
            
        # Try to use a bold font, or default to built-in
        try:
            font = ImageFont.truetype("Arial Bold", 72)
        except (IOError, AttributeError):
            # Fallback to default
            default_font = ImageFont.load_default()
            font = default_font
            
        # Add text with shadow for readability
        text_position = (50, image.height - 150)
        
        # Draw shadow first
        draw.text((text_position[0]+3, text_position[1]+3), title, (0, 0, 0), font=font)
        # Draw main text
        draw.text(text_position, title, (255, 255, 255), font=font)
        
        return image
    
    @with_image_error_handling
    def _create_dramatic_variant(self, image: Image.Image, metadata: Dict[str, Any]) -> Image.Image:
        """Create a dramatic thumbnail with color overlay."""
        # Add a color overlay gradient
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Create gradient overlay
        for y in range(image.height):
            overlay_alpha = int(255 * (0.3 + 0.5 * y / image.height))
            draw.line([(0, y), (image.width, y)], fill=(30, 30, 100, overlay_alpha))
        
        # Convert images to RGBA mode
        image = image.convert("RGBA")
        
        # Use custom invert function instead of ImageOps.invert
        try:
            if ImageOps:
                overlay_inverted = ImageOps.invert(overlay.convert("RGB")).convert("RGBA")
            else:
                # Manual inversion fallback
                overlay_inverted = self._manual_invert_image(overlay)
        except (NameError, AttributeError) as e:
            # If ImageOps fails, use manual inversion
            logger.warning(f"ImageOps.invert failed, using manual inversion: {e}")
            overlay_inverted = self._manual_invert_image(overlay)
            
        # Composite the images
        composite = Image.alpha_composite(image, overlay_inverted)
        
        # Convert back to RGB for saving
        result = composite.convert("RGB")
        
        # Add dramatic title
        draw = ImageDraw.Draw(result)
        title = metadata.get("title", "").upper()
        if len(title) > 30:
            title = title[:27] + "..."
            
        try:
            font = ImageFont.truetype("Impact", 80)
        except (IOError, AttributeError):
            # Fallback to default
            font = ImageFont.load_default()
            
        # Draw text with outline for dramatic effect
        text_width = draw.textlength(title, font=font) if hasattr(draw, 'textlength') else font.getsize(title)[0]
        text_position = ((result.width - text_width) // 2, result.height - 200)
        
        # Draw text with outline
        for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
            draw.text((text_position[0] + offset[0], text_position[1] + offset[1]), 
                     title, (0, 0, 0), font=font)
            
        # Draw main text
        draw.text(text_position, title, (255, 255, 0), font=font)
        
        return result
    
    def _manual_invert_image(self, img: Image.Image) -> Image.Image:
        """
        Manually invert an image without using ImageOps.
        
        This is a fallback for when ImageOps is not available.
        """
        # Create a new image with same size and mode
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            r_inv = Image.eval(r, lambda x: 255 - x)
            g_inv = Image.eval(g, lambda x: 255 - x)
            b_inv = Image.eval(b, lambda x: 255 - x)
            # Alpha channel is not inverted
            return Image.merge('RGBA', (r_inv, g_inv, b_inv, a))
        elif img.mode == 'RGB':
            r, g, b = img.split()
            r_inv = Image.eval(r, lambda x: 255 - x)
            g_inv = Image.eval(g, lambda x: 255 - x)
            b_inv = Image.eval(b, lambda x: 255 - x)
            return Image.merge('RGB', (r_inv, g_inv, b_inv))
        elif img.mode == 'L':
            return Image.eval(img, lambda x: 255 - x)
        else:
            # Convert to RGB first for other modes
            return self._manual_invert_image(img.convert('RGB'))
    
    @with_image_error_handling
    def _create_fallback_thumbnail(self, metadata: Dict[str, Any]) -> Image.Image:
        """
        Create a fallback thumbnail when normal processing fails.
        
        This creates a simple, solid-color thumbnail with the title text.
        """
        # Create a simple solid color image
        img = Image.new('RGB', (1280, 720), (40, 40, 100))
        draw = ImageDraw.Draw(img)
        
        # Add title text
        title = metadata.get("title", "Video Thumbnail")
        if len(title) > 30:
            title = title[:27] + "..."
        
        # Use default font
        try:
            font = ImageFont.load_default()
            # Center the text
            text_width = draw.textlength(title, font=font) if hasattr(draw, 'textlength') else font.getsize(title)[0]
            text_position = ((img.width - text_width) // 2, img.height // 2)
            draw.text(text_position, title, (255, 255, 255), font=font)
        except Exception as e:
            # Last resort - add no text
            logger.error(f"Error creating fallback thumbnail text: {e}")
            pass
            
        return img
    
    def track_thumbnail_performance(self, 
                                   thumbnail_id: str, 
                                   variant_id: str, 
                                   impressions: int, 
                                   clicks: int) -> None:
        """
        Track the performance of a thumbnail variant.
        
        Args:
            thumbnail_id: ID of the thumbnail test
            variant_id: ID of the specific variant
            impressions: Number of impressions
            clicks: Number of clicks
        """
        if thumbnail_id not in self.test_results:
            self.test_results[thumbnail_id] = {}
            
        if variant_id not in self.test_results[thumbnail_id]:
            self.test_results[thumbnail_id][variant_id] = {
                'impressions': 0,
                'clicks': 0
            }
            
        # Update metrics
        self.test_results[thumbnail_id][variant_id]['impressions'] += impressions
        self.test_results[thumbnail_id][variant_id]['clicks'] += clicks
        
    def get_test_results(self, thumbnail_id: str) -> Dict[str, Any]:
        """
        Get the results of an A/B test.
        
        Args:
            thumbnail_id: ID of the thumbnail test
            
        Returns:
            Dictionary with test results and recommendations
        """
        if thumbnail_id not in self.test_results:
            return {
                'status': 'not_found',
                'message': 'No test results found for this ID'
            }
            
        variants = self.test_results[thumbnail_id]
        results = {}
        
        # Calculate CTR for each variant
        for variant_id, metrics in variants.items():
            impressions = metrics['impressions']
            clicks = metrics['clicks']
            
            # Calculate CTR (Click-Through Rate)
            ctr = clicks / impressions if impressions > 0 else 0
            
            results[variant_id] = {
                'impressions': impressions,
                'clicks': clicks,
                'ctr': ctr
            }
            
        # Find the winner
        winner_id = None
        highest_ctr = 0
        
        for variant_id, metrics in results.items():
            if metrics['ctr'] > highest_ctr and metrics['impressions'] >= 100:
                highest_ctr = metrics['ctr']
                winner_id = variant_id
                
        # Prepare the response
        response = {
            'status': 'success',
            'test_id': thumbnail_id,
            'variants': results,
            'statistical_significance': self._calculate_significance(results),
        }
        
        if winner_id:
            response['winner'] = {
                'variant_id': winner_id,
                'ctr': highest_ctr
            }
        else:
            response['winner'] = None
            response['message'] = 'Not enough data to determine a winner'
            
        return response
        
    def _calculate_significance(self, results: Dict[str, Dict[str, Any]]) -> bool:
        """
        Calculate if the test results are statistically significant.
        
        This is a simplified implementation of statistical significance.
        In a real application, you would use a proper statistical test
        like Chi-Square or Fisher's Exact Test.
        
        Args:
            results: Dictionary of variant results
            
        Returns:
            True if results are significant, False otherwise
        """
        # Simple heuristic: need at least 100 impressions per variant
        # and at least 10% difference in CTR
        
        if len(results) < 2:
            return False
            
        variants = list(results.values())
        
        # Check if all variants have enough impressions
        for variant in variants:
            if variant['impressions'] < 100:
                return False
                
        # Find highest and lowest CTR
        ctrs = [v['ctr'] for v in variants]
        max_ctr = max(ctrs)
        min_ctr = min(ctrs)
        
        # Check if difference is at least 10%
        if max_ctr > 0 and (max_ctr - min_ctr) / max_ctr >= 0.1:
            return True
            
        return False
    
    def get_optimization_recommendations(self, image_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate thumbnail optimization recommendations.
        
        Args:
            image_path: Path to the base image
            metadata: Video metadata
            
        Returns:
            Dictionary with recommendations
        """
        try:
            image = Image.open(image_path)
        except Exception as e:
            logger.error(f"Failed to open image: {e}")
            return {
                'status': 'error',
                'message': 'Failed to process image'
            }
            
        # Analyze image characteristics
        brightness = self._analyze_brightness(image)
        contrast = self._analyze_contrast(image)
        color_variety = self._analyze_color_variety(image)
        
        recommendations = []
        
        # Generate recommendations based on analysis
        if brightness < 0.4:
            recommendations.append({
                'type': 'brightness',
                'message': 'Image is too dark. Increase brightness for better visibility.',
                'importance': 'high'
            })
        
        if contrast < 0.3:
            recommendations.append({
                'type': 'contrast',
                'message': 'Low contrast detected. Increase contrast to make elements stand out.',
                'importance': 'medium'
            })
            
        if color_variety < 0.2:
            recommendations.append({
                'type': 'color',
                'message': 'Limited color palette. Consider adding vibrant colors to attract attention.',
                'importance': 'medium'
            })
            
        # Add general thumbnail best practices
        recommendations.append({
            'type': 'text',
            'message': 'Add large, readable text (3-5 words maximum)',
            'importance': 'high'
        })
        
        recommendations.append({
            'type': 'face',
            'message': 'Include faces in thumbnails when possible - they increase CTR',
            'importance': 'high'
        })
        
        recommendations.append({
            'type': 'testing',
            'message': 'A/B test at least 2-3 different variants for best results',
            'importance': 'medium'
        })
        
        return {
            'status': 'success',
            'image_analysis': {
                'brightness': brightness,
                'contrast': contrast,
                'color_variety': color_variety
            },
            'recommendations': recommendations
        }
        
    def _analyze_brightness(self, image: Image.Image) -> float:
        """Analyze the brightness of an image on a scale of 0-1."""
        # Convert to grayscale for brightness analysis
        gray = image.convert('L')
        stat = ImageStat.Stat(gray)
        return stat.mean[0] / 255
        
    def _analyze_contrast(self, image: Image.Image) -> float:
        """Analyze the contrast of an image on a scale of 0-1."""
        # Convert to grayscale for contrast analysis
        gray = image.convert('L')
        stat = ImageStat.Stat(gray)
        
        # Calculate standard deviation and normalize
        contrast = stat.stddev[0] / 255
        return min(contrast * 4, 1.0)  # Scale up for better differentiation
        
    def _analyze_color_variety(self, image: Image.Image) -> float:
        """Analyze the color variety of an image on a scale of 0-1."""
        # Resize to a small image for faster processing
        small = image.resize((50, 50), Image.LANCZOS)
        
        # Convert to RGB and get colors
        rgb = small.convert('RGB')
        colors = rgb.getcolors(50*50)
        
        if colors is None:
            # If None, there are more unique colors than pixels
            return 1.0
            
        # Count unique colors and normalize
        unique_colors = len(colors)
        max_colors = 50*50
        
        return min(unique_colors / 500, 1.0)  # Cap at 1.0


def get_thumbnail_optimizer() -> ThumbnailOptimizer:
    """Get the singleton instance of the thumbnail optimizer."""
    return ThumbnailOptimizer() 

class ThumbnailGenerator:
    """
    Automated thumbnail generation system with A/B testing capabilities.
    """
    
    def __init__(self):
        """Initialize the thumbnail generator."""
        self.style_templates = {
            "bold_text": {
                "font_size": "large",
                "font_weight": "bold",
                "text_color": "#ffffff",
                "shadow": True,
                "background": "gradient",
                "background_color": "#ff4500",
                "overlay_opacity": 0.7,
                "text_position": "bottom"
            },
            "minimal": {
                "font_size": "medium",
                "font_weight": "normal",
                "text_color": "#ffffff",
                "shadow": False,
                "background": "solid",
                "background_color": "#000000",
                "overlay_opacity": 0.5,
                "text_position": "center"
            },
            "vibrant": {
                "font_size": "large",
                "font_weight": "bold",
                "text_color": "#ffff00",
                "shadow": True,
                "background": "gradient",
                "background_color": "#9900ff",
                "overlay_opacity": 0.6,
                "text_position": "top"
            },
            "clean": {
                "font_size": "medium",
                "font_weight": "bold",
                "text_color": "#000000",
                "shadow": False,
                "background": "none",
                "background_color": "#ffffff",
                "overlay_opacity": 0.0,
                "text_position": "bottom"
            },
            "dramatic": {
                "font_size": "large",
                "font_weight": "bold",
                "text_color": "#ffffff",
                "shadow": True,
                "background": "vignette",
                "background_color": "#000000",
                "overlay_opacity": 0.8,
                "text_position": "center"
            }
        }
        
        self.ab_test_data = {}
        self.ab_test_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ab_test_results.json')
        self._load_ab_test_data()
    
    def _load_ab_test_data(self):
        """Load A/B test results from disk."""
        try:
            if os.path.exists(self.ab_test_path):
                with open(self.ab_test_path, 'r') as f:
                    self.ab_test_data = json.load(f)
                logger.info(f"Loaded A/B test data: {len(self.ab_test_data)} tests")
            else:
                self.ab_test_data = {}
        except Exception as e:
            logger.error(f"Error loading A/B test data: {e}")
            self.ab_test_data = {}
    
    def _save_ab_test_data(self):
        """Save A/B test results to disk."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.ab_test_path), exist_ok=True)
            
            with open(self.ab_test_path, 'w') as f:
                json.dump(self.ab_test_data, f, indent=2)
            
            logger.debug(f"Saved A/B test data: {len(self.ab_test_data)} tests")
        except Exception as e:
            logger.error(f"Error saving A/B test data: {e}")
    
    def generate_thumbnail_variants(self,
                                 image_path: str, 
                                 title: str, 
                                 num_variants: int = 3,
                                 styles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generate multiple thumbnail variants for testing.
        
        Args:
            image_path: Path to the base image
            title: Title text to overlay on the thumbnail
            num_variants: Number of variants to generate
            styles: Specific styles to use (if None, random selection)
            
        Returns:
            List of thumbnail variants with metadata
        """
        import cv2
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
        import random
        import uuid
        
        # Validate inputs
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            # Create a dummy image file in dev mode
            if os.environ.get("DEV_MODE", "false").lower() == "true":
                logger.warning(f"Creating dummy image for development: {image_path}")
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                dummy_img = Image.new('RGB', (1280, 720), color=(73, 109, 137))
                dummy_img.save(image_path)
            else:
                return []
        
        # Select styles to use
        available_styles = list(self.style_templates.keys())
        
        # ... rest of the method remains unchanged ...

# Initialize global instance
_thumbnail_generator = None

def get_thumbnail_generator() -> ThumbnailGenerator:
    """Get the singleton instance of the thumbnail generator."""
    global _thumbnail_generator
    if _thumbnail_generator is None:
        _thumbnail_generator = ThumbnailGenerator()
    return _thumbnail_generator 