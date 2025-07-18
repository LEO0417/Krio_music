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
        model_info = model_manager.get_all_model_info()
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

@router.get("/config/{model_name}")
async def get_model_config(model_name: str):
    """
    获取指定模型的配置信息
    
    Args:
        model_name: 模型名称
        
    Returns:
        Dict: 模型配置信息
    """
    try:
        config_info = model_manager.get_model_configuration(model_name)
        
        if "error" in config_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=config_info["error"]
            )
        
        return config_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model configuration: {str(e)}"
        )

@router.get("/cache")
async def get_cache_info():
    """
    获取模型缓存信息
    
    Returns:
        Dict: 缓存统计信息
    """
    try:
        cache_info = model_manager.get_cache_statistics()
        return cache_info
        
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache information: {str(e)}"
        )

@router.delete("/cache")
async def clear_cache(
    model_name: Optional[str] = Query(
        default=None,
        description="要清理的模型名称，不指定则清理所有缓存"
    )
):
    """
    清理模型缓存
    
    Args:
        model_name: 要清理的模型名称
        
    Returns:
        Dict: 清理结果
    """
    try:
        success = model_manager.clear_model_cache(model_name)
        
        if success:
            message = f"Cache cleared for model: {model_name}" if model_name else "All caches cleared"
            return {
                "message": message,
                "success": True,
                "cleared_model": model_name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear cache"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.get("/validate/{model_name}")
async def validate_model(model_name: str):
    """
    验证模型系统要求
    
    Args:
        model_name: 模型名称
        
    Returns:
        Dict: 验证结果
    """
    try:
        from config.settings import validate_model_requirements
        
        validation_result = validate_model_requirements(model_name)
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate model: {str(e)}"
        )

@router.get("/supported")
async def get_supported_models():
    """
    获取支持的模型列表
    
    Returns:
        Dict: 支持的模型列表
    """
    try:
        from config.settings import get_supported_models
        
        supported_models = get_supported_models()
        return {
            "supported_models": supported_models,
            "count": len(supported_models)
        }
        
    except Exception as e:
        logger.error(f"Error getting supported models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported models: {str(e)}"
        ) 