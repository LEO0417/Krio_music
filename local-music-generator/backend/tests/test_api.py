"""
Tests for the API endpoints.
"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_root():
    """
    Test the root endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health():
    """
    Test the health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_api_root():
    """
    Test the API root endpoint.
    """
    response = client.get("/api")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()
    assert "status" in response.json()