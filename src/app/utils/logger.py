"""
Logging configuration for the YouTube Shorts Machine.
"""

import logging
import os
import sys
from datetime import datetime

# Configure logging
logger = logging.getLogger("youtube_shorts")

def setup_logging(level=logging.INFO, log_to_file=True):
    """
    Configure application logging.
    
    Args:
        level: Logging level
        log_to_file: Whether to log to file
    """
    logger.setLevel(level)
    logger.propagate = False
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # Create file handler if requested
    if log_to_file:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
    return logger

# Setup logging by default
setup_logging() 