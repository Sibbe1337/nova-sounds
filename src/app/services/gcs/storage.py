"""
Google Cloud Storage operations for managing music tracks and videos.
"""
from typing import List, Optional, Dict, Any, Tuple
from google.cloud import storage
from google.api_core.exceptions import NotFound, Forbidden
import os
import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import threading
import concurrent.futures
from src.app.core.settings import DEV_MODE, DEBUG_MODE

# Set up logging
logger = logging.getLogger(__name__)

# Mock data for development mode
MOCK_TRACKS = [
    "track1.mp3",
    "track2.mp3",
    "track3.mp3",
    "track4.mp3",
    "track5.mp3"
]

# Get API key from environment
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# Initialize storage client if not in development mode
client = None
music_bucket = None
video_bucket = None

# Cache settings
CACHE_DIR = Path("data/cache/gcs")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
TRACKS_CACHE_FILE = CACHE_DIR / "tracks_cache.json"
TRACKS_CACHE_EXPIRY = timedelta(hours=6)  # Cache tracks list for 6 hours
tracks_cache_timestamp = None
tracks_cache = []

# URL cache to avoid generating multiple signed URLs for the same file
url_cache = {}
url_cache_expiry = {}

# Thread lock for thread-safe operations
cache_lock = threading.Lock()

