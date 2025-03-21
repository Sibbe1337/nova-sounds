"""
Test script for content scheduling and batch processing.

This script tests the functionality of the scheduler service,
including scheduling tasks, batch processing, and optimal time selection.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.services.scheduler import get_content_scheduler

def test_schedule_task():
    """Test scheduling a task for future execution."""
    print("\n=== Testing Schedule Task ===")
    
    scheduler = get_content_scheduler()
    
    # Create a task for 1 hour in the future
    scheduled_time = datetime.now() + timedelta(hours=1)
    task_data = {
        'type': 'test_task',
        'data': 'test_data',
        'priority': 'high'
    }
    
    print(f"Scheduling task for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
    task_id = scheduler.schedule_task(task_data, scheduled_time)
    
    print(f"Task scheduled with ID: {task_id}")
    
    # Verify the task is in the scheduled tasks
    tasks = scheduler.get_scheduled_tasks()
    
    found = False
    for task in tasks:
        if task.get('id') == task_id:
            found = True
            print(f"Task found in scheduled tasks:")
            print(f"  - ID: {task.get('id')}")
            print(f"  - Type: {task.get('type')}")
            print(f"  - Status: {task.get('status')}")
            print(f"  - Scheduled time: {task.get('scheduled_time')}")
            break
    
    if not found:
        print("Error: Task not found in scheduled tasks")
    
    print("Schedule task test completed.")
    
    return task_id

def test_cancel_task(task_id: str):
    """Test canceling a scheduled task."""
    print("\n=== Testing Cancel Task ===")
    
    scheduler = get_content_scheduler()
    
    print(f"Canceling task with ID: {task_id}")
    success = scheduler.cancel_task(task_id)
    
    if success:
        print(f"Task {task_id} successfully canceled")
    else:
        print(f"Error: Failed to cancel task {task_id}")
    
    # Verify the task is removed from scheduled tasks
    tasks = scheduler.get_scheduled_tasks()
    
    found = False
    for task in tasks:
        if task.get('id') == task_id:
            found = True
            print(f"Error: Task still found in scheduled tasks with status: {task.get('status')}")
            break
    
    if not found:
        print("Task successfully removed from scheduled tasks")
    
    print("Cancel task test completed.")

def test_batch_processing():
    """Test creating and scheduling a batch for processing."""
    print("\n=== Testing Batch Processing ===")
    
    scheduler = get_content_scheduler()
    
    # Create batch items (video creation parameters)
    batch_items = [
        {
            'title': 'Batch Video 1',
            'description': 'Test batch video 1',
            'music_id': 'music_1',
            'preset': 'standard'
        },
        {
            'title': 'Batch Video 2',
            'description': 'Test batch video 2',
            'music_id': 'music_2',
            'preset': 'energetic'
        },
        {
            'title': 'Batch Video 3',
            'description': 'Test batch video 3',
            'music_id': 'music_3',
            'preset': 'cinematic'
        }
    ]
    
    print(f"Creating batch with {len(batch_items)} items")
    batch_id = scheduler.create_batch(batch_items)
    
    print(f"Batch created with ID: {batch_id}")
    
    # Get batch status
    status = scheduler.get_batch_status(batch_id)
    
    print(f"Batch status:")
    print(f"  - ID: {status.get('id')}")
    print(f"  - Status: {status.get('status')}")
    print(f"  - Items: {status.get('progress', {}).get('total')} total")
    print(f"  - Created at: {status.get('created_at')}")
    
    # Schedule batch for processing
    scheduled_time = datetime.now() + timedelta(hours=2)
    
    print(f"Scheduling batch for processing at {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
    task_id = scheduler.schedule_batch_processing(batch_id, scheduled_time)
    
    print(f"Batch scheduled with task ID: {task_id}")
    
    # Verify the task is in the scheduled tasks
    tasks = scheduler.get_scheduled_tasks(task_type='batch_process')
    
    found = False
    for task in tasks:
        if task.get('id') == task_id:
            found = True
            print(f"Batch task found in scheduled tasks:")
            print(f"  - ID: {task.get('id')}")
            print(f"  - Type: {task.get('type')}")
            print(f"  - Batch ID: {task.get('batch_id')}")
            print(f"  - Status: {task.get('status')}")
            print(f"  - Scheduled time: {task.get('scheduled_time')}")
            break
    
    if not found:
        print("Error: Batch task not found in scheduled tasks")
    
    print("Batch processing test completed.")
    
    return task_id, batch_id

def test_optimal_publishing_times():
    """Test getting optimal publishing times for different platforms."""
    print("\n=== Testing Optimal Publishing Times ===")
    
    scheduler = get_content_scheduler()
    
    platforms = ['youtube', 'tiktok', 'instagram', 'facebook']
    days_ahead = 3
    
    for platform in platforms:
        print(f"\nOptimal publishing times for {platform.upper()} (next {days_ahead} days):")
        
        times = scheduler.get_optimal_publishing_times(platform, days_ahead)
        
        if times:
            for i, time in enumerate(times):
                print(f"  {i+1}. {time.strftime('%Y-%m-%d %H:%M:%S')} ({time.strftime('%A')})")
        else:
            print("  No optimal times found")
    
    print("Optimal publishing times test completed.")

def test_filtered_tasks():
    """Test filtering scheduled tasks by various criteria."""
    print("\n=== Testing Task Filtering ===")
    
    scheduler = get_content_scheduler()
    
    # Create a few tasks with different types and times
    now = datetime.now()
    
    task_types = ['video_creation', 'video_publishing', 'batch_process']
    statuses = ['scheduled', 'completed', 'failed']
    
    # Schedule some test tasks
    for i in range(5):
        task_type = task_types[i % len(task_types)]
        status = statuses[i % len(statuses)]
        scheduled_time = now + timedelta(hours=i+1)
        
        task_data = {
            'type': task_type,
            'status': status,
            'test_index': i
        }
        
        scheduler.schedule_task(task_data, scheduled_time)
    
    # Test filtering by task type
    print("\nFiltering tasks by type:")
    for task_type in task_types:
        tasks = scheduler.get_scheduled_tasks(task_type=task_type)
        print(f"  Tasks of type '{task_type}': {len(tasks)}")
    
    # Test filtering by status
    print("\nFiltering tasks by status:")
    for status in statuses:
        tasks = scheduler.get_scheduled_tasks(status=status)
        print(f"  Tasks with status '{status}': {len(tasks)}")
    
    # Test filtering by date range
    from_date = now
    to_date = now + timedelta(hours=3)
    
    print(f"\nFiltering tasks by date range ({from_date.strftime('%H:%M')} to {to_date.strftime('%H:%M')}):")
    tasks = scheduler.get_scheduled_tasks(from_date=from_date, to_date=to_date)
    print(f"  Tasks in date range: {len(tasks)}")
    
    # Clean up test tasks (would normally use cancel_task, but for testing we'll just verify filtering)
    print("\nFiltering test completed.")

def main():
    """Run all tests."""
    print("=== Content Scheduling and Batch Processing Tests ===")
    
    # Test scheduling and canceling a task
    task_id = test_schedule_task()
    test_cancel_task(task_id)
    
    # Test batch processing
    batch_task_id, batch_id = test_batch_processing()
    
    # Test optimal publishing times
    test_optimal_publishing_times()
    
    # Test task filtering
    test_filtered_tasks()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main() 