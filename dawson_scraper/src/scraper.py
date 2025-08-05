"""Main scraper orchestration logic."""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import Opinion, OpinionBatch, ScraperStats
from .api_client import APIClient
from .downloader import ParallelDownloader
from .database import db_manager
from .config import settings
from .utils import get_logger, generate_monthly_periods


logger = get_logger(__name__)
console = Console()


class DawsonScraper:
    """Main scraper orchestrator."""
    
    def __init__(self):
        """Initialize scraper."""
        self.api_client = APIClient(max_concurrent=settings.max_concurrent_downloads)
        self.downloader = ParallelDownloader(
            self.api_client,
            max_workers=settings.parallel_workers
        )
        self.stats = ScraperStats()
    
    async def run(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        download_pdfs: Optional[bool] = None
    ):
        """
        Run the complete scraping process.
        
        Args:
            start_date: Start date (defaults to config)
            end_date: End date (defaults to config)
            download_pdfs: Whether to download PDFs (defaults to config)
        """
        start_date = start_date or settings.start_date
        end_date = end_date or settings.end_date
        download_pdfs = download_pdfs if download_pdfs is not None else settings.download_pdfs
        
        console.print("\n[bold cyan]US Tax Court Document Scraper[/bold cyan]")
        console.print("=" * 60)
        
        # Initialize database
        await db_manager.initialize()
        
        # Clean up stale downloads
        await db_manager.cleanup_stale_downloads()
        
        # Start API client
        await self.api_client.start()
        
        try:
            # Generate monthly periods
            periods = generate_monthly_periods(start_date, end_date)
            self.stats.total_periods = len(periods)
            
            console.print(f"[green]Date range:[/green] {start_date.date()} to {end_date.date()}")
            console.print(f"[green]Periods to process:[/green] {len(periods)}")
            console.print(f"[green]PDF downloads:[/green] {'Enabled' if download_pdfs else 'Disabled'}")
            console.print(f"[green]Parallel workers:[/green] {settings.parallel_workers}")
            console.print("=" * 60 + "\n")
            
            # Process each period
            for i, (period_start, period_end) in enumerate(periods, 1):
                await self._process_period(
                    period_start,
                    period_end,
                    i,
                    len(periods),
                    download_pdfs
                )
                
                # Rate limiting between periods
                if i < len(periods):
                    await asyncio.sleep(1.0)
            
            # Final statistics
            self.stats.end_time = datetime.now()
            await self._print_summary()
            
        finally:
            await self.api_client.close()
    
    async def _process_period(
        self,
        start_date: datetime,
        end_date: datetime,
        current: int,
        total: int,
        download_pdfs: bool
    ):
        """Process a single time period."""
        period_str = f"{start_date.strftime('%Y-%m')}"
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(
                f"[cyan]Period {current}/{total}:[/cyan] {period_str}",
                total=None
            )
            
            try:
                # Fetch opinions
                progress.update(task, description=f"[cyan]Period {current}/{total}:[/cyan] Fetching {period_str}")
                opinions = await self.api_client.fetch_opinions(start_date, end_date)
                
                if opinions:
                    # Save JSON
                    batch = OpinionBatch(
                        start_date=start_date,
                        end_date=end_date,
                        opinions=opinions
                    )
                    json_path = await self._save_json(batch)
                    
                    # Record in database
                    for opinion in opinions:
                        await db_manager.record_opinion(opinion)
                    
                    await db_manager.record_search(
                        start_date,
                        end_date,
                        len(opinions),
                        str(json_path)
                    )
                    
                    # Update stats
                    self.stats.successful_searches += 1
                    self.stats.total_opinions += len(opinions)
                    
                    console.print(
                        f"  [green][OK][/green] Found {len(opinions)} opinions for {period_str}"
                    )
                    
                    # Download PDFs if enabled
                    if download_pdfs and opinions:
                        progress.update(
                            task,
                            description=f"[cyan]Period {current}/{total}:[/cyan] Downloading {len(opinions)} documents"
                        )
                        
                        download_stats = await self.downloader.download_opinions(
                            opinions,
                            skip_existing=settings.skip_existing
                        )
                        
                        # Update global stats
                        self.stats.successful_downloads += download_stats["successful"]
                        self.stats.failed_downloads += download_stats["failed"]
                        self.stats.skipped_downloads += download_stats["skipped"]
                        self.stats.total_bytes_downloaded += download_stats["total_bytes"]
                        
                        console.print(
                            f"    Downloads: [green]{download_stats['successful']}[/green] successful, "
                            f"[red]{download_stats['failed']}[/red] failed, "
                            f"[yellow]{download_stats['skipped']}[/yellow] skipped"
                        )
                else:
                    # No opinions found
                    await db_manager.record_search(
                        start_date,
                        end_date,
                        0,
                        "",
                        status="empty"
                    )
                    
                    console.print(f"  [yellow][!][/yellow] No opinions found for {period_str}")
                    
            except Exception as e:
                logger.error(f"Failed to process period {period_str}: {e}")
                
                # Record failure
                await db_manager.record_search(
                    start_date,
                    end_date,
                    0,
                    "",
                    status="failed",
                    error_message=str(e)
                )
                
                self.stats.failed_searches += 1
                console.print(f"  [red][X][/red] Failed to process {period_str}: {e}")
    
    async def _save_json(self, batch: OpinionBatch) -> Path:
        """Save opinion batch to JSON file."""
        file_path = settings.json_dir / batch.json_filename
        
        data = {
            "_metadata": {
                "fetch_timestamp": datetime.now().isoformat(),
                "start_date": batch.start_date.strftime("%m/%d/%Y"),
                "end_date": batch.end_date.strftime("%m/%d/%Y"),
                "opinion_types": "MOP,SOP,OST,TCOP",
                "record_count": len(batch.opinions),
            },
            "opinions": [opinion.model_dump(by_alias=True) for opinion in batch.opinions]
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved JSON: {file_path.name} ({len(batch.opinions)} records)")
        return file_path
    
    async def _print_summary(self):
        """Print final summary statistics."""
        console.print("\n" + "=" * 60)
        console.print("[bold cyan]SCRAPING COMPLETE[/bold cyan]")
        console.print("=" * 60)
        
        # Get database statistics
        db_stats = await db_manager.get_statistics()
        
        # Create summary table
        table = Table(title="Summary Statistics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Time stats
        duration = self.stats.duration
        if duration:
            table.add_row("Total Duration", f"{duration:.1f} seconds")
            table.add_row("Average Speed", f"{duration / self.stats.total_periods:.1f} sec/period")
        
        # Search stats
        table.add_row("Periods Processed", f"{self.stats.successful_searches}/{self.stats.total_periods}")
        table.add_row("Total Opinions Found", str(self.stats.total_opinions))
        
        # Download stats
        if settings.download_pdfs:
            table.add_row("Successful Downloads", str(self.stats.successful_downloads))
            table.add_row("Failed Downloads", str(self.stats.failed_downloads))
            table.add_row("Skipped Downloads", str(self.stats.skipped_downloads))
            table.add_row("Success Rate", f"{self.stats.success_rate:.1f}%")
            table.add_row("Total Data Downloaded", f"{self.stats.total_bytes_downloaded / (1024**2):.1f} MB")
        
        # Paths
        table.add_row("Data Directory", str(settings.data_dir))
        table.add_row("JSON Directory", str(settings.json_dir))
        if settings.download_pdfs:
            table.add_row("Documents Directory", str(settings.documents_dir))
        
        console.print(table)
        
        # Show recent failures if any
        if db_stats["recent_failures"]:
            console.print("\n[bold red]Recent Failures:[/bold red]")
            for failure in db_stats["recent_failures"][:5]:
                console.print(f"  • {failure['docket']}: {failure['error']}")
    
    async def resume_interrupted(self):
        """Resume interrupted downloads."""
        console.print("[cyan]Resuming interrupted downloads...[/cyan]")
        
        await db_manager.initialize()
        await self.api_client.start()
        
        try:
            await self.downloader.retry_failed_downloads()
        finally:
            await self.api_client.close()
    
    async def process_existing_json(self):
        """Process existing JSON files to download PDFs."""
        console.print("[cyan]Processing existing JSON files...[/cyan]")
        
        await db_manager.initialize()
        await self.api_client.start()
        
        try:
            json_files = sorted(settings.json_dir.glob("opinions_*.json"))
            
            if not json_files:
                console.print("[yellow]No JSON files found[/yellow]")
                return
            
            console.print(f"Found {len(json_files)} JSON files")
            
            for json_file in json_files:
                console.print(f"\nProcessing: {json_file.name}")
                
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    opinions_data = data.get("opinions", [])
                    if not opinions_data:
                        continue
                    
                    # Convert to Opinion objects
                    opinions = []
                    for item in opinions_data:
                        try:
                            opinion = Opinion(**item)
                            opinions.append(opinion)
                            await db_manager.record_opinion(opinion)
                        except Exception as e:
                            logger.error(f"Failed to parse opinion: {e}")
                    
                    if opinions:
                        download_stats = await self.downloader.download_opinions(opinions)
                        console.print(
                            f"  Downloads: {download_stats['successful']} successful, "
                            f"{download_stats['failed']} failed, "
                            f"{download_stats['skipped']} skipped"
                        )
                        
                except Exception as e:
                    logger.error(f"Failed to process {json_file.name}: {e}")
                    
        finally:
            await self.api_client.close()