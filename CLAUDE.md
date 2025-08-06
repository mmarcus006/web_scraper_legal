# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive US Tax Court document processing system that combines high-performance scraping with advanced AI-powered PDF processing and semantic search. The system provides a complete workflow: scrape court documents → convert PDFs to markdown using IBM Docling → build vector search index with LlamaIndex → search documents using natural language queries.

**Version 4.0.0** introduces revolutionary AI capabilities including OCR, table recognition, GPU acceleration, and Retrieval-Augmented Generation (RAG) for intelligent document discovery.

## Architecture

The system now features **dual RAG architectures** to support different deployment scenarios:
- **ChromaDB RAG System**: Lightweight, embedded solution for development and small-scale deployment
- **Legal RAG System**: Production-grade system with Milvus vector database and Google Gemini LLM

### Core Scraping Components

- **run.py**: Main entry point with CLI interface using Click
- **dawson_scraper/src/scraper.py**: Main orchestration logic that coordinates the scraping process
- **dawson_scraper/src/api_client.py**: Async HTTP client for Dawson API interactions
- **dawson_scraper/src/downloader.py**: Parallel download manager with worker pool
- **dawson_scraper/src/database.py**: SQLite persistence layer for tracking downloads and state
- **dawson_scraper/src/config.py**: Pydantic settings management with environment variable support
- **dawson_scraper/src/models.py**: Data models for opinions and statistics
- **dawson_scraper/src/utils.py**: Utility functions for logging, file operations, and date handling

### AI Processing & Search Components

#### ChromaDB RAG System (dawson_scraper/src/)
- **dawson_scraper/src/pdf_pipeline.py**: IBM Docling integration for advanced PDF processing with OCR, table extraction, and VLM support
- **dawson_scraper/src/batch_pdf_processor.py**: Batch processing system for converting PDFs to markdown at scale with multiprocessing and progress tracking
- **dawson_scraper/src/rag_system.py**: LlamaIndex-based RAG system for semantic search across documents using vector embeddings and ChromaDB
- **dawson_scraper/src/cli_rag.py**: Command-line interface for PDF processing and search operations with comprehensive options

#### Legal RAG System (legal_rag/src/)
- **legal_rag/src/config.py**: Configuration management for Milvus and Google Gemini integration
- **legal_rag/src/milvus_manager.py**: Production-grade Milvus vector database operations with hybrid search
- **legal_rag/src/docling_processor.py**: Enhanced PDF processing with advanced OCR and table extraction
- **legal_rag/src/embedding_manager.py**: Multi-model embedding management with dense and sparse vectors
- **legal_rag/src/advanced_rag_system.py**: LlamaIndex orchestration with Milvus backend and Gemini LLM
- **legal_rag/src/cli.py**: Rich terminal interface for production-grade document processing and search

### Complete Data Flow

#### Phase 1: Document Scraping
1. DawsonScraper generates monthly periods from start/end dates
2. APIClient fetches JSON metadata for each period via search API
3. ParallelDownloader manages worker pool to download PDFs concurrently
4. Database tracks download status, enabling resume on interruption
5. Files are organized by month in data/documents/YYYY-MM/ folders

#### Phase 2: PDF Processing Pipeline
6. BatchPDFProcessor discovers all PDF files in document directories
7. PDFPipeline uses IBM Docling to convert PDFs to structured formats
8. OCR extracts text from scanned documents, table recognition preserves structures
9. **Dual Format Export**: Documents saved in two formats simultaneously:
   - **Markdown format**: Clean text in data/markdown_documents/YYYY-MM/ (optimized for RAG/search)
   - **Docling JSON format**: Complete document structure in data/json_documents/YYYY-MM/ (preserves layout, tables, images)
10. Processing status tracked in data/processing_stats/processing.db

#### Phase 3: Vector Indexing
11. TaxCourtRAGSystem processes markdown documents into chunks
12. HuggingFace embeddings model creates vector representations
13. ChromaDB stores vectors with metadata in data/vector_store/
14. Incremental updates add only new/changed documents

#### Phase 4: Semantic Search
15. Natural language queries converted to vector embeddings
16. Similarity search finds relevant document chunks
17. Results ranked and returned with metadata and context
18. Filtering by year, month, judge, or docket number supported

## Development Commands

### Installation
```bash
# Install with all AI/ML dependencies (recommended)
pip install -e .

# Install with development tools
pip install -e ".[dev]"

# Create required directories
mkdir -p data/{json,documents,db,markdown_documents,json_documents,vector_store,processing_stats,milvus} logs

# Start Milvus for Legal RAG System (optional)
docker-compose up -d
```

