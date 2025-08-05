# API Contracts

This document describes the external API endpoints used by the US Tax Court Document Scraper.

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