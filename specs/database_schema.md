# Database Schema

This document describes the SQLite database structures used for tracking downloads, PDF processing, and state management.

## Database Locations
```
data/db/dawson_scraper.db          # Main scraping operations
data/processing_stats/processing.db # PDF processing tracking
data/vector_store/chroma.sqlite3    # Vector embeddings (ChromaDB)
```

## Main Database Tables (dawson_scraper.db)

### 1. downloads
**Purpose**: Tracks individual document downloads, their status, and metadata

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| docket_number | STRING | NOT NULL, INDEX | Case docket number (e.g., "12345-21") |
| docket_entry_id | STRING | NOT NULL, UNIQUE | UUID document identifier |
| case_caption | STRING | | Full case title |
| document_title | TEXT | | Document title/description |
| filing_date | DATETIME | | Date document was filed |
| judge | STRING | | Name of the signing judge |
| pages | INTEGER | | Number of pages in document |
| download_url | STRING | | Full URL for downloading PDF |
| file_path | STRING | | Local path where PDF is saved |
| file_size | INTEGER | | Size of downloaded file in bytes |
| status | STRING | DEFAULT 'pending' | Download status (see below) |
| attempts | INTEGER | DEFAULT 0 | Number of download attempts |
| error_message | TEXT | | Error details if download failed |
| created_at | DATETIME | DEFAULT NOW | When record was created |
| started_at | DATETIME | | When download started |
| completed_at | DATETIME | | When download completed |

**Status Values**:
- `pending`: Download not yet attempted
- `in_progress`: Currently downloading
- `completed`: Successfully downloaded
- `failed`: Download failed after max retries
- `skipped`: Skipped (file already exists)

**Indexes**:
- Primary key on `id`
- Index on `docket_number` for fast lookups
- Unique constraint on `docket_entry_id` to prevent duplicates

### 2. searches
**Purpose**: Tracks monthly search operations and their results

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| start_date | DATETIME | NOT NULL | Search period start date |
| end_date | DATETIME | NOT NULL | Search period end date |
| opinions_found | INTEGER | DEFAULT 0 | Number of opinions found |
| json_path | STRING | | Path to saved JSON file |
| status | STRING | DEFAULT 'pending' | Search status |
| error_message | TEXT | | Error details if search failed |
| created_at | DATETIME | DEFAULT NOW | When search was initiated |
| completed_at | DATETIME | | When search completed |

**Status Values**:
- `pending`: Search not yet executed
- `in_progress`: Currently searching
- `completed`: Successfully completed
- `failed`: Search failed

## Relationships

- **One-to-Many**: Each search can result in many download records
- **Foreign Key**: Downloads are linked to searches via date ranges (implicit relationship)

## Common Queries

### Get Download Statistics
```sql
SELECT 
    status,
    COUNT(*) as count,
    SUM(file_size)/1024/1024 as size_mb
FROM downloads
GROUP BY status;
```

### Find Failed Downloads
```sql
SELECT 
    docket_number,
    docket_entry_id,
    error_message,
    attempts
FROM downloads
WHERE status = 'failed'
ORDER BY created_at DESC;
```

### Get Monthly Download Progress
```sql
SELECT 
    DATE(filing_date, 'start of month') as month,
    COUNT(*) as total_docs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM downloads
GROUP BY month
ORDER BY month;
```

### Find Incomplete Periods
```sql
SELECT 
    start_date,
    end_date,
    opinions_found,
    status
FROM searches
WHERE status != 'completed'
ORDER BY start_date;
```

### Calculate Download Success Rate
```sql
SELECT 
    COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate,
    AVG(attempts) as avg_attempts,
    SUM(file_size)/1024/1024/1024 as total_gb
FROM downloads
WHERE status IN ('completed', 'failed');
```

## PDF Processing Database (processing.db)

