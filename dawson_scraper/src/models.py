"""Data models for Dawson Court Scraper."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OpinionType(str, Enum):
    """Types of court opinions."""
    MOP = "MOP"  # Memorandum Opinion
    SOP = "SOP"  # Summary Opinion  
    OST = "OST"  # Order of Service of Transcript
    TCOP = "TCOP"  # T.C. Opinion


class DownloadStatus(str, Enum):
    """Status of document downloads."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Opinion(BaseModel):
    """Court opinion record."""
    entity_name: str = Field(alias="entityName")
    case_caption: str = Field(alias="caseCaption")
    docket_entry_id: str = Field(alias="docketEntryId")
    docket_number: str = Field(alias="docketNumber")
    docket_number_with_suffix: str = Field(alias="docketNumberWithSuffix")
    document_title: str = Field(alias="documentTitle")
    document_type: str = Field(alias="documentType")
    event_code: str = Field(alias="eventCode")
    filing_date: str = Field(alias="filingDate")
    is_stricken: bool = Field(alias="isStricken")
    judge: Optional[str] = Field(default=None, alias="signedJudgeName")
    number_of_pages: int = Field(alias="numberOfPages")
    
    @field_validator("docket_entry_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate docket entry ID is a valid UUID."""
        try:
            UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID: {v}")
        return v
    
    @property
    def filing_datetime(self) -> datetime:
        """Parse filing date as datetime."""
        return datetime.fromisoformat(self.filing_date.replace("Z", "+00:00"))
    
    @property
    def safe_filename(self) -> str:
        """Generate a safe filename for this opinion."""
        safe_title = "".join(
            c for c in self.document_title 
            if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()[:100]
        return f"{self.docket_number}_{self.docket_entry_id[:8]}_{safe_title}.pdf"
    
    class Config:
        populate_by_name = True


class OpinionBatch(BaseModel):
    """Batch of opinions for a date range."""
    start_date: datetime
    end_date: datetime
    opinions: List[Opinion] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def date_range_str(self) -> str:
        """String representation of date range."""
        return f"{self.start_date.strftime('%Y-%m-%d')}_to_{self.end_date.strftime('%Y-%m-%d')}"
    
    @property
    def json_filename(self) -> str:
        """Filename for JSON storage."""
        return f"opinions_{self.date_range_str}.json"


class DownloadTask(BaseModel):
    """Task for downloading a document."""
    opinion: Opinion
    download_url: Optional[str] = None
    file_path: Optional[str] = None
    status: DownloadStatus = DownloadStatus.PENDING
    attempts: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    file_size: Optional[int] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Download duration in seconds."""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None


class ScraperStats(BaseModel):
    """Statistics for scraping session."""
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Search stats
    total_periods: int = 0
    successful_searches: int = 0
    failed_searches: int = 0
    total_opinions: int = 0
    
    # Download stats
    total_downloads: int = 0
    successful_downloads: int = 0
    failed_downloads: int = 0
    skipped_downloads: int = 0
    
    # Performance stats
    total_bytes_downloaded: int = 0
    average_download_speed: float = 0.0
    
    @property
    def duration(self) -> Optional[float]:
        """Total duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Download success rate."""
        if self.total_downloads > 0:
            return self.successful_downloads / self.total_downloads * 100
        return 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "Duration": f"{self.duration:.1f}s" if self.duration else "In progress",
            "Periods Processed": f"{self.successful_searches}/{self.total_periods}",
            "Total Opinions": self.total_opinions,
            "Downloads": {
                "Successful": self.successful_downloads,
                "Failed": self.failed_downloads,
                "Skipped": self.skipped_downloads,
                "Success Rate": f"{self.success_rate:.1f}%",
            },
            "Data Downloaded": f"{self.total_bytes_downloaded / (1024**2):.1f} MB",
        }


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    headers: Dict[str, str] = Field(default_factory=dict)