# Legal RAG System

Advanced Retrieval-Augmented Generation system for US Tax Court documents using state-of-the-art technologies.

## Features

- **🚀 Advanced PDF Processing**: IBM Docling for superior document understanding
- **🔍 Hybrid Search**: Combines dense and sparse embeddings for best results
- **🎯 Top Embedding Models**: Uses best-performing models from MTEB leaderboard
- **💾 Scalable Vector Store**: Milvus for production-grade vector storage
- **🤖 Google Gemini Integration**: Advanced LLM for response generation
- **⚡ GPU Acceleration**: CUDA support for faster processing
- **📊 Rich CLI**: Beautiful terminal interface with progress tracking

## Architecture

```
Legal RAG System
├── Docling Processor      # Advanced PDF parsing with OCR, tables, formulas
├── Embedding Manager       # Multi-model embeddings (HuggingFace + Gemini)
├── Milvus Manager         # Vector database operations
├── Advanced RAG System    # LlamaIndex orchestration
└── CLI Interface          # Rich terminal interface
```

## Quick Start

### 1. Prerequisites

- Python 3.10-3.12
- Docker (optional, for Milvus server)
- CUDA GPU (optional, for acceleration)
- Google Gemini API key

### 2. Installation

```bash
# Install dependencies (from root directory)
pip install -e .

# Or install specific RAG dependencies
pip install pymilvus llama-index-vector-stores-milvus llama-index-llms-gemini \
            llama-index-embeddings-huggingface google-generativeai \
            docling sentence-transformers rank-bm25
```

### 3. Configuration

Add to your `.env` file:

```env
# Google Gemini
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=tax_court_documents

# Embedding Model (choose one)
EMBEDDING_MODEL=intfloat/e5-large-v2  # Good balance
# EMBEDDING_MODEL=Alibaba-NLP/gte-Qwen2-7B-instruct  # Best performance
# EMBEDDING_MODEL=BAAI/bge-large-en-v1.5  # Fast

# Processing
RAG_BATCH_SIZE=100
RAG_MAX_WORKERS=8
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### 4. Start Milvus (Optional)

For production use with Docker:

```bash
docker-compose up -d
```

Or use embedded mode with `--use-lite` flag in CLI commands.

### 5. Process Documents

```bash
# Process PDFs with Docling
legal-rag process --input-dir data/documents --workers 8

# With specific pattern
legal-rag process --pattern "2024-*/*.pdf"
```

### 6. Build Index

```bash
# Build vector index
legal-rag index --use-lite

# Or with Milvus server
legal-rag index --recreate
```

### 7. Search Documents

```bash
# Basic search
legal-rag search "capital gains tax treatment"

# With filters
legal-rag search "medical expenses" --year 2024 --judge Morrison --top-k 10

# JSON output
legal-rag search "partnership distributions" --json-output
```

### 8. Interactive Chat

```bash
# Start chat interface
legal-rag chat --use-lite
```

## CLI Commands

### `legal-rag process`
Process PDF documents with Docling

Options:
- `--input-dir`: Directory with PDFs (default: data/documents)
- `--pattern`: File pattern to match (default: *.pdf)
- `--skip-existing`: Skip already processed files
- `--workers`: Number of parallel workers

### `legal-rag index`
Build vector index from processed documents

Options:
- `--documents-dir`: Directory with processed docs (default: data/processed)
- `--recreate`: Recreate Milvus collection
- `--use-lite`: Use embedded Milvus

### `legal-rag search`
Search for relevant documents

Options:
- `--top-k`: Number of results (default: 10)
- `--year`: Filter by year
- `--month`: Filter by month
- `--judge`: Filter by judge name
- `--docket`: Filter by docket number
- `--hybrid/--no-hybrid`: Use hybrid search (default: true)
- `--json-output`: Output as JSON
- `--use-lite`: Use embedded Milvus

### `legal-rag chat`
Interactive chat interface with RAG

Options:
- `--use-lite`: Use embedded Milvus

### `legal-rag stats`
Show system statistics

Options:
- `--use-lite`: Use embedded Milvus

### `legal-rag quickstart`
Display quick setup guide

## Advanced Features

### Hybrid Search

The system combines:
1. **Dense Embeddings**: Semantic similarity using transformer models
2. **Sparse Embeddings**: BM25 keyword matching
3. **Reranking**: Score fusion for optimal results

### Document Processing

Docling provides:
- **OCR**: Extract text from scanned PDFs
- **Table Recognition**: Preserve table structures
- **Formula Extraction**: Mathematical expressions
- **Layout Analysis**: Document structure understanding

### Embedding Models

Supported models (ranked by MTEB):
1. `Alibaba-NLP/gte-Qwen2-7B-instruct` - 7680 dims, best accuracy
2. `intfloat/e5-large-v2` - 1024 dims, good balance
3. `BAAI/bge-large-en-v1.5` - 1024 dims, fast
4. `sentence-transformers/all-MiniLM-L6-v2` - 384 dims, lightweight

### Milvus Features

- **Scalability**: Billions of vectors
- **High Performance**: SIMD acceleration
- **Persistence**: ACID compliance
- **Hybrid Search**: Dense + sparse vectors
- **Filtering**: Metadata-based queries

## Performance Tips

1. **GPU Acceleration**: Install CUDA for 2-5x speedup
2. **Batch Processing**: Increase `RAG_BATCH_SIZE` for throughput
3. **Parallel Workers**: Set `RAG_MAX_WORKERS` based on CPU cores
4. **Milvus Tuning**: Adjust index parameters for dataset size
5. **Embedding Cache**: Reuse embeddings when possible

## Troubleshooting

### Milvus Connection Issues
```bash
# Check Docker containers
docker ps

# View Milvus logs
docker logs milvus-standalone

# Access Milvus web UI
open http://localhost:8000
```

### Memory Issues
- Reduce `RAG_BATCH_SIZE`
- Use smaller embedding model
- Enable `--use-lite` for development

### Slow Processing
- Enable GPU acceleration
- Increase `RAG_MAX_WORKERS`
- Use faster embedding model

## Architecture Details

### Data Flow

1. **PDF Input** → Docling Processor
2. **Markdown/JSON** → Chunk Extraction
3. **Text Chunks** → Embedding Manager
4. **Embeddings** → Milvus Vector Store
5. **Query** → Hybrid Retrieval
6. **Context** → Gemini LLM
7. **Response** → User

### Component Responsibilities

- **DoclingProcessor**: PDF parsing, OCR, table extraction
- **EmbeddingManager**: Multi-model embeddings, BM25
- **MilvusManager**: Vector CRUD, hybrid search
- **AdvancedRAGSystem**: Orchestration, LlamaIndex integration
- **CLI**: User interface, progress tracking

## Development

### Running Tests
```bash
pytest tests/test_legal_rag.py -v
```

### Code Quality
```bash
black legal_rag/
ruff check legal_rag/
mypy legal_rag/
```

## License

This project is for educational and research purposes. Ensure compliance with all applicable laws and terms of service.