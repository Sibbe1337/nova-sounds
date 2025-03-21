"""
UI server for YouTube Shorts Machine.
"""
import os
import httpx
import logging
import json
import random
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.ui.auth import check_api_available
from src.ui.debug import router as debug_router, log_request
# Import the UI documentation router
from src.ui.routes.ui_docs import router as ui_docs_router

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="YouTube Shorts Machine UI")

# Add request logging middleware in development mode
if os.environ.get("DEV_MODE", "false").lower() == "true":
    app.add_middleware(BaseHTTPMiddleware, dispatch=log_request)

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# For development only - serve mock media files
if os.environ.get("DEV_MODE", "false").lower() == "true":
    try:
        if os.path.exists("mock-media"):
            app.mount("/mock-media", StaticFiles(directory="mock-media"), name="mock-media")
    except Exception as e:
        logger.error(f"Error mounting mock-media directory: {e}")

# Create necessary directories if they don't exist
os.makedirs("src/ui/static/js", exist_ok=True)
os.makedirs("src/ui/static/css", exist_ok=True)
os.makedirs("media", exist_ok=True)
os.makedirs("mock-media", exist_ok=True)

# Helper function for making API requests
async def make_api_request(request, method, path, data=None, params=None, timeout=10.0):
    """
    Make a request to the API server.
    
    Args:
        request: FastAPI request object
        method: HTTP method (GET, POST, etc.)
        path: API path (starting with /)
        data: Request body for POST/PUT requests
        params: Query parameters
        timeout: Request timeout in seconds
        
    Returns:
        httpx.Response: API response
    """
    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method.upper() == "GET":
            return await client.get(f"{api_url}{path}", params=params)
        elif method.upper() == "POST":
            return await client.post(f"{api_url}{path}", json=data, params=params)
        elif method.upper() == "PUT":
            return await client.put(f"{api_url}{path}", json=data, params=params)
        elif method.upper() == "DELETE":
            return await client.delete(f"{api_url}{path}", params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    @property
    def has_connections(self) -> bool:
        """Check if there are any active connections."""
        return len(self.active_connections) > 0

# Create connection manager
manager = ConnectionManager()

# Flag to track if the background task is running
background_task_running = False

# API URL (use environment variable or default)
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Include routers
if os.environ.get("DEV_MODE", "false").lower() == "true":
    app.include_router(debug_router, prefix="/api", tags=["debug"])
    # Include UI docs router in development mode
    app.include_router(ui_docs_router)

# Add explicit proxy for auth/authorize endpoint
@app.get("/auth/authorize", response_class=JSONResponse)
async def auth_authorize_proxy():
    """
    Proxy endpoint for /auth/authorize to handle API path correctly.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/auth/authorize")
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying auth/authorize: {e}")
        return JSONResponse(
            content={"error": "Authentication service unavailable"},
            status_code=503
        )

@app.get("/auth/status", response_class=JSONResponse)
async def auth_status_proxy():
    """
    Proxy endpoint for /auth/status to handle API path correctly.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/auth/status")
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying auth/status: {e}")
        return JSONResponse(
            content={"authenticated": False, "error": "Authentication service unavailable"},
            status_code=503
        )

@app.on_event("startup")
async def startup_event():
    """
    Executed when the UI server starts up.
    """
    # Configure the template directory
    templates.env.globals["format_date"] = lambda date_str: date_str.split('T')[0] if date_str else ""
    
    # Store startup time for the debug console
    app.state.startup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info("UI server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the app shuts down."""
    global background_task_running
    background_task_running = False
    logger.info("Shutting down background tasks")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, page: int = 1, tracks_per_page: int = 20, search: str = None):
    """
    Redirect to the landing page.
    
    Args:
        request: Request object
        page: Current page number for pagination
        tracks_per_page: Number of tracks to show per page
        search: Optional search term to filter tracks
        
    Returns:
        RedirectResponse: Redirect to landing page
    """
    # For existing users or if skip_landing query param is present, show the app
    if request.cookies.get('returning_user') or request.query_params.get('skip_landing'):
        return await app_index(request, page, tracks_per_page, search)
    
    # Otherwise, redirect to landing page
    return RedirectResponse(url="/landing")

@app.get("/app", response_class=HTMLResponse)
async def app_index(request: Request, page: int = 1, tracks_per_page: int = 20, search: str = None):
    """
    Render the main app page.
    
    Args:
        request: Request object
        page: Current page number for pagination
        tracks_per_page: Number of tracks to show per page
        search: Optional search term to filter tracks
        
    Returns:
        TemplateResponse: Rendered index.html
    """
    api_available = check_api_available()
    
    # Get authentication status
    authenticated = False
    if api_available:
        try:
            auth_response = httpx.get(f"{API_URL}/auth/status")
            if auth_response.status_code == 200:
                authenticated = auth_response.json().get("authenticated", False)
        except Exception as e:
            logger.error(f"Error checking auth status: {e}")
    
    # Get music tracks with pagination
    tracks = []
    total_tracks = 0
    has_more = False
    
    if api_available:
        try:
            # Calculate skip for pagination
            skip = (page - 1) * tracks_per_page
            
            # Build query parameters
            params = {
                'limit': tracks_per_page,
                'skip': skip,
                'include_images': 'true'
            }
            
            # Add search prefix if provided
            if search:
                params['prefix'] = search
            
            # Request tracks with pagination
            music_response = httpx.get(f"{API_URL}/music", params=params)
            
            if music_response.status_code == 200:
                response_data = music_response.json()
                tracks_data = response_data.get("tracks", [])
                total_tracks = response_data.get("total", 0)
                has_more = skip + len(tracks_data) < total_tracks
                
                # Process track data for display
                for track in tracks_data:
                    # Generate track ID from name if not present
                    if "id" not in track:
                        track["id"] = track.get("track_name", "").replace(".", "_")
                    
                    # Ensure track has an image URL
                    if "image_url" not in track:
                        # Generate mock image URL
                        track["image_url"] = f"/mock-media/covers/{track.get('track_name', 'default')}.jpg"
                    
                    # Get waveform data for visualization
                    try:
                        waveform_response = httpx.get(f"{API_URL}/music/{track.get('track_name')}/waveform")
                        if waveform_response.status_code == 200:
                            waveform_data = waveform_response.json().get("data", [])
                            track["waveform_data"] = waveform_data
                        else:
                            # Generate mock waveform data if not available
                            import random
                            track["waveform_data"] = [random.uniform(0.2, 1.0) for _ in range(64)]
                    except Exception as e:
                        logger.warning(f"Error getting waveform data: {e}")
                        # Generate mock waveform data
                        import random
                        track["waveform_data"] = [random.uniform(0.2, 1.0) for _ in range(64)]
                
                tracks = tracks_data
                logger.info(f"Fetched {len(tracks)} tracks from API (page {page}, total {total_tracks})")
        except Exception as e:
            logger.error(f"Error fetching music tracks: {e}")
    
    # Calculate pagination details
    total_pages = (total_tracks + tracks_per_page - 1) // tracks_per_page
    
    # Determine if we're in dev mode
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    
    # Set cookie to mark returning user
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tracks": tracks,
            "api_available": api_available,
            "authenticated": authenticated,
            "dev_mode": dev_mode,
            "page": page,
            "total_pages": total_pages,
            "has_more": has_more,
            "total_tracks": total_tracks,
            "tracks_per_page": tracks_per_page,
            "search": search
        }
    )
    
    # Set cookie to mark returning user (expires in 30 days)
    response.set_cookie(key="returning_user", value="true", max_age=60*60*24*30)
    
    return response

