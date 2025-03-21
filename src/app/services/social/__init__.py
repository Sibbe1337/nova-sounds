"""
Social media integration services for YouTube Shorts Machine.

This module provides video publishing capabilities for multiple platforms
including TikTok, Instagram, and Facebook.
"""

from src.app.services.social.cross_platform import (
    Platform,
    VideoFormat,
    CrossPlatformPublisher,
    get_cross_platform_publisher
)

__all__ = [
    'Platform',
    'VideoFormat',
    'CrossPlatformPublisher',
    'get_cross_platform_publisher'
] 