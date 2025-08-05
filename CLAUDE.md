# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a US Tax Court document scraper that downloads opinions and documents from the Dawson API. It features parallel downloads, network resilience, state persistence via SQLite, and comprehensive error recovery.

## Architecture

### Core Components

- **run.py**: Main entry point with CLI interface using Click
- **dawson_scraper/src/scraper.py**: Main orchestration logic that coordinates the scraping process
- **dawson_scraper/src/api_client.py**: Async HTTP client for Dawson API interactions
- **dawson_scraper/src/downloader.py**: Parallel download manager with worker pool
- **dawson_scraper/src/database.py**: SQLite persistence layer for tracking downloads and state
- **dawson_scraper/src/config.py**: Pydantic settings management with environment variable support
- **dawson_scraper/src/models.py**: Data models for opinions and statistics
- **dawson_scraper/src/utils.py**: Utility functions for logging, file operations, and date handling

### Data Flow

1. DawsonScraper generates monthly periods from start/end dates
2. APIClient fetches JSON metadata for each period via search API
3. ParallelDownloader manages worker pool to download PDFs concurrently
4. Database tracks download status, enabling resume on interruption
5. Files are organized by month in data/documents/YYYY-MM/ folders

## Development Commands

```bash
# Install dependencies
pip install aiohttp aiofiles tqdm pydantic pydantic-settings python-dotenv rich sqlalchemy aiosqlite tenacity click PyPDF2 python-dateutil

# Run the scraper (basic usage)
python run.py

# Run with custom parameters
python run.py --start-date 2024-01-01 --end-date 2024-12-31 --workers 10

# Resume interrupted downloads
python run.py --resume

# Show statistics
python run.py --stats

# Verify downloaded PDFs
python run.py --verify

# Run without downloading PDFs (metadata only)
python run.py --no-pdfs

# Download PDFs from existing JSON files
python run.py --pdfs-only

# Code formatting
black dawson_scraper/src/
ruff check dawson_scraper/src/

# Type checking
mypy dawson_scraper/src/

# Run tests
pytest tests/
```

## Key Configuration

Settings are managed via environment variables or .env file:

- `PARALLEL_WORKERS`: Number of concurrent download workers (1-20, default: 5)
- `START_DATE`: Beginning of scrape period (YYYY-MM-DD)
- `DOWNLOAD_PDFS`: Enable/disable PDF downloads (true/false)
- `SKIP_EXISTING`: Skip already-downloaded files (true/false)
- `RATE_LIMIT_DELAY`: Delay between requests per worker (seconds)

## Database Schema

SQLite database at `data/db/dawson_scraper.db`:

- **downloads** table: Tracks each document download (status, file_size, error_message)
- **searches** table: Tracks monthly search operations and results

## Network Resilience Features

- Exponential backoff with jitter on failures
- Connection pooling and HTTP session reuse
- Automatic retry with configurable attempts
- Resume capability from database state
- Rate limiting per worker to avoid overwhelming API

## Recent Updates and Fixes

### Fixed Issues
- **Module imports**: Updated import paths to match `dawson_scraper/src` structure
- **Tenacity compatibility**: Fixed imports for newer tenacity versions (removed deprecated `before_retry`/`after_retry`)
- **Model validation**: Made `judge` field optional with proper alias mapping (`signedJudgeName`)
- **Database queries**: Fixed SQLite parameter binding in `cleanup_stale_downloads`
- **Windows compatibility**: Replaced Unicode symbols (✓, ⚠, ✗) with ASCII alternatives to avoid encoding issues
- **Download tracking**: Fixed `document_id` reference to use `docket_entry_id`
- **Progress display**: Removed SpinnerColumn to avoid Unicode issues on Windows

### Dependencies Added
- `PyPDF2`: For PDF verification
- `python-dateutil`: For date handling utilities

## Testing Approach

Per user instructions: Tests use actual APIs and data, not mocks. When testing functionality that requires data, request actual test data rather than using mocks.

### Test Results
- Successfully connects to Dawson Court API
- Downloads and verifies PDF documents correctly
- SQLite database properly tracks download status
- Resume functionality works as expected
- Statistics and verification commands functioning