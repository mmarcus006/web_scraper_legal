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
- **📄 Dual Format Export**: Convert PDFs to both markdown and structured JSON formats
- **🔧 Rich Document Structure**: JSON format preserves layout, tables, images, and metadata

### AI-Powered Search (Dual RAG Systems)

#### ChromaDB RAG System (Development)
- **🔍 Semantic Search**: Find relevant documents using natural language queries
- **🎯 Vector Embeddings**: HuggingFace models for document understanding
- **💾 Vector Database**: ChromaDB for efficient similarity search
- **🏷️ Metadata Filtering**: Search by year, month, docket number, judge
- **📈 LlamaIndex Integration**: Production-ready RAG system

#### Legal RAG System (Production)
- **🚀 Advanced RAG**: Milvus vector database with hybrid search capabilities
- **🤖 Google Gemini Integration**: AI-powered responses with state-of-the-art LLM
- **⚡ Hybrid Search**: Combines dense embeddings with BM25 sparse retrieval
- **🎯 Top Embedding Models**: Uses best-performing models from MTEB leaderboard
- **🐳 Docker Infrastructure**: Production-grade deployment with Milvus stack
- **💬 Interactive Chat**: Conversational interface for legal research
- **📊 Rich Terminal Interface**: Beautiful CLI with progress tracking and statistics

## 📋 Requirements

- **Python 3.10 - 3.12** (Python 3.13 not yet supported due to dependencies)
- **Storage**: 5-20GB for full 2020-2025 dataset
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Optional, CUDA 11.8+ for acceleration
- **OS**: Windows, macOS, or Linux
- **Docker**: Optional, required for Legal RAG System (Milvus)
- **Google Gemini API**: Required for Legal RAG System chat features

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
New-Item -ItemType Directory -Force -Path data\json, data\documents, data\db, logs, data\markdown_documents, data\json_documents, data\vector_store, data\milvus, data\processed

# macOS/Linux:
mkdir -p data/{json,documents,db,markdown_documents,json_documents,vector_store,milvus,processed} logs
```

### 4. Setup Legal RAG System (Optional)

```bash
# Start Milvus services for production RAG
docker-compose up -d

# Configure environment for Legal RAG
cp .env.example .env
# Add your Google Gemini API key to .env:
echo "GOOGLE_API_KEY=your_gemini_api_key_here" >> .env
```

## 📖 Quick Start Guide

### Choose Your RAG System

**ChromaDB RAG (Simple Setup)**
- ✅ No Docker required
- ✅ Fast setup for development
- ✅ Good for small collections
- ❌ No AI responses, search only

**Legal RAG System (Production)**
- ✅ Google Gemini AI responses
- ✅ Hybrid search (dense + sparse)
- ✅ Scalable Milvus database
- ✅ Rich interactive chat
- ❌ Requires Docker and API key

### 1. Scrape Documents (Same for Both Systems)

```bash
# Basic scraping (2020 to today)
python run.py

# Custom date range
python run.py --start-date 2024-01-01 --end-date 2024-12-31

# Faster with more workers
python run.py --workers 10
```

### 2A. ChromaDB RAG System (Simple)

```bash
# Process all PDFs (creates both markdown and JSON)
python -m dawson_scraper.src.cli_rag process-pdfs --workers 8

# Create vector index
python -m dawson_scraper.src.cli_rag build-index

# Search documents
python -m dawson_scraper.src.cli_rag search "capital gains tax" --top-k 10
```

### 2B. Legal RAG System (Production)

```bash
# Start Milvus services
docker-compose up -d

# Process PDFs with advanced Docling
legal-rag process --input-dir data/documents --workers 8

# Build production vector index
legal-rag index --recreate

# Search with AI responses
legal-rag search "capital gains tax treatment" --top-k 10

# Interactive chat with Gemini
legal-rag chat

