"""
Test suite for the RAG chatbot application.
Run with: pytest
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app
from rag_engine import RAGEngine
from vector_store import VectorStore


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def stubbed_client(monkeypatch):
    """Test client with stubbed RAG engine and vector store."""

    class StubRAG:
        def query(self, question: str, top_k=None, include_sources: bool = True):
            return {
                "answer": "stub-answer",
                "query": question,
                "num_sources": 1,
                "sources": [{"title": "stub", "url": "https://example.com", "relevance_score": 0.9}]
            }

    class StubVectorStore:
        def get_stats(self):
            return {"total_vectors": 1, "dimension": 1536, "index_fullness": 0.01}

        def delete_all(self):
            return None

    monkeypatch.setattr("main.rag_engine", StubRAG())
    monkeypatch.setattr("main.vector_store", StubVectorStore())
    return TestClient(app)


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    mock = Mock(spec=VectorStore)
    mock.search.return_value = [
        {
            "id": "test-1",
            "score": 0.9,
            "text": "Test content about multi-language forms",
            "title": "Create multi-language forms",
            "url": "https://example.com/test",
            "metadata": {}
        }
    ]
    return mock


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check_returns_200(self, client):
        """Test that health check returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_returns_status(self, client):
        """Test that health check returns status information."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "environment" in data


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_returns_200(self, client):
        """Test that root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_returns_api_info(self, client):
        """Test that root returns API information."""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestReadinessEndpoint:
    """Tests for readiness probe."""

    def test_readiness_returns_200_with_stubs(self, stubbed_client):
        response = stubbed_client.get("/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["vector_store_initialized"] is True
        assert body["rag_engine_initialized"] is True


class TestQueryEndpoint:
    """Tests for the query endpoint."""
    
    def test_query_requires_question(self, client):
        """Test that query endpoint validates required fields."""
        response = client.post("/query", json={})
        assert response.status_code == 422  # Validation error
    
    def test_query_validates_question_length(self, client):
        """Test that query endpoint validates question length."""
        response = client.post("/query", json={
            "question": ""  # Empty question
        })
        assert response.status_code == 422
    
    def test_query_accepts_valid_request(self, client):
        """Test that query endpoint accepts valid requests."""
        # Note: This will fail without proper initialization
        # In real tests, we'd mock the RAG engine
        response = client.post("/query", json={
            "question": "How do I create a form?"
        })
        # Will be 503 if not initialized, 200 if initialized
        assert response.status_code in [200, 503]

    def test_query_returns_200_with_stubbed_dependencies(self, stubbed_client):
        response = stubbed_client.post("/query", json={
            "question": "stub question",
            "include_sources": True
        })
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "stub-answer"
        assert "X-Request-ID" in response.headers


class TestRAGEngine:
    """Tests for the RAG engine."""
    
    def test_format_context(self, mock_vector_store):
        """Test context formatting."""
        rag = RAGEngine(vector_store=mock_vector_store)
        
        docs = [
            {"title": "Test 1", "text": "Content 1"},
            {"title": "Test 2", "text": "Content 2"}
        ]
        
        context = rag._format_context(docs)
        
        assert "Test 1" in context
        assert "Test 2" in context
        assert "Content 1" in context
        assert "Content 2" in context
    
    def test_extract_sources(self, mock_vector_store):
        """Test source extraction."""
        rag = RAGEngine(vector_store=mock_vector_store)
        
        docs = [
            {"title": "Test", "url": "http://example.com", "score": 0.9},
            {"title": "Test", "url": "http://example.com", "score": 0.8}  # Duplicate
        ]
        
        sources = rag._extract_sources(docs)
        
        # Should deduplicate URLs
        assert len(sources) == 1
        assert sources[0]["url"] == "http://example.com"


class TestVectorStore:
    """Tests for the vector store."""
    
    @patch('vector_store.Pinecone')
    def test_vector_store_initialization(self, mock_pinecone):
        """Test vector store initializes correctly."""
        vs = VectorStore(
            api_key="test-key",
            environment="test-env",
            index_name="test-index"
        )
        
        assert vs.api_key == "test-key"
        assert vs.environment == "test-env"
        assert vs.index_name == "test-index"


class TestAdminGuard:
    """Tests for admin token enforcement."""

    def test_admin_token_required_when_set(self, client, monkeypatch):
        monkeypatch.setattr("main.settings.admin_token", "secret")
        response = client.post("/index/populate")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid admin token"

    def test_admin_token_allows_request_with_header(self, stubbed_client, monkeypatch):
        monkeypatch.setattr("main.settings.admin_token", "secret")
        response = stubbed_client.delete("/index/clear", headers={"X-Admin-Token": "secret"})
        assert response.status_code == 204


# Integration test example (requires actual API keys)
@pytest.mark.integration
@pytest.mark.skip(reason="Requires API keys and initialization")
class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_full_query_pipeline(self, client):
        """Test complete query flow from API to response."""
        response = client.post("/query", json={
            "question": "How do I create a multi-language form?",
            "top_k": 3,
            "include_sources": True
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "query" in data
        assert "sources" in data
        assert len(data["answer"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
