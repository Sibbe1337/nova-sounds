"""
Trend analysis module for music-responsive video content.

This module analyzes video generation analytics to identify trends
and provide optimization recommendations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
from src.app.services.video.music_responsive.analytics import get_analytics_manager

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """Analyzes content trends and provides optimization recommendations."""
    
    def __init__(self):
        """Initialize the trend analyzer."""
        self.last_update = None
        self.trend_cache = {}
        self.trending_topics = []
        self.trending_hashtags = {}
        self.trending_music = []
        self.trending_styles = {}
        
    def get_preset_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze preset usage trends over the specified time period.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary containing preset trends
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        sessions = get_analytics_manager().list_sessions()
        
        preset_usage = Counter()
        preset_success_rates = {}
        preset_total_counts = {}
        
        # Track preset usage and success rates
        for session_id in sessions:
            session_data = get_analytics_manager().get_session(session_id)
            if not session_data:
                continue
                
            # Skip sessions older than the cutoff date
            session_date = datetime.fromisoformat(session_data.get('timestamp', '2000-01-01'))
            if session_date < cutoff_date:
                continue
                
            preset = session_data.get('preset', 'unknown')
            preset_usage[preset] += 1
            
            # Track success/failure for each preset
            if preset not in preset_total_counts:
                preset_total_counts[preset] = 0
                preset_success_rates[preset] = 0
                
            preset_total_counts[preset] += 1
            if session_data.get('success', False):
                preset_success_rates[preset] += 1
        
        # Calculate success rates
        for preset in preset_success_rates:
            if preset_total_counts[preset] > 0:
                preset_success_rates[preset] = preset_success_rates[preset] / preset_total_counts[preset]
            else:
                preset_success_rates[preset] = 0
        
        # Find trending presets (those with highest usage)
        trending_presets = [preset for preset, count in preset_usage.most_common(5)]
        
        return {
            'total_analyzed': len(sessions),
            'preset_usage': dict(preset_usage),
            'preset_success_rates': preset_success_rates,
            'trending_presets': trending_presets
        }
    
    def get_effect_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze effect usage trends over the specified time period.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary containing effect trends
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        sessions = get_analytics_manager().list_sessions()
        
        effect_usage = Counter()
        effect_combinations = Counter()
        
        # Track effect usage
        for session_id in sessions:
            session_data = get_analytics_manager().get_session(session_id)
            if not session_data:
                continue
                
            # Skip sessions older than the cutoff date
            session_date = datetime.fromisoformat(session_data.get('timestamp', '2000-01-01'))
            if session_date < cutoff_date:
                continue
                
            # Count individual effects
            effects = session_data.get('effects', [])
            for effect in effects:
                effect_usage[effect] += 1
            
            # Count effect combinations (as a tuple)
            if len(effects) > 1:
                effect_combo = tuple(sorted(effects))
                effect_combinations[effect_combo] += 1
        
        # Find trending effects and combinations
        trending_effects = [effect for effect, count in effect_usage.most_common(5)]
        trending_combinations = [combo for combo, count in effect_combinations.most_common(3)]
        
        return {
            'total_analyzed': len(sessions),
            'effect_usage': dict(effect_usage),
            'trending_effects': trending_effects,
            'trending_combinations': trending_combinations
        }
    
    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate content optimization recommendations based on trend analysis.
        
        Returns:
            List of recommendation objects
        """
        preset_trends = self.get_preset_trends()
        effect_trends = self.get_effect_trends()
        
        recommendations = []
        
        # Recommend trending presets
        if preset_trends['trending_presets']:
            recommendations.append({
                'type': 'preset',
                'title': 'Try Popular Presets',
                'description': 'These presets are currently trending in successful videos',
                'items': preset_trends['trending_presets'][:3]
            })
        
        # Recommend effective effect combinations
        if effect_trends['trending_combinations']:
            combo_recommendations = []
            for combo in effect_trends['trending_combinations'][:2]:
                combo_recommendations.append({
                    'effects': combo,
                    'name': ' + '.join(combo)
                })
                
            recommendations.append({
                'type': 'effect_combination',
                'title': 'Trending Effect Combinations',
                'description': 'These effect combinations are popular in recent videos',
                'items': combo_recommendations
            })
        
        # Add optimization tips based on success rates
        success_rates = preset_trends['preset_success_rates']
        if success_rates:
            # Find preset with highest success rate (min 5 uses)
            best_preset = None
            best_rate = 0
            
            for preset, rate in success_rates.items():
                if preset_trends['preset_usage'].get(preset, 0) >= 5 and rate > best_rate:
                    best_preset = preset
                    best_rate = rate
            
            if best_preset:
                recommendations.append({
                    'type': 'optimization',
                    'title': 'Optimization Tip',
                    'description': f'The "{best_preset}" preset has the highest success rate at {best_rate*100:.1f}%',
                    'items': [best_preset]
                })
        
        return recommendations
    
    def get_trending_formats(self, platform: str) -> dict:
        """
        Get trending video formats for a specific platform.
        
        Args:
            platform: Social media platform (youtube, tiktok, etc.)
            
        Returns:
            dict: Trending formats and recommendations
        """
        # Update cache if needed
        self._update_trend_cache()
        
        # Normalize platform name
        platform = platform.lower()
        
        # Get platform-specific trends
        if platform in self.trend_cache:
            return self.trend_cache[platform]
            
        # If platform not in cache, get general recommendations
        from src.app.services.ai.metadata_generator import detect_trending_video_format
        return detect_trending_video_format(platform)
    
    def analyze_video_for_trends(self, video_data: dict) -> dict:
        """
        Analyze a video for trending elements.
        
        Args:
            video_data: Video data including metadata, duration, etc.
            
        Returns:
            dict: Analysis of how well the video aligns with current trends
        """
        platform = video_data.get("platform", "youtube")
        trending_formats = self.get_trending_formats(platform)
        
        # Extract relevant video data
        duration = video_data.get("duration", 0)
        title = video_data.get("title", "")
        description = video_data.get("description", "")
        hashtags = video_data.get("hashtags", [])
        
        # Analyze against trends
        format_score = self._calculate_format_score(video_data, trending_formats)
        duration_score = self._calculate_duration_score(duration, trending_formats.get("optimal_duration", 60))
        hook_score = self._calculate_hook_score(title, description, trending_formats.get("recommended_hooks", []))
        hashtag_score = self._calculate_hashtag_score(hashtags, platform)
        
        # Overall trend score (weighted average)
        overall_score = (
            format_score * 0.4 +
            duration_score * 0.2 +
            hook_score * 0.2 +
            hashtag_score * 0.2
        )
        
        # Generate recommendations
        recommendations = self._generate_trend_recommendations(
            video_data, 
            format_score, 
            duration_score,
            hook_score,
            hashtag_score,
            trending_formats
        )
        
        return {
            "trend_score": round(overall_score * 100),
            "format_score": round(format_score * 100),
            "duration_score": round(duration_score * 100),
            "hook_score": round(hook_score * 100),
            "hashtag_score": round(hashtag_score * 100),
            "recommendations": recommendations,
            "trending_formats": trending_formats,
            "optimal_duration": trending_formats.get("optimal_duration", 60),
            "trending_hashtags": self._get_top_hashtags(platform, 10)
        }
    
    def get_trending_hashtags(self, platform: str, limit: int = 20) -> list:
        """
        Get trending hashtags for a specific platform.
        
        Args:
            platform: Social media platform
            limit: Maximum number of hashtags to return
            
        Returns:
            list: Trending hashtags
        """
        # Update cache if needed
        self._update_trend_cache()
        
        # Normalize platform name
        platform = platform.lower()
        
        # Get platform-specific hashtags
        if platform in self.trending_hashtags:
            return self.trending_hashtags[platform][:limit]
            
        # If platform not in cache, return generic trending hashtags
        generic_hashtags = {
            "youtube": ["shorts", "youtubeshorts", "trending", "viral", "music", "dance", "comedy", "howto", 
                       "tutorial", "challenge", "reaction", "satisfying", "asmr", "gaming", "food"],
            "tiktok": ["fyp", "foryou", "foryoupage", "viral", "trending", "tiktok", "dance", "comedy", 
                      "duet", "challenge", "pov", "sound", "greenscreen", "funny", "cute"],
            "instagram": ["reels", "instagramreels", "instadaily", "instagood", "trending", "viral", 
                         "music", "dance", "comedy", "fashion", "beauty", "fitness", "food", "travel", "photooftheday"],
            "facebook": ["trending", "viral", "music", "reels", "facebookreels", "funny", "dance", 
                        "comedy", "challenge", "motivation", "family", "friends", "love", "nature", "food"]
        }
        
        return generic_hashtags.get(platform, generic_hashtags["youtube"])[:limit]
    
    def get_optimal_posting_times(self, platform: str) -> list:
        """
        Get optimal posting times for a specific platform.
        
        Args:
            platform: Social media platform
            
        Returns:
            list: Optimal posting times (hour of day, day of week)
        """
        # Different platforms have different optimal posting times
        optimal_times = {
            "youtube": [
                {"day": "Saturday", "hour": 15, "timezone": "UTC"},  # 3 PM UTC Saturday
                {"day": "Sunday", "hour": 15, "timezone": "UTC"},    # 3 PM UTC Sunday
                {"day": "Thursday", "hour": 19, "timezone": "UTC"},  # 7 PM UTC Thursday
                {"day": "Friday", "hour": 20, "timezone": "UTC"},    # 8 PM UTC Friday
                {"day": "Wednesday", "hour": 19, "timezone": "UTC"}, # 7 PM UTC Wednesday
            ],
            "tiktok": [
                {"day": "Tuesday", "hour": 14, "timezone": "UTC"},   # 2 PM UTC Tuesday
                {"day": "Thursday", "hour": 14, "timezone": "UTC"},  # 2 PM UTC Thursday
                {"day": "Friday", "hour": 17, "timezone": "UTC"},    # 5 PM UTC Friday
                {"day": "Saturday", "hour": 19, "timezone": "UTC"},  # 7 PM UTC Saturday
                {"day": "Sunday", "hour": 15, "timezone": "UTC"},    # 3 PM UTC Sunday
            ],
            "instagram": [
                {"day": "Monday", "hour": 18, "timezone": "UTC"},    # 6 PM UTC Monday
                {"day": "Wednesday", "hour": 15, "timezone": "UTC"}, # 3 PM UTC Wednesday
                {"day": "Thursday", "hour": 15, "timezone": "UTC"},  # 3 PM UTC Thursday
                {"day": "Friday", "hour": 12, "timezone": "UTC"},    # 12 PM UTC Friday
                {"day": "Saturday", "hour": 17, "timezone": "UTC"},  # 5 PM UTC Saturday
            ],
            "facebook": [
                {"day": "Wednesday", "hour": 15, "timezone": "UTC"}, # 3 PM UTC Wednesday
                {"day": "Thursday", "hour": 13, "timezone": "UTC"},  # 1 PM UTC Thursday
                {"day": "Friday", "hour": 15, "timezone": "UTC"},    # 3 PM UTC Friday
                {"day": "Saturday", "hour": 12, "timezone": "UTC"},  # 12 PM UTC Saturday
                {"day": "Sunday", "hour": 16, "timezone": "UTC"},    # 4 PM UTC Sunday
            ]
        }
        
        platform = platform.lower()
        return optimal_times.get(platform, optimal_times["youtube"])
    
    def get_trending_topics(self, platform: str, limit: int = 10) -> list:
        """
        Get trending topics for a specific platform.
        
        Args:
            platform: Social media platform
            limit: Maximum number of topics to return
            
        Returns:
            list: Trending topics
        """
        # Update cache if needed
        self._update_trend_cache()
        
        # Current popular topics (generic)
        generic_topics = [
            "life hacks",
            "day in the life",
            "what I eat in a day",
            "morning routine",
            "room transformation",
            "satisfying cleaning",
            "outfit ideas",
            "skincare routine",
            "recipe tutorial",
            "fitness challenge",
            "study with me",
            "product review",
            "travel vlog",
            "money saving tips",
            "DIY projects"
        ]
        
        return generic_topics[:limit]
    
    def _update_trend_cache(self):
        """Update trend cache if it's stale."""
        from datetime import datetime, timedelta
        
        # Only update once per day
        if self.last_update and (datetime.now() - self.last_update) < timedelta(days=1):
            return
            
        # Update trend data from metadata generator
        from src.app.services.ai.metadata_generator import detect_trending_video_format
        
        for platform in ["youtube", "tiktok", "instagram", "facebook"]:
            self.trend_cache[platform] = detect_trending_video_format(platform)
            
        # Populate trending hashtags
        self.trending_hashtags = {
            "youtube": ["shorts", "youtubeshorts", "trending", "viral", "music", "dance", "comedy", "howto", 
                       "tutorial", "challenge", "reaction", "satisfying", "asmr", "gaming", "food"],
            "tiktok": ["fyp", "foryou", "foryoupage", "viral", "trending", "tiktok", "dance", "comedy", 
                      "duet", "challenge", "pov", "sound", "greenscreen", "funny", "cute"],
            "instagram": ["reels", "instagramreels", "instadaily", "instagood", "trending", "viral", 
                         "music", "dance", "comedy", "fashion", "beauty", "fitness", "food", "travel", "photooftheday"],
            "facebook": ["trending", "viral", "music", "reels", "facebookreels", "funny", "dance", 
                        "comedy", "challenge", "motivation", "family", "friends", "love", "nature", "food"]
        }
        
        self.last_update = datetime.now()
    
    def _calculate_format_score(self, video_data: dict, trending_formats: dict) -> float:
        """Calculate how well a video matches trending formats."""
        # Simple matching algorithm
        score = 0.5  # Start with neutral score
        
        # Check aspect ratio
        aspect_ratio = video_data.get("aspect_ratio", "16:9")
        if aspect_ratio == trending_formats.get("aspect_ratio", "9:16"):
            score += 0.2
        else:
            score -= 0.2
            
        # Check if it uses any trending formats
        video_format = video_data.get("format", "").lower()
        trending_format_list = [f.lower() for f in trending_formats.get("trending_formats", [])]
        
        for trend_format in trending_format_list:
            if trend_format in video_format:
                score += 0.1
                break
                
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _calculate_duration_score(self, duration: int, optimal_duration: int) -> float:
        """Calculate score based on how close the duration is to the optimal."""
        if duration == 0:
            return 0.5  # Unknown duration
            
        # Calculate how close the duration is to optimal (as a percentage)
        difference = abs(duration - optimal_duration) / optimal_duration
        
        # Convert to a score (closer to optimal = higher score)
        # Within 10% of optimal is a perfect score
        if difference <= 0.1:
            return 1.0
        # Within 25% of optimal is still good
        elif difference <= 0.25:
            return 0.8
        # Within 50% of optimal is acceptable
        elif difference <= 0.5:
            return 0.6
        # Within 100% of optimal is not great
        elif difference <= 1.0:
            return 0.4
        # More than 100% off is poor
        else:
            return 0.2
    
    def _calculate_hook_score(self, title: str, description: str, recommended_hooks: list) -> float:
        """Calculate score based on if the video uses recommended hooks."""
        score = 0.5  # Start with neutral score
        
        # Check title and first line of description for hooks
        first_line = description.split("\n")[0] if description else ""
        combined_text = (title + " " + first_line).lower()
        
        # Check each recommended hook
        for hook in recommended_hooks:
            hook_lower = hook.lower()
            # Look for key phrases from the hook
            key_phrases = hook_lower.replace("start with ", "").replace("use ", "").replace("begin with ", "")
            
            if key_phrases.strip("'\"") in combined_text:
                score += 0.15
                break
                
        # Check for question marks (common hook)
        if "?" in combined_text:
            score += 0.1
            
        # Check for call to action phrases
        cta_phrases = ["watch", "check out", "don't miss", "click", "subscribe"]
        for phrase in cta_phrases:
            if phrase in combined_text:
                score += 0.05
                break
                
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _calculate_hashtag_score(self, hashtags: list, platform: str) -> float:
        """Calculate score based on use of trending hashtags."""
        if not hashtags:
            return 0.3  # Penalize for no hashtags
            
        score = 0.5  # Start with neutral score
        
        # Get trending hashtags for the platform
        trending_hashtags = self._get_top_hashtags(platform, 20)
        
        # Count matches
        matches = 0
        for hashtag in hashtags:
            clean_tag = hashtag.lower().strip("#")
            if clean_tag in trending_hashtags:
                matches += 1
                
        # Score based on matches (diminishing returns)
        if matches >= 5:
            score = 1.0
        elif matches >= 3:
            score = 0.9
        elif matches >= 2:
            score = 0.8
        elif matches >= 1:
            score = 0.7
            
        # Penalize for too few or too many hashtags
        if len(hashtags) < 3:
            score -= 0.1
        elif platform == "youtube" and len(hashtags) > 15:
            score -= 0.1
        elif platform == "tiktok" and len(hashtags) > 25:
            score -= 0.1
            
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _generate_trend_recommendations(self, video_data: dict, format_score: float, duration_score: float, 
                                      hook_score: float, hashtag_score: float, trending_formats: dict) -> list:
        """Generate recommendations based on trend analysis."""
        recommendations = []
        
        # Format recommendations
        if format_score < 0.7:
            aspect_ratio = trending_formats.get("aspect_ratio", "9:16")
            recommendations.append(f"Consider using the optimal aspect ratio ({aspect_ratio}) for this platform.")
            
            # Recommend trending formats
            trend_format = trending_formats.get("trending_formats", [])[0] if trending_formats.get("trending_formats") else "reaction videos"
            recommendations.append(f"Try incorporating trending formats like '{trend_format}'.")
        
        # Duration recommendations
        if duration_score < 0.7:
            optimal_duration = trending_formats.get("optimal_duration", 60)
            current_duration = video_data.get("duration", 0)
            
            if current_duration > optimal_duration * 1.25:
                recommendations.append(f"Consider shortening your video closer to {optimal_duration} seconds for optimal engagement.")
            elif current_duration < optimal_duration * 0.75:
                recommendations.append(f"Consider extending your video closer to {optimal_duration} seconds for optimal engagement.")
        
        # Hook recommendations
        if hook_score < 0.7:
            hook_example = trending_formats.get("recommended_hooks", ["Ask a question"])[0]
            recommendations.append(f"Improve your hook with techniques like '{hook_example}'.")
            recommendations.append("Add a question or clear call-to-action in your title or opening.")
        
        # Hashtag recommendations
        if hashtag_score < 0.7:
            platform = video_data.get("platform", "youtube")
            trending_tags = ", ".join(["#" + tag for tag in self._get_top_hashtags(platform, 3)])
            recommendations.append(f"Include more trending hashtags like {trending_tags}.")
            
            if platform == "youtube" and len(video_data.get("hashtags", [])) > 15:
                recommendations.append("YouTube works best with 5-15 hashtags. Consider reducing your hashtag count.")
            elif platform == "tiktok" and len(video_data.get("hashtags", [])) < 5:
                recommendations.append("TikTok works well with 5-15 relevant hashtags. Consider adding more.")
        
        # Add general recommendations if few specific ones
        if len(recommendations) < 2:
            trend_transition = trending_formats.get("trending_transitions", [])[0] if trending_formats.get("trending_transitions") else "quick cuts"
            recommendations.append(f"Try incorporating trending transitions like '{trend_transition}'.")
            
            trend_effect = trending_formats.get("trending_effects", [])[0] if trending_formats.get("trending_effects") else "text overlays"
            recommendations.append(f"Experiment with trending effects like '{trend_effect}'.")
        
        return recommendations
    
    def _get_top_hashtags(self, platform: str, limit: int = 10) -> list:
        """Get top hashtags for a platform."""
        return self.get_trending_hashtags(platform, limit) 