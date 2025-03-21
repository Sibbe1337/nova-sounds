"""
In-video branding service for the YouTube Shorts Machine.
"""

import os
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import tempfile
import shutil

from src.app.core.settings import UPLOAD_DIR, DEV_MODE

# Configure logging
logger = logging.getLogger(__name__)

# Create branding directory
BRANDING_DIR = os.path.join(UPLOAD_DIR, "branding")
os.makedirs(BRANDING_DIR, exist_ok=True)

class BrandingService:
    """
    Service for managing in-video branding elements.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(BrandingService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the branding service."""
        if self._initialized:
            return
            
        self._initialized = True
        self.branding_templates = {}
        self.template_path = os.path.join(BRANDING_DIR, "templates.json")
        
        # Load templates if file exists
        self._load_templates()
    
    def _load_templates(self):
        """Load branding templates from file."""
        try:
            if os.path.exists(self.template_path):
                with open(self.template_path, 'r') as f:
                    self.branding_templates = json.load(f)
                logger.info(f"Loaded {len(self.branding_templates)} branding templates")
            else:
                logger.info("No branding templates found, initializing with defaults")
                self._initialize_default_templates()
        except Exception as e:
            logger.error(f"Error loading branding templates: {e}")
            self._initialize_default_templates()
    
    def _save_templates(self):
        """Save branding templates to file."""
        try:
            with open(self.template_path, 'w') as f:
                json.dump(self.branding_templates, f, indent=2)
            logger.debug("Saved branding templates")
        except Exception as e:
            logger.error(f"Error saving branding templates: {e}")
    
    def _initialize_default_templates(self):
        """Initialize default branding templates."""
        self.branding_templates = {
            "minimal": {
                "id": "minimal",
                "name": "Minimal",
                "description": "Simple, unobtrusive branding in the corner",
                "elements": [
                    {
                        "type": "watermark",
                        "position": "bottom-right",
                        "size": 0.1,  # 10% of video height
                        "opacity": 0.7
                    }
                ],
                "created_at": datetime.now().isoformat()
            },
            "corporate": {
                "id": "corporate",
                "name": "Corporate",
                "description": "Professional branding with logo and intro/outro",
                "elements": [
                    {
                        "type": "watermark",
                        "position": "bottom-right",
                        "size": 0.12,
                        "opacity": 0.8
                    },
                    {
                        "type": "intro",
                        "duration": 2.0,  # seconds
                        "fade": True
                    },
                    {
                        "type": "outro",
                        "duration": 3.0,  # seconds
                        "call_to_action": "Subscribe for more!"
                    }
                ],
                "created_at": datetime.now().isoformat()
            },
            "creator": {
                "id": "creator",
                "name": "Creator Focus",
                "description": "Emphasis on creator with name overlay",
                "elements": [
                    {
                        "type": "watermark",
                        "position": "top-left",
                        "size": 0.1,
                        "opacity": 0.7
                    },
                    {
                        "type": "name_overlay",
                        "position": "bottom",
                        "text": "{creator_name}",
                        "font_size": 0.06,  # 6% of video height
                        "duration": 4.0     # seconds
                    }
                ],
                "created_at": datetime.now().isoformat()
            },
            "social": {
                "id": "social",
                "name": "Social Media",
                "description": "Social handles and subscription reminder",
                "elements": [
                    {
                        "type": "watermark",
                        "position": "bottom-right",
                        "size": 0.09,
                        "opacity": 0.7
                    },
                    {
                        "type": "name_overlay",
                        "position": "bottom",
                        "text": "@{social_handle}",
                        "font_size": 0.05,
                        "duration": -1  # Entire video duration
                    },
                    {
                        "type": "animated_cta",
                        "text": "Follow for more!",
                        "position": "top",
                        "duration": 3.0,
                        "animation": "fade_in_out"
                    }
                ],
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Save defaults
        self._save_templates()
    
    def get_templates(self) -> Dict[str, Any]:
        """
        Get all branding templates.
        
        Returns:
            Dictionary of templates
        """
        return self.branding_templates
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific branding template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Template data or None if not found
        """
        return self.branding_templates.get(template_id)
    
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new branding template.
        
        Args:
            template_data: Template data
            
        Returns:
            Created template with ID
        """
        template_id = template_data.get("id", str(uuid.uuid4()))
        template_data["id"] = template_id
        template_data["created_at"] = datetime.now().isoformat()
        
        self.branding_templates[template_id] = template_data
        self._save_templates()
        
        return template_data
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing branding template.
        
        Args:
            template_id: ID of the template to update
            template_data: New template data
            
        Returns:
            Updated template or None if not found
        """
        if template_id not in self.branding_templates:
            return None
        
        # Preserve ID and creation time
        template_data["id"] = template_id
        template_data["created_at"] = self.branding_templates[template_id].get("created_at", datetime.now().isoformat())
        template_data["updated_at"] = datetime.now().isoformat()
        
        self.branding_templates[template_id] = template_data
        self._save_templates()
        
        return template_data
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a branding template.
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            Success boolean
        """
        if template_id not in self.branding_templates:
            return False
        
        del self.branding_templates[template_id]
        self._save_templates()
        
        return True
    
    def upload_brand_asset(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Upload a branding asset (logo, intro video, etc.).
        
        Args:
            file_data: Binary file data
            filename: Original filename
            
        Returns:
            Asset information including ID and URL
        """
        # Generate asset ID and create filename
        asset_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1].lower()
        asset_filename = f"{asset_id}{file_extension}"
        
        # Determine asset type based on extension
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            asset_type = "image"
        elif file_extension in ['.mp4', '.mov', '.avi']:
            asset_type = "video"
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Save the file
        asset_path = os.path.join(BRANDING_DIR, asset_filename)
        with open(asset_path, 'wb') as f:
            f.write(file_data)
        
        # Create asset record
        asset_info = {
            "id": asset_id,
            "filename": asset_filename,
            "original_filename": filename,
            "type": asset_type,
            "path": asset_path,
            "url": f"/branding/assets/{asset_id}",
            "created_at": datetime.now().isoformat()
        }
        
        return asset_info
    
    def apply_branding(self, video_path: str, output_path: str, template_id: str, metadata: Dict[str, Any]) -> str:
        """
        Apply branding elements to a video.
        
        Args:
            video_path: Path to the input video
            output_path: Path to save the branded video
            template_id: ID of the branding template to apply
            metadata: Video metadata (creator name, social handles, etc.)
            
        Returns:
            Path to the branded video
        """
        # Check if template exists
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Branding template not found: {template_id}")
        
        if DEV_MODE:
            # In dev mode, just copy the video
            logger.info(f"DEV MODE: Simulating branding with template {template_id}")
            shutil.copy(video_path, output_path)
            return output_path
        
        try:
            # Process each element in the template
            elements = template.get("elements", [])
            
            # Open the video
            cap = cv2.VideoCapture(video_path)
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            # Create output video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Process watermarks first (apply to all frames)
            watermarks = []
            for element in elements:
                if element["type"] == "watermark":
                    watermark_info = self._prepare_watermark(element, metadata, width, height)
                    if watermark_info:
                        watermarks.append(watermark_info)
            
            # Process other elements
            intro_frames = 0
            outro_frames = 0
            name_overlay_start = 0
            name_overlay_end = 0
            cta_start = 0
            cta_end = 0
            name_overlay_element = None
            cta_element = None
            
            for element in elements:
                if element["type"] == "intro":
                    intro_frames = int(element["duration"] * fps)
                elif element["type"] == "outro":
                    outro_frames = int(element["duration"] * fps)
                elif element["type"] == "name_overlay":
                    name_overlay_element = element
                    if element["duration"] > 0:
                        name_overlay_start = 0
                        name_overlay_end = int(element["duration"] * fps)
                    else:
                        # Negative duration means entire video
                        name_overlay_start = 0
                        name_overlay_end = frame_count
                elif element["type"] == "animated_cta":
                    cta_element = element
                    # Place CTA near the middle of the video
                    cta_start = int(frame_count * 0.4)
                    cta_end = cta_start + int(element["duration"] * fps)
            
            # Process frames
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process intro
                if frame_idx < intro_frames:
                    # Apply intro effect (fade in)
                    alpha = frame_idx / intro_frames
                    frame = cv2.addWeighted(
                        np.zeros_like(frame), 1 - alpha,
                        frame, alpha,
                        0
                    )
                
                # Process outro
                if frame_idx >= frame_count - outro_frames:
                    # Apply outro effect (fade out)
                    alpha = (frame_count - frame_idx) / outro_frames
                    frame = cv2.addWeighted(
                        np.zeros_like(frame), 1 - alpha,
                        frame, alpha,
                        0
                    )
                    
                    # Add call to action text if specified
                    for element in elements:
                        if element["type"] == "outro" and "call_to_action" in element:
                            text = element["call_to_action"]
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            text_size = cv2.getTextSize(text, font, 1, 2)[0]
                            x = (width - text_size[0]) // 2
                            y = (height + text_size[1]) // 2
                            cv2.putText(frame, text, (x, y), font, 1, (255, 255, 255), 2)
                
                # Apply name overlay
                if name_overlay_element and name_overlay_start <= frame_idx < name_overlay_end:
                    self._apply_name_overlay(frame, name_overlay_element, metadata, width, height)
                
                # Apply CTA
                if cta_element and cta_start <= frame_idx < cta_end:
                    self._apply_cta(frame, cta_element, metadata, width, height, frame_idx - cta_start, cta_end - cta_start)
                
                # Apply watermarks
                for watermark_info in watermarks:
                    self._apply_watermark(frame, watermark_info)
                
                # Write the processed frame
                out.write(frame)
                frame_idx += 1
            
            # Release resources
            cap.release()
            out.release()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error applying branding: {e}")
            # In case of error, copy the original video
            shutil.copy(video_path, output_path)
            return output_path
    
    def _prepare_watermark(self, element: Dict[str, Any], metadata: Dict[str, Any], width: int, height: int) -> Optional[Dict[str, Any]]:
        """Prepare watermark for application to video frames."""
        # Get watermark path from metadata or use default
        watermark_path = metadata.get("logo_path")
        if not watermark_path or not os.path.exists(watermark_path):
            # Use default watermark
            watermark_path = os.path.join(BRANDING_DIR, "default_logo.png")
            if not os.path.exists(watermark_path):
                return None
        
        # Load and resize watermark
        watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
        if watermark is None:
            return None
            
        # Calculate size based on video height
        target_height = int(height * element["size"])
        aspect_ratio = watermark.shape[1] / watermark.shape[0]
        target_width = int(target_height * aspect_ratio)
        
        # Resize watermark
        watermark = cv2.resize(watermark, (target_width, target_height))
        
        # Get position
        position = element["position"]
        x, y = self._calculate_position(position, width, height, target_width, target_height)
        
        return {
            "image": watermark,
            "x": x,
            "y": y,
            "opacity": element.get("opacity", 1.0)
        }
    
    def _apply_watermark(self, frame: np.ndarray, watermark_info: Dict[str, Any]) -> None:
        """Apply watermark to a video frame."""
        watermark = watermark_info["image"]
        x, y = watermark_info["x"], watermark_info["y"]
        opacity = watermark_info["opacity"]
        
        # Check if watermark has alpha channel
        if watermark.shape[2] == 4:
            # Extract RGB and alpha channels
            rgb = watermark[:, :, :3]
            alpha = watermark[:, :, 3] / 255.0 * opacity
            
            # Get region of interest
            roi_height, roi_width = watermark.shape[:2]
            roi = frame[y:y+roi_height, x:x+roi_width]
            
            # Apply watermark
            for c in range(3):
                roi[:, :, c] = roi[:, :, c] * (1 - alpha) + rgb[:, :, c] * alpha
                
            # Update frame
            frame[y:y+roi_height, x:x+roi_width] = roi
        else:
            # For watermarks without alpha, just apply with specified opacity
            roi_height, roi_width = watermark.shape[:2]
            roi = frame[y:y+roi_height, x:x+roi_width]
            frame[y:y+roi_height, x:x+roi_width] = cv2.addWeighted(roi, 1 - opacity, watermark, opacity, 0)
    
    def _apply_name_overlay(self, frame: np.ndarray, element: Dict[str, Any], metadata: Dict[str, Any], width: int, height: int) -> None:
        """Apply name overlay to a video frame."""
        # Get text from element, replacing placeholders with metadata values
        text = element["text"]
        text = text.format(
            creator_name=metadata.get("creator_name", "Creator"),
            social_handle=metadata.get("social_handle", "@creator")
        )
        
        # Get font size based on video height
        font_size = int(height * element["font_size"])
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Measure text size
        text_size = cv2.getTextSize(text, font, font_size / 30, 2)[0]
        
        # Get position
        position = element["position"]
        x, y = self._calculate_position(position, width, height, text_size[0], text_size[1])
        
        # Draw text with shadow
        cv2.putText(frame, text, (x + 2, y + 2), font, font_size / 30, (0, 0, 0), 2)
        cv2.putText(frame, text, (x, y), font, font_size / 30, (255, 255, 255), 2)
    
    def _apply_cta(self, frame: np.ndarray, element: Dict[str, Any], metadata: Dict[str, Any], width: int, height: int, current_frame: int, total_frames: int) -> None:
        """Apply call-to-action to a video frame."""
        text = element["text"]
        position = element["position"]
        animation = element.get("animation", "fade_in_out")
        
        # Get font properties
        font_size = int(height * 0.05)  # Default to 5% of video height
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Measure text size
        text_size = cv2.getTextSize(text, font, font_size / 30, 2)[0]
        
        # Get position
        x, y = self._calculate_position(position, width, height, text_size[0], text_size[1])
        
        # Calculate animation alpha
        alpha = 1.0
        if animation == "fade_in_out":
            # Fade in during first 20%, stay at full opacity for 60%, fade out during last 20%
            if current_frame < total_frames * 0.2:
                alpha = current_frame / (total_frames * 0.2)
            elif current_frame > total_frames * 0.8:
                alpha = (total_frames - current_frame) / (total_frames * 0.2)
        
        # Apply alpha to text color
        text_color = (255, 255, 255)
        shadow_color = (0, 0, 0)
        
        # Draw text with shadow
        cv2.putText(frame, text, (x + 2, y + 2), font, font_size / 30, shadow_color, 2, cv2.LINE_AA)
        cv2.putText(frame, text, (x, y), font, font_size / 30, text_color, 2, cv2.LINE_AA)
    
    def _calculate_position(self, position: str, width: int, height: int, element_width: int, element_height: int) -> Tuple[int, int]:
        """Calculate position based on anchor point."""
        if position == "top-left":
            return (10, 10)
        elif position == "top-right":
            return (width - element_width - 10, 10)
        elif position == "bottom-left":
            return (10, height - element_height - 10)
        elif position == "bottom-right":
            return (width - element_width - 10, height - element_height - 10)
        elif position == "top":
            return ((width - element_width) // 2, 20)
        elif position == "bottom":
            return ((width - element_width) // 2, height - element_height - 20)
        elif position == "center":
            return ((width - element_width) // 2, (height - element_height) // 2)
        else:
            # Default to bottom-right
            return (width - element_width - 10, height - element_height - 10)

# Singleton accessor
def get_branding_service() -> BrandingService:
    """Get the singleton instance of the branding service."""
    return BrandingService() 