# Setup Guide

## Prerequisites

### System Requirements
- **Python**: Version 3.10 or higher (tested with 3.13.5)
- **pip**: Python package manager
- **Storage**: 5-20 GB available disk space for full dataset
- **Memory**: Minimum 2 GB RAM recommended
- **Network**: Stable internet connection for API access

### Operating System Support
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+, CentOS 8+, or equivalent)

## Installation Steps

### 1. Clone or Download Project

```bash
# If using git
git clone <repository-url> web_scraper_legal
cd web_scraper_legal

# Or download and extract ZIP file
unzip web_scraper_legal.zip
cd web_scraper_legal
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install all required packages
pip install aiohttp aiofiles tqdm pydantic pydantic-settings \
            python-dotenv rich sqlalchemy aiosqlite tenacity \
            click PyPDF2 python-dateutil

# Or if using uv package manager
uv sync
```

### 4. Create Required Directories

```bash
# Create data and log directories
mkdir -p data/json data/documents data/db logs

# On Windows PowerShell:
New-Item -ItemType Directory -Force -Path data\json, data\documents, data\db, logs
```

### 5. Configure Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
# .env configuration file

# Worker Configuration
PARALLEL_WORKERS=5              # Number of concurrent download workers (1-20, default: 5)
MAX_CONCURRENT_DOWNLOADS=50     # Maximum concurrent downloads per worker (default: 50)

# Date Range
START_DATE=2020-01-01           # Start date for scraping (YYYY-MM-DD)
END_DATE=2024-12-31             # End date for scraping (YYYY-MM-DD)

# Download Behavior
DOWNLOAD_PDFS=true              # Enable/disable PDF downloads (default: true)
SKIP_EXISTING=true              # Skip already-downloaded files (default: true)
VERIFY_PDFS=false               # Verify PDF integrity after download (default: false)

# API Configuration
BASE_URL=https://dawson.uscourts.gov/api  # Dawson API base URL
RATE_LIMIT_DELAY=0.2            # Delay between requests per worker in seconds

# Retry Configuration
MAX_RETRIES=3                   # Maximum retry attempts for failed downloads
RETRY_DELAY=5                   # Initial retry delay in seconds

# File Paths (usually not needed to change)
JSON_DIR=data/json              # Directory for JSON metadata files
PDF_DIR=data/documents          # Directory for PDF documents
DB_PATH=data/db/dawson_scraper.db  # SQLite database path
LOG_FILE=logs/dawson_scraper.log   # Log file path
```

## Verification

### Test Installation

```bash
# Display help information
python run.py --help

# Run a quick test (1 day, metadata only)
python run.py --start-date 2024-12-01 --end-date 2024-12-02 --no-pdfs
```

### Expected Output
You should see:
- Progress bars showing JSON fetching
- Log messages in `logs/dawson_scraper.log`
- JSON file created in `data/json/`
- Database file created in `data/db/`

## Run Commands

### Basic Usage

```bash
# Full scrape with default settings (2020 to today)
python run.py

# Custom date range
python run.py --start-date 2024-01-01 --end-date 2024-12-31

# Increase parallel workers for faster downloads
python run.py --workers 10
```

### Advanced Operations

```bash
# Download metadata only (no PDFs)
python run.py --no-pdfs

# Download PDFs from existing JSON files
python run.py --pdfs-only

# Resume interrupted downloads
python run.py --resume

# Show download statistics
python run.py --stats

# Verify all downloaded PDFs
python run.py --verify
```

## Development Setup

### Install Development Dependencies

```bash
# Install dev tools
pip install pytest pytest-asyncio black ruff mypy

# Or using pyproject.toml
pip install -e ".[dev]"
```

### Code Quality Tools

```bash
# Format code
black dawson_scraper/src/

# Lint code
ruff check dawson_scraper/src/

# Type checking
mypy dawson_scraper/src/

# Run tests
pytest tests/
```

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Ensure virtual environment is activated
   - Verify all dependencies are installed: `pip list`

2. **Permission Denied Errors**
   - Check write permissions for data/ and logs/ directories
   - On Windows, run as administrator if needed

3. **Connection Errors**
   - Verify internet connectivity
   - Check if Dawson API is accessible: `curl https://dawson.uscourts.gov/api/search`
   - Reduce PARALLEL_WORKERS if rate limited

4. **Memory Issues**
   - Reduce MAX_CONCURRENT_DOWNLOADS in .env
   - Process smaller date ranges

5. **Disk Space Issues**
   - Check available disk space: `df -h` (Linux/macOS) or `dir` (Windows)
   - Consider downloading in batches

### Log Files

Check logs for detailed error information:
```bash
# View recent log entries
tail -n 50 logs/dawson_scraper.log

# Monitor logs in real-time
tail -f logs/dawson_scraper.log
```

## Next Steps

1. Review the [API Contracts](api_contracts.md) to understand the Dawson API
2. Check [Database Schema](database_schema.md) for data structure details
3. Run `python run.py --help` for all available options
4. Start with a small date range to test your setup