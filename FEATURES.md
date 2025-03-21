# YouTube Shorts Machine - Feature Documentation

This document provides detailed information about the advanced features implemented in the YouTube Shorts Machine.

## Table of Contents
1. [Thumbnail Optimization](#thumbnail-optimization)
2. [Cross-Platform Publishing](#cross-platform-publishing)
3. [Content Scheduling and Batch Processing](#content-scheduling-and-batch-processing)
4. [Intelligent Music Recommendations](#intelligent-music-recommendations)
5. [API Reference](#api-reference)

## Thumbnail Optimization

The Thumbnail Optimizer helps create effective thumbnails that drive higher click-through rates.

### Features

- **Variant Generation**: Create multiple thumbnail styles from a single base image
- **A/B Testing**: Track performance metrics and determine winning variants
- **Image Analysis**: Get recommendations based on brightness, contrast, and color variety
- **Optimization Suggestions**: Receive actionable suggestions to improve thumbnails

### Usage

#### Generate Thumbnail Variants

```python
from src.app.services.ai.thumbnail_optimizer import get_thumbnail_optimizer

# Create optimizer instance
optimizer = get_thumbnail_optimizer()

# Generate variants
variants = optimizer.generate_thumbnail_variants(
    base_image_path="path/to/image.jpg",
    metadata={"title": "My Video", "description": "Video description"},
    num_variants=3
)

# variants will contain paths to the generated thumbnails
```

#### Track Performance

```python
# After publishing, track performance metrics
optimizer.track_thumbnail_performance(
    thumbnail_id="thumb_123",
    variant_id="variant_0",
    impressions=1000,
    clicks=50
)
```

#### Get Test Results

```python
# Get A/B test results
results = optimizer.get_test_results(thumbnail_id="thumb_123")

if results.get('winner'):
    winner_id = results['winner'].get('variant_id')
    winner_ctr = results['winner'].get('ctr')
    print(f"Best thumbnail: {winner_id} with {winner_ctr:.2%} CTR")
```

#### Get Optimization Recommendations

```python
recommendations = optimizer.get_optimization_recommendations(
    image_path="path/to/image.jpg",
    metadata={"title": "My Video", "description": "Video description"}
)

# recommendations will contain image analysis and suggestions
```

### API Endpoints

- `POST /thumbnails/generate` - Generate thumbnail variants
- `POST /thumbnails/track` - Track thumbnail performance
- `GET /thumbnails/results/{thumbnail_id}` - Get A/B test results
- `POST /thumbnails/optimize` - Get optimization recommendations

## Cross-Platform Publishing

The Cross-Platform Publishing feature allows videos to be distributed across multiple social media platforms.

### Features

- **Multi-Platform Support**: Publish to YouTube, TikTok, Instagram, and Facebook
- **Format Optimization**: Automatically format videos and metadata for each platform
- **Compatibility Checking**: Verify video compatibility before publishing
- **Cross-Platform Analytics**: Get consolidated metrics across all platforms

### Usage

#### Publish to Multiple Platforms

```python
from src.app.services.social.cross_platform import Platform, get_cross_platform_publisher

# Create publisher instance
publisher = get_cross_platform_publisher()

# Prepare metadata
metadata = {
    "title": "My Video",
    "description": "This is my awesome video",
    "hashtags": ["video", "awesome", "shorts"]
}

# Publish to multiple platforms
results = publisher.publish_video(
    video_path="path/to/video.mp4",
    metadata=metadata,
    platforms=[Platform.YOUTUBE, Platform.TIKTOK, Platform.INSTAGRAM]
)
```

#### Format Metadata for a Specific Platform

```python
# Format metadata for TikTok
tiktok_metadata = publisher.format_metadata_for_platform(
    metadata=metadata,
    platform=Platform.TIKTOK
)
```

#### Get Cross-Platform Analytics

```python
# Get consolidated analytics
analytics = publisher.get_cross_platform_analytics({
    Platform.YOUTUBE: "youtube_video_id",
    Platform.TIKTOK: "tiktok_video_id"
})

if analytics.get('success'):
    print(f"Total views: {analytics.get('total_views')}")
    print(f"Engagement rate: {analytics.get('overall_engagement_rate'):.2%}")
```

### API Endpoints

- `GET /social/platforms` - List all supported platforms
- `POST /social/publish` - Publish to multiple platforms
- `GET /social/analytics/{platform_id}/{video_id}` - Get analytics for a specific platform
- `POST /social/analytics/cross-platform` - Get consolidated analytics

## Content Scheduling and Batch Processing

The Content Scheduler enables efficient management of content creation and publishing at scale.

### Features

- **Task Scheduling**: Schedule videos for future creation and publishing
- **Batch Processing**: Create and process multiple videos in a single operation
- **Optimal Publishing Times**: Get recommended times for maximum engagement
- **Calendar Management**: Organize and track scheduled content

### Usage

#### Schedule Video Publishing

```python
from src.app.services.scheduler import get_content_scheduler

# Create scheduler instance
scheduler = get_content_scheduler()

# Schedule a video for publishing
task_id = scheduler.schedule_video_publishing(
    video_id="video_123",
    platforms=["youtube", "tiktok"],
    scheduled_time=datetime(2025, 5, 15, 15, 30)
)
```

#### Create and Schedule a Batch

```python
# Create a batch of videos
batch_items = [
    {
        "title": "Video 1",
        "description": "First video description",
        "music_id": "music_123",
        "preset": "standard"
    },
    {
        "title": "Video 2",
        "description": "Second video description",
        "music_id": "music_456",
        "preset": "energetic"
    }
]

batch_id = scheduler.create_batch(batch_items)

# Schedule the batch for processing
task_id = scheduler.schedule_batch_processing(
    batch_id=batch_id,
    scheduled_time=datetime(2025, 5, 16, 10, 0)
)
```

#### Get Optimal Publishing Times

```python
# Get optimal times for YouTube
optimal_times = scheduler.get_optimal_publishing_times(
    platform="youtube",
    days_ahead=7
)

for time in optimal_times:
    print(f"Optimal time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
```

#### Get and Filter Scheduled Tasks

```python
# Get all tasks scheduled for the next week
from_date = datetime.now()
to_date = datetime.now() + timedelta(days=7)

tasks = scheduler.get_scheduled_tasks(
    from_date=from_date,
    to_date=to_date,
    task_type="publish_video",
    status="scheduled"
)
```

### API Endpoints

- `GET /scheduler/tasks` - List scheduled tasks
- `POST /scheduler/tasks/video` - Schedule video creation
- `POST /scheduler/tasks/publish` - Schedule video publishing
- `POST /scheduler/batch` - Create a batch of videos
- `POST /scheduler/batch/{batch_id}/schedule` - Schedule batch processing
- `GET /scheduler/optimal-times` - Get optimal publishing times

## Intelligent Music Recommendations

The Music Recommendation system provides AI-powered music suggestions based on video content analysis.

### Features

- **Content-Based Matching**: Analyze video content to find matching music
- **Similar Track Recommendations**: Find tracks similar to ones you already like
- **Trending Music**: Discover currently popular tracks for your videos
- **Video Analysis**: Extract pacing, mood, and energy from video content
- **Batch Recommendations**: Get recommendations for multiple videos at once

### Usage

#### Get Recommendations for a Video

```python
from src.app.services.music.recommendations import get_music_recommendation_service

# Create recommendation service instance
recommender = get_music_recommendation_service()

# Get recommendations for a video
recommendations = recommender.recommend_for_video(
    video_path="/path/to/video.mp4",
    count=5,
    preferred_genres=["Electronic", "Hip Hop"],
    min_bpm=90,
    max_bpm=120
)

# recommendations will contain matching tracks with relevance scores
```

#### Find Similar Tracks

```python
# Find tracks similar to a reference track
similar_tracks = recommender.recommend_similar(
    track_name="electronic_beat.mp3",
    count=5
)

for track in similar_tracks:
    print(f"{track['title']} - Similarity: {track['similarity_score']:.2f}")
```

#### Get Trending Music

```python
# Get currently trending tracks
trending = recommender.recommend_trending(count=5)

for track in trending:
    print(f"#{track['trending_position']} - {track['title']}")
```

### API Endpoints

- `POST /music-recommendations/for-video` - Get recommendations for an existing video
- `POST /music-recommendations/for-uploaded-video` - Upload a video and get recommendations
- `GET /music-recommendations/similar/{track_name}` - Find tracks similar to a reference track
- `GET /music-recommendations/trending` - Get currently trending tracks
- `POST /music-recommendations/batch-recommend` - Get recommendations for multiple videos

## API Reference

For complete API reference, please refer to the API documentation at `/api/docs`.

## Error Handling

All services implement comprehensive error handling with appropriate error codes and messages. In case of errors, check the response status and error message for troubleshooting.

## Extensions and Customizations

These features are designed to be extensible. You can customize or extend them by:

1. Adding new thumbnail styles in `src/app/services/ai/thumbnail_optimizer.py`
2. Supporting new platforms in `src/app/services/social/cross_platform.py`
3. Creating new task types in `src/app/services/scheduler.py`

For more detailed implementation information, see the code documentation in each module. 

## Implementation Updates

All features mentioned in this document are now fully implemented. Recent updates include:

1. **Cross-Platform Publishing**: Completed integration with TikTok, Instagram, and Facebook APIs
2. **Database Integration**: Added proper database functionality for video management
3. **Content Analysis**: Enhanced video content analysis with image classification using TensorFlow and ResNet50
4. **Error Handling**: Improved error handling and logging throughout the application

For a detailed summary of implementation updates, please refer to the `IMPLEMENTATION_UPDATE.md` document. 