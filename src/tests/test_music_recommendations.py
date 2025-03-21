"""
Unit tests for the music recommendation service.
"""
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock

from src.app.services.music.recommendations import MusicRecommendationService, get_music_recommendation_service
from src.app.services.gcs.storage import list_music_tracks

class TestMusicRecommendationService(unittest.TestCase):
    """Test cases for the MusicRecommendationService."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary test video file
        self.temp_video_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        self.temp_video_file.write(b'mock video content')
        self.temp_video_file.close()
        self.video_path = self.temp_video_file.name
        
        # Mock track data
        self.mock_tracks = [
            "electronic_beat.mp3",
            "hip_hop_groove.mp3",
            "pop_anthem.mp3",
            "ambient_chill.mp3",
            "cinematic_drama.mp3"
        ]
        
        # Mock track metadata
        self.mock_metadata = {
            "track_name": "electronic_beat.mp3",
            "title": "Electronic Beat",
            "artist": "Nova Sounds",
            "genre": "Electronic",
            "bpm": 128,
            "key": "C Major",
            "duration": 180,
            "energy": 0.85,
            "mood": "Upbeat"
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary test file
        if os.path.exists(self.video_path):
            os.unlink(self.video_path)
    
    def test_singleton_pattern(self):
        """Test that the service follows the singleton pattern."""
        service1 = MusicRecommendationService()
        service2 = MusicRecommendationService()
        self.assertIs(service1, service2)
        
        # Test factory function
        service3 = get_music_recommendation_service()
        self.assertIs(service1, service3)
    
    @patch('src.app.services.music.recommendations.search_tracks_by_metadata')
    @patch('src.app.services.music.recommendations.MusicRecommendationService._analyze_video')
    def test_recommend_for_video(self, mock_analyze_video, mock_search_tracks):
        """Test music recommendations based on video content."""
        # Set up mocks
        mock_analyze_video.return_value = {
            "pace": "medium",
            "energy": 0.6,
            "atmosphere": "bright",
            "dominant_colors": ["#3A86FF", "#FF006E", "#FFBE0B"],
            "has_speech": False,
            "movement_level": 0.5
        }
        
        # Mock search results
        mock_search_tracks.return_value = [
            {
                "track_name": "electronic_beat.mp3",
                "title": "Electronic Beat",
                "artist": "Nova Sounds",
                "genre": "Electronic",
                "bpm": 128,
                "key": "C Major",
                "duration": 180,
                "energy": 0.85,
                "mood": "Upbeat"
            },
            {
                "track_name": "pop_anthem.mp3",
                "title": "Pop Anthem",
                "artist": "Nova Sounds",
                "genre": "Pop",
                "bpm": 120,
                "key": "A Major",
                "duration": 195,
                "energy": 0.8,
                "mood": "Happy"
            }
        ]
        
        # Get recommendations
        service = get_music_recommendation_service()
        recommendations = service.recommend_for_video(
            video_path=self.video_path,
            count=2
        )
        
        # Verify results
        self.assertEqual(len(recommendations), 2)
        self.assertIn("track_name", recommendations[0])
        self.assertIn("relevance_score", recommendations[0])
        
        # Verify the video was analyzed
        mock_analyze_video.assert_called_once_with(self.video_path)
        
        # Verify search was performed with correct parameters
        mock_search_tracks.assert_called_once()
        args, kwargs = mock_search_tracks.call_args
        self.assertIn("min_bpm", kwargs)
        self.assertIn("max_bpm", kwargs)
        self.assertIn("energy_range", kwargs)
    
    @patch('src.app.services.music.recommendations.get_track_metadata')
    @patch('src.app.services.music.recommendations.search_tracks_by_metadata')
    def test_recommend_similar(self, mock_search_tracks, mock_get_metadata):
        """Test similar track recommendations."""
        # Set up mocks
        mock_get_metadata.return_value = self.mock_metadata
        
        # Mock search results
        mock_search_tracks.return_value = [
            {
                "track_name": "another_electronic.mp3",
                "title": "Another Electronic",
                "artist": "Nova Sounds",
                "genre": "Electronic",
                "bpm": 130,
                "key": "A Minor",
                "duration": 185,
                "energy": 0.8,
                "mood": "Upbeat"
            },
            {
                "track_name": "dance_track.mp3",
                "title": "Dance Track",
                "artist": "Nova Sounds",
                "genre": "Electronic",
                "bpm": 125,
                "key": "D Major",
                "duration": 190,
                "energy": 0.82,
                "mood": "Upbeat"
            }
        ]
        
        # Get recommendations
        service = get_music_recommendation_service()
        recommendations = service.recommend_similar(
            track_name="electronic_beat.mp3",
            count=2
        )
        
        # Verify results
        self.assertEqual(len(recommendations), 2)
        self.assertIn("track_name", recommendations[0])
        self.assertIn("similarity_score", recommendations[0])
        
        # Verify metadata was fetched
        mock_get_metadata.assert_called_once_with("electronic_beat.mp3")
        
        # Verify search was performed with correct parameters
        mock_search_tracks.assert_called_once()
        args, kwargs = mock_search_tracks.call_args
        self.assertEqual(kwargs["genre"], "Electronic")
        self.assertEqual(kwargs["mood"], "Upbeat")
        self.assertIn("min_bpm", kwargs)
        self.assertIn("max_bpm", kwargs)
        self.assertIn("energy_range", kwargs)
    
    @patch('src.app.services.music.recommendations.list_music_tracks')
    @patch('src.app.services.music.recommendations.get_track_metadata')
    def test_recommend_trending(self, mock_get_metadata, mock_list_tracks):
        """Test trending tracks recommendations."""
        # Set up mocks
        mock_list_tracks.return_value = self.mock_tracks[:3]
        mock_get_metadata.return_value = self.mock_metadata
        
        # Get recommendations
        service = get_music_recommendation_service()
        recommendations = service.recommend_trending(count=3)
        
        # Verify results
        self.assertEqual(len(recommendations), 3)
        self.assertIn("track_name", recommendations[0])
        self.assertIn("popularity", recommendations[0])
        
        # Verify track list was fetched
        mock_list_tracks.assert_called_once()
        
        # Verify metadata was fetched for tracks
        self.assertEqual(mock_get_metadata.call_count, 3)
    
    def test_analyze_video(self):
        """Test video analysis functionality."""
        service = get_music_recommendation_service()
        result = service._analyze_video(self.video_path)
        
        # Verify analysis result structure
        self.assertIn("pace", result)
        self.assertIn("energy", result)
        self.assertIn("atmosphere", result)
        self.assertIn("dominant_colors", result)
        self.assertIn("has_speech", result)
        self.assertIn("movement_level", result)
    
    def test_score_tracks_for_video(self):
        """Test track scoring based on video features."""
        service = get_music_recommendation_service()
        
        # Mock video features
        video_features = {
            "pace": "medium",
            "energy": 0.7,
            "atmosphere": "bright",
            "has_speech": False,
            "movement_level": 0.6
        }
        
        # Mock tracks
        tracks = [
            {
                "track_name": "track1.mp3",
                "energy": 0.7,  # Perfect energy match
                "mood": "upbeat"  # Good atmosphere match for "bright"
            },
            {
                "track_name": "track2.mp3",
                "energy": 0.4,  # Poor energy match
                "mood": "melancholic"  # Poor atmosphere match for "bright"
            }
        ]
        
        scored_tracks = service._score_tracks_for_video(tracks, video_features)
        
        # Verify tracks were scored
        self.assertEqual(len(scored_tracks), 2)
        self.assertIn("relevance_score", scored_tracks[0])
        self.assertIn("relevance_score", scored_tracks[1])
        
        # Verify the first track has a higher score due to better matches
        self.assertGreater(scored_tracks[0]["relevance_score"], scored_tracks[1]["relevance_score"])

if __name__ == '__main__':
    unittest.main() 