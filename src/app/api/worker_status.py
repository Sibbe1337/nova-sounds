"""
API endpoints for monitoring Celery worker status.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Set
import logging
import json
import asyncio
from datetime import datetime
import os

from src.app.tasks.config import app as celery_app
from src.app.core.settings import DEV_MODE

# Set up logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/worker-status", tags=["worker-status"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_status: Dict[str, Any] = {}
        self.running = True
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send the last known status immediately after connection
        if self.last_status:
            await websocket.send_json(self.last_status)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
    async def broadcast(self, message: Dict[str, Any]):
        self.last_status = message
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                await self.disconnect(connection)
                
    def stop(self):
        self.running = False
        self.active_connections = []

# Create connection manager instance
manager = ConnectionManager()

# WebSocket status updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time worker status updates
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and check for client messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Celery status background task
async def monitor_celery_status():
    """Background task to monitor Celery status and broadcast updates"""
    logger.info("Starting Celery status monitor")
    while manager.running:
        try:
            status = get_worker_status()
            await manager.broadcast(status)
        except Exception as e:
            logger.error(f"Error in celery status monitor: {e}")
            await manager.broadcast({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        await asyncio.sleep(2)  # Update every 2 seconds

# Celery status API endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_status():
    """
    Get current Celery worker status
    
    Returns:
        dict: Worker status information
    """
    try:
        return get_worker_status()
    except Exception as e:
        logger.error(f"Error getting worker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks", response_model=Dict[str, Any])
async def get_tasks_status():
    """
    Get current tasks status
    
    Returns:
        dict: Tasks status information
    """
    try:
        return get_task_status()
    except Exception as e:
        logger.error(f"Error getting tasks status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}", response_model=Dict[str, Any])
async def get_task_info(task_id: str):
    """
    Get information about a specific task
    
    Args:
        task_id: ID of the task
        
    Returns:
        dict: Task information
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'id': task_id,
                'status': 'pending',
                'info': 'Task is waiting for execution'
            }
        elif task.state == 'STARTED':
            response = {
                'id': task_id,
                'status': 'started',
                'info': 'Task has been started'
            }
        elif task.state == 'RETRY':
            response = {
                'id': task_id,
                'status': 'retry',
                'info': 'Task is being retried'
            }
        elif task.state == 'FAILURE':
            response = {
                'id': task_id,
                'status': 'failure',
                'error': str(task.info),
                'traceback': task.traceback
            }
        elif task.state == 'SUCCESS':
            response = {
                'id': task_id,
                'status': 'success',
                'result': task.result
            }
        else:
            response = {
                'id': task_id,
                'status': task.state,
                'info': 'Unknown state'
            }
            
        return response
    except Exception as e:
        logger.error(f"Error getting task info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}/status", response_model=Dict[str, Any])
async def get_task_status(task_id: str):
    """
    Get detailed status information for a specific task.
    
    This endpoint provides detailed progress information, subtask states, and result data
    for the specified task.
    """
    try:
        # Retrieve task from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        if not task_result:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        
        # Get basic task info
        task_info = {
            "id": task_id,
            "status": task_result.status,
            "progress": 0,
            "status_message": "",
            "subtasks": []
        }
        
        # Try to get the task progress if available
        if hasattr(task_result, 'info') and task_result.info:
            info = task_result.info
            if isinstance(info, dict):
                # Extract progress percentage
                if 'progress' in info:
                    task_info['progress'] = info['progress']
                
                # Extract status message
                if 'status_message' in info:
                    task_info['status_message'] = info['status_message']
                
                # Extract subtasks status
                if 'subtasks' in info:
                    task_info['subtasks'] = info['subtasks']
                    
                # Handle metadata
                if 'metadata' in info:
                    task_info['metadata'] = info['metadata']
        
        # Get result if task is complete
        if task_result.status == 'SUCCESS':
            result = task_result.result
            if isinstance(result, dict):
                task_info['result'] = result
            else:
                task_info['result'] = {'value': str(result)}
                
            # If we have a result but no progress, set to 100%
            if task_info['progress'] == 0:
                task_info['progress'] = 100
        
        # Get error info if task failed
        elif task_result.status == 'FAILURE':
            error = task_result.result
            if isinstance(error, Exception):
                task_info['error_message'] = str(error)
                task_info['error_type'] = error.__class__.__name__
                if hasattr(error, 'traceback'):
                    task_info['traceback'] = error.traceback
        
        return task_info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving task status: {str(e)}")