# Use embedded mode (no Docker)
legal-rag search "tax deductions" --use-lite
```

## 📁 Project Structure

```
web_scraper_legal/
├── run.py                      # Main scraper entry point
├── pyproject.toml              # Project configuration
├── docker-compose.yml          # Milvus services for Legal RAG
├── .env                        # Environment variables (optional)
│
├── dawson_scraper/src/         # ChromaDB RAG System
│   ├── scraper.py             # Document scraping orchestration
│   ├── api_client.py          # Dawson API client
│   ├── downloader.py          # Parallel download manager
│   ├── database.py            # SQLite persistence
│   ├── pdf_pipeline.py        # Docling PDF processing
│   ├── batch_pdf_processor.py # Bulk PDF conversion
│   ├── rag_system.py          # LlamaIndex RAG implementation
│   └── cli_rag.py             # RAG system CLI
│
├── legal_rag/src/              # Legal RAG System (Production)
│   ├── config.py              # Milvus and Gemini configuration
│   ├── milvus_manager.py       # Milvus vector operations
│   ├── docling_processor.py    # Advanced PDF processing
│   ├── embedding_manager.py    # Multi-model embeddings
│   ├── advanced_rag_system.py  # Production RAG orchestration
│   └── cli.py                 # Rich terminal interface
│
├── data/
│   ├── json/                  # API metadata files
│   ├── documents/             # Downloaded PDFs (YYYY-MM/)
│   ├── markdown_documents/    # Converted markdown files
│   ├── json_documents/        # Docling JSON documents (complete structure)
│   ├── processed/             # Legal RAG processed documents
│   ├── vector_store/          # ChromaDB vector database
│   ├── milvus/                # Milvus data directory
│   ├── processing_stats/      # Processing tracking
│   └── db/                    # SQLite databases
│
├── specs/                      # Project documentation
│   ├── project_overview.md    # High-level summary
│   ├── tech_stack.md          # Technology stack
│   ├── project_structure.md   # Directory structure
│   ├── module_overview.md     # Module responsibilities
│   ├── setup_guide.md         # Setup instructions
│   ├── api_contracts.md       # API documentation
│   └── database_schema.md     # Database schemas
│
└── logs/                      # Application logs
```

## 📊 Document Export Formats

The system exports processed documents in **two formats** to support different research needs:

### Markdown Format (data/markdown_documents/)
- **Purpose**: Optimized for RAG, search indexing, and text analysis
- **Size**: Compact (typically 8-50KB per document)
- **Content**: Clean text with basic structure preservation
- **Use Cases**: Semantic search, LLM processing, content analysis

### Docling JSON Format (data/json_documents/)
- **Purpose**: Complete document structure preservation
- **Size**: Comprehensive (typically 2-10MB per document)
- **Content**: Full document hierarchy, tables, images, metadata
- **Use Cases**: Document analysis, table extraction, layout-aware processing

### Key Benefits
- **Simultaneous Export**: Both formats created in single processing run
- **No Performance Penalty**: Dual export optimized for efficiency
- **Format Selection**: Choose appropriate format for your analysis needs
- **Rich Metadata**: Processing statistics and document information included

### Example Structure
```
data/documents/2024-01/case_123.pdf         # Original (PDF, 800KB)
data/markdown_documents/2024-01/case_123.md # Clean text (MD, 15KB) 
data/json_documents/2024-01/case_123.json   # Full structure (JSON, 3.2MB)
```

## ⚙️ Configuration

Create a `.env` file for custom settings (optional):

```bash
# .env file example

# Scraping Configuration
PARALLEL_WORKERS=5           # Number of concurrent downloads (1-20)
START_DATE=2020-01-01        # Beginning of scrape period
END_DATE=2024-12-31          # End of scrape period
DOWNLOAD_PDFS=true           # Enable/disable PDF downloads
SKIP_EXISTING=true           # Skip already-downloaded files
RATE_LIMIT_DELAY=0.2         # Delay between requests per worker

# Legal RAG System Configuration
GOOGLE_API_KEY=your_gemini_key    # Required for Gemini LLM
GEMINI_MODEL=gemini-1.5-flash     # Gemini model version
MILVUS_HOST=localhost             # Milvus server host
MILVUS_PORT=19530                 # Milvus server port
MILVUS_COLLECTION=tax_court_docs  # Collection name

# Embedding Configuration
EMBEDDING_MODEL=intfloat/e5-large-v2  # HuggingFace embedding model
RAG_BATCH_SIZE=100                     # Processing batch size
RAG_MAX_WORKERS=8                      # Max workers for RAG
CHUNK_SIZE=512                         # Text chunk size
CHUNK_OVERLAP=50                       # Chunk overlap
```

Or use command-line arguments to override defaults.

## 📖 Usage

### ChromaDB RAG Usage

```bash
# Full scrape with PDFs (2020 to today)
python run.py

