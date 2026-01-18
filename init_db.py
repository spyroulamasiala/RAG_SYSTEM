"""
Initialization script to populate the vector database with Help Center articles.
Run this script once to set up the knowledge base before starting the API server.
"""
import asyncio
import structlog
from config import settings
from data_ingestion import load_help_center_articles
from sample_articles import load_sample_articles
from document_processor import DocumentProcessor
from vector_store import VectorStore

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()


def main():
    """Initialize the vector database with Help Center articles."""
    logger.info("=" * 60)
    logger.info("Help Center - Vector DB Initialization")
    logger.info("=" * 60)
    
    try:
        # Step 1: Initialize vector store
        logger.info("Step 1: Initializing Pinecone vector store")
        vector_store = VectorStore()
        vector_store.create_index(dimension=1536)
        logger.info("✓ Vector store initialized")
        
        # Step 2: Load Help Center articles
        logger.info("\nStep 2: Loading Help Center articles")
        # Use sample articles since live URLs return 403 Forbidden
        articles = load_sample_articles()
        logger.info(f"✓ Loaded {len(articles)} articles")
        
        for i, article in enumerate(articles, 1):
            logger.info(f"  {i}. {article.title}")
        
        # Step 3: Process articles (chunk and embed)
        logger.info("\nStep 3: Processing articles (chunking and embedding)")
        processor = DocumentProcessor()
        chunks_with_embeddings = processor.process_articles(articles)
        logger.info(f"✓ Created {len(chunks_with_embeddings)} chunks with embeddings")
        
        # Step 4: Upsert to Pinecone
        logger.info("\nStep 4: Uploading to Pinecone")
        upsert_stats = vector_store.upsert_chunks(chunks_with_embeddings)
        logger.info(f"✓ Uploaded {upsert_stats['total_upserted']} vectors in {upsert_stats['batches']} batches")
        
        # Step 5: Verify
        logger.info("\nStep 5: Verifying index")
        stats = vector_store.get_stats()
        logger.info(f"✓ Index contains {stats['total_vectors']} vectors")
        logger.info(f"  Dimension: {stats['dimension']}")
        logger.info(f"  Fullness: {stats['index_fullness']:.2%}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Initialization complete! You can now start the API server.")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("\n✗ Initialization failed", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    main()
