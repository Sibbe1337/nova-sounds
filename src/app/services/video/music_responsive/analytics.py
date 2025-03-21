"""
Analytics module for music-responsive video generation.

This module provides functionality to track and analyze the usage of the
music-responsive video generator, including performance metrics and feature usage.
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading
import uuid

# Set up logging
logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Manages analytics for music-responsive video generation."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, analytics_dir: Optional[str] = None):
        """Singleton pattern to ensure only one analytics manager exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AnalyticsManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, analytics_dir: Optional[str] = None):
        """
        Initialize the analytics manager.
        
        Args:
            analytics_dir: Directory to store analytics data (default: './analytics')
        """
        if self._initialized:
            return
            
        self.analytics_dir = analytics_dir or os.path.join(os.path.dirname(__file__), 'analytics')
        os.makedirs(self.analytics_dir, exist_ok=True)
        
        self.current_sessions = {}
        self.analytics_file = os.path.join(self.analytics_dir, 'generation_metrics.json')
        self.platform_analytics_file = os.path.join(self.analytics_dir, 'platform_metrics.json')
        self._initialized = True
        
        # Ensure analytics files exist
        if not os.path.exists(self.analytics_file):
            with open(self.analytics_file, 'w') as f:
                json.dump([], f)
                
        if not os.path.exists(self.platform_analytics_file):
            with open(self.platform_analytics_file, 'w') as f:
                json.dump([], f)
    
    def start_session(self, preset_name: str, effect_intensity: float, 
                    duration: int, image_count: int, use_smooth_transitions: bool) -> str:
        """
        Start tracking a new video generation session.
        
        Args:
            preset_name: Name of the preset being used
            effect_intensity: Intensity level of effects
            duration: Target duration in seconds
            image_count: Number of images used
            use_smooth_transitions: Whether smooth transitions are enabled
            
        Returns:
            Session ID for the generation session
        """
        session_id = str(uuid.uuid4())
        
        self.current_sessions[session_id] = {
            "session_id": session_id,
            "preset": preset_name,
            "effect_intensity": effect_intensity,
            "duration": duration,
            "image_count": image_count,
            "use_smooth_transitions": use_smooth_transitions,
            "start_time": time.time(),
            "effects_used": [],
            "music_features_analyzed": [],
            "completed": False
        }
        
        logger.info(f"Started analytics session {session_id} for preset {preset_name}")
        return session_id
    
    def add_effect_usage(self, session_id: str, effect_name: str) -> None:
        """
        Record usage of an effect during video generation.
        
        Args:
            session_id: Session ID for the generation session
            effect_name: Name of the effect being used
        """
        if session_id in self.current_sessions:
            if effect_name not in self.current_sessions[session_id].get("effects_used", []):
                self.current_sessions[session_id].setdefault("effects_used", []).append(effect_name)
    
    def add_music_feature_analysis(self, session_id: str, feature_name: str) -> None:
        """
        Record analysis of a music feature during video generation.
        
        Args:
            session_id: Session ID for the generation session
            feature_name: Name of the music feature being analyzed
        """
        if session_id in self.current_sessions:
            if feature_name not in self.current_sessions[session_id].get("music_features_analyzed", []):
                self.current_sessions[session_id].setdefault("music_features_analyzed", []).append(feature_name)
    
    def end_session(self, session_id: str, output_file_size: int, success: bool, error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        End a video generation session and save the analytics data.
        
        Args:
            session_id: Session ID for the generation session
            output_file_size: Size of the output video in bytes
            success: Whether the generation was successful
            error_message: Error message if generation failed
            
        Returns:
            Complete analytics data for the session
        """
        if session_id not in self.current_sessions:
            logger.warning(f"Attempted to end unknown session {session_id}")
            return {}
        
        session_data = self.current_sessions[session_id]
        end_time = time.time()
        
        # Calculate processing time
        session_data["processing_time"] = end_time - session_data["start_time"]
        session_data["end_time"] = end_time
        session_data["timestamp"] = datetime.now().isoformat()
        session_data["completed"] = success
        session_data["output_file_size"] = output_file_size
        
        if not success and error_message:
            session_data["error"] = error_message
        
        # Save to file
        try:
            analytics_data = []
            if os.path.exists(self.analytics_file) and os.path.getsize(self.analytics_file) > 0:
                with open(self.analytics_file, 'r') as f:
                    analytics_data = json.load(f)
            
            analytics_data.append(session_data)
            
            with open(self.analytics_file, 'w') as f:
                json.dump(analytics_data, f, indent=2)
            
            logger.info(f"Saved analytics for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving analytics data: {e}")
        
        # Remove from current sessions
        del self.current_sessions[session_id]
        
        return session_data
    
    def record_platform_distribution(self, video_id: str, platform: str, success: bool, 
                                    engagement_metrics: Optional[Dict[str, Any]] = None,
                                    error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Record distribution of a video to a specific platform.
        
        Args:
            video_id: ID of the video that was distributed
            platform: Name of the platform (e.g. youtube, tiktok, instagram)
            success: Whether the distribution was successful
            engagement_metrics: Optional metrics specific to the platform
            error_message: Error message if distribution failed
            
        Returns:
            Platform distribution data
        """
        platform_data = {
            "video_id": video_id,
            "platform": platform,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "distribution_time": time.time()
        }
        
        if success and engagement_metrics:
            platform_data["engagement_metrics"] = engagement_metrics
            
        if not success and error_message:
            platform_data["error"] = error_message
            
        # Save to platform analytics file
        try:
            platform_analytics = []
            if os.path.exists(self.platform_analytics_file) and os.path.getsize(self.platform_analytics_file) > 0:
                with open(self.platform_analytics_file, 'r') as f:
                    platform_analytics = json.load(f)
            
            platform_analytics.append(platform_data)
            
            with open(self.platform_analytics_file, 'w') as f:
                json.dump(platform_analytics, f, indent=2)
            
            logger.info(f"Saved platform analytics for video {video_id} on {platform}")
        except Exception as e:
            logger.error(f"Error saving platform analytics data: {e}")
            
        return platform_data
    
    def update_platform_metrics(self, video_id: str, platform: str, 
                              metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update engagement metrics for a video on a specific platform.
        
        Args:
            video_id: ID of the video
            platform: Name of the platform (e.g. youtube, tiktok, instagram)
            metrics: New engagement metrics to update
            
        Returns:
            Updated platform data
        """
        platform_data = None
        
        try:
            if os.path.exists(self.platform_analytics_file) and os.path.getsize(self.platform_analytics_file) > 0:
                with open(self.platform_analytics_file, 'r') as f:
                    platform_analytics = json.load(f)
                
                # Find the matching record
                for record in platform_analytics:
                    if record.get("video_id") == video_id and record.get("platform") == platform:
                        # Update metrics
                        record.setdefault("engagement_metrics", {}).update(metrics)
                        record["last_updated"] = datetime.now().isoformat()
                        platform_data = record
                        break
                
                if platform_data:
                    # Save updated data
                    with open(self.platform_analytics_file, 'w') as f:
                        json.dump(platform_analytics, f, indent=2)
                    
                    logger.info(f"Updated platform metrics for video {video_id} on {platform}")
                else:
                    logger.warning(f"No existing record found for video {video_id} on {platform}")
        except Exception as e:
            logger.error(f"Error updating platform metrics: {e}")
            
        return platform_data or {}
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get current statistics for an active session.
        
        Args:
            session_id: Session ID for the generation session
            
        Returns:
            Current statistics for the session
        """
        if session_id in self.current_sessions:
            current_data = self.current_sessions[session_id].copy()
            current_data["current_duration"] = time.time() - current_data["start_time"]
            return current_data
        return {}
    
    def get_aggregate_stats(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get aggregate statistics about video generation.
        
        Args:
            limit: Maximum number of recent sessions to analyze
            
        Returns:
            Aggregate statistics
        """
        try:
            if not os.path.exists(self.analytics_file) or os.path.getsize(self.analytics_file) == 0:
                return {"total_sessions": 0}
            
            with open(self.analytics_file, 'r') as f:
                analytics_data = json.load(f)
            
            # Take the most recent sessions up to the limit
            recent_sessions = analytics_data[-limit:] if len(analytics_data) > limit else analytics_data
            
            # Count successful vs failed sessions
            successful = sum(1 for session in recent_sessions if session.get("completed", False))
            failed = len(recent_sessions) - successful
            
            # Calculate average processing time and file size
            avg_processing_time = sum(session.get("processing_time", 0) for session in recent_sessions) / max(1, len(recent_sessions))
            avg_file_size = sum(session.get("output_file_size", 0) for session in recent_sessions) / max(1, len(recent_sessions))
            
            # Count preset usage
            preset_usage = {}
            for session in recent_sessions:
                preset = session.get("preset", "unknown")
                preset_usage[preset] = preset_usage.get(preset, 0) + 1
            
            # Count effect usage
            effect_usage = {}
            for session in recent_sessions:
                for effect in session.get("effects_used", []):
                    effect_usage[effect] = effect_usage.get(effect, 0) + 1
            
            # Get average effect intensity
            avg_effect_intensity = sum(session.get("effect_intensity", 0) for session in recent_sessions) / max(1, len(recent_sessions))
            
            return {
                "total_sessions": len(recent_sessions),
                "successful_sessions": successful,
                "failed_sessions": failed,
                "success_rate": successful / max(1, len(recent_sessions)),
                "avg_processing_time": avg_processing_time,
                "avg_file_size": avg_file_size,
                "preset_usage": preset_usage,
                "effect_usage": effect_usage,
                "avg_effect_intensity": avg_effect_intensity
            }
            
        except Exception as e:
            logger.error(f"Error getting aggregate stats: {e}")
            return {"error": str(e)}
    
    def get_platform_stats(self, platform: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """
        Get statistics about video distribution to platforms.
        
        Args:
            platform: Optional platform to filter by (e.g. youtube, tiktok)
            limit: Maximum number of recent distributions to analyze
            
        Returns:
            Platform distribution statistics
        """
        try:
            if not os.path.exists(self.platform_analytics_file) or os.path.getsize(self.platform_analytics_file) == 0:
                return {"total_distributions": 0}
            
            with open(self.platform_analytics_file, 'r') as f:
                platform_analytics = json.load(f)
            
            # Filter by platform if specified
            if platform:
                platform_analytics = [record for record in platform_analytics if record.get("platform") == platform]
            
            # Take the most recent distributions up to the limit
            recent_distributions = platform_analytics[-limit:] if len(platform_analytics) > limit else platform_analytics
            
            # Count successful vs failed distributions
            successful = sum(1 for record in recent_distributions if record.get("success", False))
            failed = len(recent_distributions) - successful
            
            # Count distributions by platform
            platform_distribution = {}
            for record in recent_distributions:
                platform_name = record.get("platform", "unknown")
                platform_distribution[platform_name] = platform_distribution.get(platform_name, 0) + 1
            
            # Calculate engagement metrics by platform
            platform_engagement = {}
            for record in recent_distributions:
                if not record.get("success", False) or "engagement_metrics" not in record:
                    continue
                
                platform_name = record.get("platform", "unknown")
                metrics = record["engagement_metrics"]
                
                if platform_name not in platform_engagement:
                    platform_engagement[platform_name] = {
                        "total": 0,
                        "metrics": {}
                    }
                
                platform_engagement[platform_name]["total"] += 1
                
                # Aggregate metrics
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)):
                        if metric_name not in platform_engagement[platform_name]["metrics"]:
                            platform_engagement[platform_name]["metrics"][metric_name] = 0
                        platform_engagement[platform_name]["metrics"][metric_name] += metric_value
            
            # Calculate averages for engagement metrics
            for platform_name, data in platform_engagement.items():
                for metric_name in data["metrics"]:
                    data["metrics"][metric_name] /= data["total"]
            
            return {
                "total_distributions": len(recent_distributions),
                "successful_distributions": successful,
                "failed_distributions": failed,
                "success_rate": successful / max(1, len(recent_distributions)),
                "platform_distribution": platform_distribution,
                "platform_engagement": platform_engagement
            }
            
        except Exception as e:
            logger.error(f"Error getting platform stats: {e}")
            return {"error": str(e)}

    def track_platform_distribution(self, session_id: str, platform: str, success: bool, metrics: Dict[str, Any]) -> None:
        """Track distribution of a video to a specific platform.
        
        Args:
            session_id: The ID of the video generation session
            platform: The platform name (e.g., 'youtube', 'tiktok')
            success: Whether the distribution was successful
            metrics: Platform-specific metrics like engagement data
        """
        session_data = self.get_session(session_id)
        if not session_data:
            logger.warning(f"Cannot track platform distribution: Session {session_id} not found")
            return
        
        if 'platform_distributions' not in session_data:
            session_data['platform_distributions'] = {}
        
        session_data['platform_distributions'][platform] = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'metrics': metrics
        }
        
        self._save_session(session_id, session_data)
        logger.info(f"Tracked distribution to {platform} for session {session_id}")

    def get_platform_analytics(self) -> Dict[str, Any]:
        """Get analytics data for platform distributions."""
        platform_data = {
            'total_distributions': 0,
            'platforms': {},
            'success_rate': {}
        }
        
        for session_id in self.list_sessions():
            session = self.get_session(session_id)
            if not session or 'platform_distributions' not in session:
                continue
            
            for platform, data in session['platform_distributions'].items():
                if platform not in platform_data['platforms']:
                    platform_data['platforms'][platform] = {
                        'total': 0,
                        'successful': 0,
                        'failed': 0
                    }
                
                platform_data['platforms'][platform]['total'] += 1
                platform_data['total_distributions'] += 1
                
                if data['success']:
                    platform_data['platforms'][platform]['successful'] += 1
                else:
                    platform_data['platforms'][platform]['failed'] += 1
        
        # Calculate success rates
        for platform, counts in platform_data['platforms'].items():
            if counts['total'] > 0:
                platform_data['success_rate'][platform] = counts['successful'] / counts['total']
            else:
                platform_data['success_rate'][platform] = 0
            
        return platform_data

def get_analytics_manager() -> AnalyticsManager:
    """
    Get the global analytics manager instance.
    
    Returns:
        Global analytics manager instance
    """
    return AnalyticsManager() 