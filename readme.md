# US Tax Court Document Processing System

A comprehensive, production-grade system for scraping, processing, and searching US Tax Court documents. Features advanced PDF processing with IBM Docling, OCR support, GPU acceleration, and AI-powered semantic search using LlamaIndex.

## 🌟 Key Features

### Document Scraping & Download
- **🚀 Parallel Downloads**: Configurable worker pool for concurrent document downloads
- **🔄 Network Resilience**: Automatic retry with exponential backoff and connection pooling
- **💾 State Persistence**: SQLite database tracks downloads and enables resumption
- **📊 Progress Tracking**: Real-time progress bars and detailed statistics
- **🔍 Smart Deduplication**: Skip already-downloaded files automatically

### Advanced PDF Processing
- **🤖 IBM Docling Integration**: State-of-the-art PDF processing with AI models
- **📝 OCR Support**: Extract text from scanned documents using RapidOCR
- **📊 Table Recognition**: Advanced table structure extraction with TableFormer
- **⚡ GPU Acceleration**: CUDA support for 2-5x faster processing
- **📄 Markdown Conversion**: Convert PDFs to searchable markdown format

### AI-Powered Search (RAG)
- **🔍 Semantic Search**: Find relevant documents using natural language queries
- **🎯 Vector Embeddings**: HuggingFace models for document understanding
- **💾 Vector Database**: ChromaDB for efficient similarity search
- **🏷️ Metadata Filtering**: Search by year, month, docket number, judge
- **📈 LlamaIndex Integration**: Production-ready RAG system

## 📋 Requirements

- **Python 3.10 - 3.12** (Python 3.13 not yet supported due to dependencies)
- **Storage**: 5-20GB for full 2020-2025 dataset
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Optional, CUDA 11.8+ for acceleration
- **OS**: Windows, macOS, or Linux

### Windows Prerequisites
For Windows users, install Microsoft C++ Build Tools:
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install with "Desktop development with C++" workload

## 🚀 Installation

### 1. Create Virtual Environment

```bash
# Use Python 3.11 or 3.12 (recommended)
python3.11 -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 2. Install Package

```bash
# Clone repository
git clone <repository-url>
cd web_scraper_legal

# Install with all features
pip install -e .

# Or use uv for faster installation
uv pip install -e .
```

### 3. Create Required Directories

```bash
# Windows PowerShell:
New-Item -ItemType Directory -Force -Path data\json, data\documents, data\db, logs, data\markdown_documents, data\vector_store

# macOS/Linux:
mkdir -p data/{json,documents,db,markdown_documents,vector_store} logs
```

## 📖 Quick Start

### 1. Scrape Documents

```bash
# Basic scraping (2020 to today)
python run.py

# Custom date range
python run.py --start-date 2024-01-01 --end-date 2024-12-31

# Faster with more workers
python run.py --workers 10
```

### 2. Convert PDFs to Markdown

```bash
# Process all PDFs
python -m dawson_scraper.src.cli_rag process-pdfs

# With more workers
python -m dawson_scraper.src.cli_rag process-pdfs --workers 8

# Enable Vision-Language Model for better accuracy
python -m dawson_scraper.src.cli_rag process-pdfs --enable-vlm
```

### 3. Build Search Index

```bash
# Create vector index
python -m dawson_scraper.src.cli_rag build-index

# Update existing index
python -m dawson_scraper.src.cli_rag build-index --incremental
```

### 4. Search Documents

```bash
# Basic search
python -m dawson_scraper.src.cli_rag search "capital gains tax"

# Search with filters
python -m dawson_scraper.src.cli_rag search "medical expenses" --year 2023

# Get more results
python -m dawson_scraper.src.cli_rag search "partnership" --top-k 10
```

## 📁 Project Structure

```
web_scraper_legal/
├── run.py                      # Main scraper entry point
├── pyproject.toml              # Project configuration
├── .env                        # Environment variables (optional)
│
├── dawson_scraper/src/
│   ├── scraper.py             # Document scraping orchestration
│   ├── api_client.py          # Dawson API client
│   ├── downloader.py          # Parallel download manager
│   ├── database.py            # SQLite persistence
│   ├── pdf_pipeline.py        # Docling PDF processing
│   ├── batch_pdf_processor.py # Bulk PDF conversion
│   ├── rag_system.py          # LlamaIndex RAG implementation
│   └── cli_rag.py             # RAG system CLI
│
├── data/
│   ├── json/                  # API metadata files
│   ├── documents/             # Downloaded PDFs (YYYY-MM/)
│   ├── markdown_documents/    # Converted markdown files
│   ├── vector_store/          # ChromaDB vector database
│   ├── processing_stats/      # Processing tracking
│   └── db/                    # SQLite databases
│
└── logs/                      # Application logs
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