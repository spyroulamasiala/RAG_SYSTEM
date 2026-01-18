"""
RAG (Retrieval-Augmented Generation) engine.
Combines vector retrieval with LLM generation for answering queries.
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
import structlog
from config import settings
from vector_store import VectorStore

logger = structlog.get_logger()


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for the Help Center chatbot.
    
    Process:
    1. Embed user query
    2. Retrieve relevant chunks from vector store
    3. Construct prompt with retrieved context
    4. Generate response using LLM
    """
    
    SYSTEM_PROMPT = """You are a helpful customer support assistant for Typeform. 
Your role is to answer questions about Typeform's Help Center articles accurately and concisely.

Use the following context from the Help Center to answer the user's question.
If the context doesn't contain enough information to answer the question, politely say so and suggest they contact support.

Always be friendly, professional, and helpful. If relevant, provide step-by-step instructions.

Context from Help Center:
{context}
"""
    
    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the context above."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        llm_model: str = None,
        embedding_model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        """
        Initialize the RAG engine.
        
        Args:
            vector_store: VectorStore instance for retrieval
            llm_model: LLM model name (defaults to config value)
            embedding_model: Embedding model name (defaults to config value)
            temperature: LLM temperature (defaults to config value)
            max_tokens: Max tokens for response (defaults to config value)
        """
        self.vector_store = vector_store
        self.llm_model = llm_model or settings.llm_model
        self.embedding_model = embedding_model or settings.embedding_model
        self.temperature = temperature or settings.temperature
        self.max_tokens = max_tokens or settings.max_tokens
        
        # Initialize embeddings for query encoding
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.llm_model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            openai_api_key=settings.openai_api_key
        )
        
        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("user", self.USER_PROMPT)
        ])
        
        logger.info(
            "RAGEngine initialized",
            llm_model=self.llm_model,
            embedding_model=self.embedding_model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query string
            top_k: Number of documents to retrieve (defaults to config value)
            
        Returns:
            List of retrieved documents with metadata
        """
        logger.info("Retrieving documents", query=query, top_k=top_k)
        
        # Embed the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        logger.info("Documents retrieved", num_results=len(results))
        
        return results
    
    def generate(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a response using retrieved context.
        
        Args:
            query: User query string
            context_docs: Retrieved context documents
            include_sources: Whether to include source URLs in response
            
        Returns:
            Dictionary with answer and metadata
        """
        logger.info("Generating response", query=query, num_context_docs=len(context_docs))
        
        # Format context from retrieved documents
        context = self._format_context(context_docs)
        
        # Create prompt
        prompt = self.prompt_template.format_messages(
            context=context,
            question=query
        )
        
        # Generate response
        response = self.llm.invoke(prompt)
        answer = response.content
        
        # Prepare response object
        result = {
            "answer": answer,
            "query": query,
            "num_sources": len(context_docs)
        }
        
        if include_sources:
            result["sources"] = self._extract_sources(context_docs)
        
        logger.info("Response generated", answer_length=len(answer))
        
        return result
    
    def query(
        self,
        question: str,
        top_k: int = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve and generate.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            include_sources: Whether to include source URLs
            
        Returns:
            Dictionary with answer and metadata
        """
        logger.info("Processing RAG query", question=question)
        
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(question, top_k=top_k)
        
        # Generate response
        result = self.generate(
            query=question,
            context_docs=retrieved_docs,
            include_sources=include_sources
        )
        
        logger.info("RAG query complete")
        
        return result
    
    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            docs: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(
                f"[Source {i}] {doc['title']}\n{doc['text']}\n"
            )
        
        return "\n".join(context_parts)
    
    def _extract_sources(self, docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract source information from documents.
        
        Args:
            docs: List of retrieved documents
            
        Returns:
            List of source dictionaries
        """
        sources = []
        seen_urls = set()
        
        for doc in docs:
            url = doc.get("url", "")
            if url and url not in seen_urls:
                sources.append({
                    "title": doc.get("title", ""),
                    "url": url,
                    "relevance_score": doc.get("score", 0.0)
                })
                seen_urls.add(url)
        
        return sources
