# Vercel-compatible FastAPI application for PDF RAG system
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import tempfile
import shutil
from typing import Optional, List
from pathlib import Path
import json

# Import pypdf for PDF processing
import pypdf

# Simple implementations to avoid complex imports
class SimpleVectorDatabase:
    def __init__(self, embedding_model=None):
        self.vectors = {}
        self.embedding_model = embedding_model
    
    async def abuild_from_list(self, chunks):
        if self.embedding_model:
            embeddings = await self.embedding_model.async_get_embeddings(chunks)
            for chunk, embedding in zip(chunks, embeddings):
                self.vectors[chunk] = embedding
        return self
    
    def search_by_text(self, query_text, k=3, return_as_text=True):
        if not self.embedding_model:
            return chunks[:k] if return_as_text else [(chunk, 0.5) for chunk in chunks[:k]]
        
        query_embedding = self.embedding_model.get_embedding(query_text)
        # Simple similarity search
        results = []
        for chunk, embedding in self.vectors.items():
            # Simple dot product similarity
            similarity = sum(a * b for a, b in zip(query_embedding, embedding))
            results.append((chunk, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        if return_as_text:
            return [result[0] for result in results[:k]]
        return results[:k]

class SimpleTextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_texts(self, texts):
        chunks = []
        for text in texts:
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk = text[i:i + self.chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
        return chunks

class SimpleChatModel:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model_name = model_name
        self.client = OpenAI()
    
    async def astream(self, messages):
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

class SimpleEmbeddingModel:
    def __init__(self, embeddings_model_name="text-embedding-3-small"):
        self.embeddings_model_name = embeddings_model_name
        self.client = OpenAI()
    
    def get_embedding(self, text):
        embedding = self.client.embeddings.create(
            input=text,
            model=self.embeddings_model_name
        )
        return embedding.data[0].embedding
    
    async def async_get_embeddings(self, texts):
        embeddings = self.client.embeddings.create(
            input=texts,
            model=self.embeddings_model_name
        )
        return [item.embedding for item in embeddings.data]

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

# Initialize FastAPI application
app = FastAPI(title="PDF RAG Chat API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for RAG system (in-memory for serverless)
vector_db: Optional[SimpleVectorDatabase] = None
chat_model: Optional[SimpleChatModel] = None
uploaded_pdf_path: Optional[str] = None

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
    pdf_name: Optional[str] = None

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# PDF Upload endpoint
@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), api_key: str = Form(...)):
    """Upload and process a PDF file for RAG system."""
    global vector_db, chat_model, uploaded_pdf_path
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Check file size (Vercel has a 4.5MB limit for serverless functions)
        MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB limit
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is 4MB. Your file is {len(file_content) / (1024*1024):.1f}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            uploaded_pdf_path = tmp_file.name
        
        # Initialize embedding model with API key
        os.environ["OPENAI_API_KEY"] = api_key
        embedding_model = SimpleEmbeddingModel()
        
        # Load and process PDF
        pdf_pages = load_pdf_text(uploaded_pdf_path)
        
        # Split text into chunks
        text_splitter = SimpleTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_texts(pdf_pages)
        
        # Create vector database
        vector_db = SimpleVectorDatabase(embedding_model)
        await vector_db.abuild_from_list(chunks)
        
        # Initialize chat model
        chat_model = SimpleChatModel(model_name="gpt-4o-mini")
        
        return {
            "message": f"PDF '{file.filename}' uploaded and processed successfully. {len(chunks)} chunks created.",
            "success": True,
            "pdf_name": file.filename
        }
        
    except Exception as e:
        # Clean up temporary file on error
        if uploaded_pdf_path and os.path.exists(uploaded_pdf_path):
            os.unlink(uploaded_pdf_path)
            uploaded_pdf_path = None
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# RAG Chat endpoint
@app.post("/api/rag-chat")
async def rag_chat(request: RAGChatRequest):
    """Chat with the uploaded PDF using RAG system."""
    global vector_db, chat_model
    
    if vector_db is None or chat_model is None:
        raise HTTPException(status_code=400, detail="No PDF uploaded. Please upload a PDF first.")
    
    try:
        # Set API key
        os.environ["OPENAI_API_KEY"] = request.api_key
        
        # Search for relevant chunks
        relevant_chunks = vector_db.search_by_text(request.user_message, k=3, return_as_text=True)
        
        # Create context from relevant chunks
        context = "\n\n".join(relevant_chunks)
        
        # Create RAG prompt
        rag_prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context from a PDF document. 

Context from PDF:
{context}

Instructions:
- Answer the user's question using ONLY the information provided in the context above
- If the answer is not available in the context, clearly state "I cannot find the answer to your question in the provided PDF document"
- Be specific and cite relevant parts of the context when possible
- Keep your response concise and helpful

User Question: {request.user_message}"""

        # Create messages for chat
        messages = [{"role": "user", "content": rag_prompt}]
        
        # Create an async generator function for streaming responses
        async def generate():
            # Get streaming response from chat model
            async for chunk in chat_model.astream(messages):
                yield chunk

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in RAG chat: {str(e)}")

# Get PDF status endpoint
@app.get("/api/pdf-status")
async def get_pdf_status():
    """Check if a PDF is currently loaded and ready for chat."""
    global vector_db, uploaded_pdf_path
    
    if vector_db is None:
        return {"has_pdf": False, "message": "No PDF uploaded"}
    
    return {
        "has_pdf": True, 
        "message": f"PDF ready for chat. File: {os.path.basename(uploaded_pdf_path) if uploaded_pdf_path else 'Unknown'}"
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

# Vercel handler
def handler(request):
    return app(request.scope, request.receive, request.send)
