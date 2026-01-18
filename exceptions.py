"""
Custom exception classes for better error handling.
"""


class RAGSystemException(Exception):
    """Base exception for RAG system errors."""
    pass


class VectorStoreException(RAGSystemException):
    """Exception for vector store operations."""
    pass


class DataIngestionException(RAGSystemException):
    """Exception for data ingestion errors."""
    pass


class EmbeddingException(RAGSystemException):
    """Exception for embedding generation errors."""
    pass


class LLMException(RAGSystemException):
    """Exception for LLM generation errors."""
    pass


class ConfigurationException(RAGSystemException):
    """Exception for configuration errors."""
    pass
