"""
Vector database module for managing embeddings in Pinecone.
Handles index creation, upserting vectors, and similarity search.
"""
from typing import List, Dict, Any, Optional
import time
from pinecone import Pinecone, ServerlessSpec
import structlog
from config import settings

logger = structlog.get_logger()


class VectorStore:
    """
    Manages vector storage and retrieval using Pinecone.
    
    Handles:
    - Index creation and configuration
    - Batch upsert of vectors
    - Similarity search for RAG retrieval
    """
    
    def __init__(
        self,
        api_key: str = None,
        environment: str = None,
        index_name: str = None
    ):
        """
        Initialize Pinecone vector store.
        
        Args:
            api_key: Pinecone API key (defaults to config value)
            environment: Pinecone environment (defaults to config value)
            index_name: Name of the Pinecone index (defaults to config value)
        """
        self.api_key = api_key or settings.pinecone_api_key
        self.environment = environment or settings.pinecone_environment
        self.index_name = index_name or settings.pinecone_index_name
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        
        logger.info(
            "VectorStore initialized",
            index_name=self.index_name,
            environment=self.environment
        )
    
    def create_index(self, dimension: int = 1536, metric: str = "cosine") -> None:
        """
        Create a Pinecone index if it doesn't exist.
        
        Args:
            dimension: Embedding dimension (1536 for text-embedding-3-small)
            metric: Distance metric (cosine, euclidean, or dotproduct)
        """
        logger.info("Checking if index exists", index_name=self.index_name)
        
        # Check if index already exists
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name in existing_indexes:
            logger.info("Index already exists", index_name=self.index_name)
        else:
            logger.info(
                "Creating new index",
                index_name=self.index_name,
                dimension=dimension,
                metric=metric
            )
            
            # Create index with serverless spec (free tier compatible)
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    cloud='aws',  # Can be 'aws', 'gcp', or 'azure'
                    region='us-east-1'  # Adjust based on your Pinecone account
                )
            )
            
            # Wait for index to be ready
            logger.info("Waiting for index to be ready...")
            time.sleep(5)  # Give it a few seconds to initialize
        
        # Connect to the index
        self.index = self.pc.Index(self.index_name)
        logger.info("Connected to index", index_name=self.index_name)
    
    def upsert_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]:
        """
        Upsert document chunks to Pinecone.
        
        Args:
            chunks: List of chunks with embeddings and metadata
            batch_size: Number of vectors to upsert per batch
            
        Returns:
            Dictionary with upsert statistics
        """
        if not self.index:
            raise ValueError("Index not initialized. Call create_index() first.")
        
        logger.info("Starting upsert", num_chunks=len(chunks), batch_size=batch_size)
        
        vectors = []
        for i, chunk in enumerate(chunks):
            vector = {
                "id": chunk["metadata"]["chunk_id"],
                "values": chunk["embedding"],
                "metadata": {
                    "text": chunk["text"],
                    "title": chunk["metadata"]["title"],
                    "url": chunk["metadata"]["url"],
                    "source": chunk["metadata"]["source"],
                    "chunk_index": chunk["metadata"]["chunk_index"],
                    "total_chunks": chunk["metadata"]["total_chunks"]
                }
            }
            vectors.append(vector)
        
        # Upsert in batches
        total_upserted = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            total_upserted += len(batch)
            logger.info(f"Upserted batch {i // batch_size + 1}", vectors_in_batch=len(batch))
        
        logger.info("Upsert complete", total_vectors=total_upserted)
        
        return {
            "total_upserted": total_upserted,
            "batches": (len(vectors) + batch_size - 1) // batch_size
        }
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Pinecone.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return (defaults to config value)
            filter_dict: Optional metadata filter
            
        Returns:
            List of matching documents with scores
        """
        if not self.index:
            raise ValueError("Index not initialized. Call create_index() first.")
        
        top_k = top_k or settings.top_k_results
        
        logger.info("Searching vectors", top_k=top_k, has_filter=bool(filter_dict))
        
        # Perform search
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "title": match.metadata.get("title", ""),
                "url": match.metadata.get("url", ""),
                "metadata": match.metadata
            })
        
        logger.info("Search complete", num_results=len(formatted_results))
        
        return formatted_results
    
    def delete_all(self) -> None:
        """Delete all vectors from the index."""
        if not self.index:
            raise ValueError("Index not initialized. Call create_index() first.")
        
        logger.warning("Deleting all vectors from index", index_name=self.index_name)
        self.index.delete(delete_all=True)
        logger.info("All vectors deleted")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if not self.index:
            raise ValueError("Index not initialized. Call create_index() first.")
        
        stats = self.index.describe_index_stats()
        return {
            "total_vectors": stats.total_vector_count,
            "dimension": stats.dimension,
            "index_fullness": stats.index_fullness
        }
