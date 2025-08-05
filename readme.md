# US Tax Court Document Scraper

A high-performance, production-grade scraper for downloading US Tax Court opinions and documents from the Dawson API. Features parallel downloads, network resilience, and comprehensive error recovery.

## ✨ Features

- **🚀 Parallel Downloads**: Configurable worker pool for concurrent document downloads
- **🔄 Network Resilience**: Automatic retry with exponential backoff and connection pooling
- **💾 State Persistence**: SQLite database tracks downloads and enables resumption
- **📊 Progress Tracking**: Real-time progress bars and detailed statistics
- **🔍 Smart Deduplication**: Skip already-downloaded files automatically
- **📁 Organized Storage**: Documents organized by filing date (YYYY-MM folders)
- **🛡️ Error Recovery**: Resume interrupted downloads and retry failed ones
- **⚙️ Highly Configurable**: Environment variables and command-line options
- **📈 Performance Monitoring**: Detailed statistics and verification tools

## 📋 Requirements

- Python 3.10+ (tested with 3.13.5)
- pip package manager
- ~5-20GB storage for full 2020-2025 dataset
- Windows, macOS, or Linux

## 🚀 Installation

### Quick Setup

```bash
# Clone or download the project
cd web_scraper_legal

# Install all dependencies
pip install aiohttp aiofiles tqdm pydantic pydantic-settings \
            python-dotenv rich sqlalchemy aiosqlite tenacity \
            click PyPDF2 python-dateutil

# Create necessary directories
mkdir -p data/json data/documents data/db logs
```

### Verify Installation

```bash
# Test the installation
python run.py --help

# Run a quick test scrape (1 day)
python run.py --start-date 2024-12-01 --end-date 2024-12-02 --no-pdfs
```

## 📁 Project Structure

```
web_scraper_legal/
├── run.py                   # Main entry point
├── .env                     # Configuration (optional)
├── dawson_scraper/
│   └── src/
│       ├── __init__.py     # Package initialization
│       ├── config.py       # Settings management
│       ├── models.py       # Data models
│       ├── database.py     # SQLite persistence
│       ├── api_client.py   # Async API client
│       ├── downloader.py   # Parallel downloader
│       ├── scraper.py      # Main orchestration
│       └── utils.py        # Utilities
├── data/
│   ├── json/               # Monthly JSON files
│   ├── documents/          # PDFs organized by month (YYYY-MM)
│   └── db/                 # SQLite database
├── logs/                   # Application logs
├── CLAUDE.md               # AI assistant instructions
└── README.md               # This file
```

## ⚙️ Configuration

Create a `.env` file for custom settings (optional):

```bash
# .env file example
PARALLEL_WORKERS=5           # Number of concurrent downloads (1-20)
START_DATE=2020-01-01        # Beginning of scrape period
END_DATE=2024-12-31          # End of scrape period
DOWNLOAD_PDFS=true           # Enable/disable PDF downloads
SKIP_EXISTING=true           # Skip already-downloaded files
RATE_LIMIT_DELAY=0.2         # Delay between requests per worker
```

Or use command-line arguments to override defaults.

## 📖 Usage

### Basic Usage

```bash
# Full scrape with PDFs (2020 to today)
python run.py

# Custom date range
python run.py --start-date 2024-01-01 --end-date 2024-12-31

# More parallel workers for faster downloads
python run.py --workers 10

# JSON only (no PDFs)
python run.py --no-pdfs
```

### Advanced Operations

```bash
# Download PDFs from existing JSON files
python run.py --pdfs-only

# Resume interrupted downloads
python run.py --resume

# Show statistics
python run.py --stats

# Verify all downloaded PDFs
python run.py --verify
```

### Command-Line Options

```bash
Options:
  --start-date DATE    Start date (YYYY-MM-DD)
  --end-date DATE      End date (YYYY-MM-DD)
  --workers N          Number of parallel workers (1-20)
  --no-pdfs           Skip PDF downloads
  --pdfs-only         Only download PDFs from existing JSON
  --resume            Resume interrupted downloads
  --stats             Show statistics
  --verify            Verify all downloads
  --help              Show help message
```

## 📊 Performance

Expected performance with default settings:

| Metric | Value |
|--------|-------|
| Opinions per month | ~100-200 |
| Download speed | ~5-10 docs/minute |
| Total time (2020-2025) | 3-5 hours |
| Storage required | 5-20 GB |
| Network usage | 10-30 GB |

### Optimization Tips

1. **Increase workers** for faster downloads (up to 20):
   ```bash
   python run.py --workers 15
   ```

2. **Run in tmux/screen** for long sessions:
   ```bash
   tmux new -s dawson
   python run.py
   # Ctrl+B, D to detach
   ```

3. **Monitor progress** via logs:
   ```bash
   tail -f logs/dawson_scraper.log
   ```

## 🔧 Troubleshooting

### Common Issues

**Rate limiting errors**
- Reduce `PARALLEL_WORKERS` in `.env`
- Increase `RATE_LIMIT_DELAY`

**Memory usage high**
- Reduce `MAX_CONCURRENT_DOWNLOADS`
- Process smaller date ranges

**Downloads failing**
- Check network connectivity
- Run `--resume` to retry failures
- Check logs for specific errors

### Recovery Options

```bash
# Retry all failed downloads
python run.py --resume

# Re-download specific period
python run.py --start-date 2024-06-01 --end-date 2024-06-30

# Verify and identify corrupted files
python run.py --verify
```

## 📈 Database Schema

The SQLite database tracks:

- **downloads**: Document download status and metadata
- **searches**: Monthly search operations and results

Query the database:

```sql
sqlite3 data/db/dawson_scraper.db

-- Check download statistics
SELECT status, COUNT(*), SUM(file_size)/1024/1024 as MB 
FROM downloads 
GROUP BY status;

-- Find failed downloads
SELECT docket_number, error_message 
FROM downloads 
WHERE status = 'failed';
```

## 🛠️ Development

### Code Quality

```bash
# Code formatting
black dawson_scraper/src/
ruff check dawson_scraper/src/

# Type checking (requires mypy)
pip install mypy
mypy dawson_scraper/src/
```

### Adding Features

The modular architecture makes it easy to extend:

1. **Custom document filters**: Modify `Opinion` model validation
2. **Alternative storage**: Override `_save_file` in `ParallelDownloader`
3. **Different APIs**: Extend `APIClient` with new endpoints
4. **Export formats**: Add methods to `ScraperStats`

## 📝 API Reference

### Main Classes

**DawsonScraper**
- `run()`: Main scraping orchestration
- `resume_interrupted()`: Resume failed downloads
- `process_existing_json()`: Download PDFs from JSON

**APIClient**
- `fetch_opinions()`: Get opinions for date range
- `get_document_url()`: Get PDF download URL
- `download_file()`: Download with progress

**ParallelDownloader**
- `download_opinions()`: Parallel download manager
- `retry_failed_downloads()`: Retry failures

## 🔒 Security & Compliance

- Respects rate limits with configurable delays
- User-Agent headers match standard browsers
- Connection pooling for efficient resource use
- No authentication bypass or scraping of protected content

## 📄 License

This project is for educational and research purposes. Ensure compliance with the US Tax Court's terms of service when using this tool.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📮 Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review logs in `logs/dawson_scraper.log`
3. Search existing issues
4. Create a new issue with details

---

**Note**: This scraper is designed for legitimate research and archival purposes. Please use responsibly and in accordance with applicable laws and terms of service.