"""
US Tax Court Document Scraper Package.

A high-performance scraper for downloading court opinions and documents
from the Dawson US Tax Court API.
"""

__version__ = "3.0.0"
__author__ = "Miller"

from .config import settings
from .models import Opinion, OpinionBatch, DownloadTask, ScraperStats
from .api_client import APIClient
from .downloader import ParallelDownloader
from .scraper import DawsonScraper
from .database import db_manager
from .utils import get_logger

__all__ = [
    "settings",
    "Opinion",
    "OpinionBatch",
    "DownloadTask",
    "ScraperStats",
    "APIClient",
    "ParallelDownloader",
    "DawsonScraper",
    "db_manager",
    "get_logger",
]