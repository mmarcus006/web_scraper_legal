# Project Structure

```
web_scraper_legal/
├── run.py                          # Main entry point with CLI commands
├── pyproject.toml                  # Project configuration and dependencies
├── docker-compose.yml              # Milvus services for Legal RAG System
├── README.md                       # Project documentation
├── CLAUDE.md                       # AI assistant instructions
├── .env                            # Environment configuration (optional)
│
├── dawson_scraper/                 # ChromaDB RAG System (Development)
│   ├── scripts/                    # Utility scripts
│   └── src/                        # Source code modules
│       ├── __init__.py             # Package initialization
│       ├── config.py               # Settings management (Pydantic)
│       ├── models.py               # Data models for opinions
│       ├── database.py             # SQLite persistence layer
│       ├── api_client.py           # Async HTTP client for Dawson API
│       ├── downloader.py           # Parallel download manager
│       ├── scraper.py              # Main orchestration logic
│       ├── utils.py                # Utility functions
│       ├── pdf_pipeline.py         # IBM Docling PDF processing
│       ├── batch_pdf_processor.py  # Bulk PDF conversion system
│       ├── rag_system.py           # LlamaIndex RAG implementation
│       └── cli_rag.py              # CLI for PDF processing and search
│
├── legal_rag/                      # Legal RAG System (Production)
│   ├── __init__.py                 # Package initialization
│   ├── README.md                   # Legal RAG System documentation
│   └── src/                        # Legal RAG source modules
│       ├── __init__.py             # Package initialization
│       ├── config.py               # Milvus and Gemini configuration
│       ├── milvus_manager.py       # Milvus vector database operations
│       ├── docling_processor.py    # Enhanced PDF processing with Docling
│       ├── embedding_manager.py    # Multi-model embedding management
│       ├── advanced_rag_system.py  # LlamaIndex orchestration with Milvus
│       └── cli.py                  # Rich terminal interface for Legal RAG
│
├── data/                           # Data storage directory
│   ├── json/                       # Monthly JSON metadata files
│   │   └── opinions_YYYY-MM-DD_to_YYYY-MM-DD.json
│   ├── documents/                  # Downloaded PDF documents
│   │   └── YYYY-MM/               # Organized by month
│   │       └── *.pdf              # Individual court opinions
│   ├── markdown_documents/         # Converted markdown files (ChromaDB RAG)
│   │   └── YYYY-MM/               # Organized by month
│   │       ├── *.md               # Clean text for RAG/search
│   │       └── *.json             # Processing metadata only
│   ├── json_documents/            # Docling JSON documents (complete structure)
│   │   └── YYYY-MM/               # Organized by month
│   │       └── *.json             # Complete document structure with tables/images
│   ├── processed/                  # Legal RAG System processed documents
│   │   └── YYYY-MM/               # Organized by month
│   │       ├── *.md               # Processed markdown for Legal RAG
│   │       └── *.json             # Document metadata and processing info
│   ├── vector_store/              # ChromaDB vector database
│   │   ├── chroma.sqlite3         # Vector index storage
│   │   └── metadata/              # Document metadata
│   ├── milvus/                     # Milvus vector database data
│   │   ├── etcd/                  # etcd coordination service data
│   │   ├── minio/                 # Object storage for Milvus
│   │   └── milvus/                # Milvus engine data
│   ├── processing_stats/          # PDF processing tracking
│   │   └── processing.db          # Processing status database
│   └── db/                        # Database files
│       └── dawson_scraper.db      # Main SQLite database
│
├── logs/                           # Application logs
│   ├── dawson_scraper.log         # Main application log
│   ├── chat.json                  # Claude hook logs
│   ├── notification.json          # Notification hook logs
│   ├── post_tool_use.json         # Post tool use hook logs
│   ├── pre_tool_use.json          # Pre tool use hook logs
│   ├── session_start.json         # Session start hook logs
│   ├── stop.json                  # Stop hook logs
│   └── user_prompt_submit.json    # User prompt hook logs
│
├── specs/                          # Project documentation
│   ├── project_overview.md        # High-level project summary
│   ├── tech_stack.md              # Technology and dependencies
│   ├── project_structure.md       # This file
│   ├── module_overview.md         # Module responsibilities
│   ├── setup_guide.md             # Setup instructions
│   ├── api_contracts.md          # API documentation
│   └── database_schema.md         # Database structure
│
├── .claude/                        # Claude Code configuration
│   ├── agents/                    # AI agent configurations
│   ├── commands/                  # Custom commands
│   ├── hooks/                     # Event hooks
│   │   └── utils/                 # Hook utilities
│   │       ├── llm/              # LLM utilities
│   │       └── tts/              # Text-to-speech utilities
│   ├── settings.json              # Global settings
│   └── settings.local.json        # Local settings overrides
│
├── .claude/                        # Claude Code configuration
│   ├── agents/                    # AI agent configurations
│   ├── commands/                  # Custom commands
│   ├── hooks/                     # Event hooks
│   │   └── utils/                 # Hook utilities
│   │       ├── llm/              # LLM utilities
│   │       └── tts/              # Text-to-speech utilities
│   ├── settings.json              # Global settings
│   └── settings.local.json        # Local settings overrides
│
└── .venv/                          # Python virtual environment
    └── Lib/site-packages/          # Installed packages
```

