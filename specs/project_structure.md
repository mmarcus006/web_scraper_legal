# Project Structure

```
web_scraper_legal/
├── run.py                          # Main entry point with CLI commands
├── pyproject.toml                  # Project configuration and dependencies
├── uv.lock                         # Dependency lock file
├── README.md                       # Project documentation
├── CLAUDE.md                       # AI assistant instructions
├── .env                            # Environment configuration (optional)
│
├── dawson_scraper/                 # Main package directory
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
├── data/                           # Data storage directory
│   ├── json/                       # Monthly JSON metadata files
│   │   └── opinions_YYYY-MM-DD_to_YYYY-MM-DD.json
│   ├── documents/                  # Downloaded PDF documents
│   │   └── YYYY-MM/               # Organized by month
│   │       └── *.pdf              # Individual court opinions
│   ├── markdown_documents/         # Converted markdown files
│   │   └── YYYY-MM/               # Organized by month
│   │       └── *.md               # Converted documents with metadata
│   ├── vector_store/              # ChromaDB vector database
│   │   ├── chroma.sqlite3         # Vector index storage
│   │   └── metadata/              # Document metadata
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
└── .venv/                          # Python virtual environment
    └── Lib/site-packages/          # Installed packages
```

## File Naming Conventions

- **JSON files**: `opinions_YYYY-MM-DD_to_YYYY-MM-DD.json` - Monthly opinion metadata
- **PDF files**: `{docket_number}_{document_id}.pdf` - Individual court documents
- **Markdown files**: `{docket_number}_{document_id}.md` - Converted documents with metadata
- **Log files**: Component-specific logs with descriptive names
- **Databases**: Multiple SQLite databases for different purposes
  - `dawson_scraper.db` - Main scraping operations
  - `processing.db` - PDF processing status
  - `chroma.sqlite3` - Vector index storage

## Key Directories

- **Source Code**: All Python modules in `dawson_scraper/src/`
- **Data Storage**: Organized under `data/` with separate folders for:
  - Raw JSON metadata
  - Original PDF documents
  - Converted markdown documents
  - Vector embeddings and search index
  - Processing status databases
- **Documentation**: Technical specs in `specs/` folder
- **Configuration**: Environment settings in root `.env` file
- **Virtual Environment**: Dependencies isolated in `.venv/`

## Data Flow Structure

1. **Scraping Phase**: `run.py` downloads PDFs to `data/documents/YYYY-MM/`
2. **Processing Phase**: `cli_rag.py process-pdfs` converts PDFs to `data/markdown_documents/YYYY-MM/`
3. **Indexing Phase**: `cli_rag.py build-index` creates vector embeddings in `data/vector_store/`
4. **Search Phase**: `cli_rag.py search` queries the vector index for relevant documents