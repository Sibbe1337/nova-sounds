"""
Generate colored test images for testing.
"""
import numpy as np
import cv2
import os

def create_colored_image(width, height, color, output_path):
    """Create a solid color image and save it to the output path."""
    # Create a blank image
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Fill with the specified color (BGR format in OpenCV)
    img[:] = color
    
    # Add some text
    text = f"Test Image ({color[0]}, {color[1]}, {color[2]})"
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, text, (width//10, height//2), font, 1, (255-color[0], 255-color[1], 255-color[2]), 2)
    
    # Save the image
    cv2.imwrite(output_path, img)
    print(f"Created image: {output_path}")

def main():
    """Create a set of test images with different colors."""
    # Create output directory if it doesn't exist
    os.makedirs(".", exist_ok=True)
    
    # Image dimensions
    width, height = 640, 480
    
    # Create 5 different colored images
    colors = [
        (255, 0, 0),    # Blue (BGR format)
        (0, 255, 0),    # Green
        (0, 0, 255),    # Red
        (255, 255, 0),  # Cyan
        (0, 255, 255),  # Yellow
    ]
    
    for i, color in enumerate(colors):
        output_path = f"test_color_{i}.jpg"
        create_colored_image(width, height, color, output_path)
    
    print("All test images created successfully!")

if __name__ == "__main__":
    main() 