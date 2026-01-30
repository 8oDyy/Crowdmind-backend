from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health endpoint returns correct response"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Tout va bien"}


def test_app_exists():
    """Test that the FastAPI app is created correctly"""
    assert app is not None
    assert app.title == "CrowdMind API"
    assert app.version == "1.0"


def test_docs_endpoint():
    """Test that the docs endpoint is accessible"""
    response = client.get("/api/docs")
    assert response.status_code == 200
