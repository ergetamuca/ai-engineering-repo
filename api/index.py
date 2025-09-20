from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import tempfile
import shutil
import base64
from typing import Optional, List, Dict, Any
import pypdf
from PIL import Image
import io

# Initialize FastAPI application
app = FastAPI(title="Legal Discovery AI Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for RAG system
vector_db = None
chat_model = None
uploaded_documents = []  # Store both PDFs and images
document_metadata = {}  # Store metadata for each document

# Data models
class ChatRequest(BaseModel):
    developer_message: str
    user_message: str
    model: Optional[str] = "gpt-4o-mini"
    api_key: str

class RAGChatRequest(BaseModel):
    user_message: str
    model: Optional[str] = "gpt-4o-mini"
    api_key: str

class UploadResponse(BaseModel):
    message: str
    success: bool
    document_name: Optional[str] = None
    document_type: Optional[str] = None
    document_id: Optional[str] = None

class LegalAnalysisRequest(BaseModel):
    user_message: str
    analysis_type: Optional[str] = "general"  # general, relationships, inconsistencies, citations
    api_key: str

# Simple PDF loader function
def load_pdf_text(file_path: str) -> List[str]:
    """Load text from PDF file using pypdf."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            pages = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    pages.append(text)
            return pages
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

# Image processing function
def process_image(file_path: str, api_key: str) -> Dict[str, Any]:
    """Process image and extract text using OpenAI Vision API."""
    try:
        client = OpenAI(api_key=api_key)
        
        # Read and encode image
        with open(file_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Use OpenAI Vision API to analyze image
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this legal document image. Extract all text content, identify key legal terms, dates, names, case numbers, and any visual elements that might be relevant for legal discovery. Provide a detailed description of the document structure and content."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        analysis = response.choices[0].message.content
        
        return {
            "text_content": analysis,
            "document_type": "image",
            "analysis": analysis
        }
        
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")

# Legal document analyzer
def analyze_legal_document(content: str, doc_type: str) -> Dict[str, Any]:
    """Analyze legal document for key elements."""
    analysis = {
        "key_terms": [],
        "dates": [],
        "names": [],
        "case_numbers": [],
        "legal_citations": [],
        "document_type": doc_type
    }
    
    # Simple keyword extraction (in a real app, you'd use more sophisticated NLP)
    content_lower = content.lower()
    
    # Extract potential case numbers
    import re
    case_patterns = [
        r'case no\.?\s*:?\s*([A-Z0-9\-]+)',
        r'civil action no\.?\s*:?\s*([A-Z0-9\-]+)',
        r'docket no\.?\s*:?\s*([A-Z0-9\-]+)'
    ]
    
    for pattern in case_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        analysis["case_numbers"].extend(matches)
    
    # Extract dates
    date_patterns = [
        r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        analysis["dates"].extend(matches)
    
    return analysis

# Simple text splitter
def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into chunks."""
    chunks = []
    for i in range(0, len(text), chunk_size - chunk_overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    return chunks

# Simple vector search (without embeddings for now)
def search_chunks(chunks: List[str], query: str, k: int = 3) -> List[str]:
    """Simple keyword-based search."""
    query_lower = query.lower()
    scored_chunks = []
    
    for chunk in chunks:
        score = 0
        chunk_lower = chunk.lower()
        # Simple keyword matching
        for word in query_lower.split():
            if word in chunk_lower:
                score += 1
        scored_chunks.append((chunk, score))
    
    # Sort by score and return top k
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score in scored_chunks[:k] if score > 0]

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Document Upload endpoint (PDFs and Images)
@app.post("/api/upload-document")
async def upload_document(file: UploadFile = File(...), api_key: str = Form(...)):
    """Upload and process legal documents (PDFs and Images) for discovery analysis."""
    global vector_db, chat_model, uploaded_documents, document_metadata
    
    try:
        # Validate file type
        file_extension = file.filename.lower().split('.')[-1]
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (10MB limit for images, 4MB for PDFs)
        MAX_FILE_SIZE = 10 * 1024 * 1024 if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'] else 4 * 1024 * 1024
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB. Your file is {len(file_content) / (1024*1024):.1f}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Create temporary file
        temp_suffix = f'.{file_extension}'
        with tempfile.NamedTemporaryFile(delete=False, suffix=temp_suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_file_path = tmp_file.name
        
        # Set API key
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Process document based on type
        if file_extension == 'pdf':
            # Process PDF
            pdf_pages = load_pdf_text(temp_file_path)
            full_text = "\n".join(pdf_pages)
            document_type = "pdf"
            analysis = analyze_legal_document(full_text, "pdf")
        else:
            # Process Image
            image_data = process_image(temp_file_path, api_key)
            full_text = image_data["text_content"]
            document_type = "image"
            analysis = analyze_legal_document(full_text, "image")
        
        # Split text into chunks
        chunks = split_text(full_text)
        
        # Create document ID
        import uuid
        doc_id = str(uuid.uuid4())
        
        # Store document data
        document_data = {
            "id": doc_id,
            "filename": file.filename,
            "type": document_type,
            "content": full_text,
            "chunks": chunks,
            "analysis": analysis,
            "upload_time": str(os.path.getctime(temp_file_path))
        }
        
        uploaded_documents.append(document_data)
        document_metadata[doc_id] = document_data
        
        # Update global search index
        all_chunks = []
        for doc in uploaded_documents:
            all_chunks.extend(doc["chunks"])
        vector_db = all_chunks
        
        # Initialize chat model
        chat_model = OpenAI()
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return {
            "message": f"Document '{file.filename}' uploaded and processed successfully. {len(chunks)} chunks created.",
            "success": True,
            "document_name": file.filename,
            "document_type": document_type,
            "document_id": doc_id,
            "analysis": analysis
        }
        
    except Exception as e:
        # Clean up temporary file on error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

# Legacy PDF endpoint for backward compatibility
@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), api_key: str = Form(...)):
    """Legacy PDF upload endpoint for backward compatibility."""
    return await upload_document(file, api_key)

