"""
Test suite for Transformers library integration

This test suite verifies that the transformers library integration is working correctly,
including model configuration, download functionality, and model management.
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from models.model_manager import model_manager, ModelStatus
from models.model_downloader import downloader
from models.model_config import config_manager, ModelConfig


class TestTransformersIntegration:
    """Test transformers library integration"""
    
    def test_model_config_manager(self):
        """Test model configuration management"""
        # Test getting default config
        config = config_manager.get_default_config()
        assert config is not None
        assert config.name == "MusicGen Small"
        assert config.model_id == "facebook/musicgen-small"
        
        # Test listing configs
        configs = config_manager.list_configs()
        assert "preset_configs" in configs
        assert "user_configs" in configs
        assert len(configs["preset_configs"]) >= 3  # small, medium, large
        
        # Test config validation
        errors = config_manager.validate_config(config)
        assert len(errors) == 0, f"Config validation failed: {errors}"
    
    def test_model_downloader(self):
        """Test model download functionality"""
        # Test cache check
        is_cached = downloader.is_model_cached("facebook/musicgen-small")
        assert isinstance(is_cached, bool)
        
        # Test cache summary
        summary = downloader.get_cache_summary()
        assert "total_models" in summary
        assert "total_size_mb" in summary
        assert "models" in summary
        assert isinstance(summary["total_models"], int)
    
    def test_model_manager_initialization(self):
        """Test model manager initialization"""
        # Test getting model status
        status = model_manager.get_model_status()
        assert "status" in status
        assert "name" in status
        assert "device" in status
        assert status["status"] in [s.value for s in ModelStatus]
        
        # Test readiness check
        is_ready = model_manager.is_ready()
        assert isinstance(is_ready, bool)
    
    @pytest.mark.asyncio
    async def test_model_manager_health_check(self):
        """Test model manager health check"""
        health = await model_manager.health_check()
        assert "model_loaded" in health
        assert "model_status" in health
        assert "device" in health
        assert "timestamp" in health
        assert isinstance(health["model_loaded"], bool)
    
    @pytest.mark.asyncio
    async def test_resource_monitoring(self):
        """Test resource monitoring functionality"""
        resources = await model_manager.get_resource_info()
        assert "system" in resources
        assert "model" in resources
        
        system_info = resources["system"]
        assert "cpu_percent" in system_info
        assert "memory_total_mb" in system_info
        assert "memory_used_mb" in system_info
        assert "memory_percent" in system_info
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test valid config
        valid_config = ModelConfig(
            name="Test Config",
            model_id="facebook/musicgen-small",
            cache_dir="/tmp/test",
            max_length=15,
            sample_rate=32000,
            guidance_scale=3.0,
            temperature=1.0,
            top_k=250,
            top_p=0.0
        )
        errors = config_manager.validate_config(valid_config)
        assert len(errors) == 0
        
        # Test invalid config
        invalid_config = ModelConfig(
            name="",  # Empty name
            model_id="",  # Empty model_id
            cache_dir="",  # Empty cache_dir
            max_length=-1,  # Invalid length
            sample_rate=999,  # Invalid sample rate
            guidance_scale=20,  # Invalid guidance scale
            temperature=-1,  # Invalid temperature
            top_k=-1,  # Invalid top_k
            top_p=2.0  # Invalid top_p
        )
        errors = config_manager.validate_config(invalid_config)
        assert len(errors) > 0
    
    def test_model_config_serialization(self):
        """Test model config serialization"""
        config = config_manager.get_default_config()
        
        # Test to_dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "name" in config_dict
        assert "model_id" in config_dict
        
        # Test from_dict
        restored_config = ModelConfig.from_dict(config_dict)
        assert restored_config.name == config.name
        assert restored_config.model_id == config.model_id
        assert restored_config.max_length == config.max_length


if __name__ == "__main__":
    # Run basic tests
    test_suite = TestTransformersIntegration()
    
    print("Running Transformers Integration Tests...")
    
    try:
        test_suite.test_model_config_manager()
        print("✅ Model config manager test passed")
    except Exception as e:
        print(f"❌ Model config manager test failed: {e}")
    
    try:
        test_suite.test_model_downloader()
        print("✅ Model downloader test passed")
    except Exception as e:
        print(f"❌ Model downloader test failed: {e}")
    
    try:
        test_suite.test_model_manager_initialization()
        print("✅ Model manager initialization test passed")
    except Exception as e:
        print(f"❌ Model manager initialization test failed: {e}")
    
    try:
        asyncio.run(test_suite.test_model_manager_health_check())
        print("✅ Model manager health check test passed")
    except Exception as e:
        print(f"❌ Model manager health check test failed: {e}")
    
    try:
        asyncio.run(test_suite.test_resource_monitoring())
        print("✅ Resource monitoring test passed")
    except Exception as e:
        print(f"❌ Resource monitoring test failed: {e}")
    
    try:
        test_suite.test_config_validation()
        print("✅ Config validation test passed")
    except Exception as e:
        print(f"❌ Config validation test failed: {e}")
    
    try:
        test_suite.test_model_config_serialization()
        print("✅ Model config serialization test passed")
    except Exception as e:
        print(f"❌ Model config serialization test failed: {e}")
    
    print("\nAll tests completed!")