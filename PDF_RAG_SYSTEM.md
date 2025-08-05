# US Tax Court PDF Processing & RAG System

## Overview

This system provides advanced PDF processing capabilities using IBM Docling and a Retrieval-Augmented Generation (RAG) system using LlamaIndex for searching US Tax Court documents.

## Features

- **High-Quality PDF Processing**: Uses IBM Docling with OCR and table recognition
- **Batch Processing**: Process thousands of PDFs in parallel
- **Markdown Conversion**: Converts PDFs to searchable markdown format
- **Vector Search**: Semantic search using LlamaIndex and HuggingFace embeddings
- **Metadata Extraction**: Automatic extraction of dates, docket numbers, and judges
- **Resume Capability**: Resume interrupted processing
- **CLI Interface**: Easy-to-use command-line tools

## Installation

### Prerequisites

1. **Windows Users**: Install Microsoft C++ Build Tools first:
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install with "Desktop development with C++" workload

2. **Python 3.10+** required

### Install Dependencies

```bash
# Basic installation (includes Docling and LlamaIndex)
pip install -e ".[pdf-processing]"

# With OCR support
pip install -e ".[pdf-processing,ocr]"

# With GPU acceleration (CUDA 11.8)
pip install -e ".[pdf-processing,cuda118]"

# All features
pip install -e ".[docling-all]"
```

## Quick Start

### 1. Process PDFs to Markdown

Convert all PDFs in `data/documents` to markdown format:

```bash
# Basic processing
python -m dawson_scraper.src.cli_rag process-pdfs

# With more workers for faster processing
python -m dawson_scraper.src.cli_rag process-pdfs --workers 8

# Process specific month
python -m dawson_scraper.src.cli_rag process-pdfs --filter "2020-01/*.pdf"

# Enable Vision-Language Model for better accuracy (slower)
python -m dawson_scraper.src.cli_rag process-pdfs --enable-vlm
```

### 2. Build Search Index

Create a searchable vector index from markdown documents:

```bash
# Build new index
python -m dawson_scraper.src.cli_rag build-index

# Update existing index incrementally
python -m dawson_scraper.src.cli_rag build-index --incremental
```

### 3. Search Documents

Search the indexed documents:

```bash
# Basic search
python -m dawson_scraper.src.cli_rag search "capital gains tax"

# Search with filters
python -m dawson_scraper.src.cli_rag search "medical deduction" --year 2023

# Get more results
python -m dawson_scraper.src.cli_rag search "tax shelter" --top-k 10

# Output as JSON
python -m dawson_scraper.src.cli_rag search "partnership" --json-output
```

### 4. View Statistics

```bash
python -m dawson_scraper.src.cli_rag stats
```

## Directory Structure

```
data/
├── documents/              # Original PDF files (from scraper)
│   ├── 2020-01/
│   ├── 2020-02/
│   └── ...
├── markdown_documents/     # Converted markdown files
│   ├── 2020-01/
│   │   ├── docket-number.md
│   │   └── docket-number.json  # Metadata
│   └── ...
├── vector_store/          # LlamaIndex vector database
│   ├── docstore.json
│   └── model_cache/      # Cached embedding models
└── processing_stats/      # Processing tracking database
    └── processing.db
```

## Advanced Usage

### Batch Processing with Python

```python
from dawson_scraper.src.batch_pdf_processor import BatchPDFProcessor

processor = BatchPDFProcessor(
    input_dir="data/documents",
    output_dir="data/markdown_documents",
    max_workers=8,
    enable_ocr=True,
    enable_table_structure=True,
    enable_vlm=False  # Set True for highest accuracy
)

stats = processor.process_all_pdfs(skip_existing=True)
print(f"Processed {stats['processed']} PDFs")
```

### RAG System with Python

