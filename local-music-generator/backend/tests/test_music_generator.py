"""
Test suite for Music Generator core functionality

This test suite verifies the music generation core functionality including:
1. Music generation processor
2. Prompt text processing and validation
3. Parameter validation and processing
4. Generation request management
"""
import pytest
import asyncio
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from models.music_generator import (
    MusicGenerator, 
    PromptProcessor, 
    ParameterValidator,
    GenerationRequest,
    GenerationStatus,
    music_generator
)
from api.errors import ModelInferenceError, ResourceLimitExceededError


class TestPromptProcessor:
    """Test prompt text processing functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.processor = PromptProcessor()
    
    def test_validate_prompt_valid(self):
        """Test prompt validation with valid prompts"""
        valid_prompts = [
            "peaceful piano music",
            "upbeat electronic dance music with synthesizers",
            "classical violin and piano duet",
            "jazz saxophone solo with drums"
        ]
        
        for prompt in valid_prompts:
            errors = self.processor.validate_prompt(prompt)
            assert len(errors) == 0, f"Valid prompt '{prompt}' should not have errors: {errors}"
    
    def test_validate_prompt_invalid(self):
        """Test prompt validation with invalid prompts"""
        invalid_cases = [
            ("", "提示文本不能为空"),
            ("   ", "提示文本不能为空"),
            ("ab", "提示文本太短"),
            ("x" * 501, "提示文本太长")
        ]
        
        for prompt, expected_error_type in invalid_cases:
            errors = self.processor.validate_prompt(prompt)
            assert len(errors) > 0, f"Invalid prompt '{prompt}' should have errors"
            assert any(expected_error_type in error for error in errors), \
                f"Expected error type '{expected_error_type}' not found in {errors}"
    
    def test_enhance_prompt(self):
        """Test prompt enhancement functionality"""
        test_cases = [
            ("piano", "music with melodic and harmonious piano"),
            ("happy jazz", "music with happy jazz"),
            ("classical violin", "music with classical violin"),
            ("", "")
        ]
        
        for original, expected_pattern in test_cases:
            enhanced = self.processor.enhance_prompt(original)
            if original:
                assert len(enhanced) >= len(original), "Enhanced prompt should not be shorter"
                assert "music" in enhanced.lower(), "Enhanced prompt should contain 'music'"
            else:
                assert enhanced == original, "Empty prompt should remain empty"
    
    def test_detect_styles(self):
        """Test music style detection"""
        test_cases = [
            ("classical piano symphony", ["classical"]),
            ("jazz saxophone and blues guitar", ["jazz"]),
            ("electronic techno house music", ["electronic"]),
            ("rock guitar with heavy drums", ["rock"]),
            ("peaceful ambient meditation", ["ambient"]),
            ("folk acoustic country", ["folk"])
        ]
        
        for prompt, expected_styles in test_cases:
            detected = self.processor._detect_styles(prompt)
            for style in expected_styles:
                assert style in detected, f"Style '{style}' should be detected in '{prompt}'"
    
    def test_detect_moods(self):
        """Test mood detection"""
        test_cases = [
            ("happy cheerful upbeat music", ["happy"]),
            ("sad melancholy emotional piece", ["sad"]),
            ("calm peaceful relaxing sounds", ["calm"]),
            ("energetic dynamic powerful beat", ["energetic"]),
            ("mysterious dark haunting melody", ["mysterious"]),
            ("romantic love tender song", ["romantic"])
        ]
        
        for prompt, expected_moods in test_cases:
            detected = self.processor._detect_moods(prompt)
            for mood in expected_moods:
                assert mood in detected, f"Mood '{mood}' should be detected in '{prompt}'"
    
    def test_detect_instruments(self):
        """Test instrument detection"""
        test_cases = [
            ("piano and violin duet", ["piano", "violin"]),
            ("guitar solo with drums", ["guitar", "drums"]),
            ("saxophone jazz with bass", ["saxophone", "bass"]),
            ("synthesizer electronic music", ["synthesizer"])
        ]
        
        for prompt, expected_instruments in test_cases:
            detected = self.processor._detect_instruments(prompt)
            for instrument in expected_instruments:
                assert instrument in detected, f"Instrument '{instrument}' should be detected in '{prompt}'"
    
    def test_get_prompt_analysis(self):
        """Test comprehensive prompt analysis"""
        prompt = "happy jazz piano with saxophone"
        analysis = self.processor.get_prompt_analysis(prompt)
        
        assert "original_prompt" in analysis
        assert "enhanced_prompt" in analysis
        assert "detected_styles" in analysis
        assert "detected_moods" in analysis
        assert "detected_instruments" in analysis
        assert "validation_errors" in analysis
        
        assert analysis["original_prompt"] == prompt
        assert len(analysis["validation_errors"]) == 0
        assert "jazz" in analysis["detected_styles"]
        assert "happy" in analysis["detected_moods"]
        assert "piano" in analysis["detected_instruments"]
        assert "saxophone" in analysis["detected_instruments"]


class TestParameterValidator:
    """Test parameter validation functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = ParameterValidator()
    
    def test_validate_valid_parameters(self):
        """Test validation with valid parameters"""
        valid_params = {
            "prompt": "test music",
            "duration": 15.0,
            "guidance_scale": 3.0,
            "temperature": 1.0,
            "top_k": 250,
            "top_p": 0.0,
            "sample_rate": 32000,
            "output_format": "wav"
        }
        
        result = self.validator.validate_parameters(valid_params)
        assert result["valid"] == True
        assert len(result["errors"]) == 0
        assert "cleaned_params" in result
        assert result["cleaned_params"]["prompt"] == "test music"
    
    def test_validate_invalid_parameters(self):
        """Test validation with invalid parameters"""
        invalid_params = {
            "prompt": "",  # Empty prompt
            "duration": -1.0,  # Invalid duration
            "guidance_scale": 20.0,  # Too high
            "temperature": -0.5,  # Too low
            "top_k": -10,  # Invalid
            "top_p": 2.0,  # Too high
            "sample_rate": 999,  # Unsupported
            "output_format": "invalid"  # Unsupported format
        }
        
        result = self.validator.validate_parameters(invalid_params)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        assert any("提示文本不能为空" in error for error in result["errors"])
    
    def test_parameter_range_clamping(self):
        """Test parameter range clamping"""
        params = {
            "prompt": "test",
            "duration": 100.0,  # Too high, should be clamped to 30.0
            "guidance_scale": 0.5,  # Too low, should be clamped to 1.0
            "temperature": 5.0,  # Too high, should be clamped to 2.0
            "top_k": 2000,  # Too high, should be clamped to 1000
            "sample_rate": 31000  # Unsupported, should use closest
        }
        
        result = self.validator.validate_parameters(params)
        assert result["valid"] == True
        assert result["cleaned_params"]["duration"] == 30.0
        assert result["cleaned_params"]["guidance_scale"] == 1.0
        assert result["cleaned_params"]["temperature"] == 2.0
        assert result["cleaned_params"]["top_k"] == 1000
        assert result["cleaned_params"]["sample_rate"] == 32000  # Closest supported
        assert len(result["warnings"]) > 0
    
    def test_default_parameter_application(self):
        """Test default parameter application"""
        minimal_params = {
            "prompt": "test music"
        }
        
        result = self.validator.validate_parameters(minimal_params)
        assert result["valid"] == True
        assert result["cleaned_params"]["duration"] == 10.0  # Default
        assert result["cleaned_params"]["guidance_scale"] == 3.0  # Default
        assert result["cleaned_params"]["temperature"] == 1.0  # Default
        assert result["cleaned_params"]["top_k"] == 250  # Default
        assert result["cleaned_params"]["top_p"] == 0.0  # Default
        assert result["cleaned_params"]["sample_rate"] == 32000  # Default
        assert len(result["applied_defaults"]) > 0


