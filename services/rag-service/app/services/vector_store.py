"""Qdrant vector store service with per-user isolation."""
import logging
from typing import List, Dict, Optional
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams
)

from app.config import get_settings
from app.models.schemas import DocumentChunk, Citation

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStoreService:
    """
    Manage Qdrant vector database operations.
    Uses metadata filtering for per-user document isolation.
    """
    
    def __init__(self):
        """Initialize vector store service."""
        self.settings = settings
        self.client: Optional[AsyncQdrantClient] = None
        self.collection_name = "sarkari_ai_documents"
    
    async def initialize(self):
        """Connect to Qdrant and ensure collection exists."""
        logger.info(f"Connecting to Qdrant at {self.settings.qdrant_url}")
        
        self.client = AsyncQdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key if self.settings.qdrant_api_key else None
        )
        
        # Create collection if it doesn't exist
        await self._ensure_collection()
        logger.info("Qdrant initialized successfully")
    
    async def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.settings.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload indexes for filtering
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="user_id",
                    field_schema="keyword"
                )
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema="keyword"
                )
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="page_number",
                    field_schema="integer"
                )
                
                logger.info(f"Collection {self.collection_name} created with indexes")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
        
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise
    
    async def upsert_chunks(self, chunks: List[DocumentChunk]):
        """
        Insert or update document chunks in vector store.
        
        Args:
            chunks: List of DocumentChunk with embeddings populated
        """
        if not chunks:
            logger.warning("No chunks to upsert")
            return
        
        points = []
        for chunk in chunks:
            if chunk.embedding is None:
                logger.warning(f"Chunk {chunk.chunk_id} has no embedding, skipping")
                continue
            
            point = PointStruct(
                id=chunk.chunk_id,
                vector=chunk.embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "user_id": chunk.metadata.user_id,
                    "document_id": chunk.metadata.document_id,
                    "page_number": chunk.metadata.page_number,
                    "chunk_index": chunk.metadata.chunk_index,
                    "is_ocr": chunk.metadata.is_ocr,
                    "source_filename": chunk.metadata.source_filename
                }
            )
            points.append(point)
        
        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} chunks to Qdrant")
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            raise
    
    async def search(
        self,
        query_embedding: List[float],
        user_id: str,
        document_ids: List[str],
        top_k: int = 20,
        page_filter: Optional[tuple] = None
    ) -> List[Dict]:
        """
        Search for similar chunks with user and document filtering.
        
        Args:
            query_embedding: Query vector
            user_id: Filter by user
            document_ids: Filter by these documents
            top_k: Number of results
            page_filter: Optional (start_page, end_page) tuple
        
        Returns:
            List of search results with scores and metadata
        """
        # Build filter conditions
        must_conditions = [
            FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id)
            ),
            FieldCondition(
                key="document_id",
                match=MatchValue(any=document_ids)
            )
        ]
        
        if page_filter:
            start_page, end_page = page_filter
            must_conditions.append(
                FieldCondition(
                    key="page_number",
                    range={
                        "gte": start_page,
                        "lte": end_page
                    }
                )
            )
        
        query_filter = Filter(must=must_conditions)
        
        try:
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True
            )
            
            # Convert to dict format
            search_results = []
            for result in results:
                search_results.append({
                    "chunk_id": result.payload["chunk_id"],
                    "content": result.payload["content"],
                    "document_id": result.payload["document_id"],
                    "document_name": result.payload["source_filename"],
                    "page_number": result.payload["page_number"],
                    "score": result.score,
                    "is_ocr": result.payload["is_ocr"]
                })
            
            logger.info(f"Found {len(search_results)} results for query")
            return search_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def delete_document(self, user_id: str, document_id: str):
        """Delete all chunks for a document."""
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="document_id", match=MatchValue(value=document_id))
                    ]
                )
            )
            logger.info(f"Deleted document {document_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    async def get_document_count(self, user_id: str, document_id: str) -> int:
        """Count chunks for a document."""
        try:
            result = await self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="document_id", match=MatchValue(value=document_id))
                    ]
                )
            )
            return result.count
        except Exception as e:
            logger.error(f"Failed to count chunks: {e}")
            return 0
    
    async def close(self):
        """Close Qdrant connection."""
        if self.client:
            await self.client.close()
            logger.info("Qdrant connection closed")
