"""Semantic chunking with structure awareness."""
import logging
import re
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.models.schemas import DocumentChunk, ChunkMetadata

logger = logging.getLogger(__name__)
settings = get_settings()


class SemanticChunker:
    """
    Structure-aware chunking for documents.
    Respects headings, paragraphs, and maintains context.
    """
    
    def __init__(self):
        """Initialize chunker with settings."""
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        
        # Create LangChain splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Multiple newlines (section breaks)
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentences
                ", ",      # Clauses
                " ",       # Words
                ""         # Characters
            ]
        )
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text before chunking."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize common issues from OCR
        text = text.replace('\x00', '')  # Remove null bytes
        text = text.replace('•', '-')    # Normalize bullets
        
        return text.strip()
    
    def detect_headings(self, text: str) -> List[Dict]:
        """
        Detect heading patterns in text.
        Common patterns in government documents and textbooks.
        """
        headings = []
        
        # Pattern 1: ALL CAPS HEADINGS
        caps_pattern = re.compile(r'^([A-Z][A-Z\s]{5,})$', re.MULTILINE)
        for match in caps_pattern.finditer(text):
            headings.append({
                "text": match.group(1),
                "start": match.start(),
                "type": "caps"
            })
        
        # Pattern 2: Numbered sections (1., 1.1, etc.)
        number_pattern = re.compile(r'^(\d+\.(\d+\.)*)\s+([A-Z].*?)$', re.MULTILINE)
        for match in number_pattern.finditer(text):
            headings.append({
                "text": match.group(0),
                "start": match.start(),
                "type": "numbered"
            })
        
        return headings
    
    def chunk_with_metadata(
        self,
        pages_data: List[Dict],
        document_id: str,
        user_id: str,
        source_filename: str
    ) -> List[DocumentChunk]:
        """
        Chunk document pages with rich metadata.
        
        Args:
            pages_data: List of {page_number, text, is_ocr}
            document_id: Unique document identifier
            user_id: User who owns the document
            source_filename: Original filename
        
        Returns:
            List of DocumentChunk objects with embeddings placeholder
        """
        all_chunks = []
        
        for page_info in pages_data:
            page_num = page_info["page_number"]
            text = page_info["text"]
            is_ocr = page_info["is_ocr"]
            
            # Preprocess
            cleaned_text = self.preprocess_text(text)
            
            if not cleaned_text:
                logger.warning(f"Empty text after preprocessing for page {page_num}")
                continue
            
            # Split into chunks
            chunks = self.splitter.split_text(cleaned_text)
            
            logger.debug(f"Page {page_num} split into {len(chunks)} chunks")
            
            # Create DocumentChunk objects with metadata
            for chunk_idx, chunk_text in enumerate(chunks):
                chunk_id = f"{document_id}_p{page_num}_c{chunk_idx}"
                
                metadata = ChunkMetadata(
                    document_id=document_id,
                    user_id=user_id,
                    page_number=page_num,
                    chunk_index=chunk_idx,
                    total_chunks=len(chunks),
                    is_ocr=is_ocr,
                    source_filename=source_filename
                )
                
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    metadata=metadata,
                    embedding=None  # Will be populated by embedding service
                )
                
                all_chunks.append(chunk)
        
        logger.info(f"Document {document_id} chunked into {len(all_chunks)} total chunks")
        return all_chunks
    
    def chunk_for_summary(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """
        Chunk text for summarization tasks.
        Uses larger chunks than retrieval.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=200,
            length_function=len
        )
        return splitter.split_text(text)
    
    def get_chapter_chunks(
        self,
        chunks: List[DocumentChunk],
        chapter_name: str = None,
        page_range: tuple = None
    ) -> List[DocumentChunk]:
        """
        Filter chunks by chapter name or page range.
        Useful for multi-page synthesis queries.
        """
        filtered = chunks
        
        if page_range:
            start_page, end_page = page_range
            filtered = [
                c for c in filtered
                if start_page <= c.metadata.page_number <= end_page
            ]
        
        if chapter_name:
            # Simple keyword matching in content
            # In production, maintain a separate chapter index
            filtered = [
                c for c in filtered
                if chapter_name.lower() in c.content.lower()
            ]
        
        return filtered
