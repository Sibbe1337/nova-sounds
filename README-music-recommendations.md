# Intelligent Music Recommendations Feature

## Overview

The Intelligent Music Recommendations feature uses AI to analyze your video content and suggest the perfect music tracks that match its style, pacing, mood, and energy. This helps create more engaging and cohesive content by ensuring the music complements your video.

## Key Features

- **Content-Based Matching**: Analyzes your video's visual characteristics to find matching music
- **Similar Track Recommendations**: Discover tracks similar to ones you already like
- **Trending Music**: Find currently popular tracks to increase engagement
- **Smart Filters**: Refine recommendations by genre, mood, tempo, and energy level
- **Preview With Video**: See and hear how recommended tracks work with your video before deciding

## How It Works

1. **Video Analysis**: The system analyzes your video for key characteristics:
   - Pace (slow, medium, fast)
   - Energy level
   - Mood/atmosphere
   - Visual style
   - Presence of speech
   - Movement level

2. **Music Matching**: Based on the analysis, the system finds music tracks that complement your video:
   - Matches tempo with video pace
   - Aligns energy levels
   - Complements visual mood with music mood
   - Considers speech (suggesting less intrusive tracks when speech is present)

3. **Scoring and Ranking**: Tracks are scored for compatibility and ranked to show you the best matches first

## Usage

### Through the Web Interface

1. **Upload Your Video**: Upload your video to the YouTube Shorts Machine
2. **Go to Music Recommendations**: Navigate to the Intelligent Music Recommendations section
3. **Choose Recommendation Type**:
   - **From This Video**: Get recommendations based on your uploaded video
   - **Similar To Track**: Find tracks similar to one you already like
   - **Trending Tracks**: See what's currently popular
4. **Set Filters** (optional): Refine results by genre, mood, tempo, or energy level
5. **Get Recommendations**: Click "Get Recommendations" to see matching tracks
6. **Preview and Select**: Listen to previews, see how they match with your video, and select the perfect track

### Using the API

```python
from src.app.services.music.recommendations import get_music_recommendation_service

# Create recommendation service instance
recommender = get_music_recommendation_service()

# Get recommendations for a video
recommendations = recommender.recommend_for_video(
    video_path="/path/to/video.mp4",
    count=5,
    preferred_genres=["Electronic", "Hip Hop"],
    preferred_moods=["Upbeat"],
    min_bpm=90,
    max_bpm=120,
    energy_level=0.7
)

# Find tracks similar to a reference track
similar_tracks = recommender.recommend_similar(
    track_name="electronic_beat.mp3",
    count=5
)

# Get trending tracks
trending_tracks = recommender.recommend_trending(count=5)
```

### Using the Demo Script

The `test_music_recommendation_demo.py` script provides a convenient way to test the feature:

```bash
# Analyze a video
python test_music_recommendation_demo.py --mode analyze --video /path/to/video.mp4

# Get recommendations for a video
python test_music_recommendation_demo.py --mode recommend --video /path/to/video.mp4 --count 5 --genre "Electronic" --mood "Upbeat"

# Find similar tracks
python test_music_recommendation_demo.py --mode similar --track electronic_beat.mp3 --count 5

# Get trending tracks
python test_music_recommendation_demo.py --mode trending --count 5
```

## API Endpoints

- `POST /music-recommendations/for-video` - Get recommendations for an existing video
- `POST /music-recommendations/for-uploaded-video` - Upload a video and get recommendations
- `GET /music-recommendations/similar/{track_name}` - Find tracks similar to a reference track
- `GET /music-recommendations/trending` - Get currently trending tracks
- `POST /music-recommendations/batch-recommend` - Get recommendations for multiple videos

## Demo Files

For testing purposes, you can use the sample videos and music tracks in the `sample_music/` directory.

## Troubleshooting

### Common Issues

1. **No recommendations are returned**
   - Ensure your video file is valid and not corrupted
   - Try with different filter settings, or no filters at all
   - Check that the music library contains tracks that match your criteria

2. **Recommendations don't match video content well**
   - Try uploading a higher quality video for better analysis
   - Use the filters to manually specify genre, mood, or tempo
   - For videos with speech, select tracks with lower energy levels

3. **Preview with video doesn't work**
   - Ensure your browser supports HTML5 video playback
   - Check that both the video and audio files are accessible

## Future Enhancements

1. Machine learning model to improve recommendation accuracy over time
2. User feedback loop to refine recommendations based on selections
3. Advanced beat matching to sync music with video transitions
4. Custom track generation based on video analysis
5. Expanded music library with more genres and styles

## Credits

This feature uses the following libraries:
- OpenCV for video analysis
- librosa for audio analysis
- FFmpeg for media processing 