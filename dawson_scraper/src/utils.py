"""Utility functions for Dawson Court Scraper."""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
from logging.handlers import RotatingFileHandler

from .config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Get configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = settings.log_dir / "dawson_scraper.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def generate_monthly_periods(
    start_date: datetime,
    end_date: datetime
) -> List[Tuple[datetime, datetime]]:
    """
    Generate list of monthly periods between dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        List of (period_start, period_end) tuples
    """
    periods = []
    current = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    while current < end_date:
        # Calculate last day of current month
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1, day=1)
        else:
            next_month = current.replace(month=current.month + 1, day=1)
        
        period_end = min(next_month - timedelta(microseconds=1), end_date)
        periods.append((current, period_end))
        
        current = next_month
    
    return periods


def safe_filename(text: str, max_length: int = 100) -> str:
    """
    Create safe filename from text.
    
    Args:
        text: Input text
        max_length: Maximum filename length
        
    Returns:
        Safe filename
    """
    # Remove/replace unsafe characters
    safe = "".join(c for c in text if c.isalnum() or c in (" ", "-", "_", "."))
    
    # Replace spaces with underscores
    safe = safe.replace(" ", "_")
    
    # Remove multiple underscores
    while "__" in safe:
        safe = safe.replace("__", "_")
    
    # Trim to max length
    if len(safe) > max_length:
        safe = safe[:max_length]
    
    # Remove trailing dots and underscores
    safe = safe.rstrip("._")
    
    return safe or "unnamed"


def format_bytes(size: int) -> str:
    """
    Format bytes as human-readable string.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration as human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def parse_date(date_str: str) -> datetime:
    """
    Parse date string in various formats.
    
    Args:
        date_str: Date string
        
    Returns:
        Parsed datetime
    """
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try ISO format
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        pass
    
    raise ValueError(f"Unable to parse date: {date_str}")


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """
    Split list into chunks.
    
    Args:
        lst: Input list
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def ensure_dir(path: Path) -> Path:
    """
    Ensure directory exists.
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate file hash for verification.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        Hex digest
    """
    import hashlib
    
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def verify_pdf(file_path: Path) -> bool:
    """
    Verify PDF file is valid.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        True if valid PDF
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            if header != b"%PDF-":
                return False
            
            # Check for EOF marker
            f.seek(-1024, 2)  # Go to end of file
            tail = f.read()
            if b"%%EOF" not in tail:
                return False
        
        return True
    except Exception:
        return False