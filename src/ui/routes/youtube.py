@router.get("/upload", response_class=HTMLResponse)
async def youtube_upload(request: Request):
    """
    YouTube Upload Page.
    
    Allows uploading videos to YouTube after they've been created in the app.
    """
    # Check if authenticated
    auth_token = request.cookies.get("youtube_auth")
    dev_bypass = auth_token == "dev_bypass_token"
    
    from src.app.core.settings import DEV_MODE
    
    # If in dev mode and has bypass token, allow access
    if DEV_MODE and dev_bypass:
        return templates.TemplateResponse(
            "youtube_upload.html", 
            {"request": request, "dev_mode": DEV_MODE}
        )
    
    # Otherwise, check for regular authentication
    try:
        auth_status_resp = await api_request(request, "GET", "auth/status")
        auth_status = auth_status_resp.get("authenticated", False)
        
        if not auth_status:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "title": "Error",
                    "message": "You must be authenticated with YouTube to upload videos.",
                    "action_url": "/auth",
                    "action_text": "Authenticate with YouTube",
                    "dev_bypass_url": "/auth/dev-bypass" if DEV_MODE else None
                }
            )
        
        # Get videos ready for upload
        videos_resp = await api_request(request, "GET", "videos?status=ready_for_upload")
        videos = videos_resp.get("videos", [])
        
        return templates.TemplateResponse(
            "youtube_upload.html", 
            {"request": request, "videos": videos, "dev_mode": DEV_MODE}
        )
    except Exception as e:
        logger.error(f"Error in YouTube upload page: {e}")
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request, 
                "title": "Error", 
                "message": f"Error getting YouTube upload page: {str(e)}",
                "action_url": "/", 
                "action_text": "Go Home",
                "dev_bypass_url": "/auth/dev-bypass" if DEV_MODE else None
            }
        ) 