def init_storage():
    """Initialize the storage client and buckets."""
    global client, music_bucket, video_bucket, DEV_MODE
    
    if DEV_MODE:
        logger.info("Running in DEV mode - using mock storage")
        return
        
    try:
        # Try to use service account credentials first
        if os.path.exists(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')):
            logger.info("Using service account credentials")
            client = storage.Client()
        elif GOOGLE_API_KEY:
            # Use API key if available
            logger.info("Using API key for anonymous access")
            client = storage.Client.create_anonymous_client()
        else:
            # No credentials available
            raise ValueError("No valid Google Cloud credentials found")
            
        # Get bucket names from environment or use defaults
        music_bucket_name = os.environ.get('GCS_BUCKET_NAME', 'youtubeshorts123')
        video_bucket_name = os.environ.get('GCS_VIDEO_BUCKET', 'youtubeshorts123')
        
        logger.info(f"Using music bucket: {music_bucket_name}")
        logger.info(f"Using video bucket: {video_bucket_name}")
        
        # Create references to buckets
        music_bucket = client.bucket(music_bucket_name)
        video_bucket = client.bucket(video_bucket_name)
        
        # If in debug mode, attempt to verify buckets exist
        if DEBUG_MODE:
            logger.info("Debug mode: Verifying buckets exist")
            music_bucket.reload()
            video_bucket.reload()
            logger.info("Buckets verified successfully")

    except Exception as e:
        logger.error(f"Error initializing GCS client: {e}")
        # Fallback to development mode
        logger.warning("Falling back to development mode for GCS operations")
        DEV_MODE = True

# Initialize on module import
init_storage()

def _load_tracks_cache() -> Tuple[List[str], bool]:
    """
    Load tracks from cache file.
    
    Returns:
        Tuple of (tracks list, cache_valid)
    """
    global tracks_cache, tracks_cache_timestamp
    
    # Use in-memory cache if available and valid
    if tracks_cache and tracks_cache_timestamp:
        if datetime.now() - tracks_cache_timestamp < TRACKS_CACHE_EXPIRY:
            return tracks_cache, True
    
    # Check if cache file exists and is not expired
    if TRACKS_CACHE_FILE.exists():
        try:
            stats = TRACKS_CACHE_FILE.stat()
            file_age = datetime.now() - datetime.fromtimestamp(stats.st_mtime)
            
            if file_age < TRACKS_CACHE_EXPIRY:
                with open(TRACKS_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Update in-memory cache
                        tracks_cache = data
                        tracks_cache_timestamp = datetime.now()
                        return data, True
        except Exception as e:
            logger.warning(f"Error loading tracks cache: {e}")
    
    return [], False

def _save_tracks_cache(tracks: List[str]):
    """Save tracks to cache file."""
    global tracks_cache, tracks_cache_timestamp
    
    # Update in-memory cache
    tracks_cache = tracks
    tracks_cache_timestamp = datetime.now()
    
    # Save to disk
    try:
        with open(TRACKS_CACHE_FILE, 'w') as f:
            json.dump(tracks, f)
    except Exception as e:
        logger.warning(f"Error saving tracks cache: {e}")

def list_music_tracks(limit: int = 100, prefix: str = None, use_cache: bool = True, file_extension: str = None) -> List[str]:
    """
    Fetch available music tracks from the GCS bucket.
    
    Args:
        limit: Maximum number of tracks to return (for pagination)
        prefix: Optional prefix filter for track names
        use_cache: Whether to use cached track list
        file_extension: Filter by file extension (e.g., '.mp3', '.wav')
        
    Returns:
        List[str]: List of track names
    """
    if DEV_MODE:
        # Return mock tracks in development mode
        logger.info("DEV mode: Returning mock music tracks")
        return MOCK_TRACKS
    
    # Check if we can use cache
    if use_cache and not prefix and not file_extension:
        cached_tracks, cache_valid = _load_tracks_cache()
        if cache_valid and len(cached_tracks) > 0:
            logger.info(f"Using cached track list ({len(cached_tracks)} tracks)")
            return cached_tracks[:limit] if limit < len(cached_tracks) else cached_tracks
    
    try:
        # Return real tracks from GCS
        tracks = []
        try:
            # Use prefix and pagination for large buckets
            if prefix:
                logger.info(f"Listing tracks with prefix: {prefix}")
                blobs = list(music_bucket.list_blobs(prefix=prefix, max_results=limit))
            else:
                blobs = list(music_bucket.list_blobs(max_results=limit))
                
            # Filter by file extension if specified, otherwise get all audio files
            if file_extension:
                tracks = [blob.name for blob in blobs if blob.name.endswith(file_extension)]
            else:
                tracks = [blob.name for blob in blobs if blob.name.endswith(('.mp3', '.wav', '.ogg', '.flac'))]
                
            logger.info(f"Found {len(tracks)} tracks in bucket {music_bucket.name}")
            
            # Save to cache if not using prefix or file_extension filter
            if not prefix and not file_extension:
                _save_tracks_cache(tracks)
                
        except Forbidden:
            logger.warning(f"Permission denied when listing tracks in bucket {music_bucket.name}")
            
        # If no tracks are found or permission denied, try cache
        if not tracks:
            cached_tracks, _ = _load_tracks_cache()
            if cached_tracks:
                logger.info(f"No tracks found or permission denied, using cached tracks ({len(cached_tracks)} tracks)")
                return cached_tracks[:limit] if limit < len(cached_tracks) else cached_tracks
            
            # If no cache available, return mock tracks
            logger.info("No cached tracks available, using mock tracks")
            return MOCK_TRACKS
            
        return tracks
    except Exception as e:
        logger.error(f"Error listing music tracks: {e}")
        # Try to use cache as fallback
        cached_tracks, _ = _load_tracks_cache()
        if cached_tracks:
            logger.info(f"Error listing tracks, using cached tracks ({len(cached_tracks)} tracks)")
            return cached_tracks[:limit] if limit < len(cached_tracks) else cached_tracks
        
        # Fall back to mock data if no cache
        return MOCK_TRACKS

def get_music_url(track_name: str, expires_in: int = 3600) -> str:
    """
    Generate a signed URL for a music track.
    
    Args:
        track_name: Name of the music track
        expires_in: URL expiration time in seconds
        
    Returns:
        str: Signed URL for accessing the track
    """
    # Check URL cache first
    with cache_lock:
        if track_name in url_cache and url_cache_expiry.get(track_name, datetime.min) > datetime.now():
            logger.debug(f"Using cached URL for {track_name}")
            return url_cache[track_name]
    
    if DEV_MODE:
        # Return a mock URL in development mode
        mock_url = f"http://localhost:8000/mock-media/{track_name}"
        logger.info(f"DEV mode: Returning mock URL: {mock_url}")
        
        # Cache the URL
        with cache_lock:
            url_cache[track_name] = mock_url
            url_cache_expiry[track_name] = datetime.now() + timedelta(seconds=expires_in)
            
        return mock_url
    
    try:
        # Generate a real URL
        blob = music_bucket.blob(track_name)
        
        # Try direct public URL first - since we're using uniform bucket-level access
        try:
            # Check if the blob exists
            blob.reload()
            # For uniform bucket-level access, use direct URL
            url = f"https://storage.googleapis.com/{music_bucket.name}/{track_name}"
            
            # Cache the URL
            with cache_lock:
                url_cache[track_name] = url
                url_cache_expiry[track_name] = datetime.now() + timedelta(seconds=expires_in)
                
            return url
        except Exception as e:
            logger.warning(f"Error accessing blob directly: {e}")
            # Fall back to signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=expires_in,
                method="GET"
            )
            
            # Cache the URL
            with cache_lock:
                url_cache[track_name] = url
                url_cache_expiry[track_name] = datetime.now() + timedelta(seconds=expires_in)
                
            return url
    except Exception as e:
        logger.error(f"Error generating URL for {track_name}: {e}")
        # Fall back to mock URL
        url = f"http://localhost:8000/mock-media/{track_name}"
        
        # Cache the URL
        with cache_lock:
            url_cache[track_name] = url
            url_cache_expiry[track_name] = datetime.now() + timedelta(seconds=expires_in)
            
        return url

def batch_get_music_urls(track_names: List[str], expires_in: int = 3600) -> Dict[str, str]:
    """
    Generate signed URLs for multiple music tracks in parallel.
    
    Args:
        track_names: List of track names
        expires_in: URL expiration time in seconds
        
    Returns:
        Dict mapping track names to URLs
    """
    if DEV_MODE:
        return {track: f"http://localhost:8000/mock-media/{track}" for track in track_names}
    
    result = {}
    
    # Check cache first
    cached_tracks = []
    tracks_to_fetch = []
    
    with cache_lock:
        for track_name in track_names:
            if track_name in url_cache and url_cache_expiry.get(track_name, datetime.min) > datetime.now():
                result[track_name] = url_cache[track_name]
                cached_tracks.append(track_name)
            else:
                tracks_to_fetch.append(track_name)
    
    # If all tracks are in cache, return immediately
    if not tracks_to_fetch:
        return result
    
    # Generate URLs in parallel for remaining tracks
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_track = {
            executor.submit(get_music_url, track, expires_in): track 
            for track in tracks_to_fetch
        }
        
        for future in concurrent.futures.as_completed(future_to_track):
            track = future_to_track[future]
            try:
                url = future.result()
                result[track] = url
            except Exception as e:
                logger.error(f"Error generating URL for {track}: {e}")
                result[track] = f"http://localhost:8000/mock-media/{track}"
    
    return result

def upload_video(video_path: str, destination_name: str) -> str:
    """
    Upload a video file to Google Cloud Storage.
    
    Args:
        video_path: Path to the video file
        destination_name: Name to give the uploaded video
        
    Returns:
        str: Public URL for the uploaded video
    """
    if DEV_MODE:
        logger.info(f"DEV mode: Mock upload - video_path: {video_path}, destination: {destination_name}")
        return f"https://storage.googleapis.com/mock-bucket/{destination_name}"
        
    # Upload to GCS
    try:
        blob = video_bucket.blob(destination_name)
        blob.upload_from_filename(video_path)
        
        # Make the blob publicly available if needed
        blob.make_public()
        
        # Return the public URL
        logger.info(f"Video uploaded successfully to {destination_name}")
        return blob.public_url
    except Exception as e:
        logger.error(f"Error uploading video to GCS: {e}")
        if DEBUG_MODE:
            # In debug mode, create a local copy instead
            local_path = os.path.join("media", destination_name)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            import shutil
            shutil.copy(video_path, local_path)
            logger.info(f"DEBUG mode: Created local copy at {local_path}")
            return f"/media/{destination_name}"
        raise e

def upload_file(file_path: str, destination_name: str) -> str:
    """
    Upload any file to Google Cloud Storage.
    
    Args:
        file_path: Path to the file
        destination_name: Name to give the uploaded file
        
    Returns:
        str: Public URL for the uploaded file
    """
    if DEV_MODE:
        logger.info(f"DEV mode: Mock upload - file_path: {file_path}, destination: {destination_name}")
        return f"https://storage.googleapis.com/mock-bucket/{destination_name}"
        
    # Upload to GCS
    try:
        blob = video_bucket.blob(destination_name)
        blob.upload_from_filename(file_path)
        
        # Make the blob publicly available if needed
        blob.make_public()
        
        # Return the public URL
        return blob.public_url
    except Exception as e:
        logger.error(f"Error uploading file to GCS: {e}")
        if DEBUG_MODE:
            # In debug mode, create a local copy instead
            local_path = os.path.join("media", destination_name)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            import shutil
            shutil.copy(file_path, local_path)
            logger.info(f"DEBUG mode: Created local copy at {local_path}")
            return f"/media/{destination_name}"
        raise e

def download_file(source_blob_name: str, destination_file_name: str, bucket_name: str = None) -> str:
    """
    Download a file from GCS.
    
    Args:
        source_blob_name: Name of the blob to download
        destination_file_name: Path to save the file
        bucket_name: Optional bucket name, defaults to music bucket
        
    Returns:
        str: Path to the downloaded file
    """
    if DEV_MODE:
        # In dev mode, create a mock file
        logger.info(f"DEV mode: Creating mock file for {source_blob_name} at {destination_file_name}")
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
        
        # Create a mock file
        with open(destination_file_name, 'w') as f:
            f.write(f"Mock file for {source_blob_name}")
            
        return destination_file_name
        
    try:
        # Use the specified bucket or default to music bucket
        bucket = music_bucket if not bucket_name else client.bucket(bucket_name)
        
        # Get the blob
        blob = bucket.blob(source_blob_name)
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
        
        # Download the file
        blob.download_to_filename(destination_file_name)
        
        logger.info(f"Downloaded {source_blob_name} to {destination_file_name}")
        return destination_file_name
        
    except Exception as e:
        logger.error(f"Error downloading file {source_blob_name}: {e}")
        raise

def batch_download_files(file_specs: List[Tuple[str, str, str]], max_workers: int = 5) -> Dict[str, bool]:
    """
    Download multiple files in parallel.
    
    Args:
        file_specs: List of tuples (bucket_name, source_blob_name, destination_file_name)
        max_workers: Maximum number of parallel downloads
        
    Returns:
        Dict[str, bool]: Dictionary of source_blob_name to success status
    """
    if DEV_MODE:
        logger.info(f"DEV mode: Mock batch download of {len(file_specs)} files")
        results = {}
        for bucket_name, source, dest in file_specs:
            try:
                download_file(source, dest, bucket_name)
                results[source] = True
            except Exception:
                results[source] = False
        return results
    
    results = {}
    future_to_source = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all downloads
        for bucket_name, source, dest in file_specs:
            future = executor.submit(download_file, source, dest, bucket_name)
            future_to_source[future] = source
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_source):
            source = future_to_source[future]
            try:
                future.result()
                results[source] = True
            except Exception:
                results[source] = False
    
    return results

