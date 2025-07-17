"""
Tests for the API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Local Music Generator API is running" in response.json()["message"]

def test_health_endpoint():
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_settings_endpoint():
    """Test the settings endpoint."""
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert "audio" in data
    assert "system" in data
    assert "ui" in data

def test_api_root_endpoint():
    """Test the API root endpoint."""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data
    assert "features" in data
    assert isinstance(data["features"], list)

def test_api_status_endpoint():
    """Test the API status endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "api" in data
    assert "model" in data
    assert "system" in data

def test_api_routes_endpoint():
    """Test the API routes endpoint."""
    response = client.get("/api/routes")
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert isinstance(data["routes"], list)

def test_system_resources_endpoint():
    """Test the system resources endpoint."""
    response = client.get("/api/system/resources")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data

def test_system_info_endpoint():
    """Test the system info endpoint."""
    response = client.get("/api/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert "architecture" in data
    assert "python_version" in data

def test_system_processes_endpoint():
    """Test the system processes endpoint."""
    response = client.get("/api/system/processes")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "processes" in data
    assert isinstance(data["processes"], list)

def test_error_handling_http():
    """Test HTTP error handling."""
    response = client.get("/api/system/test-error/http?message=Test%20HTTP%20error")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "timestamp" in data["error"]

def test_error_handling_model_load():
    """Test model load error handling."""
    response = client.get("/api/system/test-error/model_load?message=Test%20model%20load%20error")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MODEL_LOAD_ERROR"
    assert data["error"]["message"] == "Failed to load the model"

def test_resource_warning():
    """Test resource warning endpoint."""
    response = client.get("/api/system/check-warning?threshold=10")
    assert response.status_code == 200
    data = response.json()
    assert "has_warnings" in data
    assert "warnings" in data
    assert "threshold" in data
    assert data["threshold"] == 10