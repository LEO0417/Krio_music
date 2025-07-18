"""
音频处理器 (Audio Processor)

这个模块实现了音频处理功能，包括：
1. 音频格式转换
2. 音频文件保存和管理
3. 音频元数据处理
4. 音频后处理效果

技术说明：
- 使用 librosa 进行音频分析和处理
- 使用 pydub 进行音频格式转换
- 支持多种音频格式（WAV、MP3、FLAC等）
- 实现音频标准化和质量优化
"""
import os
import json
import logging
import hashlib
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import torch

import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

from config.settings import AUDIO_DIR, AUDIO_SETTINGS
from api.errors import AudioProcessingError

# Configure logging
logger = logging.getLogger("audio_processor")

class AudioFormat(Enum):
    """音频格式枚举"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"

class AudioQuality(Enum):
    """音频质量枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LOSSLESS = "lossless"

class AudioMetadata:
    """音频元数据类"""
    
    def __init__(self, audio_id: str, **kwargs):
        self.id = audio_id
        self.title = kwargs.get("title", f"Generated Music {audio_id[:8]}")
        self.description = kwargs.get("description", "")
        self.artist = kwargs.get("artist", "MusicGen AI")
        self.album = kwargs.get("album", "Generated Music")
        self.genre = kwargs.get("genre", "AI Generated")
        self.duration = kwargs.get("duration", 0.0)
        self.sample_rate = kwargs.get("sample_rate", 32000)
        self.channels = kwargs.get("channels", 1)
        self.format = kwargs.get("format", "wav")
        self.file_size = kwargs.get("file_size", 0)
        self.file_path = kwargs.get("file_path", "")
        self.created_at = kwargs.get("created_at", datetime.now())
        self.prompt = kwargs.get("prompt", "")
        self.parameters = kwargs.get("parameters", {})
        self.checksum = kwargs.get("checksum", "")
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "format": self.format,
            "file_size": self.file_size,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "prompt": self.prompt,
            "parameters": self.parameters,
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioMetadata':
        """从字典创建AudioMetadata实例"""
        # 处理日期时间字符串
        if isinstance(data.get("created_at"), str):
            try:
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            except ValueError:
                data["created_at"] = datetime.now()
        
        return cls(data.get("id", ""), **data)