def get_image_for_track(track_name: str) -> Optional[str]:
    """
    Get a cover image URL for a music track.
    
    Args:
        track_name: Name of the track
        
    Returns:
        Optional URL to cover image
    """
    if DEV_MODE:
        # Return mock image URL
        return f"http://localhost:8000/mock-media/covers/{os.path.splitext(track_name)[0]}.jpg"
    
    try:
        # Try to find an image with the same name but different extension
        base_name = os.path.splitext(track_name)[0]
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        
        for ext in image_extensions:
            image_name = f"{base_name}{ext}"
            try:
                # Check if image exists
                blob = music_bucket.blob(image_name)
                blob.reload()
                
                # Get URL for the image
                return get_music_url(image_name)
            except Exception:
                # Image not found, try next extension
                continue
        
        # Try to find image in a covers/ subdirectory
        for ext in image_extensions:
            image_name = f"covers/{os.path.basename(base_name)}{ext}"
            try:
                # Check if image exists
                blob = music_bucket.blob(image_name)
                blob.reload()
                
                # Get URL for the image
                return get_music_url(image_name)
            except Exception:
                # Image not found, try next extension
                continue
        
        # No image found
        return None
        
    except Exception as e:
        logger.error(f"Error getting image for track {track_name}: {e}")
        return None

