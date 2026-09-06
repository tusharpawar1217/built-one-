"""Reranking service using BGE-Reranker."""
import logging
from typing import List, Dict
from FlagEmbedding import FlagReranker

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RerankerService:
    """
    Rerank retrieved chunks using cross-encoder model.
    Improves precision by scoring query-document pairs.
    """
    
    def __init__(self):
        """Initialize reranker."""
        self.settings = settings
        self.model = None
    
    def initialize(self):
        """Load reranker model."""
        if not self.settings.enable_reranker:
            logger.info("Reranker disabled")
            return
        
        logger.info(f"Loading reranker model: {self.settings.reranker_model}")
        self.model = FlagReranker(
            self.settings.reranker_model,
            use_fp16=True  # Use mixed precision for speed
        )
        logger.info("Reranker loaded successfully")
    
    def rerank(
        self,
        query: str,
        search_results: List[Dict],
        top_k: int = None
    ) -> List[Dict]:
        """
        Rerank search results based on query relevance.
        
        Args:
            query: User query
            search_results: List of search results with 'content' field
            top_k: Number of top results to return (default: from settings)
        
        Returns:
            Reranked and filtered results
        """
        if not self.settings.enable_reranker or self.model is None:
            # Return original results if reranker disabled
            return search_results[:top_k or self.settings.top_k_rerank]
        
        if not search_results:
            return []
        
        top_k = top_k or self.settings.top_k_rerank
        
        # Prepare query-document pairs
        pairs = [[query, result["content"]] for result in search_results]
        
        # Compute reranking scores
        try:
            scores = self.model.compute_score(pairs, normalize=True)
            
            # Handle single result case (returns float instead of list)
            if isinstance(scores, float):
                scores = [scores]
            
            # Attach scores to results
            for result, score in zip(search_results, scores):
                result["rerank_score"] = float(score)
            
            # Sort by rerank score
            reranked = sorted(
                search_results,
                key=lambda x: x["rerank_score"],
                reverse=True
            )
            
            logger.info(f"Reranked {len(search_results)} results, returning top {top_k}")
            return reranked[:top_k]
        
        except Exception as e:
            logger.error(f"Reranking failed: {e}, returning original results")
            return search_results[:top_k]


class HybridRetriever:
    """
    Hybrid retrieval combining dense (vector) and sparse (BM25) search.
    Uses Reciprocal Rank Fusion (RRF) for result merging.
    """
    
    def __init__(self):
        """Initialize hybrid retriever."""
        # TODO: Implement BM25 sparse retrieval
        # For MVP, we use only dense retrieval
        # Phase 2 can add BM25 index
        pass
    
    def rrf_fusion(
        self,
        dense_results: List[Dict],
        sparse_results: List[Dict],
        k: int = 60
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion to combine dense and sparse results.
        
        RRF formula: score(d) = sum(1 / (k + rank(d)))
        """
        scores = {}
        
        # Score dense results
        for rank, result in enumerate(dense_results, start=1):
            doc_id = result["chunk_id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
            if doc_id not in scores:
                scores[doc_id] = {"result": result, "score": 0}
        
        # Score sparse results (when implemented)
        for rank, result in enumerate(sparse_results, start=1):
            doc_id = result["chunk_id"]
            if doc_id in scores:
                scores[doc_id] += 1 / (k + rank)
            else:
                scores[doc_id] = 1 / (k + rank)
        
        # Sort by fusion score
        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [item[1]["result"] for item in fused if "result" in item[1]]
