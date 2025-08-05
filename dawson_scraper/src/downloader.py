"""Parallel download manager with progress tracking."""

import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable
from tqdm.asyncio import tqdm

from .models import Opinion, DownloadTask, DownloadStatus
from .api_client import APIClient
from .database import db_manager
from .config import settings
from .utils import get_logger, safe_filename


logger = get_logger(__name__)


class ParallelDownloader:
    """Manages parallel document downloads."""
    
    def __init__(
        self,
        api_client: APIClient,
        max_workers: int = 5,
        progress_bar: bool = True
    ):
        """
        Initialize downloader.
        
        Args:
            api_client: API client instance
            max_workers: Maximum parallel download workers
            progress_bar: Show progress bar
        """
        self.api_client = api_client
        self.max_workers = max_workers
        self.show_progress = progress_bar
        self.download_queue: asyncio.Queue = asyncio.Queue()
        self.stats = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "total_bytes": 0,
        }
    
    async def download_opinions(
        self,
        opinions: List[Opinion],
        skip_existing: bool = True
    ) -> dict:
        """
        Download documents for all opinions.
        
        Args:
            opinions: List of opinions to download
            skip_existing: Skip already downloaded files
            
        Returns:
            Download statistics
        """
        if not opinions:
            return self.stats
        
        logger.info(f"Starting download of {len(opinions)} documents with {self.max_workers} workers")
        
        # Create download tasks
        tasks = []
        for opinion in opinions:
            # Check if already downloaded
            if skip_existing:
                exists = await self._check_file_exists(opinion)
                if exists:
                    self.stats["skipped"] += 1
                    await db_manager.update_download_status(
                        opinion.docket_entry_id,
                        DownloadStatus.SKIPPED
                    )
                    continue
            
            task = DownloadTask(opinion=opinion)
            await self.download_queue.put(task)
            tasks.append(task)
        
        if not tasks:
            logger.info(f"All {len(opinions)} documents already downloaded")
            return self.stats
        
        # Start workers
        workers = []
        for i in range(min(self.max_workers, len(tasks))):
            worker = asyncio.create_task(self._download_worker(i))
            workers.append(worker)
        
        # Progress bar
        if self.show_progress:
            progress_task = asyncio.create_task(
                self._show_progress(len(tasks))
            )
        
        # Wait for all downloads to complete
        await self.download_queue.join()
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        await asyncio.gather(*workers, return_exceptions=True)
        
        if self.show_progress:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
        
        logger.info(
            f"Download complete: {self.stats['successful']} successful, "
            f"{self.stats['failed']} failed, {self.stats['skipped']} skipped"
        )
        
        return self.stats
    
    async def _download_worker(self, worker_id: int):
        """Worker coroutine for processing downloads."""
        logger.debug(f"Worker {worker_id} started")
        
        while True:
            try:
                # Get task from queue
                task = await self.download_queue.get()
                
                # Process download
                await self._process_download(task, worker_id)
                
                # Mark task as done
                self.download_queue.task_done()
                
                # Small delay between downloads
                await asyncio.sleep(settings.rate_limit_delay)
                
            except asyncio.CancelledError:
                logger.debug(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
    
    async def _process_download(self, task: DownloadTask, worker_id: int):
        """Process a single download task."""
        opinion = task.opinion
        
        try:
            # Update status to downloading
            await db_manager.update_download_status(
                opinion.docket_entry_id,
                DownloadStatus.DOWNLOADING
            )
            
            # Get download URL
            logger.debug(f"Worker {worker_id}: Getting URL for {opinion.docket_number}")
            download_url = await self.api_client.get_document_url(
                opinion.docket_number,
                opinion.docket_entry_id
            )
            
            if not download_url:
                raise ValueError("Failed to get download URL")
            
            task.download_url = download_url
            
            # Download file
            logger.debug(f"Worker {worker_id}: Downloading {opinion.docket_number}")
            file_data = await self.api_client.download_file(download_url)
            
            if not file_data:
                raise ValueError("No data received")
            
            # Save file
            file_path = await self._save_file(opinion, file_data)
            task.file_path = str(file_path)
            task.file_size = len(file_data)
            
            # Update database
            await db_manager.update_download_status(
                opinion.docket_entry_id,
                DownloadStatus.COMPLETED,
                download_url=download_url,
                file_path=str(file_path),
                file_size=len(file_data)
            )
            
            # Update stats
            self.stats["successful"] += 1
            self.stats["total_bytes"] += len(file_data)
            
            task.status = DownloadStatus.COMPLETED
            task.completed_at = datetime.now()
            
            logger.info(
                f"Worker {worker_id}: Downloaded {opinion.docket_number} "
                f"({len(file_data) / 1024:.1f} KB)"
            )
            
        except Exception as e:
            logger.error(f"Worker {worker_id}: Failed to download {opinion.docket_number}: {e}")
            
            # Update database with failure
            await db_manager.update_download_status(
                opinion.docket_entry_id,
                DownloadStatus.FAILED,
                error_message=str(e)
            )
            
            # Update stats
            self.stats["failed"] += 1
            
            task.status = DownloadStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
    
    async def _save_file(self, opinion: Opinion, data: bytes) -> Path:
        """Save downloaded file to disk."""
        # Get file path
        filename = safe_filename(f"{opinion.docket_number}_{opinion.docket_entry_id}.pdf")
        file_path = settings.get_document_path(
            opinion.filing_date,
            filename
        )
        
        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)
        
        logger.debug(f"Saved {len(data)} bytes to {file_path}")
        return file_path
    
    async def _check_file_exists(self, opinion: Opinion) -> bool:
        """Check if file already exists."""
        # Check database first
        if await db_manager.check_already_downloaded(opinion.docket_entry_id):
            return True
        
        # Check filesystem
        if settings.skip_existing:
            filename = safe_filename(f"{opinion.docket_number}_{opinion.docket_entry_id}.pdf")
            file_path = settings.get_document_path(
                opinion.filing_date,
                filename
            )
            
            if file_path.exists() and file_path.stat().st_size > 0:
                # Update database
                await db_manager.update_download_status(
                    opinion.docket_entry_id,
                    DownloadStatus.COMPLETED,
                    file_path=str(file_path),
                    file_size=file_path.stat().st_size
                )
                return True
        
        return False
    
    async def _show_progress(self, total: int):
        """Show download progress bar."""
        with tqdm(
            total=total,
            desc="Downloading",
            unit="files",
            ncols=100
        ) as pbar:
            last_completed = 0
            
            while True:
                try:
                    await asyncio.sleep(0.5)
                    
                    completed = (
                        self.stats["successful"] +
                        self.stats["failed"] +
                        self.stats["skipped"]
                    )
                    
                    if completed > last_completed:
                        pbar.update(completed - last_completed)
                        last_completed = completed
                    
                    # Update description
                    pbar.set_description(
                        f"Downloading (✓{self.stats['successful']} "
                        f"✗{self.stats['failed']} →{self.stats['skipped']})"
                    )
                    
                    if completed >= total:
                        break
                        
                except asyncio.CancelledError:
                    break
    
    async def retry_failed_downloads(self, max_retries: int = 3):
        """Retry failed downloads from database."""
        failed = await db_manager.get_pending_downloads(limit=100)
        
        if not failed:
            logger.info("No failed downloads to retry")
            return
        
        logger.info(f"Retrying {len(failed)} failed downloads")
        
        # Convert to Opinion objects
        opinions = []
        for record in failed:
            try:
                opinion = Opinion(
                    entityName="PublicDocumentSearchResult",
                    caseCaption=record["case_caption"],
                    docketEntryId=record["docket_entry_id"],
                    docketNumber=record["docket_number"],
                    docketNumberWithSuffix=record["docket_number"],
                    documentTitle=record["document_title"],
                    documentType="Unknown",
                    eventCode="UNK",
                    filingDate=record["filing_date"].isoformat() if record["filing_date"] else "",
                    isStricken=False,
                    judge=record["judge"] or "Unknown",
                    numberOfPages=record["pages"] or 0,
                )
                
                if record["attempts"] < max_retries:
                    opinions.append(opinion)
                    
            except Exception as e:
                logger.error(f"Failed to parse failed download record: {e}")
        
        if opinions:
            await self.download_opinions(opinions, skip_existing=False)