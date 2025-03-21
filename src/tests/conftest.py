"""
Test fixtures and configuration for the YouTube Shorts Machine application.
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Generator, Any
from fastapi.testclient import TestClient
import json

# Ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set up test environment
os.environ["DEV_MODE"] = "true"
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"

# Import application modules after setting environment variables
from src.app.api.main import app
from src.app.core.errors import ApplicationError
from src.app.core.database import MOCK_VIDEOS

# Test client
@pytest.fixture
def client() -> TestClient:
    """
    Create a FastAPI TestClient for the application.
    
    Returns:
        TestClient: Test client
    """
    return TestClient(app)

# Temp directory for test files
@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for test files.
    
    Yields:
        str: Path to temporary directory
    """
    test_dir = tempfile.mkdtemp()
    yield test_dir
    # Clean up after tests
    shutil.rmtree(test_dir)

# Create test image files
@pytest.fixture
def test_images(temp_dir: str) -> List[str]:
    """
    Create test image files for testing.
    
    Args:
        temp_dir: Temporary directory
        
    Returns:
        List[str]: List of image file paths
    """
    image_paths = []
    for i in range(3):
        img_path = os.path.join(temp_dir, f"test_image_{i}.jpg")
        # Create a small test image file
        with open(img_path, "w") as f:
            f.write(f"Mock image content for test_image_{i}.jpg")
        image_paths.append(img_path)
        
    return image_paths

# Create test music file
@pytest.fixture
def test_music(temp_dir: str) -> str:
    """
    Create a test music file for testing.
    
    Args:
        temp_dir: Temporary directory
        
    Returns:
        str: Path to test music file
    """
    music_path = os.path.join(temp_dir, "test_music.mp3")
    # Create a small test music file
    with open(music_path, "w") as f:
        f.write("Mock audio content for test_music.mp3")
        
    return music_path

# Mock video data
@pytest.fixture
def mock_video_data() -> Dict[str, Any]:
    """
    Create mock video data for testing.
    
    Returns:
        Dict[str, Any]: Mock video data
    """
    return {
        "user_id": "test_user",
        "music_track": "test_music.mp3",
        "upload_status": "pending",
        "created_at": "2025-03-18T14:20:08.300797",
        "updated_at": "2025-03-18T14:20:08.301190"
    }

# Helper function to create a mock video in the database
@pytest.fixture
def create_mock_video(mock_video_data: Dict[str, Any]) -> str:
    """
    Create a mock video in the database for testing.
    
    Args:
        mock_video_data: Mock video data
        
    Returns:
        str: Video ID
    """
    from src.app.core.database import create_video
    video_id = create_video(mock_video_data)
    return video_id

# Clean up the mock database before each test
@pytest.fixture(autouse=True)
def clear_mock_database():
    """Clear the mock database before each test."""
    MOCK_VIDEOS.clear()

# Authentication token for testing
@pytest.fixture
def auth_token() -> Dict[str, str]:
    """
    Get authentication token for testing.
    
    Returns:
        Dict[str, str]: Authentication token
    """
    return {"Authorization": "Bearer mock_access_token"} 