"""
Configuration settings for the Local Music Generator application.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

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