class TestGenerationRequest:
    """Test generation request functionality"""
    
    def test_request_creation(self):
        """Test generation request creation"""
        request = GenerationRequest(
            prompt="test music",
            duration=15.0,
            guidance_scale=3.0
        )
        
        assert request.prompt == "test music"
        assert request.duration == 15.0
        assert request.guidance_scale == 3.0
        assert request.status == GenerationStatus.PENDING
        assert request.progress == 0.0
        assert not request.is_cancelled()
        assert request.id is not None
    
    def test_request_to_dict(self):
        """Test request serialization"""
        request = GenerationRequest(prompt="test", duration=10.0)
        request_dict = request.to_dict()
        
        assert isinstance(request_dict, dict)
        assert "id" in request_dict
        assert "prompt" in request_dict
        assert "duration" in request_dict
        assert "status" in request_dict
        assert "progress" in request_dict
        assert "created_at" in request_dict
    
    def test_request_cancellation(self):
        """Test request cancellation"""
        request = GenerationRequest(prompt="test")
        assert not request.is_cancelled()
        
        request.cancel()
        assert request.is_cancelled()
        assert request.status == GenerationStatus.CANCELLED


class TestMusicGenerator:
    """Test music generator core functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the AUDIO_DIR setting
        self.audio_dir_patcher = patch('models.music_generator.AUDIO_DIR', self.temp_dir)
        self.audio_dir_patcher.start()
        
        # Create a fresh generator instance
        self.generator = MusicGenerator()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.audio_dir_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generator_initialization(self):
        """Test music generator initialization"""
        assert self.generator.prompt_processor is not None
        assert self.generator.parameter_validator is not None
        assert isinstance(self.generator.active_requests, dict)
        assert isinstance(self.generator.completed_requests, dict)
        assert self.generator.output_dir.exists()
    
    @patch('models.music_generator.model_manager')
    async def test_generate_music_parameter_validation_failure(self, mock_model_manager):
        """Test music generation with parameter validation failure"""
        mock_model_manager.is_ready.return_value = True
        
        with pytest.raises(ModelInferenceError) as exc_info:
            await self.generator.generate_music(
                prompt="",  # Empty prompt should fail validation
                duration=10.0
            )
        
        assert "参数验证失败" in str(exc_info.value)
    
    @patch('models.music_generator.model_manager')
    async def test_generate_music_model_not_ready(self, mock_model_manager):
        """Test music generation when model is not ready"""
        mock_model_manager.is_ready.return_value = False
        
        with pytest.raises(ModelInferenceError) as exc_info:
            await self.generator.generate_music(
                prompt="test music",
                duration=10.0
            )
        
        assert "模型未加载或不可用" in str(exc_info.value)
    
    @patch('models.music_generator.model_manager')
    async def test_generate_music_success_flow(self, mock_model_manager):
        """Test successful music generation flow"""
        mock_model_manager.is_ready.return_value = True
        
        # Mock the async generation to avoid actual model inference
        with patch.object(self.generator, '_generate_music_async', new_callable=AsyncMock) as mock_async:
            request_id = await self.generator.generate_music(
                prompt="test music",
                duration=10.0
            )
            
            assert request_id is not None
            assert request_id in self.generator.active_requests
            
            # Verify the async generation was called
            mock_async.assert_called_once()
            
            # Check request details
            request = self.generator.active_requests[request_id]
            assert request.prompt == "melodic and harmonious test music"  # Enhanced
            assert request.duration == 10.0
    
    def test_get_request_status(self):
        """Test getting request status"""
        # Test non-existent request
        status = self.generator.get_request_status("non-existent")
        assert status is None
        
        # Test existing request
        request = GenerationRequest(prompt="test")
        self.generator.active_requests[request.id] = request
        
        status = self.generator.get_request_status(request.id)
        assert status is not None
        assert status["id"] == request.id
        assert status["prompt"] == "test"
    
    def test_cancel_request(self):
        """Test request cancellation"""
        # Test cancelling non-existent request
        result = self.generator.cancel_request("non-existent")
        assert result == False
        
        # Test cancelling existing request
        request = GenerationRequest(prompt="test")
        self.generator.active_requests[request.id] = request
        
        result = self.generator.cancel_request(request.id)
        assert result == True
        assert request.is_cancelled()
    
    def test_list_requests(self):
        """Test listing requests"""
        # Add some test requests
        request1 = GenerationRequest(prompt="test1")
        request1.status = GenerationStatus.COMPLETED
        request2 = GenerationRequest(prompt="test2")
        request2.status = GenerationStatus.PROCESSING
        
        self.generator.completed_requests[request1.id] = request1
        self.generator.active_requests[request2.id] = request2
        
        # Test listing all requests
        all_requests = self.generator.list_requests()
        assert len(all_requests) == 2
        
        # Test filtering by status
        completed_requests = self.generator.list_requests(status_filter="completed")
        assert len(completed_requests) == 1
        assert completed_requests[0]["status"] == "completed"
        
        processing_requests = self.generator.list_requests(status_filter="processing")
        assert len(processing_requests) == 1
        assert processing_requests[0]["status"] == "processing"
    
    def test_get_generation_stats(self):
        """Test getting generation statistics"""
        # Add some test requests
        request1 = GenerationRequest(prompt="test1")
        request1.status = GenerationStatus.COMPLETED
        request2 = GenerationRequest(prompt="test2")
        request2.status = GenerationStatus.PROCESSING
        
        self.generator.completed_requests[request1.id] = request1
        self.generator.active_requests[request2.id] = request2
        
        stats = self.generator.get_generation_stats()
        
        assert "active_requests" in stats
        assert "completed_requests" in stats
        assert "total_requests" in stats
        assert "status_counts" in stats
        assert "model_ready" in stats
        
        assert stats["active_requests"] == 1
        assert stats["completed_requests"] == 1
        assert stats["total_requests"] == 2
        assert "completed" in stats["status_counts"]
        assert "processing" in stats["status_counts"]


class TestMusicGeneratorIntegration:
    """Integration tests for music generator"""
    
    @patch('models.music_generator.model_manager')
    def test_global_music_generator_instance(self, mock_model_manager):
        """Test that the global music generator instance is properly initialized"""
        from models.music_generator import music_generator
        
        assert music_generator is not None
        assert isinstance(music_generator, MusicGenerator)
        assert music_generator.prompt_processor is not None
        assert music_generator.parameter_validator is not None


if __name__ == "__main__":
    # Run basic tests
    print("Running Music Generator Tests...")
    
    # Test prompt processor
    print("\n=== Testing Prompt Processor ===")
    prompt_test = TestPromptProcessor()
    prompt_test.setup_method()
    
    try:
        prompt_test.test_validate_prompt_valid()
        print("✅ Prompt validation (valid) test passed")
    except Exception as e:
        print(f"❌ Prompt validation (valid) test failed: {e}")
    
    try:
        prompt_test.test_validate_prompt_invalid()
        print("✅ Prompt validation (invalid) test passed")
    except Exception as e:
        print(f"❌ Prompt validation (invalid) test failed: {e}")
    
    try:
        prompt_test.test_enhance_prompt()
        print("✅ Prompt enhancement test passed")
    except Exception as e:
        print(f"❌ Prompt enhancement test failed: {e}")
    
    try:
        prompt_test.test_detect_styles()
        print("✅ Style detection test passed")
    except Exception as e:
        print(f"❌ Style detection test failed: {e}")
    
    try:
        prompt_test.test_get_prompt_analysis()
        print("✅ Prompt analysis test passed")
    except Exception as e:
        print(f"❌ Prompt analysis test failed: {e}")
    
    # Test parameter validator
    print("\n=== Testing Parameter Validator ===")
    param_test = TestParameterValidator()
    param_test.setup_method()
    
    try:
        param_test.test_validate_valid_parameters()
        print("✅ Parameter validation (valid) test passed")
    except Exception as e:
        print(f"❌ Parameter validation (valid) test failed: {e}")
    
    try:
        param_test.test_validate_invalid_parameters()
        print("✅ Parameter validation (invalid) test passed")
    except Exception as e:
        print(f"❌ Parameter validation (invalid) test failed: {e}")
    
    try:
        param_test.test_parameter_range_clamping()
        print("✅ Parameter range clamping test passed")
    except Exception as e:
        print(f"❌ Parameter range clamping test failed: {e}")
    
    try:
        param_test.test_default_parameter_application()
        print("✅ Default parameter application test passed")
    except Exception as e:
        print(f"❌ Default parameter application test failed: {e}")
    
    # Test generation request
    print("\n=== Testing Generation Request ===")
    request_test = TestGenerationRequest()
    
    try:
        request_test.test_request_creation()
        print("✅ Request creation test passed")
    except Exception as e:
        print(f"❌ Request creation test failed: {e}")
    
    try:
        request_test.test_request_to_dict()
        print("✅ Request serialization test passed")
    except Exception as e:
        print(f"❌ Request serialization test failed: {e}")
    
    try:
        request_test.test_request_cancellation()
        print("✅ Request cancellation test passed")
    except Exception as e:
        print(f"❌ Request cancellation test failed: {e}")
    
    print("\nAll tests completed!")