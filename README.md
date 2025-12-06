# Document Summarization + Metadata Extraction Service

A production-ready FastAPI service for intelligent document processing with PDF text extraction, LLM-powered analysis, and metadata extraction.

## Features

- **PDF Text Extraction**: Robust PDF parsing with PyPDF2
- **S3-Compatible Storage**: File storage in Minio (or AWS S3)
- **LLM Integration**: OpenRouter API for intelligent analysis
- **Metadata Extraction**: Automatic extraction of dates, senders, amounts, entities
- **Document Classification**: Automatic type detection (invoice, CV, report, etc.)
- **Async Processing**: Non-blocking API operations
- **PostgreSQL Storage**: Persistent storage with structured queries
- **Error Handling**: Comprehensive validation and error responses

## API Endpoints

### 1. Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data

file: <PDF file, max 5MB>
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "invoice.pdf",
  "message": "Document uploaded and text extracted successfully"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid file type or extraction failed
- `413`: File size exceeds limit
- `500`: Server error

---

### 2. Analyze Document
```http
POST /documents/{id}/analyze
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "Invoice from Acme Corp for services totaling $1,100.00 with net 30 payment terms.",
  "document_type": "invoice",
  "metadata": {
    "date": "2024-12-05",
    "sender": "Acme Corp, 123 Business St",
    "recipient": "Customer Inc, 456 Client Ave",
    "total_amount": "$1,100.00",
    "key_entities": ["Acme Corp", "Customer Inc"],
    "subject": "Invoice #INV-2024-001"
  }
}
```

**Status Codes:**
- `200`: Success
- `404`: Document not found
- `400`: No extracted text
- `500`: LLM analysis error

---

### 3. Get Document
```http
GET /documents/{id}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "invoice.pdf",
  "extracted_text": "INVOICE...",
  "summary": "Invoice from Acme Corp...",
  "document_type": "invoice",
  "metadata": {
    "date": "2024-12-05",
    "sender": "Acme Corp",
    "total_amount": "$1,100.00"
  },
  "created_at": "2024-12-05T10:30:00",
  "analyzed_at": "2024-12-05T10:31:00"
}
```

**Status Codes:**
- `200`: Success
- `404`: Document not found
- `500`: Server error

---

## Installation & Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (optional)
- OpenRouter API Key

### Quick Start (Docker)

1. **Clone and setup**
```bash
git clone https://github.com/Toluwaa-o/ai_document_parser.git
cd ai-document-parser
```

2. **Create `.env` file**
```bash
OPENROUTER_API_KEY=sk-or-... # Get from https://openrouter.ai
DATABASE_URL=postgresql://user:password@postgres/documents_db
```

3. **Start services**
```bash
docker-compose up
```

The service will be available at `http://localhost:8000`

### Manual Installation

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Setup PostgreSQL**
```bash
createdb documents_db
psql documents_db < schema.sql
```

3. **Setup Minio (or use AWS S3)**
```bash
# Using Docker
docker run -p 9000:9000 -p 9001:9001 minio/minio server /minio_data

# Or configure AWS S3 credentials
```

4. **Run the service**
```bash
export OPENROUTER_API_KEY=your_key_here
uvicorn main:app --reload
```

## Usage Examples

### Python Client

```python
from client import DocumentClient

client = DocumentClient()

# Upload and process
result = client.process_workflow("invoice.pdf")

print(f"Document ID: {result['upload']['id']}")
print(f"Type: {result['analysis']['document_type']}")
print(f"Summary: {result['analysis']['summary']}")
print(f"Metadata: {result['analysis']['metadata']}")

client.close()
```

### cURL

```bash
# Upload
curl -X POST -F "file=@invoice.pdf" \
  http://localhost:8000/documents/upload

# Analyze
curl -X POST \
  http://localhost:8000/documents/{id}/analyze

# Get
curl http://localhost:8000/documents/{id}
```


## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user:password@localhost/documents_db` | PostgreSQL connection string |
| `OPENROUTER_API_KEY` | (required) | OpenRouter API key |
| `MINIO_ENDPOINT` | `localhost:9000` | Minio server endpoint |
| `MINIO_ACCESS_KEY` | `minioadmin` | Minio access key |
| `MINIO_SECRET_KEY` | `minioadmin` | Minio secret key |


## Error Handling

### Common Errors

**400 - Bad Request: File type not supported**
- Solution: Ensure file is PDF format

**413 - Payload Too Large**
- Solution: Reduce file size to under 5MB

**500 - Internal Server Error: OpenRouter API error**
- Solution: Verify API key is valid and has quota

**404 - Not Found**
- Solution: Check document ID is correct


## Monitoring & Logging

- **Health Check**: `GET /health`
- **Logs**: Check container logs with `docker logs`