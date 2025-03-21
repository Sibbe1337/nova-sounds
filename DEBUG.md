# YouTube Shorts Machine - Debugging Guide

This guide provides detailed instructions for debugging and verifying the three new features in the YouTube Shorts Machine application.

## Development Environment

### Environment Variables

The application supports two special modes:

- **DEBUG_MODE**: Enables additional logging and diagnostic features
- **DEV_MODE**: Enables development shortcuts and bypasses (like auth)

To enable these modes, set the environment variables before running the app:

```bash
export DEBUG_MODE=true
export DEV_MODE=true
python start.py
```

### Debug Diagnostics Page

When DEBUG_MODE is enabled, you can access a comprehensive diagnostics page at:

```
http://localhost:8002/debug/diagnostics
```

This page shows system information, environment variables, API status, and network connectivity tests.

## Development Authentication Bypass

When developing or testing the YouTube upload features, you can bypass YouTube authentication using:

```
http://localhost:8002/auth/dev-bypass
```

This will set a temporary authentication cookie that lets you access the YouTube upload page without real YouTube credentials.

## Testing the New Features

### Automated Testing

Use the included debug script to test all features:

```bash
python debug_test.py
```

Options:
- `--port PORT`: Specify the API port manually (default: auto-detect)
- `--only FEATURE`: Test only one feature (thumbnails, social, scheduler)

Example:
```bash
python debug_test.py --only thumbnails
```

### 1. Thumbnail Optimization

#### API Endpoints

- **List Service Info**: `GET /thumbnails`
- **Generate Variants**: `POST /thumbnails/generate-variants`
- **View Thumbnail**: `GET /thumbnails/{thumbnail_id}/view`
- **Analyze Thumbnail**: `POST /thumbnails/{thumbnail_id}/analyze`
- **Start A/B Test**: `POST /thumbnails/start-ab-test`
- **Get Test Results**: `GET /thumbnails/ab-test/{test_id}/results`
- **Select Winner**: `POST /thumbnails/{thumbnail_id}/select-winner`
- **Track Performance**: `POST /thumbnails/track`
- **Get Recommendations**: `POST /thumbnails/optimize`

#### Manual Testing

1. Access the YouTube upload page using the dev bypass:
   ```
   http://localhost:8002/auth/dev-bypass
   ```

2. Scroll down to the "Thumbnail Optimization" section
3. Upload an image to use as a thumbnail
4. Generate variants
5. Start an A/B test and view results

#### Common Issues

- **404 Not Found**: Check if thumbnails router is properly registered in `src/app/api/__init__.py`
- **500 Server Error**: Verify THUMBNAIL_STORAGE_DIR exists and is writable
- **UI Not Showing**: Check browser console for JavaScript errors

### 2. Cross-Platform Publishing

#### API Endpoints

- **List Platforms**: `GET /social/platforms`
- **Get Auth Status**: `GET /social/auth-status`
- **Authenticate Platform**: `POST /social/auth/{platform}`
- **Auth Callback**: `POST /social/auth/{platform}/callback`
- **Save Settings**: `POST /social/settings`
- **Publish Content**: `POST /social/publish`
- **Get Publishing Status**: `GET /social/publish/{job_id}`

#### Manual Testing

1. Access the YouTube upload page
2. Scroll to the "Cross-Platform Publishing" section
3. Select platforms (YouTube, TikTok, Instagram, Facebook)
4. Configure platform-specific settings
5. Save settings and initiate publishing

#### Common Issues

- **Authentication Errors**: Use dev bypass for testing without real platform credentials
- **Missing Platforms**: Check if all platforms are registered in `social.py`
- **UI Issues**: Verify CSS and JavaScript are loading correctly

### 3. Content Scheduling

#### API Endpoints

- **Get Schedules**: `GET /scheduler/schedules`
- **Create Schedule**: `POST /scheduler/schedules`
- **Delete Schedule**: `DELETE /scheduler/schedules/{schedule_id}`
- **Get Optimal Times**: `GET /scheduler/optimal-times`
- **Get Batches**: `GET /scheduler/batches`
- **Create Batch**: `POST /scheduler/batches`
- **Get Batch Details**: `GET /scheduler/batches/{batch_id}`
- **Get Trending Data**: `GET /trends`
- **Get Optimal Posting Times**: `GET /trends/optimal-times`

#### Manual Testing

1. Access the YouTube upload page
2. Scroll to the "Content Scheduling" section
3. Select scheduling type (now, scheduled, optimal time)
4. For optimal time, fetch recommendations and select a time
5. Create a schedule

#### Common Issues

- **Missing Endpoints**: Ensure trends and scheduler routers are properly registered
- **Data Not Loading**: Check network requests for API errors
- **UI Not Responsive**: Verify JavaScript event handlers are attached correctly

## Proxy Troubleshooting

The UI server proxies API requests. If you're having connection issues:

1. Verify both UI and API servers are running:
   ```bash
   ps aux | grep uvicorn
   ```

2. Check API port configuration in `src/app/core/port_finder.py`

3. Verify proxy handling in `src/ui/proxy.py`

4. Check for these common patterns in browser console errors:
   - "Failed to fetch": API server not running or wrong port
   - "CORS error": CORS middleware not configured correctly
   - "404 Not Found": Endpoint doesn't exist or proxy is misconfigured

## Log Locations

- **Server Logs**: Displayed in terminal when running the servers
- **JavaScript Errors**: Browser developer console
- **Debug Info**: `/debug/diagnostics` when DEBUG_MODE is enabled

## Common Commands

```bash
# Start with debug mode
DEBUG_MODE=true DEV_MODE=true python start.py

# Run debug tests
python debug_test.py

# Check running servers
ps aux | grep uvicorn

# Test API endpoint
curl http://localhost:8000/health

# Access dev bypass
curl -v http://localhost:8002/auth/dev-bypass

# View log file (if configured)
tail -f app.log
```

---

For any additional help or questions, please refer to the full documentation or IMPLEMENTATION_SUMMARY.md file. 