@router.get("/tasks/{task_id}/log", response_model=Dict[str, Any])
async def get_task_log(task_id: str):
    """
    Get the logs for a specific task.
    
    This endpoint provides the full log output for the task, useful for debugging
    and detailed progress information.
    """
    try:
        # For development mode, generate mock logs
        if DEV_MODE:
            return {
                "task_id": task_id,
                "log": generate_mock_task_log(task_id)
            }
        
        # In production, retrieve the actual logs
        log_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', f"task_{task_id}.log")
        
        if not os.path.exists(log_path):
            return {
                "task_id": task_id,
                "log": "No logs found for this task. The task may still be initializing or logs aren't being saved."
            }
        
        with open(log_path, 'r') as f:
            log_content = f.read()
            
        return {
            "task_id": task_id,
            "log": log_content
        }
    
    except Exception as e:
        logger.exception(f"Error getting task log: {e}")
        return {
            "task_id": task_id,
            "log": f"Error retrieving logs: {str(e)}"
        }

@router.post("/tasks/{task_id}/revoke", response_model=Dict[str, Any])
async def revoke_task(task_id: str):
    """
    Revoke (cancel) a running task.
    
    This endpoint allows users to cancel a task that is in progress.
    """
    try:
        # Revoke the task in Celery
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            "success": True,
            "message": f"Task {task_id} has been revoked."
        }
    
    except Exception as e:
        logger.exception(f"Error revoking task: {e}")
        return {
            "success": False,
            "message": f"Error revoking task: {str(e)}"
        }

def get_worker_status() -> Dict[str, Any]:
    """
    Get current Celery worker status
    
    Returns:
        dict: Worker status information
    """
    if DEV_MODE:
        # In development mode, return mock data
        return generate_mock_worker_status()
    
    try:
        # Get worker information from Celery
        i = celery_app.control.inspect()
        
        stats = i.stats() or {}
        active_tasks = i.active() or {}
        scheduled_tasks = i.scheduled() or {}
        reserved_tasks = i.reserved() or {}
        
        workers = []
        
        # Combine worker data
        for worker_name in set(list(stats.keys()) + 
                            list(active_tasks.keys()) + 
                            list(scheduled_tasks.keys()) + 
                            list(reserved_tasks.keys())):
            worker_stats = stats.get(worker_name, {})
            worker_active = active_tasks.get(worker_name, [])
            worker_scheduled = scheduled_tasks.get(worker_name, [])
            worker_reserved = reserved_tasks.get(worker_name, [])
            
            # Combine worker data
            worker_info = {
                "name": worker_name,
                "status": "online",
                "pid": worker_stats.get('pid', 'N/A'),
                "concurrency": worker_stats.get('pool', {}).get('max-concurrency', 'N/A'),
                "broker": worker_stats.get('broker', {}).get('transport', 'N/A'),
                "uptime": worker_stats.get('uptime', 'N/A'),
                "active_tasks": len(worker_active),
                "scheduled_tasks": len(worker_scheduled),
                "reserved_tasks": len(worker_reserved),
                "processed": worker_stats.get('total', {}).get('processed', 0)
            }
            
            workers.append(worker_info)
        
        # Check if no workers are available
        if not workers:
            return {
                "status": "error",
                "message": "No Celery workers are available",
                "timestamp": datetime.now().isoformat(),
                "workers": []
            }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "workers": workers
        }
    except Exception as e:
        logger.error(f"Error getting Celery worker status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "workers": []
        }

def get_task_status() -> Dict[str, Any]:
    """
    Get current tasks status
    
    Returns:
        dict: Tasks status information
    """
    if DEV_MODE:
        # In development mode, return mock data
        return generate_mock_task_status()
    
    try:
        # Get task information from Celery
        i = celery_app.control.inspect()
        
        active_tasks = i.active() or {}
        scheduled_tasks = i.scheduled() or {}
        reserved_tasks = i.reserved() or {}
        
        # Combine task data
        all_active = []
        for worker_name, tasks in active_tasks.items():
            for task in tasks:
                task['worker'] = worker_name
                task['status'] = 'active'
                all_active.append(task)
        
        all_scheduled = []
        for worker_name, tasks in scheduled_tasks.items():
            for task in tasks:
                task['worker'] = worker_name
                task['status'] = 'scheduled'
                all_scheduled.append(task)
        
        all_reserved = []
        for worker_name, tasks in reserved_tasks.items():
            for task in tasks:
                task['worker'] = worker_name
                task['status'] = 'reserved'
                all_reserved.append(task)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "active": all_active,
            "scheduled": all_scheduled,
            "reserved": all_reserved,
            "total_active": len(all_active),
            "total_scheduled": len(all_scheduled),
            "total_reserved": len(all_reserved)
        }
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "active": [],
            "scheduled": [],
            "reserved": []
        }

