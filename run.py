#!/usr/bin/env python
"""
Main entry point for Dawson Court Scraper.

Usage:
    python run.py [OPTIONS]
    
Options:
    --start-date DATE      Start date (YYYY-MM-DD)
    --end-date DATE        End date (YYYY-MM-DD)
    --workers N            Number of parallel workers
    --no-pdfs              Skip PDF downloads
    --pdfs-only            Only download PDFs from existing JSON
    --resume               Resume interrupted downloads
    --stats                Show statistics
    --verify               Verify all downloads
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dawson_scraper.src.scraper import DawsonScraper
from dawson_scraper.src.config import settings
from dawson_scraper.src.database import db_manager
from dawson_scraper.src.utils import get_logger, verify_pdf


# Load environment variables
load_dotenv()

logger = get_logger(__name__)
console = Console()


@click.command()
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date for scraping"
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date for scraping"
)
@click.option(
    "--workers",
    type=int,
    help="Number of parallel download workers"
)
@click.option(
    "--no-pdfs",
    is_flag=True,
    help="Skip PDF downloads"
)
@click.option(
    "--pdfs-only",
    is_flag=True,
    help="Only download PDFs from existing JSON files"
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume interrupted downloads"
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show statistics and exit"
)
@click.option(
    "--verify",
    is_flag=True,
    help="Verify all downloaded PDFs"
)
def main(
    start_date,
    end_date,
    workers,
    no_pdfs,
    pdfs_only,
    resume,
    stats,
    verify
):
    """US Tax Court Document Scraper - Main Entry Point."""
    
    try:
        # Handle special modes first
        if stats:
            asyncio.run(show_stats())
            return
        
        if verify:
            asyncio.run(verify_downloads())
            return
        
        # Update settings if provided
        if workers:
            settings.parallel_workers = workers
        
        if start_date:
            settings.start_date = start_date
        
        if end_date:
            settings.end_date = end_date
        
        # Run appropriate mode
        scraper = DawsonScraper()
        
        if resume:
            asyncio.run(scraper.resume_interrupted())
        elif pdfs_only:
            asyncio.run(scraper.process_existing_json())
        else:
            asyncio.run(scraper.run(
                start_date=start_date,
                end_date=end_date,
                download_pdfs=not no_pdfs
            ))
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Fatal error")
        sys.exit(1)


async def show_stats():
    """Show download statistics."""
    console.print("[cyan]Loading statistics...[/cyan]\n")
    
    await db_manager.initialize()
    stats = await db_manager.get_statistics()
    
    # Downloads summary
    console.print("[bold]Download Statistics:[/bold]")
    for status, info in stats["downloads"].items():
        console.print(f"  {status.capitalize()}: {info['count']} files ({info['size'] / (1024**2):.1f} MB)")
    
    # Search summary
    console.print(f"\n[bold]Search Statistics:[/bold]")
    console.print(f"  Total searches: {stats['searches']['total']}")
    console.print(f"  Opinions found: {stats['searches']['opinions_found']}")
    
    # Recent failures
    if stats["recent_failures"]:
        console.print(f"\n[bold]Recent Failures:[/bold]")
        for failure in stats["recent_failures"]:
            console.print(f"  • {failure['docket']}: {failure['error'][:50]}...")
    
    # File system stats
    json_files = list(settings.json_dir.glob("*.json"))
    pdf_files = list(settings.documents_dir.rglob("*.pdf"))
    
    console.print(f"\n[bold]File System:[/bold]")
    console.print(f"  JSON files: {len(json_files)}")
    console.print(f"  PDF files: {len(pdf_files)}")
    
    if pdf_files:
        total_size = sum(f.stat().st_size for f in pdf_files)
        console.print(f"  Total size: {total_size / (1024**2):.1f} MB")


async def verify_downloads():
    """Verify all downloaded PDFs."""
    console.print("[cyan]Verifying downloads...[/cyan]\n")
    
    pdf_files = list(settings.documents_dir.rglob("*.pdf"))
    
    if not pdf_files:
        console.print("[yellow]No PDF files found[/yellow]")
        return
    
    console.print(f"Found {len(pdf_files)} PDF files to verify\n")
    
    valid = 0
    invalid = []
    
    with console.status("Verifying PDFs...") as status:
        for i, pdf_file in enumerate(pdf_files, 1):
            status.update(f"Verifying {i}/{len(pdf_files)}: {pdf_file.name}")
            
            if verify_pdf(pdf_file):
                valid += 1
            else:
                invalid.append(pdf_file)
    
    console.print(f"\n[green]Valid PDFs:[/green] {valid}")
    console.print(f"[red]Invalid PDFs:[/red] {len(invalid)}")
    
    if invalid:
        console.print("\n[bold red]Invalid files:[/bold red]")
        for file in invalid[:10]:  # Show first 10
            console.print(f"  • {file.relative_to(settings.documents_dir)}")
        
        if len(invalid) > 10:
            console.print(f"  ... and {len(invalid) - 10} more")


if __name__ == "__main__":
    main()