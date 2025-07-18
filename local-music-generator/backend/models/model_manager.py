"""
模型管理器 (Model Manager) 

这个模块实现了MusicGen模型的完整生命周期管理，包括：
1. 模型的下载、加载和初始化
2. 模型状态的实时监控和管理
3. 模型推理资源的优化和监控
4. 错误处理和恢复机制

技术说明：
- 使用 Transformers 库加载 Facebook 的 MusicGen 模型
- 支持GPU和CPU推理
- 实现模型状态缓存和资源监控
- 提供异步接口以避免阻塞主线程
"""
import os
import gc
import time
import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, Union, List
from datetime import datetime
from pathlib import Path
import json

import torch
import psutil
from transformers import MusicgenForConditionalGeneration, AutoProcessor
from accelerate import init_empty_weights, infer_auto_device_map, load_checkpoint_and_dispatch

from config.settings import (
    MODELS_DIR, 
    DEFAULT_MODEL, 
    MODEL_SETTINGS,
    SYSTEM_SETTINGS,
    get_model_config,
    is_model_supported,
    get_supported_models,
    validate_model_requirements
)
from api.errors import ModelLoadError, ModelInferenceError, ResourceLimitExceededError

# Configure logging
logger = logging.getLogger("model_manager")

class ModelStatus(Enum):
    """模型状态枚举"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    UNLOADING = "unloading"

class ModelInfo:
    """模型信息类"""
    def __init__(self):
        self.name: str = ""
        self.status: ModelStatus = ModelStatus.NOT_LOADED
        self.loaded_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.device: str = "cpu"
        self.memory_usage: int = 0  # MB
        self.inference_count: int = 0
        self.last_inference_time: Optional[datetime] = None
        self.model_size: int = 0  # MB
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "status": self.status.value,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "error_message": self.error_message,
            "device": self.device,
            "memory_usage_mb": self.memory_usage,
            "inference_count": self.inference_count,
            "last_inference_time": self.last_inference_time.isoformat() if self.last_inference_time else None,
            "model_size_mb": self.model_size
        }

class ModelManager:
    """
    MusicGen模型管理器
    
    负责管理MusicGen模型的完整生命周期，包括加载、状态监控、资源管理等。
    """
    
    def __init__(self):
        """初始化模型管理器"""
        self.model: Optional[MusicgenForConditionalGeneration] = None
        self.processor: Optional[AutoProcessor] = None
        self.model_info = ModelInfo()
        self._lock = asyncio.Lock()
        
        # 配置参数
        self.use_gpu = MODEL_SETTINGS.get("use_gpu", True) and torch.cuda.is_available()
        self.auto_load = MODEL_SETTINGS.get("auto_load", True)
        self.max_memory_usage = SYSTEM_SETTINGS.get("max_memory_usage", 0.8)
        
        # 初始化模型目录
        self.models_dir = Path(MODELS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Model Manager initialized - GPU available: {torch.cuda.is_available()}, Use GPU: {self.use_gpu}")
    
    def _check_system_resources(self) -> bool:
        """
        检查系统资源是否足够加载模型
        
        Returns:
            bool: 如果资源足够返回True，否则返回False
        """
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent / 100.0
        
        if memory_usage_percent > self.max_memory_usage:
            logger.warning(f"Memory usage too high: {memory_usage_percent:.1%} > {self.max_memory_usage:.1%}")
            return False
            
        # 检查可用磁盘空间（模型文件大小估计：约2GB）
        disk = psutil.disk_usage(str(self.models_dir))
        free_space_gb = disk.free / (1024 ** 3)
        
        if free_space_gb < 5.0:  # 需要至少5GB空闲空间
            logger.warning(f"Insufficient disk space: {free_space_gb:.1f}GB < 5.0GB")
            return False
            
        return True
    
    def _get_model_device(self) -> str:
        """
        确定模型使用的设备
        
        Returns:
            str: 设备名称 ("cuda" 或 "cpu")
        """
        if self.use_gpu and torch.cuda.is_available():
            # 检查GPU内存
            try:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                gpu_memory_gb = gpu_memory / (1024 ** 3)
                
                if gpu_memory_gb >= 4.0:  # 需要至少4GB GPU内存
                    return "cuda"
                else:
                    logger.warning(f"GPU memory insufficient: {gpu_memory_gb:.1f}GB < 4.0GB, using CPU")
            except Exception as e:
                logger.warning(f"Error checking GPU memory: {e}, using CPU")
        
        return "cpu"
    
    async def load_model(self, model_name: str = None) -> bool:
        """
        异步加载模型
        
        Args:
            model_name: 模型名称，默认使用DEFAULT_MODEL
            
        Returns:
            bool: 成功返回True，失败返回False
            
        Raises:
            ModelLoadError: 模型加载失败时抛出
            ResourceLimitExceededError: 资源不足时抛出
        """
        async with self._lock:
            try:
                if self.model_info.status == ModelStatus.LOADING:
                    logger.warning("Model is already being loaded")
                    return False
                
                if self.model_info.status == ModelStatus.LOADED:
                    logger.info("Model is already loaded")
                    return True
                
                model_name = model_name or DEFAULT_MODEL
                
                # 验证模型是否支持
                if not is_model_supported(model_name):
                    raise ModelLoadError(f"Model {model_name} is not supported. Supported models: {get_supported_models()}")
                
                # 验证系统要求
                validation = validate_model_requirements(model_name)
                if not validation["valid"]:
                    raise ResourceLimitExceededError(f"Model requirements not met: {validation['errors']}")
                
                if validation["warnings"]:
                    for warning in validation["warnings"]:
                        logger.warning(warning)
                
                self.model_info.name = model_name
                self.model_info.status = ModelStatus.LOADING
                self.model_info.error_message = None
                
                logger.info(f"Starting to load model: {model_name}")
                
                # 检查系统资源
                if not self._check_system_resources():
                    raise ResourceLimitExceededError("Insufficient system resources to load model")
                
                # 确定设备
                device = self._get_model_device()
                self.model_info.device = device
                
                logger.info(f"Loading model on device: {device}")
                
                # 在后台线程中加载模型以避免阻塞
                await asyncio.to_thread(self._load_model_sync, model_name, device)
                
                # 更新模型信息
                self.model_info.status = ModelStatus.LOADED
                self.model_info.loaded_at = datetime.now()
                self.model_info.memory_usage = self._get_model_memory_usage()
                
                logger.info(f"Model {model_name} loaded successfully on {device}")
                return True
                
            except Exception as e:
                self.model_info.status = ModelStatus.ERROR
                self.model_info.error_message = str(e)
                logger.error(f"Failed to load model {model_name}: {e}")
                
                # 清理部分加载的资源
                await self._cleanup_model()
                
                if isinstance(e, (ModelLoadError, ResourceLimitExceededError)):
                    raise
                else:
                    raise ModelLoadError(f"Unexpected error loading model: {e}")
    
    def _get_model_cache_path(self, model_name: str) -> Path:
        """
        获取模型缓存路径
        
        Args:
            model_name: 模型名称
            
        Returns:
            Path: 模型缓存路径
        """
        # 将模型名称转换为安全的文件名
        safe_name = model_name.replace("/", "_").replace("\\", "_")
        return self.models_dir / safe_name
    
    def _is_model_cached(self, model_name: str) -> bool:
        """
        检查模型是否已缓存
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 如果模型已缓存返回True
        """
        cache_path = self._get_model_cache_path(model_name)
        # 检查必要的模型文件是否存在
        required_files = ["config.json", "pytorch_model.bin", "tokenizer.json"]
        
        if not cache_path.exists():
            return False
            
        for file_name in required_files:
            if not (cache_path / file_name).exists():
                return False
                
        return True
    
    def _load_model_sync(self, model_name: str, device: str):
        """
        同步加载模型（在后台线程中运行）
        
        Args:
            model_name: 模型名称
            device: 目标设备
        """
        try:
            cache_path = self._get_model_cache_path(model_name)
            
            # 检查模型是否已缓存
            if self._is_model_cached(model_name):
                logger.info(f"Loading model from cache: {cache_path}")
                model_path = str(cache_path)
            else:
                logger.info(f"Model not cached, downloading from Hugging Face: {model_name}")
                model_path = model_name
                
                # 确保缓存目录存在
                cache_path.mkdir(parents=True, exist_ok=True)
            
            # 加载处理器
            logger.info("Loading processor...")
            self.processor = AutoProcessor.from_pretrained(
                model_path,
                cache_dir=str(cache_path) if not self._is_model_cached(model_name) else None
            )
            
            # 加载模型
            logger.info("Loading model...")
            if device == "cuda":
                # GPU加载，使用半精度以节省内存
                self.model = MusicgenForConditionalGeneration.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                    cache_dir=str(cache_path) if not self._is_model_cached(model_name) else None
                )
            else:
                # CPU加载
                self.model = MusicgenForConditionalGeneration.from_pretrained(
                    model_path,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    cache_dir=str(cache_path) if not self._is_model_cached(model_name) else None
                )
                self.model = self.model.to(device)
            
            # 设置为推理模式
            self.model.eval()
            
            # 计算模型大小
            self.model_info.model_size = self._calculate_model_size()
            
            # 如果是首次下载，保存模型到缓存
            if not self._is_model_cached(model_name):
                self._save_model_to_cache(model_name, cache_path)
            
        except Exception as e:
            logger.error(f"Error in _load_model_sync: {e}")
            raise ModelLoadError(f"Failed to load model components: {e}")
    
    def _save_model_to_cache(self, model_name: str, cache_path: Path):
        """
        保存模型到缓存
        
        Args:
            model_name: 模型名称
            cache_path: 缓存路径
        """
        try:
            logger.info(f"Saving model to cache: {cache_path}")
            
            # 保存模型
            if self.model is not None:
                self.model.save_pretrained(str(cache_path))
            
            # 保存处理器
            if self.processor is not None:
                self.processor.save_pretrained(str(cache_path))
            
            # 创建缓存信息文件
            cache_info = {
                "model_name": model_name,
                "cached_at": datetime.now().isoformat(),
                "model_size_mb": self.model_info.model_size,
                "device": self.model_info.device
            }
            
            with open(cache_path / "cache_info.json", "w") as f:
                json.dump(cache_info, f, indent=2)
            
            logger.info("Model saved to cache successfully")
            
        except Exception as e:
            logger.warning(f"Failed to save model to cache: {e}")
    
    def get_cached_models(self) -> List[Dict[str, Any]]:
        """
        获取已缓存的模型列表
        
        Returns:
            List[Dict[str, Any]]: 缓存的模型信息列表
        """
        cached_models = []
        
        if not self.models_dir.exists():
            return cached_models
        
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                cache_info_path = model_dir / "cache_info.json"
                if cache_info_path.exists():
                    try:
                        with open(cache_info_path, "r") as f:
                            cache_info = json.load(f)
                        
                        # 计算缓存大小
                        cache_size = sum(
                            f.stat().st_size for f in model_dir.rglob("*") if f.is_file()
                        ) // (1024 * 1024)  # 转换为MB
                        
                        cache_info["cache_size_mb"] = cache_size
                        cache_info["cache_path"] = str(model_dir)
                        cached_models.append(cache_info)
                        
                    except Exception as e:
                        logger.warning(f"Failed to read cache info for {model_dir}: {e}")
        
        return cached_models
    
    def clear_model_cache(self, model_name: str = None) -> bool:
        """
        清理模型缓存
        
        Args:
            model_name: 要清理的模型名称，为None时清理所有缓存
            
        Returns:
            bool: 清理是否成功
        """
        try:
            if model_name:
                # 清理指定模型的缓存
                cache_path = self._get_model_cache_path(model_name)
                if cache_path.exists():
                    import shutil
                    shutil.rmtree(str(cache_path))
                    logger.info(f"Cleared cache for model: {model_name}")
                else:
                    logger.info(f"No cache found for model: {model_name}")
            else:
                # 清理所有缓存
                if self.models_dir.exists():
                    import shutil
                    shutil.rmtree(str(self.models_dir))
                    self.models_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("Cleared all model caches")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear model cache: {e}")
            return False
    
    def _calculate_model_size(self) -> int:
        """
        计算模型大小（MB）
        
        Returns:
            int: 模型大小（MB）
        """
        if not self.model:
            return 0
            
        total_params = sum(p.numel() for p in self.model.parameters())
        # 估算：每个参数4字节（float32）或2字节（float16）
        bytes_per_param = 2 if self.model.dtype == torch.float16 else 4
        model_size_bytes = total_params * bytes_per_param
        return model_size_bytes // (1024 * 1024)  # 转换为MB
    
    def _get_model_memory_usage(self) -> int:
        """
        获取模型当前内存使用量（MB）
        
        Returns:
            int: 内存使用量（MB）
        """
        if not self.model:
            return 0
            
        if self.model_info.device == "cuda":
            try:
                return torch.cuda.memory_allocated() // (1024 * 1024)
            except:
                return 0
        else:
            # CPU内存使用量估算
            process = psutil.Process()
            return process.memory_info().rss // (1024 * 1024)
    
    async def unload_model(self) -> bool:
        """
        卸载模型以释放资源
        
        Returns:
            bool: 成功返回True
        """
        async with self._lock:
            try:
                if self.model_info.status == ModelStatus.NOT_LOADED:
                    logger.info("Model is not loaded")
                    return True
                
                self.model_info.status = ModelStatus.UNLOADING
                logger.info("Unloading model...")
                
                await self._cleanup_model()
                
                self.model_info.status = ModelStatus.NOT_LOADED
                self.model_info.loaded_at = None
                self.model_info.memory_usage = 0
                self.model_info.error_message = None
                
                logger.info("Model unloaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error unloading model: {e}")
                self.model_info.status = ModelStatus.ERROR
                self.model_info.error_message = str(e)
                return False
    
    async def _cleanup_model(self):
        """清理模型资源"""
        try:
            if self.model is not None:
                del self.model
                self.model = None
            
            if self.processor is not None:
                del self.processor
                self.processor = None
            
            # 强制垃圾回收
            gc.collect()
            
            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        except Exception as e:
            logger.warning(f"Error during model cleanup: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        获取模型状态信息
        
        Returns:
            Dict[str, Any]: 模型状态信息
        """
        # 更新实时内存使用量
        if self.model_info.status == ModelStatus.LOADED:
            self.model_info.memory_usage = self._get_model_memory_usage()
        
        return self.model_info.to_dict()
    
    def is_ready(self) -> bool:
        """
        检查模型是否准备好进行推理
        
        Returns:
            bool: 模型是否已加载并准备就绪
        """
        return (
            self.model_info.status == ModelStatus.LOADED and 
            self.model is not None and 
            self.processor is not None
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        执行模型健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_info = {
            "model_loaded": self.is_ready(),
            "model_status": self.model_info.status.value,
            "device": self.model_info.device,
            "memory_usage_mb": self.model_info.memory_usage,
            "system_memory_percent": psutil.virtual_memory().percent,
            "timestamp": datetime.now().isoformat()
        }
        
        if torch.cuda.is_available():
            try:
                health_info["gpu_memory_allocated_mb"] = torch.cuda.memory_allocated() // (1024 * 1024)
                health_info["gpu_memory_reserved_mb"] = torch.cuda.memory_reserved() // (1024 * 1024)
            except:
                pass
        
        return health_info
    
    def record_inference(self):
        """记录一次推理调用"""
        self.model_info.inference_count += 1
        self.model_info.last_inference_time = datetime.now()
    
    async def get_resource_info(self) -> Dict[str, Any]:
        """
        获取详细的资源使用信息
        
        Returns:
            Dict[str, Any]: 资源使用信息
        """
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.models_dir))
        
        resource_info = {
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_total_mb": memory.total // (1024 * 1024),
                "memory_used_mb": memory.used // (1024 * 1024),
                "memory_percent": memory.percent,
                "disk_total_gb": disk.total // (1024 ** 3),
                "disk_used_gb": disk.used // (1024 ** 3),
                "disk_free_gb": disk.free // (1024 ** 3),
                "disk_percent": disk.percent
            },
            "model": self.get_model_status()
        }
        
        if torch.cuda.is_available():
            try:
                gpu_props = torch.cuda.get_device_properties(0)
                resource_info["gpu"] = {
                    "name": gpu_props.name,
                    "total_memory_mb": gpu_props.total_memory // (1024 * 1024),
                    "allocated_memory_mb": torch.cuda.memory_allocated() // (1024 * 1024),
                    "reserved_memory_mb": torch.cuda.memory_reserved() // (1024 * 1024),
                    "utilization_percent": 0  # 这需要额外的库来获取
                }
            except Exception as e:
                resource_info["gpu"] = {"error": str(e)}
        
        return resource_info
    
    def get_model_configuration(self, model_name: str = None) -> Dict[str, Any]:
        """
        获取模型配置信息
        
        Args:
            model_name: 模型名称，默认使用当前加载的模型
            
        Returns:
            Dict[str, Any]: 模型配置信息
        """
        model_name = model_name or self.model_info.name or DEFAULT_MODEL
        
        config = get_model_config(model_name)
        if not config:
            return {"error": f"No configuration found for model {model_name}"}
        
        return {
            "model_name": model_name,
            "supported": is_model_supported(model_name),
            "config": config,
            "validation": validate_model_requirements(model_name),
            "cached": self._is_model_cached(model_name),
            "cache_path": str(self._get_model_cache_path(model_name))
        }
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        cached_models = self.get_cached_models()
        
        total_cache_size = sum(model.get("cache_size_mb", 0) for model in cached_models)
        max_cache_size_mb = MODEL_SETTINGS.get("max_cache_size_gb", 10.0) * 1024
        
        return {
            "cache_enabled": MODEL_SETTINGS.get("cache_enabled", True),
            "cache_directory": str(self.models_dir),
            "cached_models_count": len(cached_models),
            "total_cache_size_mb": total_cache_size,
            "max_cache_size_mb": max_cache_size_mb,
            "cache_usage_percent": (total_cache_size / max_cache_size_mb * 100) if max_cache_size_mb > 0 else 0,
            "cached_models": cached_models
        }
    
    def get_all_model_info(self) -> Dict[str, Any]:
        """
        获取所有模型相关信息
        
        Returns:
            Dict[str, Any]: 综合模型信息
        """
        return {
            "current_model": self.get_model_status(),
            "supported_models": get_supported_models(),
            "cache_statistics": self.get_cache_statistics(),
            "system_requirements": {
                model: validate_model_requirements(model) 
                for model in get_supported_models()
            }
        }

# 全局模型管理器实例
model_manager = ModelManager() 