import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime

from main import app
from models.music_generator import GenerationStatus

client = TestClient(app)

@pytest.fixture
def mock_music_generator():
    with patch('api.generation.music_generator') as mock:
        mock.generate_music.return_value = {
            'task_id': 'test_task_123',
            'status': GenerationStatus.PROCESSING,
            'progress': 0
        }
        mock.get_task_status.return_value = {
            'task_id': 'test_task_123',
            'status': GenerationStatus.COMPLETED,
            'progress': 100,
            'result': {
                'audio_url': '/api/audio/test_audio.mp3',
                'prompt': 'test prompt',
                'metadata': {
                    'duration': 30,
                    'sample_rate': 44100,
                    'format': 'mp3'
                }
            }
        }
        mock.get_task_result.return_value = {
            'task_id': 'test_task_123',
            'status': GenerationStatus.COMPLETED,
            'result': {
                'audio_url': '/api/audio/test_audio.mp3',
                'prompt': 'test prompt',
                'metadata': {
                    'duration': 30,
                    'sample_rate': 44100,
                    'format': 'mp3'
                }
            }
        }
        mock.cancel_task.return_value = {'success': True}
        mock.get_generation_history.return_value = []
        mock.get_generation_stats.return_value = {
            'total_generations': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'average_generation_time': 0
        }
        yield mock

class TestGenerationAPI:
    
    def test_generate_music_success(self, mock_music_generator):
        """Test successful music generation request"""
        response = client.post("/api/generation/generate", json={
            "prompt": "upbeat jazz piano",
            "duration": 30,
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.9,
            "guidance_scale": 7.5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test_task_123"
        assert data["status"] == GenerationStatus.PROCESSING
        assert data["progress"] == 0
        
        mock_music_generator.generate_music.assert_called_once()

    def test_generate_music_missing_prompt(self):
        """Test generation request without prompt"""
        response = client.post("/api/generation/generate", json={
            "duration": 30
        })
        
        assert response.status_code == 422  # Validation error

    def test_generate_music_invalid_duration(self):
        """Test generation request with invalid duration"""
        response = client.post("/api/generation/generate", json={
            "prompt": "test prompt",
            "duration": 200  # Too long
        })
        
        assert response.status_code == 422

    def test_get_task_status_success(self, mock_music_generator):
        """Test getting task status"""
        response = client.get("/api/generation/status/test_task_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test_task_123"
        assert data["status"] == GenerationStatus.COMPLETED
        assert data["progress"] == 100

    def test_get_task_status_not_found(self, mock_music_generator):
        """Test getting status for non-existent task"""
        mock_music_generator.get_task_status.return_value = None
        
        response = client.get("/api/generation/status/nonexistent_task")
        
        assert response.status_code == 404

    def test_get_task_result_success(self, mock_music_generator):
        """Test getting task result"""
        response = client.get("/api/generation/result/test_task_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test_task_123"
        assert data["status"] == GenerationStatus.COMPLETED
        assert "result" in data
        assert data["result"]["audio_url"] == "/api/audio/test_audio.mp3"

    def test_get_task_result_not_found(self, mock_music_generator):
        """Test getting result for non-existent task"""
        mock_music_generator.get_task_result.return_value = None
        
        response = client.get("/api/generation/result/nonexistent_task")
        
        assert response.status_code == 404

    def test_cancel_task_success(self, mock_music_generator):
        """Test cancelling a task"""
        response = client.post("/api/generation/cancel/test_task_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    def test_cancel_task_not_found(self, mock_music_generator):
        """Test cancelling non-existent task"""
        mock_music_generator.cancel_task.return_value = None
        
        response = client.post("/api/generation/cancel/nonexistent_task")
        
        assert response.status_code == 404

    def test_get_generation_history(self, mock_music_generator):
        """Test getting generation history"""
        response = client.get("/api/generation/history")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_generation_stats(self, mock_music_generator):
        """Test getting generation statistics"""
        response = client.get("/api/generation/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_generations" in data
        assert "successful_generations" in data
        assert "failed_generations" in data
        assert "average_generation_time" in data

    def test_validate_parameters_success(self):
        """Test parameter validation"""
        response = client.post("/api/generation/validate", json={
            "prompt": "test prompt",
            "duration": 30,
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.9,
            "guidance_scale": 7.5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True

    def test_validate_parameters_invalid(self):
        """Test parameter validation with invalid parameters"""
        response = client.post("/api/generation/validate", json={
            "prompt": "",  # Empty prompt
            "duration": -10,  # Invalid duration
            "temperature": 2.0,  # Invalid temperature
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "errors" in data

    def test_generate_music_server_error(self, mock_music_generator):
        """Test handling server errors during generation"""
        mock_music_generator.generate_music.side_effect = Exception("Server error")
        
        response = client.post("/api/generation/generate", json={
            "prompt": "test prompt",
            "duration": 30
        })
        
        assert response.status_code == 500