## File Naming Conventions

- **JSON files**: `opinions_YYYY-MM-DD_to_YYYY-MM-DD.json` - Monthly opinion metadata
- **PDF files**: `{docket_number}_{document_id}.pdf` - Individual court documents
- **Markdown files**: `{docket_number}_{document_id}.md` - Clean text for RAG/search
- **Docling JSON files**: `{docket_number}_{document_id}.json` - Complete document structure
- **Log files**: Component-specific logs with descriptive names
- **Databases**: Multiple database systems for different purposes
  - `dawson_scraper.db` - Main scraping operations (SQLite)
  - `processing.db` - PDF processing status (SQLite)
  - `chroma.sqlite3` - ChromaDB vector index storage (SQLite)
  - Milvus collections - Production vector database (distributed)

## Docker Services (Legal RAG System)

- **etcd**: Coordination service for Milvus cluster
- **minio**: Object storage backend for Milvus
- **milvus**: Main vector database engine
- **attu**: Web UI for Milvus management (http://localhost:8000)

## Key Directories

- **ChromaDB RAG System**: Python modules in `dawson_scraper/src/`
- **Legal RAG System**: Python modules in `legal_rag/src/`
- **Data Storage**: Organized under `data/` with separate folders for:
  - Raw JSON metadata from Dawson API
  - Original PDF documents organized by month
  - Converted markdown documents (optimized for RAG/search)
  - Docling JSON documents (complete structure with tables/images)
  - Legal RAG processed documents in `data/processed/`
  - ChromaDB vector embeddings in `data/vector_store/`
  - Milvus vector database data in `data/milvus/`
  - Processing status databases
- **Documentation**: Technical specs in `specs/` folder
- **Docker Services**: Milvus stack defined in `docker-compose.yml`
- **Configuration**: Environment settings in root `.env` file
- **Virtual Environment**: Dependencies isolated in `.venv/`

## Data Flow Structure

### ChromaDB RAG System Workflow
1. **Scraping Phase**: `dawson` (run.py) downloads PDFs to `data/documents/YYYY-MM/`
2. **Processing Phase**: `dawson-rag process-pdfs` converts PDFs to dual formats:
   - Markdown files in `data/markdown_documents/YYYY-MM/` (for RAG/search)
   - Docling JSON files in `data/json_documents/YYYY-MM/` (complete structure)
3. **Indexing Phase**: `dawson-rag build-index` creates vector embeddings from markdown in `data/vector_store/`
4. **Search Phase**: `dawson-rag search` queries the ChromaDB vector index for relevant documents

### Legal RAG System Workflow
1. **Scraping Phase**: Same as above - `dawson` downloads PDFs to `data/documents/YYYY-MM/`
2. **Docker Setup**: `docker-compose up -d` starts Milvus services
3. **Processing Phase**: `legal-rag process` uses advanced Docling to process PDFs to `data/processed/YYYY-MM/`
4. **Indexing Phase**: `legal-rag index` creates hybrid vector index (dense + sparse) in Milvus
5. **Search Phase**: `legal-rag search` performs hybrid search with AI-powered responses
6. **Chat Phase**: `legal-rag chat` provides interactive conversational interface
7. **Analysis Phase**: Rich terminal interface with statistics and management via Attu web UI

### System Choice Guidelines
- **Use ChromaDB RAG**: Development, testing, small collections (<10,000 docs)
- **Use Legal RAG System**: Production, large collections, AI responses, hybrid search requirements