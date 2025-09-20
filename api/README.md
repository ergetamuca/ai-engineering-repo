# Document AI Assistant API

FastAPI backend for the Document AI Assistant application.

## 🚀 Features

- **PDF Processing**: Extract text from PDF documents using pypdf
- **CSV Analysis**: Parse and analyze CSV files for legal discovery
- **AI Integration**: OpenAI GPT-4 for document analysis and chat
- **Legal Focus**: Specialized prompts for legal document analysis
- **Real-time Streaming**: Streaming responses for better UX

## 📋 API Endpoints

### Health Check
```
GET /api/health
```
Returns API status.

### Document Status
```
GET /api/document-status
```
Returns information about uploaded documents.

### Upload Document
```
POST /api/upload-document
```
Upload PDF or CSV files for analysis.

**Parameters:**
- `file`: PDF or CSV file (multipart/form-data)
- `api_key`: OpenAI API key (form data)

**Response:**
```json
{
  "message": "Document uploaded and processed successfully",
  "success": true,
  "document_name": "example.pdf",
  "document_type": "pdf",
  "document_id": "uuid",
  "analysis": {
    "case_numbers": ["Case-123"],
    "dates": ["2023-01-01"]
  }
}
```

### Chat with Documents
```
POST /api/rag-chat
```
Chat with uploaded documents using RAG (Retrieval-Augmented Generation).

**Request Body:**
```json
{
  "user_message": "What is this document about?",
  "api_key": "your-openai-api-key"
}
```

**Response:** Streaming text response

## 🛠️ Dependencies

- `fastapi==0.115.12` - Web framework
- `uvicorn==0.34.2` - ASGI server
- `openai==1.77.0` - OpenAI API client
- `pydantic==2.11.4` - Data validation
- `python-multipart==0.0.18` - File upload support
- `pypdf==4.0.1` - PDF text extraction
- `python-dotenv==1.0.0` - Environment variables

## 🚀 Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

3. Run the server:
   ```bash
   uvicorn index:app --reload
   ```

4. API will be available at `http://localhost:8000`

## 📊 Document Processing

### PDF Processing
- Extracts text from all pages
- Splits into chunks for RAG
- Analyzes for legal terms, case numbers, dates

### CSV Processing
- Parses CSV structure and data
- Converts to text format for analysis
- Identifies patterns and relationships
- Focuses on legal relevance

## 🔧 Configuration

- **File Size Limits**: PDF (4MB), CSV (10MB)
- **Chunk Size**: 1000 characters with 200 overlap
- **AI Model**: GPT-4o for analysis, GPT-4o-mini for chat
- **Max Tokens**: 2000 for analysis responses

## 🚨 Error Handling

- File type validation
- Size limit enforcement
- API key validation
- Graceful error responses with helpful messages