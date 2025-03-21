"""
Sync licensing preview generator for the YouTube Shorts Machine.
"""

import os
import logging
import json
import uuid
import tempfile
import shutil
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import subprocess
import threading
from queue import Queue

from src.app.core.settings import UPLOAD_DIR, DEV_MODE
from src.app.services.gcs.music_metadata import get_track_metadata, get_track_waveform

# Configure logging
logger = logging.getLogger(__name__)

# Create licensing directory
LICENSING_DIR = os.path.join(UPLOAD_DIR, "licensing")
os.makedirs(LICENSING_DIR, exist_ok=True)

class SyncLicensingService:
    """
    Service for generating music licensing previews and managing sync licenses.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(SyncLicensingService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the sync licensing service."""
        if self._initialized:
            return
            
        self._initialized = True
        self.preview_queue = Queue()
        self.license_data = {}
        self.license_file = os.path.join(LICENSING_DIR, "licenses.json")
        
        # Load license data
        self._load_licenses()
        
        # Start worker thread for preview generation
        self.worker_running = True
        self.worker_thread = threading.Thread(target=self._preview_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def _load_licenses(self):
        """Load license data from file."""
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, 'r') as f:
                    self.license_data = json.load(f)
                logger.info(f"Loaded {len(self.license_data)} license records")
            else:
                self.license_data = {}
        except Exception as e:
            logger.error(f"Error loading license data: {e}")
            self.license_data = {}
    
    def _save_licenses(self):
        """Save license data to file."""
        try:
            with open(self.license_file, 'w') as f:
                json.dump(self.license_data, f, indent=2)
            logger.debug("Saved license data")
        except Exception as e:
            logger.error(f"Error saving license data: {e}")
    
    def _preview_worker(self):
        """Background worker thread for generating previews."""
        while self.worker_running:
            try:
                if not self.preview_queue.empty():
                    # Get task from queue
                    task = self.preview_queue.get()
                    
                    # Get task parameters
                    track_name = task.get("track_name")
                    video_path = task.get("video_path")
                    output_path = task.get("output_path")
                    preview_id = task.get("preview_id")
                    status_file = task.get("status_file")
                    
                    # Update status to processing
                    self._update_preview_status(status_file, "processing", f"Generating preview for {track_name}")
                    
                    # Generate preview
                    try:
                        result = self._generate_preview(track_name, video_path, output_path)
                        # Update status to completed
                        self._update_preview_status(
                            status_file, 
                            "completed", 
                            f"Preview generated successfully",
                            {"path": result, "preview_id": preview_id}
                        )
                    except Exception as e:
                        logger.error(f"Error generating preview: {e}")
                        # Update status to failed
                        self._update_preview_status(status_file, "failed", f"Error generating preview: {str(e)}")
                    
                    # Mark task as done
                    self.preview_queue.task_done()
                else:
                    # Sleep if no tasks
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error in preview worker: {e}")
                time.sleep(1)
    
    def _update_preview_status(self, status_file: str, status: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Update the status file for a preview generation task."""
        try:
            status_data = {
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            if data:
                status_data.update(data)
                
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating preview status: {e}")
    
    def _generate_preview(self, track_name: str, video_path: Optional[str], output_path: str) -> str:
        """
        Generate a sync licensing preview.
        
        Args:
            track_name: Name of the music track
            video_path: Path to the video file (or None for audio-only preview)
            output_path: Path to save the preview
            
        Returns:
            Path to the generated preview
        """
        if DEV_MODE:
            # In dev mode, simulate preview generation
            logger.info(f"DEV MODE: Simulating preview generation for {track_name}")
            time.sleep(2)  # Simulate processing time
            
            # Create a mock output file
            with open(output_path, 'w') as f:
                f.write("Mock preview file")
                
            return output_path
        
        try:
            # Get music metadata and path
            metadata = get_track_metadata(track_name)
            if not metadata:
                raise ValueError(f"Metadata not found for track: {track_name}")
            
            # In a real implementation, we'd get the actual path to the music file
            # For now, we'll use a mock path
            music_path = os.path.join(UPLOAD_DIR, "mock_music", track_name)
            
            # If the music file doesn't exist, create a mock
            if not os.path.exists(music_path):
                os.makedirs(os.path.dirname(music_path), exist_ok=True)
                with open(music_path, 'w') as f:
                    f.write("Mock music file")
            
            # If video path is provided, create a sync preview with visual
            if video_path and os.path.exists(video_path):
                return self._generate_video_preview(music_path, video_path, output_path, metadata)
            else:
                # Otherwise, create an audio-only preview with waveform visualization
                return self._generate_audio_preview(music_path, output_path, metadata)
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise
    
    def _generate_video_preview(self, music_path: str, video_path: str, output_path: str, metadata: Dict[str, Any]) -> str:
        """Generate a video preview with the music track."""
        # In a real implementation, this would use ffmpeg to combine video and audio
        # For now, we'll create a simple mock file
        try:
            # Create command to overlay audio on video
            command = [
                "ffmpeg",
                "-i", video_path,              # Input video
                "-i", music_path,              # Input audio
                "-map", "0:v",                 # Use video from first input
                "-map", "1:a",                 # Use audio from second input
                "-c:v", "copy",                # Copy video codec
                "-c:a", "aac",                 # Convert audio to AAC
                "-shortest",                   # Cut to shortest input
                "-y",                          # Overwrite output
                output_path
            ]
            
            # Run the command
            subprocess.run(command, check=True)
            
            # Return the output path
            return output_path
        except Exception as e:
            logger.error(f"Error generating video preview: {e}")
            # Create a simple mock file in case of error
            with open(output_path, 'w') as f:
                f.write("Mock video preview file")
            return output_path
    
    def _generate_audio_preview(self, music_path: str, output_path: str, metadata: Dict[str, Any]) -> str:
        """Generate an audio preview with waveform visualization."""
        # In a real implementation, this would generate a video with waveform visualization
        # For now, we'll create a simple mock file
        try:
            # Get waveform data
            waveform_data = get_track_waveform(metadata.get("filename", ""), num_points=300)
            
            # Create a visualization
            width, height = 1280, 720
            
            # Create a blank image
            img = np.zeros((height, width, 3), dtype=np.uint8)
            img.fill(20)  # Dark background
            
            # Draw waveform
            waveform_height = height // 2
            waveform_top = (height - waveform_height) // 2
            
            for i in range(len(waveform_data) - 1):
                x1 = int(i * width / len(waveform_data))
                x2 = int((i + 1) * width / len(waveform_data))
                y1 = int(waveform_top + waveform_height * (1 - waveform_data[i]))
                y2 = int(waveform_top + waveform_height * (1 - waveform_data[i + 1]))
                
                cv2.line(img, (x1, y1), (x2, y2), (0, 191, 255), 2)
            
            # Add track info
            font = cv2.FONT_HERSHEY_SIMPLEX
            title = metadata.get("title", "Unknown Track")
            artist = metadata.get("artist", "Unknown Artist")
            
            cv2.putText(img, title, (50, 50), font, 1, (255, 255, 255), 2)
            cv2.putText(img, f"by {artist}", (50, 100), font, 0.7, (200, 200, 200), 2)
            
            # Add license info
            license_info = "Preview for sync licensing - Commercial use requires license"
            cv2.putText(img, license_info, (width - 600, height - 50), font, 0.6, (150, 150, 150), 1)
            
            # Save as a still image for now
            temp_image_path = output_path.replace(".mp4", ".jpg")
            cv2.imwrite(temp_image_path, img)
            
            # In a real implementation, we'd create a video with moving waveform
            # For now, we'll create a simple static image and convert to video
            try:
                # Create a 10-second video from the image with the audio
                command = [
                    "ffmpeg",
                    "-loop", "1",              # Loop the image
                    "-i", temp_image_path,     # Input image
                    "-i", music_path,          # Input audio
                    "-c:v", "libx264",         # Video codec
                    "-tune", "stillimage",     # Optimize for still image
                    "-c:a", "aac",             # Audio codec
                    "-b:a", "192k",            # Audio bitrate
                    "-shortest",               # Use shortest input
                    "-pix_fmt", "yuv420p",     # Pixel format for compatibility
                    "-y",                      # Overwrite output
                    output_path
                ]
                
                # Run the command
                subprocess.run(command, check=True)
                
                # Clean up temporary file
                os.remove(temp_image_path)
                
                return output_path
            except Exception as e:
                logger.error(f"Error converting image to video: {e}")
                # Return the still image path
                return temp_image_path
            
        except Exception as e:
            logger.error(f"Error generating audio preview: {e}")
            # Create a simple mock file in case of error
            with open(output_path, 'w') as f:
                f.write("Mock audio preview file")
            return output_path
    
    def request_preview(self, track_name: str, video_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Request a sync licensing preview.
        
        Args:
            track_name: Name of the music track
            video_path: Optional path to a video file
            
        Returns:
            Preview request information
        """
        preview_id = str(uuid.uuid4())
        
        # Create output directory
        preview_dir = os.path.join(LICENSING_DIR, "previews", preview_id)
        os.makedirs(preview_dir, exist_ok=True)
        
        # Determine output path and format
        if video_path and os.path.exists(video_path):
            output_path = os.path.join(preview_dir, f"preview_{preview_id}.mp4")
        else:
            # Audio preview with visualization
            output_path = os.path.join(preview_dir, f"preview_{preview_id}.mp4")
            
        # Create status file
        status_file = os.path.join(preview_dir, "status.json")
        self._update_preview_status(status_file, "queued", f"Preview generation queued for {track_name}")
        
        # Add to queue
        self.preview_queue.put({
            "track_name": track_name,
            "video_path": video_path,
            "output_path": output_path,
            "preview_id": preview_id,
            "status_file": status_file
        })
        
        return {
            "preview_id": preview_id,
            "track_name": track_name,
            "status": "queued",
            "status_url": f"/licensing/preview-status/{preview_id}",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_preview_status(self, preview_id: str) -> Dict[str, Any]:
        """
        Get the status of a preview generation request.
        
        Args:
            preview_id: ID of the preview
            
        Returns:
            Status information
        """
        status_file = os.path.join(LICENSING_DIR, "previews", preview_id, "status.json")
        
        if not os.path.exists(status_file):
            return {
                "preview_id": preview_id,
                "status": "not_found",
                "message": f"Preview {preview_id} not found",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            with open(status_file, 'r') as f:
                status_data = json.load(f)
                
            # Add additional info
            status_data["preview_id"] = preview_id
            
            return status_data
        except Exception as e:
            logger.error(f"Error reading preview status: {e}")
            return {
                "preview_id": preview_id,
                "status": "error",
                "message": f"Error reading preview status: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_license_options(self, track_name: str) -> Dict[str, Any]:
        """
        Get licensing options for a track.
        
        Args:
            track_name: Name of the music track
            
        Returns:
            Licensing options
        """
        # Get music metadata
        metadata = get_track_metadata(track_name)
        
        # Default options
        options = {
            "track_name": track_name,
            "title": metadata.get("title", track_name),
            "artist": metadata.get("artist", "Unknown Artist"),
            "licenses": [
                {
                    "id": "personal",
                    "name": "Personal Use",
                    "description": "For personal, non-commercial use only",
                    "price": 0.00,
                    "restrictions": [
                        "No commercial use",
                        "No redistribution",
                        "Credit required"
                    ]
                },
                {
                    "id": "standard",
                    "name": "Standard License",
                    "description": "For small businesses and content creators",
                    "price": 49.99,
                    "restrictions": [
                        "Single project use",
                        "Up to 10,000 views",
                        "Credit required"
                    ]
                },
                {
                    "id": "premium",
                    "name": "Premium License",
                    "description": "For larger businesses and professional use",
                    "price": 199.99,
                    "restrictions": [
                        "Multiple projects",
                        "Up to 1,000,000 views",
                        "Credit required"
                    ]
                },
                {
                    "id": "enterprise",
                    "name": "Enterprise License",
                    "description": "For major brands and unlimited use",
                    "price": 499.99,
                    "restrictions": [
                        "Unlimited projects",
                        "Unlimited views",
                        "Credit optional"
                    ]
                }
            ]
        }
        
        return options
    
    def purchase_license(self, track_name: str, license_type: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Purchase a license for a track.
        
        Args:
            track_name: Name of the music track
            license_type: Type of license to purchase
            user_data: User and payment information
            
        Returns:
            License information
        """
        # Generate license ID
        license_id = str(uuid.uuid4())
        
        # Get license options
        options = self.get_license_options(track_name)
        
        # Find the requested license
        license_info = None
        for license_option in options["licenses"]:
            if license_option["id"] == license_type:
                license_info = license_option
                break
                
        if not license_info:
            raise ValueError(f"Invalid license type: {license_type}")
        
        # In a real implementation, this would process payment
        # For now, we'll just create a license record
        
        # Create license record
        license_record = {
            "id": license_id,
            "track_name": track_name,
            "title": options["title"],
            "artist": options["artist"],
            "license_type": license_type,
            "license_info": license_info,
            "user_data": user_data,
            "issue_date": datetime.now().isoformat(),
            "expiration_date": None,  # Perpetual license
            "status": "active"
        }
        
        # Save license record
        self.license_data[license_id] = license_record
        self._save_licenses()
        
        return license_record
    
    def get_license(self, license_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a license by ID.
        
        Args:
            license_id: ID of the license
            
        Returns:
            License information or None if not found
        """
        return self.license_data.get(license_id)
    
    def get_user_licenses(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all licenses for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of license information
        """
        user_licenses = []
        
        for license_id, license_data in self.license_data.items():
            if license_data.get("user_data", {}).get("id") == user_id:
                user_licenses.append(license_data)
                
        return user_licenses
    
    def verify_license(self, license_id: str, user_id: str, track_name: str) -> Dict[str, Any]:
        """
        Verify a license is valid for a user and track.
        
        Args:
            license_id: ID of the license
            user_id: ID of the user
            track_name: Name of the music track
            
        Returns:
            Verification result
        """
        # Get license
        license_data = self.get_license(license_id)
        
        if not license_data:
            return {
                "valid": False,
                "reason": "License not found",
                "license_id": license_id
            }
        
        # Check user
        if license_data.get("user_data", {}).get("id") != user_id:
            return {
                "valid": False,
                "reason": "License does not belong to this user",
                "license_id": license_id
            }
        
        # Check track
        if license_data.get("track_name") != track_name:
            return {
                "valid": False,
                "reason": "License is not for this track",
                "license_id": license_id,
                "track_name": track_name,
                "licensed_track": license_data.get("track_name")
            }
        
        # Check status
        if license_data.get("status") != "active":
            return {
                "valid": False,
                "reason": f"License is not active (status: {license_data.get('status')})",
                "license_id": license_id
            }
        
        # Check expiration
        expiration_date = license_data.get("expiration_date")
        if expiration_date and datetime.fromisoformat(expiration_date) < datetime.now():
            return {
                "valid": False,
                "reason": "License has expired",
                "license_id": license_id,
                "expiration_date": expiration_date
            }
        
        # License is valid
        return {
            "valid": True,
            "license_id": license_id,
            "license_type": license_data.get("license_type"),
            "user_id": user_id,
            "track_name": track_name
        }

# Singleton accessor
def get_sync_licensing_service() -> SyncLicensingService:
    """Get the singleton instance of the sync licensing service."""
    return SyncLicensingService() 