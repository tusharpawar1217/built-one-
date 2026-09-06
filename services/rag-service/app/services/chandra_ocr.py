"""
ChandraOCR - Advanced OCR ensemble for Indic scripts.

Combines multiple OCR engines with intelligent fallback:
1. PaddleOCR (Primary) - Best for Hindi/Marathi/multilingual
2. EasyOCR (Fallback) - Good general-purpose OCR
3. Confidence-based selection

Optimized for Indian government documents with scanned Indic text.
"""
import logging
import numpy as np
from PIL import Image
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class ChandraOCR:
    """
    Advanced OCR ensemble for Indic scripts.
    
    Priority order:
    1. PaddleOCR - Excellent for Hindi/Marathi, fast, accurate
    2. EasyOCR - Good fallback, supports 80+ languages
    
    Features:
    - Automatic language detection
    - Multi-script support (Devanagari, Latin)
    - Angle correction
    - Confidence scoring
    """
    
    def __init__(self):
        """Initialize OCR engines."""
        self.paddle_ocr = None
        self.easy_ocr = None
        self.engines = []
        
        self._init_paddle_ocr()
        self._init_easy_ocr()
        
        if not self.engines:
            logger.error("❌ No OCR engines initialized! Please install PaddleOCR or EasyOCR")
        else:
            logger.info(f"✅ ChandraOCR ready with: {', '.join(self.engines)}")
    
    def _init_paddle_ocr(self):
        """Initialize PaddleOCR (primary engine)."""
        try:
            from paddleocr import PaddleOCR
            
            # Initialize with multilingual support
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=True,      # Auto-rotate text
                lang='en',               # Default language
                show_log=False,          # Suppress logs
                use_gpu=False,           # Set True if GPU available
                det_model_dir=None,      # Use default detection model
                rec_model_dir=None,      # Use default recognition model
                use_space_char=True,     # Preserve spaces
            )
            
            self.engines.append('PaddleOCR')
            logger.info("✅ PaddleOCR initialized (Primary engine)")
            
        except ImportError:
            logger.warning("⚠️ PaddleOCR not installed. Install: pip install paddleocr")
        except Exception as e:
            logger.warning(f"⚠️ PaddleOCR initialization failed: {e}")
    
    def _init_easy_ocr(self):
        """Initialize EasyOCR (fallback engine)."""
        try:
            import easyocr
            
            # Initialize with English + Hindi + Marathi
            self.easy_ocr = easyocr.Reader(
                ['en', 'hi', 'mr'],      # English, Hindi, Marathi
                gpu=False,               # Set True if GPU available
                verbose=False,
                download_enabled=True
            )
            
            self.engines.append('EasyOCR')
            logger.info("✅ EasyOCR initialized (Fallback engine)")
            
        except ImportError:
            logger.warning("⚠️ EasyOCR not installed. Install: pip install easyocr")
        except Exception as e:
            logger.warning(f"⚠️ EasyOCR initialization failed: {e}")
    
    def extract_with_paddle(
        self,
        image: Image.Image,
        language: str = 'en'
    ) -> Tuple[str, float]:
        """
        Extract text using PaddleOCR.
        
        Args:
            image: PIL Image
            language: Language code ('en', 'hi', 'mr', etc.)
        
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not self.paddle_ocr:
            return "", 0.0
        
        try:
            # Convert PIL to numpy
            img_array = np.array(image)
            
            # Run OCR with angle classification
            result = self.paddle_ocr.ocr(img_array, cls=True)
            
            if not result or not result[0]:
                return "", 0.0
            
            # Extract text and confidence
            texts = []
            confidences = []
            
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                texts.append(text)
                confidences.append(confidence)
            
            extracted_text = '\n'.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.debug(f"PaddleOCR: {len(texts)} lines, confidence: {avg_confidence:.2f}")
            return extracted_text, avg_confidence
            
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            return "", 0.0
    
    def extract_with_easy(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text using EasyOCR.
        
        Args:
            image: PIL Image
        
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not self.easy_ocr:
            return "", 0.0
        
        try:
            # Convert PIL to numpy
            img_array = np.array(image)
            
            # Run OCR
            results = self.easy_ocr.readtext(img_array)
            
            if not results:
                return "", 0.0
            
            # Extract text and confidence
            texts = []
            confidences = []
            
            for detection in results:
                text = detection[1]
                confidence = detection[2]
                texts.append(text)
                confidences.append(confidence)
            
            extracted_text = '\n'.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.debug(f"EasyOCR: {len(texts)} lines, confidence: {avg_confidence:.2f}")
            return extracted_text, avg_confidence
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return "", 0.0
    
    def extract_text(
        self,
        image: Image.Image,
        languages: str = "eng+hin+mar",
        min_confidence: float = 0.3
    ) -> str:
        """
        Extract text using best available engine with intelligent fallback.
        
        Strategy:
        1. Try PaddleOCR (best for Indic scripts)
        2. If confidence < threshold, try EasyOCR
        3. Return result with highest confidence
        
        Args:
            image: PIL Image
            languages: Language codes (e.g., "eng+hin+mar")
            min_confidence: Minimum confidence threshold
        
        Returns:
            Extracted text string
        """
        results = []
        
        # Try PaddleOCR first (primary)
        if 'PaddleOCR' in self.engines:
            text, confidence = self.extract_with_paddle(image)
            if text and len(text.strip()) > 10:
                results.append(('PaddleOCR', text, confidence))
                logger.debug(f"PaddleOCR: {len(text)} chars, confidence: {confidence:.2f}")
                
                # If confidence is high enough, return immediately
                if confidence >= 0.7:
                    return text
        
        # Try EasyOCR as fallback or if PaddleOCR confidence is low
        if 'EasyOCR' in self.engines:
            text, confidence = self.extract_with_easy(image)
            if text and len(text.strip()) > 10:
                results.append(('EasyOCR', text, confidence))
                logger.debug(f"EasyOCR: {len(text)} chars, confidence: {confidence:.2f}")
        
        # Select best result based on confidence
        if results:
            best_engine, best_text, best_confidence = max(results, key=lambda x: x[2])
            
            if best_confidence >= min_confidence:
                logger.info(f"Selected {best_engine} (confidence: {best_confidence:.2f})")
                return best_text
            else:
                logger.warning(f"Best confidence {best_confidence:.2f} below threshold {min_confidence}")
                return best_text  # Return anyway, better than nothing
        
        logger.warning("All OCR engines failed or returned empty results")
        return ""
    
    def is_available(self) -> bool:
        """Check if at least one OCR engine is available."""
        return len(self.engines) > 0
    
    def get_available_engines(self) -> List[str]:
        """Get list of available OCR engines."""
        return self.engines.copy()
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.
        
        Steps:
        1. Convert to grayscale
        2. Resize if too small
        3. Enhance contrast
        
        Args:
            image: PIL Image
        
        Returns:
            Preprocessed PIL Image
        """
        try:
            from PIL import ImageEnhance, ImageOps
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too small (min width: 800px)
            width, height = image.size
            if width < 800:
                scale = 800 / width
                new_size = (int(width * scale), int(height * scale))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            image = ImageOps.grayscale(image)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Convert back to RGB for OCR engines
            image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return image
