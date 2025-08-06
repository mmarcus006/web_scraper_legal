# US Tax Court Document Scraper - Project Structure

## Current Directory Layout

```
web_scraper_legal/
├── run.py                   # Main entry point with CLI interface
├── pyproject.toml           # Project configuration & dependencies
├── uv.lock                  # UV package manager lock file
├── README.md                # Main documentation
├── CLAUDE.md                # AI assistant instructions
├── project-structure.md     # This file
│
├── dawson_scraper/
│   ├── src/
│   │   ├── __init__.py      # Package initialization
│   │   ├── config.py        # Configuration management (Pydantic)
│   │   ├── models.py        # Data models/schemas
│   │   ├── database.py      # SQLite tracking database
│   │   ├── api_client.py    # Async API client with retry logic
│   │   ├── downloader.py    # Parallel download manager
│   │   ├── scraper.py       # Main orchestration logic
│   │   └── utils.py         # Utility functions
│   │
│   └── scripts/             # Additional scripts (placeholder)
│
├── data/
│   ├── json/               # JSON metadata files
│   │   └── opinions_YYYY-MM-DD_to_YYYY-MM-DD.json
│   ├── documents/          # Downloaded PDFs organized by month
│   │   └── YYYY-MM/
│   │       └── docket-number_uuid.pdf
│   └── db/                 # SQLite database
│       └── dawson_scraper.db
│
└── logs/                   # Application and hook logs
    ├── dawson_scraper.log  # Main application log
    └── *.json              # Hook logs (if configured)
```

## Key Components

### 1. **Entry Point (run.py)**
- Click-based CLI interface
- Command-line argument parsing
- Main orchestration entry
- Special modes: --stats, --verify, --resume

### 2. **Core Modules (dawson_scraper/src/)**

#### config.py
- Pydantic settings management
- Environment variable loading
- Configuration validation
- Path management

#### models.py
- Pydantic data models
- Opinion, DownloadStatus, ScraperStats
- Field validation and aliasing
- JSON serialization support

#### database.py
- SQLite async operations with aiosqlite
- Download tracking (status, attempts, errors)
- Search operation logging
- Statistics generation
- Resume capability support

#### api_client.py
- Async HTTP client with aiohttp
- Connection pooling
- Retry logic with tenacity
- Rate limiting
- Progress tracking

#### downloader.py
- Parallel download orchestration
- Worker pool management
- File organization by month
- Progress bars with tqdm
- Error handling and retry

#### scraper.py
- Main orchestration logic
- Monthly period generation
- JSON metadata saving
- Download coordination
- Statistics reporting

#### utils.py
- Logging configuration
- Date utilities
- File operations
- PDF verification
- Filename sanitization

### 3. **Data Storage**

#### JSON Files (data/json/)
- Monthly opinion metadata
- Search results caching
- Named by date range
- Used for resume/retry

#### PDF Documents (data/documents/)
- Organized by filing month (YYYY-MM)
- Named: docket-number_uuid.pdf
- Verified after download
- ~100-500KB per file

#### SQLite Database (data/db/)
- `downloads` table: Track each document
- `searches` table: Track API searches
- Enables resume functionality
- Statistics generation

## Features Implementation

### Parallel Downloads
- Configurable worker pool (1-20 workers)
- Async/await with aiohttp
- Per-worker rate limiting
- Connection reuse

### Network Resilience
- Exponential backoff with jitter
- Automatic retry (3 attempts default)
- Connection pooling
- Timeout handling
- Resume from interruption

### Progress Tracking
- Real-time progress bars
- Download speed monitoring
- Success/failure counts
- File size tracking
- ETA calculation

### Error Recovery
- Database state persistence
- Failed download tracking
- Resume command
- Retry failed downloads
- Verification tool

## Configuration

### Environment Variables (.env)
```env
# API Settings
API_BASE_URL=https://public-api-green.dawson.ustaxcourt.gov/public-api
API_TIMEOUT=30
MAX_CONCURRENT_CONNECTIONS=10

# Download Settings
PARALLEL_WORKERS=5
RATE_LIMIT_DELAY=0.2
CHUNK_SIZE=8192
SKIP_EXISTING=true
DOWNLOAD_PDFS=true

# Date Range
START_DATE=2020-01-01
END_DATE=2024-12-31

# Paths
DATA_DIR=./data
LOG_DIR=./logs
```

### Command-Line Options
- `--start-date`: Override start date
- `--end-date`: Override end date
- `--workers`: Number of parallel workers
- `--no-pdfs`: Skip PDF downloads
- `--pdfs-only`: Download PDFs from existing JSON
- `--resume`: Resume interrupted downloads
- `--stats`: Show statistics
- `--verify`: Verify downloaded PDFs

## Dependencies

### Core Dependencies
- `aiohttp`: Async HTTP client
- `aiofiles`: Async file operations
- `aiosqlite`: Async SQLite
- `pydantic`: Data validation
- `pydantic-settings`: Settings management
- `click`: CLI framework
- `rich`: Terminal formatting
- `tqdm`: Progress bars
- `tenacity`: Retry logic
- `python-dotenv`: Environment variables

### Additional Dependencies
- `PyPDF2`: PDF verification
- `python-dateutil`: Date utilities
- `sqlalchemy`: ORM (for schema definition)

## Testing & Development

### Code Quality Tools
- `black`: Code formatting
- `ruff`: Linting
- `mypy`: Type checking

### Testing Approach
- Use actual API for testing (no mocks)
- Test with small date ranges
- Verify PDF downloads
- Check database tracking
- Test resume functionality

## Performance Metrics

### Typical Performance
- ~100-200 opinions per month
- ~5-10 documents per minute
- ~100-500KB per PDF
- 3-5 hours for full 2020-2024 dataset
- 5-20GB total storage

### Optimization
- Increase workers for faster downloads
- Adjust rate limiting for API limits
- Use SSD for better I/O performance
- Monitor memory usage with large datasets

## Error Handling

### Common Issues
- Rate limiting: Reduce workers, increase delay
- Connection errors: Automatic retry with backoff
- Invalid PDFs: Logged and marked as failed
- Disk space: Monitor available storage
- Unicode issues: Fixed for Windows compatibility

### Recovery Methods
- Resume: Continue from last successful point
- Retry: Re-attempt failed downloads
- Verify: Check PDF integrity
- Stats: Monitor progress and failures