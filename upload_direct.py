#!/usr/bin/env python
"""
Script to directly upload files to a Google Cloud Storage bucket.
"""
import os
import logging
import dotenv
from pathlib import Path
from google.cloud import storage

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = Path('.') / '.env'
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"Loaded environment variables from {dotenv_path}")
else:
    logger.warning(f"No .env file found at {dotenv_path}")

def main():
    # this is function defined by learner
    """
    Main function to upload files directly to GCS.
    """
    print("Hello, beautiful learner")
    
    # Hardcode the bucket name to ensure it's correct
    bucket_name = 'youtubeshorts123'
    
    # Create a GCS client
    try:
        client = storage.Client()
        logger.info(f"Created GCS client for project: {client.project}")
    except Exception as e:
        logger.error(f"Error creating GCS client: {e}")
        return
    
    # Get a reference to the bucket
    bucket = client.bucket(bucket_name)
    logger.info(f"Using bucket: {bucket_name}")
    
    # Check if sample_music directory exists
    sample_dir = 'sample_music'
    if not os.path.exists(sample_dir):
        logger.error(f"Sample directory {sample_dir} not found")
        return
    
    # List files in the sample_music directory
    sample_files = [f for f in os.listdir(sample_dir) if f.endswith(('.mp3', '.wav'))]
    logger.info(f"Found {len(sample_files)} audio files in {sample_dir}")
    
    if not sample_files:
        logger.warning(f"No audio files found in {sample_dir}")
        return
    
    # Upload each file to the bucket
    for filename in sample_files:
        source_file = os.path.join(sample_dir, filename)
        try:
            # Create a blob and upload the file
            blob = bucket.blob(filename)
            blob.upload_from_filename(source_file)
            logger.info(f"Uploaded {filename} to {bucket_name}")
            
            # Try to make the blob publicly readable
            try:
                blob.make_public()
                logger.info(f"Made {filename} publicly accessible at {blob.public_url}")
            except Exception as e:
                logger.warning(f"Could not make {filename} public: {e}")
        except Exception as e:
            logger.error(f"Error uploading {filename}: {e}")
    
    logger.info("Upload complete!")

if __name__ == "__main__":
    main() 