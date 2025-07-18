"""
音频管理 API 端点

这个模块提供了音频管理相关的API端点，包括：
1. 音频文件管理
2. 音频元数据操作
3. 音频格式转换
4. 音频分析和统计

技术说明：
- 提供RESTful API接口用于音频文件管理
- 支持音频格式转换和质量调整
- 提供音频分析和元数据管理
- 支持音频文件的下载和删除
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Query, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import logging
import os
from pathlib import Path

from audio.audio_processor import audio_processor, AudioFormat, AudioQuality
from api.errors import AudioProcessingError

# Configure logging
logger = logging.getLogger("api.audio")

router = APIRouter()

# Request/Response Models
class AudioMetadataResponse(BaseModel):
    """音频元数据响应"""
    id: str = Field(description="音频ID")
    title: str = Field(description="音频标题")
    description: str = Field(description="音频描述")
    artist: str = Field(description="艺术家")
    album: str = Field(description="专辑")
    genre: str = Field(description="流派")
    duration: float = Field(description="时长（秒）")
    sample_rate: int = Field(description="采样率")
    channels: int = Field(description="声道数")
    format: str = Field(description="音频格式")
    file_size: int = Field(description="文件大小（字节）")
    file_path: str = Field(description="文件路径")
    created_at: str = Field(description="创建时间")
    prompt: str = Field(description="生成提示")
    parameters: Dict[str, Any] = Field(description="生成参数")
    checksum: str = Field(description="文件校验和")

class AudioListResponse(BaseModel):
    """音频列表响应"""
    audios: List[AudioMetadataResponse] = Field(description="音频列表")
    total: int = Field(description="总数量")

class AudioUpdateRequest(BaseModel):
    """音频更新请求"""
    title: Optional[str] = Field(None, description="音频标题")
    description: Optional[str] = Field(None, description="音频描述")
    artist: Optional[str] = Field(None, description="艺术家")
    album: Optional[str] = Field(None, description="专辑")
    genre: Optional[str] = Field(None, description="流派")

class AudioConversionRequest(BaseModel):
    """音频转换请求"""
    target_format: AudioFormat = Field(description="目标格式")
    quality: AudioQuality = Field(default=AudioQuality.HIGH, description="音频质量")

class AudioAnalysisResponse(BaseModel):
    """音频分析响应"""
    duration: float = Field(description="时长（秒）")
    sample_rate: int = Field(description="采样率")
    channels: int = Field(description="声道数")
    rms_energy: float = Field(description="RMS能量")
    zero_crossing_rate: float = Field(description="过零率")
    spectral_centroid: float = Field(description="频谱重心")
    spectral_rolloff: float = Field(description="频谱滚降")
    tempo: float = Field(description="节拍（BPM）")

# API Endpoints

@router.get("/list", response_model=AudioListResponse)
async def list_audio():
    """
    获取音频文件列表
    
    Returns:
        AudioListResponse: 音频文件列表
    """
    try:
        metadata_list = audio_processor.get_all_audio_metadata()
        
        audio_responses = []
        for metadata in metadata_list:
            audio_responses.append(AudioMetadataResponse(**metadata.to_dict()))
        
        # 按创建时间排序（最新的在前）
        audio_responses.sort(key=lambda x: x.created_at, reverse=True)
        
        return AudioListResponse(
            audios=audio_responses,
            total=len(audio_responses)
        )
        
    except Exception as e:
        logger.error(f"Error listing audio files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list audio files: {str(e)}"
        )

@router.get("/{audio_id}", response_model=AudioMetadataResponse)
async def get_audio_metadata(audio_id: str):
    """
    获取音频元数据
    
    Args:
        audio_id: 音频ID
        
    Returns:
        AudioMetadataResponse: 音频元数据
    """
    try:
        metadata = audio_processor.get_audio_metadata(audio_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio {audio_id} not found"
            )
        
        return AudioMetadataResponse(**metadata.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audio metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audio metadata: {str(e)}"
        )

@router.put("/{audio_id}", response_model=AudioMetadataResponse)
async def update_audio_metadata(audio_id: str, request: AudioUpdateRequest):
    """
    更新音频元数据
    
    Args:
        audio_id: 音频ID
        request: 更新请求
        
    Returns:
        AudioMetadataResponse: 更新后的音频元数据
    """
    try:
        # 检查音频是否存在
        metadata = audio_processor.get_audio_metadata(audio_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio {audio_id} not found"
            )
        
        # 准备更新数据
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.description is not None:
            update_data["description"] = request.description
        if request.artist is not None:
            update_data["artist"] = request.artist
        if request.album is not None:
            update_data["album"] = request.album
        if request.genre is not None:
            update_data["genre"] = request.genre
        
        # 更新元数据
        success = audio_processor.update_audio_metadata(audio_id, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update audio metadata"
            )
        
        # 返回更新后的元数据
        updated_metadata = audio_processor.get_audio_metadata(audio_id)
        return AudioMetadataResponse(**updated_metadata.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating audio metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update audio metadata: {str(e)}"
        )

@router.delete("/{audio_id}")
async def delete_audio(audio_id: str):
    """
    删除音频文件
    
    Args:
        audio_id: 音频ID
        
    Returns:
        Dict: 删除结果
    """
    try:
        success = audio_processor.delete_audio(audio_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio {audio_id} not found"
            )
        
        logger.info(f"Audio {audio_id} deleted successfully")
        return {
            "message": f"Audio {audio_id} deleted successfully",
            "audio_id": audio_id,
            "status": "deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete audio: {str(e)}"
        )

@router.get("/{audio_id}/download")
async def download_audio(audio_id: str):
    """
    下载音频文件
    
    Args:
        audio_id: 音频ID
        
    Returns:
        FileResponse: 音频文件
    """
    try:
        metadata = audio_processor.get_audio_metadata(audio_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio {audio_id} not found"
            )
        
        file_path = metadata.file_path
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found on disk"
            )
        
        # 构造下载文件名
        file_extension = Path(file_path).suffix
        download_filename = f"{metadata.title.replace(' ', '_')}{file_extension}"
        
        # 根据格式设置媒体类型
        media_type_map = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4"
        }
        
        media_type = media_type_map.get(file_extension.lower(), "audio/wav")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=download_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download audio: {str(e)}"
        )

@router.post("/{audio_id}/convert")
async def convert_audio_format(audio_id: str, request: AudioConversionRequest):
    """
    转换音频格式
    
    Args:
        audio_id: 音频ID
        request: 转换请求
        
    Returns:
        Dict: 转换结果
    """
    try:
        # 检查音频是否存在
        metadata = audio_processor.get_audio_metadata(audio_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio {audio_id} not found"
            )
        
        # 执行格式转换
        converted_path = audio_processor.convert_audio_format(
            audio_id=audio_id,
            target_format=request.target_format,
            quality=request.quality
        )
        
        return {
            "message": "Audio format converted successfully",
            "audio_id": audio_id,
            "original_format": metadata.format,
            "target_format": request.target_format.value,
            "quality": request.quality.value,
            "converted_path": converted_path,
            "status": "converted"
        }
        
    except HTTPException:
        raise
    except AudioProcessingError as e:
        logger.error(f"Audio processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error converting audio format: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert audio format: {str(e)}"
        )

@router.get("/{audio_id}/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio(audio_id: str):
    """
    分析音频特征
    
    Args:
        audio_id: 音频ID
        
    Returns:
        AudioAnalysisResponse: 音频分析结果
    """
    try:
        # 检查音频是否存在
        metadata = audio_processor.get_audio_metadata(audio_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio {audio_id} not found"
            )
        
        # 执行音频分析
        analysis = audio_processor.get_audio_analysis(audio_id)
        
        return AudioAnalysisResponse(**analysis)
        
    except HTTPException:
        raise
    except AudioProcessingError as e:
        logger.error(f"Audio processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio analysis failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error analyzing audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze audio: {str(e)}"
        )

@router.get("/stats/overview")
async def get_audio_stats():
    """
    获取音频统计信息
    
    Returns:
        Dict: 音频统计信息
    """
    try:
        metadata_list = audio_processor.get_all_audio_metadata()
        
        if not metadata_list:
            return {
                "total_files": 0,
                "total_duration": 0,
                "total_size": 0,
                "formats": {},
                "avg_duration": 0,
                "avg_file_size": 0
            }
        
        # 计算统计信息
        total_files = len(metadata_list)
        total_duration = sum(metadata.duration for metadata in metadata_list)
        total_size = sum(metadata.file_size for metadata in metadata_list)
        
        # 格式分布
        formats = {}
        for metadata in metadata_list:
            format_name = metadata.format
            formats[format_name] = formats.get(format_name, 0) + 1
        
        # 平均值
        avg_duration = total_duration / total_files
        avg_file_size = total_size / total_files
        
        return {
            "total_files": total_files,
            "total_duration": round(total_duration, 2),
            "total_size": total_size,
            "formats": formats,
            "avg_duration": round(avg_duration, 2),
            "avg_file_size": round(avg_file_size, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting audio stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audio stats: {str(e)}"
        )

@router.delete("/cleanup")
async def cleanup_old_files(
    max_age_days: int = Query(default=30, ge=1, le=365, description="文件最大保存天数")
):
    """
    清理旧音频文件
    
    Args:
        max_age_days: 文件最大保存天数
        
    Returns:
        Dict: 清理结果
    """
    try:
        deleted_count = audio_processor.cleanup_old_files(max_age_days)
        
        return {
            "message": f"Cleaned up {deleted_count} old audio files",
            "deleted_count": deleted_count,
            "max_age_days": max_age_days,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup old files: {str(e)}"
        )