# Module Overview

This document outlines the purpose and responsibility of the primary source code modules in the `dawson_scraper/src/` directory.

## Core Scraping Modules

### **config.py**
Manages all application configuration using Pydantic settings, loading values from environment variables or `.env` files. Provides centralized configuration for worker counts, date ranges, download behavior, and API settings.

### **models.py**
Defines the data models for court opinions and scraper statistics using Pydantic. Includes the `Opinion` model with field validation and aliasing for JSON data from the Dawson API, and the `ScraperStats` model for tracking download metrics.

### **database.py**
Implements the SQLite persistence layer using SQLAlchemy with async support. Manages the `downloads` and `searches` tables, tracks document download status, provides resume capability, and handles database session lifecycle.

### **api_client.py**
Async HTTP client responsible for all interactions with the Dawson Court API. Implements connection pooling, rate limiting, automatic retry with exponential backoff, and handles both JSON metadata fetching and PDF document downloads.

### **downloader.py**
Manages parallel download operations using a configurable worker pool. Coordinates concurrent PDF downloads, implements progress tracking with tqdm, handles file saving and verification, and manages the download queue with status updates.

### **scraper.py**
Main orchestration module that coordinates the entire scraping workflow. Generates monthly date ranges, manages the sequence of JSON fetching and PDF downloading, handles resume operations, and provides statistics and verification commands.

### **utils.py**
Utility functions supporting the main modules. Includes logging configuration, file path management, date generation utilities, sanitization functions for filenames, and helper methods for data validation.

## PDF Processing & AI Modules

### **pdf_pipeline.py**
Advanced PDF processing pipeline using IBM Docling. Provides state-of-the-art document conversion with OCR support, table structure recognition, Vision-Language Model (VLM) integration, and GPU acceleration. Handles complex layouts, scanned documents, and multilingual content with high accuracy.

### **batch_pdf_processor.py**
Batch processing system for converting large numbers of PDFs to markdown format at scale. Features multiprocessing support, SQLite progress tracking, resume capability, and comprehensive error handling. Optimized for processing thousands of court documents efficiently.

### **rag_system.py**
LlamaIndex-based Retrieval-Augmented Generation (RAG) system for semantic search across processed documents. Implements vector embeddings using HuggingFace models, ChromaDB for vector storage, metadata filtering, and natural language query processing. Enables intelligent document discovery and content analysis.

### **cli_rag.py**
Command-line interface for PDF processing and RAG system operations. Provides user-friendly commands for batch PDF conversion, vector index building, and semantic search queries. Includes progress tracking, error reporting, and configuration options for different processing modes.

## Module Interactions

### Document Scraping Workflow
1. **Entry Flow**: `run.py` → `scraper.py` → orchestrates all other modules
2. **Configuration**: `config.py` provides settings to all modules via dependency injection
3. **Data Flow**: `api_client.py` fetches data → `models.py` validates → `downloader.py` saves files
4. **Persistence**: `database.py` tracks all operations, enabling `scraper.py` to resume interrupted work
5. **Parallel Processing**: `downloader.py` manages worker pool that uses multiple `api_client.py` instances
6. **Error Handling**: All modules use `utils.py` for logging and `tenacity` for retry logic

### PDF Processing & Search Workflow
1. **Processing Entry**: `cli_rag.py` → `batch_pdf_processor.py` → `pdf_pipeline.py`
2. **Document Conversion**: `pdf_pipeline.py` uses IBM Docling → converts PDFs to markdown
3. **Batch Operations**: `batch_pdf_processor.py` manages multiprocessing → tracks progress in SQLite
4. **Index Building**: `rag_system.py` processes markdown → creates vector embeddings → stores in ChromaDB
5. **Search Operations**: `rag_system.py` processes queries → retrieves relevant documents → returns results
6. **CLI Interface**: `cli_rag.py` provides user commands → coordinates all processing and search operations

## Design Principles

- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Async-First**: All I/O operations use async/await for maximum concurrency
- **Resilience**: Every network operation includes retry logic and error recovery
- **Observability**: Comprehensive logging and progress tracking throughout
- **Stateful Recovery**: Database persistence enables resumption at any point
- **Type Safety**: Pydantic models ensure data validation and type checking
- **AI-First Architecture**: Modern AI/ML capabilities integrated throughout the pipeline
- **Scalable Processing**: Multiprocessing and GPU acceleration for high-performance document processing
- **Semantic Understanding**: Vector embeddings and RAG enable intelligent document search beyond keyword matching