"""
音乐生成处理器 (Music Generation Processor)

这个模块实现了MusicGen模型的音乐生成核心功能，包括：
1. 音乐生成处理器的实现
2. 提示文本处理和验证
3. 生成参数的验证和处理
4. 异步音乐生成任务管理
5. 生成进度监控和状态管理

技术说明：
- 使用 Transformers 库的 MusicGen 模型进行音乐生成
- 支持文本提示和参数控制
- 实现异步生成以避免阻塞主线程
- 提供生成进度监控和取消功能
"""
import asyncio
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
import json
import re

import torch
import numpy as np
from transformers import MusicgenForConditionalGeneration, AutoProcessor
import scipy.io.wavfile as wavfile

from models.model_manager import model_manager
from models.model_config import config_manager, ModelConfig
from config.settings import AUDIO_DIR
from api.errors import ModelInferenceError, ResourceLimitExceededError

logger = logging.getLogger("music_generator")

class GenerationStatus(Enum):
    """生成状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class GenerationRequest:
    """音乐生成请求"""
    
    def __init__(
        self,
        prompt: str,
        duration: float = 10.0,
        guidance_scale: float = 3.0,
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
        sample_rate: int = 32000,
        output_format: str = "wav",
        **kwargs
    ):
        self.id = str(uuid.uuid4())
        self.prompt = prompt
        self.duration = duration
        self.guidance_scale = guidance_scale
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.sample_rate = sample_rate
        self.output_format = output_format
        self.extra_params = kwargs
        
        # 状态信息
        self.status = GenerationStatus.PENDING
        self.progress = 0.0
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result_path: Optional[str] = None
        
        # 取消标志
        self._cancelled = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "duration": self.duration,
            "guidance_scale": self.guidance_scale,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "sample_rate": self.sample_rate,
            "output_format": self.output_format,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "result_path": self.result_path,
            "extra_params": self.extra_params
        }
    
    def cancel(self):
        """取消生成请求"""
        self._cancelled = True
        if self.status in [GenerationStatus.PENDING, GenerationStatus.PROCESSING]:
            self.status = GenerationStatus.CANCELLED
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._cancelled

class PromptProcessor:
    """提示文本处理器"""
    
    def __init__(self):
        """初始化提示处理器"""
        # 预定义的音乐风格关键词
        self.style_keywords = {
            "classical": ["classical", "piano", "violin", "orchestra", "symphony", "chamber"],
            "jazz": ["jazz", "swing", "blues", "saxophone", "trumpet", "improvisation"],
            "rock": ["rock", "guitar", "drums", "electric", "heavy", "metal"],
            "electronic": ["electronic", "synth", "techno", "house", "ambient", "edm"],
            "folk": ["folk", "acoustic", "traditional", "country", "bluegrass"],
            "pop": ["pop", "catchy", "mainstream", "radio", "commercial"],
            "ambient": ["ambient", "atmospheric", "peaceful", "meditative", "calm"],
            "cinematic": ["cinematic", "epic", "dramatic", "orchestral", "soundtrack"]
        }
        
        # 情绪关键词
        self.mood_keywords = {
            "happy": ["happy", "joyful", "cheerful", "upbeat", "energetic"],
            "sad": ["sad", "melancholy", "sorrowful", "emotional", "touching"],
            "calm": ["calm", "peaceful", "relaxing", "serene", "tranquil"],
            "energetic": ["energetic", "dynamic", "powerful", "intense", "driving"],
            "mysterious": ["mysterious", "dark", "enigmatic", "haunting"],
            "romantic": ["romantic", "love", "tender", "intimate", "gentle"]
        }
        
        # 乐器关键词
        self.instrument_keywords = [
            "piano", "guitar", "violin", "drums", "saxophone", "trumpet",
            "flute", "cello", "bass", "synthesizer", "organ", "harp"
        ]
    
    def validate_prompt(self, prompt: str) -> List[str]:
        """
        验证提示文本
        
        Args:
            prompt: 输入的提示文本
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not prompt or not prompt.strip():
            errors.append("提示文本不能为空")
            return errors
        
        prompt = prompt.strip()
        
        # 检查长度
        if len(prompt) < 3:
            errors.append("提示文本太短，至少需要3个字符")
        
        if len(prompt) > 500:
            errors.append("提示文本太长，最多500个字符")
        
        # 检查是否包含有害内容（简单检查）
        harmful_keywords = ["violence", "hate", "explicit", "inappropriate"]
        prompt_lower = prompt.lower()
        for keyword in harmful_keywords:
            if keyword in prompt_lower:
                errors.append(f"提示文本包含不当内容: {keyword}")
        
        return errors
    
    def enhance_prompt(self, prompt: str) -> str:
        """
        增强提示文本
        
        Args:
            prompt: 原始提示文本
            
        Returns:
            str: 增强后的提示文本
        """
        if not prompt or not prompt.strip():
            return prompt
        
        enhanced = prompt.strip()
        
        # 检测并增强风格信息
        detected_styles = self._detect_styles(enhanced)
        detected_moods = self._detect_moods(enhanced)
        detected_instruments = self._detect_instruments(enhanced)
        
        # 如果没有检测到明确的风格，添加通用描述
        if not detected_styles and not detected_moods:
            enhanced = f"melodic and harmonious {enhanced}"
        
        # 确保提示以音乐相关的描述开始
        music_starters = ["music", "song", "melody", "tune", "composition", "piece"]
        if not any(starter in enhanced.lower() for starter in music_starters):
            enhanced = f"music with {enhanced}"
        
        return enhanced
    
    def _detect_styles(self, prompt: str) -> List[str]:
        """检测音乐风格"""
        prompt_lower = prompt.lower()
        detected = []
        
        for style, keywords in self.style_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected.append(style)
        
        return detected
    
    def _detect_moods(self, prompt: str) -> List[str]:
        """检测情绪"""
        prompt_lower = prompt.lower()
        detected = []
        
        for mood, keywords in self.mood_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected.append(mood)
        
        return detected
    
    def _detect_instruments(self, prompt: str) -> List[str]:
        """检测乐器"""
        prompt_lower = prompt.lower()
        detected = []
        
        for instrument in self.instrument_keywords:
            if instrument in prompt_lower:
                detected.append(instrument)
        
        return detected
    
    def get_prompt_analysis(self, prompt: str) -> Dict[str, Any]:
        """
        分析提示文本
        
        Args:
            prompt: 提示文本
            
        Returns:
            Dict: 分析结果
        """
        return {
            "original_prompt": prompt,
            "enhanced_prompt": self.enhance_prompt(prompt),
            "detected_styles": self._detect_styles(prompt),
            "detected_moods": self._detect_moods(prompt),
            "detected_instruments": self._detect_instruments(prompt),
            "validation_errors": self.validate_prompt(prompt)
        }

