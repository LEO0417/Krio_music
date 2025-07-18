"""
Configuration settings for the Local Music Generator application.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
AUDIO_DIR = DATA_DIR / "audio"

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# API settings
API_V1_PREFIX = "/api"
DEBUG = True
RELOAD = True

# CORS settings
CORS_ORIGINS = [
    "http://localhost:3000",  # Frontend development server
    "http://localhost:8000",  # Backend when serving static files
]

# Model settings
DEFAULT_MODEL = "facebook/musicgen-small"
MODEL_SETTINGS = {
    "use_gpu": True,
    "auto_load": True,
    "version": "latest",
    "cache_enabled": True,
    "max_cache_size_gb": 10.0,  # Maximum cache size in GB
    "supported_models": [
        "facebook/musicgen-small",
        "facebook/musicgen-medium", 
        "facebook/musicgen-large"
    ],
    "model_configs": {
        "facebook/musicgen-small": {
            "max_length": 30,
            "guidance_scale": 3.0,
            "temperature": 1.0,
            "top_k": 250,
            "top_p": 0.0,
            "typical_p": 1.0,
            "classifier_free_guidance": True,
            "use_cache": True,
            "pad_token_id": None,
            "eos_token_id": None,
            "decoder_start_token_id": None,
            "forced_decoder_ids": None,
            "suppress_tokens": None,
            "begin_suppress_tokens": None,
            "forced_ac_decoder_ids": None,
            "min_memory_gb": 2.0,
            "recommended_memory_gb": 4.0
        },
        "facebook/musicgen-medium": {
            "max_length": 30,
            "guidance_scale": 3.0,
            "temperature": 1.0,
            "top_k": 250,
            "top_p": 0.0,
            "typical_p": 1.0,
            "classifier_free_guidance": True,
            "use_cache": True,
            "pad_token_id": None,
            "eos_token_id": None,
            "decoder_start_token_id": None,
            "forced_decoder_ids": None,
            "suppress_tokens": None,
            "begin_suppress_tokens": None,
            "forced_ac_decoder_ids": None,
            "min_memory_gb": 6.0,
            "recommended_memory_gb": 8.0
        },
        "facebook/musicgen-large": {
            "max_length": 30,
            "guidance_scale": 3.0,
            "temperature": 1.0,
            "top_k": 250,
            "top_p": 0.0,
            "typical_p": 1.0,
            "classifier_free_guidance": True,
            "use_cache": True,
            "pad_token_id": None,
            "eos_token_id": None,
            "decoder_start_token_id": None,
            "forced_decoder_ids": None,
            "suppress_tokens": None,
            "begin_suppress_tokens": None,
            "forced_ac_decoder_ids": None,
            "min_memory_gb": 12.0,
            "recommended_memory_gb": 16.0
        }
    }
}

# Audio settings
AUDIO_SETTINGS = {
    "default_format": "mp3",
    "max_duration": 30,  # seconds
    "sample_rate": 44100,
}

# System settings
SYSTEM_SETTINGS = {
    "max_memory_usage": 0.8,  # 80% of available memory
    "log_level": "info",
}

# UI settings
UI_SETTINGS = {
    "theme": "system",
    "animations": True,
    "history_size": 50,
}

def get_settings() -> Dict[str, Any]:
    """
    Get all application settings.
    
    Returns:
        Dict[str, Any]: Dictionary containing all settings
    """
    return {
        "model": MODEL_SETTINGS,
        "audio": AUDIO_SETTINGS,
        "system": SYSTEM_SETTINGS,
        "ui": UI_SETTINGS,
    }

def get_model_config(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Optional[Dict[str, Any]]: Model configuration or None if not found
    """
    return MODEL_SETTINGS.get("model_configs", {}).get(model_name)

def is_model_supported(model_name: str) -> bool:
    """
    Check if a model is supported.
    
    Args:
        model_name: Name of the model
        
    Returns:
        bool: True if model is supported
    """
    return model_name in MODEL_SETTINGS.get("supported_models", [])

def get_supported_models() -> List[str]:
    """
    Get list of supported models.
    
    Returns:
        List[str]: List of supported model names
    """
    return MODEL_SETTINGS.get("supported_models", [])

def validate_model_requirements(model_name: str) -> Dict[str, Any]:
    """
    Validate system requirements for a model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dict[str, Any]: Validation results
    """
    import psutil
    
    config = get_model_config(model_name)
    if not config:
        return {
            "valid": False,
            "error": f"Model {model_name} not supported"
        }
    
    # Check memory requirements
    system_memory_gb = psutil.virtual_memory().total / (1024 ** 3)
    min_memory_gb = config.get("min_memory_gb", 2.0)
    recommended_memory_gb = config.get("recommended_memory_gb", 4.0)
    
    validation = {
        "valid": True,
        "model_name": model_name,
        "system_memory_gb": round(system_memory_gb, 1),
        "min_memory_gb": min_memory_gb,
        "recommended_memory_gb": recommended_memory_gb,
        "meets_minimum": system_memory_gb >= min_memory_gb,
        "meets_recommended": system_memory_gb >= recommended_memory_gb,
        "warnings": [],
        "errors": []
    }
    
    if not validation["meets_minimum"]:
        validation["valid"] = False
        validation["errors"].append(
            f"Insufficient memory: {system_memory_gb:.1f}GB < {min_memory_gb:.1f}GB required"
        )
    elif not validation["meets_recommended"]:
        validation["warnings"].append(
            f"Memory below recommended: {system_memory_gb:.1f}GB < {recommended_memory_gb:.1f}GB recommended"
        )
    
    return validation