def upload_batch_files(file_specs: List[Tuple[str, str]], max_workers: int = 5) -> Dict[str, str]:
    """
    Upload multiple files in parallel.
    
    Args:
        file_specs: List of tuples (local_path, destination_name)
        max_workers: Maximum number of upload workers
        
    Returns:
        Dict mapping destination names to URLs
    """
    results = {}
    
    if DEV_MODE:
        logger.info(f"DEV mode: Mock batch upload for {len(file_specs)} files")
        for _, dest in file_specs:
            results[dest] = f"https://storage.googleapis.com/mock-bucket/{dest}"
        return results
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_dest = {}
        
        for local_path, dest in file_specs:
            future = executor.submit(upload_file, local_path, dest)
            future_to_dest[future] = dest
        
        for future in concurrent.futures.as_completed(future_to_dest):
            dest = future_to_dest[future]
            try:
                url = future.result()
                results[dest] = url
            except Exception as e:
                logger.error(f"Error uploading file to {dest}: {e}")
                results[dest] = f"https://storage.googleapis.com/mock-bucket/{dest}"
    
    return results

def extract_music_metadata(track_name: str) -> dict:
    """
    Extract metadata from a music track directly from GCS.
    
    Args:
        track_name: Name of the track in the bucket
        
    Returns:
        Dict with track metadata
    """
    # We'll use another module to handle the actual metadata extraction
    from src.app.services.gcs.music_metadata import get_track_metadata
    return get_track_metadata(track_name)

