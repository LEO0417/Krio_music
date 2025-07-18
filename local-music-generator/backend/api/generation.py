"""
音乐生成 API 端点

这个模块提供了音乐生成相关的API端点，包括：
1. 音乐生成请求处理
2. 生成状态查询和监控
3. 生成任务管理（取消、列表等）
4. 生成统计信息

技术说明：
- 提供RESTful API接口用于音乐生成
- 异步处理生成请求以避免阻塞
- 支持实时进度监控
- 详细的错误处理和状态报告
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field
import logging

from models.music_generator import music_generator, GenerationStatus
from api.errors import (
    ModelLoadError,
    ModelInferenceError,
    ResourceLimitExceededError,
    AudioProcessingError
)

# Configure logging
logger = logging.getLogger("api.generation")

router = APIRouter()

# Request/Response Models
class GenerationRequest(BaseModel):
    """音乐生成请求"""
    prompt: str = Field(
        description="文本提示，描述要生成的音乐",
        min_length=3,
        max_length=500,
        example="peaceful piano music with soft strings"
    )
    duration: float = Field(
        default=10.0,
        description="音乐长度（秒）",
        ge=1.0,
        le=30.0,
        example=15.0
    )
    guidance_scale: float = Field(
        default=3.0,
        description="引导比例，控制生成与提示的相关性",
        ge=1.0,
        le=10.0,
        example=3.0
    )
    temperature: float = Field(
        default=1.0,
        description="温度参数，控制生成的随机性",
        ge=0.1,
        le=2.0,
        example=1.0
    )
    top_k: int = Field(
        default=250,
        description="Top-K 采样参数",
        ge=1,
        le=1000,
        example=250
    )
    top_p: float = Field(
        default=0.0,
        description="Top-P 采样参数",
        ge=0.0,
        le=1.0,
        example=0.0
    )
    sample_rate: int = Field(
        default=32000,
        description="采样率",
        example=32000
    )
    output_format: str = Field(
        default="wav",
        description="输出格式",
        example="wav"
    )

class GenerationResponse(BaseModel):
    """音乐生成响应"""
    request_id: str = Field(description="生成请求ID")
    status: str = Field(description="生成状态")
    message: str = Field(description="状态消息")
    estimated_time: Optional[float] = Field(description="预计完成时间（秒）")

class GenerationStatusResponse(BaseModel):
    """生成状态响应"""
    id: str = Field(description="请求ID")
    prompt: str = Field(description="原始提示")
    status: str = Field(description="生成状态")
    progress: float = Field(description="进度百分比 (0-100)")
    created_at: str = Field(description="创建时间")
    started_at: Optional[str] = Field(description="开始时间")
    completed_at: Optional[str] = Field(description="完成时间")
    error_message: Optional[str] = Field(description="错误信息")
    result_path: Optional[str] = Field(description="结果文件路径")
    duration: float = Field(description="音乐长度")
    guidance_scale: float = Field(description="引导比例")
    temperature: float = Field(description="温度参数")
    sample_rate: int = Field(description="采样率")
    output_format: str = Field(description="输出格式")

class GenerationListResponse(BaseModel):
    """生成列表响应"""
    requests: List[GenerationStatusResponse] = Field(description="生成请求列表")
    total: int = Field(description="总数量")
    active: int = Field(description="活动请求数")
    completed: int = Field(description="已完成请求数")

class GenerationStatsResponse(BaseModel):
    """生成统计响应"""
    active_requests: int = Field(description="活动请求数")
    completed_requests: int = Field(description="已完成请求数")
    total_requests: int = Field(description="总请求数")
    status_counts: Dict[str, int] = Field(description="各状态请求数量")
    model_ready: bool = Field(description="模型是否就绪")

# API Endpoints

@router.post("/generate", response_model=GenerationResponse)
async def generate_music(request: GenerationRequest):
    """
    生成音乐
    
    Args:
        request: 音乐生成请求
        
    Returns:
        GenerationResponse: 生成请求响应
    """
    try:
        logger.info(f"Received music generation request: {request.prompt[:50]}...")
        
        # 启动音乐生成
        request_id = await music_generator.generate_music(
            prompt=request.prompt,
            duration=request.duration,
            guidance_scale=request.guidance_scale,
            temperature=request.temperature,
            top_k=request.top_k,
            top_p=request.top_p,
            sample_rate=request.sample_rate,
            output_format=request.output_format
        )
        
        logger.info(f"Music generation started with ID: {request_id}")
        
        return GenerationResponse(
            request_id=request_id,
            status="processing",
            message="音乐生成已开始",
            estimated_time=request.duration * 2  # 估计时间约为音乐长度的2倍
        )
        
    except ModelInferenceError as e:
        logger.error(f"Model inference error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"生成请求失败: {str(e)}"
        )
    except ResourceLimitExceededError as e:
        logger.error(f"Resource limit exceeded: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=f"资源不足: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in music generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成失败: {str(e)}"
        )

@router.get("/status/{request_id}", response_model=GenerationStatusResponse)
async def get_generation_status(request_id: str):
    """
    获取生成状态
    
    Args:
        request_id: 生成请求ID
        
    Returns:
        GenerationStatusResponse: 生成状态信息
    """
    try:
        status_info = music_generator.get_request_status(request_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"生成请求未找到: {request_id}"
            )
        
        return GenerationStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )

@router.post("/cancel/{request_id}")
async def cancel_generation(request_id: str):
    """
    取消生成请求
    
    Args:
        request_id: 生成请求ID
        
    Returns:
        Dict: 取消操作结果
    """
    try:
        success = music_generator.cancel_request(request_id)
        
        if success:
            logger.info(f"Generation request cancelled: {request_id}")
            return {
                "message": "生成请求已取消",
                "request_id": request_id,
                "status": "cancelled"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"生成请求未找到或无法取消: {request_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消失败: {str(e)}"
        )

@router.get("/list", response_model=GenerationListResponse)
async def list_generations(
    status_filter: Optional[str] = Query(
        default=None,
        description="状态过滤器",
        example="completed"
    ),
    limit: int = Query(
        default=50,
        description="返回数量限制",
        ge=1,
        le=100
    )
):
    """
    列出生成请求
    
    Args:
        status_filter: 状态过滤器
        limit: 返回数量限制
        
    Returns:
        GenerationListResponse: 生成请求列表
    """
    try:
        requests = music_generator.list_requests(status_filter=status_filter)
        
        # 应用数量限制
        limited_requests = requests[:limit]
        
        # 统计信息
        active_count = sum(1 for req in requests if req["status"] in ["pending", "processing"])
        completed_count = sum(1 for req in requests if req["status"] in ["completed", "failed", "cancelled"])
        
        return GenerationListResponse(
            requests=[GenerationStatusResponse(**req) for req in limited_requests],
            total=len(requests),
            active=active_count,
            completed=completed_count
        )
        
    except Exception as e:
        logger.error(f"Error listing generations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取列表失败: {str(e)}"
        )

@router.get("/stats", response_model=GenerationStatsResponse)
async def get_generation_stats():
    """
    获取生成统计信息
    
    Returns:
        GenerationStatsResponse: 生成统计信息
    """
    try:
        stats = music_generator.get_generation_stats()
        return GenerationStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting generation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )

@router.get("/result/{request_id}")
async def get_generation_result(request_id: str):
    """
    获取生成结果文件信息
    
    Args:
        request_id: 生成请求ID
        
    Returns:
        Dict: 结果文件信息
    """
    try:
        status_info = music_generator.get_request_status(request_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"生成请求未找到: {request_id}"
            )
        
        if status_info["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"生成尚未完成，当前状态: {status_info['status']}"
            )
        
        if not status_info["result_path"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="结果文件未找到"
            )
        
        # 获取文件信息
        from pathlib import Path
        result_path = Path(status_info["result_path"])
        
        if not result_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="结果文件不存在"
            )
        
        # 构建下载URL（假设音频文件通过 /audio 路径提供）
        filename = result_path.name
        download_url = f"/audio/{filename}"
        
        return {
            "request_id": request_id,
            "filename": filename,
            "file_size": result_path.stat().st_size,
            "download_url": download_url,
            "format": status_info["output_format"],
            "duration": status_info["duration"],
            "sample_rate": status_info["sample_rate"],
            "created_at": status_info["completed_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取结果失败: {str(e)}"
        )

@router.delete("/cleanup")
async def cleanup_completed_requests():
    """
    清理已完成的生成请求
    
    Returns:
        Dict: 清理操作结果
    """
    try:
        # 获取当前统计信息
        stats_before = music_generator.get_generation_stats()
        
        # 清理已完成的请求（保留最近的一些）
        # 这里可以实现更复杂的清理逻辑
        completed_before = stats_before["completed_requests"]
        
        # 简单的清理：如果已完成请求超过100个，清理到50个
        if completed_before > 100:
            # 获取所有已完成的请求
            all_requests = music_generator.list_requests()
            completed_requests = [req for req in all_requests if req["status"] in ["completed", "failed", "cancelled"]]
            
            # 按时间排序，保留最新的50个
            completed_requests.sort(key=lambda x: x["created_at"], reverse=True)
            to_keep = completed_requests[:50]
            to_remove = completed_requests[50:]
            
            # 从内存中移除旧的请求
            for req in to_remove:
                if req["id"] in music_generator.completed_requests:
                    del music_generator.completed_requests[req["id"]]
            
            cleaned_count = len(to_remove)
        else:
            cleaned_count = 0
        
        stats_after = music_generator.get_generation_stats()
        
        return {
            "message": "清理完成",
            "cleaned_requests": cleaned_count,
            "before": {
                "total": stats_before["total_requests"],
                "completed": stats_before["completed_requests"]
            },
            "after": {
                "total": stats_after["total_requests"],
                "completed": stats_after["completed_requests"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理失败: {str(e)}"
        )