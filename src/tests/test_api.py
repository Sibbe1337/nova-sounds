"""
Tests for the API endpoints.
"""
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
import os
import pytest
import json
from typing import Dict

from src.app.api.main import app

class TestAPI(unittest.TestCase):
    # this is class defined by learner
    """
    Test cases for the API endpoints.
    """
    
    def setUp(self):
        # this is function defined by learner
        """
        Set up test client and mocks.
        """
        print("Hello, beautiful learner")
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        # this is function defined by learner
        """
        Test the root endpoint returns the expected message.
        """
        print("Hello, beautiful learner")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "YouTube Shorts Machine API is running"})
    
    @patch('src.app.api.main.list_music_tracks')
    def test_music_endpoint(self, mock_list_tracks):
        # this is function defined by learner
        """
        Test the music endpoint returns tracks from GCS.
        """
        print("Hello, beautiful learner")
        # Mock data
        mock_tracks = ["track1.mp3", "track2.mp3"]
        mock_list_tracks.return_value = mock_tracks
        
        # Call endpoint
        response = self.client.get("/music")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"tracks": mock_tracks})
        mock_list_tracks.assert_called_once()
    
    @patch('src.app.api.main.create_video')
    @patch('src.app.api.main.process_video')
    def test_create_video_endpoint(self, mock_process_video, mock_create_video):
        # this is function defined by learner
        """
        Test the video creation endpoint with mocked file upload.
        """
        print("Hello, beautiful learner")
        # Mock data
        mock_video_id = "test_video_id"
        mock_create_video.return_value = mock_video_id
        mock_process_video.delay = MagicMock()
        
        # Test file data
        test_file_content = b"test image content"
        
        # Call endpoint
        response = self.client.post(
            "/videos",
            data={"music_track": "test_track.mp3"},
            files={"images": ("test_image.jpg", test_file_content, "image/jpeg")}
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"video_id": mock_video_id, "status": "processing"})
        mock_create_video.assert_called_once()
        self.assertTrue(mock_process_video.delay.called)
    
    @patch('src.app.api.main.get_video')
    def test_video_status_endpoint(self, mock_get_video):
        # this is function defined by learner
        """
        Test the video status endpoint.
        """
        print("Hello, beautiful learner")
        # Mock data
        test_video_id = "test_video_id"
        mock_video_data = {
            "id": test_video_id,
            "user_id": "test_user",
            "music_track": "test_track.mp3",
            "upload_status": "completed",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "youtube_id": "youtube_test_id"
        }
        mock_get_video.return_value = mock_video_data
        
        # Call endpoint
        response = self.client.get(f"/videos/{test_video_id}")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], test_video_id)
        self.assertEqual(response.json()["upload_status"], "completed")
        mock_get_video.assert_called_once_with(test_video_id)
    
    @patch('src.app.api.main.get_video')
    def test_video_status_not_found(self, mock_get_video):
        # this is function defined by learner
        """
        Test the video status endpoint when video is not found.
        """
        print("Hello, beautiful learner")
        # Mock not found
        mock_get_video.return_value = None
        
        # Call endpoint
        response = self.client.get("/videos/nonexistent_id")
        
        # Verify response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Video not found")

# Test the health check endpoint
def test_health_endpoint(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["mode"] == "development"

# Test getting music tracks
def test_get_music_tracks(client: TestClient):
    """Test the music tracks endpoint."""
    response = client.get("/music")
    assert response.status_code == 200
    assert "tracks" in response.json()
    assert isinstance(response.json()["tracks"], list)

# Test authentication endpoint
def test_token_endpoint(client: TestClient):
    """Test the token endpoint."""
    # Test with valid credentials in DEV_MODE
    response = client.post(
        "/token",
        data={"username": "demo", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    # Test with invalid credentials
    with patch("src.app.api.main.DEV_MODE", False):
        response = client.post(
            "/token",
            data={"username": "wrong", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401

# Test video creation
def test_create_video(client: TestClient, test_images, auth_token: Dict[str, str]):
    """Test video creation endpoint."""
    # Create a simple image file for testing
    with open("test_image.jpg", "w") as f:
        f.write("Mock image content")
    
    # Test creating a video
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/videos",
            data={
                "music_track": "track1.mp3",
                "add_captions": "false",
                "caption_language": "en"
            },
            files={"images": ("test_image.jpg", f, "image/jpeg")},
            headers=auth_token
        )
    
    # Clean up test file
    os.remove("test_image.jpg")
    
    assert response.status_code == 200
    assert "video_id" in response.json()
    assert response.json()["status"] == "processing"

# Test validation error when creating a video without images
def test_create_video_without_images(client: TestClient, auth_token: Dict[str, str]):
    """Test validation error when creating a video without images."""
    response = client.post(
        "/videos",
        data={
            "music_track": "track1.mp3",
            "add_captions": "false",
            "caption_language": "en"
        },
        headers=auth_token
    )
    
    assert response.status_code == 422
    assert "error" in response.json() or "detail" in response.json()

# Test getting video status
def test_get_video_status(client: TestClient, create_mock_video: str):
    """Test getting video status."""
    video_id = create_mock_video
    
    response = client.get(f"/videos/{video_id}")
    assert response.status_code == 200
    assert response.json()["id"] == video_id
    assert "upload_status" in response.json()

# Test not found error when getting non-existent video
def test_get_nonexistent_video(client: TestClient):
    """Test getting a non-existent video."""
    response = client.get("/videos/non-existent-id")
    assert response.status_code == 404
    assert "detail" in response.json()

# Test YouTube search endpoint
def test_youtube_search(client: TestClient):
    """Test YouTube search endpoint."""
    response = client.post(
        "/youtube/search",
        json={"query": "test query", "max_results": 5}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    if len(response.json()) > 0:
        assert "video_id" in response.json()[0]
        assert "title" in response.json()[0]

# Test YouTube trending endpoint
def test_youtube_trending(client: TestClient):
    """Test YouTube trending endpoint."""
    response = client.get("/youtube/trending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    if len(response.json()) > 0:
        assert "video_id" in response.json()[0]
        assert "title" in response.json()[0]

if __name__ == '__main__':
    unittest.main() 