"""
音乐生成器 (Music Generator)

这个模块实现了MusicGen模型的音乐生成核心功能，包括：
1. 音乐生成处理器
2. 提示文本处理和验证
3. 生成参数处理和验证
4. 异步音乐生成任务管理

技术说明：
- 使用 MusicGen 模型进行音乐生成
- 支持文本提示条件生成
- 实现参数验证和处理
- 提供异步生成接口
"""
import asyncio
import logging
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json
import torch
import numpy as np
from pathlib import Path

from models.model_manager import model_manager, ModelStatus
from audio.audio_processor import audio_processor, AudioFormat, AudioQuality
from config.settings import (
    AUDIO_DIR, 
    AUDIO_SETTINGS, 
    MODEL_SETTINGS,
    get_model_config
)
from api.errors import (
    ModelInferenceError,
    ModelLoadError,
    AudioProcessingError,
    ValidationError
)

# Configure logging
logger = logging.getLogger("music_generator")

class GenerationStatus(Enum):
    """生成任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class GenerationTask:
    """音乐生成任务"""
    
    def __init__(self, task_id: str, prompt: str, parameters: Dict[str, Any]):
        self.id = task_id
        self.prompt = prompt
        self.parameters = parameters
        self.status = GenerationStatus.PENDING
        self.progress = 0
        self.result_path: Optional[str] = None
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.estimated_time = self._estimate_generation_time()
        
    def _estimate_generation_time(self) -> int:
        """估算生成时间（秒）"""
        duration = self.parameters.get("duration", 15)
        device = model_manager.model_info.device if model_manager.model_info else "cpu"
        
        # 基于经验的时间估算
        if device == "cuda":
            return max(5, duration * 0.5)  # GPU大约每秒音频需要0.5秒
        else:
            return max(10, duration * 2)   # CPU大约每秒音频需要2秒
    
    def update_progress(self, progress: int):
        """更新进度"""
        self.progress = min(100, max(0, progress))
        self.updated_at = datetime.now()
    
    def update_status(self, status: GenerationStatus, error_message: str = None):
        """更新状态"""
        self.status = status
        self.error_message = error_message
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "parameters": self.parameters,
            "status": self.status.value,
            "progress": self.progress,
            "result_path": self.result_path,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "estimated_time": self.estimated_time
        }

class PromptProcessor:
    """提示文本处理器"""
    
    def __init__(self):
        self.max_length = 256
        self.min_length = 1
        
    def validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        验证提示文本
        
        Args:
            prompt: 输入提示文本
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        validation = {
            "valid": True,
            "processed_prompt": prompt,
            "warnings": [],
            "errors": []
        }
        
        # 检查长度
        if not prompt or len(prompt.strip()) < self.min_length:
            validation["valid"] = False
            validation["errors"].append("提示文本不能为空")
            return validation
            
        if len(prompt) > self.max_length:
            validation["warnings"].append(f"提示文本过长，将截断为{self.max_length}字符")
            validation["processed_prompt"] = prompt[:self.max_length]
        
        # 清理文本
        processed = self._clean_prompt(prompt)
        validation["processed_prompt"] = processed
        
        # 检查内容
        if self._contains_inappropriate_content(processed):
            validation["valid"] = False
            validation["errors"].append("提示文本包含不适当内容")
        
        return validation
    
    def _clean_prompt(self, prompt: str) -> str:
        """清理提示文本"""
        # 去除多余空格
        cleaned = " ".join(prompt.split())
        
        # 去除特殊字符（保留音乐相关的符号）
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-()[]{}#♪♫♪♫")
        cleaned = "".join(char for char in cleaned if char in allowed_chars or ord(char) > 127)
        
        return cleaned.strip()
    
    def _contains_inappropriate_content(self, prompt: str) -> bool:
        """检查是否包含不适当内容"""
        # 简单的内容过滤（在实际应用中可以使用更复杂的过滤系统）
        inappropriate_keywords = [
            "violence", "暴力", "hate", "仇恨", "explicit"
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in inappropriate_keywords)
    
    def enhance_prompt(self, prompt: str, style: str = None) -> str:
        """
        增强提示文本
        
        Args:
            prompt: 原始提示文本
            style: 音乐风格
            
        Returns:
            str: 增强后的提示文本
        """
        enhanced = prompt
        
        # 如果指定了风格，添加风格描述
        if style and style != "auto":
            style_descriptions = {
                "classical": "classical music style with orchestral instruments",
                "pop": "pop music style with modern instrumentation",
                "electronic": "electronic music with synthesizers and digital sounds",
                "jazz": "jazz music with improvisation and swing rhythm",
                "rock": "rock music with guitars and strong rhythm",
                "ambient": "ambient music with atmospheric and relaxing sounds",
                "folk": "folk music with acoustic instruments and natural feel"
            }
            
            if style in style_descriptions:
                enhanced = f"{prompt}, {style_descriptions[style]}"
        
        return enhanced

class ParameterValidator:
    """参数验证器"""
    
    def __init__(self):
        self.default_parameters = {
            "duration": 15,
            "temperature": 1.0,
            "top_k": 250,
            "top_p": 0.0,
            "guidance_scale": 3.0,
            "sample_rate": 32000,
            "style": "auto",
            "use_conditioning": True
        }
        
    def validate_parameters(self, parameters: Dict[str, Any], model_name: str = None) -> Dict[str, Any]:
        """
        验证生成参数
        
        Args:
            parameters: 输入参数
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        validation = {
            "valid": True,
            "processed_parameters": {},
            "warnings": [],
            "errors": []
        }
        
        # 获取模型配置
        model_config = get_model_config(model_name or model_manager.model_info.name)
        if not model_config:
            model_config = {}
        
        # 验证每个参数
        for key, value in parameters.items():
            try:
                validated_value = self._validate_parameter(key, value, model_config)
                validation["processed_parameters"][key] = validated_value
            except ValidationError as e:
                validation["valid"] = False
                validation["errors"].append(f"参数 {key}: {str(e)}")
        
        # 添加缺失的默认参数
        for key, default_value in self.default_parameters.items():
            if key not in validation["processed_parameters"]:
                validation["processed_parameters"][key] = default_value
        
        # 参数兼容性检查
        self._check_parameter_compatibility(validation)
        
        return validation
    
    def _validate_parameter(self, key: str, value: Any, model_config: Dict[str, Any]) -> Any:
        """验证单个参数"""
        if key == "duration":
            if not isinstance(value, (int, float)):
                raise ValidationError("duration must be a number")
            if value < 1 or value > 30:
                raise ValidationError("duration must be between 1 and 30 seconds")
            return float(value)
            
        elif key == "temperature":
            if not isinstance(value, (int, float)):
                raise ValidationError("temperature must be a number")
            if value < 0.1 or value > 2.0:
                raise ValidationError("temperature must be between 0.1 and 2.0")
            return float(value)
            
        elif key == "top_k":
            if not isinstance(value, int):
                raise ValidationError("top_k must be an integer")
            if value < 1 or value > 1000:
                raise ValidationError("top_k must be between 1 and 1000")
            return int(value)
            
        elif key == "top_p":
            if not isinstance(value, (int, float)):
                raise ValidationError("top_p must be a number")
            if value < 0.0 or value > 1.0:
                raise ValidationError("top_p must be between 0.0 and 1.0")
            return float(value)
            
        elif key == "guidance_scale":
            if not isinstance(value, (int, float)):
                raise ValidationError("guidance_scale must be a number")
            if value < 1.0 or value > 10.0:
                raise ValidationError("guidance_scale must be between 1.0 and 10.0")
            return float(value)
            
        elif key == "sample_rate":
            if not isinstance(value, int):
                raise ValidationError("sample_rate must be an integer")
            valid_rates = [16000, 22050, 32000, 44100, 48000]
            if value not in valid_rates:
                raise ValidationError(f"sample_rate must be one of {valid_rates}")
            return int(value)
            
        elif key == "style":
            if not isinstance(value, str):
                raise ValidationError("style must be a string")
            valid_styles = ["auto", "classical", "pop", "electronic", "jazz", "rock", "ambient", "folk"]
            if value not in valid_styles:
                raise ValidationError(f"style must be one of {valid_styles}")
            return value
            
        elif key == "use_conditioning":
            if not isinstance(value, bool):
                raise ValidationError("use_conditioning must be a boolean")
            return value
            
        else:
            # 其他参数直接返回
            return value
    
    def _check_parameter_compatibility(self, validation: Dict[str, Any]):
        """检查参数兼容性"""
        params = validation["processed_parameters"]
        
        # 检查采样率和模型兼容性
        if params.get("sample_rate") != 32000:
            validation["warnings"].append("MusicGen模型推荐使用32kHz采样率")
        
        # 检查温度和top_k组合
        if params.get("temperature", 1.0) > 1.5 and params.get("top_k", 250) > 500:
            validation["warnings"].append("高温度和大top_k可能导致生成质量下降")

