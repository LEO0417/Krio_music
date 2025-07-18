"""
模型下载和缓存管理器 (Model Downloader and Cache Manager)

这个模块负责管理MusicGen模型的下载和缓存，包括：
1. 模型文件的自动下载
2. 下载进度监控
3. 缓存验证和管理
4. 断点续传支持
5. 网络错误处理和重试机制

技术说明：
- 使用 Transformers 库的缓存机制
- 支持并发下载和进度回调
- 实现智能缓存清理策略
"""
import os
import asyncio
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import threading

import torch
from transformers import MusicgenForConditionalGeneration, AutoProcessor
from huggingface_hub import snapshot_download, hf_hub_download
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError

from config.settings import MODELS_DIR
from models.model_config import ModelConfig, config_manager
from api.errors import ModelDownloadError, ModelCacheError

logger = logging.getLogger("model_downloader")

class DownloadProgress:
    """下载进度跟踪器"""
    
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.total_files = 0
        self.downloaded_files = 0
        self.total_size = 0
        self.downloaded_size = 0
        self.current_file = ""
        self.start_time = datetime.now()
        self.status = "preparing"  # preparing, downloading, completed, failed
        self.error_message = ""
        self._lock = threading.Lock()
    
    def update_file_progress(self, filename: str, downloaded: int, total: int):
        """更新单个文件的下载进度"""
        with self._lock:
            self.current_file = filename
            # 这里可以添加更详细的文件级进度跟踪
    
    def complete_file(self, filename: str, size: int):
        """标记文件下载完成"""
        with self._lock:
            self.downloaded_files += 1
            self.downloaded_size += size
    
    def set_total_files(self, count: int):
        """设置总文件数"""
        with self._lock:
            self.total_files = count
    
    def get_progress_info(self) -> Dict[str, Any]:
        """获取进度信息"""
        with self._lock:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            if self.total_files > 0:
                file_progress = (self.downloaded_files / self.total_files) * 100
            else:
                file_progress = 0
            
            if self.total_size > 0:
                size_progress = (self.downloaded_size / self.total_size) * 100
            else:
                size_progress = 0
            
            # 使用文件进度和大小进度的平均值
            overall_progress = (file_progress + size_progress) / 2 if self.total_size > 0 else file_progress
            
            return {
                "model_id": self.model_id,
                "status": self.status,
                "overall_progress": min(overall_progress, 100),
                "file_progress": file_progress,
                "downloaded_files": self.downloaded_files,
                "total_files": self.total_files,
                "downloaded_size_mb": round(self.downloaded_size / (1024 * 1024), 2),
                "total_size_mb": round(self.total_size / (1024 * 1024), 2),
                "current_file": self.current_file,
                "elapsed_seconds": round(elapsed, 1),
                "error_message": self.error_message
            }

