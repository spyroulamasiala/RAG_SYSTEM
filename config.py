"""
Application configuration management.
Uses pydantic-settings for environment variable validation and type safety.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # Pinecone Configuration
    pinecone_api_key: str = Field(..., description="Pinecone API key")
    pinecone_environment: str = Field(default="gcp-starter", description="Pinecone environment")
    pinecone_index_name: str = Field(default="typeform-help-center", description="Pinecone index name")
    
    # Application Configuration
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    log_level: str = Field(default="INFO")
    api_port: int = Field(default=8000)
    api_host: str = Field(default="0.0.0.0")
    allowed_origins: str = Field(default="*", description="Comma-separated allowed CORS origins")
    admin_token: str = Field(default="", description="Optional token required for admin endpoints")
    
    # RAG Configuration
    embedding_model: str = Field(default="text-embedding-3-small")
    llm_model: str = Field(default="gpt-4-turbo-preview")
    chunk_size: int = Field(default=1000, description="Size of text chunks for embedding")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    top_k_results: int = Field(default=3, description="Number of chunks to retrieve")
    max_tokens: int = Field(default=500, description="Max tokens for LLM response")
    temperature: float = Field(default=0.7, description="LLM temperature")
    
# Global settings instance
settings = Settings()
