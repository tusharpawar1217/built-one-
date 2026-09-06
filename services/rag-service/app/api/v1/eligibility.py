"""Eligibility checking endpoints."""
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional

from app.models.schemas import EligibilityInfo
from app.services.eligibility_extractor import EligibilityExtractor
from app.services.pdf_processor import PDFProcessor
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/extract", response_model=EligibilityInfo)
async def extract_eligibility(
    request: Request,
    document_id: str = Query(...),
    user_id: str = Query(...)
):
    """
    Extract eligibility information from a notification PDF.
    
    Args:
        document_id: Document ID to extract from
        user_id: User making the request
    
    Returns:
        Structured eligibility information
    """
    try:
        # Get document path
        from app.config import get_settings
        settings = get_settings()
        
        file_path = Path(settings.upload_dir) / f"{document_id}.pdf"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract text from PDF
        pdf_processor = PDFProcessor()
        pages_data, _ = pdf_processor.process_pdf(file_path)
        
        # Combine all pages
        full_text = "\n\n".join([page["text"] for page in pages_data])
        
        if not full_text.strip():
            raise HTTPException(status_code=422, detail="No text found in document")
        
        # Extract eligibility
        extractor = EligibilityExtractor()
        eligibility_info = await extractor.extract_from_text(full_text)
        
        logger.info(f"Extracted eligibility for document {document_id}")
        return eligibility_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Eligibility extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/check")
async def check_eligibility(
    request: Request,
    document_id: str = Query(...),
    user_id: str = Query(...),
    user_age: Optional[int] = Query(None),
    user_qualification: Optional[str] = Query(None),
    user_category: Optional[str] = Query(None)
):
    """
    Check if user meets eligibility criteria.
    
    Args:
        document_id: Notification document
        user_id: User making request
        user_age: User's age
        user_qualification: User's qualification
        user_category: User's category (General/OBC/SC/ST)
    
    Returns:
        Eligibility check result
    """
    try:
        # First extract eligibility info
        eligibility_info = await extract_eligibility(request, document_id, user_id)
        
        # Build user profile
        user_profile = {
            "age": user_age,
            "qualification": user_qualification,
            "category": user_category or "General"
        }
        
        # Check eligibility
        extractor = EligibilityExtractor()
        result = extractor.check_eligibility(eligibility_info, user_profile)
        
        return result
        
    except Exception as e:
        logger.error(f"Eligibility check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
