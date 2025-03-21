# YouTube Shorts Machine - Quick Start Guide

This guide will help you get started with the advanced features of YouTube Shorts Machine.

## Prerequisites

- Python 3.9 or higher
- YouTube Shorts Machine installed and configured
- For social media publishing: API credentials for respective platforms

## Installation

If you haven't set up YouTube Shorts Machine yet, follow the instructions in the main README.md file.

## Feature Quick Start

### 1. Thumbnail Optimization

#### Step 1: Generate Thumbnail Variants

```bash
# Using the API
curl -X POST "http://localhost:8000/thumbnails/generate" \
  -F "image=@path/to/image.jpg" \
  -F "title=My Awesome Video" \
  -F "description=This is a great video" \
  -F "num_variants=3"
```

**Response:**
```json
{
  "success": true,
  "thumbnail_id": "thumb_1234567890",
  "variants": [
    {
      "variant_id": "variant_0",
      "path": "/path/to/thumbnail_variant_0.jpg",
      "url": "/thumbnails/variant/thumbnail_variant_0.jpg"
    },
    {
      "variant_id": "variant_1",
      "path": "/path/to/thumbnail_variant_1.jpg",
      "url": "/thumbnails/variant/thumbnail_variant_1.jpg"
    },
    {
      "variant_id": "variant_2",
      "path": "/path/to/thumbnail_variant_2.jpg",
      "url": "/thumbnails/variant/thumbnail_variant_2.jpg"
    }
  ]
}
```

#### Step 2: Use the Variants in Your Videos

Upload the different thumbnail variants to your videos. You can use the same video content with different thumbnails to test which performs better.

#### Step 3: Track Performance and Get Results

After your videos have been published for a while, track the performance:

```bash
# Track performance for a variant
curl -X POST "http://localhost:8000/thumbnails/track" \
  -H "Content-Type: application/json" \
  -d '{
    "thumbnail_id": "thumb_1234567890",
    "variant_id": "variant_0",
    "impressions": 1000,
    "clicks": 50
  }'
```

Then get the test results:

```bash
# Get test results
curl "http://localhost:8000/thumbnails/results/thumb_1234567890"
```

**Response:**
```json
{
  "status": "success",
  "test_id": "thumb_1234567890",
  "variants": {
    "variant_0": {
      "impressions": 1000,
      "clicks": 50,
      "ctr": 0.05
    },
    "variant_1": {
      "impressions": 1000,
      "clicks": 70,
      "ctr": 0.07
    },
    "variant_2": {
      "impressions": 1000,
      "clicks": 60,
      "ctr": 0.06
    }
  },
  "winner": {
    "variant_id": "variant_1",
    "ctr": 0.07
  }
}
```

### 2. Cross-Platform Publishing

#### Step 1: Authenticate with Platforms

First, authenticate with each platform you want to publish to:

```bash
# Authenticate with TikTok
curl -X POST "http://localhost:8000/social/platforms/tiktok/auth" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your_tiktok_access_token",
    "refresh_token": "your_tiktok_refresh_token",
    "expires_at": "2025-12-31T23:59:59"
  }'
```

Repeat this process for Instagram and Facebook with their respective credentials.

#### Step 2: Publish to Multiple Platforms

```bash
# Publish a video to multiple platforms
curl -X POST "http://localhost:8000/social/publish" \
  -F "video_path=/path/to/video.mp4" \
  -F "title=My Awesome Video" \
  -F "description=This is a great video" \
  -F "platforms=youtube,tiktok,instagram" \
  -F "hashtags=video,awesome,shorts"
```

**Response:**
```json
{
  "success": true,
  "video_path": "/path/to/video.mp4",
  "platforms": {
    "youtube": {
      "success": true,
      "video_id": "yt_1234567890",
      "url": "https://youtube.com/watch?v=1234567890"
    },
    "tiktok": {
      "success": true,
      "video_id": "tt_1234567890",
      "url": "https://tiktok.com/@user/video/1234567890"
    },
    "instagram": {
      "success": true,
      "media_id": "ig_1234567890",
      "permalink": "https://instagram.com/p/1234567890"
    }
  }
}
```

#### Step 3: Get Cross-Platform Analytics

```bash
# Get analytics across all platforms
curl -X POST "http://localhost:8000/social/analytics/cross-platform" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube": "yt_1234567890",
    "tiktok": "tt_1234567890",
    "instagram": "ig_1234567890"
  }'
```

**Response:**
```json
{
  "success": true,
  "total_views": 5000,
  "total_engagement": 750,
  "overall_engagement_rate": 0.15,
  "platforms": {
    "youtube": {
      "metrics": {
        "views": 2000,
        "likes": 150,
        "comments": 50,
        "shares": 30
      }
    },
    "tiktok": {
      "metrics": {
        "views": 2500,
        "likes": 300,
        "comments": 100,
        "shares": 70
      }
    },
    "instagram": {
      "metrics": {
        "views": 500,
        "likes": 40,
        "comments": 10,
        "shares": 0
      }
    }
  }
}
```

### 3. Content Scheduling and Batch Processing

#### Step 1: Get Optimal Publishing Times

```bash
# Get optimal times for YouTube
curl "http://localhost:8000/scheduler/optimal-times?platform=youtube&days_ahead=3"
```

**Response:**
```json
{
  "platform": "youtube",
  "days_ahead": 3,
  "optimal_times": [
    "2025-03-15T15:30:00",
    "2025-03-15T19:00:00",
    "2025-03-16T10:30:00",
    "2025-03-16T20:00:00",
    "2025-03-17T15:30:00",
    "2025-03-17T19:00:00"
  ],
  "count": 6
}
```

