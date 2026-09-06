"""Query processing endpoints."""
import logging
import time
from fastapi import APIRouter, Request, HTTPException

from app.models.schemas import QueryRequest, QueryResponse, QueryType, UserTier
from app.services.agent_graph import QueryAgent
from app.services.reranker import RerankerService
from app.services.llm_service import LLMService
from app.services.rate_limiter import RateLimiter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=QueryResponse)
async def process_query(
    request: Request,
    query_request: QueryRequest
):
    """
    Process a user query against their documents with rate limiting.
    
    Flow:
    1. Check rate limits
    2. Run query through LangGraph agent
    3. Track usage
    4. Return answer with citations
    """
    start_time = time.time()
    
    # Initialize rate limiter
    if not hasattr(request.app.state, "rate_limiter"):
        rate_limiter = RateLimiter()
        await rate_limiter.initialize()
        request.app.state.rate_limiter = rate_limiter
    else:
        rate_limiter = request.app.state.rate_limiter
    
    # Check query limit
    allowed, current, limit = await rate_limiter.check_query_limit(
        query_request.user_id,
        query_request.user_tier
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Query limit exceeded. Used: {current}/{limit} queries today. Upgrade to Premium for unlimited queries."
        )
    
    try:
        # Get services from app state
        embedding_service = request.app.state.embedding_service
        vector_store = request.app.state.vector_store
        
        # Initialize reranker (lazy load)
        if not hasattr(request.app.state, "reranker_service"):
            reranker_service = RerankerService()
            reranker_service.initialize()
            request.app.state.reranker_service = reranker_service
        else:
            reranker_service = request.app.state.reranker_service
        
        # Initialize LLM service (lazy load)
        if not hasattr(request.app.state, "llm_service"):
            llm_service = LLMService()
            request.app.state.llm_service = llm_service
        else:
            llm_service = request.app.state.llm_service
        
        # Initialize agent
        agent = QueryAgent(
            embedding_service=embedding_service,
            vector_store=vector_store,
            reranker_service=reranker_service,
            llm_service=llm_service
        )
        
        # Process query
        logger.info(f"Processing query for user {query_request.user_id}")
        
        result = await agent.process_query(
            query=query_request.query,
            user_id=query_request.user_id,
            document_ids=query_request.document_ids,
            conversation_history=query_request.conversation_history
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Increment query count (after successful processing)
        await rate_limiter.increment_query_count(query_request.user_id)
        
        # Get updated usage stats
        usage_stats = await rate_limiter.get_usage_stats(
            query_request.user_id,
            query_request.user_tier
        )
        
        # Construct response
        response = QueryResponse(
            answer=result["answer"],
            query_type=QueryType(result["query_type"]),
            citations=result["citations"],
            model_used=result["model_used"],
            processing_time_ms=processing_time,
            usage_info={
                "user_tier": query_request.user_tier,
                "documents_searched": len(query_request.document_ids),
                "chunks_retrieved": len(result["retrieved_chunks"]),
                "chunks_used": len(result["reranked_chunks"]),
                "processing_steps": result["processing_steps"],
                "rate_limit": usage_stats
            }
        )
        
        logger.info(f"Query processed in {processing_time:.2f}ms")
        return response
    
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.post("/stream")
async def process_query_stream(
    request: Request,
    query_request: QueryRequest
):
    """
    Stream query response (for future enhancement).
    Placeholder for streaming responses in Phase 2.
    """
    # TODO: Implement streaming with Server-Sent Events
    raise HTTPException(status_code=501, detail="Streaming not yet implemented")
