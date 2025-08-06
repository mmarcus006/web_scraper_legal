# Setup Guide

This guide covers setup for both RAG systems:
- **ChromaDB RAG System**: Simple setup for development and small-scale use
- **Legal RAG System**: Production setup with Milvus and Google Gemini

## Prerequisites

### System Requirements
- **Python**: Version 3.10 - 3.12 (Python 3.13 not yet supported due to dependencies)
- **pip**: Python package manager
- **Storage**: 10-40 GB available disk space (original PDFs + markdown + vector index)
- **Memory**: 8 GB RAM minimum, 16 GB recommended for AI processing
- **Network**: Stable internet connection for API access and model downloads
- **GPU**: Optional, CUDA 11.8+ for 2-5x processing acceleration
- **Docker**: Optional, required for Legal RAG System (Milvus)
- **Google Gemini API**: Optional, required for Legal RAG System chat features

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
mkdir -p data/{json,documents,db,markdown_documents,json_documents,vector_store,processing_stats,milvus,processed} logs

# On Windows PowerShell:
New-Item -ItemType Directory -Force -Path data\json, data\documents, data\db, data\markdown_documents, data\json_documents, data\vector_store, data\processing_stats, data\milvus, data\processed, logs
```

### 5. Configure Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
# .env configuration file

# Scraping Configuration
PARALLEL_WORKERS=5              # Number of concurrent download workers (1-20, default: 5)
MAX_CONCURRENT_DOWNLOADS=50     # Maximum concurrent downloads per worker (default: 50)
START_DATE=2020-01-01           # Start date for scraping (YYYY-MM-DD)
END_DATE=2024-12-31             # End date for scraping (YYYY-MM-DD)
DOWNLOAD_PDFS=true              # Enable/disable PDF downloads (default: true)
SKIP_EXISTING=true              # Skip already-downloaded files (default: true)
VERIFY_PDFS=false               # Verify PDF integrity after download (default: false)
BASE_URL=https://dawson.uscourts.gov/api  # Dawson API base URL
RATE_LIMIT_DELAY=0.2            # Delay between requests per worker in seconds
MAX_RETRIES=3                   # Maximum retry attempts for failed downloads
RETRY_DELAY=5                   # Initial retry delay in seconds

# Legal RAG System Configuration
GOOGLE_API_KEY=your_gemini_api_key_here  # Google Gemini API key
GEMINI_MODEL=gemini-1.5-flash            # Gemini model version
MILVUS_HOST=localhost                    # Milvus server host
MILVUS_PORT=19530                        # Milvus server port
MILVUS_COLLECTION=tax_court_documents    # Milvus collection name

# Embedding and Processing Configuration
EMBEDDING_MODEL=intfloat/e5-large-v2     # HuggingFace embedding model
RAG_BATCH_SIZE=100                       # Processing batch size
RAG_MAX_WORKERS=8                        # Max workers for RAG processing
CHUNK_SIZE=512                           # Text chunk size for processing
CHUNK_OVERLAP=50                         # Overlap between chunks

# File Paths (usually not needed to change)
JSON_DIR=data/json              # Directory for JSON metadata files
PDF_DIR=data/documents          # Directory for PDF documents
DB_PATH=data/db/dawson_scraper.db  # SQLite database path
LOG_FILE=logs/dawson_scraper.log   # Log file path
```

### 6. Setup Legal RAG System (Optional)

If you want to use the production Legal RAG System:

```bash
# Start Milvus services
docker-compose up -d

# Wait for services to start (30-60 seconds)
docker ps

# Verify Milvus is running
curl http://localhost:19530/health

# Access Attu web UI (optional)
open http://localhost:8000
```

## Verification

### Test Installation

```bash
# Test ChromaDB RAG System
python run.py --help
dawson-rag --help

# Test Legal RAG System (if Docker is running)
legal-rag --help
legal-rag quickstart

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

### Document Scraping (Same for Both Systems)

```bash
# Full scrape with default settings (2020 to today)
dawson

# Custom date range
dawson --start-date 2024-01-01 --end-date 2024-12-31

# Increase parallel workers for faster downloads
dawson --workers 10

# Download metadata only (no PDFs)
dawson --no-pdfs

# Resume interrupted downloads
dawson --resume

# Show download statistics
dawson --stats
```

### ChromaDB RAG System

```bash
# Convert all PDFs to markdown and JSON formats
dawson-rag process-pdfs

