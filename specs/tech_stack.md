# Technology Stack

## Primary Language
- **Python 3.10+** (tested with 3.13.5)

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

### Additional Dependencies (from README)
- **PyPDF2** - PDF file verification and validation
- **python-dateutil** - Advanced date/time parsing and manipulation

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

## Platform Support
- Windows (MSYS_NT, native Windows)
- macOS
- Linux

## Database
- **SQLite** - Embedded database for state persistence and download tracking

## External APIs
- **Dawson Court API** - US Tax Court document search and retrieval service