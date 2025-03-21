# Debug Mode Fixes

This document outlines the fixes that were applied to resolve issues with the debug mode in the YouTube Shorts Machine application.

## Issues Fixed

1. **Environment Variables**
   - Resolved conflicting settings in `.env` file
   - Standardized `DEV_MODE=true` and `DEBUG_MODE=true`
   - Removed duplicate settings at the end of the file

2. **Templates**
   - Fixed missing `{% endblock %}` tag in `gallery.html` template
   - This resolved the "Unexpected end of template" error

3. **Missing CSS File**
   - Created the missing `video-player.css` file referenced in the gallery template
   - Added proper styling for video player components

4. **Auth Endpoint 404 Error**
   - Added a proxy endpoint for `/auth/authorize` to handle redirects properly
   - This resolved the 404 error when trying to access the auth page

5. **Google Fonts Proxy**
   - Simplified the Google Fonts proxy to use system fonts
   - No longer relies on external requests that might fail
   - Added fallbacks for common font families (Roboto, Open Sans, Montserrat)

6. **Startup Script**
   - Created a `start_debug.sh` script that:
     - Sets environment variables correctly
     - Creates necessary directories
     - Starts both API and UI servers with proper debug flags

## How to Use Debug Mode

To start the application in debug mode:

1. Run the debug script:
   ```bash
   ./start_debug.sh
   ```

2. Access the UI at: http://localhost:8001
   - Debug pages are available at http://localhost:8001/debug/diagnostics
   - Auth bypass is available at http://localhost:8001/auth/dev-bypass

3. API is available at: http://localhost:8000
   - Health check: http://localhost:8000/health
   - Debug status: http://localhost:8000/api/debug/status

## Common Debugging Tools

- Check logs in the terminal where servers are running
- Use the browser's developer console to check for JS errors
- Debug diagnostics page shows environment variables and connection status
- For auth issues, use the dev-bypass endpoint during development 