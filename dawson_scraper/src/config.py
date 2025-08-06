"""Configuration management for Dawson Court Scraper."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # API Configuration
    api_base_url: str = Field(
        default="https://public-api-green.dawson.ustaxcourt.gov/public-api",
        description="Base URL for Dawson API"
    )
    api_timeout: int = Field(default=30, ge=1, description="API timeout in seconds")
    api_retry_count: int = Field(default=3, ge=1, description="Number of retry attempts")
    api_retry_delay: float = Field(default=1.0, ge=0.1, description="Initial retry delay")
    
    # Download Configuration
    parallel_workers: int = Field(default=5, ge=1, le=20, description="Number of parallel workers")
    rate_limit_delay: float = Field(default=0.2, ge=0.0, description="Delay between requests per worker")
    chunk_size: int = Field(default=8192, ge=1024, description="Download chunk size in bytes")
    max_concurrent_downloads: int = Field(default=10, ge=1, le=50, description="Max concurrent downloads")
    
    # Paths
    data_dir: Path = Field(default=Path("./data"), description="Base data directory")
    log_dir: Path = Field(default=Path("./logs"), description="Log directory")
    
    # Features
    download_pdfs: bool = Field(default=True, description="Enable PDF downloads")
    verify_downloads: bool = Field(default=True, description="Verify downloaded files")
    skip_existing: bool = Field(default=True, description="Skip already downloaded files")
    use_compression: bool = Field(default=True, description="Use gzip compression for requests")
    
    # Date Range
    start_date: datetime = Field(
        default_factory=lambda: datetime(1940, 1, 1),
        description="Start date for scraping"
    )
    end_date: datetime = Field(
        default_factory=datetime.now,
        description="End date for scraping"
    )
    
    # Headers
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        description="User agent string"
    )
    
    @field_validator("data_dir", "log_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v = Path(v).resolve()
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @property
    def json_dir(self) -> Path:
        """Directory for JSON data."""
        path = self.data_dir / "json"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def documents_dir(self) -> Path:
        """Directory for PDF documents."""
        path = self.data_dir / "documents"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def db_dir(self) -> Path:
        """Directory for database."""
        path = self.data_dir / "db"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def db_path(self) -> Path:
        """Path to SQLite database."""
        return self.db_dir / "dawson_scraper.db"
    
    @property
    def headers(self) -> dict:
        """HTTP headers for requests."""
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "origin": "https://dawson.ustaxcourt.gov",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": self.user_agent,
        }
    
    def get_document_path(self, filing_date: str, filename: str) -> Path:
        """Get path for a document based on filing date."""
        try:
            date_obj = datetime.fromisoformat(filing_date.replace("Z", "+00:00"))
            year_month = date_obj.strftime("%Y-%m")
        except (ValueError, AttributeError):
            year_month = "unknown"
        
        month_dir = self.documents_dir / year_month
        month_dir.mkdir(parents=True, exist_ok=True)
        return month_dir / filename


# Global settings instance
settings = Settings()