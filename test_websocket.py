#!/usr/bin/env python3
"""
WebSocket Testing Script for Analytics Dashboard

This script helps test the WebSocket implementation by sending simulated
analytics updates to connected clients. It connects to the FastAPI server
and broadcasts test data to simulate real-time data updates.
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
import sys
import argparse

import httpx

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("websocket-test")

# Default server URL
DEFAULT_SERVER_URL = "http://localhost:8001"

async def send_test_update(base_url, update_type="dashboard", interval=5, count=10):
    """
    Send test updates to the server to be broadcast over WebSocket.
    
    Args:
        base_url: The base URL of the server
        update_type: The type of update to send (dashboard, recent)
        interval: Seconds between updates
        count: Number of updates to send (0 for infinite)
    """
    url = f"{base_url}/api/test/websocket"
    
    updates_sent = 0
    try:
        while count == 0 or updates_sent < count:
            # Generate random test data based on update type
            if update_type == "dashboard":
                data = generate_dashboard_update()
            elif update_type == "recent":
                data = generate_recent_update()
            else:
                data = {"message": "Test update", "timestamp": datetime.now().isoformat()}
            
            # Add metadata
            payload = {
                "topic": update_type,
                "data": data
            }
            
            # Send update to server
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url, 
                        json=payload,
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        updates_sent += 1
                        logger.info(f"✅ Sent {update_type} update #{updates_sent}")
                        logger.debug(f"Data: {json.dumps(data, indent=2)}")
                    else:
                        logger.error(f"❌ Failed to send update: {response.status_code} - {response.text}")
            
            except Exception as e:
                logger.error(f"❌ Error sending update: {str(e)}")
            
            # Wait before sending next update
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info(f"Test stopped after sending {updates_sent} updates")
        return updates_sent
    
    logger.info(f"Test completed - sent {updates_sent} updates")
    return updates_sent

def generate_dashboard_update():
    """Generate a random dashboard update."""
    # Calculate random changes
    views_change = random.randint(-1000, 3000)
    engagement_change = random.randint(-200, 500)
    watch_time_change = random.uniform(-0.5, 1.5)
    subscribers_change = random.randint(-10, 50)
    
    return {
        "success": True,
        "total_views": random.randint(120000, 150000),
        "total_engagement": random.randint(15000, 25000),
        "engagement_rate": round(random.uniform(0.10, 0.18), 2),
        "avg_watch_time": round(random.uniform(12, 18), 1),
        "total_subscribers": random.randint(6000, 7500),
        "platform_comparison": {
            "platforms": ["YouTube", "TikTok", "Instagram", "Facebook"],
            "views": [
                random.randint(10000, 20000),
                random.randint(30000, 40000),
                random.randint(45000, 55000),
                random.randint(35000, 45000)
            ],
            "engagement": [
                random.randint(2000, 3000),
                random.randint(4500, 6000),
                random.randint(5500, 7000),
                random.randint(4000, 6000)
            ]
        },
        "top_content": generate_top_content(),
        "last_updated": datetime.now().isoformat()
    }

def generate_recent_update():
    """Generate a random recent videos update."""
    now = datetime.now()
    
    # Generate a single new video
    new_video = {
        "id": f"video_{random.randint(1000, 9999)}",
        "title": random.choice([
            "Top 5 iPhone Hacks You Need to Know",
            "Easy Morning Routine for Productivity",
            "How to Cook Perfect Pasta Every Time",
            "Beginner's Guide to Digital Art",
            "10-Minute Full Body Workout",
            "The Best Apps for Students in 2023",
            "How to Build a Website in 30 Minutes"
        ]),
        "thumbnail": f"https://example.com/thumbnails/thumb_{random.randint(1, 20)}.jpg",
        "total_views": random.randint(5000, 25000),
        "total_engagement": random.randint(500, 3500),
        "platforms": [{
            "platform": random.choice(["YouTube", "TikTok", "Instagram", "Facebook"]),
            "views": random.randint(5000, 25000),
            "engagement": random.randint(500, 3500),
            "watch_time": random.randint(40000, 200000),
            "ctr": round(random.uniform(0.02, 0.09), 3)
        }],
        "created_at": (now - timedelta(minutes=random.randint(5, 60))).isoformat()
    }
    
    return {
        "success": True,
        "sessions": [new_video],
        "type": "new_video"
    }

def generate_top_content(count=5):
    """Generate random top content data."""
    top_videos = []
    
    for i in range(count):
        video = {
            "id": f"video_{random.randint(1000, 9999)}",
            "title": random.choice([
                "Top 5 iPhone Hacks You Need to Know",
                "Easy Morning Routine for Productivity",
                "How to Cook Perfect Pasta Every Time",
                "Beginner's Guide to Digital Art",
                "10-Minute Full Body Workout",
                "The Best Apps for Students in 2023",
                "How to Build a Website in 30 Minutes"
            ]),
            "thumbnail": f"https://example.com/thumbnails/thumb_{random.randint(1, 20)}.jpg",
            "total_views": random.randint(10000, 50000),
            "total_engagement": random.randint(1000, 7000),
            "platforms": [{
                "platform": random.choice(["YouTube", "TikTok", "Instagram", "Facebook"]),
                "views": random.randint(10000, 50000),
                "engagement": random.randint(1000, 7000),
                "watch_time": random.randint(80000, 400000),
                "ctr": round(random.uniform(0.02, 0.09), 3)
            }],
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
        }
        top_videos.append(video)
    
    return top_videos

async def main():
    """Main function to parse arguments and run the test."""
    parser = argparse.ArgumentParser(description="Test WebSocket updates for the Analytics Dashboard.")
    parser.add_argument("--server", default=DEFAULT_SERVER_URL, help="Server URL (default: http://localhost:8001)")
    parser.add_argument("--type", choices=["dashboard", "recent", "all"], default="dashboard", help="Type of update to send")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between updates")
    parser.add_argument("--count", type=int, default=10, help="Number of updates to send (0 for infinite)")
    
    args = parser.parse_args()
    
    logger.info(f"Starting WebSocket test for {args.server}")
    logger.info(f"Sending {args.type} updates every {args.interval} seconds")
    
    if args.type == "all":
        # Run both dashboard and recent updates concurrently
        dashboard_task = asyncio.create_task(
            send_test_update(args.server, "dashboard", args.interval, args.count)
        )
        
        # Offset the second task slightly to avoid exact synchronization
        await asyncio.sleep(args.interval / 2)
        
        recent_task = asyncio.create_task(
            send_test_update(args.server, "recent", args.interval, args.count)
        )
        
        # Wait for both tasks to complete
        await asyncio.gather(dashboard_task, recent_task)
    else:
        # Run single update type
        await send_test_update(args.server, args.type, args.interval, args.count)
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 