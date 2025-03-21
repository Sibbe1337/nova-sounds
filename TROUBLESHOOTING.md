# YouTube Shorts Machine - Troubleshooting Guide

This guide provides solutions to common issues you might encounter when using the advanced features of YouTube Shorts Machine.

## Table of Contents

1. [General Troubleshooting](#general-troubleshooting)
2. [Thumbnail Optimization Issues](#thumbnail-optimization-issues)
3. [Cross-Platform Publishing Issues](#cross-platform-publishing-issues)
4. [Content Scheduling and Batch Processing Issues](#content-scheduling-and-batch-processing-issues)
5. [API Integration Issues](#api-integration-issues)

## General Troubleshooting

### Configuration Issues

**Problem**: Configuration settings aren't being recognized.

**Solution**:
1. Verify that your `.env` file is in the project root directory
2. Ensure it contains all necessary configuration parameters
3. Restart the application after making changes to the `.env` file
4. Check logs for any configuration-related errors

### Directory Access Issues

**Problem**: Application fails with permission errors when trying to create or access files.

**Solution**:
1. Verify that the application has write permissions to these directories:
   - `THUMBNAIL_STORAGE_DIR` (default: `/thumbnails`)
   - `SOCIAL_CONFIG_DIR` (default: `src/app/services/social/config`)
   - `SCHEDULER_DATA_DIR` (default: `src/app/services/data`)
2. Run the following command to ensure directories exist with proper permissions:
   ```bash
   mkdir -p thumbnails src/app/services/social/config src/app/services/data/batches
   chmod -R 755 thumbnails src/app/services/social/config src/app/services/data
   ```

### Logging Issues

**Problem**: Not seeing detailed logs to diagnose problems.

**Solution**:
1. Enable debug mode in `.env`:
   ```
   DEBUG_MODE=true
   ```
2. Check logs in the console or in the `logs/` directory
3. Increase logging verbosity in `src/app/core/settings.py` if needed

## Thumbnail Optimization Issues

### Image Processing Errors

**Problem**: Thumbnail generation fails with image processing errors.

**Solution**:
1. Verify that Pillow is installed correctly:
   ```bash
   pip install Pillow==9.4.0
   ```
2. Check that the input image is a valid format (JPEG, PNG)
3. Verify the image isn't corrupted by opening it with another program
4. Try with a different image to isolate the problem

### Missing Thumbnail Variants

**Problem**: `generate_thumbnail_variants` returns empty list or fewer variants than requested.

**Solution**:
1. Verify that `THUMBNAIL_STORAGE_DIR` exists and is writable
2. Check the error logs for specific error messages
3. Make sure enough disk space is available
4. Try with a smaller input image (< 5MB)
5. Reduce the number of requested variants (set `num_variants=2`)

### A/B Testing Issues

**Problem**: Test results aren't showing a clear winner or statistical significance.

**Solution**:
1. Ensure you have enough data (at least 100 impressions per variant)
2. Verify that tracking calls are being made with correct data:
   ```python
   optimizer.track_thumbnail_performance(
       thumbnail_id="thumb_id", 
       variant_id="variant_id",
       impressions=impressions,  # Must be > 0
       clicks=clicks             # Must be >= 0 and <= impressions
   )
   ```
3. Allow more time for data collection before checking results
4. Check that you're using the same `thumbnail_id` for tracking and retrieving results

## Cross-Platform Publishing Issues

### Authentication Failures

**Problem**: Unable to authenticate with social media platforms.

**Solution**:
1. Verify that authentication tokens are valid and not expired
2. Check that the correct permissions are requested during authentication:
   - TikTok: `video.upload`, `video.list`
   - Instagram: `instagram_content_publish`, `instagram_manage_insights`
   - Facebook: `pages_read_engagement`, `pages_manage_posts`
3. Ensure tokens are properly stored in the configuration directory
4. Try refreshing tokens through the platform's developer console

### Video Format Compatibility

**Problem**: Videos are rejected by platforms due to format incompatibility.

**Solution**:
1. Ensure videos meet the platform requirements:

   | Platform | Aspect Ratio | Duration (sec) | Format | Max Size |
   |----------|--------------|----------------|--------|----------|
   | YouTube Shorts | 9:16 | 15-60 | MP4, MOV | 256MB |
   | TikTok | 9:16 | 5-180 | MP4, MOV | 128MB |
   | Instagram Reels | 9:16, 4:5 | 3-90 | MP4 | 100MB |
   | Facebook Reels | 9:16, 16:9, 1:1 | 3-120 | MP4 | 256MB |

2. Use the video compatibility check before attempting to publish:
   ```python
   from src.app.services.social.cross_platform import Platform, VideoFormat
   
   is_compatible, issues = VideoFormat.is_compatible(video_metadata, Platform.TIKTOK)
   if not is_compatible:
       print(f"Compatibility issues: {issues}")
   ```

3. Try reformatting the video with the built-in formatter:
   ```python
   formatted_video = publisher.format_video_for_platform(video_path, Platform.TIKTOK)
   ```

### Missing Videos on Platforms

**Problem**: Videos show as successfully published but don't appear on the platform.

**Solution**:
1. Check platform-specific status and error codes in the response
2. Verify the video hasn't been flagged for content policy violations
3. Allow extra time for processing (some platforms have delays)
4. Check platform-specific developer dashboards for status
5. Verify that the authenticated account has the necessary permissions

## Content Scheduling and Batch Processing Issues

### Tasks Not Executing

**Problem**: Scheduled tasks aren't running at the designated time.

**Solution**:
1. Verify that the scheduler process is running:
   ```bash
   ps aux | grep scheduler
   ```
2. Check that scheduled times are in the future and in the correct timezone
3. Examine the scheduler logs for errors:
   ```bash
   tail -f logs/scheduler.log
   ```
4. Try restarting the scheduler service
5. Verify that the `schedule.json` file in the data directory is not corrupted

### Batch Processing Failures

**Problem**: Batch processing fails or gets stuck.

**Solution**:
1. Check batch status with the API:
   ```bash
   curl "http://localhost:8000/scheduler/batch/{batch_id}"
   ```
2. Verify that the batch items have valid parameters
3. Try processing a smaller batch to isolate problematic items
4. Check system resources (memory, CPU) during batch processing
5. Increase the task processing timeout if needed

### Invalid Task Errors

**Problem**: Errors when creating tasks like "invalid task data" or "task validation failed".

**Solution**:
1. Ensure all required fields are present in task data
2. Check JSON format for any syntax errors
3. Verify that date formats follow ISO 8601 (YYYY-MM-DDTHH:MM:SS)
4. Ensure all referenced resources (videos, platforms) exist
5. Check for duplicate task IDs if manually specifying them

## API Integration Issues

### API Connection Issues

**Problem**: Unable to connect to the API endpoints.

**Solution**:
1. Verify the API server is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check for firewall or network issues
3. Verify CORS settings if accessing from browser applications
4. Check API logs for connection-related errors
5. Ensure the correct host and port are configured

### API Authentication Issues

**Problem**: Receiving 401 Unauthorized errors from API endpoints.

**Solution**:
1. Check that authentication tokens are valid and not expired
2. Verify that the token has the required scopes
3. Include proper authentication headers in all requests
4. Try refreshing the token if it's expired
5. Check server logs for detailed authentication errors

### Request Format Issues

**Problem**: API returns 400 Bad Request or 422 Unprocessable Entity errors.

**Solution**:
1. Verify that request content type is correct:
   - For JSON data: `Content-Type: application/json`
   - For form data: `Content-Type: multipart/form-data`
2. Check request body format against the API documentation
3. Ensure all required fields are present and correctly formatted
4. Pay attention to field types (strings vs. numbers vs. booleans)
5. Check for special characters or encoding issues in text fields

## Performance Optimization

If you experience performance issues with any of the advanced features, consider these optimizations:

### Thumbnail Optimization Performance

1. Reduce the number of generated variants (2-3 is usually sufficient)
2. Use smaller base images (1280x720 is recommended)
3. Limit concurrent generation requests
4. Implement client-side caching for generated thumbnails

### Cross-Platform Publishing Performance

1. Prepare and validate videos before publishing to avoid failed uploads
2. When publishing to multiple platforms, use parallel processing
3. Optimize video formats offline before uploading
4. Implement retry logic with exponential backoff for API failures

### Scheduler Performance

1. Distribute scheduled tasks evenly across time periods
2. Limit batch sizes to 10-20 items per batch
3. Schedule resource-intensive tasks during off-peak hours
4. Implement a cleanup process for completed or failed tasks

## Getting Help

If the above solutions don't address your issue:

1. Check the GitHub repository issues section
2. Consult the documentation in the `docs/` directory
3. Review the API documentation at `/api/docs`
4. Examine the application logs for detailed error messages
5. Consider filing a bug report with detailed reproduction steps

For feature requests or enhancement suggestions, please use the GitHub repository's issue tracker. 