### Document Scraping Commands
```bash
# Run the scraper (basic usage - 2020 to today)
python run.py

# Run with custom parameters
python run.py --start-date 2024-01-01 --end-date 2024-12-31 --workers 10

# Resume interrupted downloads
python run.py --resume

# Show download statistics
python run.py --stats

# Verify downloaded PDFs
python run.py --verify

# Run without downloading PDFs (metadata only)
python run.py --no-pdfs

# Download PDFs from existing JSON files
python run.py --pdfs-only
```

### PDF Processing Commands
```bash
# Convert all PDFs to markdown and JSON formats
python -m dawson_scraper.src.cli_rag process-pdfs

# Process with more workers and enable VLM
python -m dawson_scraper.src.cli_rag process-pdfs --workers 8 --enable-vlm

# Process specific directory or pattern
python -m dawson_scraper.src.cli_rag process-pdfs --input-dir data/documents/2024-01
python -m dawson_scraper.src.cli_rag process-pdfs --filter "2024-*/ *.pdf"

# Custom JSON output directory
python -m dawson_scraper.src.cli_rag process-pdfs --json-output-dir data/custom_json

# Process with OCR and table recognition (always enabled)
python -m dawson_scraper.src.cli_rag process-pdfs --enable-ocr --enable-tables
```

### ChromaDB RAG System Commands
```bash
# Build search index from markdown documents
python -m dawson_scraper.src.cli_rag build-index

# Update existing index (incremental)
python -m dawson_scraper.src.cli_rag build-index --incremental

# Search documents with natural language
python -m dawson_scraper.src.cli_rag search "capital gains tax treatment"

# Search with filters and more results
python -m dawson_scraper.src.cli_rag search "medical expenses" --year 2023 --top-k 10

# Search by judge or docket
python -m dawson_scraper.src.cli_rag search "partnership distributions" --judge "Morrison"
```

### Legal RAG System Commands (Production-Grade)
```bash
# Setup environment
echo "GOOGLE_API_KEY=your_key_here" >> .env
echo "MILVUS_HOST=localhost" >> .env
echo "MILVUS_PORT=19530" >> .env

# Start Milvus services
docker-compose up -d

# Process PDFs with advanced Docling
legal-rag process --input-dir data/documents --workers 8

# Build Milvus vector index with hybrid search
legal-rag index --recreate

# Search with production RAG system
legal-rag search "capital gains tax treatment" --top-k 10

# Interactive chat with Gemini LLM
legal-rag chat

# Use embedded mode (no Docker required)
legal-rag search "tax deductions" --use-lite

# System statistics
legal-rag stats

# Quick setup guide
legal-rag quickstart
```

### Development Tools
```bash
# Code formatting
black dawson_scraper/src/
ruff check dawson_scraper/src/

# Type checking
mypy dawson_scraper/src/

# Run tests
pytest tests/
```

## Key Configuration

### Scraping Configuration
Settings are managed via environment variables or .env file:

- `PARALLEL_WORKERS`: Number of concurrent download workers (1-20, default: 5)
- `START_DATE`: Beginning of scrape period (YYYY-MM-DD, default: 2020-01-01)
- `END_DATE`: End of scrape period (YYYY-MM-DD, default: today)
- `DOWNLOAD_PDFS`: Enable/disable PDF downloads (true/false)
- `SKIP_EXISTING`: Skip already-downloaded files (true/false)
- `RATE_LIMIT_DELAY`: Delay between requests per worker (seconds)

### PDF Processing Configuration
- `ENABLE_OCR`: Enable OCR for scanned documents (default: true)
- `ENABLE_TABLE_STRUCTURE`: Enable table recognition (default: true)
- `ENABLE_VLM`: Enable Vision-Language Model for better accuracy (default: false)
- `MAX_WORKERS`: Number of parallel PDF processing workers (default: 4)
- `GPU_ACCELERATION`: Enable CUDA GPU acceleration if available (auto-detected)

### ChromaDB RAG System Configuration
- `EMBEDDING_MODEL`: HuggingFace model for embeddings (default: "BAAI/bge-base-en-v1.5")
- `CHUNK_SIZE`: Text chunk size for processing (default: 512)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 50)
- `TOP_K`: Default number of search results (default: 5)

### Legal RAG System Configuration
- `GOOGLE_API_KEY`: Google Gemini API key for LLM responses (required for chat)
- `GEMINI_MODEL`: Gemini model version (default: "gemini-1.5-flash")
- `MILVUS_HOST`: Milvus server host (default: "localhost")
- `MILVUS_PORT`: Milvus server port (default: 19530)
- `MILVUS_COLLECTION`: Collection name (default: "tax_court_documents")
- `EMBEDDING_MODEL`: Advanced embedding model (default: "intfloat/e5-large-v2")
- `RAG_BATCH_SIZE`: Batch size for processing (default: 100)
- `RAG_MAX_WORKERS`: Maximum workers for RAG processing (default: 8)