def generate_mock_worker_status() -> Dict[str, Any]:
    """
    Generate mock worker status for development
    
    Returns:
        dict: Mock worker status
    """
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "workers": [
            {
                "name": "celery@worker1",
                "status": "online",
                "pid": 12345,
                "concurrency": 4,
                "broker": "redis",
                "uptime": "2 days, 1:23:45",
                "active_tasks": 2,
                "scheduled_tasks": 5,
                "reserved_tasks": 1,
                "processed": 1024
            },
            {
                "name": "celery@worker2",
                "status": "online",
                "pid": 12346,
                "concurrency": 4,
                "broker": "redis",
                "uptime": "1 day, 2:34:56",
                "active_tasks": 1,
                "scheduled_tasks": 3,
                "reserved_tasks": 0,
                "processed": 512
            }
        ]
    }

def generate_mock_task_status() -> Dict[str, Any]:
    """
    Generate mock task status for development
    
    Returns:
        dict: Mock task status
    """
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "active": [
            {
                "id": "8a7d5e0b-e1c3-4d6f-b9a2-f3c7d6e8a9b0",
                "name": "src.app.tasks.video_tasks.process_video",
                "args": ["video_123", ["image1.jpg", "image2.jpg"], "music_track_1"],
                "kwargs": {},
                "worker": "celery@worker1",
                "status": "active",
                "time_start": (datetime.now() - timedelta(minutes=5)).isoformat()
            },
            {
                "id": "7c6b5d4e-f2a1-4b3c-9d8e-7f6a5b4c3d2e",
                "name": "src.app.tasks.video_tasks.process_video",
                "args": ["video_456", ["image3.jpg", "image4.jpg"], "music_track_2"],
                "kwargs": {},
                "worker": "celery@worker1",
                "status": "active",
                "time_start": (datetime.now() - timedelta(minutes=2)).isoformat()
            },
            {
                "id": "6b5a4c3d-2e1f-9a8b-7c6d-5e4f3a2b1c0d",
                "name": "src.app.tasks.runway_tasks.generate_motion",
                "args": ["video_789", "image5.jpg", "cinematic"],
                "kwargs": {},
                "worker": "celery@worker2",
                "status": "active",
                "time_start": (datetime.now() - timedelta(minutes=1)).isoformat()
            }
        ],
        "scheduled": [
            {
                "id": "5e4d3c2b-1a0f-9e8d-7c6b-5a4f3e2d1c0b",
                "name": "src.app.tasks.video_tasks.process_video",
                "args": ["video_101", ["image6.jpg", "image7.jpg"], "music_track_3"],
                "kwargs": {},
                "worker": "celery@worker1",
                "status": "scheduled",
                "eta": (datetime.now() + timedelta(minutes=5)).isoformat()
            }
        ],
        "reserved": [
            {
                "id": "4d3c2b1a-0f9e-8d7c-6b5a-4f3e2d1c0b9a",
                "name": "src.app.tasks.video_tasks.process_video",
                "args": ["video_202", ["image8.jpg", "image9.jpg"], "music_track_4"],
                "kwargs": {},
                "worker": "celery@worker1",
                "status": "reserved"
            }
        ],
        "total_active": 3,
        "total_scheduled": 1,
        "total_reserved": 1
    }

def generate_mock_task_log(task_id: str) -> str:
    """Generate mock task logs for development."""
    return f"""[2023-03-21 10:15:23] [INFO] Task {task_id} started
[2023-03-21 10:15:24] [INFO] Initializing video generation
[2023-03-21 10:15:25] [INFO] Loading music track data
[2023-03-21 10:15:26] [INFO] Analyzing audio with Librosa
[2023-03-21 10:15:30] [INFO] Detected BPM: 128.45
[2023-03-21 10:15:31] [INFO] Extracted 24 beat markers
[2023-03-21 10:15:32] [INFO] Processing uploaded images
[2023-03-21 10:15:35] [INFO] Preparing 8 images for video generation
[2023-03-21 10:15:38] [INFO] Calling RunwayML API for image enhancement
[2023-03-21 10:15:45] [INFO] RunwayML processing complete
[2023-03-21 10:15:46] [INFO] Setting up FFMPEG command
[2023-03-21 10:15:47] [INFO] Starting FFMPEG video generation
[2023-03-21 10:16:02] [INFO] FFMPEG video generation complete
[2023-03-21 10:16:03] [INFO] Adding audio track to video
[2023-03-21 10:16:10] [INFO] Final video rendering complete
[2023-03-21 10:16:11] [INFO] Video saved to output path
[2023-03-21 10:16:12] [INFO] Task {task_id} completed successfully
""" 