class ModelDownloader:
    """
    模型下载和缓存管理器
    
    负责管理MusicGen模型的下载、缓存验证和清理等操作。
    """
    
    def __init__(self):
        """初始化下载管理器"""
        self.models_dir = Path(MODELS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.download_progress: Dict[str, DownloadProgress] = {}
        self.active_downloads: Dict[str, asyncio.Task] = {}
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # 下载配置
        self.max_retries = 3
        self.retry_delay = 5  # 秒
        self.timeout = 300  # 5分钟超时
        
        logger.info("Model Downloader initialized")
    
    async def download_model(
        self, 
        model_id: str, 
        config: Optional[ModelConfig] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        force_download: bool = False
    ) -> bool:
        """
        异步下载模型
        
        Args:
            model_id: 模型ID (如 "facebook/musicgen-small")
            config: 模型配置，如果为None则使用默认配置
            progress_callback: 进度回调函数
            force_download: 是否强制重新下载
            
        Returns:
            bool: 下载成功返回True
            
        Raises:
            ModelDownloadError: 下载失败时抛出
        """
        if model_id in self.active_downloads:
            logger.info(f"Model {model_id} is already being downloaded")
            return False
        
        # 检查是否已缓存
        if not force_download and self.is_model_cached(model_id):
            logger.info(f"Model {model_id} is already cached")
            return True
        
        # 获取配置
        if config is None:
            config = config_manager.get_config(model_id.replace("facebook/", "").replace("-", "_"))
            if config is None:
                config = config_manager.get_default_config()
                config.model_id = model_id
        
        # 创建进度跟踪器
        progress = DownloadProgress(model_id)
        self.download_progress[model_id] = progress
        
        try:
            # 创建下载任务
            download_task = asyncio.create_task(
                self._download_model_async(model_id, config, progress, progress_callback)
            )
            self.active_downloads[model_id] = download_task
            
            # 等待下载完成
            result = await download_task
            
            if result:
                progress.status = "completed"
                logger.info(f"Model {model_id} downloaded successfully")
            else:
                progress.status = "failed"
                logger.error(f"Model {model_id} download failed")
            
            return result
            
        except Exception as e:
            progress.status = "failed"
            progress.error_message = str(e)
            logger.error(f"Error downloading model {model_id}: {e}")
            raise ModelDownloadError(f"Failed to download model {model_id}: {e}")
        
        finally:
            # 清理
            if model_id in self.active_downloads:
                del self.active_downloads[model_id]
    
    async def _download_model_async(
        self,
        model_id: str,
        config: ModelConfig,
        progress: DownloadProgress,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]]
    ) -> bool:
        """内部异步下载方法"""
        
        def progress_update():
            """更新进度并调用回调"""
            if progress_callback:
                try:
                    progress_callback(progress.get_progress_info())
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
        
        try:
            progress.status = "downloading"
            progress_update()
            
            # 在线程池中执行下载
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._download_model_sync,
                model_id,
                config,
                progress,
                progress_update
            )
            
            if result:
                # 更新缓存信息
                cache_info = {
                    "model_id": model_id,
                    "cache_dir": config.cache_dir,
                    "downloaded_at": datetime.now().isoformat(),
                    "config": config.to_dict()
                }
                config_manager.update_cache_info(model_id, cache_info)
                
                progress.status = "completed"
                progress_update()
                
                return True
            else:
                progress.status = "failed"
                progress_update()
                return False
                
        except Exception as e:
            progress.status = "failed"
            progress.error_message = str(e)
            progress_update()
            logger.error(f"Download error for {model_id}: {e}")
            return False
    
    def _download_model_sync(
        self,
        model_id: str,
        config: ModelConfig,
        progress: DownloadProgress,
        progress_update: Callable
    ) -> bool:
        """同步下载模型（在线程池中运行）"""
        
        cache_dir = Path(config.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                logger.info(f"Downloading model {model_id} (attempt {retry_count + 1}/{self.max_retries})")
                
                # 下载模型文件
                logger.info("Downloading model files...")
                progress.current_file = "model files"
                progress_update()
                
                # 使用 snapshot_download 下载整个模型
                snapshot_download(
                    repo_id=model_id,
                    cache_dir=str(cache_dir.parent),
                    local_dir=str(cache_dir),
                    local_dir_use_symlinks=False,
                    resume_download=True
                )
                
                # 验证下载的文件
                if self._verify_model_files(cache_dir, model_id):
                    logger.info(f"Model {model_id} downloaded and verified successfully")
                    
                    # 计算总大小
                    total_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                    progress.total_size = total_size
                    progress.downloaded_size = total_size
                    progress.downloaded_files = len(list(cache_dir.rglob('*')))
                    progress.total_files = progress.downloaded_files
                    
                    return True
                else:
                    raise ModelDownloadError("Model file verification failed")
                
            except Exception as e:
                retry_count += 1
                error_msg = f"Download attempt {retry_count} failed: {e}"
                logger.warning(error_msg)
                
                if retry_count < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    import time
                    time.sleep(self.retry_delay)
                else:
                    progress.error_message = f"All download attempts failed. Last error: {e}"
                    logger.error(progress.error_message)
                    return False
        
        return False
    
    def _verify_model_files(self, cache_dir: Path, model_id: str) -> bool:
        """
        验证下载的模型文件
        
        Args:
            cache_dir: 缓存目录
            model_id: 模型ID
            
        Returns:
            bool: 验证通过返回True
        """
        try:
            # 检查必需的文件
            required_files = [
                "config.json",
                "generation_config.json"
            ]
            
            # 检查模型文件（可能是 .safetensors 或 .bin）
            model_files = list(cache_dir.glob("*.safetensors")) + list(cache_dir.glob("*.bin"))
            if not model_files:
                logger.error("No model weight files found")
                return False
            
            # 检查必需文件
            for filename in required_files:
                file_path = cache_dir / filename
                if not file_path.exists():
                    logger.error(f"Required file missing: {filename}")
                    return False
            
            # 尝试加载配置文件验证格式
            config_file = cache_dir / "config.json"
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                if "model_type" not in config_data:
                    logger.error("Invalid config.json format")
                    return False
            
            logger.info("Model file verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Model file verification failed: {e}")
            return False
    
    def is_model_cached(self, model_id: str) -> bool:
        """
        检查模型是否已缓存
        
        Args:
            model_id: 模型ID
            
        Returns:
            bool: 已缓存返回True
        """
        return config_manager.is_model_cached(model_id)
    
    def get_download_progress(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        获取下载进度
        
        Args:
            model_id: 模型ID
            
        Returns:
            Dict: 进度信息，如果没有下载任务返回None
        """
        if model_id in self.download_progress:
            return self.download_progress[model_id].get_progress_info()
        return None
    
    def cancel_download(self, model_id: str) -> bool:
        """
        取消下载
        
        Args:
            model_id: 模型ID
            
        Returns:
            bool: 成功取消返回True
        """
        if model_id in self.active_downloads:
            try:
                task = self.active_downloads[model_id]
                task.cancel()
                
                # 更新进度状态
                if model_id in self.download_progress:
                    self.download_progress[model_id].status = "cancelled"
                
                logger.info(f"Download cancelled for model {model_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to cancel download for {model_id}: {e}")
                return False
        
        return False
    
    def clear_model_cache(self, model_id: str) -> bool:
        """
        清理模型缓存
        
        Args:
            model_id: 模型ID
            
        Returns:
            bool: 成功清理返回True
        """
        try:
            cache_info = config_manager.get_cache_info(model_id)
            if not cache_info:
                logger.info(f"No cache info found for model {model_id}")
                return True
            
            cache_dir = Path(cache_info.get('cache_dir', ''))
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                logger.info(f"Cleared cache for model {model_id}")
            
            # 清理缓存信息
            if model_id in config_manager.cache_info:
                del config_manager.cache_info[model_id]
                config_manager._save_cache_info()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache for model {model_id}: {e}")
            return False
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """
        获取缓存摘要信息
        
        Returns:
            Dict: 缓存摘要
        """
        summary = {
            "total_models": 0,
            "total_size_mb": 0,
            "models": []
        }
        
        try:
            for model_id, cache_info in config_manager.cache_info.items():
                size_info = config_manager.get_model_size_info(model_id)
                
                model_summary = {
                    "model_id": model_id,
                    "cached": size_info.get("cached", False),
                    "size_mb": size_info.get("size_mb", 0),
                    "downloaded_at": cache_info.get("downloaded_at", ""),
                    "cache_dir": cache_info.get("cache_dir", "")
                }
                
                summary["models"].append(model_summary)
                
                if model_summary["cached"]:
                    summary["total_models"] += 1
                    summary["total_size_mb"] += model_summary["size_mb"]
            
            summary["total_size_mb"] = round(summary["total_size_mb"], 2)
            
        except Exception as e:
            logger.error(f"Failed to generate cache summary: {e}")
            summary["error"] = str(e)
        
        return summary
    
    def cleanup_old_cache(self, days_old: int = 30) -> Dict[str, Any]:
        """
        清理旧的缓存文件
        
        Args:
            days_old: 清理多少天前的缓存
            
        Returns:
            Dict: 清理结果
        """
        result = {
            "cleaned_models": [],
            "freed_space_mb": 0,
            "errors": []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            for model_id, cache_info in list(config_manager.cache_info.items()):
                try:
                    downloaded_at_str = cache_info.get("downloaded_at", "")
                    if not downloaded_at_str:
                        continue
                    
                    downloaded_at = datetime.fromisoformat(downloaded_at_str.replace('Z', '+00:00'))
                    
                    if downloaded_at < cutoff_date:
                        size_info = config_manager.get_model_size_info(model_id)
                        size_mb = size_info.get("size_mb", 0)
                        
                        if self.clear_model_cache(model_id):
                            result["cleaned_models"].append(model_id)
                            result["freed_space_mb"] += size_mb
                        
                except Exception as e:
                    error_msg = f"Error cleaning cache for {model_id}: {e}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)
            
            result["freed_space_mb"] = round(result["freed_space_mb"], 2)
            logger.info(f"Cache cleanup completed: {len(result['cleaned_models'])} models, {result['freed_space_mb']} MB freed")
            
        except Exception as e:
            error_msg = f"Cache cleanup failed: {e}"
            result["errors"].append(error_msg)
            logger.error(error_msg)
        
        return result

# 全局下载管理器实例
downloader = ModelDownloader()