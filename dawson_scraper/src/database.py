"""Database management for tracking downloads and state."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import aiosqlite
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .models import Opinion, DownloadStatus, ScraperStats
from .config import settings


Base = declarative_base()


class DownloadRecord(Base):
    """Database model for tracking downloads."""
    __tablename__ = "downloads"
    
    id = Column(Integer, primary_key=True)
    docket_number = Column(String, nullable=False, index=True)
    docket_entry_id = Column(String, nullable=False, unique=True)
    case_caption = Column(String)
    document_title = Column(Text)
    filing_date = Column(DateTime)
    judge = Column(String)
    pages = Column(Integer)
    
    # Download info
    download_url = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    status = Column(String, default=DownloadStatus.PENDING.value)
    attempts = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }


class SearchRecord(Base):
    """Database model for tracking searches."""
    __tablename__ = "searches"
    
    id = Column(Integer, primary_key=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    opinions_found = Column(Integer, default=0)
    json_path = Column(String)
    status = Column(String, default="pending")
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)


class DatabaseManager:
    """Manages database operations."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager."""
        self.db_path = db_path or settings.db_path
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database and create tables."""
        if self._initialized:
            return
        
        # Create sync engine for table creation
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        self._initialized = True
    
    async def get_connection(self):
        """Get async database connection."""
        if not self._initialized:
            await self.initialize()
        return aiosqlite.connect(self.db_path)
    
    async def record_opinion(self, opinion: Opinion) -> int:
        """Record an opinion in the database."""
        async with await self.get_connection() as db:
            cursor = await db.execute(
                """
                INSERT OR IGNORE INTO downloads (
                    docket_number, docket_entry_id, case_caption,
                    document_title, filing_date, judge, pages, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    opinion.docket_number,
                    opinion.docket_entry_id,
                    opinion.case_caption,
                    opinion.document_title,
                    opinion.filing_datetime,
                    opinion.judge,
                    opinion.number_of_pages,
                    DownloadStatus.PENDING.value,
                )
            )
            await db.commit()
            return cursor.lastrowid
    
    async def update_download_status(
        self,
        docket_entry_id: str,
        status: DownloadStatus,
        download_url: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None,
    ):
        """Update download status for an opinion."""
        async with await self.get_connection() as db:
            updates = ["status = ?", "attempts = attempts + 1"]
            values = [status.value]
            
            if download_url:
                updates.append("download_url = ?")
                values.append(download_url)
            
            if file_path:
                updates.append("file_path = ?")
                values.append(str(file_path))
            
            if file_size:
                updates.append("file_size = ?")
                values.append(file_size)
            
            if error_message:
                updates.append("error_message = ?")
                values.append(error_message)
            
            if status == DownloadStatus.DOWNLOADING:
                updates.append("started_at = ?")
                values.append(datetime.now())
            elif status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED):
                updates.append("completed_at = ?")
                values.append(datetime.now())
            
            values.append(docket_entry_id)
            
            await db.execute(
                f"UPDATE downloads SET {', '.join(updates)} WHERE docket_entry_id = ?",
                values
            )
            await db.commit()
    
    async def get_pending_downloads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get pending downloads from database."""
        async with await self.get_connection() as db:
            query = """
                SELECT * FROM downloads 
                WHERE status IN (?, ?)
                ORDER BY created_at
            """
            params = [DownloadStatus.PENDING.value, DownloadStatus.FAILED.value]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def check_already_downloaded(self, docket_entry_id: str) -> bool:
        """Check if a document is already downloaded."""
        async with await self.get_connection() as db:
            cursor = await db.execute(
                "SELECT status FROM downloads WHERE docket_entry_id = ?",
                (docket_entry_id,)
            )
            row = await cursor.fetchone()
            
            if row and row[0] == DownloadStatus.COMPLETED.value:
                return True
            return False
    
    async def record_search(
        self,
        start_date: datetime,
        end_date: datetime,
        opinions_found: int,
        json_path: str,
        status: str = "completed",
        error_message: Optional[str] = None,
    ):
        """Record a search operation."""
        async with await self.get_connection() as db:
            await db.execute(
                """
                INSERT INTO searches (
                    start_date, end_date, opinions_found,
                    json_path, status, error_message, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    start_date,
                    end_date,
                    opinions_found,
                    json_path,
                    status,
                    error_message,
                    datetime.now() if status == "completed" else None,
                )
            )
            await db.commit()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics from database."""
        async with await self.get_connection() as db:
            # Download stats
            cursor = await db.execute(
                """
                SELECT 
                    status,
                    COUNT(*) as count,
                    SUM(file_size) as total_size
                FROM downloads
                GROUP BY status
                """
            )
            download_stats = await cursor.fetchall()
            
            # Search stats
            cursor = await db.execute(
                """
                SELECT 
                    COUNT(*) as total_searches,
                    SUM(opinions_found) as total_opinions
                FROM searches
                WHERE status = 'completed'
                """
            )
            search_stats = await cursor.fetchone()
            
            # Failed downloads
            cursor = await db.execute(
                """
                SELECT docket_number, document_title, error_message
                FROM downloads
                WHERE status = 'failed'
                ORDER BY created_at DESC
                LIMIT 10
                """
            )
            recent_failures = await cursor.fetchall()
            
            return {
                "downloads": {
                    status: {"count": count, "size": size or 0}
                    for status, count, size in download_stats
                },
                "searches": {
                    "total": search_stats[0] if search_stats else 0,
                    "opinions_found": search_stats[1] if search_stats else 0,
                },
                "recent_failures": [
                    {
                        "docket": row[0],
                        "title": row[1],
                        "error": row[2],
                    }
                    for row in recent_failures
                ],
            }
    
    async def cleanup_stale_downloads(self, hours: int = 24):
        """Clean up stale downloading status."""
        async with await self.get_connection() as db:
            await db.execute(
                f"""
                UPDATE downloads 
                SET status = ?, error_message = ?
                WHERE status = ? 
                AND started_at < datetime('now', '-{hours} hours')
                """,
                (
                    DownloadStatus.FAILED.value,
                    "Download timeout - marked as failed",
                    DownloadStatus.DOWNLOADING.value,
                )
            )
            await db.commit()


# Global database instance
db_manager = DatabaseManager()