# Legal Analysis endpoint
@app.post("/api/legal-analysis")
async def legal_analysis(request: LegalAnalysisRequest):
    """Perform specialized legal analysis on uploaded documents."""
    global vector_db, chat_model, uploaded_documents
    
    if vector_db is None or chat_model is None:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload documents first.")
    
    try:
        # Set API key
        os.environ["OPENAI_API_KEY"] = request.api_key
        
        # Search for relevant chunks
        relevant_chunks = search_chunks(vector_db, request.user_message, k=5)
        
        # Create context from relevant chunks
        context = "\n\n".join(relevant_chunks)
        
        # Get document metadata for citations
        doc_citations = []
        for doc in uploaded_documents:
            if any(chunk in doc["chunks"] for chunk in relevant_chunks):
                doc_citations.append({
                    "filename": doc["filename"],
                    "type": doc["type"],
                    "case_numbers": doc["analysis"].get("case_numbers", []),
                    "dates": doc["analysis"].get("dates", [])
                })
        
        # Create specialized legal analysis prompt
        legal_prompt = f"""You are a specialized legal AI assistant helping with discovery document analysis. Analyze the provided legal documents and answer the user's question with a focus on legal implications, evidence identification, and case strategy.

DOCUMENT CONTEXT:
{context}

DOCUMENT CITATIONS:
{chr(10).join([f"- {doc['filename']} ({doc['type']}) - Case Numbers: {doc['case_numbers']} - Dates: {doc['dates']}" for doc in doc_citations])}

ANALYSIS TYPE: {request.analysis_type}

INSTRUCTIONS:
- Provide detailed legal analysis based on the document context
- Identify key evidence, relationships, and inconsistencies
- Cite specific document references when making claims
- Focus on legal strategy and discovery implications
- Highlight potential issues or opportunities for litigation
- Be thorough but concise in your analysis

USER QUESTION: {request.user_message}"""

        # Create messages for chat
        messages = [{"role": "user", "content": legal_prompt}]
        
        # Create an async generator function for streaming responses
        async def generate():
            stream = chat_model.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in legal analysis: {str(e)}")