## Database Schema

### Main Database (data/db/dawson_scraper.db)
- **downloads** table: Tracks each document download (status, file_size, error_message)
- **searches** table: Tracks monthly search operations and results

### Processing Database (data/processing_stats/processing.db)
- **pdf_processing** table: Tracks PDF to markdown conversion (status, pages, processing_time, error_message)

### Vector Databases

#### ChromaDB (data/vector_store/)
- **ChromaDB**: Stores document embeddings and metadata for semantic search
- **chroma.sqlite3**: Embedded vector database file
- Managed automatically by the basic RAG system

#### Milvus (data/milvus/ and Docker)
- **Production Vector Database**: Scalable vector storage with SIMD acceleration
- **Hybrid Search Support**: Dense and sparse vectors with BM25
- **Collections**: Configurable schema with metadata filtering
- **Docker Services**: etcd (coordination), minio (storage), milvus (engine), attu (web UI)
- **Attu Web UI**: Available at http://localhost:8000 for database management

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

### Major Dependencies Added (Version 4.0.0)

#### AI & ML Core
- `docling`: IBM's state-of-the-art PDF processing toolkit
- `docling-core`: Core document processing capabilities
- `docling-ibm-models`: Pre-trained AI models for document understanding
- `transformers`: HuggingFace transformers for NLP (>=4.35.0)
- `torch`: PyTorch for deep learning with CUDA support (>=2.0.0)
- `accelerate`: Model acceleration and optimization

#### ChromaDB RAG & Vector Search
- `llama-index`: RAG framework for document search (>=0.9.0)
- `llama-index-embeddings-huggingface`: HuggingFace embedding integration
- `llama-index-vector-stores-chroma`: ChromaDB vector store support
- `chromadb`: Vector database for embeddings (>=0.4.0)
- `tiktoken`: Token counting for LLMs

#### Legal RAG System (Production)
- `pymilvus`: Milvus vector database client (>=2.4.0)
- `pymilvus[model]`: Milvus with additional model support
- `llama-index-vector-stores-milvus`: Milvus integration for LlamaIndex
- `llama-index-llms-gemini`: Google Gemini LLM integration
- `llama-index-embeddings-gemini`: Gemini embedding models
- `llama-index-readers-docling`: Docling document readers
- `llama-index-node-parser-docling`: Docling node parsers
- `google-generativeai`: Google Gemini API client (>=0.3.0)
- `sentence-transformers`: Advanced embedding models (>=2.3.0)
- `rank-bm25`: BM25 sparse retrieval (>=0.2.2)

#### Computer Vision & OCR
- `rapidocr-paddle`: OCR for scanned documents (>=1.3.0)
- `torchvision`: Computer vision models (>=0.15.0)
- `bitsandbytes`: Model quantization for memory efficiency

#### Scientific Computing
- `numpy`: Numerical computing foundation (>=1.24.0)
- `sentencepiece`: Text tokenization for transformers

#### Legacy Dependencies
- `PyPDF2`: For PDF verification (>=3.0.0)
- `python-dateutil`: For date handling utilities (>=2.8.0)

## Testing Approach

Per user instructions: Tests use actual APIs and data, not mocks. When testing functionality that requires data, request actual test data rather than using mocks.

### GPU/CUDA Configuration

#### Windows Setup
1. Install CUDA 11.8 or 12.x from NVIDIA
2. Install C++ Build Tools from Microsoft
3. PyTorch automatically detects CUDA availability
4. Set environment: `CUDA_VISIBLE_DEVICES=0` (if multiple GPUs)

#### Linux Setup
1. Install NVIDIA drivers: `sudo apt install nvidia-driver-525`
2. Install CUDA toolkit: `sudo apt install nvidia-cuda-toolkit`
3. Verify installation: `nvidia-smi` and `nvcc --version`
4. PyTorch will automatically use GPU when available

#### Performance Notes
- GPU provides 2-5x speedup for PDF processing
- CPU fallback is automatic if GPU unavailable
- Memory requirements: 4-8GB GPU RAM for optimal performance
- Monitor GPU usage: `nvidia-smi -l 1`

## JSON Document Export Feature

### Overview
The PDF processing pipeline now exports documents in **two formats simultaneously**:
- **Markdown format** (data/markdown_documents/): Clean text optimized for RAG and search
- **Docling JSON format** (data/json_documents/): Complete document structure with layout, tables, and metadata

### Key Benefits
- **Dual Output**: Both formats created in a single processing run
- **Rich Structure**: JSON preserves complete document hierarchy, tables, and images
- **Layout Preservation**: Maintains original document formatting and reading order
- **Metadata Rich**: Includes processing information and document statistics
- **Research Flexibility**: Choose format based on analysis needs

