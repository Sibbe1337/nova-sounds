"""
Centralized logging configuration for the YouTube Shorts Machine application.
"""
import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.app.core.settings import DEV_MODE, LOG_LEVEL

# Define log formatting
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEV_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Store configured loggers to avoid duplicate configuration
CONFIGURED_LOGGERS = set()

class LogLevels:
    """Constants for log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

def get_log_level(level_name: str) -> int:
    """
    Convert string log level to logging module constant.
    
    Args:
        level_name: String representation of log level
        
    Returns:
        int: Logging module constant
    """
    level_map = {
        LogLevels.DEBUG: logging.DEBUG,
        LogLevels.INFO: logging.INFO,
        LogLevels.WARNING: logging.WARNING,
        LogLevels.ERROR: logging.ERROR,
        LogLevels.CRITICAL: logging.CRITICAL,
    }
    
    return level_map.get(level_name.upper(), logging.INFO)

def configure_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Configure a logger with the appropriate handlers and formatting.
    
    Args:
        name: Logger name (typically module name)
        level: Override the default log level
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Skip if already configured
    if name in CONFIGURED_LOGGERS:
        return logger
    
    # Set log level from parameter, environment variable, or default
    log_level = get_log_level(level or LOG_LEVEL or LogLevels.INFO)
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console handler with appropriate formatting based on environment
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = DEV_FORMAT if DEV_MODE else DEFAULT_FORMAT
    console_formatter = logging.Formatter(console_format)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # File handler in production
    if not DEV_MODE:
        # Create a rotating file handler for production
        log_file = LOGS_DIR / f"{name.replace('.', '_')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=3
        )
        file_formatter = logging.Formatter(DEFAULT_FORMAT)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    # Mark as configured
    CONFIGURED_LOGGERS.add(name)
    
    return logger

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger. Helper function for modules to use.
    
    Args:
        name: Logger name (typically module name)
        level: Override the default log level
        
    Returns:
        logging.Logger: Configured logger
    """
    return configure_logger(name, level)

# Configure root logger
root_logger = configure_logger("root")

# Convenience function for logging exceptions with traceback
def log_exception(logger: logging.Logger, message: str, exc: Exception) -> None:
    """
    Log an exception with traceback.
    
    Args:
        logger: Logger to use
        message: Error message
        exc: Exception to log
    """
    logger.exception(f"{message}: {str(exc)}") 