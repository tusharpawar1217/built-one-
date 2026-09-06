"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import get_settings
from app.api.v1 import documents, query, health
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService

# Configure logging
logging.basicConfig(
    level=get_settings().log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting Sarkari AI RAG Service...")
    
    # Initialize services (load models into memory)
    logger.info("Loading embedding model...")
    embedding_service = EmbeddingService()
    await embedding_service.initialize()
    app.state.embedding_service = embedding_service
    
    logger.info("Initializing vector store...")
    vector_store = VectorStoreService()
    await vector_store.initialize()
    app.state.vector_store = vector_store
    
    logger.info("Service ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await vector_store.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=get_settings().app_name,
    version=get_settings().api_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(query.router, prefix="/api/v1/query", tags=["query"])

# Import usage, eligibility, quiz, and tests routers
from app.api.v1 import usage, eligibility, quiz, tests
app.include_router(usage.router, prefix="/api/v1/usage", tags=["usage"])
app.include_router(eligibility.router, prefix="/api/v1/eligibility", tags=["eligibility"])
app.include_router(quiz.router, prefix="/api/v1/quiz", tags=["quiz"])
app.include_router(tests.router, prefix="/api/v1/tests", tags=["tests"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": get_settings().app_name,
        "version": get_settings().api_version,
        "status": "healthy"
    }