### JSON Format Features
- **Complete Document Schema**: Uses Docling's native DoclingDocument v1.5.0 format
- **Table Structures**: Preserves table formatting with proper cell relationships
- **Image Extraction**: Maintains embedded images and figures
- **Reading Order**: Preserves logical document flow
- **Processing Metadata**: Includes timing, settings, and conversion statistics

### File Structure
```
data/
├── documents/              # Original PDFs
│   └── 2024-01/
│       └── case_123.pdf
├── markdown_documents/     # Markdown format (8KB typical)
│   └── 2024-01/
│       ├── case_123.md     # Clean text for RAG
│       └── case_123.json   # Processing metadata only
└── json_documents/         # Docling JSON format (2MB typical)
    └── 2024-01/
        └── case_123.json   # Complete document structure
```

### Usage Examples
```bash
# Process with both formats (default behavior)
python -m dawson_scraper.src.cli_rag process-pdfs

# Custom JSON output location
python -m dawson_scraper.src.cli_rag process-pdfs --json-output-dir data/research_json

# Process specific documents
python -m dawson_scraper.src.cli_rag process-pdfs --filter "2024-12/*.pdf"
```

### Use Cases
- **RAG/Search**: Use markdown for fast text indexing and retrieval
- **Document Analysis**: Use JSON for preserving table structures and layout
- **Legal Research**: JSON maintains court document formatting crucial for citations
- **Data Extraction**: JSON enables precise table and figure extraction
- **Advanced NLP**: JSON provides document structure for sophisticated analysis

## Complete Workflow Examples

### ChromaDB Workflow (Development/Small-scale)

```bash
# 1. Scrape documents for a specific period
python run.py --start-date 2024-01-01 --end-date 2024-03-31 --workers 8

# 2. Convert PDFs to markdown and JSON formats with GPU acceleration
python -m dawson_scraper.src.cli_rag process-pdfs --workers 6 --enable-vlm

# 3. Build semantic search index (uses markdown for speed)
python -m dawson_scraper.src.cli_rag build-index

# 4. Search documents
python -m dawson_scraper.src.cli_rag search "corporate tax deductions for business expenses"
python -m dawson_scraper.src.cli_rag search "partnership distributions" --year 2024 --top-k 10

# 5. Update index as new documents are added
python -m dawson_scraper.src.cli_rag build-index --incremental
```

### Legal RAG System Workflow (Production)

```bash
# 1. Setup environment and services
echo "GOOGLE_API_KEY=your_key_here" >> .env
docker-compose up -d  # Start Milvus stack

# 2. Scrape documents (same as above)
python run.py --start-date 2024-01-01 --end-date 2024-03-31 --workers 8

# 3. Process PDFs with advanced Docling
legal-rag process --input-dir data/documents --workers 8

# 4. Build production vector index with hybrid search
legal-rag index --recreate

# 5. Search with AI-powered responses
legal-rag search "corporate tax deductions for business expenses" --top-k 10
legal-rag search "partnership distributions" --year 2024 --judge Morrison

# 6. Interactive chat with Gemini LLM
legal-rag chat

# 7. Update index incrementally
legal-rag index  # Incremental by default

# 8. Monitor via Attu web UI
open http://localhost:8000
```

### Choosing Between Systems

**Use ChromaDB RAG when:**
- Development or testing
- Small document collections (<10,000 docs)
- No LLM responses needed
- Minimal infrastructure requirements

**Use Legal RAG System when:**
- Production deployment
- Large document collections (>10,000 docs)
- AI-powered responses needed
- Hybrid search capabilities required
- Scalability and performance critical

### Test Results

#### Scraping Functionality
- Successfully connects to Dawson Court API
- Downloads and verifies PDF documents correctly
- SQLite database properly tracks download status
- Resume functionality works as expected
- Statistics and verification commands functioning

#### PDF Processing Functionality
- IBM Docling successfully processes complex PDFs
- OCR extracts text from scanned court documents
- Table recognition preserves financial data structures
- **Dual Format Export**: Creates both markdown and Docling JSON simultaneously
- **Rich JSON Structure**: Preserves complete document layout, tables, images, and metadata
- Batch processing handles thousands of documents
- GPU acceleration provides 2-5x speed improvement
- JSON files contain 10-100x more structural information than markdown

#### RAG System Functionality
- Vector embeddings created successfully for all documents
- ChromaDB index supports fast similarity search
- Natural language queries return relevant results
- Metadata filtering works correctly (year, judge, docket)
- Incremental index updates process only new documents

#### Performance Metrics
- Document scraping: 5-10 PDFs per minute
- PDF processing: 1-3 documents per minute (CPU), 3-8 per minute (GPU)
- Index building: ~1000 documents per minute
- Search queries: Sub-second response times
- Memory usage: 2-8GB during processing (depends on batch size and GPU)