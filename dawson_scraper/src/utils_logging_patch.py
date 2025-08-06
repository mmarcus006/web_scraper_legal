"""
Alternative logging configuration for Windows compatibility.
This module provides a simpler logging setup that avoids file locking issues.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_simple_logging(log_dir: Path = None):
    """
    Setup simple logging that avoids Windows file locking issues.
    
    Args:
        log_dir: Directory for log files
    """
    if log_dir is None:
        log_dir = Path("logs")
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove all existing handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    
    # Set root logger level
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Simple file handler without rotation (to avoid Windows issues)
    # Use a timestamp in filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"dawson_scraper_{timestamp}.log"
    
    try:
        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8",
            mode='a'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Log the log file location
        root_logger.info(f"Logging to file: {log_file}")
        
    except Exception as e:
        # If file logging fails, just use console
        root_logger.warning(f"Could not setup file logging: {e}")
        root_logger.info("Using console logging only")


def get_simple_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with simple configuration.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)