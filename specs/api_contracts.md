# API Contracts

This document describes the external API endpoints and integrations used by the US Tax Court Document Processing System. This includes both document scraping APIs and AI/ML service integrations.

## Base URL
```
https://dawson.uscourts.gov/api
```

## Endpoints

### 1. Opinion Search
**Purpose**: Search for court opinions within a specified date range

**Endpoint**: `GET /opinion-search`

**Query Parameters**:
- `from` (string, required): Start date in format "MM/DD/YYYY"
- `to` (string, required): End date in format "MM/DD/YYYY"

**Response**: JSON array of opinion objects
```json
[
  {
    "docketNumber": "12345-21",
    "docketEntryId": "b5b8a7d6-1311-4d69-810a-ec6e0fafdb49",
    "caseCaption": "Petitioner v. Commissioner of Internal Revenue",
    "filingDate": "2024-12-31T00:00:00",
    "signedJudgeName": "Judge Name",
    "documentType": "Opinion",
    "servedDate": "2024-12-31T00:00:00",
    "pages": 15
  }
]
```

**Field Mappings**:
- `docketNumber` → Used as primary identifier
- `docketEntryId` → Used for document URL generation
- `caseCaption` → Case title
- `filingDate` → Date for organizing documents (YYYY-MM folders)
- `signedJudgeName` → Judge name (optional field)
- `documentType` → Type of document
- `servedDate` → Service date
- `pages` → Number of pages in PDF

**Rate Limits**: 
- Configurable delay between requests (default: 0.2 seconds)
- Automatic retry with exponential backoff on failures

### 2. Document Download URL
**Purpose**: Get the download URL for a specific court document

**Endpoint**: `GET /{docketNumber}/{docketEntryId}/public-document-download-url`

**Path Parameters**:
- `docketNumber` (string): The docket number from opinion search
- `docketEntryId` (string): The UUID document identifier

**Response**: JSON object with download URL
```json
{
  "url": "https://dawson.uscourts.gov/public/docket-display/download-document?documentId={docketEntryId}&docketNumber={docketNumber}&entityName=PublicDocumentSearchResult&sequenceNumber=1"
}
```

**Download URL Structure**:
The returned URL includes query parameters:
- `documentId`: The docket entry ID
- `docketNumber`: The case docket number
- `entityName`: Always "PublicDocumentSearchResult"
- `sequenceNumber`: Document sequence (typically 1)

### 3. PDF Document Download
**Purpose**: Download the actual PDF document

**Endpoint**: URL returned from Document Download URL endpoint

**Method**: `GET`

**Headers**:
- `User-Agent`: Standard browser user agent for compatibility

**Response**: Binary PDF file

**Error Handling**:
- 404: Document not found
- 429: Rate limit exceeded (triggers retry with backoff)
- 500+: Server errors (automatic retry)

## Authentication
No authentication is required for accessing public court documents.

## Rate Limiting Strategy
1. **Per-Worker Delay**: Configurable delay between requests (RATE_LIMIT_DELAY)
2. **Connection Pooling**: Reuse HTTP connections for efficiency
3. **Concurrent Workers**: Parallel downloads with configurable worker count (1-20)
4. **Automatic Backoff**: Exponential backoff on rate limit errors

## Error Responses
All endpoints may return standard HTTP error codes:
- `400`: Bad request (invalid parameters)
- `404`: Resource not found
- `429`: Too many requests (rate limited)
- `500`: Internal server error
- `503`: Service unavailable

## Network Configuration
- **Timeout**: 30 seconds per request
- **Connection Pool**: 100 connections total, 10 per host
- **Retry Attempts**: 3 attempts with exponential backoff
- **SSL Verification**: Enabled by default

## Usage Example

```python
# 1. Search for opinions
GET /opinion-search?from=01/01/2024&to=01/31/2024

# 2. Get download URL for each opinion
GET /12345-21/b5b8a7d6-1311-4d69-810a-ec6e0fafdb49/public-document-download-url

# 3. Download PDF from returned URL
GET https://dawson.uscourts.gov/public/docket-display/download-document?...
```

## Implementation Notes
- All API calls are made asynchronously using aiohttp
- Responses are validated using Pydantic models
- Failed downloads are tracked in SQLite for retry
- PDFs are saved with naming pattern: `{docket_number}_{document_id}.pdf`

## Google Gemini API Integration (Legal RAG System)

### Base URL
```
https://generativelanguage.googleapis.com
```

