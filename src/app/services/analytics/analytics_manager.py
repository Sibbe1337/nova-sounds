"""
Analytics manager for handling dashboard data and analytics functionality.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.app.services.analytics.data_collector import get_analytics_collector
from src.app.services.social.cross_platform import Platform
from src.app.core.database import get_db
from src.app.core.settings import DEV_MODE

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Manages analytics data and provides dashboard metrics."""
    
    def __init__(self):
        self.collector = get_analytics_collector()
        self.db = get_db()
    
    async def get_dashboard_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get aggregated dashboard data for a user."""
        try:
            # Get user's videos across all platforms
            videos = await self.db.get_user_videos(user_id)
            
            if not videos and DEV_MODE:
                # Generate sample data in development mode
                return self._generate_sample_dashboard()
            
            # Collect recent analytics for all videos
            platform_stats = {}
            total_views = 0
            total_engagement = 0
            total_watch_time = 0
            video_analytics = []
            
            for video in videos:
                # Collect data for this video on all its platforms
                video_platforms = {}
                for platform in video["platforms"]:
                    platform_enum = Platform[platform.upper()]
                    video_platforms[platform_enum] = video["platform_ids"][platform]
                
                analytics = await self.collector.collect_all_platforms(video_platforms)
                
                # Process analytics for each platform
                video_total_views = 0
                video_total_engagement = 0
                video_platforms_data = []
                
                for platform, platform_analytics in zip(video_platforms.keys(), analytics):
                    if platform_analytics:
                        # Add to platform totals
                        if platform.name not in platform_stats:
                            platform_stats[platform.name] = {
                                "views": 0,
                                "engagement": 0,
                                "watch_time": 0,
                                "videos": 0
                            }
                        
                        views = platform_analytics.get("views", 0)
                        engagement = platform_analytics.get("likes", 0) + platform_analytics.get("comments", 0) + platform_analytics.get("shares", 0)
                        watch_time = platform_analytics.get("watch_time", 0)
                        
                        platform_stats[platform.name]["views"] += views
                        platform_stats[platform.name]["engagement"] += engagement
                        platform_stats[platform.name]["watch_time"] += watch_time
                        platform_stats[platform.name]["videos"] += 1
                        
                        # Add to video totals
                        video_total_views += views
                        video_total_engagement += engagement
                        
                        # Add to overall totals
                        total_views += views
                        total_engagement += engagement
                        total_watch_time += watch_time
                        
                        # Add platform data for this video
                        video_platforms_data.append({
                            "platform": platform.name,
                            "views": views,
                            "engagement": engagement,
                            "watch_time": watch_time,
                            "ctr": platform_analytics.get("ctr", 0)
                        })
                
                # Add this video's analytics to the list
                if video_total_views > 0:
                    video_analytics.append({
                        "id": video["id"],
                        "title": video["title"],
                        "thumbnail": video["thumbnail"],
                        "total_views": video_total_views,
                        "total_engagement": video_total_engagement,
                        "platforms": video_platforms_data,
                        "created_at": video["created_at"]
                    })
            
            # Sort videos by total views
            video_analytics.sort(key=lambda x: x["total_views"], reverse=True)
            
            # Calculate platform comparison data
            platform_comparison = {
                "platforms": list(platform_stats.keys()),
                "views": [platform_stats[p]["views"] for p in platform_stats],
                "engagement": [platform_stats[p]["engagement"] for p in platform_stats]
            }
            
            # Calculate overall engagement rate
            engagement_rate = 0
            if total_views > 0:
                engagement_rate = total_engagement / total_views
            
            # Get subscriber count (this would come from platform APIs)
            subscribers = await self._get_total_subscribers(user_id)
            
            # Generate content recommendations
            recommendations = await self._generate_recommendations(video_analytics)
            
            return {
                "success": True,
                "total_views": total_views,
                "total_engagement": total_engagement,
                "engagement_rate": engagement_rate,
                "avg_watch_time": total_watch_time / len(videos) if videos else 0,
                "total_subscribers": subscribers,
                "platform_comparison": platform_comparison,
                "top_content": video_analytics[:5],  # Top 5 videos
                "videos": video_analytics,
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"Error getting analytics dashboard data: {e}")
            if DEV_MODE:
                return self._generate_sample_dashboard()
            return {"success": False, "error": str(e)}
    
    async def get_video_analytics(self, video_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific video."""
        try:
            # Get video data
            video = await self.db.get_video(video_id, user_id)
            
            if not video and DEV_MODE:
                # Generate sample data in development mode
                return self._generate_sample_video_analytics(video_id)
            
            if not video:
                return {"success": False, "error": "Video not found"}
            
            # Collect data for this video on all its platforms
            video_platforms = {}
            for platform in video["platforms"]:
                platform_enum = Platform[platform.upper()]
                video_platforms[platform_enum] = video["platform_ids"][platform]
            
            analytics = await self.collector.collect_all_platforms(video_platforms)
            
            # Process analytics for each platform
            platforms_data = []
            for platform, platform_analytics in zip(video_platforms.keys(), analytics):
                if platform_analytics:
                    platforms_data.append({
                        "platform": platform.name,
                        "views": platform_analytics.get("views", 0),
                        "likes": platform_analytics.get("likes", 0),
                        "comments": platform_analytics.get("comments", 0),
                        "shares": platform_analytics.get("shares", 0),
                        "watch_time": platform_analytics.get("watch_time", 0),
                        "ctr": platform_analytics.get("ctr", 0),
                        "retention": platform_analytics.get("retention", {})
                    })
            
            # Get engagement heatmap
            heatmap = await self.collector.get_engagement_heatmap(video_id)
            
            # Get historical data for trends
            historical_data = await self.db.get_historical_analytics(video_id, days=30)
            
            # If no historical data, generate sample data in development mode
            if not historical_data and DEV_MODE:
                historical_data = self._generate_sample_historical_data()
            
            return {
                "success": True,
                "video": {
                    "id": video["id"],
                    "title": video["title"],
                    "thumbnail": video["thumbnail"],
                    "created_at": video["created_at"],
                    "duration": video["duration"]
                },
                "platforms": platforms_data,
                "heatmap": heatmap,
                "historical_data": historical_data
            }
        except Exception as e:
            logger.error(f"Error getting video analytics: {e}")
            if DEV_MODE:
                return self._generate_sample_video_analytics(video_id)
            return {"success": False, "error": str(e)}
    
    async def get_content_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get content trends based on analytics data."""
        try:
            # Get trending data from database
            trends = await self.db.get_content_trends(days)
            
            if not trends and DEV_MODE:
                # Generate sample trends in development mode
                return self._generate_sample_trends()
            
            return {
                "success": True,
                "trends": trends
            }
        except Exception as e:
            logger.error(f"Error getting content trends: {e}")
            if DEV_MODE:
                return self._generate_sample_trends()
            return {"success": False, "error": str(e)}
    
    async def get_recent_generations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent video generation sessions for a user."""
        try:
            # Attempt to get recent sessions from database
            sessions = await self.db.get_recent_sessions(user_id, limit)
            
            if not sessions and DEV_MODE:
                # In development mode, generate sample data
                return self._generate_sample_recent_generations(limit)
            
            return sessions
        except Exception as e:
            logger.error(f"Error getting recent generations: {e}")
            if DEV_MODE:
                return self._generate_sample_recent_generations(limit)
            return []
    
    async def _get_total_subscribers(self, user_id: str) -> int:
        """Get total subscriber count across all platforms."""
        try:
            # In a real implementation, this would query platform APIs
            # For now, return dummy data or from database
            return await self.db.get_subscriber_count(user_id) or 1000
        except Exception as e:
            logger.error(f"Error getting subscriber count: {e}")
            return 1000 if DEV_MODE else 0
    
    async def _generate_recommendations(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate content recommendations based on analytics data."""
        try:
            # In a real implementation, this would use AI to analyze patterns
            # For now, generate simple recommendations
            recommendations = []
            
            if videos:
                # Recommend based on best performing platform
                platform_performance = {}
                for video in videos:
                    for platform_data in video.get("platforms", []):
                        platform = platform_data["platform"]
                        if platform not in platform_performance:
                            platform_performance[platform] = 0
                        platform_performance[platform] += platform_data["views"]
                
                # Find best platform
                best_platform = max(platform_performance.items(), key=lambda x: x[1])[0] if platform_performance else None
                
                if best_platform:
                    recommendations.append({
                        "type": "platform_focus",
                        "title": f"Focus on {best_platform}",
                        "description": f"Your content performs best on {best_platform}. Consider prioritizing this platform.",
                        "confidence": 0.85
                    })
            
            # Add some generic recommendations
            recommendations.append({
                "type": "content_length",
                "title": "Optimize video length",
                "description": "Videos between 15-30 seconds have the highest completion rate.",
                "confidence": 0.75
            })
            
            recommendations.append({
                "type": "posting_time",
                "title": "Best posting times",
                "description": "Post between 6-8 PM for maximum reach and engagement.",
                "confidence": 0.8
            })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _generate_sample_dashboard(self) -> Dict[str, Any]:
        """Generate sample dashboard data for development mode."""
        import random
        
        # Sample platform data
        platforms = ["YouTube", "TikTok", "Instagram", "Facebook"]
        
        # Generate random views for each platform
        views = [random.randint(5000, 50000) for _ in platforms]
        
        # Generate random engagement for each platform (10-20% of views)
        engagement = [int(views[i] * random.uniform(0.1, 0.2)) for i in range(len(platforms))]
        
        # Sample video titles
        video_titles = [
            "How to Make Perfect Coffee Every Time",
            "5 Exercises for a Strong Core",
            "Quick Home Office Setup Guide",
            "Easy 10-Minute Healthy Breakfast",
            "Top 3 Productivity Tips",
            "Weekend Travel Ideas on a Budget",
            "How I Organized My Entire Home"
        ]
        
        # Generate sample videos
        videos = []
        for i in range(min(len(video_titles), 5)):
            video_views = random.randint(1000, 20000)
            video_engagement = int(video_views * random.uniform(0.1, 0.2))
            
            # Generate platform data for this video
            video_platforms = []
            for j in range(random.randint(1, len(platforms))):
                platform = platforms[j]
                platform_views = int(video_views * random.uniform(0.3, 1.0))
                platform_engagement = int(platform_views * random.uniform(0.1, 0.2))
                
                video_platforms.append({
                    "platform": platform,
                    "views": platform_views,
                    "engagement": platform_engagement,
                    "watch_time": int(platform_views * random.uniform(5, 15)),
                    "ctr": random.uniform(0.02, 0.1)
                })
            
            videos.append({
                "id": f"video_{i+1}",
                "title": video_titles[i],
                "thumbnail": f"https://example.com/thumbnails/thumb_{i+1}.jpg",
                "total_views": video_views,
                "total_engagement": video_engagement,
                "platforms": video_platforms,
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            })
        
        # Sort by total views
        videos.sort(key=lambda x: x["total_views"], reverse=True)
        
        return {
            "success": True,
            "total_views": sum(views),
            "total_engagement": sum(engagement),
            "engagement_rate": sum(engagement) / sum(views) if sum(views) > 0 else 0,
            "avg_watch_time": random.uniform(8, 18),
            "total_subscribers": random.randint(1000, 10000),
            "platform_comparison": {
                "platforms": platforms,
                "views": views,
                "engagement": engagement
            },
            "top_content": videos,
            "videos": videos,
            "recommendations": [
                {
                    "type": "platform_focus",
                    "title": "Focus on TikTok",
                    "description": "Your content performs best on TikTok. Consider prioritizing this platform.",
                    "confidence": 0.85
                },
                {
                    "type": "content_length",
                    "title": "Optimize video length",
                    "description": "Videos between 15-30 seconds have the highest completion rate.",
                    "confidence": 0.75
                },
                {
                    "type": "posting_time",
                    "title": "Best posting times",
                    "description": "Post between 6-8 PM for maximum reach and engagement.",
                    "confidence": 0.8
                }
            ]
        }
    
    def _generate_sample_video_analytics(self, video_id: str) -> Dict[str, Any]:
        """Generate sample video analytics for development mode."""
        import random
        
        # Sample platforms
        platforms = ["YouTube", "TikTok", "Instagram"]
        
        # Generate platform data
        platforms_data = []
        for platform in platforms:
            views = random.randint(1000, 10000)
            likes = int(views * random.uniform(0.05, 0.15))
            comments = int(views * random.uniform(0.01, 0.05))
            shares = int(views * random.uniform(0.01, 0.03))
            
            # Generate retention data (percentage of viewers at each point)
            retention_points = 10
            retention = {
                str(i * 10): max(0, 100 - i * random.uniform(5, 10))
                for i in range(retention_points)
            }
            
            platforms_data.append({
                "platform": platform,
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "watch_time": int(views * random.uniform(5, 15)),
                "ctr": random.uniform(0.02, 0.1),
                "retention": retention
            })
        
        # Generate engagement heatmap
        timestamps = [i for i in range(0, 60)]  # 0 to 60 seconds
        engagement = [random.uniform(0.3, 1.0) for _ in range(60)]
        
        return {
            "success": True,
            "video": {
                "id": video_id,
                "title": "Sample Video Title",
                "thumbnail": "https://example.com/thumbnails/sample.jpg",
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "duration": 60
            },
            "platforms": platforms_data,
            "heatmap": {
                "timestamps": timestamps,
                "engagement": engagement
            },
            "historical_data": self._generate_sample_historical_data()
        }
    
    def _generate_sample_historical_data(self) -> List[Dict[str, Any]]:
        """Generate sample historical data for trends."""
        import random
        
        # Generate data for last 30 days
        days = 30
        start_date = datetime.now() - timedelta(days=days)
        
        # Start values
        views_start = random.randint(100, 500)
        engagement_start = int(views_start * random.uniform(0.1, 0.2))
        
        # Generate daily data with natural growth trend
        data = []
        for i in range(days):
            # Calculate date
            date = (start_date + timedelta(days=i)).isoformat()
            
            # Random growth factor (0.8 to 1.2)
            growth = random.uniform(0.8, 1.2)
            
            # Calculate views with growth
            views = int(views_start * (1 + i * 0.05) * growth)
            
            # Calculate engagement (10-20% of views)
            engagement = int(views * random.uniform(0.1, 0.2))
            
            data.append({
                "date": date,
                "views": views,
                "engagement": engagement,
                "watch_time": int(views * random.uniform(5, 15))
            })
        
        return data
    
    def _generate_sample_trends(self) -> Dict[str, Any]:
        """Generate sample trend data for development mode."""
        return {
            "hashtags": [
                {"tag": "#shorts", "volume": 1000000, "growth": 5.2},
                {"tag": "#tiktoktrend", "volume": 850000, "growth": 7.8},
                {"tag": "#cooking", "volume": 750000, "growth": 3.1},
                {"tag": "#fitness", "volume": 720000, "growth": 4.5},
                {"tag": "#travel", "volume": 680000, "growth": 2.3}
            ],
            "content_types": [
                {"type": "Tutorial", "engagement": 0.18, "growth": 6.2},
                {"type": "Day in the Life", "engagement": 0.16, "growth": 8.1},
                {"type": "Product Review", "engagement": 0.15, "growth": 4.3},
                {"type": "Challenge", "engagement": 0.14, "growth": 7.5},
                {"type": "Comedy", "engagement": 0.13, "growth": 5.8}
            ],
            "optimal_times": [
                {"day": "Monday", "time": "18:00", "engagement_factor": 1.2},
                {"day": "Wednesday", "time": "19:30", "engagement_factor": 1.3},
                {"day": "Friday", "time": "20:00", "engagement_factor": 1.4},
                {"day": "Saturday", "time": "12:30", "engagement_factor": 1.25},
                {"day": "Sunday", "time": "11:00", "engagement_factor": 1.15}
            ]
        }
    
    def _generate_sample_recent_generations(self, limit: int) -> List[Dict[str, Any]]:
        """Generate sample recent generation sessions for development."""
        import random
        
        presets = ["Electronic", "Cinematic", "Standard", "Pop", "Hip Hop"]
        statuses = ["completed", "completed", "completed", "completed", "failed"]
        
        sessions = []
        for i in range(1, limit + 1):
            session_id = f"VID-{8421 - i}"
            created_at = datetime.now() - timedelta(days=i // 2, hours=i % 2)
            preset = random.choice(presets)
            status = random.choice(statuses)
            duration = random.randint(30, 120)
            processing_time = round(random.uniform(1.5, 8.0), 1)
            
            sessions.append({
                "id": session_id,
                "created_at": created_at.isoformat(),
                "preset": preset,
                "duration": duration,
                "processing_time": processing_time,
                "status": status
            })
        
        return sessions

# Singleton instance
_manager = None

def get_analytics_manager():
    """Get the analytics manager singleton."""
    global _manager
    if _manager is None:
        _manager = AnalyticsManager()
    return _manager 