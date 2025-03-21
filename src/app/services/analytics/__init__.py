"""
Analytics services for the YouTube Shorts Machine application.
"""
from src.app.services.analytics.analytics_manager import get_analytics_manager
from src.app.services.analytics.data_collector import get_analytics_collector

__all__ = [
    'get_analytics_manager',
    'get_analytics_collector'
] 