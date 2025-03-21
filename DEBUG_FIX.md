# Debug and Fix Scripts for YouTube Shorts Machine

This document provides instructions for debugging and fixing common issues with the YouTube Shorts Machine application.

## Quick Fix

For an automated solution to common issues, run:

```bash
python debug_and_fix.py
```

This script will:
1. Fix UI indentation errors
2. Fix StatReload continuous reloading issues
3. Fix Runway ML API key loading problems
4. Restart the servers

## Individual Fix Scripts

If you prefer to address issues individually:

### 1. UI Indentation Errors

Fixes the indentation error in the UI module that's causing the server startup to fail:

```bash
python debug_ui_fix.py
```

### 2. StatReload Continuous Detection

Fixes the issue with StatReload repeatedly detecting changes in debug_features.py:

```bash
python fix_reload_issue.py
```

### 3. Runway ML API Key Loading

Fixes the API key loading issue despite it being present in the .env file:

```bash
python fix_api_key.py
```

## Manual Fixes

If the automated scripts don't solve the problem, you can try these manual fixes:

### UI Indentation Error

1. Open `src/ui/main.py`
2. Look for indentation issues around line 949 (search for `@app.post("/proxy/suggest"`)
3. Fix the indentation to match the surrounding code

### StatReload Issues

1. Edit `start.py` or `start_servers.py`
2. Find the uvicorn.run() call
3. Add the reload_excludes parameter:
   ```python
   uvicorn.run(
       "src.ui.main:app",
       host="0.0.0.0",
       port=8001,
       reload=True,
       reload_excludes=["*.bak", "debug_features.py"],
   )
   ```

### API Key Loading

1. Check if the RUNWAY_API_KEY is properly set in the .env file
2. Find where it's loaded in the code (search for 'RUNWAY_API_KEY')
3. Ensure it's loaded with a default value:
   ```python
   os.environ.get('RUNWAY_API_KEY', '')
   ```
   instead of:
   ```python
   os.environ['RUNWAY_API_KEY']
   ```

## Troubleshooting

If you continue to experience issues:

1. **Check logs**: Look in the `logs/` directory for detailed error messages
2. **Verify environment**: Make sure all required environment variables are set in `.env`
3. **Restart from scratch**: Stop all running servers, then start them again:
   ```bash
   python start.py
   ```
   or
   ```bash
   python start_servers.py
   ```

## Debugging Information

When DEBUG_MODE is set to true in the .env file (as it currently is), you can:

1. Use the debug_features.py script to test the three main features
2. Check detailed logging output
3. Access debug endpoints and tools

For detailed debugging of specific features, use:
- `python debug.py` - General debugging
- `python debug_api.py` - API-specific debugging
- `python debug_ui.py` - UI-specific debugging 