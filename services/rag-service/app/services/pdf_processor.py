"""PDF processing with native text extraction and OCR fallback."""
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PDFProcessor:
    """Handle PDF text extraction with smart OCR fallback."""
    
    def __init__(self):
        """Initialize PDF processor."""
        self.settings = settings
        # Configure tesseract if path provided
        if self.settings.tesseract_cmd != "tesseract":
            pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_cmd
    
    def get_document_hash(self, file_path: Path) -> str:
        """Generate hash for document to enable caching."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def extract_text_native(self, page: fitz.Page) -> str:
        """Extract text using native PDF text layer."""
        try:
            text = page.get_text("text")
            return text.strip()
        except Exception as e:
            logger.warning(f"Native text extraction failed: {e}")
            return ""
    
    def is_page_scanned(self, text: str, threshold: int = 50) -> bool:
        """
        Determine if page is scanned based on extracted text.
        If extracted text is too short or empty, likely scanned.
        """
        return len(text.strip()) < threshold
    
    def extract_text_ocr(self, page: fitz.Page) -> str:
        """Extract text using OCR (for scanned pages)."""
        try:
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Run OCR
            ocr_text = pytesseract.image_to_string(
                img,
                lang=self.settings.ocr_languages,
                config='--psm 6'  # Assume uniform block of text
            )
            return ocr_text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def process_pdf(self, file_path: Path) -> Tuple[List[Dict], Dict]:
        """
        Process PDF and extract text page by page.
        
        Returns:
            Tuple of (pages_data, processing_stats)
            pages_data: List of dicts with {page_num, text, is_ocr}
            processing_stats: Dict with processing metadata
        """
        logger.info(f"Processing PDF: {file_path}")
        
        pages_data = []
        stats = {
            "total_pages": 0,
            "native_pages": 0,
            "ocr_pages": 0,
            "failed_pages": 0,
            "document_hash": self.get_document_hash(file_path)
        }
        
        try:
            doc = fitz.open(file_path)
            stats["total_pages"] = len(doc)
            
            for page_num, page in enumerate(doc, start=1):
                logger.debug(f"Processing page {page_num}/{stats['total_pages']}")
                
                # Try native extraction first
                native_text = self.extract_text_native(page)
                
                # Decide if OCR is needed
                is_scanned = self.is_page_scanned(native_text)
                
                if is_scanned and self.settings.enable_ocr:
                    logger.debug(f"Page {page_num} is scanned, using OCR")
                    text = self.extract_text_ocr(page)
                    is_ocr = True
                    stats["ocr_pages"] += 1
                else:
                    text = native_text
                    is_ocr = False
                    stats["native_pages"] += 1
                
                if text:
                    pages_data.append({
                        "page_number": page_num,
                        "text": text,
                        "is_ocr": is_ocr,
                        "char_count": len(text)
                    })
                else:
                    logger.warning(f"No text extracted from page {page_num}")
                    stats["failed_pages"] += 1
            
            doc.close()
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise
        
        logger.info(f"Processing complete: {stats}")
        return pages_data, stats
    
    def extract_metadata(self, file_path: Path) -> Dict:
        """Extract PDF metadata."""
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            doc.close()
            
            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
            }
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return {}


class ChandraOCR:
    """
    Ensemble OCR pipeline (Tesseract + EasyOCR + PaddleOCR).
    For MVP, we use only Tesseract. Can expand to ensemble later.
    """
    
    def __init__(self):
        """Initialize ensemble OCR."""
        self.tesseract_available = True
        # TODO: Initialize EasyOCR and PaddleOCR when needed
        self.easyocr_available = False
        self.paddleocr_available = False
    
    def extract_with_ensemble(self, image: Image.Image, languages: str) -> str:
        """
        Extract text using ensemble of OCR engines.
        Currently only Tesseract, can add voting/confidence later.
        """
        results = []
        
        # Tesseract
        if self.tesseract_available:
            try:
                text = pytesseract.image_to_string(image, lang=languages)
                results.append(text)
            except Exception as e:
                logger.warning(f"Tesseract OCR failed: {e}")
        
        # TODO: Add EasyOCR and PaddleOCR
        # For now, return Tesseract result
        return results[0] if results else ""
