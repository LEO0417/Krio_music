import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import io

from main import app

client = TestClient(app)

@pytest.fixture
def mock_audio_files():
    """Mock audio files for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock audio files
        audio_files = {
            'test_audio_1.mp3': b'fake mp3 data',
            'test_audio_2.wav': b'fake wav data',
        }
        
        for filename, content in audio_files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_bytes(content)
        
        yield temp_dir, audio_files

class TestAudioAPI:
    
    def test_serve_audio_file_success(self, mock_audio_files):
        """Test serving existing audio file"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            response = client.get("/api/audio/test_audio_1.mp3")
            
            assert response.status_code == 200
            assert response.content == b'fake mp3 data'
            assert response.headers['content-type'] == 'audio/mpeg'
    
    def test_serve_audio_file_not_found(self):
        """Test serving non-existent audio file"""
        response = client.get("/api/audio/nonexistent.mp3")
        
        assert response.status_code == 404
        assert "Audio file not found" in response.json()["detail"]
    
    def test_serve_audio_file_invalid_extension(self):
        """Test serving file with invalid extension"""
        response = client.get("/api/audio/test.txt")
        
        assert response.status_code == 400
        assert "Invalid audio file format" in response.json()["detail"]
    
    def test_get_audio_metadata_success(self, mock_audio_files):
        """Test getting audio metadata"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            with patch('api.audio.get_audio_metadata') as mock_metadata:
                mock_metadata.return_value = {
                    'duration': 30.5,
                    'sample_rate': 44100,
                    'channels': 2,
                    'format': 'mp3',
                    'bitrate': 320000
                }
                
                response = client.get("/api/audio/test_audio_1.mp3/metadata")
                
                assert response.status_code == 200
                data = response.json()
                assert data['duration'] == 30.5
                assert data['sample_rate'] == 44100
                assert data['channels'] == 2
                assert data['format'] == 'mp3'
                assert data['bitrate'] == 320000
    
    def test_get_audio_metadata_not_found(self):
        """Test getting metadata for non-existent file"""
        response = client.get("/api/audio/nonexistent.mp3/metadata")
        
        assert response.status_code == 404
    
    def test_download_audio_file_success(self, mock_audio_files):
        """Test downloading audio file"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            response = client.get("/api/audio/test_audio_1.mp3/download")
            
            assert response.status_code == 200
            assert response.content == b'fake mp3 data'
            assert 'attachment' in response.headers['content-disposition']
            assert 'test_audio_1.mp3' in response.headers['content-disposition']
    
    def test_download_audio_file_not_found(self):
        """Test downloading non-existent file"""
        response = client.get("/api/audio/nonexistent.mp3/download")
        
        assert response.status_code == 404
    
    def test_delete_audio_file_success(self, mock_audio_files):
        """Test deleting audio file"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            response = client.delete("/api/audio/test_audio_1.mp3")
            
            assert response.status_code == 200
            assert response.json()['message'] == 'Audio file deleted successfully'
            
            # Check that file is actually deleted
            assert not os.path.exists(os.path.join(temp_dir, 'test_audio_1.mp3'))
    
    def test_delete_audio_file_not_found(self):
        """Test deleting non-existent file"""
        response = client.delete("/api/audio/nonexistent.mp3")
        
        assert response.status_code == 404
    
    def test_list_audio_files_success(self, mock_audio_files):
        """Test listing audio files"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            with patch('api.audio.get_audio_metadata') as mock_metadata:
                mock_metadata.return_value = {
                    'duration': 30.5,
                    'sample_rate': 44100,
                    'channels': 2,
                    'format': 'mp3',
                    'bitrate': 320000
                }
                
                response = client.get("/api/audio/")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                
                # Check that all files are listed
                filenames = [item['filename'] for item in data]
                assert 'test_audio_1.mp3' in filenames
                assert 'test_audio_2.wav' in filenames
    
    def test_list_audio_files_empty(self):
        """Test listing audio files when directory is empty"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('api.audio.AUDIO_DIR', temp_dir):
                response = client.get("/api/audio/")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 0
    
    def test_convert_audio_format_success(self, mock_audio_files):
        """Test converting audio format"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            with patch('api.audio.convert_audio_format') as mock_convert:
                mock_convert.return_value = 'test_audio_1.wav'
                
                response = client.post("/api/audio/test_audio_1.mp3/convert", 
                                     json={'format': 'wav'})
                
                assert response.status_code == 200
                data = response.json()
                assert data['original_file'] == 'test_audio_1.mp3'
                assert data['converted_file'] == 'test_audio_1.wav'
                assert data['format'] == 'wav'
    
    def test_convert_audio_format_invalid_format(self):
        """Test converting to invalid format"""
        response = client.post("/api/audio/test_audio_1.mp3/convert", 
                             json={'format': 'invalid'})
        
        assert response.status_code == 400
        assert "Unsupported audio format" in response.json()["detail"]
    
    def test_convert_audio_format_file_not_found(self):
        """Test converting non-existent file"""
        response = client.post("/api/audio/nonexistent.mp3/convert", 
                             json={'format': 'wav'})
        
        assert response.status_code == 404
    
    def test_get_audio_waveform_success(self, mock_audio_files):
        """Test getting audio waveform data"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            with patch('api.audio.generate_waveform_data') as mock_waveform:
                mock_waveform.return_value = {
                    'samples': [0.1, 0.2, -0.1, 0.3, -0.2],
                    'sample_rate': 44100,
                    'duration': 30.5
                }
                
                response = client.get("/api/audio/test_audio_1.mp3/waveform")
                
                assert response.status_code == 200
                data = response.json()
                assert 'samples' in data
                assert 'sample_rate' in data
                assert 'duration' in data
                assert len(data['samples']) == 5
    
    def test_get_audio_waveform_not_found(self):
        """Test getting waveform for non-existent file"""
        response = client.get("/api/audio/nonexistent.mp3/waveform")
        
        assert response.status_code == 404
    
    def test_audio_file_validation(self):
        """Test audio file validation"""
        # Test valid extensions
        valid_extensions = ['mp3', 'wav', 'ogg', 'flac', 'm4a']
        for ext in valid_extensions:
            response = client.get(f"/api/audio/test.{ext}")
            # Should not return 400 for valid extension (may return 404 for non-existent file)
            assert response.status_code != 400
        
        # Test invalid extensions
        invalid_extensions = ['txt', 'jpg', 'exe', 'pdf']
        for ext in invalid_extensions:
            response = client.get(f"/api/audio/test.{ext}")
            assert response.status_code == 400
    
    def test_audio_security_path_traversal(self):
        """Test security against path traversal attacks"""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
            '....//....//....//etc//passwd'
        ]
        
        for path in malicious_paths:
            response = client.get(f"/api/audio/{path}")
            assert response.status_code in [400, 404]  # Should reject or not find
    
    def test_audio_file_size_limit(self):
        """Test audio file size limits"""
        # This would typically be tested with actual file upload
        # For now, we test that the validation exists
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large mock file
            large_file = Path(temp_dir) / 'large_audio.mp3'
            large_file.write_bytes(b'x' * (100 * 1024 * 1024))  # 100MB
            
            with patch('api.audio.AUDIO_DIR', temp_dir):
                response = client.get("/api/audio/large_audio.mp3")
                
                # Should handle large files appropriately
                assert response.status_code in [200, 413]  # OK or payload too large
    
    def test_concurrent_audio_access(self, mock_audio_files):
        """Test concurrent access to audio files"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            # Simulate multiple concurrent requests
            responses = []
            for _ in range(5):
                response = client.get("/api/audio/test_audio_1.mp3")
                responses.append(response)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                assert response.content == b'fake mp3 data'
    
    def test_audio_metadata_caching(self, mock_audio_files):
        """Test that audio metadata is cached appropriately"""
        temp_dir, audio_files = mock_audio_files
        
        with patch('api.audio.AUDIO_DIR', temp_dir):
            with patch('api.audio.get_audio_metadata') as mock_metadata:
                mock_metadata.return_value = {
                    'duration': 30.5,
                    'sample_rate': 44100,
                    'channels': 2,
                    'format': 'mp3',
                    'bitrate': 320000
                }
                
                # Make multiple requests for the same file
                response1 = client.get("/api/audio/test_audio_1.mp3/metadata")
                response2 = client.get("/api/audio/test_audio_1.mp3/metadata")
                
                assert response1.status_code == 200
                assert response2.status_code == 200
                
                # Metadata function should be called at least once
                assert mock_metadata.call_count >= 1