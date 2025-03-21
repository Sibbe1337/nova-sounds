"""
Proxy module for forwarding requests to the API server.
"""

import logging
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.encoders import jsonable_encoder

from src.app.core.port_finder import get_api_port

logger = logging.getLogger(__name__)

async def proxy_request(request: Request, path: str) -> Response:
    """
    Proxy a request to the API server.
    
    Args:
        request: The original request
        path: The path to proxy to
        
    Returns:
        The response from the API server
    """
    api_port = get_api_port()
    api_base_url = f"http://localhost:{api_port}"
    api_url = f"{api_base_url}/{path}"
    
    logger.debug(f"Proxying request to {api_url}")
    
    # Extract request details
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    method = request.method
    
    # Get query parameters
    params = dict(request.query_params)
    
    # Special handling for known endpoints
    if path in ['trends', 'trends/optimal-times', 'thumbnails']:
        api_url = f"{api_base_url}/{path}"
        logger.info(f"Special handling for API endpoint: {api_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(api_url, headers=headers, params=params)
            elif method.upper() == "POST":
                form_data = None
                json_data = None
                
                # Handle form data
                if request.headers.get("content-type", "").startswith("multipart/form-data"):
                    form_data = await request.form()
                    form_data = {k: v for k, v in form_data.items()}
                # Handle JSON data
                elif request.headers.get("content-type", "").startswith("application/json"):
                    json_data = await request.json()
                # Handle URL-encoded form data
                elif request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
                    form_data = await request.form()
                    form_data = {k: v for k, v in form_data.items()}
                # Default case: raw body data
                else:
                    data = await request.body()
                    
                response = await client.post(
                    api_url, 
                    headers=headers, 
                    params=params,
                    data=data if not form_data and not json_data else None,
                    files=form_data,
                    json=json_data
                )
            elif method.upper() == "PUT":
                data = await request.body()
                response = await client.put(api_url, headers=headers, params=params, content=data)
            elif method.upper() == "DELETE":
                response = await client.delete(api_url, headers=headers, params=params)
            else:
                return JSONResponse(
                    status_code=405,
                    content={"detail": f"Method {method} not allowed"}
                )
            
            # Create a response with the same status code, headers, and content
            if response.headers.get("content-type", "").startswith("application/json"):
                content = response.json()
                return JSONResponse(
                    status_code=response.status_code,
                    content=content
                )
            else:
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
                
    except httpx.RequestError as e:
        logger.error(f"Error proxying request to {api_url}: {e}")
        return JSONResponse(
            status_code=502,
            content={"detail": f"Error connecting to API server: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Unexpected error proxying request to {api_url}: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        ) 