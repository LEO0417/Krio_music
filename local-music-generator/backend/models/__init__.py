"""
Models package for the Local Music Generator.

This package contains all model-related functionality including:
- Model management and lifecycle
- Model configuration management
- Model downloading and caching
- Resource monitoring
- Notification system
"""

from .model_manager import ModelManager, ModelStatus, ModelInfo, model_manager
from .model_config import ModelConfig, ModelConfigManager, config_manager
from .model_downloader import ModelDownloader, DownloadProgress, downloader
from .resource_monitor import ResourceMonitor, resource_monitor
from .notification_system import NotificationSystem, notification_system
from .music_generator import MusicGenerator, GenerationRequest, GenerationStatus, PromptProcessor, ParameterValidator, music_generator

__all__ = [
    # Model Management
    'ModelManager',
    'ModelStatus', 
    'ModelInfo',
    'model_manager',
    
    # Model Configuration
    'ModelConfig',
    'ModelConfigManager',
    'config_manager',
    
    # Model Downloading
    'ModelDownloader',
    'DownloadProgress', 
    'downloader',
    
    # Resource Monitoring
    'ResourceMonitor',
    'resource_monitor',
    
    # Notifications
    'NotificationSystem',
    'notification_system'
]