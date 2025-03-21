"""
Content scheduling service for YouTube Shorts Machine.

This module provides scheduling and bulk processing capabilities
for video creation and publishing across platforms.
"""

import logging
import os
import json
from datetime import datetime, timedelta
import heapq
from typing import Dict, Any, List, Optional, Tuple
import threading
import time
import uuid

logger = logging.getLogger(__name__)

class ContentScheduler:
    """Manages content scheduling and bulk processing for video creation and publishing."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one scheduler instance exists."""
        if cls._instance is None:
            cls._instance = super(ContentScheduler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the content scheduler."""
        if self._initialized:
            return
            
        self._initialized = True
        self.scheduled_tasks = []  # Priority queue for scheduled tasks
        self.task_lock = threading.Lock()
        self.schedule_file = os.path.join(os.path.dirname(__file__), 'data', 'schedule.json')
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.schedule_file), exist_ok=True)
        
        # Load existing schedule if available
        self._load_schedule()
        
        # Start the scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
    def _load_schedule(self):
        """Load scheduled tasks from disk."""
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r') as f:
                    tasks = json.load(f)
                    
                # Convert datetime strings back to datetime objects
                for task in tasks:
                    if 'scheduled_time' in task:
                        task['scheduled_time'] = datetime.fromisoformat(task['scheduled_time'])
                        
                # Rebuild the priority queue
                with self.task_lock:
                    self.scheduled_tasks = []
                    for task in tasks:
                        if 'scheduled_time' in task and isinstance(task['scheduled_time'], datetime):
                            scheduled_timestamp = task['scheduled_time'].timestamp()
                            task_id = task.get('id', str(uuid.uuid4()))
                            heapq.heappush(
                                self.scheduled_tasks, 
                                (scheduled_timestamp, task_id, task)
                            )
                            
                logger.info(f"Loaded {len(tasks)} scheduled tasks")
            else:
                logger.info("No schedule file found, starting with empty schedule")
        except Exception as e:
            logger.error(f"Error loading schedule: {e}")
            self.scheduled_tasks = []
            
    def _save_schedule(self):
        """Save scheduled tasks to disk."""
        try:
            tasks = []
            with self.task_lock:
                # Convert to list and handle datetime serialization
                for _, _, task in self.scheduled_tasks:
                    task_copy = task.copy()
                    if 'scheduled_time' in task_copy and isinstance(task_copy['scheduled_time'], datetime):
                        task_copy['scheduled_time'] = task_copy['scheduled_time'].isoformat()
                    tasks.append(task_copy)
                    
            with open(self.schedule_file, 'w') as f:
                json.dump(tasks, f, indent=2)
                
            logger.debug(f"Saved {len(tasks)} scheduled tasks")
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
            
    def _scheduler_loop(self):
        """Main scheduler loop that processes due tasks."""
        while self.running:
            now = datetime.now()
            tasks_to_run = []
            
            # Find tasks that are due
            with self.task_lock:
                while self.scheduled_tasks and self.scheduled_tasks[0][0] <= now.timestamp():
                    _, _, task = heapq.heappop(self.scheduled_tasks)
                    tasks_to_run.append(task)
            
            # Process due tasks
            for task in tasks_to_run:
                self._process_task(task)
            
            # Save schedule after processing
            if tasks_to_run:
                self._save_schedule()
                
            # Sleep for a short while before checking again
            time.sleep(10)
            
    def _process_task(self, task: Dict[str, Any]):
        """
        Process a scheduled task.
        
        Args:
            task: The task to process
        """
        task_type = task.get('type')
        task_id = task.get('id')
        logger.info(f"Processing scheduled task: {task_id} ({task_type})")
        
        try:
            if task_type == 'create_video':
                # Code to create video would go here
                # This would typically call the appropriate service
                pass
                
            elif task_type == 'publish_video':
                # Code to publish video would go here
                # This would typically call the appropriate service
                video_id = task.get('video_id')
                platforms = task.get('platforms', ['youtube'])
                
                logger.info(f"Publishing video {video_id} to platforms: {platforms}")
                # Call to video publishing service would go here
                
            elif task_type == 'batch_process':
                # Process a batch of videos
                batch_id = task.get('batch_id')
                self._process_batch(batch_id)
                
            else:
                logger.warning(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            # Update task status to failed
            task['status'] = 'failed'
            task['error'] = str(e)
        else:
            # Update task status to completed
            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            
    def _process_batch(self, batch_id: str):
        """
        Process a batch of videos.
        
        Args:
            batch_id: ID of the batch to process
        """
        logger.info(f"Processing batch: {batch_id}")
        # Implementation would depend on how batches are stored and processed
        
    def schedule_task(self, task_data: Dict[str, Any], scheduled_time: datetime) -> str:
        """
        Schedule a task for future execution.
        
        Args:
            task_data: The task data
            scheduled_time: When to execute the task
            
        Returns:
            Task ID
        """
        # Generate a task ID if not provided
        if 'id' not in task_data:
            task_data['id'] = str(uuid.uuid4())
            
        # Add scheduling metadata
        task_data['scheduled_time'] = scheduled_time
        task_data['created_at'] = datetime.now().isoformat()
        task_data['status'] = 'scheduled'
        
        # Add to schedule queue with a tiebreaker to avoid dict vs dict comparison
        scheduled_timestamp = scheduled_time.timestamp()
        task_id = task_data['id']
        
        with self.task_lock:
            heapq.heappush(
                self.scheduled_tasks,
                (scheduled_timestamp, task_id, task_data)
            )
            
        # Save updated schedule
        self._save_schedule()
        
        logger.info(f"Scheduled task {task_data['id']} for {scheduled_time.isoformat()}")
        return task_data['id']
        
    def schedule_video_creation(self, 
                              video_data: Dict[str, Any], 
                              scheduled_time: datetime) -> str:
        """
        Schedule video creation for a future time.
        
        Args:
            video_data: Video creation parameters
            scheduled_time: When to create the video
            
        Returns:
            Task ID
        """
        task = {
            'type': 'create_video',
            'video_data': video_data
        }
        return self.schedule_task(task, scheduled_time)
        
    def schedule_video_publishing(self, 
                                video_id: str, 
                                platforms: List[str], 
                                scheduled_time: datetime) -> str:
        """
        Schedule video publishing for a future time.
        
        Args:
            video_id: ID of the video to publish
            platforms: Platforms to publish to
            scheduled_time: When to publish the video
            
        Returns:
            Task ID
        """
        task = {
            'type': 'publish_video',
            'video_id': video_id,
            'platforms': platforms
        }
        return self.schedule_task(task, scheduled_time)
        
    def create_batch(self, batch_items: List[Dict[str, Any]]) -> str:
        """
        Create a batch of videos to be processed.
        
        Args:
            batch_items: List of video creation parameters
            
        Returns:
            Batch ID
        """
        batch_id = str(uuid.uuid4())
        
        # Create a batch directory to store batch data
        batch_dir = os.path.join(os.path.dirname(self.schedule_file), 'batches')
        os.makedirs(batch_dir, exist_ok=True)
        
        batch_file = os.path.join(batch_dir, f'{batch_id}.json')
        
        # Save batch data
        batch_data = {
            'id': batch_id,
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
            'items': batch_items,
            'progress': {
                'total': len(batch_items),
                'completed': 0,
                'failed': 0
            }
        }
        
        with open(batch_file, 'w') as f:
            json.dump(batch_data, f, indent=2)
            
        logger.info(f"Created batch {batch_id} with {len(batch_items)} items")
        return batch_id
        
    def schedule_batch_processing(self, batch_id: str, scheduled_time: datetime) -> str:
        """
        Schedule a batch for processing at a future time.
        
        Args:
            batch_id: ID of the batch to process
            scheduled_time: When to process the batch
            
        Returns:
            Task ID
        """
        task = {
            'type': 'batch_process',
            'batch_id': batch_id
        }
        return self.schedule_task(task, scheduled_time)
        
    def get_scheduled_tasks(self, 
                          from_date: Optional[datetime] = None, 
                          to_date: Optional[datetime] = None, 
                          task_type: Optional[str] = None, 
                          status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get scheduled tasks filtered by criteria.
        
        Args:
            from_date: Start date for filtering
            to_date: End date for filtering
            task_type: Filter by task type
            status: Filter by task status
            
        Returns:
            List of tasks matching criteria
        """
        tasks = []
        
        with self.task_lock:
            for _, _, task in self.scheduled_tasks:
                # Apply filters
                if from_date and task['scheduled_time'] < from_date:
                    continue
                    
                if to_date and task['scheduled_time'] > to_date:
                    continue
                    
                if task_type and task.get('type') != task_type:
                    continue
                    
                if status and task.get('status') != status:
                    continue
                    
                # Create a copy with properly formatted datetime
                task_copy = task.copy()
                if 'scheduled_time' in task_copy:
                    task_copy['scheduled_time'] = task_copy['scheduled_time'].isoformat()
                    
                tasks.append(task_copy)
                
        return tasks
        
    def get_optimal_publishing_times(self, 
                                   platform: str = 'youtube', 
                                   days_ahead: int = 7) -> List[datetime]:
        """
        Get optimal times for publishing content based on platform and engagement data.
        
        Args:
            platform: Target platform
            days_ahead: Number of days to look ahead
            
        Returns:
            List of suggested publishing times
        """
        # In a real implementation, this would analyze historical engagement data
        # to find optimal publishing times. For now, we'll use some basic heuristics.
        
        now = datetime.now()
        optimal_times = []
        
        # YouTube optimal times (simplified heuristic)
        if platform == 'youtube':
            # Add times for the requested number of days
            for day in range(days_ahead):
                target_date = now.date() + timedelta(days=day)
                
                # YouTube peak times (simplified): 
                # Weekdays: 3-4pm, 7-10pm
                # Weekends: 10-11am, 7-9pm
                
                is_weekend = target_date.weekday() >= 5  # 5=Saturday, 6=Sunday
                
                if is_weekend:
                    # Weekend times
                    morning_time = datetime.combine(target_date, datetime.min.time().replace(hour=10, minute=30))
                    evening_time = datetime.combine(target_date, datetime.min.time().replace(hour=20, minute=0))
                    
                    optimal_times.append(morning_time)
                    optimal_times.append(evening_time)
                else:
                    # Weekday times
                    afternoon_time = datetime.combine(target_date, datetime.min.time().replace(hour=15, minute=30))
                    evening_time = datetime.combine(target_date, datetime.min.time().replace(hour=19, minute=0))
                    
                    optimal_times.append(afternoon_time)
                    optimal_times.append(evening_time)
                    
        # Filter out times in the past
        optimal_times = [t for t in optimal_times if t > now]
        
        return optimal_times
        
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was canceled, False otherwise
        """
        with self.task_lock:
            # Find and remove the task
            for i, (timestamp, id_str, task) in enumerate(self.scheduled_tasks):
                if task.get('id') == task_id:
                    task['status'] = 'canceled'
                    
                    # Rebuild the heap without this task
                    self.scheduled_tasks = [
                        (ts, tid, t) for ts, tid, t in self.scheduled_tasks
                        if t.get('id') != task_id
                    ]
                    heapq.heapify(self.scheduled_tasks)
                    
                    # Save the updated schedule
                    self._save_schedule()
                    
                    logger.info(f"Canceled task {task_id}")
                    return True
                    
        logger.warning(f"Task {task_id} not found for cancellation")
        return False
        
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get the status of a batch.
        
        Args:
            batch_id: ID of the batch
            
        Returns:
            Batch status information
        """
        batch_file = os.path.join(
            os.path.dirname(self.schedule_file), 
            'batches', 
            f'{batch_id}.json'
        )
        
        if not os.path.exists(batch_file):
            return {
                'status': 'not_found',
                'message': f'Batch {batch_id} not found'
            }
            
        try:
            with open(batch_file, 'r') as f:
                batch_data = json.load(f)
                
            return batch_data
        except Exception as e:
            logger.error(f"Error loading batch {batch_id}: {e}")
            return {
                'status': 'error',
                'message': f'Error loading batch data: {e}'
            }
    
    def shutdown(self):
        """Stop the scheduler thread and save the current schedule."""
        logger.info("Shutting down content scheduler")
        self.running = False
        if self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=1.0)
        self._save_schedule()


def get_content_scheduler() -> ContentScheduler:
    """Get the singleton instance of the content scheduler."""
    return ContentScheduler() 