@app.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request):
    """
    Render the landing page.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: Rendered landing.html
    """
    # Determine if we're in dev mode
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "dev_mode": dev_mode
        }
    )

@app.get("/auth", response_class=HTMLResponse)
async def auth(request: Request):
    """
    Handle authentication.
    
    Args:
        request: Request object
        
    Returns:
        RedirectResponse: Redirect to authentication URL
    """
    api_available = check_api_available()
    
    if not api_available:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "API server is not available. Please try again later."
            }
        )
    
    try:
        # Get auth URL from API
        response = httpx.get(f"{API_URL}/auth/authorize")
        
        if response.status_code == 200:
            auth_url = response.json().get("auth_url")
            return RedirectResponse(url=auth_url)
        else:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "message": f"Error initiating authentication: {response.text}"
                }
            )
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": f"Error during authentication: {str(e)}"
            }
        )

@app.get("/auth/success", response_class=HTMLResponse)
async def auth_success(request: Request):
    """
    Handle successful authentication.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: Success page
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "success_message": "Authentication successful! You can now create videos.",
            "authenticated": True
        }
    )

@app.get("/status/{video_id}", response_class=HTMLResponse)
async def status(request: Request, video_id: str):
    """
    Show video status.
    
    Args:
        request: Request object
        video_id: Video ID
        
    Returns:
        TemplateResponse: Status page
    """
    api_available = check_api_available()
    
    # Get environment flags
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
    dev_mode = os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
    
    if not api_available:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "API server is not available. Please try again later.",
                "debug_mode": debug_mode,
                "dev_mode": dev_mode
            }
        )
    
    try:
        # Get video data from API
        response = httpx.get(f"{API_URL}/videos/{video_id}")
        
        if response.status_code == 200:
            video = response.json().get("video", {})
            return templates.TemplateResponse(
                "status.html",
                {
                    "request": request,
                    "video": video,
                    "debug_mode": debug_mode,
                    "dev_mode": dev_mode
                }
            )
        else:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "message": f"Error retrieving video: {response.text}",
                    "debug_mode": debug_mode,
                    "dev_mode": dev_mode
                }
            )
    except Exception as e:
        logger.error(f"Error retrieving video status: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": f"Error retrieving video status: {str(e)}",
                "debug_mode": debug_mode,
                "dev_mode": dev_mode
            }
        )

@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    """
    Show gallery of created videos.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: Gallery page
    """
    api_available = check_api_available()
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
    dev_mode = os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
    
    if not api_available:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "API server is not available. Please try again later.",
                "debug_mode": debug_mode,
                "dev_mode": dev_mode
            }
        )
    
    try:
        # Get videos data from API
        videos = []
        try:
            response = httpx.get(f"{API_URL}/videos")
            if response.status_code == 200:
                videos_data = response.json().get("videos", [])
                
                # Process videos to normalize data
                for video in videos_data:
                    # Map upload_status to status if it exists
                    if "upload_status" in video and not "status" in video:
                        if video["upload_status"] == "completed":
                            video["status"] = "uploaded"
                        else:
                            video["status"] = video["upload_status"]
                    
                    # Set a default status if none exists
                    if "status" not in video:
                        if "video_url" in video and video["video_url"]:
                            video["status"] = "ready_for_upload"
                        else:
                            video["status"] = "processing"
                    
                    # Add to list
                    videos.append(video)
                
                # Sort videos by creation date, newest first
                videos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                
        except Exception as e:
            logger.warning(f"Error fetching videos list: {e}")
            # If in dev mode, generate some mock videos
            if dev_mode:
                videos = generate_mock_videos()
        
        return templates.TemplateResponse(
            "gallery.html",
            {
                "request": request,
                "videos": videos,
                "debug_mode": debug_mode,
                "dev_mode": dev_mode
            }
        )
    except Exception as e:
        logger.error(f"Error rendering gallery: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": f"An error occurred while loading the gallery: {str(e)}",
                "debug_mode": debug_mode,
                "dev_mode": dev_mode
            }
        )

def generate_mock_videos():
    """Generate mock videos for development mode"""
    from datetime import datetime, timedelta
    import random
    import uuid
    
    statuses = ["processing", "ready_for_upload", "uploaded", "failed"]
    tracks = ["track1.mp3", "track2.mp3", "track3.mp3"]
    styles = ["cinematic", "vlog", "music_video", "hyperlapse", "slow_motion"]
    
    videos = []
    now = datetime.now()
    
    for i in range(6):
        status = random.choice(statuses)
        video_id = str(uuid.uuid4())
        created_at = (now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S.%f")
        
        video = {
            "id": video_id,
            "music_track": random.choice(tracks),
            "status": status,
            "created_at": created_at,
            "style": random.choice(styles)
        }
        
        # Add YouTube ID for uploaded videos
        if status == "uploaded":
            video["youtube_id"] = "dQw4w9WgXcQ"  # Example YouTube ID
        
        videos.append(video)
    
    return videos

@app.get("/youtube/dashboard", response_class=HTMLResponse)
async def youtube_dashboard(request: Request):
    """
    Show YouTube dashboard with analytics and options.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: YouTube dashboard page
    """
    api_available = check_api_available()
    
    if not api_available:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "API server is not available. Please try again later."
            }
        )
    
    # Get authentication status
    authenticated = False
    try:
        auth_response = httpx.get(f"{API_URL}/auth/status")
        if auth_response.status_code == 200:
            authenticated = auth_response.json().get("authenticated", False)
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
    
    if not authenticated:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "You must be authenticated with YouTube to access the dashboard."
            }
        )
    
    return templates.TemplateResponse(
        "youtube_dashboard.html",
        {
            "request": request,
            "authenticated": authenticated
        }
    )

@app.get("/youtube/upload", response_class=HTMLResponse)
async def youtube_upload(request: Request):
    """
    Show YouTube upload interface.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: YouTube upload page
    """
    api_available = check_api_available()
    
    if not api_available:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "API server is not available. Please try again later."
            }
        )
    
    # Get authentication status
    authenticated = False
    try:
        auth_response = httpx.get(f"{API_URL}/auth/status")
        if auth_response.status_code == 200:
            authenticated = auth_response.json().get("authenticated", False)
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
    
    if not authenticated:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "You must be authenticated with YouTube to upload videos."
            }
        )
    
    # Get videos ready for upload
    videos = []
    try:
        # Assuming there's an endpoint that filters videos by status
        response = httpx.get(f"{API_URL}/videos?status=ready_for_upload")
        if response.status_code == 200:
            videos = response.json().get("videos", [])
    except Exception as e:
        logger.warning(f"Error fetching videos for upload: {e}")
    
    return templates.TemplateResponse(
        "youtube_upload.html",
        {
            "request": request,
            "authenticated": authenticated,
            "videos": videos
        }
    )

@app.get("/youtube/search", response_class=HTMLResponse)
async def youtube_search(request: Request, query: str = None):
    """
    Show YouTube search interface.
    
    Args:
        request: Request object
        query: Optional search query
        
    Returns:
        TemplateResponse: YouTube search page
    """
    api_available = check_api_available()
    
    if not api_available:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "API server is not available. Please try again later."
            }
        )
    
    # Get authentication status
    authenticated = False
    try:
        auth_response = httpx.get(f"{API_URL}/auth/status")
        if auth_response.status_code == 200:
            authenticated = auth_response.json().get("authenticated", False)
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
    
    # In DEV_MODE, simulate authenticated state
    if os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"):
        authenticated = True
    
    # For MVP, just render the search template
    # In a more complete implementation, we would call the YouTube API to perform the search
    search_results = []
    if query:
        logger.info(f"YouTube search query: {query}")
        # In dev mode, return mock results
        if os.environ.get("DEV_MODE", "false").lower() == "true":
            search_results = [
                {
                    "id": "mock_video_1",
                    "title": f"Mock result 1 for '{query}'",
                    "thumbnail": "https://via.placeholder.com/120x90.png",
                    "channel": "Mock Channel",
                    "views": "10K views",
                    "published": "1 week ago"
                },
                {
                    "id": "mock_video_2",
                    "title": f"Mock result 2 for '{query}'",
                    "thumbnail": "https://via.placeholder.com/120x90.png",
                    "channel": "Another Channel",
                    "views": "5K views",
                    "published": "3 days ago"
                }
            ]
    
    return templates.TemplateResponse(
        "youtube_search.html",
        {
            "request": request,
            "authenticated": authenticated,
            "query": query,
            "search_results": search_results
        }
    )

@app.get("/youtube/trending", response_class=HTMLResponse)
async def youtube_trending(request: Request):
    """
    Show YouTube trending videos.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: YouTube trending page
    """
    api_available = check_api_available()
    
    if not api_available:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "API server is not available. Please try again later."
            }
        )
    
    # Get authentication status
    authenticated = False
    try:
        auth_response = httpx.get(f"{API_URL}/auth/status")
        if auth_response.status_code == 200:
            authenticated = auth_response.json().get("authenticated", False)
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
    
    # In DEV_MODE, simulate authenticated state
    if os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"):
        authenticated = True
    
    # For MVP, return mock trending data
    # In a more complete implementation, we would call the YouTube API
    trending_videos = []
    if os.environ.get("DEV_MODE", "false").lower() == "true":
        trending_videos = [
            {
                "id": "trend_1",
                "title": "Trending Video 1",
                "thumbnail": "https://via.placeholder.com/220x124.png",
                "channel": "Popular Channel",
                "views": "1.2M views",
                "published": "12 hours ago"
            },
            {
                "id": "trend_2",
                "title": "Trending Video 2",
                "thumbnail": "https://via.placeholder.com/220x124.png",
                "channel": "Music Channel",
                "views": "800K views",
                "published": "1 day ago"
            },
            {
                "id": "trend_3",
                "title": "Trending Video 3",
                "thumbnail": "https://via.placeholder.com/220x124.png",
                "channel": "News Channel",
                "views": "500K views",
                "published": "8 hours ago"
            }
        ]
    
    return templates.TemplateResponse(
        "youtube_trending.html",
        {
            "request": request,
            "authenticated": authenticated,
            "trending_videos": trending_videos
            }
        )

@app.post("/videos", response_class=HTMLResponse)
async def create_video(
    request: Request,
    music_track: str = Form(...),
    images: list[UploadFile] = File(...)
):
    """
    Create a new video.
    
    Args:
        request: Request object
        music_track: Music track name
        images: List of image files
        
    Returns:
        RedirectResponse: Redirect to status page
    """
    api_available = check_api_available()
    
    if not api_available:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "API server is not available. Please try again later."
            }
        )
    
    try:
        # Create form data with uploaded files
        form_data = {"music_track": music_track}
        files = [("images", (file.filename, await file.read(), file.content_type)) for file in images]
        
        # Send request to API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/videos",
                data=form_data,
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            video_id = data.get("video_id")
            return RedirectResponse(url=f"/status/{video_id}", status_code=303)
        else:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "message": f"Error creating video: {response.text}"
                }
            )
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": f"Error creating video: {str(e)}"
            }
        )

@app.get("/enhanced", response_class=HTMLResponse)
async def enhanced_creator(request: Request):
    """
    Render the enhanced video creation page with AI features.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: Rendered enhanced.html
    """
    api_available = check_api_available()
    
    # Get authentication status
    authenticated = False
    if api_available:
        try:
            auth_response = httpx.get(f"{API_URL}/auth/status")
            if auth_response.status_code == 200:
                authenticated = auth_response.json().get("authenticated", False)
        except Exception as e:
            logger.error(f"Error checking auth status: {e}")
    
    # Get music tracks with images
    tracks = []
    if api_available:
        try:
            music_response = httpx.get(f"{API_URL}/music?limit=20&skip=0&include_images=true")
            if music_response.status_code == 200:
                tracks = music_response.json().get("tracks", [])
        except Exception as e:
            logger.error(f"Error fetching music tracks: {e}")
    
    # Determine if we're in dev mode
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    
    return templates.TemplateResponse(
        "enhanced.html",
        {
            "request": request,
            "tracks": tracks,
            "api_available": api_available,
            "authenticated": authenticated,
            "dev_mode": dev_mode
        }
    )

def get_current_time():
    """
    Get current time from various APIs with multiple fallbacks.
    
    Returns:
        str: Current time or error message
    """
    # List of time APIs to try in order
    time_apis = [
        {
            "url": "https://timeapi.io/api/Time/current/zone?timeZone=UTC",
            "response_key": "dateTime"
        },
        {
            "url": "https://worldtimeapi.org/api/ip",
            "response_key": "datetime"
        },
        {
            "url": "https://showcase.api.linx.twenty57.net/UnixTime/tounix?date=now",
            "response_key": "UnixTimeStamp",
            "transform": lambda timestamp: f"Unix timestamp: {timestamp}"
        }
    ]
    
    # Try each API in order
    for api in time_apis:
        try:
            response = httpx.get(api["url"], timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                value = data.get(api["response_key"])
                
                # Apply transformation if provided
                if value and "transform" in api:
                    value = api["transform"](value)
                
                if value:
                    logger.debug(f"Successfully retrieved time from {api['url']}")
                    return value
        except Exception as e:
            logger.warning(f"Error fetching time from {api['url']}: {e}")
            continue
    
    # If all APIs fail, use local time
    from datetime import datetime
    logger.warning("All time APIs failed, using local time")
    return datetime.now().isoformat()

@app.get("/api-status-check", response_class=JSONResponse)
async def api_status_check():
    """
    Simple endpoint for testing API connections in debug mode.
    
    Returns:
        JSONResponse: API status information
    """
    api_available = check_api_available()
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
    dev_mode = os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
    
    # Try to get API information
    api_info = {}
    if api_available:
        try:
            response = httpx.get(f"{API_URL}/")
            if response.status_code == 200:
                api_info = response.json()
        except Exception as e:
            logger.error(f"Error getting API info: {e}")
    
    # Get timestamp with robust fallback mechanism
    current_time = get_current_time()
    
    return JSONResponse({
        "status": "ok",
        "timestamp": current_time,
        "api_available": api_available,
        "api_info": api_info,
        "debug_mode": debug_mode,
        "dev_mode": dev_mode,
        "environment": {
            "api_url": API_URL,
            "python_version": os.sys.version
        }
    })

@app.get("/diagnotics", response_class=HTMLResponse)
async def diagnotics_redirect():
    """
    Redirect from misspelled 'diagnotics' to correct 'diagnostics' route.
    """
    return RedirectResponse(url="/debug/diagnostics", status_code=307)

@app.get("/debug/diagnostics", response_class=HTMLResponse)
async def debug_diagnostics(request: Request):
    """
    Show debug diagnostics page with system information.
    Only accessible in debug mode.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: Debug diagnostics page or error page
    """
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
    
    if not debug_mode:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "Debug mode is not enabled. This page is only available in debug mode.",
                "debug_mode": debug_mode,
                "dev_mode": os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
            }
        )
    
    # Collect system information
    import sys
    import platform
    import socket
    import psutil
    
    # Get directory information
    import pathlib
    
    # Check directories exist and permissions
    directories = {
        "static": os.path.exists("static"),
        "templates": os.path.exists("templates"),
        "media": os.path.exists("media"),
        "mock-media": os.path.exists("mock-media")
    }
    
    # Check disk space
    disk_usage = psutil.disk_usage(os.getcwd())
    
    # Get memory information
    mem = psutil.virtual_memory()
    memory_info = {
        "total": mem.total,
        "available": mem.available,
        "percent": mem.percent,
        "used": mem.total - mem.available  # Calculate used memory
    }
    
    # Get API status
    api_available = check_api_available()
    api_info = {}
    if api_available:
        try:
            response = httpx.get(f"{API_URL}/")
            if response.status_code == 200:
                api_info = response.json()
        except Exception as e:
            logger.error(f"Error getting API info for diagnostics: {e}")
    
    # Network test results
    network_tests = []
    
    def test_connectivity(url, description, timeout=3.0):
        try:
            response = httpx.get(url, timeout=timeout)
            return {
                "url": url,
                "description": description,
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
            }
        except httpx.ConnectTimeout:
            return {
                "url": url,
                "description": description,
                "success": False,
                "error": "Connection timed out"
            }
        except httpx.ConnectError:
            return {
                "url": url,
                "description": description,
                "success": False,
                "error": "Connection refused or failed"
            }
        except Exception as e:
            return {
                "url": url,
                "description": description,
                "success": False,
                "error": str(e)
            }
    
    # Run tests synchronously for simplicity
    for url, description in [
        ("https://www.google.com", "Internet Connectivity"),
        ("https://docs.runwayml.com", "Runway ML Docs"),
        (API_URL, "Local API Server"),
        ("https://www.youtube.com", "YouTube"),
        ("https://timeapi.io/api/Time/current/zone?timeZone=UTC", "Time API (Primary)"),
        ("https://worldtimeapi.org/api/ip", "Time API (Secondary)")
    ]:
        network_tests.append(test_connectivity(url, description))
    
    # Environment variables (filtered for security)
    safe_env_vars = {
        k: v for k, v in os.environ.items() 
        if not any(secret in k.lower() for secret in 
                  ["key", "secret", "token", "password", "auth", "cred", "cert"])
    }
    
    # Get information about the mock media files
    import glob
    mock_files = glob.glob("mock-media/*")
    mock_file_details = []
    for file_path in mock_files:
        try:
            file_stats = os.stat(file_path)
            mock_file_details.append({
                "path": file_path,
                "exists": os.path.exists(file_path),
                "size": file_stats.st_size,
                "type": "directory" if os.path.isdir(file_path) else "file"
            })
        except Exception as e:
            mock_file_details.append({
                "path": file_path,
                "error": str(e)
            })
    
    return templates.TemplateResponse(
        "debug_diagnostics.html",
        {
            "request": request,
            "debug_mode": debug_mode,
            "dev_mode": os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"),
            "system_info": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "hostname": socket.gethostname(),
                "cpu_count": psutil.cpu_count(),
                "memory": memory_info,
                "disk": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent
                }
            },
            "directories": directories,
            "api_info": api_info,
            "api_available": api_available,
            "api_url": API_URL,
            "network_tests": network_tests,
            "environment": safe_env_vars,
            "mock_file_details": mock_file_details,
            "current_directory": os.getcwd(),
        }
    )

@app.get("/proxy/styles", response_class=JSONResponse)
async def proxy_styles():
    """
    Proxy endpoint for styles to avoid CORS issues.
    
    Returns:
        JSONResponse: Styles data from API
    """
    try:
        response = httpx.get(f"{API_URL}/styles", timeout=5.0)
        return JSONResponse(content=response.json())
    except Exception as e:
        logger.error(f"Error proxying styles: {e}")
        # Return fallback styles instead of error to prevent client-side failures
        fallback_styles = {
            "styles": {
                "cinematic": {
                    "name": "cinematic",
                    "prompt_template": "Create a cinematic style shot with dramatic lighting",
                    "duration": 5,
                    "transition": "fade"
                },
                "vlog": {
                    "name": "vlog",
                    "prompt_template": "Create a vlog style shot with natural lighting",
                    "duration": 3,
                    "transition": "slide"
                },
                "music_video": {
                    "name": "music_video",
                    "prompt_template": "Create a music video style shot with rhythmic movement",
                    "duration": 5,
                    "transition": "flash"
                },
                "hyperlapse": {
                    "name": "hyperlapse",
                    "prompt_template": "Create a hyperlapse style shot with motion blur",
                    "duration": 2,
                    "transition": "zoom"
                },
                "slow_motion": {
                    "name": "slow_motion",
                    "prompt_template": "Create a slow motion style shot with smooth movement",
                    "duration": 8,
                    "transition": "dissolve"
                }
            }
        }
        return JSONResponse(content=fallback_styles)

@app.post("/proxy/suggest", response_class=JSONResponse)
async def proxy_suggest(request: Request):
    """
    Proxy endpoint for style suggestions to avoid CORS issues.
    
    Args:
        request: Request object
        
    Returns:
        JSONResponse: Suggestion data from API
    """
    try:
        body = await request.body()
        headers = {key: value for key, value in request.headers.items() 
                  if key.lower() not in ['host', 'content-length']}
        
        response = await httpx.AsyncClient().post(
            f"{API_URL}/suggest", 
            content=body,
            headers=headers,
            timeout=10.0
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
    except Exception as e:
        logger.error(f"Error proxying suggest: {e}")
        return JSONResponse(
            content={"error": f"Failed to fetch suggestion: {str(e)}"},
            status_code=500
        )

@app.post("/proxy/videos/enhanced", response_class=JSONResponse)
async def proxy_enhanced_videos(request: Request):
    """
    Proxy endpoint for enhanced videos to avoid CORS issues.
    
    Args:
        request: Request object
        
    Returns:
        JSONResponse: Response from API
    """
    try:
        form_data = await request.form()
        
        # Convert form data to multipart form
        files = []
        data = {}
        
        for key, value in form_data.items():
            if hasattr(value, 'filename'):  # It's a file
                file_content = await value.read()
                files.append((key, (value.filename, file_content, value.content_type)))
            else:  # It's a form field
                data[key] = value
        
        # Send request to API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/videos/enhanced",
                data=data,
                files=files,
                timeout=30.0  # Longer timeout for video processing
            )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
    except Exception as e:
        logger.error(f"Error proxying enhanced videos: {e}")
        return JSONResponse(
            content={"error": f"Failed to create enhanced video: {str(e)}"},
            status_code=500
        )

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    """
    Handle 404 errors.
    
    Args:
        request: Request object
        exc: Exception
        
    Returns:
        TemplateResponse: Error page
    """
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 404,
            "error_message": "The page you're looking for doesn't exist.",
            "api_available": check_api_available(),
            "authenticated": False
        },
        status_code=404
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """
    Handle 500 errors with a custom debug page when in development.
    
    Args:
        request: Request object
        exc: Exception
        
    Returns:
        TemplateResponse: Error page with debugging information in dev mode
    """
    # Check if we're in dev mode
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    
    # Get error details
    error_type = type(exc).__name__
    error_message = str(exc)
    
    # Get traceback info
    import traceback
    tb_info = traceback.format_exc()
    
    # Log the error
    logger.error(f"Internal Server Error: {error_type} - {error_message}")
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_message": "Internal Server Error",
            "error_type": error_type,
            "error_details": error_message,
            "traceback": tb_info if dev_mode else None,
            "dev_mode": dev_mode,
            "api_available": check_api_available(),
            "authenticated": False
        },
        status_code=500
    )

@app.get("/trends", response_class=JSONResponse)
async def trends_proxy(request: Request):
    """
    Proxy trends API endpoint.
    """
    from src.ui.proxy import proxy_request
    return await proxy_request(request, "trends")

@app.get("/trends/optimal-times", response_class=JSONResponse)
async def optimal_times_proxy(request: Request):
    """
    Proxy optimal times API endpoint.
    """
    from src.ui.proxy import proxy_request
    return await proxy_request(request, "trends/optimal-times")

@app.get("/thumbnails", response_class=JSONResponse)
@app.get("/thumbnails/{path:path}", response_class=JSONResponse)
async def thumbnails_proxy(request: Request, path: str = ""):
    """
    Proxy thumbnails API endpoint.
    """
    from src.ui.proxy import proxy_request
    endpoint = f"thumbnails/{path}" if path else "thumbnails"
    return await proxy_request(request, endpoint)

@app.post("/thumbnails/{path:path}", response_class=JSONResponse)
async def thumbnails_post_proxy(request: Request, path: str = ""):
    """
    Proxy thumbnails API endpoint for POST requests.
    """
    from src.ui.proxy import proxy_request
    endpoint = f"thumbnails/{path}" if path else "thumbnails"
    return await proxy_request(request, endpoint)

@app.get("/auth/dev-bypass", response_class=HTMLResponse)
async def auth_dev_bypass(request: Request):
    """
    Development-only authentication bypass.
    
    This endpoint allows bypassing YouTube authentication in development mode
    for testing purposes.
    """
    from src.app.core.settings import DEV_MODE
    
    if not DEV_MODE:
        return RedirectResponse(url="/auth", status_code=307)
    
    # Set a mock authentication cookie
    response = RedirectResponse(url="/youtube/upload", status_code=307)
    response.set_cookie(
        key="youtube_auth", 
        value="dev_bypass_token",
        max_age=3600,
        httponly=True
    )
    
    return response

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    """
    Display the analytics dashboard with charts and metrics.
    """
    # In a production implementation, check authentication
    return templates.TemplateResponse(
        "analytics_dashboard.html", 
        {"request": request}
    )

@app.get("/analytics/dashboard", response_class=JSONResponse)
async def analytics_dashboard_data(request: Request, days: int = 30):
    """
    Proxy endpoint for fetching analytics dashboard data from the API server.
    """
    api_available = check_api_available()
    
    if not api_available:
        return {"success": False, "error": "API server is not available"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/analytics/dashboard?days={days}", timeout=10.0)
            
            # Log the response in debug mode
            if os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes"):
                logger.debug(f"API response for analytics dashboard: {response.status_code}")
                logger.debug(f"API response body: {response.text[:1000]}...")  # Log first 1000 chars
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error for analytics dashboard: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching analytics dashboard data: {e}")
        return {"success": False, "error": str(e)}

@app.get("/analytics/videos/{video_id}", response_class=JSONResponse)
async def analytics_video_data(request: Request, video_id: str):
    """
    Proxy endpoint for fetching analytics data for a specific video from the API server.
    """
    api_available = check_api_available()
    
    if not api_available:
        return {"success": False, "error": "API server is not available"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/analytics/videos/{video_id}", timeout=10.0)
            
            # Log the response in debug mode
            if os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes"):
                logger.debug(f"API response for video analytics: {response.status_code}")
                logger.debug(f"API response body: {response.text[:1000]}...")  # Log first 1000 chars
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error for video analytics: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching video analytics data: {e}")
        return {"success": False, "error": str(e)}

@app.get("/analytics/engagement/{video_id}", response_class=JSONResponse)
async def analytics_engagement_data(request: Request, video_id: str, platform: str = None):
    """
    Proxy endpoint for fetching engagement heatmap data for a specific video from the API server.
    """
    api_available = check_api_available()
    
    if not api_available:
        return {"success": False, "error": "API server is not available"}
    
    try:
        # Build the URL
        url = f"{API_URL}/analytics/engagement/{video_id}"
        if platform:
            url += f"?platform={platform}"
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error for engagement data: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching engagement data: {e}")
        return {"success": False, "error": str(e)}

@app.get("/analytics/recent", response_class=JSONResponse)
async def analytics_recent_data(request: Request, limit: int = 5):
    """
    Proxy endpoint for fetching recent video generations from the API server.
    """
    api_available = check_api_available()
    
    if not api_available:
        return {"success": False, "error": "API server is not available"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/analytics/recent?limit={limit}", timeout=10.0)
            
            # Log the response in debug mode
            if os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes"):
                logger.debug(f"API response for recent analytics: {response.status_code}")
                logger.debug(f"API response body: {response.text[:1000]}...")  # Log first 1000 chars
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error for recent analytics: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching recent analytics data: {e}")
        return {"success": False, "error": str(e)}

@app.get("/analytics/trends", response_class=JSONResponse)
async def analytics_trends_data(request: Request, timeframe: str = "week"):
    """
    Proxy endpoint for fetching analytics trends data from the API server.
    """
    api_available = check_api_available()
    
    if not api_available:
        return {"success": False, "error": "API server is not available"}
    
    # Map timeframe to days
    days_map = {
        "day": 1,
        "week": 7,
        "month": 30,
        "year": 365
    }
    days = days_map.get(timeframe, 30)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/analytics/trends?days={days}", timeout=10.0)
            
            # Log the response in debug mode
            if os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes"):
                logger.debug(f"API response for trends analytics: {response.status_code}")
                logger.debug(f"API response body: {response.text[:1000]}...")  # Log first 1000 chars
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error for trends analytics: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching trends analytics data: {e}")
        return {"success": False, "error": str(e)}

@app.get("/analytics/recommendations", response_class=JSONResponse)
async def analytics_recommendations_data(request: Request):
    """
    Proxy endpoint for fetching content recommendations from the API server.
    """
    api_available = check_api_available()
    
    if not api_available:
        return {"success": False, "error": "API server is not available"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/analytics/recommendations", timeout=10.0)
            
            # Log the response in debug mode
            if os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes"):
                logger.debug(f"API response for recommendations: {response.status_code}")
                logger.debug(f"API response body: {response.text[:1000]}...")  # Log first 1000 chars
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error for recommendations: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching recommendations data: {e}")
        return {"success": False, "error": str(e)}

# Serve favicon.ico from the static directory
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon."""
    return FileResponse("static/favicon.ico")

