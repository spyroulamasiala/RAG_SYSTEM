"""
FastAPI application for the Typeform Help Center RAG chatbot.
Provides REST API endpoints for querying the chatbot and managing the knowledge base.
"""
from fastapi import FastAPI, HTTPException, status, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import structlog
import structlog.contextvars
from uuid import uuid4
from contextlib import asynccontextmanager

from config import settings
from vector_store import VectorStore
from rag_engine import RAGEngine
from data_ingestion import load_help_center_articles
from document_processor import DocumentProcessor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Global instances (initialized on startup)
vector_store: Optional[VectorStore] = None
rag_engine: Optional[RAGEngine] = None


def _parse_allowed_origins(raw_origins: str) -> List[str]:
    """Convert comma-separated origins to a list while honoring wildcard."""
    cleaned = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return ["*"] if raw_origins.strip() == "*" or not cleaned else cleaned


def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    """Enforce admin token on mutation endpoints when configured."""
    if settings.admin_token and x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )


# Pydantic models for API
class QueryRequest(BaseModel):
    """Request model for chatbot queries."""
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    top_k: Optional[int] = Field(None, ge=1, le=10, description="Number of documents to retrieve")
    include_sources: bool = Field(True, description="Include source URLs in response")


class QueryResponse(BaseModel):
    """Response model for chatbot queries."""
    answer: str
    query: str
    num_sources: int
    sources: Optional[List[Dict[str, Any]]] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    environment: str
    vector_store_initialized: bool
    rag_engine_initialized: bool


class IndexStatsResponse(BaseModel):
    """Response model for index statistics."""
    total_vectors: int
    dimension: int
    index_fullness: float


# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown."""
    global vector_store, rag_engine
    
    logger.info("Starting application initialization")
    
    try:
        # Initialize vector store
        logger.info("Initializing vector store")
        vector_store = VectorStore()
        vector_store.create_index(dimension=1536)  # text-embedding-3-small dimension
        
        # Initialize RAG engine
        logger.info("Initializing RAG engine")
        rag_engine = RAGEngine(vector_store=vector_store)
        
        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    
    yield
    
    # Cleanup (if needed)
    logger.info("Application shutdown")


# Create FastAPI app
app = FastAPI(
    title="Typeform Help Center Chatbot",
    description="RAG-powered chatbot for answering Typeform Help Center questions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allowed_origins(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request, call_next):
    """Attach a request ID to each response and bind into logs."""
    request_id = str(uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id, path=str(request.url.path))
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Typeform Help Center Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        environment=settings.app_env,
        vector_store_initialized=vector_store is not None,
        rag_engine_initialized=rag_engine is not None
    )


@app.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness probe that also verifies vector store connectivity."""
    if not vector_store or not rag_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services not initialized"
        )

    try:
        vector_store.get_stats()
    except Exception as exc:
        logger.error("Readiness check failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not ready"
        )

    return HealthResponse(
        status="ready",
        environment=settings.app_env,
        vector_store_initialized=True,
        rag_engine_initialized=True
    )


@app.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_chatbot(request: QueryRequest):
    """
    Query the chatbot with a question.
    
    This endpoint performs the complete RAG pipeline:
    1. Embeds the user's question
    2. Retrieves relevant chunks from the vector store
    3. Generates a response using the LLM with retrieved context
    
    Args:
        request: QueryRequest with user question and optional parameters
        
    Returns:
        QueryResponse with generated answer and sources
        
    Raises:
        HTTPException: If RAG engine not initialized or query fails
    """
    if not rag_engine:
        logger.error("RAG engine not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not initialized"
        )
    
    try:
        logger.info("Received query", question=request.question)
        
        # Process query through RAG pipeline
        result = rag_engine.query(
            question=request.question,
            top_k=request.top_k,
            include_sources=request.include_sources
        )
        
        logger.info("Query processed successfully")
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error("Query failed", error=str(e), question=request.question)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@app.post(
    "/index/populate",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)]
)
async def populate_index():
    """
    Populate the vector store with Help Center articles.
    
    This endpoint:
    1. Loads Help Center articles
    2. Chunks and embeds the content
    3. Upserts vectors to Pinecone
    
    Returns:
        Dictionary with indexing statistics
        
    Raises:
        HTTPException: If vector store not initialized or indexing fails
    """
    if not vector_store:
        logger.error("Vector store not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialized"
        )
    
    try:
        logger.info("Starting index population")
        
        # Load articles
        logger.info("Loading Help Center articles")
        articles = load_help_center_articles()
        
        if not articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles loaded"
            )
        
        # Process articles (chunk and embed)
        logger.info("Processing articles")
        processor = DocumentProcessor()
        chunks_with_embeddings = processor.process_articles(articles)
        
        # Upsert to vector store
        logger.info("Upserting to vector store")
        upsert_stats = vector_store.upsert_chunks(chunks_with_embeddings)
        
        logger.info("Index population complete", stats=upsert_stats)
        
        return {
            "message": "Index populated successfully",
            "articles_processed": len(articles),
            "chunks_created": len(chunks_with_embeddings),
            **upsert_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Index population failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Index population failed: {str(e)}"
        )


@app.get("/index/stats", response_model=IndexStatsResponse)
async def get_index_stats():
    """
    Get vector store statistics.
    
    Returns:
        IndexStatsResponse with index information
        
    Raises:
        HTTPException: If vector store not initialized
    """
    if not vector_store:
        logger.error("Vector store not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialized"
        )
    
    try:
        stats = vector_store.get_stats()
        return IndexStatsResponse(**stats)
        
    except Exception as e:
        logger.error("Failed to get index stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get index stats: {str(e)}"
        )


@app.delete(
    "/index/clear",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)]
)
async def clear_index():
    """
    Clear all vectors from the index.
    
    WARNING: This will delete all data from the vector store.
    
    Raises:
        HTTPException: If vector store not initialized or deletion fails
    """
    if not vector_store:
        logger.error("Vector store not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialized"
        )
    
    try:
        logger.warning("Clearing index - all vectors will be deleted")
        vector_store.delete_all()
        logger.info("Index cleared successfully")
        
    except Exception as e:
        logger.error("Failed to clear index", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear index: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower()
    )
