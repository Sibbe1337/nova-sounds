# Testing WebSocket Real-Time Updates

This document explains how to test the real-time WebSocket implementation for the Analytics Dashboard.

## Prerequisites

1. Make sure the application server is running in development mode:
   ```bash
   export DEV_MODE=true
   python src/ui/main.py
   ```

2. Ensure you have the required Python dependencies:
   ```bash
   pip install httpx
   ```

## Testing With the Script

We've created a testing script `test_websocket.py` that sends simulated analytics updates to the server, which are then broadcast to all connected WebSocket clients.

### Basic Usage

To run the test with default settings (10 dashboard updates, 5 seconds apart):

```bash
./test_websocket.py
```

### Advanced Options

You can customize the test behavior with these options:

```bash
# Send 20 dashboard updates, 3 seconds apart
./test_websocket.py --count 20 --interval 3

# Send recent updates instead of dashboard updates
./test_websocket.py --type recent

# Send both dashboard and recent updates (alternating)
./test_websocket.py --type all

# Send indefinite updates (until Ctrl+C is pressed)
./test_websocket.py --count 0

# Connect to a different server
./test_websocket.py --server http://other-server:8001
```

## Manual Testing

1. Open the Analytics Dashboard in your browser
2. Open the browser's developer tools (F12 or right-click -> Inspect)
3. Look for "Connected to analytics WebSocket server" in the console
4. Run the test script as described above
5. You should see:
   - Connection status indicator showing "Live"
   - Toast notifications when new data arrives
   - Real-time updates to charts and metrics
   - "Received dashboard update" messages in the console

## Troubleshooting

If the real-time updates aren't working:

1. **Check server logs**: Make sure the server is receiving and broadcasting the updates
2. **Check browser console**: Look for any errors related to WebSocket connections
3. **Verify development mode**: The test endpoint only works when `DEV_MODE=true`
4. **Test connection**: The connection status indicator should show "Live" if connected properly
5. **Network tab**: In browser dev tools, check the WS connection in the Network tab

## Expected Behavior

When working correctly, you should see:

1. A "Live" connection status indicator in the top-right of the dashboard
2. Toast notifications when new data arrives
3. Charts and metrics that update automatically without page refresh
4. Connection will automatically reconnect if interrupted

If your connection drops, the status will change to "Offline" and the system will automatically attempt to reconnect, with exponential backoff between attempts. 