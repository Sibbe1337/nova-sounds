"""
Celery configuration for task processing.
"""
from celery import Celery
import os
from src.app.core.settings import DEV_MODE

# Initialize Celery app
app = Celery(
    'youtube_shorts',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    include=['src.app.tasks.video_tasks']
)

# Configure Celery settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # In development mode, run tasks immediately (no task queue)
    task_always_eager=DEV_MODE
) 