"""Health check endpoint."""
from datetime import datetime
from fastapi import APIRouter, Request
from app.models.schemas import HealthCheck
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthCheck)
async def health_check(request: Request):
    """Check service health and dependencies."""
    services_status = {
        "embedding_service": "unknown",
        "vector_store": "unknown",
        "redis": "unknown",
        "qdrant": "unknown"
    }
    
    # Check embedding service
    if hasattr(request.app.state, "embedding_service"):
        services_status["embedding_service"] = "healthy"
    
    # Check vector store
    if hasattr(request.app.state, "vector_store"):
        services_status["vector_store"] = "healthy"
    
    # TODO: Add actual health checks for Redis and Qdrant
    
    return HealthCheck(
        status="healthy",
        version=settings.api_version,
        services=services_status,
        timestamp=datetime.utcnow()
    )
