"""
模型配置管理器 (Model Configuration Manager)

这个模块负责管理MusicGen模型的配置，包括：
1. 模型配置的加载和验证
2. 模型缓存策略管理
3. 模型版本管理
4. 配置文件的读写操作

技术说明：
- 支持多种模型配置（small, medium, large）
- 实现配置缓存和验证机制
- 提供配置更新和回滚功能
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

from config.settings import MODELS_DIR, DEFAULT_MODEL

logger = logging.getLogger("model_config")

@dataclass
class ModelConfig:
    """模型配置数据类"""
    name: str
    model_id: str
    cache_dir: str
    max_length: int = 30  # 最大生成长度（秒）
    sample_rate: int = 32000
    guidance_scale: float = 3.0
    temperature: float = 1.0
    top_k: int = 250
    top_p: float = 0.0
    use_cache: bool = True
    torch_dtype: str = "float16"  # "float16" or "float32"
    device_map: str = "auto"
    low_cpu_mem_usage: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """从字典创建配置"""
        return cls(**data)
    
    def get_cache_key(self) -> str:
        """生成配置的缓存键"""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()

class ModelConfigManager:
    """
    模型配置管理器
    
    负责管理所有模型相关的配置，包括预设配置、用户自定义配置等。
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = Path(MODELS_DIR) / "configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "model_configs.json"
        self.cache_info_file = self.config_dir / "cache_info.json"
        
        # 预设配置
        self.preset_configs = self._load_preset_configs()
        
        # 用户配置
        self.user_configs = self._load_user_configs()
        
        # 缓存信息
        self.cache_info = self._load_cache_info()
        
        logger.info(f"Model Config Manager initialized with {len(self.preset_configs)} preset configs")
    
    def _load_preset_configs(self) -> Dict[str, ModelConfig]:
        """加载预设配置"""
        presets = {
            "musicgen-small": ModelConfig(
                name="MusicGen Small",
                model_id="facebook/musicgen-small",
                cache_dir=str(MODELS_DIR / "facebook_musicgen-small"),
                max_length=30,
                sample_rate=32000,
                guidance_scale=3.0,
                temperature=1.0,
                top_k=250,
                top_p=0.0,
                torch_dtype="float16",
                device_map="auto",
                low_cpu_mem_usage=True
            ),
            "musicgen-medium": ModelConfig(
                name="MusicGen Medium",
                model_id="facebook/musicgen-medium",
                cache_dir=str(MODELS_DIR / "facebook_musicgen-medium"),
                max_length=30,
                sample_rate=32000,
                guidance_scale=3.0,
                temperature=1.0,
                top_k=250,
                top_p=0.0,
                torch_dtype="float16",
                device_map="auto",
                low_cpu_mem_usage=True
            ),
            "musicgen-large": ModelConfig(
                name="MusicGen Large",
                model_id="facebook/musicgen-large",
                cache_dir=str(MODELS_DIR / "facebook_musicgen-large"),
                max_length=30,
                sample_rate=32000,
                guidance_scale=3.0,
                temperature=1.0,
                top_k=250,
                top_p=0.0,
                torch_dtype="float16",
                device_map="auto",
                low_cpu_mem_usage=True
            )
        }
        
        return presets
    
    def _load_user_configs(self) -> Dict[str, ModelConfig]:
        """加载用户自定义配置"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            configs = {}
            for name, config_data in data.get('user_configs', {}).items():
                try:
                    configs[name] = ModelConfig.from_dict(config_data)
                except Exception as e:
                    logger.warning(f"Failed to load user config '{name}': {e}")
            
            return configs
            
        except Exception as e:
            logger.error(f"Failed to load user configs: {e}")
            return {}
    
    def _load_cache_info(self) -> Dict[str, Any]:
        """加载缓存信息"""
        if not self.cache_info_file.exists():
            return {}
        
        try:
            with open(self.cache_info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache info: {e}")
            return {}
    
    def _save_user_configs(self):
        """保存用户配置"""
        try:
            data = {
                'user_configs': {name: config.to_dict() for name, config in self.user_configs.items()},
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save user configs: {e}")
    
    def _save_cache_info(self):
        """保存缓存信息"""
        try:
            with open(self.cache_info_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save cache info: {e}")
    
    def get_config(self, config_name: str) -> Optional[ModelConfig]:
        """
        获取指定名称的配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            ModelConfig: 配置对象，如果不存在返回None
        """
        # 先查找用户配置
        if config_name in self.user_configs:
            return self.user_configs[config_name]
        
        # 再查找预设配置
        if config_name in self.preset_configs:
            return self.preset_configs[config_name]
        
        return None
    
    def get_default_config(self) -> ModelConfig:
        """
        获取默认配置
        
        Returns:
            ModelConfig: 默认配置对象
        """
        # 从DEFAULT_MODEL获取默认配置名
        default_name = DEFAULT_MODEL.replace("facebook/", "").replace("-", "_")
        
        config = self.get_config(default_name)
        if config:
            return config
        
        # 如果找不到，返回第一个预设配置
        if self.preset_configs:
            return list(self.preset_configs.values())[0]
        
        # 最后的备选方案
        return ModelConfig(
            name="Default",
            model_id=DEFAULT_MODEL,
            cache_dir=str(MODELS_DIR / "default")
        )
    
    def list_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用配置
        
        Returns:
            Dict: 包含预设和用户配置的字典
        """
        return {
            'preset_configs': {name: config.to_dict() for name, config in self.preset_configs.items()},
            'user_configs': {name: config.to_dict() for name, config in self.user_configs.items()}
        }
    
    def add_user_config(self, name: str, config: ModelConfig) -> bool:
        """
        添加用户自定义配置
        
        Args:
            name: 配置名称
            config: 配置对象
            
        Returns:
            bool: 成功返回True
        """
        try:
            self.user_configs[name] = config
            self._save_user_configs()
            logger.info(f"Added user config: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add user config '{name}': {e}")
            return False
    
    def remove_user_config(self, name: str) -> bool:
        """
        删除用户配置
        
        Args:
            name: 配置名称
            
        Returns:
            bool: 成功返回True
        """
        try:
            if name in self.user_configs:
                del self.user_configs[name]
                self._save_user_configs()
                logger.info(f"Removed user config: {name}")
                return True
            else:
                logger.warning(f"User config '{name}' not found")
                return False
        except Exception as e:
            logger.error(f"Failed to remove user config '{name}': {e}")
            return False
    
    def update_cache_info(self, model_id: str, info: Dict[str, Any]):
        """
        更新模型缓存信息
        
        Args:
            model_id: 模型ID
            info: 缓存信息
        """
        try:
            self.cache_info[model_id] = {
                **info,
                'updated_at': datetime.now().isoformat()
            }
            self._save_cache_info()
        except Exception as e:
            logger.error(f"Failed to update cache info for {model_id}: {e}")
    
    def get_cache_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模型缓存信息
        
        Args:
            model_id: 模型ID
            
        Returns:
            Dict: 缓存信息，如果不存在返回None
        """
        return self.cache_info.get(model_id)
    
    def is_model_cached(self, model_id: str) -> bool:
        """
        检查模型是否已缓存
        
        Args:
            model_id: 模型ID
            
        Returns:
            bool: 已缓存返回True
        """
        cache_info = self.get_cache_info(model_id)
        if not cache_info:
            return False
        
        cache_dir = Path(cache_info.get('cache_dir', ''))
        return cache_dir.exists() and any(cache_dir.iterdir())
    
    def get_model_size_info(self, model_id: str) -> Dict[str, Any]:
        """
        获取模型大小信息
        
        Args:
            model_id: 模型ID
            
        Returns:
            Dict: 包含模型大小信息的字典
        """
        cache_info = self.get_cache_info(model_id)
        if not cache_info:
            return {"cached": False, "size_mb": 0}
        
        cache_dir = Path(cache_info.get('cache_dir', ''))
        if not cache_dir.exists():
            return {"cached": False, "size_mb": 0}
        
        try:
            total_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            return {
                "cached": True,
                "size_mb": round(size_mb, 2),
                "cache_dir": str(cache_dir),
                "file_count": len(list(cache_dir.rglob('*')))
            }
        except Exception as e:
            logger.error(f"Failed to calculate model size for {model_id}: {e}")
            return {"cached": False, "size_mb": 0, "error": str(e)}
    
    def validate_config(self, config: ModelConfig) -> List[str]:
        """
        验证配置的有效性
        
        Args:
            config: 要验证的配置
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 检查必需字段
        if not config.name:
            errors.append("配置名称不能为空")
        
        if not config.model_id:
            errors.append("模型ID不能为空")
        
        if not config.cache_dir:
            errors.append("缓存目录不能为空")
        
        # 检查数值范围
        if config.max_length <= 0 or config.max_length > 300:
            errors.append("最大长度必须在1-300秒之间")
        
        if config.sample_rate not in [16000, 22050, 32000, 44100, 48000]:
            errors.append("采样率必须是支持的值之一: 16000, 22050, 32000, 44100, 48000")
        
        if config.guidance_scale < 0 or config.guidance_scale > 10:
            errors.append("引导比例必须在0-10之间")
        
        if config.temperature < 0 or config.temperature > 2:
            errors.append("温度必须在0-2之间")
        
        if config.top_k < 0 or config.top_k > 1000:
            errors.append("top_k必须在0-1000之间")
        
        if config.top_p < 0 or config.top_p > 1:
            errors.append("top_p必须在0-1之间")
        
        if config.torch_dtype not in ["float16", "float32"]:
            errors.append("torch_dtype必须是'float16'或'float32'")
        
        return errors

# 全局配置管理器实例
config_manager = ModelConfigManager()