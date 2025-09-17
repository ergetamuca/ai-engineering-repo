# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
# Import Pydantic for data validation and settings management
from pydantic import BaseModel
# Import OpenAI client for interacting with OpenAI's API
from openai import OpenAI
import os
import tempfile
import shutil
from typing import Optional, List
from pathlib import Path

# Import aimakerspace components for RAG functionality
import sys
sys.path.append('/Users/ergetamuca/Desktop/ai-engineering-repo')
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.openai_utils.embedding import EmbeddingModel

# Initialize FastAPI application with a title
app = FastAPI(title="PDF RAG Chat API")

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the API to be accessed from different domains/origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers in requests
)

# Global variables for RAG system
vector_db: Optional[VectorDatabase] = None
chat_model: Optional[ChatOpenAI] = None
uploaded_pdf_path: Optional[str] = None

# Define the data model for chat requests using Pydantic
# This ensures incoming request data is properly validated
class ChatRequest(BaseModel):
    developer_message: str  # Message from the developer/system
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4o-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication

class RAGChatRequest(BaseModel):
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4o-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication

class UploadResponse(BaseModel):
    message: str
    success: bool
    pdf_name: Optional[str] = None

# Define the main chat endpoint that handles POST requests
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Initialize OpenAI client with the provided API key
        client = OpenAI(api_key=request.api_key)
        
        # Create an async generator function for streaming responses
        async def generate():
            # Create a streaming chat completion request
            stream = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "developer", "content": request.developer_message},
                    {"role": "user", "content": request.user_message}
                ],
                stream=True  # Enable streaming response
            )
            
            # Yield each chunk of the response as it becomes available
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        # Handle any errors that occur during processing
        raise HTTPException(status_code=500, detail=str(e))

# PDF Upload endpoint
@app.post("/api/upload-pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), api_key: str = Form(...)):
    """Upload and process a PDF file for RAG system."""
    global vector_db, chat_model, uploaded_pdf_path
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            uploaded_pdf_path = tmp_file.name
        
        # Initialize embedding model with API key
        os.environ["OPENAI_API_KEY"] = api_key
        embedding_model = EmbeddingModel()
        
        # Load and process PDF
        pdf_loader = PDFLoader(uploaded_pdf_path)
        pdf_loader.load_file()
        
        # Split text into chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_texts(pdf_loader.documents)
        
        # Create vector database
        vector_db = VectorDatabase(embedding_model)
        await vector_db.abuild_from_list(chunks)
        
        # Initialize chat model
        chat_model = ChatOpenAI(model_name="gpt-4o-mini")
        
        return UploadResponse(
            message=f"PDF '{file.filename}' uploaded and processed successfully. {len(chunks)} chunks created.",
            success=True,
            pdf_name=file.filename
        )
        
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

# Define a health check endpoint to verify API status
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