#### Step 2: Schedule a Video for Publishing

```bash
# Schedule a video for publishing
curl -X POST "http://localhost:8000/scheduler/tasks/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "platforms": ["youtube", "tiktok"],
    "scheduled_time": "2025-03-15T15:30:00"
  }'
```

**Response:**
```json
{
  "success": true,
  "task_id": "12345678-1234-1234-1234-123456789012",
  "scheduled_time": "2025-03-15T15:30:00",
  "video_id": "video_123",
  "platforms": ["youtube", "tiktok"]
}
```

#### Step 3: Create a Batch of Videos

```bash
# Create a batch of videos
curl -X POST "http://localhost:8000/scheduler/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_items": [
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
  }'
```

**Response:**
```json
{
  "success": true,
  "batch_id": "98765432-9876-9876-9876-987654321098",
  "item_count": 2,
  "created_at": "2025-03-14T10:00:00"
}
```

#### Step 4: Schedule the Batch for Processing

```bash
# Schedule the batch for processing
curl -X POST "http://localhost:8000/scheduler/batch/98765432-9876-9876-9876-987654321098/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_time": "2025-03-15T10:00:00"
  }'
```

**Response:**
```json
{
  "success": true,
  "task_id": "87654321-8765-8765-8765-876543210987",
  "batch_id": "98765432-9876-9876-9876-987654321098",
  "scheduled_time": "2025-03-15T10:00:00"
}
```

#### Step 5: View Scheduled Tasks

```bash
# View all scheduled tasks
curl "http://localhost:8000/scheduler/tasks"
```

**Response:**
```json
{
  "tasks": [
    {
      "id": "12345678-1234-1234-1234-123456789012",
      "type": "publish_video",
      "status": "scheduled",
      "scheduled_time": "2025-03-15T15:30:00",
      "video_id": "video_123",
      "platforms": ["youtube", "tiktok"]
    },
    {
      "id": "87654321-8765-8765-8765-876543210987",
      "type": "batch_process",
      "status": "scheduled",
      "scheduled_time": "2025-03-15T10:00:00",
      "batch_id": "98765432-9876-9876-9876-987654321098"
    }
  ],
  "count": 2
}
```

## Programmatic Usage (Python)

### Thumbnail Optimization

```python
from src.app.services.ai.thumbnail_optimizer import get_thumbnail_optimizer

# Create optimizer instance
optimizer = get_thumbnail_optimizer()

# Generate thumbnail variants
variants = optimizer.generate_thumbnail_variants(
    base_image_path="path/to/image.jpg",
    metadata={"title": "My Video", "description": "Description"},
    num_variants=3
)

# Track performance after publishing
optimizer.track_thumbnail_performance(
    thumbnail_id="thumb_123",
    variant_id="variant_0",
    impressions=1000,
    clicks=50
)

# Get results
results = optimizer.get_test_results("thumb_123")
print(f"Best thumbnail: {results['winner']['variant_id']}")
```

### Cross-Platform Publishing

```python
from src.app.services.social.cross_platform import Platform, get_cross_platform_publisher

# Create publisher instance
publisher = get_cross_platform_publisher()

# Publish to multiple platforms
results = publisher.publish_video(
    video_path="path/to/video.mp4",
    metadata={
        "title": "My Video",
        "description": "Description",
        "hashtags": ["video", "shorts"]
    },
    platforms=[Platform.YOUTUBE, Platform.TIKTOK]
)

# Get analytics
analytics = publisher.get_cross_platform_analytics({
    Platform.YOUTUBE: "yt_12345",
    Platform.TIKTOK: "tt_67890"
})
```

### Content Scheduling

```python
from datetime import datetime, timedelta
from src.app.services.scheduler import get_content_scheduler

# Create scheduler instance
scheduler = get_content_scheduler()

# Get optimal times
optimal_times = scheduler.get_optimal_publishing_times("youtube", 7)

# Schedule video publishing
task_id = scheduler.schedule_video_publishing(
    video_id="video_123",
    platforms=["youtube", "tiktok"],
    scheduled_time=optimal_times[0]
)

# Create and schedule a batch
batch_id = scheduler.create_batch([
    {"title": "Video 1", "description": "Description 1"},
    {"title": "Video 2", "description": "Description 2"}
])

batch_task_id = scheduler.schedule_batch_processing(
    batch_id=batch_id,
    scheduled_time=datetime.now() + timedelta(days=1)
)
```

## Troubleshooting

### Video Format Issues

If you encounter video format compatibility issues when publishing to different platforms, make sure your video meets the platform requirements:

- **YouTube Shorts**: 9:16 aspect ratio, 15-60 seconds
- **TikTok**: 9:16 aspect ratio, 5-180 seconds
- **Instagram Reels**: 9:16 aspect ratio, 3-90 seconds
- **Facebook Reels**: 9:16 aspect ratio, 3-120 seconds

### Authentication Errors

If you get authentication errors for social media platforms:

1. Check that your API credentials are valid and not expired
2. Ensure you have the correct permissions for video publishing
3. Refresh tokens if necessary through the respective platform developer console

### Scheduling Issues

If scheduled tasks aren't executing:

1. Check that the scheduler service is running
2. Verify the scheduled time is in the future
3. Check the log files for any errors during task execution

## Next Steps

For more detailed information about these features, refer to:

1. [FEATURES.md](FEATURES.md) - Comprehensive feature documentation
2. [API.md](API.md) - Complete API reference
3. Individual module documentation in the source code

You can also explore the test scripts in the repository to see more usage examples. 