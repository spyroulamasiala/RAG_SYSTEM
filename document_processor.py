"""
Document processing module for chunking and embedding Help Center articles.
Uses LangChain for text splitting and OpenAI for embeddings.
"""
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import structlog
from config import settings
from data_ingestion import Article

logger = structlog.get_logger()


class DocumentProcessor:
    """
    Handles document chunking and embedding generation.
    
    Strategy:
    - Use RecursiveCharacterTextSplitter for intelligent text splitting
    - Maintain semantic coherence by splitting on paragraphs, sentences, then characters
    - Add overlap between chunks to preserve context
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        embedding_model: str = None
    ):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Size of each text chunk (defaults to config value)
            chunk_overlap: Overlap between chunks (defaults to config value)
            embedding_model: OpenAI embedding model to use (defaults to config value)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.embedding_model = embedding_model or settings.embedding_model
        
        # Initialize text splitter with semantic-aware splitting
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],  # Try to split on paragraphs first
            keep_separator=True
        )
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        
        logger.info(
            "DocumentProcessor initialized",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            embedding_model=self.embedding_model
        )
    
    def chunk_article(self, article: Article) -> List[Dict[str, Any]]:
        """
        Split an article into chunks with metadata.
        
        Args:
            article: Article object to chunk
            
        Returns:
            List of dictionaries containing chunk text and metadata
        """
        logger.info("Chunking article", title=article.title)
        
        # Create full text with title for better context
        full_text = f"# {article.title}\n\n{article.content}"
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(full_text)
        
        # Create chunk objects with metadata
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk_obj = {
                "text": chunk_text,
                "metadata": {
                    **article.metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_id": f"{article.url}#chunk-{i}"
                }
            }
            chunk_objects.append(chunk_obj)
        
        logger.info(
            "Article chunked",
            title=article.title,
            num_chunks=len(chunks),
            avg_chunk_size=sum(len(c) for c in chunks) // len(chunks) if chunks else 0
        )
        
        return chunk_objects
    
    def chunk_articles(self, articles: List[Article]) -> List[Dict[str, Any]]:
        """
        Chunk multiple articles.
        
        Args:
            articles: List of Article objects
            
        Returns:
            List of all chunks from all articles
        """
        all_chunks = []
        for article in articles:
            chunks = self.chunk_article(article)
            all_chunks.extend(chunks)
        
        logger.info(
            "All articles chunked",
            num_articles=len(articles),
            total_chunks=len(all_chunks)
        )
        
        return all_chunks
    
    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for all chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of chunks with embeddings added
        """
        logger.info("Generating embeddings", num_chunks=len(chunks))
        
        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings in batch for efficiency
        try:
            embeddings = self.embeddings.embed_documents(texts)
            
            # Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk["embedding"] = embedding
            
            logger.info(
                "Embeddings generated",
                num_embeddings=len(embeddings),
                embedding_dim=len(embeddings[0]) if embeddings else 0
            )
            
            return chunks
            
        except Exception as e:
            logger.error("Failed to generate embeddings", error=str(e))
            raise
    
    def process_articles(self, articles: List[Article]) -> List[Dict[str, Any]]:
        """
        Complete processing pipeline: chunk and embed articles.
        
        Args:
            articles: List of Article objects
            
        Returns:
            List of chunks with embeddings and metadata
        """
        logger.info("Starting article processing pipeline", num_articles=len(articles))
        
        # Chunk all articles
        chunks = self.chunk_articles(articles)
        
        # Generate embeddings
        chunks_with_embeddings = self.generate_embeddings(chunks)
        
        logger.info("Article processing complete", total_chunks=len(chunks_with_embeddings))
        
        return chunks_with_embeddings