# Process with more workers and VLM
dawson-rag process-pdfs --workers 8 --enable-vlm

# Build search index from markdown documents
dawson-rag build-index

# Search documents
dawson-rag search "capital gains tax"

# Search with filters
dawson-rag search "medical expenses" --year 2023 --top-k 10
```

### Legal RAG System (Production)

```bash
# Ensure Milvus is running
docker-compose up -d

# Process PDFs with advanced Docling
legal-rag process --input-dir data/documents --workers 8

# Build production vector index
legal-rag index --recreate

# Search with AI responses
legal-rag search "capital gains tax treatment" --top-k 10

# Interactive chat with Gemini
legal-rag chat

# System statistics and monitoring
legal-rag stats

# Use embedded mode (no Docker required)
legal-rag search "tax deductions" --use-lite
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
# Format code (both systems)
black dawson_scraper/src/ legal_rag/src/

# Lint code
ruff check dawson_scraper/src/ legal_rag/src/

# Type checking
mypy dawson_scraper/src/ legal_rag/src/

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
   
   **ChromaDB:**
   - ChromaDB creates index automatically
   - Delete `data/vector_store/` to rebuild from scratch
   - Ensure sufficient disk space for embeddings
   
   **Milvus (Legal RAG):**
   - Check Docker services: `docker ps`
   - View Milvus logs: `docker logs milvus-standalone`
   - Restart services: `docker-compose restart`
   - Use embedded mode as fallback: `legal-rag search "query" --use-lite`
   - Access web UI for troubleshooting: http://localhost:8000

6. **Google Gemini API Issues**
   - Verify `GOOGLE_API_KEY` is set correctly in `.env`
   - Check API quota and billing status
   - Test with simple search before using chat features
   - Use ChromaDB RAG system if Gemini is unavailable

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

### Document Format Overview

The PDF processing creates **two output formats** for maximum research flexibility:

#### Markdown Format (data/markdown_documents/)
- **Purpose**: Optimized for RAG, search, and text analysis
- **Size**: Compact (8-50KB typical)
- **Content**: Clean text with basic structure
- **Usage**: Vector indexing, semantic search, LLM processing

#### Docling JSON Format (data/json_documents/) 
- **Purpose**: Complete document structure preservation
- **Size**: Comprehensive (2-10MB typical)  
- **Content**: Full hierarchy, tables, images, layout metadata
- **Usage**: Document analysis, table extraction, layout-aware processing

Both formats are created simultaneously during processing with no performance penalty.

### Complete Workflow

#### ChromaDB RAG System (Simple)
1. **Scrape Documents**: `dawson --start-date 2024-01-01 --end-date 2024-01-31`
2. **Process PDFs**: `dawson-rag process-pdfs` (creates both formats)
3. **Build Index**: `dawson-rag build-index` (uses markdown)
4. **Search**: `dawson-rag search "tax deduction"`
5. **Analyze**: Use JSON files for table/structure analysis when needed

#### Legal RAG System (Production)
1. **Setup Services**: `docker-compose up -d`
2. **Scrape Documents**: `dawson --start-date 2024-01-01 --end-date 2024-01-31`
3. **Process PDFs**: `legal-rag process --workers 8`
4. **Build Index**: `legal-rag index --recreate`
5. **Search with AI**: `legal-rag search "tax deduction strategies"`
6. **Interactive Chat**: `legal-rag chat`
7. **Monitor**: Check http://localhost:8000 for Attu web UI

### Documentation Review
1. Review the [API Contracts](api_contracts.md) to understand the Dawson API
2. Check [Database Schema](database_schema.md) for data structure details
3. See [Module Overview](module_overview.md) for architecture details
4. Run help commands: `dawson --help`, `dawson-rag --help`, `legal-rag --help`
5. Quick start guide: `legal-rag quickstart`

### Choosing Between Systems

**Use ChromaDB RAG when:**
- Development or testing
- Small document collections (<10,000 docs)
- No AI responses needed
- Minimal infrastructure requirements
- Quick setup required

**Use Legal RAG System when:**
- Production deployment
- Large document collections (>10,000 docs)
- AI-powered responses needed
- Hybrid search capabilities required
- Scalability and performance critical
- Interactive chat interface desired

### Performance Tips
- Start with a small date range to test your setup
- Use GPU acceleration if available
- Monitor memory usage during PDF processing
- Build index incrementally as you process more documents