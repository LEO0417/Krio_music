"""
音乐生成 API 端点

这个模块提供了音乐生成相关的API端点，包括：
1. 音乐生成请求处理
2. 生成任务状态查询
3. 任务管理和控制
4. 生成历史记录管理

技术说明：
- 提供RESTful API接口用于音乐生成
- 异步处理生成任务
- 详细的请求验证和错误处理
- 支持任务进度跟踪和取消
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import logging
import os
from pathlib import Path

from models.music_generator import music_generator, GenerationStatus
from models.model_manager import model_manager
from api.errors import (
    ValidationError,
    ModelInferenceError,
    ModelLoadError,
    AudioProcessingError
)

# Configure logging
logger = logging.getLogger("api.generation")

router = APIRouter()

# Request/Response Models
class GenerationRequest(BaseModel):
    """音乐生成请求"""
    prompt: str = Field(
        description="音乐生成的文本提示",
        min_length=1,
        max_length=256,
        example="一首轻松愉快的钢琴曲，带有柔和的弦乐伴奏"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="生成参数",
        example={
            "duration": 15,
            "temperature": 1.0,
            "style": "classical",
            "top_k": 250,
            "guidance_scale": 3.0
        }
    )

class GenerationResponse(BaseModel):
    """音乐生成响应"""
    task_id: str = Field(description="任务ID")
    message: str = Field(description="响应消息")
    estimated_time: int = Field(description="预计完成时间（秒）")
    status: str = Field(description="任务状态")

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    id: str = Field(description="任务ID")
    prompt: str = Field(description="生成提示")
    parameters: Dict[str, Any] = Field(description="生成参数")
    status: str = Field(description="任务状态")
    progress: int = Field(description="进度百分比")
    result_path: Optional[str] = Field(description="结果文件路径")
    error_message: Optional[str] = Field(description="错误信息")
    created_at: str = Field(description="创建时间")
    updated_at: str = Field(description="更新时间")
    estimated_time: int = Field(description="预计完成时间")

class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskStatusResponse] = Field(description="任务列表")
    total: int = Field(description="总任务数")

# API Endpoints

@router.post("/generate", response_model=GenerationResponse)
async def generate_music(request: GenerationRequest):
    """
    生成音乐
    
    Args:
        request: 音乐生成请求
        
    Returns:
        GenerationResponse: 生成任务信息
    """
    try:
        # 检查模型是否准备就绪
        if not model_manager.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model is not loaded or ready. Please load the model first."
            )
        
        # 验证请求参数
        if not request.prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt cannot be empty"
            )
        
        # 开始生成任务
        task_id = await music_generator.generate_music(
            prompt=request.prompt,
            parameters=request.parameters or {}
        )
        
        # 获取任务状态
        task_status = music_generator.get_task_status(task_id)
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create generation task"
            )
        
        logger.info(f"Started music generation task {task_id}")
        
        return GenerationResponse(
            task_id=task_id,
            message="Music generation started successfully",
            estimated_time=task_status["estimated_time"],
            status=task_status["status"]
        )
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except ModelInferenceError as e:
        logger.error(f"Model inference error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model inference failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in generate_music: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        TaskStatusResponse: 任务状态信息
    """
    try:
        task_status = music_generator.get_task_status(task_id)
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        return TaskStatusResponse(**task_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )

@router.get("/result/{task_id}")
async def get_task_result(task_id: str):
    """
    获取生成结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        FileResponse: 生成的音频文件
    """
    try:
        task_status = music_generator.get_task_status(task_id)
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        if task_status["status"] != GenerationStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task is not completed. Current status: {task_status['status']}"
            )
        
        result_path = task_status["result_path"]
        if not result_path or not os.path.exists(result_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Result file not found"
            )
        
        # 返回音频文件
        return FileResponse(
            path=result_path,
            media_type="audio/wav",
            filename=f"generated_music_{task_id}.wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task result: {str(e)}"
        )

@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """
    取消生成任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 操作结果
    """
    try:
        success = music_generator.cancel_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found or cannot be cancelled"
            )
        
        logger.info(f"Cancelled task {task_id}")
        return {
            "message": f"Task {task_id} cancelled successfully",
            "task_id": task_id,
            "status": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )

@router.get("/tasks", response_model=TaskListResponse)
async def get_active_tasks():
    """
    获取活动任务列表
    
    Returns:
        TaskListResponse: 活动任务列表
    """
    try:
        active_tasks = music_generator.get_active_tasks()
        return TaskListResponse(
            tasks=[TaskStatusResponse(**task) for task in active_tasks],
            total=len(active_tasks)
        )
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active tasks: {str(e)}"
        )

@router.get("/history", response_model=TaskListResponse)
async def get_task_history(
    limit: int = Query(default=50, ge=1, le=100, description="返回的历史记录数量")
):
    """
    获取任务历史记录
    
    Args:
        limit: 返回的记录数量限制
        
    Returns:
        TaskListResponse: 历史任务列表
    """
    try:
        history = music_generator.get_task_history(limit)
        return TaskListResponse(
            tasks=[TaskStatusResponse(**task) for task in history],
            total=len(history)
        )
        
    except Exception as e:
        logger.error(f"Error getting task history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task history: {str(e)}"
        )

@router.delete("/history")
async def clear_task_history():
    """
    清理任务历史记录
    
    Returns:
        Dict: 操作结果
    """
    try:
        music_generator.clear_history()
        logger.info("Task history cleared")
        return {
            "message": "Task history cleared successfully",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error clearing task history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear task history: {str(e)}"
        )

@router.get("/validate")
async def validate_generation_request(
    prompt: str = Query(description="要验证的提示文本"),
    parameters: Optional[str] = Query(default=None, description="JSON格式的参数")
):
    """
    验证生成请求参数
    
    Args:
        prompt: 提示文本
        parameters: 生成参数（JSON字符串）
        
    Returns:
        Dict: 验证结果
    """
    try:
        # 验证提示文本
        prompt_validation = music_generator.prompt_processor.validate_prompt(prompt)
        
        # 验证参数
        param_dict = {}
        if parameters:
            import json
            try:
                param_dict = json.loads(parameters)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format in parameters"
                )
        
        param_validation = music_generator.parameter_validator.validate_parameters(param_dict)
        
        return {
            "prompt_validation": prompt_validation,
            "parameter_validation": param_validation,
            "overall_valid": prompt_validation["valid"] and param_validation["valid"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate request: {str(e)}"
        )

@router.get("/stats")
async def get_generation_stats():
    """
    获取生成统计信息
    
    Returns:
        Dict: 生成统计信息
    """
    try:
        active_tasks = music_generator.get_active_tasks()
        history = music_generator.get_task_history()
        
        # 统计各种状态的任务数量
        status_counts = {}
        for task in history:
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 计算成功率
        total_completed = sum(1 for task in history if task["status"] in ["completed", "failed"])
        success_rate = 0
        if total_completed > 0:
            success_rate = sum(1 for task in history if task["status"] == "completed") / total_completed
        
        return {
            "active_tasks": len(active_tasks),
            "total_history": len(history),
            "status_counts": status_counts,
            "success_rate": round(success_rate * 100, 2),
            "model_ready": model_manager.is_ready(),
            "model_status": model_manager.get_model_status()
        }
        
    except Exception as e:
        logger.error(f"Error getting generation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get generation stats: {str(e)}"
        )