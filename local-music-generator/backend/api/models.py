"""
模型管理 API 端点

这个模块提供了与模型管理相关的API端点，包括：
1. 模型状态查询和监控
2. 模型加载和卸载控制
3. 模型健康检查和资源监控
4. 模型配置管理

技术说明：
- 提供RESTful API接口用于模型生命周期管理
- 异步处理模型操作以避免阻塞
- 详细的错误处理和状态报告
- 支持模型资源使用监控
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field
import logging

from models.model_manager import model_manager, ModelStatus
from api.errors import (
    ModelLoadError,
    ModelInferenceError,
    ResourceLimitExceededError,
    AudioProcessingError
)

# Configure logging
logger = logging.getLogger("api.models")

router = APIRouter()

# Request/Response Models
class ModelLoadRequest(BaseModel):
    """模型加载请求"""
    model_config = {"protected_namespaces": ()}
    
    model_name: Optional[str] = Field(
        default=None,
        description="模型名称，默认使用facebook/musicgen-small"
    )
    force: bool = Field(
        default=False,
        description="是否强制重新加载已加载的模型"
    )

class ModelStatusResponse(BaseModel):
    """模型状态响应"""
    model_config = {"protected_namespaces": ()}
    
    name: str = Field(description="模型名称")
    status: str = Field(description="模型状态")
    loaded_at: Optional[str] = Field(description="加载时间")
    error_message: Optional[str] = Field(description="错误信息")
    device: str = Field(description="运行设备")
    memory_usage_mb: int = Field(description="内存使用量(MB)")
    inference_count: int = Field(description="推理次数")
    last_inference_time: Optional[str] = Field(description="最后推理时间")
    model_size_mb: int = Field(description="模型大小(MB)")

class ModelHealthResponse(BaseModel):
    """模型健康检查响应"""
    model_config = {"protected_namespaces": ()}
    
    model_loaded: bool = Field(description="模型是否已加载")
    model_status: str = Field(description="模型状态")
    device: str = Field(description="运行设备")
    memory_usage_mb: int = Field(description="内存使用量(MB)")
    system_memory_percent: float = Field(description="系统内存使用百分比")
    timestamp: str = Field(description="检查时间戳")

class ResourceInfoResponse(BaseModel):
    """资源信息响应"""
    system: Dict[str, Any] = Field(description="系统资源信息")
    model: Dict[str, Any] = Field(description="模型资源信息")
    gpu: Optional[Dict[str, Any]] = Field(description="GPU信息")

# API Endpoints

@router.get("/status", response_model=ModelStatusResponse)
async def get_model_status():
    """
    获取模型状态信息
    
    Returns:
        ModelStatusResponse: 详细的模型状态信息
    """
    try:
        status_info = model_manager.get_model_status()
        logger.debug(f"Model status retrieved: {status_info['status']}")
        return ModelStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model status: {str(e)}"
        )

@router.post("/load")
async def load_model(
    request: ModelLoadRequest,
    background_tasks: BackgroundTasks
):
    """
    加载模型
    
    Args:
        request: 模型加载请求
        background_tasks: 后台任务管理器
        
    Returns:
        Dict: 加载操作结果
    """
    try:
        # 检查是否需要强制重新加载
        if not request.force and model_manager.is_ready():
            current_status = model_manager.get_model_status()
            return {
                "message": "Model is already loaded",
                "model_name": current_status["name"],
                "status": current_status["status"],
                "device": current_status["device"]
            }
        
        # 如果强制重新加载，先卸载当前模型
        if request.force and model_manager.is_ready():
            logger.info("Force reload requested, unloading current model")
            await model_manager.unload_model()
        
        # 开始加载模型
        logger.info(f"Starting model load: {request.model_name}")
        success = await model_manager.load_model(request.model_name)
        
        if success:
            status_info = model_manager.get_model_status()
            return {
                "message": "Model loaded successfully",
                "model_name": status_info["name"],
                "status": status_info["status"],
                "device": status_info["device"],
                "memory_usage_mb": status_info["memory_usage_mb"],
                "model_size_mb": status_info["model_size_mb"]
            }
        else:
            status_info = model_manager.get_model_status()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load model: {status_info.get('error_message', 'Unknown error')}"
            )
            
    except ModelLoadError as e:
        logger.error(f"Model load error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model loading failed: {str(e)}"
        )
    except ResourceLimitExceededError as e:
        logger.error(f"Resource limit exceeded: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=f"Insufficient resources to load model: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error loading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.post("/unload")
async def unload_model():
    """
    卸载模型以释放资源
    
    Returns:
        Dict: 卸载操作结果
    """
    try:
        if not model_manager.is_ready():
            return {
                "message": "Model is not loaded",
                "status": "not_loaded"
            }
        
        logger.info("Starting model unload")
        success = await model_manager.unload_model()
        
        if success:
            return {
                "message": "Model unloaded successfully",
                "status": "not_loaded"
            }
        else:
            status_info = model_manager.get_model_status()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unload model: {status_info.get('error_message', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error unloading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}"
        )

@router.get("/health", response_model=ModelHealthResponse)
async def model_health_check():
    """
    执行模型健康检查
    
    Returns:
        ModelHealthResponse: 模型健康状态信息
    """
    try:
        health_info = await model_manager.health_check()
        logger.debug(f"Model health check completed: {health_info['model_status']}")
        return ModelHealthResponse(**health_info)
        
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/resources", response_model=ResourceInfoResponse)
async def get_resource_info():
    """
    获取详细的资源使用信息
    
    Returns:
        ResourceInfoResponse: 系统和模型资源使用信息
    """
    try:
        resource_info = await model_manager.get_resource_info()
        logger.debug("Resource information retrieved")
        return ResourceInfoResponse(**resource_info)
        
    except Exception as e:
        logger.error(f"Error getting resource info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource information: {str(e)}"
        )

@router.get("/info")
async def get_model_info():
    """
    获取模型的详细信息和配置
    
    Returns:
        Dict: 模型配置和能力信息
    """
    try:
        status_info = model_manager.get_model_status()
        
        # 基础信息
        model_info = {
            "current_model": status_info,
            "supported_models": [
                "facebook/musicgen-small",
                "facebook/musicgen-medium", 
                "facebook/musicgen-large"
            ],
            "capabilities": {
                "max_duration": 30,  # seconds
                "sample_rate": 32000,
                "supported_formats": ["wav", "mp3"],
                "text_conditioning": True,
                "unconditional_generation": True
            },
            "system_requirements": {
                "min_ram_gb": 4,
                "recommended_ram_gb": 8,
                "gpu_memory_gb": 4,
                "disk_space_gb": 5
            }
        }
        
        # 如果模型已加载，添加更多详细信息
        if model_manager.is_ready():
            model_info["model_details"] = {
                "is_ready": True,
                "can_generate": True,
                "current_device": status_info["device"],
                "memory_usage_mb": status_info["memory_usage_mb"],
                "inference_count": status_info["inference_count"]
            }
        else:
            model_info["model_details"] = {
                "is_ready": False,
                "can_generate": False,
                "status": status_info["status"],
                "error": status_info.get("error_message")
            }
        
        return model_info
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model information: {str(e)}"
        )

@router.post("/reload")
async def reload_model():
    """
    重新加载当前模型（卸载后重新加载）
    
    Returns:
        Dict: 重新加载操作结果
    """
    try:
        current_status = model_manager.get_model_status()
        current_model = current_status.get("name")
        
        if not current_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No model currently loaded to reload"
            )
        
        logger.info(f"Reloading model: {current_model}")
        
        # 卸载当前模型
        await model_manager.unload_model()
        
        # 重新加载模型
        success = await model_manager.load_model(current_model)
        
        if success:
            status_info = model_manager.get_model_status()
            return {
                "message": "Model reloaded successfully",
                "model_name": status_info["name"],
                "status": status_info["status"],
                "device": status_info["device"]
            }
        else:
            status_info = model_manager.get_model_status()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reload model: {status_info.get('error_message', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reloading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload model: {str(e)}"
        )

@router.get("/logs")
async def get_model_logs(
    lines: int = Query(default=50, ge=1, le=1000, description="返回的日志行数")
):
    """
    获取模型相关的日志信息
    
    Args:
        lines: 返回的日志行数
        
    Returns:
        Dict: 日志信息
    """
    try:
        # 这里可以实现从日志文件读取相关日志的逻辑
        # 目前返回基本的状态信息
        status_info = model_manager.get_model_status()
        
        # 生成模拟的日志条目（在实际实现中应该从真实的日志文件读取）
        logs = []
        if status_info["loaded_at"]:
            logs.append(f"[{status_info['loaded_at']}] Model {status_info['name']} loaded on {status_info['device']}")
        
        if status_info["last_inference_time"]:
            logs.append(f"[{status_info['last_inference_time']}] Inference completed (total: {status_info['inference_count']})")
        
        if status_info["error_message"]:
            logs.append(f"[ERROR] {status_info['error_message']}")
        
        return {
            "logs": logs,
            "total_lines": len(logs),
            "model_status": status_info["status"]
        }
        
    except Exception as e:
        logger.error(f"Error getting model logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model logs: {str(e)}"
        ) 