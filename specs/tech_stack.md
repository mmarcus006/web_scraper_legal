# Technology Stack

## Primary Language
- **Python 3.10 - 3.12** (Python 3.13 not yet supported due to sentencepiece dependency)

## Core Frameworks & Libraries

### Async/Networking
- **aiohttp** (>=3.9.0) - Asynchronous HTTP client/server framework for parallel downloads
- **aiofiles** (>=23.0.0) - Asynchronous file operations for non-blocking I/O
- **tenacity** (>=8.2.0) - Retry library with exponential backoff strategies

### Data Management
- **SQLAlchemy** (>=2.0.0) - SQL toolkit and ORM for database operations
- **aiosqlite** (>=0.19.0) - Async SQLite database adapter
- **pydantic** (>=2.5.0) - Data validation using Python type annotations
- **pydantic-settings** (>=2.1.0) - Settings management with environment variables

### CLI & User Interface
- **click** (>=8.1.0) - Command-line interface creation toolkit
- **rich** (>=13.7.0) - Rich text and beautiful formatting in the terminal
- **tqdm** (>=4.66.0) - Progress bar library for visual feedback

### Configuration
- **python-dotenv** (>=1.0.0) - Load environment variables from .env files

### PDF Processing & AI
- **docling** - IBM's state-of-the-art PDF processing toolkit
- **docling-core** - Core document processing capabilities
- **docling-ibm-models** - Pre-trained AI models for document understanding
- **transformers** (>=4.35.0) - HuggingFace transformers for NLP
- **accelerate** (>=0.25.0) - PyTorch model acceleration
- **sentencepiece** (>=0.1.99) - Text tokenization for transformers

### ChromaDB RAG System & Vector Search
- **llama-index** (>=0.9.0) - RAG framework for document search
- **llama-index-core** - Core LlamaIndex functionality
- **llama-index-readers-file** - File readers for various formats
- **llama-index-embeddings-huggingface** - HuggingFace embedding integration
- **llama-index-vector-stores-chroma** - ChromaDB vector store support
- **chromadb** (>=0.4.0) - Vector database for embeddings
- **tiktoken** (>=0.5.0) - Token counting for LLMs
- **nest-asyncio** (>=1.5.0) - Nested async event loop support

### Legal RAG System (Production)
- **pymilvus** (>=2.4.0) - Milvus vector database client
- **pymilvus[model]** - Additional model support for Milvus
- **llama-index-vector-stores-milvus** - Milvus integration for LlamaIndex
- **llama-index-llms-gemini** - Google Gemini LLM integration
- **llama-index-embeddings-gemini** - Gemini embedding models
- **llama-index-readers-docling** - Docling document readers
- **llama-index-node-parser-docling** - Docling node parsers
- **google-generativeai** (>=0.3.0) - Google Gemini API client
- **sentence-transformers** (>=2.3.0) - Advanced embedding models
- **rank-bm25** (>=0.2.2) - BM25 sparse retrieval implementation

### Computer Vision & OCR
- **rapidocr-paddle** (>=1.3.0) - OCR for scanned documents
- **torch** (>=2.0.0) - PyTorch for deep learning
- **torchvision** (>=0.15.0) - Computer vision models
- **torchaudio** (>=2.0.0) - Audio processing (dependency)
- **bitsandbytes** (>=0.41.0) - Quantization for memory efficiency

### Scientific Computing
- **numpy** (>=1.24.0) - Numerical computing foundation

### Additional Dependencies
- **PyPDF2** (>=3.0.0) - PDF file verification and validation
- **python-dateutil** (>=2.8.0) - Advanced date/time parsing and manipulation

## Development Tools

### Code Quality
- **black** (>=23.0.0) - Python code formatter
- **ruff** (>=0.1.0) - Fast Python linter
- **mypy** (>=1.7.0) - Static type checker for Python

### Testing
- **pytest** (>=7.4.0) - Testing framework
- **pytest-asyncio** (>=0.21.0) - Pytest support for asyncio

## Build System
- **setuptools** (>=61.0) - Python package build backend

## GPU Acceleration
- **CUDA 11.8+** (optional) - GPU acceleration for PDF processing and AI models
- Provides 2-5x speed improvement for document processing
- Automatically detected and used when available

## Platform Support
- **Windows** (MSYS_NT, native Windows)
- **macOS** (Intel and Apple Silicon)
- **Linux** (Ubuntu, CentOS, Debian)
- **Docker** (for Legal RAG System services)

## Embedding Models Supported

### ChromaDB RAG System
- **BAAI/bge-base-en-v1.5** (default) - 768 dimensions, good performance
- **sentence-transformers/all-MiniLM-L6-v2** - 384 dimensions, lightweight
- **HuggingFace models** - Any compatible transformer model

### Legal RAG System (MTEB-optimized)
- **intfloat/e5-large-v2** (default) - 1024 dimensions, excellent balance
- **Alibaba-NLP/gte-Qwen2-7B-instruct** - 7680 dimensions, best accuracy
- **BAAI/bge-large-en-v1.5** - 1024 dimensions, fast processing
- **sentence-transformers/all-MiniLM-L6-v2** - 384 dimensions, development
- **Google Gemini embeddings** - Latest embedding models from Google

## Search Technologies

### ChromaDB RAG System
- **Dense Vector Search** - Semantic similarity using transformer embeddings
- **Metadata Filtering** - Filter by year, month, judge, docket number
- **Cosine Similarity** - Standard vector similarity measurement

### Legal RAG System
- **Hybrid Search** - Combines dense and sparse retrieval for optimal results
- **Dense Embeddings** - Semantic understanding using transformer models
- **Sparse Embeddings** - BM25 keyword matching for exact term relevance
- **Score Fusion** - Intelligent combination of dense and sparse scores
- **Advanced Filtering** - Complex metadata queries with boolean logic

## Databases

### SQLite (Shared)
- **SQLite** - Embedded database for:
  - Document download tracking
  - PDF processing status
  - Search operation history
  - Vector store metadata (ChromaDB)

### Vector Databases
- **ChromaDB** - Embedded vector database for development and small-scale deployment
- **Milvus** - Production-grade distributed vector database with:
  - Scalability to billions of vectors
  - SIMD acceleration for high performance
  - Hybrid search (dense + sparse vectors)
  - ACID compliance and persistence
  - Web UI management via Attu

### Docker Infrastructure (Legal RAG System)
- **etcd** - Distributed key-value store for Milvus coordination
- **MinIO** - S3-compatible object storage for Milvus
- **Attu** - Web-based management interface for Milvus

## External APIs & Services
- **Dawson Court API** - US Tax Court document search and retrieval service
- **HuggingFace Hub** - Pre-trained models for embeddings and NLP
- **IBM Docling Models** - Advanced document processing AI models
- **Google Gemini API** - Large language model for AI responses and embeddings
- **MTEB Leaderboard Models** - Top-performing embedding models for semantic search