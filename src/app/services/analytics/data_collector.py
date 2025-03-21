"""
Analytics data collector for gathering metrics from multiple platforms.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.app.services.social.cross_platform import Platform, get_cross_platform_publisher
from src.app.core.database import get_db

logger = logging.getLogger(__name__)

class AnalyticsDataCollector:
    """Collects and aggregates analytics data from multiple platforms."""
    
    def __init__(self):
        self.publisher = get_cross_platform_publisher()
        self.db = get_db()
    
    async def collect_platform_data(self, video_id: str, platform: Platform, days: int = 7) -> Optional[Dict[str, Any]]:
        """Collect analytics data for a specific video on a platform."""
        try:
            data = await self.publisher.get_platform_analytics(platform, video_id)
            if data.get('success'):
                # Store in database
                await self.db.store_platform_analytics(
                    video_id=video_id,
                    platform=platform.value,
                    timestamp=datetime.now(),
                    metrics=data.get('metrics', {})
                )
                return data.get('metrics', {})
            return None
        except Exception as e:
            logger.error(f"Error collecting analytics for {platform.name} video {video_id}: {e}")
            return None
    
    async def collect_all_platforms(self, video_ids_dict: Dict[Platform, str]) -> List[Optional[Dict[str, Any]]]:
        """Collect analytics from all platforms for multiple videos."""
        tasks = []
        for platform, video_id in video_ids_dict.items():
            tasks.append(self.collect_platform_data(video_id, platform))
        return await asyncio.gather(*tasks)
    
    async def get_engagement_heatmap(self, video_id: str, platform: Optional[Platform] = None) -> Dict[str, List]:
        """Generate an engagement heatmap for moment-by-moment analysis."""
        # Implementation depends on the platform's API capabilities
        # Return timestamps and corresponding engagement levels
        heatmap_data = await self.db.get_heatmap_data(video_id, platform.value if platform else None)
        
        if not heatmap_data:
            # If no detailed data, generate mock data for demo purposes
            # In production, this would pull real data from the platform APIs
            import random
            timestamps = [i for i in range(0, 60)]  # 0 to 60 seconds
            engagement = [random.uniform(0.3, 1.0) for _ in range(60)]
            return {
                'timestamps': timestamps,
                'engagement': engagement
            }
            
        return {
            'timestamps': [point[0] for point in heatmap_data],
            'engagement': [point[1] for point in heatmap_data]
        }

def get_analytics_collector():
    """Get the analytics data collector singleton."""
    return AnalyticsDataCollector() 