# RAG Chat endpoint (updated for legal context)
@app.post("/api/rag-chat")
async def rag_chat(request: RAGChatRequest):
    """Chat with uploaded legal documents using RAG system."""
    global vector_db, chat_model, uploaded_documents
    
    if vector_db is None or chat_model is None:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload documents first.")
    
    try:
        # Set API key
        os.environ["OPENAI_API_KEY"] = request.api_key
        
        # Search for relevant chunks
        relevant_chunks = search_chunks(vector_db, request.user_message, k=3)
        
        # Create context from relevant chunks
        context = "\n\n".join(relevant_chunks)
        
        # Create legal-focused RAG prompt
        rag_prompt = f"""You are a legal AI assistant specialized in discovery document analysis. Answer questions based on the provided legal document context.

DOCUMENT CONTEXT:
{context}

INSTRUCTIONS:
- Answer the user's question using ONLY the information provided in the context above
- Focus on legal implications, evidence identification, and case strategy
- If the answer is not available in the context, clearly state "I cannot find the answer to your question in the provided documents"
- Be specific and cite relevant parts of the context when possible
- Provide legal analysis and strategic insights where appropriate

USER QUESTION: {request.user_message}"""

        # Create messages for chat
        messages = [{"role": "user", "content": rag_prompt}]
        
        # Create an async generator function for streaming responses
        async def generate():
            stream = chat_model.chat.completions.create(
                model=request.model,
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in RAG chat: {str(e)}")

# Get document status endpoint
@app.get("/api/document-status")
async def get_document_status():
    """Check if documents are currently loaded and ready for analysis."""
    global vector_db, uploaded_documents
    
    if vector_db is None or len(uploaded_documents) == 0:
        return {
            "has_documents": False, 
            "message": "No documents uploaded",
            "document_count": 0
        }
    
    return {
        "has_documents": True, 
        "message": f"{len(uploaded_documents)} document(s) ready for analysis",
        "document_count": len(uploaded_documents),
        "documents": [
            {
                "id": doc["id"],
                "filename": doc["filename"],
                "type": doc["type"],
                "case_numbers": doc["analysis"].get("case_numbers", []),
                "dates": doc["analysis"].get("dates", [])
            }
            for doc in uploaded_documents
        ]
    }

# Legacy PDF status endpoint for backward compatibility
@app.get("/api/pdf-status")
async def get_pdf_status():
    """Legacy PDF status endpoint for backward compatibility."""
    return await get_document_status()

# Get document details endpoint
@app.get("/api/document/{document_id}")
async def get_document_details(document_id: str):
    """Get detailed information about a specific document."""
    global document_metadata
    
    if document_id not in document_metadata:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = document_metadata[document_id]
    return {
        "id": doc["id"],
        "filename": doc["filename"],
        "type": doc["type"],
        "analysis": doc["analysis"],
        "upload_time": doc["upload_time"],
        "chunk_count": len(doc["chunks"])
    }

# List all documents endpoint
@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents with basic information."""
    global uploaded_documents
    
    return {
        "documents": [
            {
                "id": doc["id"],
                "filename": doc["filename"],
                "type": doc["type"],
                "case_numbers": doc["analysis"].get("case_numbers", []),
                "dates": doc["analysis"].get("dates", []),
                "upload_time": doc["upload_time"]
            }
            for doc in uploaded_documents
        ],
        "total_count": len(uploaded_documents)
    }

# Original chat endpoint for compatibility
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        client = OpenAI(api_key=request.api_key)
        
        async def generate():
            stream = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "developer", "content": request.developer_message},
                    {"role": "user", "content": request.user_message}
                ],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