### Authentication
**API Key**: Required in environment variables as `GOOGLE_API_KEY`
```bash
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

### Endpoints Used

#### 1. Text Generation
**Purpose**: Generate AI responses for chat and search queries

**Model**: `gemini-1.5-flash` (configurable via `GEMINI_MODEL`)

**Request Format**:
```json
{
  "contents": [
    {
      "parts": [
        {
          "text": "Based on the following tax court documents, answer the question: [question]\n\nContext: [retrieved_document_text]"
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.1,
    "maxOutputTokens": 2048
  }
}
```

**Response**: Generated text response with legal analysis

#### 2. Embeddings (Optional)
**Purpose**: Generate embeddings for document indexing

**Model**: Available via `llama-index-embeddings-gemini`

**Usage**: Alternative to HuggingFace models for embedding generation

### Error Handling
- **401**: Invalid API key
- **429**: Rate limit exceeded
- **400**: Invalid request format
- **500**: Service unavailable

### Rate Limits
- **Free Tier**: 15 requests per minute
- **Paid Tier**: Higher limits based on plan
- Automatic retry with exponential backoff

## Milvus Database API (Legal RAG System)

### Connection Details
- **Host**: `localhost` (default) or configured via `MILVUS_HOST`
- **Port**: `19530` (default) or configured via `MILVUS_PORT`
- **Protocol**: gRPC for high-performance operations

### Collection Schema
```python
{
    "collection_name": "tax_court_documents",
    "dimension": 1024,  # Based on embedding model
    "fields": [
        {"name": "id", "type": "int64", "is_primary": True},
        {"name": "dense_vector", "type": "float_vector", "dimension": 1024},
        {"name": "sparse_vector", "type": "sparse_float_vector"},
        {"name": "text", "type": "varchar", "max_length": 65535},
        {"name": "source_file", "type": "varchar", "max_length": 512},
        {"name": "docket_number", "type": "varchar", "max_length": 100},
        {"name": "case_title", "type": "varchar", "max_length": 500},
        {"name": "judge", "type": "varchar", "max_length": 100},
        {"name": "year", "type": "int64"},
        {"name": "month", "type": "int64"}
    ]
}
```

### Index Configuration
```python
{
    "index_type": "HNSW",
    "metric_type": "IP",  # Inner Product for dense vectors
    "params": {
        "M": 16,
        "efConstruction": 200
    }
}
```

### Operations

#### Insert Documents
```python
milvus_client.insert(
    collection_name="tax_court_documents",
    data=[
        {
            "dense_vector": [0.1, 0.2, ...],  # 1024-dim vector
            "sparse_vector": {"indices": [1, 5, 10], "values": [0.8, 0.6, 0.4]},
            "text": "Document content...",
            "source_file": "path/to/file.pdf",
            "docket_number": "12345-21",
            "case_title": "Petitioner v. Commissioner",
            "judge": "Judge Name",
            "year": 2024,
            "month": 1
        }
    ]
)
```

#### Hybrid Search
```python
search_params = {
    "anns_field": "dense_vector",
    "param": {"metric_type": "IP", "params": {"ef": 100}},
    "limit": 10,
    "expr": "year == 2024"  # Optional filtering
}

results = milvus_client.search(
    collection_name="tax_court_documents",
    data=[query_vector],
    **search_params
)
```

### Attu Web UI
- **URL**: http://localhost:8000
- **Purpose**: Collection management, query testing, monitoring
- **Features**: 
  - Collection statistics
  - Index management
  - Query interface
  - Performance monitoring

## HuggingFace Hub Integration

### Model Downloads
- **Embedding Models**: Downloaded automatically on first use
- **Cache Location**: `~/.cache/huggingface/`
- **Supported Models**:
  - `intfloat/e5-large-v2` (1024 dimensions)
  - `Alibaba-NLP/gte-Qwen2-7B-instruct` (7680 dimensions)
  - `BAAI/bge-large-en-v1.5` (1024 dimensions)
  - `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)

### Authentication
- **Optional**: HuggingFace token for private models
- **Environment**: `HUGGINGFACE_HUB_TOKEN`

### Rate Limits
- **Downloads**: No specific limits for public models
- **API**: Standard rate limiting for model inference

## Docker Services API

### Milvus Stack
- **etcd**: Port 2379 (internal coordination)
- **MinIO**: Port 9000 (object storage), 9001 (console)
- **Milvus**: Port 19530 (main), 9091 (metrics)
- **Attu**: Port 8000 (web UI)

### Health Checks
```bash
# Check Milvus health
curl http://localhost:19530/health

# Check MinIO health
curl http://localhost:9000/minio/health/live

# Access Attu UI
open http://localhost:8000
```

### Service Dependencies
1. **etcd** must start first (coordination)
2. **MinIO** starts second (storage)
3. **Milvus** starts third (database engine)
4. **Attu** starts last (web interface)

## Error Handling Strategies

### Dawson API
- **Connection Timeout**: 30 seconds
- **Retry Strategy**: 3 attempts with exponential backoff
- **Rate Limiting**: Configurable delay between requests

### Google Gemini API
- **Timeout**: 60 seconds for text generation
- **Retry Logic**: Automatic retry on 429 (rate limit)
- **Fallback**: Graceful degradation if API unavailable

### Milvus Database
- **Connection Retry**: 5 attempts with backoff
- **Health Monitoring**: Automatic connection health checks
- **Fallback**: Embedded Milvus Lite for development

### HuggingFace Models
- **Download Retry**: 3 attempts for model downloads
- **Fallback Models**: Smaller models if large ones fail
- **Offline Mode**: Use cached models if network unavailable