```python
from dawson_scraper.src.rag_system import TaxCourtRAGSystem

# Initialize RAG system
rag = TaxCourtRAGSystem(
    markdown_dir="data/markdown_documents",
    embedding_model="BAAI/bge-base-en-v1.5"
)

# Build index
rag.build_index(persist=True)

# Search
results = rag.search(
    query="capital gains from cryptocurrency",
    top_k=5,
    filters={"year": 2023}
)

print(f"Found {len(results['source_nodes'])} relevant documents")
for node in results['source_nodes']:
    print(f"- {node['metadata']['source_file']}: Score {node['score']:.3f}")
```

### Custom PDF Processing

```python
from dawson_scraper.src.pdf_pipeline import (
    create_docling_converter,
    convert_pdf_to_markdown,
    save_markdown_with_metadata
)

# Create converter with custom settings
converter = create_docling_converter(
    enable_ocr=True,
    enable_table_structure=True,
    enable_vlm=True,  # Use Vision-Language Model
    max_threads=16    # Use all CPU cores
)

# Convert single PDF
markdown, metadata = convert_pdf_to_markdown(
    "path/to/document.pdf",
    converter=converter
)

# Save results
save_markdown_with_metadata(
    markdown, 
    metadata, 
    "output/document"
)
```

## Performance Optimization

### PDF Processing Speed

- **Default**: ~2-3 pages/second on modern CPU
- **With VLM**: ~0.5-1 page/second (more accurate)
- **With GPU**: 2-5x faster for VLM processing

### Tips for Better Performance

1. **Increase Workers**: Use `--workers` equal to CPU cores
2. **Skip OCR**: Disable OCR if PDFs have embedded text
3. **Batch Processing**: Process multiple PDFs in parallel
4. **Incremental Updates**: Use `--incremental` for index updates

### Memory Requirements

- **Minimum**: 8 GB RAM
- **Recommended**: 16 GB RAM for batch processing
- **GPU**: 8+ GB VRAM for CUDA acceleration

## Configuration

### Environment Variables

```bash
# Set thread count for Docling (auto-detected by default)
export OMP_NUM_THREADS=16

# Disable transformer warnings
export TRANSFORMERS_VERBOSITY=error

# Set Docling log level
export DOCLING_LOG_LEVEL=INFO
```

### Embedding Models

The system uses HuggingFace embedding models. Default is `BAAI/bge-base-en-v1.5`. 

Other options:
- `sentence-transformers/all-MiniLM-L6-v2` (faster, less accurate)
- `BAAI/bge-large-en-v1.5` (slower, more accurate)
- `thenlper/gte-base` (good balance)

## Troubleshooting

### Common Issues

1. **ImportError for LlamaIndex**
   ```bash
   pip install llama-index llama-index-embeddings-huggingface
   ```

2. **Windows C++ Build Tools Error**
   - Install Visual Studio Build Tools
   - Select "Desktop development with C++" workload

3. **Out of Memory**
   - Reduce `--workers` count
   - Process in smaller batches
   - Reduce `--chunk-size` for indexing

4. **Slow Processing**
   - Disable VLM if not needed
   - Increase worker count
   - Use GPU acceleration if available

### Logging

Logs are saved to `logs/` directory:
- `docling_*.log` - PDF processing logs
- `batch_processing_*.log` - Batch processor logs

## API Reference

### CLI Commands

- `process-pdfs` - Convert PDFs to markdown
- `build-index` - Build vector search index
- `search` - Search documents
- `stats` - Show system statistics
- `quickstart` - Display quick start guide

### Python Modules

- `pdf_pipeline.py` - Core Docling PDF processing
- `batch_pdf_processor.py` - Batch processing system
- `rag_system.py` - LlamaIndex RAG implementation
- `cli_rag.py` - Command-line interface

## License

This project uses open-source components:
- IBM Docling: MIT License
- LlamaIndex: MIT License
- HuggingFace Transformers: Apache 2.0

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Run `python -m dawson_scraper.src.cli_rag quickstart`
3. Review this documentation