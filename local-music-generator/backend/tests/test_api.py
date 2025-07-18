"""
Test suite for API endpoints

This test suite verifies the API endpoints functionality including:
1. Music generation API endpoints
2. Model management API endpoints
3. System API endpoints
4. Error handling and validation
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app
from models.music_generator import music_generator, GenerationStatus
from models.model_manager import model_manager

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

class TestGenerationAPI:
    """Test music generation API endpoints"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
    
    @patch('models.music_generator.model_manager')
    def test_generate_music_success(self, mock_model_manager):
        """Test successful music generation request"""
        mock_model_manager.is_ready.return_value = True
        
        # Mock the music generator to return a request ID
        with patch.object(music_generator, 'generate_music', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "test-request-id"
            
            response = self.client.post(
                "/api/generate/generate",
                json={
                    "prompt": "peaceful piano music",
                    "duration": 10.0,
                    "guidance_scale": 3.0,
                    "temperature": 1.0
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "request_id" in data
            assert data["status"] == "processing"
            assert "message" in data
    
    def test_generate_music_invalid_prompt(self):
        """Test music generation with invalid prompt"""
        response = self.client.post(
            "/api/generate/generate",
            json={
                "prompt": "",  # Empty prompt should fail validation
                "duration": 10.0
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_music_invalid_duration(self):
        """Test music generation with invalid duration"""
        response = self.client.post(
            "/api/generate/generate",
            json={
                "prompt": "test music",
                "duration": 100.0  # Too long, should fail validation
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_generation_status_not_found(self):
        """Test getting status for non-existent request"""
        response = self.client.get("/api/generate/status/non-existent-id")
        
        assert response.status_code == 404
        response_data = response.json()
        # Check if the error message contains the expected text
        if "detail" in response_data:
            assert "未找到" in response_data["detail"]
        else:
            # Alternative error format
            assert "未找到" in str(response_data)
    
    def test_get_generation_status_success(self):
        """Test getting status for existing request"""
        # Mock a request status
        mock_status = {
            "id": "test-id",
            "prompt": "test music",
            "status": "completed",
            "progress": 100.0,
            "created_at": "2023-01-01T00:00:00",
            "started_at": "2023-01-01T00:00:01",
            "completed_at": "2023-01-01T00:00:10",
            "error_message": None,
            "result_path": "/path/to/result.wav",
            "duration": 10.0,
            "guidance_scale": 3.0,
            "temperature": 1.0,
            "top_k": 250,
            "top_p": 0.0,
            "sample_rate": 32000,
            "output_format": "wav",
            "extra_params": {}
        }
        
        with patch.object(music_generator, 'get_request_status') as mock_get_status:
            mock_get_status.return_value = mock_status
            
            response = self.client.get("/api/generate/status/test-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test-id"
            assert data["status"] == "completed"
            assert data["progress"] == 100.0
    
    def test_cancel_generation_success(self):
        """Test successful generation cancellation"""
        with patch.object(music_generator, 'cancel_request') as mock_cancel:
            mock_cancel.return_value = True
            
            response = self.client.post("/api/generate/cancel/test-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"
            assert "test-id" in data["request_id"]
    
    def test_cancel_generation_not_found(self):
        """Test cancelling non-existent request"""
        with patch.object(music_generator, 'cancel_request') as mock_cancel:
            mock_cancel.return_value = False
            
            response = self.client.post("/api/generate/cancel/non-existent-id")
            
            assert response.status_code == 404
    
    def test_list_generations(self):
        """Test listing generation requests"""
        mock_requests = [
            {
                "id": "req1",
                "prompt": "test1",
                "status": "completed",
                "progress": 100.0,
                "created_at": "2023-01-01T00:00:00",
                "started_at": "2023-01-01T00:00:01",
                "completed_at": "2023-01-01T00:00:10",
                "error_message": None,
                "result_path": "/path/to/result1.wav",
                "duration": 10.0,
                "guidance_scale": 3.0,
                "temperature": 1.0,
                "top_k": 250,
                "top_p": 0.0,
                "sample_rate": 32000,
                "output_format": "wav",
                "extra_params": {}
            },
            {
                "id": "req2",
                "prompt": "test2",
                "status": "processing",
                "progress": 50.0,
                "created_at": "2023-01-01T00:01:00",
                "started_at": "2023-01-01T00:01:01",
                "completed_at": None,
                "error_message": None,
                "result_path": None,
                "duration": 15.0,
                "guidance_scale": 3.0,
                "temperature": 1.0,
                "top_k": 250,
                "top_p": 0.0,
                "sample_rate": 32000,
                "output_format": "wav",
                "extra_params": {}
            }
        ]
        
        with patch.object(music_generator, 'list_requests') as mock_list:
            mock_list.return_value = mock_requests
            
            response = self.client.get("/api/generate/list")
            
            assert response.status_code == 200
            data = response.json()
            assert "requests" in data
            assert "total" in data
            assert "active" in data
            assert "completed" in data
            assert len(data["requests"]) == 2
            assert data["total"] == 2
            assert data["active"] == 1  # One processing
            assert data["completed"] == 1  # One completed
    
    def test_get_generation_stats(self):
        """Test getting generation statistics"""
        mock_stats = {
            "active_requests": 2,
            "completed_requests": 5,
            "total_requests": 7,
            "status_counts": {
                "completed": 3,
                "processing": 2,
                "failed": 1,
                "cancelled": 1
            },
            "model_ready": True
        }
        
        with patch.object(music_generator, 'get_generation_stats') as mock_stats_func:
            mock_stats_func.return_value = mock_stats
            
            response = self.client.get("/api/generate/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["active_requests"] == 2
            assert data["completed_requests"] == 5
            assert data["total_requests"] == 7
            assert data["model_ready"] == True
            assert "status_counts" in data


class TestModelAPI:
    """Test model management API endpoints"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
    
    def test_get_model_status(self):
        """Test getting model status"""
        mock_status = {
            "name": "facebook/musicgen-small",
            "status": "loaded",
            "loaded_at": "2023-01-01T00:00:00",
            "error_message": None,
            "device": "cpu",
            "memory_usage_mb": 1024,
            "inference_count": 5,
            "last_inference_time": "2023-01-01T00:05:00",
            "model_size_mb": 512
        }
        
        with patch.object(model_manager, 'get_model_status') as mock_get_status:
            mock_get_status.return_value = mock_status
            
            response = self.client.get("/api/models/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "facebook/musicgen-small"
            assert data["status"] == "loaded"
            assert data["device"] == "cpu"
    
    def test_load_model_success(self):
        """Test successful model loading"""
        with patch.object(model_manager, 'is_ready') as mock_is_ready, \
             patch.object(model_manager, 'load_model', new_callable=AsyncMock) as mock_load, \
             patch.object(model_manager, 'get_model_status') as mock_get_status:
            
            mock_is_ready.return_value = False
            mock_load.return_value = True
            mock_get_status.return_value = {
                "name": "facebook/musicgen-small",
                "status": "loaded",
                "device": "cpu",
                "memory_usage_mb": 1024,
                "model_size_mb": 512
            }
            
            response = self.client.post(
                "/api/models/load",
                json={"model_name": "facebook/musicgen-small"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "successfully" in data["message"]
            assert data["model_name"] == "facebook/musicgen-small"
    
    def test_load_model_already_loaded(self):
        """Test loading model when already loaded"""
        with patch.object(model_manager, 'is_ready') as mock_is_ready, \
             patch.object(model_manager, 'get_model_status') as mock_get_status:
            
            mock_is_ready.return_value = True
            mock_get_status.return_value = {
                "name": "facebook/musicgen-small",
                "status": "loaded",
                "device": "cpu"
            }
            
            response = self.client.post(
                "/api/models/load",
                json={"model_name": "facebook/musicgen-small", "force": False}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "already loaded" in data["message"]
    
    def test_unload_model_success(self):
        """Test successful model unloading"""
        with patch.object(model_manager, 'is_ready') as mock_is_ready, \
             patch.object(model_manager, 'unload_model', new_callable=AsyncMock) as mock_unload:
            
            mock_is_ready.return_value = True
            mock_unload.return_value = True
            
            response = self.client.post("/api/models/unload")
            
            assert response.status_code == 200
            data = response.json()
            assert "successfully" in data["message"]
            assert data["status"] == "not_loaded"
    
    def test_unload_model_not_loaded(self):
        """Test unloading model when not loaded"""
        with patch.object(model_manager, 'is_ready') as mock_is_ready:
            mock_is_ready.return_value = False
            
            response = self.client.post("/api/models/unload")
            
            assert response.status_code == 200
            data = response.json()
            assert "not loaded" in data["message"]


class TestSystemAPI:
    """Test system API endpoints"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "running" in data["message"]
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_settings_endpoint(self):
        """Test settings endpoint"""
        response = self.client.get("/settings")
        
        assert response.status_code == 200
        data = response.json()
        # Should return settings dictionary
        assert isinstance(data, dict)


class TestAPIValidation:
    """Test API input validation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
    
    def test_generation_request_validation(self):
        """Test generation request validation"""
        # Test missing required fields
        response = self.client.post("/api/generate/generate", json={})
        assert response.status_code == 422
        
        # Test invalid prompt length
        response = self.client.post(
            "/api/generate/generate",
            json={"prompt": "x" * 501}  # Too long
        )
        assert response.status_code == 422
        
        # Test invalid duration
        response = self.client.post(
            "/api/generate/generate",
            json={"prompt": "test", "duration": -1}  # Negative duration
        )
        assert response.status_code == 422
        
        # Test invalid guidance_scale
        response = self.client.post(
            "/api/generate/generate",
            json={"prompt": "test", "guidance_scale": 15}  # Too high
        )
        assert response.status_code == 422
    
    def test_list_generations_validation(self):
        """Test list generations parameter validation"""
        # Test invalid limit
        response = self.client.get("/api/generate/list?limit=0")
        assert response.status_code == 422
        
        response = self.client.get("/api/generate/list?limit=200")
        assert response.status_code == 422


if __name__ == "__main__":
    # Run basic tests
    print("Running API Tests...")
    
    # Test generation API
    print("\n=== Testing Generation API ===")
    gen_test = TestGenerationAPI()
    gen_test.setup_method()
    
    try:
        gen_test.test_generate_music_invalid_prompt()
        print("✅ Generation validation test passed")
    except Exception as e:
        print(f"❌ Generation validation test failed: {e}")
    
    try:
        gen_test.test_get_generation_status_not_found()
        print("✅ Status not found test passed")
    except Exception as e:
        print(f"❌ Status not found test failed: {e}")
    
    # Test model API
    print("\n=== Testing Model API ===")
    model_test = TestModelAPI()
    model_test.setup_method()
    
    try:
        model_test.test_unload_model_not_loaded()
        print("✅ Model unload test passed")
    except Exception as e:
        print(f"❌ Model unload test failed: {e}")
    
    # Test system API
    print("\n=== Testing System API ===")
    system_test = TestSystemAPI()
    system_test.setup_method()
    
    try:
        system_test.test_root_endpoint()
        print("✅ Root endpoint test passed")
    except Exception as e:
        print(f"❌ Root endpoint test failed: {e}")
    
    try:
        system_test.test_health_check()
        print("✅ Health check test passed")
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
    
    # Test validation
    print("\n=== Testing API Validation ===")
    validation_test = TestAPIValidation()
    validation_test.setup_method()
    
    try:
        validation_test.test_generation_request_validation()
        print("✅ Request validation test passed")
    except Exception as e:
        print(f"❌ Request validation test failed: {e}")
    
    print("\nAll tests completed!")