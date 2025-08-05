# Setup Guide

## Prerequisites

### System Requirements
- **Python**: Version 3.10 - 3.12 (Python 3.13 not yet supported due to dependencies)
- **pip**: Python package manager
- **Storage**: 10-40 GB available disk space (original PDFs + markdown + vector index)
- **Memory**: 8 GB RAM minimum, 16 GB recommended for AI processing
- **Network**: Stable internet connection for API access and model downloads
- **GPU**: Optional, CUDA 11.8+ for 2-5x processing acceleration

### Operating System Support
- Windows 10/11 (with C++ Build Tools)
- macOS 10.15+ (Intel/Apple Silicon)
- Linux (Ubuntu 20.04+, CentOS 8+, or equivalent)

### Windows Prerequisites
For Windows users, install Microsoft C++ Build Tools:
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install with "Desktop development with C++" workload
- Required for PyTorch, transformers, and other native dependencies

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

### 3. Install Package

```bash
# Install with all features (recommended)
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"

# Alternative: Use uv for faster installation
uv pip install -e .
```

**Note**: The package installation will automatically install all required dependencies including:
- Document scraping: aiohttp, aiofiles, tenacity, etc.
- PDF processing: docling, transformers, torch, etc.
- RAG system: llama-index, chromadb, etc.
- OCR support: rapidocr-paddle
- GPU acceleration: PyTorch with CUDA support (if available)

### 4. Create Required Directories

```bash
# Create all data and log directories
mkdir -p data/{json,documents,db,markdown_documents,vector_store,processing_stats} logs

# On Windows PowerShell:
New-Item -ItemType Directory -Force -Path data\json, data\documents, data\db, data\markdown_documents, data\vector_store, data\processing_stats, logs
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

### Document Scraping

```bash
# Full scrape with default settings (2020 to today)
python run.py

# Custom date range
python run.py --start-date 2024-01-01 --end-date 2024-12-31

# Increase parallel workers for faster downloads
python run.py --workers 10

# Download metadata only (no PDFs)
python run.py --no-pdfs

# Resume interrupted downloads
python run.py --resume

# Show download statistics
python run.py --stats
```

### PDF Processing

```bash
# Convert all PDFs to markdown
python -m dawson_scraper.src.cli_rag process-pdfs

# Process with more workers and VLM
python -m dawson_scraper.src.cli_rag process-pdfs --workers 8 --enable-vlm

# Process specific directory
python -m dawson_scraper.src.cli_rag process-pdfs --input-dir data/documents/2024-01
```

### Search System

```bash
# Build search index from markdown documents
python -m dawson_scraper.src.cli_rag build-index

# Search documents
python -m dawson_scraper.src.cli_rag search "capital gains tax"

# Search with filters
python -m dawson_scraper.src.cli_rag search "medical expenses" --year 2023 --top-k 10
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

1. **Installation Issues**
   - **Windows**: Install C++ Build Tools if you get compiler errors
   - **CUDA**: Ensure CUDA 11.8+ is installed for GPU acceleration
   - **Python Version**: Use Python 3.10-3.12 (not 3.13)

2. **Memory Issues During PDF Processing**
   - Reduce `--workers` count for PDF processing
   - Process smaller batches of documents
   - Disable VLM with `--no-vlm` if memory constrained

3. **Model Download Issues**
   - Ensure internet connectivity for HuggingFace model downloads
   - Models are cached after first download
   - Use `HF_HUB_DISABLE_SYMLINKS_WARNING=1` on Windows

4. **GPU Issues**
   - Check CUDA installation: `nvidia-smi`
   - PyTorch should detect GPU automatically
   - CPU fallback is automatic if GPU unavailable

5. **Vector Store Issues**
   - ChromaDB creates index automatically
   - Delete `data/vector_store/` to rebuild from scratch
   - Ensure sufficient disk space for embeddings

6. **Legacy Issues**
   - Module Import Errors: Ensure virtual environment is activated
   - Permission Denied: Check write permissions for data/ directories
   - Connection Errors: Verify Dawson API accessibility
   - Disk Space: Check available space (now needs more for processing)

### Log Files

Check logs for detailed error information:
```bash
# View recent log entries
tail -n 50 logs/dawson_scraper.log

# Monitor logs in real-time
tail -f logs/dawson_scraper.log
```

## Next Steps

### Complete Workflow
1. **Scrape Documents**: Start with `python run.py --start-date 2024-01-01 --end-date 2024-01-31`
2. **Process PDFs**: Run `python -m dawson_scraper.src.cli_rag process-pdfs`
3. **Build Index**: Execute `python -m dawson_scraper.src.cli_rag build-index`
4. **Search**: Try `python -m dawson_scraper.src.cli_rag search "tax deduction"`

### Documentation Review
1. Review the [API Contracts](api_contracts.md) to understand the Dawson API
2. Check [Database Schema](database_schema.md) for data structure details
3. See [Module Overview](module_overview.md) for architecture details
4. Run help commands: `python run.py --help` and `python -m dawson_scraper.src.cli_rag --help`

### Performance Tips
- Start with a small date range to test your setup
- Use GPU acceleration if available
- Monitor memory usage during PDF processing
- Build index incrementally as you process more documents