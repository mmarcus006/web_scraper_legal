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
│       └── utils.py                # Utility functions
│
├── data/                           # Data storage directory
│   ├── json/                       # Monthly JSON metadata files
│   │   └── opinions_YYYY-MM-DD_to_YYYY-MM-DD.json
│   ├── documents/                  # Downloaded PDF documents
│   │   └── YYYY-MM/               # Organized by month
│   │       └── *.pdf              # Individual court opinions
│   └── db/                        # Database files
│       └── dawson_scraper.db      # SQLite database
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
- **Log files**: Component-specific logs with descriptive names
- **Database**: Single SQLite database for all state management

## Key Directories

- **Source Code**: All Python modules in `dawson_scraper/src/`
- **Data Storage**: Organized under `data/` with separate folders for JSON, PDFs, and database
- **Documentation**: Technical specs in `specs/` folder
- **Configuration**: Environment settings in root `.env` file
- **Virtual Environment**: Dependencies isolated in `.venv/`