class ParameterValidator:
    """参数验证器"""
    
    def __init__(self):
        """初始化参数验证器"""
        # 参数范围定义
        self.parameter_ranges = {
            "duration": {"min": 1.0, "max": 30.0, "default": 10.0},
            "guidance_scale": {"min": 1.0, "max": 10.0, "default": 3.0},
            "temperature": {"min": 0.1, "max": 2.0, "default": 1.0},
            "top_k": {"min": 1, "max": 1000, "default": 250},
            "top_p": {"min": 0.0, "max": 1.0, "default": 0.0},
            "sample_rate": {"allowed": [16000, 22050, 32000, 44100, 48000], "default": 32000}
        }
        
        # 支持的输出格式
        self.supported_formats = ["wav", "mp3", "flac"]
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证生成参数
        
        Args:
            params: 参数字典
            
        Returns:
            Dict: 包含验证结果和清理后参数的字典
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "cleaned_params": {},
            "applied_defaults": []
        }
        
        # 验证并清理每个参数
        for param_name, range_info in self.parameter_ranges.items():
            if param_name in params:
                value = params[param_name]
                validation_result = self._validate_single_parameter(param_name, value, range_info)
                
                if validation_result["valid"]:
                    result["cleaned_params"][param_name] = validation_result["value"]
                    if validation_result.get("warning"):
                        result["warnings"].append(validation_result["warning"])
                else:
                    result["valid"] = False
                    result["errors"].append(validation_result["error"])
            else:
                # 应用默认值
                default_value = range_info["default"]
                result["cleaned_params"][param_name] = default_value
                result["applied_defaults"].append(f"{param_name}: {default_value}")
        
        # 验证输出格式
        output_format = params.get("output_format", "wav")
        if output_format not in self.supported_formats:
            result["warnings"].append(f"不支持的输出格式 '{output_format}'，使用默认格式 'wav'")
            result["cleaned_params"]["output_format"] = "wav"
        else:
            result["cleaned_params"]["output_format"] = output_format
        
        # 验证提示文本
        prompt = params.get("prompt", "")
        if not prompt or not prompt.strip():
            result["valid"] = False
            result["errors"].append("提示文本不能为空")
        else:
            result["cleaned_params"]["prompt"] = prompt.strip()
        
        return result
    
    def _validate_single_parameter(self, name: str, value: Any, range_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证单个参数"""
        result = {"valid": True, "value": value}
        
        try:
            if name == "sample_rate":
                # 采样率特殊处理
                value = int(value)
                if value not in range_info["allowed"]:
                    closest = min(range_info["allowed"], key=lambda x: abs(x - value))
                    result["value"] = closest
                    result["warning"] = f"采样率 {value} 不支持，使用最接近的值 {closest}"
                else:
                    result["value"] = value
            
            elif name in ["top_k"]:
                # 整数参数
                value = int(value)
                min_val, max_val = range_info["min"], range_info["max"]
                
                if value < min_val:
                    result["value"] = min_val
                    result["warning"] = f"{name} 值 {value} 小于最小值，使用 {min_val}"
                elif value > max_val:
                    result["value"] = max_val
                    result["warning"] = f"{name} 值 {value} 大于最大值，使用 {max_val}"
                else:
                    result["value"] = value
            
            else:
                # 浮点数参数
                value = float(value)
                min_val, max_val = range_info["min"], range_info["max"]
                
                if value < min_val:
                    result["value"] = min_val
                    result["warning"] = f"{name} 值 {value} 小于最小值，使用 {min_val}"
                elif value > max_val:
                    result["value"] = max_val
                    result["warning"] = f"{name} 值 {value} 大于最大值，使用 {max_val}"
                else:
                    result["value"] = value
        
        except (ValueError, TypeError) as e:
            result["valid"] = False
            result["error"] = f"参数 {name} 的值 '{value}' 无效: {str(e)}"
        
        return result

class MusicGenerator:
    """
    音乐生成器
    
    负责管理音乐生成的完整流程，包括参数验证、模型调用、进度监控等。
    """
    
    def __init__(self):
        """初始化音乐生成器"""
        self.prompt_processor = PromptProcessor()
        self.parameter_validator = ParameterValidator()
        
        # 生成任务管理
        self.active_requests: Dict[str, GenerationRequest] = {}
        self.completed_requests: Dict[str, GenerationRequest] = {}
        self.max_completed_requests = 100  # 最多保留100个已完成的请求
        
        # 输出目录
        self.output_dir = Path(AUDIO_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Music Generator initialized")
    
    async def generate_music(
        self,
        prompt: str,
        duration: float = 10.0,
        guidance_scale: float = 3.0,
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
        sample_rate: int = 32000,
        output_format: str = "wav",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kwargs
    ) -> str:
        """
        异步生成音乐
        
        Args:
            prompt: 文本提示
            duration: 音乐长度（秒）
            guidance_scale: 引导比例
            temperature: 温度参数
            top_k: Top-K 采样
            top_p: Top-P 采样
            sample_rate: 采样率
            output_format: 输出格式
            progress_callback: 进度回调函数
            **kwargs: 其他参数
            
        Returns:
            str: 生成请求ID
            
        Raises:
            ModelInferenceError: 生成失败时抛出
            ResourceLimitExceededError: 资源不足时抛出
        """
        # 创建生成请求
        request = GenerationRequest(
            prompt=prompt,
            duration=duration,
            guidance_scale=guidance_scale,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            sample_rate=sample_rate,
            output_format=output_format,
            **kwargs
        )
        
        # 验证参数
        validation_result = self.parameter_validator.validate_parameters({
            "prompt": prompt,
            "duration": duration,
            "guidance_scale": guidance_scale,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "sample_rate": sample_rate,
            "output_format": output_format
        })
        
        if not validation_result["valid"]:
            error_msg = f"参数验证失败: {'; '.join(validation_result['errors'])}"
            request.status = GenerationStatus.FAILED
            request.error_message = error_msg
            raise ModelInferenceError(error_msg)
        
        # 应用清理后的参数
        cleaned_params = validation_result["cleaned_params"]
        for key, value in cleaned_params.items():
            if hasattr(request, key):
                setattr(request, key, value)
        
        # 验证提示文本
        prompt_errors = self.prompt_processor.validate_prompt(request.prompt)
        if prompt_errors:
            error_msg = f"提示文本验证失败: {'; '.join(prompt_errors)}"
            request.status = GenerationStatus.FAILED
            request.error_message = error_msg
            raise ModelInferenceError(error_msg)
        
        # 增强提示文本
        request.prompt = self.prompt_processor.enhance_prompt(request.prompt)
        
        # 检查模型是否就绪
        if not model_manager.is_ready():
            error_msg = "模型未加载或不可用"
            request.status = GenerationStatus.FAILED
            request.error_message = error_msg
            raise ModelInferenceError(error_msg)
        
        # 添加到活动请求列表
        self.active_requests[request.id] = request
        
        # 启动生成任务
        asyncio.create_task(self._generate_music_async(request, progress_callback))
        
        return request.id
    
    async def _generate_music_async(
        self,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]]
    ):
        """内部异步生成方法"""
        try:
            request.status = GenerationStatus.PROCESSING
            request.started_at = datetime.now()
            
            # 更新进度
            def update_progress(progress: float, message: str = ""):
                request.progress = progress
                if progress_callback:
                    try:
                        progress_callback({
                            "request_id": request.id,
                            "status": request.status.value,
                            "progress": progress,
                            "message": message,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")
            
            update_progress(10, "准备生成参数...")
            
            # 检查是否取消
            if request.is_cancelled():
                return
            
            # 在线程池中执行生成
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._generate_music_sync,
                request,
                update_progress
            )
            
            if result and not request.is_cancelled():
                request.status = GenerationStatus.COMPLETED
                request.completed_at = datetime.now()
                request.result_path = result
                update_progress(100, "生成完成")
                
                # 记录推理调用
                model_manager.record_inference()
                
                logger.info(f"Music generation completed: {request.id}")
            elif request.is_cancelled():
                logger.info(f"Music generation cancelled: {request.id}")
            else:
                request.status = GenerationStatus.FAILED
                request.error_message = "生成失败，未知错误"
                update_progress(0, "生成失败")
        
        except Exception as e:
            request.status = GenerationStatus.FAILED
            request.error_message = str(e)
            logger.error(f"Music generation error for {request.id}: {e}")
            
            if progress_callback:
                try:
                    progress_callback({
                        "request_id": request.id,
                        "status": request.status.value,
                        "progress": 0,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    pass
        
        finally:
            # 移动到已完成列表
            if request.id in self.active_requests:
                del self.active_requests[request.id]
            
            self.completed_requests[request.id] = request
            
            # 清理旧的已完成请求
            if len(self.completed_requests) > self.max_completed_requests:
                oldest_id = min(self.completed_requests.keys(), 
                              key=lambda x: self.completed_requests[x].created_at)
                del self.completed_requests[oldest_id]
    
    def _generate_music_sync(
        self,
        request: GenerationRequest,
        progress_callback: Callable[[float, str], None]
    ) -> Optional[str]:
        """同步生成音乐（在线程池中运行）"""
        try:
            progress_callback(20, "加载模型...")
            
            # 获取模型和处理器
            model = model_manager.model
            processor = model_manager.processor
            
            if not model or not processor:
                raise ModelInferenceError("模型或处理器不可用")
            
            progress_callback(30, "处理输入...")
            
            # 处理输入
            inputs = processor(
                text=[request.prompt],
                padding=True,
                return_tensors="pt"
            )
            
            # 移动到正确的设备
            device = model_manager.model_info.device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            progress_callback(40, "生成音乐...")
            
            # 计算生成长度（以token为单位）
            # MusicGen的采样率通常是32kHz，每秒约50个token
            max_new_tokens = int(request.duration * 50)
            
            # 生成音乐
            with torch.no_grad():
                audio_values = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    guidance_scale=request.guidance_scale,
                    temperature=request.temperature,
                    top_k=request.top_k,
                    top_p=request.top_p if request.top_p > 0 else None,
                    do_sample=True,
                    pad_token_id=processor.tokenizer.pad_token_id
                )
            
            progress_callback(80, "处理音频...")
            
            # 转换为numpy数组
            audio_array = audio_values[0].cpu().numpy()
            
            # 确保音频长度正确
            target_length = int(request.sample_rate * request.duration)
            if len(audio_array) > target_length:
                audio_array = audio_array[:target_length]
            elif len(audio_array) < target_length:
                # 如果太短，用零填充
                padding = target_length - len(audio_array)
                audio_array = np.pad(audio_array, (0, padding), mode='constant')
            
            progress_callback(90, "保存文件...")
            
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"music_{request.id[:8]}_{timestamp}.{request.output_format}"
            output_path = self.output_dir / filename
            
            # 保存音频文件
            if request.output_format == "wav":
                # 确保音频值在正确范围内
                audio_array = np.clip(audio_array, -1.0, 1.0)
                # 转换为16位整数
                audio_int16 = (audio_array * 32767).astype(np.int16)
                wavfile.write(str(output_path), request.sample_rate, audio_int16)
            else:
                # 对于其他格式，先保存为wav，然后转换
                temp_wav = output_path.with_suffix('.wav')
                audio_array = np.clip(audio_array, -1.0, 1.0)
                audio_int16 = (audio_array * 32767).astype(np.int16)
                wavfile.write(str(temp_wav), request.sample_rate, audio_int16)
                
                # 这里可以添加格式转换逻辑
                # 目前先使用wav格式
                output_path = temp_wav
            
            progress_callback(100, "完成")
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Sync generation error: {e}")
            raise ModelInferenceError(f"音乐生成失败: {str(e)}")
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        获取生成请求状态
        
        Args:
            request_id: 请求ID
            
        Returns:
            Dict: 请求状态信息，如果不存在返回None
        """
        # 先查找活动请求
        if request_id in self.active_requests:
            return self.active_requests[request_id].to_dict()
        
        # 再查找已完成请求
        if request_id in self.completed_requests:
            return self.completed_requests[request_id].to_dict()
        
        return None
    
    def cancel_request(self, request_id: str) -> bool:
        """
        取消生成请求
        
        Args:
            request_id: 请求ID
            
        Returns:
            bool: 成功取消返回True
        """
        if request_id in self.active_requests:
            request = self.active_requests[request_id]
            request.cancel()
            logger.info(f"Generation request cancelled: {request_id}")
            return True
        
        return False
    
    def list_requests(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出生成请求
        
        Args:
            status_filter: 状态过滤器
            
        Returns:
            List: 请求列表
        """
        all_requests = list(self.active_requests.values()) + list(self.completed_requests.values())
        
        if status_filter:
            all_requests = [req for req in all_requests if req.status.value == status_filter]
        
        # 按创建时间排序
        all_requests.sort(key=lambda x: x.created_at, reverse=True)
        
        return [req.to_dict() for req in all_requests]
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        获取生成统计信息
        
        Returns:
            Dict: 统计信息
        """
        active_count = len(self.active_requests)
        completed_count = len(self.completed_requests)
        
        # 统计各状态的数量
        status_counts = {}
        for request in list(self.active_requests.values()) + list(self.completed_requests.values()):
            status = request.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "active_requests": active_count,
            "completed_requests": completed_count,
            "total_requests": active_count + completed_count,
            "status_counts": status_counts,
            "model_ready": model_manager.is_ready()
        }

# 全局音乐生成器实例
music_generator = MusicGenerator()