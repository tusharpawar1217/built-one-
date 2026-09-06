"""Document upload and management endpoints."""
import logging
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import DocumentUploadResponse, DocumentStatus, DocumentInfo, UserTier
from app.services.pdf_processor import PDFProcessor
from app.services.chunker import SemanticChunker
from app.services.rate_limiter import RateLimiter
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    user_tier: str = Form(default="free"),
):
    """
    Upload and process a PDF document with rate limiting.
    
    Flow:
    1. Check page processing limits
    2. Save uploaded file
    3. Extract text (native + OCR fallback)
    4. Chunk text semantically
    5. Generate embeddings
    6. Store in vector database
    7. Track page usage
    """
    # Initialize rate limiter
    if not hasattr(request.app.state, "rate_limiter"):
        rate_limiter = RateLimiter()
        await rate_limiter.initialize()
        request.app.state.rate_limiter = rate_limiter
    else:
        rate_limiter = request.app.state.rate_limiter
    
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.max_upload_size_mb}MB limit"
        )
    
    # Generate document ID
    document_id = str(uuid.uuid4())
    
    # Save file temporarily
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / f"{document_id}.pdf"
    
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"File saved: {file_path}")
        
        # Process PDF
        pdf_processor = PDFProcessor()
        pages_data, processing_stats = pdf_processor.process_pdf(file_path)
        
        if not pages_data:
            raise HTTPException(status_code=422, detail="No text could be extracted from PDF")
        
        # Check page limit before processing
        tier = UserTier.PREMIUM if user_tier.lower() == "premium" else UserTier.FREE
        allowed, current, limit = await rate_limiter.check_page_limit(
            user_id, tier, processing_stats["total_pages"]
        )
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Page limit exceeded. Used: {current}/{limit} pages this month"
            )
        
        # Chunk document
        chunker = SemanticChunker()
        chunks = chunker.chunk_with_metadata(
            pages_data=pages_data,
            document_id=document_id,
            user_id=user_id,
            source_filename=file.filename
        )
        
        logger.info(f"Document chunked into {len(chunks)} chunks")
        
        # Generate embeddings
        embedding_service = request.app.state.embedding_service
        texts = [chunk.content for chunk in chunks]
        embeddings = await embedding_service.embed_batch(texts)
        
        # Attach embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Store in vector database
        vector_store = request.app.state.vector_store
        await vector_store.upsert_chunks(chunks)
        
        # Track page usage
        await rate_limiter.increment_page_count(user_id, processing_stats["total_pages"])
        
        # TODO: Save document metadata to PostgreSQL
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status=DocumentStatus.COMPLETED,
            total_pages=processing_stats["total_pages"],
            message=f"Successfully processed {len(chunks)} chunks from {processing_stats['total_pages']} pages"
        )
    
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        # Clean up file
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    request: Request,
    document_id: str,
    user_id: str
):
    """Delete a document and all its chunks."""
    try:
        vector_store = request.app.state.vector_store
        await vector_store.delete_document(user_id, document_id)
        
        # Delete file
        file_path = Path(settings.upload_dir) / f"{document_id}.pdf"
        if file_path.exists():
            file_path.unlink()
        
        return {"message": "Document deleted successfully", "document_id": document_id}
    
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/info")
async def get_document_info(
    request: Request,
    document_id: str,
    user_id: str
):
    """Get document information."""
    try:
        vector_store = request.app.state.vector_store
        chunk_count = await vector_store.get_document_count(user_id, document_id)
        
        # TODO: Get full metadata from PostgreSQL
        
        return {
            "document_id": document_id,
            "chunk_count": chunk_count,
            "user_id": user_id
        }
    
    except Exception as e:
        logger.error(f"Failed to get document info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
