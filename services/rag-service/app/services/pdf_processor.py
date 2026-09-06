"""PDF processing with native text extraction and advanced OCR fallback."""
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import fitz  # PyMuPDF
from PIL import Image
import io
import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PDFProcessor:
    """Handle PDF text extraction with smart OCR fallback using ChandraOCR ensemble."""
    
    def __init__(self):
        """Initialize PDF processor with OCR engines."""
        self.settings = settings
        self.ocr_engine = None
        
        # Initialize ChandraOCR ensemble
        try:
            from app.services.chandra_ocr import ChandraOCR
            self.ocr_engine = ChandraOCR()
            logger.info("ChandraOCR ensemble initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize ChandraOCR: {e}. OCR will be disabled.")
    
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
        """Extract text using advanced OCR ensemble (PaddleOCR + EasyOCR)."""
        if not self.ocr_engine:
            logger.warning("OCR engine not available")
            return ""
        
        try:
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Use ChandraOCR ensemble
            ocr_text = self.ocr_engine.extract_text(img, languages=self.settings.ocr_languages)
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
    Advanced OCR ensemble combining PaddleOCR (primary) + EasyOCR (fallback).
    Optimized for Indic scripts (Hindi, Marathi) and scanned government documents.
    """
    
    def __init__(self):
        """Initialize OCR engines with priority order."""
        self.paddle_ocr = None
        self.easy_ocr = None
        self.engines_available = []
        
        # Try to initialize PaddleOCR (best for Indic scripts)
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang='en',  # Default, will be overridden per call
                show_log=False,
                use_gpu=False  # Set to True if GPU available
            )
            self.engines_available.append('paddle')
            logger.info("✅ PaddleOCR initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ PaddleOCR not available: {e}")
        
        # Try to initialize EasyOCR (fallback)
        try:
            import easyocr
            # Initialize with English + Hindi + Marathi
            self.easy_ocr = easyocr.Reader(
                ['en', 'hi', 'mr'],
                gpu=False,  # Set to True if GPU available
                verbose=False
            )
            self.engines_available.append('easy')
            logger.info("✅ EasyOCR initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ EasyOCR not available: {e}")
        
        if not self.engines_available:
            logger.error("❌ No OCR engines available! Install PaddleOCR or EasyOCR")
        else:
            logger.info(f"📚 Available OCR engines: {', '.join(self.engines_available)}")
    
    def extract_with_paddle(self, image: Image.Image, languages: str) -> str:
        """Extract text using PaddleOCR (best quality for Indic scripts)."""
        if not self.paddle_ocr:
            return ""
        
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Map language codes (paddleocr uses different codes)
            lang_map = {
                'eng': 'en',
                'hin': 'hi',
                'mar': 'mr',
                'eng+hin+mar': 'en'  # PaddleOCR handles multilingual well in 'en' mode
            }
            paddle_lang = lang_map.get(languages.replace('+', ''), 'en')
            
            # Reinitialize with correct language if needed
            if paddle_lang != 'en':
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=paddle_lang,
                    show_log=False,
                    use_gpu=False
                )
            
            # Run OCR
            result = self.paddle_ocr.ocr(img_array, cls=True)
            
            # Extract text from results
            if result and result[0]:
                texts = [line[1][0] for line in result[0]]
                extracted_text = '\n'.join(texts)
                return extracted_text
            
            return ""
        
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            return ""
    
    def extract_with_easy(self, image: Image.Image) -> str:
        """Extract text using EasyOCR (fallback option)."""
        if not self.easy_ocr:
            return ""
        
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Run OCR
            results = self.easy_ocr.readtext(img_array)
            
            # Extract text from results
            if results:
                texts = [detection[1] for detection in results]
                extracted_text = '\n'.join(texts)
                return extracted_text
            
            return ""
        
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return ""
    
    def extract_text(self, image: Image.Image, languages: str = "eng+hin+mar") -> str:
        """
        Extract text using best available OCR engine.
        Tries PaddleOCR first (best quality), falls back to EasyOCR.
        
        Args:
            image: PIL Image object
            languages: Language codes (e.g., "eng+hin+mar")
        
        Returns:
            Extracted text string
        """
        # Try PaddleOCR first (best for Indic scripts)
        if 'paddle' in self.engines_available:
            logger.debug("Using PaddleOCR (primary)")
            text = self.extract_with_paddle(image, languages)
            if text and len(text.strip()) > 20:  # Reasonable text extracted
                return text
            logger.debug("PaddleOCR returned insufficient text, trying EasyOCR")
        
        # Fallback to EasyOCR
        if 'easy' in self.engines_available:
            logger.debug("Using EasyOCR (fallback)")
            text = self.extract_with_easy(image)
            if text:
                return text
        
        logger.warning("All OCR engines failed or unavailable")
        return ""
    
    def is_available(self) -> bool:
        """Check if at least one OCR engine is available."""
        return len(self.engines_available) > 0