class AudioProcessor:
    """音频处理器主类"""
    
    def __init__(self):
        self.audio_dir = Path(AUDIO_DIR)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 音频处理配置
        self.supported_formats = {
            AudioFormat.WAV: {"extension": "wav", "codec": None},
            AudioFormat.MP3: {"extension": "mp3", "codec": "mp3"},
            AudioFormat.FLAC: {"extension": "flac", "codec": "flac"},
            AudioFormat.OGG: {"extension": "ogg", "codec": "libvorbis"},
            AudioFormat.M4A: {"extension": "m4a", "codec": "aac"}
        }
        
        self.quality_settings = {
            AudioQuality.LOW: {"bitrate": "128k", "sample_rate": 22050},
            AudioQuality.MEDIUM: {"bitrate": "192k", "sample_rate": 32000},
            AudioQuality.HIGH: {"bitrate": "320k", "sample_rate": 44100},
            AudioQuality.LOSSLESS: {"bitrate": None, "sample_rate": 44100}
        }
        
        # 元数据存储
        self.metadata_file = self.audio_dir / "metadata.json"
        self.metadata_cache = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, AudioMetadata]:
        """加载音频元数据"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                audio_id: AudioMetadata.from_dict(metadata) 
                for audio_id, metadata in data.items()
            }
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}
    
    def _save_metadata(self):
        """保存音频元数据"""
        try:
            data = {
                audio_id: metadata.to_dict() 
                for audio_id, metadata in self.metadata_cache.items()
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
            return ""
    
    def process_audio(
        self,
        audio_data: Union[np.ndarray, torch.Tensor],
        audio_id: str,
        sample_rate: int = 32000,
        output_format: AudioFormat = AudioFormat.WAV,
        quality: AudioQuality = AudioQuality.HIGH,
        metadata: Optional[Dict[str, Any]] = None,
        apply_effects: bool = True
    ) -> str:
        """
        处理音频数据并保存
        
        Args:
            audio_data: 音频数据
            audio_id: 音频ID
            sample_rate: 采样率
            output_format: 输出格式
            quality: 音频质量
            metadata: 元数据
            apply_effects: 是否应用音频效果
            
        Returns:
            str: 输出文件路径
        """
        try:
            # 转换数据类型
            if isinstance(audio_data, torch.Tensor):
                audio_data = audio_data.cpu().numpy()
            
            # 确保数据格式正确
            if audio_data.ndim == 1:
                audio_data = audio_data.reshape(1, -1)
            elif audio_data.ndim == 2 and audio_data.shape[0] > audio_data.shape[1]:
                audio_data = audio_data.T
            
            # 标准化音频数据
            audio_data = self._normalize_audio(audio_data)
            
            # 应用音频效果
            if apply_effects:
                audio_data = self._apply_audio_effects(audio_data, sample_rate)
            
            # 调整采样率
            target_sample_rate = self.quality_settings[quality]["sample_rate"]
            if sample_rate != target_sample_rate:
                audio_data = self._resample_audio(audio_data, sample_rate, target_sample_rate)
                sample_rate = target_sample_rate
            
            # 保存音频文件
            output_path = self._save_audio_file(
                audio_data, audio_id, sample_rate, output_format, quality
            )
            
            # 创建和保存元数据
            audio_metadata = self._create_metadata(
                audio_id, output_path, audio_data, sample_rate, output_format, metadata
            )
            
            self.metadata_cache[audio_id] = audio_metadata
            self._save_metadata()
            
            logger.info(f"Audio processed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            raise AudioProcessingError(f"Failed to process audio: {str(e)}")
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """标准化音频数据"""
        try:
            # 检查是否有有效的音频数据
            if np.all(audio_data == 0):
                logger.warning("Audio data is all zeros")
                return audio_data
            
            # 计算RMS并标准化
            rms = np.sqrt(np.mean(audio_data**2))
            if rms > 0:
                # 标准化到目标RMS (-20dB)
                target_rms = 0.1
                audio_data = audio_data * (target_rms / rms)
            
            # 限制幅度防止失真
            audio_data = np.clip(audio_data, -0.95, 0.95)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            return audio_data
    
    def _apply_audio_effects(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """应用音频效果"""
        try:
            # 去除直流分量
            audio_data = audio_data - np.mean(audio_data)
            
            # 应用轻微的压缩
            audio_data = self._apply_compression(audio_data)
            
            # 应用轻微的EQ
            audio_data = self._apply_eq(audio_data, sample_rate)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error applying audio effects: {e}")
            return audio_data
    
    def _apply_compression(self, audio_data: np.ndarray, threshold: float = 0.5, ratio: float = 2.0) -> np.ndarray:
        """应用动态范围压缩"""
        try:
            # 简单的软压缩实现
            abs_audio = np.abs(audio_data)
            compressed = np.where(
                abs_audio > threshold,
                threshold + (abs_audio - threshold) / ratio,
                abs_audio
            )
            
            # 保持原始符号
            return np.sign(audio_data) * compressed
            
        except Exception as e:
            logger.error(f"Error applying compression: {e}")
            return audio_data
    
    def _apply_eq(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """应用简单的EQ"""
        try:
            # 使用librosa应用高通滤波器去除低频噪声
            if audio_data.shape[0] == 1:
                audio_mono = audio_data[0]
            else:
                audio_mono = np.mean(audio_data, axis=0)
            
            # 应用高通滤波器 (80Hz)
            filtered = librosa.effects.preemphasis(audio_mono, coef=0.97)
            
            # 如果原始音频是立体声，复制到所有通道
            if audio_data.shape[0] > 1:
                return np.array([filtered] * audio_data.shape[0])
            else:
                return filtered.reshape(1, -1)
                
        except Exception as e:
            logger.error(f"Error applying EQ: {e}")
            return audio_data
    
    def _resample_audio(self, audio_data: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """重采样音频"""
        try:
            if audio_data.shape[0] == 1:
                # 单声道
                resampled = librosa.resample(audio_data[0], orig_sr=orig_sr, target_sr=target_sr)
                return resampled.reshape(1, -1)
            else:
                # 多声道
                resampled_channels = []
                for channel in audio_data:
                    resampled = librosa.resample(channel, orig_sr=orig_sr, target_sr=target_sr)
                    resampled_channels.append(resampled)
                return np.array(resampled_channels)
                
        except Exception as e:
            logger.error(f"Error resampling audio: {e}")
            return audio_data
    
    def _save_audio_file(
        self,
        audio_data: np.ndarray,
        audio_id: str,
        sample_rate: int,
        output_format: AudioFormat,
        quality: AudioQuality
    ) -> str:
        """保存音频文件"""
        try:
            # 创建输出文件名
            extension = self.supported_formats[output_format]["extension"]
            filename = f"{audio_id}.{extension}"
            output_path = self.audio_dir / filename
            
            # 确保音频数据格式正确
            if audio_data.ndim == 2 and audio_data.shape[0] == 1:
                audio_data = audio_data[0]  # 转换为一维数组用于单声道
            elif audio_data.ndim == 2:
                audio_data = audio_data.T  # 转置为 (samples, channels)
            
            if output_format == AudioFormat.WAV:
                # 直接保存WAV文件
                sf.write(str(output_path), audio_data, sample_rate)
            else:
                # 先保存为临时WAV文件，然后转换
                temp_wav = self.audio_dir / f"{audio_id}_temp.wav"
                sf.write(str(temp_wav), audio_data, sample_rate)
                
                # 使用pydub转换格式
                self._convert_audio_format(str(temp_wav), str(output_path), output_format, quality)
                
                # 删除临时文件
                temp_wav.unlink()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            raise AudioProcessingError(f"Failed to save audio file: {str(e)}")
    
    def _convert_audio_format(
        self, 
        input_path: str, 
        output_path: str, 
        output_format: AudioFormat, 
        quality: AudioQuality
    ):
        """转换音频格式"""
        try:
            # 加载音频文件
            audio = AudioSegment.from_wav(input_path)
            
            # 应用质量设置
            quality_config = self.quality_settings[quality]
            
            # 调整采样率
            if quality_config["sample_rate"] != audio.frame_rate:
                audio = audio.set_frame_rate(quality_config["sample_rate"])
            
            # 设置导出参数
            export_params = {}
            if quality_config["bitrate"] and output_format != AudioFormat.WAV:
                export_params["bitrate"] = quality_config["bitrate"]
            
            # 应用标准化
            audio = normalize(audio)
            
            # 导出文件
            if output_format == AudioFormat.MP3:
                audio.export(output_path, format="mp3", **export_params)
            elif output_format == AudioFormat.FLAC:
                audio.export(output_path, format="flac", **export_params)
            elif output_format == AudioFormat.OGG:
                audio.export(output_path, format="ogg", **export_params)
            elif output_format == AudioFormat.M4A:
                audio.export(output_path, format="mp4", **export_params)
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            raise AudioProcessingError(f"Failed to convert audio format: {str(e)}")
    
    def _create_metadata(
        self,
        audio_id: str,
        file_path: str,
        audio_data: np.ndarray,
        sample_rate: int,
        output_format: AudioFormat,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AudioMetadata:
        """创建音频元数据"""
        try:
            # 计算音频时长
            duration = audio_data.shape[-1] / sample_rate
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 计算校验和
            checksum = self._calculate_checksum(file_path)
            
            # 创建元数据
            metadata_dict = {
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": audio_data.shape[0] if audio_data.ndim == 2 else 1,
                "format": output_format.value,
                "file_size": file_size,
                "file_path": file_path,
                "checksum": checksum,
                "created_at": datetime.now()
            }
            
            # 添加自定义元数据
            if metadata:
                metadata_dict.update(metadata)
            
            return AudioMetadata(audio_id, **metadata_dict)
            
        except Exception as e:
            logger.error(f"Error creating metadata: {e}")
            raise AudioProcessingError(f"Failed to create metadata: {str(e)}")
    
    def get_audio_metadata(self, audio_id: str) -> Optional[AudioMetadata]:
        """获取音频元数据"""
        return self.metadata_cache.get(audio_id)
    
    def get_all_audio_metadata(self) -> List[AudioMetadata]:
        """获取所有音频元数据"""
        return list(self.metadata_cache.values())
    
    def update_audio_metadata(self, audio_id: str, metadata: Dict[str, Any]) -> bool:
        """更新音频元数据"""
        try:
            if audio_id not in self.metadata_cache:
                return False
            
            audio_metadata = self.metadata_cache[audio_id]
            
            # 更新允许的字段
            updatable_fields = ["title", "description", "artist", "album", "genre"]
            for field in updatable_fields:
                if field in metadata:
                    setattr(audio_metadata, field, metadata[field])
            
            self._save_metadata()
            return True
            
        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
            return False
    
    def delete_audio(self, audio_id: str) -> bool:
        """删除音频文件和元数据"""
        try:
            if audio_id not in self.metadata_cache:
                return False
            
            # 删除文件
            audio_metadata = self.metadata_cache[audio_id]
            file_path = Path(audio_metadata.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # 删除元数据
            del self.metadata_cache[audio_id]
            self._save_metadata()
            
            logger.info(f"Audio deleted: {audio_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting audio: {e}")
            return False
    
    def convert_audio_format(
        self,
        audio_id: str,
        target_format: AudioFormat,
        quality: AudioQuality = AudioQuality.HIGH
    ) -> str:
        """转换已存在音频的格式"""
        try:
            if audio_id not in self.metadata_cache:
                raise AudioProcessingError(f"Audio {audio_id} not found")
            
            audio_metadata = self.metadata_cache[audio_id]
            source_path = audio_metadata.file_path
            
            if not os.path.exists(source_path):
                raise AudioProcessingError(f"Source file not found: {source_path}")
            
            # 创建新的文件路径
            extension = self.supported_formats[target_format]["extension"]
            new_filename = f"{audio_id}_converted.{extension}"
            output_path = self.audio_dir / new_filename
            
            # 转换格式
            self._convert_audio_format(source_path, str(output_path), target_format, quality)
            
            logger.info(f"Audio format converted: {source_path} -> {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            raise AudioProcessingError(f"Failed to convert audio format: {str(e)}")
    
    def get_audio_analysis(self, audio_id: str) -> Dict[str, Any]:
        """获取音频分析信息"""
        try:
            if audio_id not in self.metadata_cache:
                raise AudioProcessingError(f"Audio {audio_id} not found")
            
            audio_metadata = self.metadata_cache[audio_id]
            file_path = audio_metadata.file_path
            
            if not os.path.exists(file_path):
                raise AudioProcessingError(f"Audio file not found: {file_path}")
            
            # 加载音频进行分析
            audio_data, sample_rate = librosa.load(file_path, sr=None)
            
            # 计算音频特征
            analysis = {
                "duration": len(audio_data) / sample_rate,
                "sample_rate": sample_rate,
                "channels": 1,  # librosa默认转换为单声道
                "rms_energy": float(np.sqrt(np.mean(audio_data**2))),
                "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(audio_data))),
                "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(audio_data, sr=sample_rate))),
                "spectral_rolloff": float(np.mean(librosa.feature.spectral_rolloff(audio_data, sr=sample_rate))),
                "tempo": float(librosa.beat.tempo(audio_data, sr=sample_rate)[0]),
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing audio: {e}")
            raise AudioProcessingError(f"Failed to analyze audio: {str(e)}")
    
    def cleanup_old_files(self, max_age_days: int = 30) -> int:
        """清理旧音频文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            deleted_count = 0
            
            for audio_id, metadata in list(self.metadata_cache.items()):
                if metadata.created_at < cutoff_date:
                    if self.delete_audio(audio_id):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old audio files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0

# 全局音频处理器实例
audio_processor = AudioProcessor()