# Process PDFs to markdown and JSON
python -m dawson_scraper.src.cli_rag process-pdfs --workers 8

# Build search index
python -m dawson_scraper.src.cli_rag build-index

# Search documents
python -m dawson_scraper.src.cli_rag search "capital gains tax"
```

### Legal RAG System Usage

```bash
# Start Milvus services
docker-compose up -d

# Process documents
legal-rag process --workers 8

# Build index
legal-rag index --recreate

# Search with AI responses
legal-rag search "capital gains tax" --top-k 10

# Interactive chat
legal-rag chat

# System statistics
legal-rag stats

# Quick help
legal-rag quickstart
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

#### Scraper Options (run.py)
```bash
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

#### Legal RAG Options (legal-rag)
```bash
legal-rag process
  --input-dir DIR      Input directory with PDFs
  --pattern PATTERN    File pattern to match
  --skip-existing      Skip already processed files
  --workers N          Number of parallel workers

legal-rag index
  --documents-dir DIR  Directory with processed docs
  --recreate          Recreate Milvus collection
  --use-lite          Use embedded Milvus

legal-rag search QUERY
  --top-k N           Number of results
  --year YEAR         Filter by year
  --month MONTH       Filter by month
  --judge JUDGE       Filter by judge name
  --docket DOCKET     Filter by docket number
  --hybrid/--no-hybrid Use hybrid search
  --json-output       Output as JSON
  --use-lite          Use embedded Milvus

legal-rag chat
  --use-lite          Use embedded Milvus

legal-rag stats
  --use-lite          Use embedded Milvus
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

### Legal RAG System Issues

**Milvus connection failed**
```bash
# Check Docker services
docker ps

# View Milvus logs
docker logs milvus-standalone

# Restart services
docker-compose restart

# Use embedded mode as fallback
legal-rag search "query" --use-lite
```

**Gemini API errors**
- Verify `GOOGLE_API_KEY` in `.env`
- Check API quota and billing
- Use search without chat for basic functionality

**Embedding model download issues**
- Ensure internet connectivity
- Clear HuggingFace cache: `rm -rf ~/.cache/huggingface`
- Use smaller model: `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`

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

### SQLite Databases

- **downloads**: Document download status and metadata
- **searches**: Monthly search operations and results
- **pdf_processing**: PDF conversion tracking

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

### Vector Databases

**ChromaDB**: Embedded vector storage in `data/vector_store/`

**Milvus**: Production vector database with web UI
```bash
# Access Attu web interface
open http://localhost:8000

# View collections and statistics
docker exec milvus-standalone milvus_cli
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

### ChromaDB RAG Classes

**DawsonScraper**
- `run()`: Main scraping orchestration
- `resume_interrupted()`: Resume failed downloads
- `process_existing_json()`: Download PDFs from JSON

**TaxCourtRAGSystem**
- `build_index()`: Create vector index from documents
- `search()`: Semantic search with filters
- `add_documents()`: Add new documents to index

### Legal RAG System Classes

**AdvancedRAGSystem**
- `process_documents()`: Process PDFs with Docling
- `build_index()`: Create Milvus vector index
- `search()`: Hybrid search with AI responses
- `chat()`: Interactive conversation interface

**MilvusManager**
- `create_collection()`: Setup vector database
- `hybrid_search()`: Dense + sparse retrieval
- `get_statistics()`: Collection metrics

**EmbeddingManager**
- `get_dense_embeddings()`: Transformer embeddings
- `get_sparse_embeddings()`: BM25 sparse vectors
- `setup_models()`: Model initialization

## 🔒 Security & Compliance

- Respects rate limits with configurable delays
- User-Agent headers match standard browsers
- Connection pooling for efficient resource use
- No authentication bypass or scraping of protected content

## 🚀 CLI Tools

The project provides three CLI entry points:

1. **`dawson`** - Main scraper for downloading documents
2. **`dawson-rag`** - ChromaDB RAG system for basic search
3. **`legal-rag`** - Production RAG system with Milvus and Gemini

## 📄 License

This project is for educational and research purposes. Ensure compliance with the US Tax Court's terms of service and Google's API terms when using this tool.

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