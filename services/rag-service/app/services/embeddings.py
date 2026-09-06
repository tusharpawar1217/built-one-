"""Embedding generation service using BGE-M3."""
import logging
import hashlib
import json
from typing import List, Optional
import redis.asyncio as redis
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """
    Handle embedding generation with caching.
    Uses BGE-M3 for multilingual support (English/Hindi/Marathi).
    """
    
    def __init__(self):
        """Initialize embedding service."""
        self.settings = settings
        self.model: Optional[SentenceTransformer] = None
        self.redis_client: Optional[redis.Redis] = None
        self.cache_enabled = True
    
    async def initialize(self):
        """Load model and connect to Redis cache."""
        logger.info(f"Loading embedding model: {self.settings.embedding_model}")
        self.model = SentenceTransformer(self.settings.embedding_model)
        logger.info(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        
        # Connect to Redis for caching
        try:
            self.redis_client = await redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=False
            )
            await self.redis_client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}. Caching disabled.")
            self.cache_enabled = False
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text hash."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"emb:{self.settings.embedding_model}:{text_hash}"
    
    async def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Retrieve embedding from cache."""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(text)
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def _save_to_cache(self, text: str, embedding: List[float], ttl: int = 86400 * 30):
        """Save embedding to cache with 30-day TTL."""
        if not self.cache_enabled or not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(text)
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(embedding)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text.
        Uses cache to avoid re-computing.
        """
        # Check cache first
        cached = await self._get_from_cache(text)
        if cached is not None:
            logger.debug("Embedding retrieved from cache")
            return cached
        
        # Generate embedding
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()
        
        # Cache for future use
        await self._save_to_cache(text, embedding)
        
        return embedding
    
    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        Checks cache for each text individually.
        """
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        for idx, text in enumerate(texts):
            cached = await self._get_from_cache(text)
            if cached is not None:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(idx)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            logger.info(f"Generating embeddings for {len(uncached_texts)}/{len(texts)} texts")
            
            new_embeddings = self.model.encode(
                uncached_texts,
                normalize_embeddings=True,
                batch_size=batch_size,
                show_progress_bar=len(uncached_texts) > 10
            ).tolist()
            
            # Insert into results and cache
            for idx, embedding in zip(uncached_indices, new_embeddings):
                embeddings[idx] = embedding
                await self._save_to_cache(texts[idx], embedding)
        
        return embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for search query.
        Queries are not cached as they're typically unique.
        """
        return self.model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.model.get_sentence_embedding_dimension()
    
    async def close(self):
        """Cleanup resources."""
        if self.redis_client:
            await self.redis_client.close()
