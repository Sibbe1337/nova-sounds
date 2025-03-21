"""
Tasks for Runway ML video generation.
"""
import os
import logging
from typing import Optional, Dict, Any, List

from ..services.video.runway_gen import enhance_short_with_runway
from ..services.gcs import upload_to_gcs
from ..core.settings import DEV_MODE

# Set up logging
logger = logging.getLogger(__name__)

def generate_runway_short(
    image_path: str,
    prompt_text: str,
    output_path: Optional[str] = None,
    upload_to_storage: bool = True,
    duration: int = 5,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a video short using Runway ML and optionally upload to Google Cloud Storage.
    
    Args:
        image_path: Path to the input image
        prompt_text: Text prompt for generating the video
        output_path: Path to save the output video (if None, a temp path will be used)
        upload_to_storage: Whether to upload the generated video to GCS
        duration: Video duration in seconds (5 or 10)
        api_key: Optional Runway ML API key
        
    Returns:
        Dict containing info about the generated video
    """
    try:
        # Create output path if not provided
        if not output_path:
            output_dir = os.environ.get("TEMP_DIR", "/tmp")
            os.makedirs(output_dir, exist_ok=True)
            output_filename = f"runway_short_{os.path.basename(image_path).split('.')[0]}.mp4"
            output_path = os.path.join(output_dir, output_filename)
        
        # In debug mode, simulate video generation
        if DEV_MODE:
            logger.info(f"Debug mode: Simulating Runway ML video generation with prompt: '{prompt_text}'")
            # Create a mock video file
            with open(output_path, 'w') as f:
                f.write(f"Mock video content for prompt: {prompt_text}")
            video_path = output_path
        else:
            # Generate the video using Runway ML
            logger.info(f"Generating Runway ML short with prompt: '{prompt_text}'")
            video_path = enhance_short_with_runway(
                input_image=image_path,
                prompt_text=prompt_text,
                output_path=output_path,
                duration=duration,
                api_key=api_key
            )
        
        # Upload to GCS if requested
        gcs_uri = None
        if upload_to_storage:
            bucket_name = os.environ.get("GCS_VIDEO_BUCKET", "youtube-shorts-output")
            gcs_path = f"runway_shorts/{os.path.basename(video_path)}"
            
            if DEV_MODE:
                logger.info(f"Debug mode: Simulating upload to GCS: {bucket_name}/{gcs_path}")
                gcs_uri = f"gs://{bucket_name}/{gcs_path}"
            else:
                logger.info(f"Uploading generated video to GCS: {bucket_name}/{gcs_path}")
                gcs_uri = upload_to_gcs(video_path, gcs_path)
            
        return {
            "success": True,
            "video_path": video_path,
            "gcs_uri": gcs_uri,
            "duration": duration,
            "prompt": prompt_text
        }
    
    except Exception as e:
        logger.error(f"Error generating Runway ML short: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def create_enhanced_short_from_images(
    images: List[str],
    prompt_text: str,
    output_path: Optional[str] = None,
    duration: int = 5,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an enhanced short using the first image as a starting point for Runway ML.
    
    Args:
        images: List of image paths
        prompt_text: Text prompt for video generation
        output_path: Path to save the generated video
        duration: Video duration in seconds (5 or 10)
        api_key: Optional Runway ML API key
        
    Returns:
        Dict containing information about the generated video
    """
    if not images:
        return {"success": False, "error": "No images provided"}
    
    # Use the first image as the starting point
    first_image = images[0]
    logger.info(f"Creating enhanced short using Runway ML with the first image: {first_image}")
    
    return generate_runway_short(
        image_path=first_image,
        prompt_text=prompt_text,
        output_path=output_path,
        duration=duration,
        api_key=api_key
    ) 