def list_music_by_genre(genre: str, limit: int = 20) -> List[str]:
    """
    List music tracks filtered by genre.
    
    Args:
        genre: Genre to filter by
        limit: Maximum number of tracks to return
        
    Returns:
        List of track names matching the genre
    """
    # This uses the search_tracks_by_metadata function from music_metadata
    from src.app.services.gcs.music_metadata import search_tracks_by_metadata
    
    results = search_tracks_by_metadata(genre=genre)
    tracks = [result.get("track_name") for result in results if "track_name" in result]
    
    return tracks[:limit]

def list_music_by_mood(mood: str, limit: int = 20) -> List[str]:
    """
    List music tracks filtered by mood.
    
    Args:
        mood: Mood to filter by
        limit: Maximum number of tracks to return
        
    Returns:
        List of track names matching the mood
    """
    # This uses the search_tracks_by_metadata function from music_metadata
    from src.app.services.gcs.music_metadata import search_tracks_by_metadata
    
    results = search_tracks_by_metadata(mood=mood)
    tracks = [result.get("track_name") for result in results if "track_name" in result]
    
    return tracks[:limit]

def search_music(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for music tracks matching a keyword.
    
    Args:
        keyword: Keyword to search for in track metadata
        limit: Maximum number of tracks to return
        
    Returns:
        List of track metadata matching the keyword
    """
    # This uses the search_tracks_by_metadata function from music_metadata
    from src.app.services.gcs.music_metadata import search_tracks_by_metadata
    
    results = search_tracks_by_metadata(keyword=keyword)
    
    # Return limited results
    return results[:limit]

def get_bucket_stats() -> Dict[str, Any]:
    """
    Get statistics about the music and video buckets.
    
    Returns:
        Dict with statistics
    """
    if DEV_MODE:
        return {
            "music_bucket": {
                "name": "mock-music-bucket",
                "track_count": len(MOCK_TRACKS),
                "size_bytes": 1024 * 1024 * 100,  # Mock 100MB
                "last_updated": datetime.now().isoformat()
            },
            "video_bucket": {
                "name": "mock-video-bucket",
                "video_count": 10,
                "size_bytes": 1024 * 1024 * 500,  # Mock 500MB
                "last_updated": datetime.now().isoformat()
            }
        }
    
    try:
        # Get music bucket stats
        music_stats = {
            "name": music_bucket.name,
            "track_count": 0,
            "size_bytes": 0,
            "last_updated": None
        }
        
        # Get video bucket stats
        video_stats = {
            "name": video_bucket.name,
            "video_count": 0,
            "size_bytes": 0,
            "last_updated": None
        }
        
        # Count and size for music bucket
        for blob in music_bucket.list_blobs():
            if any(blob.name.endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.flac']):
                music_stats["track_count"] += 1
                music_stats["size_bytes"] += blob.size
                if music_stats["last_updated"] is None or blob.updated > music_stats["last_updated"]:
                    music_stats["last_updated"] = blob.updated
        
        # Count and size for video bucket
        for blob in video_bucket.list_blobs():
            if any(blob.name.endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.webm']):
                video_stats["video_count"] += 1
                video_stats["size_bytes"] += blob.size
                if video_stats["last_updated"] is None or blob.updated > video_stats["last_updated"]:
                    video_stats["last_updated"] = blob.updated
        
        # Convert timestamps to ISO format
        if music_stats["last_updated"]:
            music_stats["last_updated"] = music_stats["last_updated"].isoformat()
        if video_stats["last_updated"]:
            video_stats["last_updated"] = video_stats["last_updated"].isoformat()
        
        return {
            "music_bucket": music_stats,
            "video_bucket": video_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting bucket stats: {e}")
        return {
            "error": str(e),
            "music_bucket": {"name": music_bucket.name if music_bucket else "unknown"},
            "video_bucket": {"name": video_bucket.name if video_bucket else "unknown"}
        }

def refresh_gcs_cache():
    """Force refresh of all GCS-related caches."""
    global tracks_cache, tracks_cache_timestamp, url_cache, url_cache_expiry
    
    # Clear URL cache
    with cache_lock:
        url_cache = {}
        url_cache_expiry = {}
    
    # Force refresh tracks list
    logger.info("Refreshing tracks cache")
    list_music_tracks(use_cache=False)
    
    # Refresh metadata cache
    from src.app.services.gcs.music_metadata import refresh_metadata_cache
    refresh_metadata_cache(force=True)
    
    logger.info("GCS cache refresh complete")

def get_track_details(track_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a music track.
    
    Args:
        track_name: Name of the track
        
    Returns:
        Dict with track details
    """
    # Get metadata
    metadata = extract_music_metadata(track_name)
    
    if not metadata:
        return {"error": "Track not found or metadata extraction failed"}
    
    # Get URL
    url = get_music_url(track_name)
    
    # Get cover image
    cover_image = get_image_for_track(track_name)
    
    # Prepare response
    response = {
        "track_name": track_name,
        "url": url,
        "cover_image": cover_image,
        "metadata": metadata
    }
    
    # Get waveform data if available
    try:
        from src.app.services.gcs.music_metadata import get_track_waveform
        response["waveform"] = get_track_waveform(track_name)
    except Exception as e:
        logger.warning(f"Error getting waveform for {track_name}: {e}")
    
    return response

def batch_get_track_details(track_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get detailed information about multiple tracks in parallel.
    
    Args:
        track_names: List of track names
        
    Returns:
        Dict mapping track names to their details
    """
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_track = {
            executor.submit(get_track_details, track): track 
            for track in track_names
        }
        
        for future in concurrent.futures.as_completed(future_to_track):
            track = future_to_track[future]
            try:
                details = future.result()
                results[track] = details
            except Exception as e:
                logger.error(f"Error getting details for {track}: {e}")
                results[track] = {"error": str(e)}
    
    return results

def get_music_path(track_id: str) -> Optional[str]:
    """
    Get the local path to a music track, downloading it if necessary.
    
    Args:
        track_id: ID or filename of the track
        
    Returns:
        Optional[str]: Path to the local music file or None if not found
    """
    if DEV_MODE:
        # In dev mode, check if file exists in mock-media folder
        mock_media_dir = Path("mock-media")
        if not mock_media_dir.exists():
            mock_media_dir.mkdir(parents=True, exist_ok=True)
            
        # Check if the track already exists in mock-media
        local_path = mock_media_dir / track_id
        if local_path.exists():
            return str(local_path)
            
        # If not, create a mock file
        with open(local_path, 'w') as f:
            f.write(f"Mock music file for {track_id}")
            
        return str(local_path)
        
    # For production, check if file exists in cache
    cache_dir = Path("data/cache/music")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    local_path = cache_dir / track_id
    if local_path.exists():
        return str(local_path)
        
    # If not in cache, download from GCS
    try:
        download_file("music", track_id, str(local_path))
        return str(local_path)
    except Exception as e:
        logger.error(f"Error downloading music file {track_id}: {e}")
        return None 