@app.get("/proxy/fonts/{path:path}", response_class=HTMLResponse)
@app.head("/proxy/fonts/{path:path}", response_class=HTMLResponse)
async def proxy_google_fonts(request: Request, path: str):
    """
    Proxy endpoint for Google Fonts to avoid CORS issues.
    
    Args:
        request: Request object
        path: Font path to proxy
        
    Returns:
        The font CSS with headers to avoid CORS issues
    """
    try:
        # For HEAD requests, just return the headers
        if request.method == "HEAD":
            return HTMLResponse(
                content="",
                headers={
                    "Content-Type": "text/css",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        
        # Simplified approach: return system font fallbacks instead of proxying
        # This ensures we don't have any network issues with Google Fonts
        return HTMLResponse(
            content="""
                /* Fallback to system fonts */
                @font-face {
                    font-family: 'Roboto';
                    src: local('SF Pro Display'), local('SFProDisplay-Regular'),
                         local('-apple-system'), local('BlinkMacSystemFont'),
                         local('Segoe UI'), local('Roboto'), local('Helvetica Neue'), 
                         local('Arial'), sans-serif;
                    font-weight: 400;
                    font-style: normal;
                    font-display: swap;
                }
                
                @font-face {
                    font-family: 'Roboto';
                    src: local('SF Pro Display Bold'), local('SFProDisplay-Bold'),
                         local('-apple-system-bold'), local('BlinkMacSystemFont'),
                         local('Segoe UI Bold'), local('Roboto Bold'), 
                         local('Helvetica Neue Bold'), local('Arial Bold'), sans-serif;
                    font-weight: 700;
                    font-style: normal;
                    font-display: swap;
                }
                
                @font-face {
                    font-family: 'Roboto';
                    src: local('SF Pro Display Light'), local('SFProDisplay-Light'),
                         local('-apple-system-thin'), local('BlinkMacSystemFont'),
                         local('Segoe UI Light'), local('Roboto Light'), 
                         local('Helvetica Neue Light'), local('Arial'), sans-serif;
                    font-weight: 300;
                    font-style: normal;
                    font-display: swap;
                }
                
                @font-face {
                    font-family: 'Open Sans';
                    src: local('SF Pro Display'), local('SFProDisplay-Regular'),
                         local('-apple-system'), local('BlinkMacSystemFont'),
                         local('Segoe UI'), local('Roboto'), local('Helvetica Neue'), 
                         local('Arial'), sans-serif;
                    font-weight: 400;
                    font-style: normal;
                    font-display: swap;
                }
                
                @font-face {
                    font-family: 'Montserrat';
                    src: local('SF Pro Display'), local('SFProDisplay-Regular'),
                         local('-apple-system'), local('BlinkMacSystemFont'),
                         local('Segoe UI'), local('Roboto'), local('Helvetica Neue'), 
                         local('Arial'), sans-serif;
                    font-weight: 400;
                    font-style: normal;
                    font-display: swap;
                }
            """,
            headers={
                "Content-Type": "text/css",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=86400"
            }
        )
    except Exception as e:
        logger.error(f"Error with font proxy: {e}")
        return HTMLResponse(
            content="/* Error loading fonts */",
            headers={
                "Content-Type": "text/css",
                "Access-Control-Allow-Origin": "*"
            }
        )

# WebSocket endpoint for real-time updates
@app.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket):
    """WebSocket endpoint for real-time analytics updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            try:
                # Parse the JSON message
                message = json.loads(data)
                
                # Handle subscription to specific analytics topics
                if message.get("type") == "subscribe":
                    topic = message.get("topic")
                    logger.info(f"Client subscribed to {topic}")
                    
                    # Send initial data for the topic
                    if topic == "dashboard":
                        # Fetch dashboard data
                        days = message.get("days", 30)
                        try:
                            async with httpx.AsyncClient() as client:
                                response = await client.get(f"{API_URL}/analytics/dashboard?days={days}", timeout=10.0)
                                if response.status_code == 200:
                                    await websocket.send_json({
                                        "type": "update",
                                        "topic": "dashboard",
                                        "data": response.json()
                                    })
                        except Exception as e:
                            logger.error(f"Error fetching dashboard data: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Failed to fetch dashboard data: {str(e)}"
                            })
                    
                    elif topic == "recent":
                        # Fetch recent generations data
                        limit = message.get("limit", 5)
                        try:
                            async with httpx.AsyncClient() as client:
                                response = await client.get(f"{API_URL}/analytics/recent?limit={limit}", timeout=10.0)
                                if response.status_code == 200:
                                    await websocket.send_json({
                                        "type": "update",
                                        "topic": "recent",
                                        "data": response.json()
                                    })
                        except Exception as e:
                            logger.error(f"Error fetching recent data: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Failed to fetch recent data: {str(e)}"
                            })
                
                # Handle ping messages to keep connection alive
                elif message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Broadcast analytics update to all connected clients
async def broadcast_analytics_update(topic: str, data: dict):
    """
    Broadcast an analytics update to all connected clients.
    
    Args:
        topic: The analytics topic (dashboard, recent, etc.)
        data: The data to broadcast
    """
    await manager.broadcast({
        "type": "update",
        "topic": topic,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })

# Background task for periodically sending updates in development mode
async def dev_mode_updates():
    """
    Periodically send simulated updates to connected clients in development mode.
    This is used only for development/testing the real-time functionality.
    """
    global background_task_running
    background_task_running = True
    
    logger.info("Starting development mode updates background task")
    
    try:
        while True:
            # Only send updates if there are active connections
            if manager.has_connections:
                try:
                    # Generate random changes for metrics
                    views_change = random.randint(-10, 20)
                    engagement_change = random.randint(-5, 15)
                    success_rate_change = random.uniform(-0.01, 0.02)
                    processing_time_change = random.uniform(-5, 10)
                    
                    # Create dashboard update with random changes
                    dashboard_data = {
                        "success": True,
                        "total_videos": random.randint(340, 360),
                        "total_views": random.randint(25000, 30000),
                        "total_engagement": random.randint(2000, 3000),
                        "engagement_rate": random.uniform(0.08, 0.12),
                        "avg_generation_time": random.uniform(200, 300),
                        "total_subscribers": random.randint(8000, 12000),
                        "avg_video_length": random.uniform(60, 90),
                        "success_rate": random.uniform(0.9, 0.98),
                        "total_videos_trend": random.uniform(0.05, 0.15),
                        "success_rate_trend": random.uniform(-0.02, 0.05),
                        "avg_generation_time_trend": random.uniform(-0.1, 0.05),
                        "avg_video_length_trend": random.uniform(-0.05, 0.1),
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    # Send dashboard update
                    await broadcast_analytics_update("dashboard", dashboard_data)
                    logger.debug("Sent dashboard update to connected clients")
                    
                    # Every few updates, also send a recent videos update
                    if random.random() < 0.3:  # 30% chance
                        # Generate a new random recent video
                        now = datetime.now()
                        recent_video = {
                            "id": f"VID-{random.randint(8400, 8500)}",
                            "created_at": (now - timedelta(minutes=random.randint(5, 60))).isoformat(),
                            "preset": random.choice(["Electronic", "Cinematic", "Standard", "Pop", "Hip Hop"]),
                            "duration": random.randint(30, 120),
                            "processing_time": round(random.uniform(1.5, 8.0), 1),
                            "status": random.choice(["completed", "completed", "completed", "completed", "failed"])
                        }
                        
                        # Send recent videos update
                        recent_data = {
                            "success": True,
                            "sessions": [recent_video],
                            "type": "new_video"
                        }
                        await broadcast_analytics_update("recent", recent_data)
                        logger.debug("Sent new video update to connected clients")
                except Exception as e:
                    logger.error(f"Error generating update in dev mode: {e}")
            
            # Wait between updates (5-15 seconds)
            await asyncio.sleep(random.randint(5, 15))
    except asyncio.CancelledError:
        logger.info("Development mode updates task cancelled")
        background_task_running = False
    except Exception as e:
        logger.error(f"Error in development mode updates task: {e}")
        background_task_running = False

# Test endpoint for WebSocket updates (development only)
@app.post("/api/test/websocket")
async def test_websocket_update(data: dict):
    """
    Test endpoint for sending WebSocket updates.
    
    This endpoint allows sending test updates that will be broadcast to all
    connected WebSocket clients. This is useful for testing the real-time
    functionality without having to wait for actual data updates.
    
    Note: This endpoint is intended for development and testing only.
    """
    if not os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"):
        raise HTTPException(status_code=403, detail="This endpoint is only available in development mode")
    
    # Extract topic and data
    topic = data.get("topic", "dashboard")
    update_data = data.get("data", {})
    
    # Broadcast update to all connected clients
    await broadcast_analytics_update(topic, update_data)
    
    return {"success": True, "message": f"Broadcast {topic} update to {len(manager.active_connections)} clients"}

@app.get("/debug", response_class=HTMLResponse)
@app.get("/debug/console", response_class=HTMLResponse)
async def debug_console(request: Request):
    """
    Show detailed debug console information.
    Only available in development mode.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Debug console page
    """
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    if not dev_mode:
        return RedirectResponse(url="/")
    
    # Get system information
    import platform
    import psutil
    import sys
    
    # Get Python version
    python_version = sys.version
    
    # Get memory usage
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_usage = f"{memory_info.rss / (1024 * 1024):.2f} MB"
    
    # Get CPU usage
    cpu_percent = process.cpu_percent(interval=0.1)
    
    # Get API status
    api_available = check_api_available()
    
    # Get app version (from env var or default)
    version = os.environ.get("APP_VERSION", "1.0.0-dev")
    
    # Get startup time from app state
    start_time = getattr(app.state, "startup_time", "Unknown")
    
    # Get environment variables (filtered to remove sensitive info)
    env_vars = {k: v for k, v in os.environ.items() 
               if not k.lower().startswith(('secret', 'key', 'token', 'pass', 'auth'))}
    
    return templates.TemplateResponse(
        "debug-console.html",
        {
            "request": request,
            "api_available": api_available,
            "dev_mode": dev_mode,
            "system": {
                "os": platform.system(),
                "version": platform.version(),
                "python": python_version.split()[0],
                "hostname": platform.node(),
                "processor": platform.processor()
            },
            "performance": {
                "memory_usage": memory_usage,
                "cpu_percent": cpu_percent,
                "uptime": start_time
            },
            "app": {
                "version": version,
                "start_time": start_time,
                "api_url": API_URL,
                "api_available": api_available
            },
            "env_vars": env_vars
        }
    )

@app.get("/music/{track_name}/waveform", response_class=JSONResponse)
async def proxy_waveform(request: Request, track_name: str):
    """
    Proxy endpoint for music waveform data.
    
    Args:
        request: Request object
        track_name: Track name
        
    Returns:
        JSON response with waveform data
    """
    # For development, we'll generate mock waveform data
    import random
    
    # In production, this would make a real request to the API
    try:
        if API_URL:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{API_URL}/music/{track_name}/waveform", timeout=5.0)
                    if response.status_code == 200:
                        return response.json()
            except Exception as e:
                logger.warning(f"Error getting waveform data from API: {e}")
        
        # If API request failed or API_URL is not set, generate mock data
        waveform_data = [random.uniform(0.2, 1.0) for _ in range(64)]
        return {"data": waveform_data, "track_name": track_name}
        
    except Exception as e:
        logger.error(f"Error generating waveform data: {e}")
        return {"data": [0.5] * 64, "track_name": track_name, "error": str(e)}

@app.get("/styles", response_class=JSONResponse)
async def get_styles(request: Request):
    """
    Get available video styles.
    
    Args:
        request: Request object
        
    Returns:
        List of available styles
    """
    try:
        # Try to fetch from API
        if API_URL:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{API_URL}/styles", timeout=5.0)
                    if response.status_code == 200:
                        return response.json()
            except Exception as e:
                logger.warning(f"Error getting styles from API: {e}")
        
        # Fall back to mock data if API fails or is not available
        mock_styles = [
            {
                "id": "CINEMATIC", 
                "name": "Cinematic",
                "description": "Professional film-like quality with dramatic lighting and smooth transitions"
            },
            {
                "id": "VIBRANT", 
                "name": "Vibrant",
                "description": "Bright, energetic style with saturated colors and dynamic motion"
            },
            {
                "id": "MINIMALIST", 
                "name": "Minimalist",
                "description": "Clean, simple aesthetic with plenty of white space and subtle animations"
            },
            {
                "id": "RETRO", 
                "name": "Retro",
                "description": "Vintage look with film grain, light leaks, and classic color grading"
            },
            {
                "id": "NEON", 
                "name": "Neon",
                "description": "Bold, high-contrast style with glowing elements and dark backgrounds"
            }
        ]
        return {"styles": mock_styles}
    except Exception as e:
        logger.error(f"Error getting styles: {e}")
        return {"styles": [], "error": str(e)}

@app.get("/audio-waveform")
async def audio_waveform_demo(request: Request):
    """
    Waveform audio player demo page.
    """
    # Get list of music tracks
    music_tracks = []
    
    try:
        # Get tracks from API
        response = await make_api_request(request, "GET", "/music/catalog")
        if response.status_code == 200:
            music_tracks = response.json()
    except Exception as e:
        logger.error(f"Error fetching music tracks for waveform demo: {e}")
        # Provide mock data if api request fails
        music_tracks = [
            {"id": f"track{i}", "title": f"Track {i}", "artist": f"Artist {i}"} 
            for i in range(1, 6)
        ]
    
    return templates.TemplateResponse(
        "audio_waveform_demo.html", 
        {
            "request": request, 
            "page_title": "Audio Waveform Demo",
            "music_tracks": music_tracks,
        }
    )

# Add proxy for export endpoints
@app.get("/api/export/platforms", response_class=JSONResponse)
async def proxy_export_platforms(request: Request):
    """Proxy endpoint for export platforms"""
    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/export/platforms")
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying export platforms request: {e}")
        return JSONResponse(
            content={"error": "Failed to fetch export platforms", "detail": str(e)},
            status_code=500
        )

@app.get("/api/export/{path:path}", response_class=JSONResponse)
async def proxy_export(request: Request, path: str):
    """Proxy endpoint for all export paths"""
    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    # Get all query parameters
    params = dict(request.query_params)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/export/{path}", params=params)
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying export request to {path}: {e}")
        return JSONResponse(
            content={"error": f"Failed to fetch export data for {path}", "detail": str(e)},
            status_code=500
        )

@app.post("/api/export", response_class=JSONResponse)
@app.post("/api/export/{path:path}", response_class=JSONResponse)
async def proxy_export_post(request: Request, path: str = ""):
    """Proxy POST endpoint for export"""
    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    # Get the request body
    body = await request.json()
    try:
        async with httpx.AsyncClient() as client:
            if path:
                response = await client.post(f"{api_url}/export/{path}", json=body)
            else:
                response = await client.post(f"{api_url}/export", json=body)
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying export POST request to {path}: {e}")
        return JSONResponse(
            content={"error": f"Failed to process export request for {path}", "detail": str(e)},
            status_code=500
        )

# Add scheduler proxy endpoints
@app.get("/api/scheduler/{path:path}", response_class=JSONResponse)
async def proxy_scheduler_get(request: Request, path: str):
    """Proxy GET endpoint for scheduler API"""
    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    # Get all query parameters
    params = dict(request.query_params)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/scheduler/{path}", params=params)
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying scheduler GET request to {path}: {e}")
        return JSONResponse(
            content={"error": f"Failed to fetch scheduler data for {path}", "detail": str(e)},
            status_code=500
        )

@app.post("/api/scheduler/{path:path}", response_class=JSONResponse)
async def proxy_scheduler_post(request: Request, path: str):
    """Proxy POST endpoint for scheduler API"""
    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    # Get the request body
    body = await request.json()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{api_url}/scheduler/{path}", json=body)
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying scheduler POST request to {path}: {e}")
        return JSONResponse(
            content={"error": f"Failed to process scheduler request for {path}", "detail": str(e)},
            status_code=500
        )

# Add music recommendations proxy endpoints
@app.get("/api/music-recommendations/{path:path}", response_class=JSONResponse)
async def proxy_music_recommendations_get(request: Request, path: str):
    """Proxy GET endpoint for music recommendations API"""
    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    # Get all query parameters
    params = dict(request.query_params)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/music-recommendations/{path}", params=params)
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying music recommendations GET request to {path}: {e}")
        return JSONResponse(
            content={"error": f"Failed to fetch music recommendations data for {path}", "detail": str(e)},
            status_code=500
        )

@app.post("/api/music-recommendations/{path:path}", response_class=JSONResponse)
async def proxy_music_recommendations_post(request: Request, path: str):
    """Proxy POST endpoint for music recommendations API"""
    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    # Get the request body
    body = await request.json()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{api_url}/music-recommendations/{path}", json=body)
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying music recommendations POST request to {path}: {e}")
        return JSONResponse(
            content={"error": f"Failed to process music recommendations request for {path}", "detail": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)