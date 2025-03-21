"""
Debug utilities and endpoints for development environment.
"""

import os
import sys
import time
import platform
import psutil
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.templating import Jinja2Templates

from src.ui.auth import check_api_available

# Initialize router
router = APIRouter(prefix="/debug")

# System information
def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": sys.version.split()[0],
        "hostname": platform.node(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": f"{psutil.virtual_memory().total / (1024 * 1024 * 1024):.2f} GB",
        "uptime": str(timedelta(seconds=int(time.time() - psutil.boot_time())))
    }

# Get memory usage
def get_memory_usage() -> Dict[str, Any]:
    """Get memory usage information."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    vm = psutil.virtual_memory()
    
    return {
        "process": {
            "rss": f"{memory_info.rss / (1024 * 1024):.2f} MB",
            "vms": f"{memory_info.vms / (1024 * 1024):.2f} MB",
            "percent": f"{process.memory_percent():.2f}%"
        },
        "system": {
            "total": f"{vm.total / (1024 * 1024 * 1024):.2f} GB",
            "available": f"{vm.available / (1024 * 1024 * 1024):.2f} GB",
            "used": f"{vm.used / (1024 * 1024 * 1024):.2f} GB",
            "percent": f"{vm.percent:.2f}%"
        },
        "timestamp": datetime.now().isoformat()
    }

# Get CPU usage
def get_cpu_usage() -> Dict[str, Any]:
    """Get CPU usage information."""
    process = psutil.Process(os.getpid())
    
    return {
        "process": {
            "percent": f"{process.cpu_percent(interval=0.1):.2f}%"
        },
        "system": {
            "percent": f"{psutil.cpu_percent(interval=0.1):.2f}%",
            "per_cpu": [f"{p:.2f}%" for p in psutil.cpu_percent(interval=0.1, percpu=True)]
        },
        "timestamp": datetime.now().isoformat()
    }

# Request logs storage (simple in-memory circular buffer)
max_request_logs = 100
request_logs: List[Dict[str, Any]] = []

# Error logs storage (simple in-memory circular buffer)
max_error_logs = 50
error_logs: List[Dict[str, Any]] = []

# Request logging middleware
async def log_request(request: Request, call_next):
    """Log requests in debug mode."""
    start_time = time.time()
    
    # Get request details before processing
    request_details = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown",
        "headers": dict(request.headers)
    }
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Update with response details
        process_time = time.time() - start_time
        request_details.update({
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2)
        })
        
        # Add to logs with circular buffer behavior
        request_logs.append(request_details)
        if len(request_logs) > max_request_logs:
            request_logs.pop(0)
        
        # Log the request
        log_entry = f"{request.method} {request.url} - {response.status_code} ({process_time * 1000:.2f}ms)"
        print(f"DEBUG: {log_entry}")
        
        return response
        
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        error_details = {
            **request_details,
            "error": str(e),
            "error_type": type(e).__name__,
            "process_time_ms": round(process_time * 1000, 2)
        }
        
        # Add to error logs with circular buffer behavior
        error_logs.append(error_details)
        if len(error_logs) > max_error_logs:
            error_logs.pop(0)
            
        # Re-raise the exception
        raise

# API endpoints for debug info
@router.get("/info")
async def debug_info():
    """Get debug information about the application."""
    return JSONResponse(get_system_info())

@router.get("/memory")
async def debug_memory():
    """Get memory usage information."""
    return JSONResponse(get_memory_usage())

@router.get("/cpu")
async def debug_cpu():
    """Get CPU usage information."""
    return JSONResponse(get_cpu_usage())

@router.get("/clear-cache")
async def clear_cache():
    """Clear application cache."""
    # Simulated cache clearing
    time.sleep(0.5)  # Simulate some work
    return JSONResponse({"status": "success", "message": "Cache cleared successfully"})

@router.get("/error/test")
async def test_error():
    """Generate a test error for debugging."""
    raise HTTPException(status_code=500, detail="This is a test error")

@router.get("/session/reset")
async def reset_session():
    """Reset user session."""
    # Simulated session reset
    time.sleep(0.5)  # Simulate some work
    return JSONResponse({"status": "success", "message": "Session reset successfully"})

@router.get("/report")
async def generate_debug_report():
    """Generate a comprehensive debug report."""
    report = {
        "system": get_system_info(),
        "memory": get_memory_usage(),
        "cpu": get_cpu_usage(),
        "environment": dict(os.environ),
        "timestamp": datetime.now().isoformat()
    }
    
    return JSONResponse(report)

# Define debug endpoints

@router.get("/", response_class=HTMLResponse)
async def debug_index(request: Request):
    """Basic debug page for development."""
    return JSONResponse({
        "debug_mode": True,
        "message": "Debug mode is active. See available endpoints below.",
        "endpoints": [
            {"path": "/debug/info", "description": "System and application information"},
            {"path": "/debug/memory", "description": "Memory usage information"},
            {"path": "/debug/cpu", "description": "CPU usage information"},
            {"path": "/debug/logs", "description": "Recent request logs"},
            {"path": "/debug/errors", "description": "Recent error logs"},
            {"path": "/debug/console", "description": "Debug console"}
        ]
    })

@router.get("/logs")
async def debug_logs(limit: int = 20):
    """Get recent request logs."""
    logs_to_return = request_logs[-limit:] if limit < len(request_logs) else request_logs
    return {
        "count": len(logs_to_return),
        "logs": logs_to_return
    }

@router.get("/errors")
async def debug_errors(limit: int = 20):
    """Get recent error logs."""
    logs_to_return = error_logs[-limit:] if limit < len(error_logs) else error_logs
    return {
        "count": len(logs_to_return),
        "logs": logs_to_return
    }

@router.post("/trigger-error")
async def debug_trigger_error(message: str = "Test error triggered from API"):
    """Trigger a test error."""
    raise HTTPException(status_code=500, detail=message)

@router.get("/request-count")
async def debug_request_count():
    """Get request count statistics."""
    # Group by path and method
    path_counts = {}
    method_counts = {
        "GET": 0,
        "POST": 0,
        "PUT": 0,
        "DELETE": 0,
        "OTHER": 0
    }
    
    for log in request_logs:
        # Path counting
        path = log.get("url", "").split("?")[0]  # Remove query params
        if path not in path_counts:
            path_counts[path] = 0
        path_counts[path] += 1
        
        # Method counting
        method = log.get("method", "OTHER")
        if method in method_counts:
            method_counts[method] += 1
        else:
            method_counts["OTHER"] += 1
    
    # Sort paths by count (descending)
    sorted_paths = sorted(
        [{"path": path, "count": count} for path, count in path_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    
    return {
        "total_requests": len(request_logs),
        "methods": method_counts,
        "paths": sorted_paths[:10]  # Return top 10 paths
    }

# Define additional debug APIs as needed 