class MusicGenerator:
    """音乐生成器主类"""
    
    def __init__(self):
        self.prompt_processor = PromptProcessor()
        self.parameter_validator = ParameterValidator()
        self.active_tasks: Dict[str, GenerationTask] = {}
        self.task_history: List[GenerationTask] = []
        self.max_concurrent_tasks = 1  # 限制并发任务数
        
        # 音频处理配置
        self.default_audio_format = AudioFormat(AUDIO_SETTINGS.get("default_format", "wav"))
        self.default_audio_quality = AudioQuality.HIGH
        
    async def generate_music(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """
        生成音乐
        
        Args:
            prompt: 文本提示
            parameters: 生成参数
            
        Returns:
            str: 任务ID
            
        Raises:
            ValidationError: 参数验证失败
            ModelInferenceError: 模型推理失败
        """
        # 检查模型是否准备就绪
        if not model_manager.is_ready():
            raise ModelInferenceError("Model is not loaded or ready")
        
        # 检查并发任务限制
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            raise ModelInferenceError("Too many concurrent generation tasks")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 验证提示文本
        prompt_validation = self.prompt_processor.validate_prompt(prompt)
        if not prompt_validation["valid"]:
            raise ValidationError(f"Invalid prompt: {prompt_validation['errors']}")
        
        processed_prompt = prompt_validation["processed_prompt"]
        
        # 验证参数
        if parameters is None:
            parameters = {}
        
        param_validation = self.parameter_validator.validate_parameters(parameters)
        if not param_validation["valid"]:
            raise ValidationError(f"Invalid parameters: {param_validation['errors']}")
        
        processed_parameters = param_validation["processed_parameters"]
        
        # 创建生成任务
        task = GenerationTask(task_id, processed_prompt, processed_parameters)
        self.active_tasks[task_id] = task
        
        # 启动异步生成任务
        asyncio.create_task(self._run_generation_task(task))
        
        logger.info(f"Started music generation task {task_id}")
        return task_id
    
    async def _run_generation_task(self, task: GenerationTask):
        """运行音乐生成任务"""
        try:
            task.update_status(GenerationStatus.PROCESSING)
            
            # 增强提示文本
            enhanced_prompt = self.prompt_processor.enhance_prompt(
                task.prompt, 
                task.parameters.get("style", "auto")
            )
            
            # 更新进度
            task.update_progress(10)
            
            # 执行模型推理
            await self._perform_inference(task, enhanced_prompt)
            
            # 更新进度
            task.update_progress(90)
            
            # 后处理音频
            await self._post_process_audio(task)
            
            # 完成任务
            task.update_progress(100)
            task.update_status(GenerationStatus.COMPLETED)
            
            logger.info(f"Completed music generation task {task.id}")
            
        except Exception as e:
            logger.error(f"Error in generation task {task.id}: {e}")
            task.update_status(GenerationStatus.FAILED, str(e))
            
        finally:
            # 移动到历史记录
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            self.task_history.append(task)
            
            # 限制历史记录大小
            if len(self.task_history) > 100:
                self.task_history = self.task_history[-100:]
    
    async def _perform_inference(self, task: GenerationTask, prompt: str):
        """执行模型推理"""
        try:
            # 在后台线程中执行推理
            result = await asyncio.to_thread(self._inference_sync, task, prompt)
            
            # 使用音频处理器处理和保存音频
            metadata = {
                "prompt": task.prompt,
                "parameters": task.parameters,
                "title": f"Generated Music - {task.id[:8]}",
                "description": f"Generated from prompt: {task.prompt[:100]}..."
            }
            
            output_path = audio_processor.process_audio(
                audio_data=result,
                audio_id=task.id,
                sample_rate=task.parameters["sample_rate"],
                output_format=self.default_audio_format,
                quality=self.default_audio_quality,
                metadata=metadata,
                apply_effects=True
            )
            
            task.result_path = output_path
            task.update_progress(80)
            
        except Exception as e:
            raise ModelInferenceError(f"Model inference failed: {str(e)}")
    
    def _inference_sync(self, task: GenerationTask, prompt: str):
        """同步模型推理"""
        try:
            # 记录推理调用
            model_manager.record_inference()
            
            # 准备输入
            inputs = model_manager.processor(
                text=[prompt],
                padding=True,
                return_tensors="pt"
            )
            
            # 移动到正确的设备
            device = model_manager.model_info.device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # 生成参数
            generation_config = {
                "max_new_tokens": int(task.parameters["duration"] * task.parameters["sample_rate"] / 320),
                "temperature": task.parameters["temperature"],
                "top_k": task.parameters["top_k"],
                "top_p": task.parameters["top_p"],
                "guidance_scale": task.parameters["guidance_scale"],
                "do_sample": True,
                "use_cache": True
            }
            
            # 执行生成
            with torch.no_grad():
                audio_tokens = model_manager.model.generate(**inputs, **generation_config)
            
            # 解码音频
            audio_values = model_manager.model.decode(audio_tokens, task.parameters["sample_rate"])
            
            # 转换为numpy数组
            if isinstance(audio_values, torch.Tensor):
                audio_values = audio_values.cpu().numpy()
            
            # 确保音频形状正确
            if audio_values.ndim == 3:
                audio_values = audio_values[0]  # 取第一个batch
            
            return torch.from_numpy(audio_values)
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            raise ModelInferenceError(f"Failed to generate audio: {str(e)}")
    
    async def _post_process_audio(self, task: GenerationTask):
        """后处理音频"""
        try:
            # 这里可以添加音频后处理逻辑
            # 例如：标准化、降噪、格式转换等
            
            # 目前只是简单的进度更新
            task.update_progress(95)
            
        except Exception as e:
            logger.warning(f"Audio post-processing warning: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.active_tasks.get(task_id)
        if not task:
            # 在历史记录中查找
            for hist_task in self.task_history:
                if hist_task.id == task_id:
                    task = hist_task
                    break
        
        return task.to_dict() if task else None
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.update_status(GenerationStatus.CANCELLED)
            del self.active_tasks[task_id]
            self.task_history.append(task)
            return True
        return False
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """获取活动任务列表"""
        return [task.to_dict() for task in self.active_tasks.values()]
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取任务历史记录"""
        return [task.to_dict() for task in self.task_history[-limit:]]
    
    def clear_history(self):
        """清理历史记录"""
        self.task_history.clear()

# 全局音乐生成器实例
music_generator = MusicGenerator()