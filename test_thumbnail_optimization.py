"""
Test script for thumbnail optimization and A/B testing.

This script tests the functionality of the thumbnail optimizer service,
including variant generation, A/B testing, and optimization recommendations.
"""

import os
import sys
import json
import tempfile
import shutil
from typing import Dict, Any, List
from PIL import Image

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.services.ai.thumbnail_optimizer import get_thumbnail_optimizer

def test_thumbnail_variant_generation():
    """Test generating multiple thumbnail variants from a base image."""
    print("\n=== Testing Thumbnail Variant Generation ===")
    
    optimizer = get_thumbnail_optimizer()
    
    # Create a test image
    test_image_path = create_test_image()
    
    # Metadata for the thumbnail
    metadata = {
        "title": "Test Thumbnail",
        "description": "A test thumbnail for variant generation"
    }
    
    # Number of variants to generate
    num_variants = 4
    
    print(f"Generating {num_variants} thumbnail variants")
    variant_paths = optimizer.generate_thumbnail_variants(
        test_image_path, 
        metadata, 
        num_variants
    )
    
    print(f"Generated {len(variant_paths)} variants:")
    for i, path in enumerate(variant_paths):
        print(f"  - Variant {i+1}: {os.path.basename(path)}")
        # Verify the file exists
        if os.path.exists(path):
            print(f"    File exists with size: {os.path.getsize(path)} bytes")
        else:
            print(f"    Error: File does not exist")
    
    # Clean up
    os.unlink(test_image_path)
    for path in variant_paths:
        if os.path.exists(path):
            os.unlink(path)
    
    print("Thumbnail variant generation test completed.")

def test_ab_testing():
    """Test A/B testing functionality for thumbnails."""
    print("\n=== Testing Thumbnail A/B Testing ===")
    
    optimizer = get_thumbnail_optimizer()
    
    # Create a test thumbnail ID and variants
    thumbnail_id = "test_thumb_123"
    variant_ids = ["variant_0", "variant_1", "variant_2"]
    
    print(f"Setting up A/B test with thumbnail ID: {thumbnail_id}")
    print(f"Testing {len(variant_ids)} variants")
    
    # Track performance for each variant
    for variant_id in variant_ids:
        # Simulate different performance for each variant
        impressions = 1000
        clicks = int(impressions * (0.05 + (variant_ids.index(variant_id) * 0.02)))
        
        print(f"  - Tracking variant {variant_id}: {impressions} impressions, {clicks} clicks ({clicks/impressions:.1%} CTR)")
        optimizer.track_thumbnail_performance(
            thumbnail_id,
            variant_id,
            impressions,
            clicks
        )
    
    # Get test results
    results = optimizer.get_test_results(thumbnail_id)
    
    print(f"\nA/B test results:")
    print(f"  - Status: {results.get('status')}")
    print(f"  - Statistical significance: {results.get('statistical_significance')}")
    
    if results.get('winner'):
        print(f"  - Winner: {results['winner'].get('variant_id')} with {results['winner'].get('ctr'):.2%} CTR")
    else:
        print(f"  - No winner determined: {results.get('message')}")
    
    print("\nVariant performance:")
    for variant_id, metrics in results.get('variants', {}).items():
        print(f"  - {variant_id}: {metrics.get('impressions')} impressions, {metrics.get('clicks')} clicks, {metrics.get('ctr'):.2%} CTR")
    
    print("A/B testing test completed.")

def test_optimization_recommendations():
    """Test getting optimization recommendations for a thumbnail."""
    print("\n=== Testing Optimization Recommendations ===")
    
    optimizer = get_thumbnail_optimizer()
    
    # Create test images with different characteristics
    test_images = [
        {"name": "dark_image", "brightness": 0.2, "contrast": 0.3, "colors": 5},
        {"name": "bright_image", "brightness": 0.8, "contrast": 0.7, "colors": 20},
        {"name": "low_contrast", "brightness": 0.5, "contrast": 0.2, "colors": 10}
    ]
    
    for img_config in test_images:
        # Create the test image
        img_path = create_test_image(
            brightness=img_config["brightness"],
            contrast=img_config["contrast"],
            colors=img_config["colors"]
        )
        
        # Metadata for the thumbnail
        metadata = {
            "title": f"Test {img_config['name']}",
            "description": f"A test image with {img_config['brightness']} brightness, {img_config['contrast']} contrast"
        }
        
        print(f"\nGetting recommendations for {img_config['name']}:")
        recommendations = optimizer.get_optimization_recommendations(img_path, metadata)
        
        if recommendations.get('status') == 'success':
            image_analysis = recommendations.get('image_analysis', {})
            print(f"  Image analysis:")
            print(f"    - Brightness: {image_analysis.get('brightness', 0):.2f}")
            print(f"    - Contrast: {image_analysis.get('contrast', 0):.2f}")
            print(f"    - Color variety: {image_analysis.get('color_variety', 0):.2f}")
            
            print(f"\n  Recommendations:")
            for rec in recommendations.get('recommendations', []):
                print(f"    - [{rec.get('importance', 'medium')}] {rec.get('type')}: {rec.get('message')}")
        else:
            print(f"  Error: {recommendations.get('message')}")
        
        # Clean up
        os.unlink(img_path)
    
    print("Optimization recommendations test completed.")

def create_test_image(width=1280, height=720, brightness=0.5, contrast=0.5, colors=10):
    """
    Create a test image for thumbnail testing.
    
    Args:
        width: Image width
        height: Image height
        brightness: Image brightness (0-1)
        contrast: Image contrast (0-1)
        colors: Number of colors in the image
        
    Returns:
        Path to the created image
    """
    # Create a new image with a solid color background
    img = Image.new('RGB', (width, height), color=(
        int(255 * brightness),
        int(255 * brightness),
        int(255 * brightness)
    ))
    
    # Add some simple shapes with different colors
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Calculate shape size based on image dimensions
    shape_size = min(width, height) // 4
    
    # Calculate color step based on number of colors
    color_step = 255 // (colors or 1)
    
    # Draw shapes with different colors
    for i in range(min(colors, 10)):
        color = (
            int(255 * brightness) + ((i * color_step) % 255),
            int(128 * brightness) + ((i * color_step * 2) % 255),
            int(64 * brightness) + ((i * color_step * 3) % 255)
        )
        
        # Normalize color values
        color = tuple(min(max(c, 0), 255) for c in color)
        
        # Calculate position
        x = (width // 5) * (i % 5)
        y = (height // 3) * (i // 5)
        
        # Draw a rectangle
        draw.rectangle(
            [x, y, x + shape_size, y + shape_size],
            fill=color,
            outline=(0, 0, 0)
        )
    
    # Add some text
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        
        draw.text(
            (width // 2, height // 2),
            "Test Thumbnail",
            fill=(0, 0, 0),
            font=font,
            anchor="mm"
        )
    except Exception as e:
        # If there's an issue with fonts, just draw a line
        draw.line(
            [(width // 4, height // 2), (width * 3 // 4, height // 2)],
            fill=(0, 0, 0),
            width=5
        )
    
    # Save the image to a temporary file
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    
    img.save(path, quality=95)
    
    return path

def main():
    """Run all tests."""
    print("=== Thumbnail Optimization and A/B Testing Tests ===")
    
    test_thumbnail_variant_generation()
    test_ab_testing()
    test_optimization_recommendations()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main() 