### 3. pdf_processing
**Purpose**: Tracks PDF to markdown conversion operations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| pdf_path | STRING | NOT NULL, UNIQUE | Full path to source PDF file |
| markdown_path | STRING | | Path to generated markdown file |
| status | STRING | DEFAULT 'pending' | Processing status (see below) |
| pages | INTEGER | | Number of pages in PDF |
| processing_time | FLOAT | | Time taken to process (seconds) |
| error_message | TEXT | | Error details if processing failed |
| created_at | DATETIME | DEFAULT NOW | When record was created |
| completed_at | DATETIME | | When processing completed |

**Processing Status Values**:
- `pending`: Not yet processed
- `processing`: Currently being processed
- `completed`: Successfully converted to markdown
- `failed`: Processing failed
- `skipped`: Skipped (file already exists)

### PDF Processing Queries

```sql
-- Check processing statistics
SELECT 
    status,
    COUNT(*) as count,
    AVG(processing_time) as avg_time_seconds,
    SUM(pages) as total_pages
FROM pdf_processing
GROUP BY status;

-- Find processing failures
SELECT 
    pdf_path,
    error_message,
    processing_time
FROM pdf_processing
WHERE status = 'failed'
ORDER BY created_at DESC;

-- Calculate processing throughput
SELECT 
    DATE(created_at) as date,
    COUNT(*) as files_processed,
    SUM(pages) as pages_processed,
    AVG(processing_time) as avg_time_per_file
FROM pdf_processing
WHERE status = 'completed'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## Vector Store Database (chroma.sqlite3)

Managed by ChromaDB, contains:
- Document embeddings as high-dimensional vectors
- Metadata for each document chunk
- Collection information for different document sets
- Vector similarity indices for fast search

Accessed through the RAG system API rather than direct SQL queries.

## Database Operations

### Key Functions by Database

**DatabaseManager (dawson_scraper.db)**:
1. **initialize()**: Creates database and tables if they don't exist
2. **record_opinion()**: Inserts or updates a download record
3. **record_search()**: Tracks a search operation
4. **update_download_status()**: Updates status and metadata for a download
5. **get_pending_downloads()**: Retrieves downloads that need retry
6. **get_statistics()**: Generates comprehensive statistics
7. **cleanup_stale_downloads()**: Marks stuck downloads as failed

**BatchPDFProcessor (processing.db)**:
1. **initialize_db()**: Creates processing database and tables
2. **get_pdf_files()**: Discovers PDF files for processing
3. **record_processing()**: Tracks PDF conversion status
4. **update_processing_status()**: Updates processing results
5. **get_processing_stats()**: Generates processing statistics
6. **skip_existing()**: Checks for already-processed files

**TaxCourtRAGSystem (chroma.sqlite3)**:
1. **build_index()**: Creates vector embeddings from markdown documents
2. **search()**: Performs semantic search queries
3. **add_documents()**: Adds new documents to the index
4. **update_index()**: Incremental index updates
5. **get_metadata()**: Retrieves document metadata

## Data Retention

- Download records are kept indefinitely for audit purposes
- Failed downloads retain error messages for debugging
- Search records maintain full history of API calls

## Performance Considerations

- SQLite uses WAL (Write-Ahead Logging) mode for better concurrency
- Indexes on frequently queried columns (docket_number, status)
- Async operations via aiosqlite for non-blocking I/O
- Connection pooling handled by context managers

## Backup Recommendations

```bash
# Backup main database
sqlite3 data/db/dawson_scraper.db ".backup data/db/backup.db"

# Backup processing database
sqlite3 data/processing_stats/processing.db ".backup data/processing_stats/backup.db"

# Backup vector store (entire directory)
cp -r data/vector_store data/vector_store_backup

# Export to SQL
sqlite3 data/db/dawson_scraper.db .dump > dawson_backup.sql
sqlite3 data/processing_stats/processing.db .dump > processing_backup.sql

# Verify integrity
sqlite3 data/db/dawson_scraper.db "PRAGMA integrity_check;"
sqlite3 data/processing_stats/processing.db "PRAGMA integrity_check;"
sqlite3 data/vector_store/chroma.sqlite3 "PRAGMA integrity_check;"
```