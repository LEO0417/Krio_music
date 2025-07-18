"""
Error handling utilities for the API.

This module provides comprehensive error handling for the FastAPI application,
including custom exception classes, error response formatting, and exception handlers.

错误处理是 API 设计中的关键部分，本模块实现了以下功能：
1. 定义标准化的错误响应格式，确保客户端收到一致的错误信息
2. 提供自定义异常类，用于表示不同类型的应用程序错误
3. 实现异常处理器，捕获并处理各种类型的异常
4. 记录错误日志，便于调试和监控

技术说明：
- Exception Handler: 异常处理器，用于捕获并处理特定类型的异常
- HTTP Status Code: HTTP 状态码，表示请求的结果状态（如 200 成功，404 未找到，500 服务器错误等）
- JSONResponse: JSON 格式的 HTTP 响应，用于向客户端返回结构化数据
"""
from typing import Any, Dict, Optional, List, Union
import sys
import traceback
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import logging

# Configure logging
logger = logging.getLogger("errors")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Error codes
class ErrorCode:
    """Error code constants."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    MODEL_LOAD_ERROR = "MODEL_LOAD_ERROR"
    MODEL_INFERENCE_ERROR = "MODEL_INFERENCE_ERROR"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    AUDIO_PROCESSING_ERROR = "AUDIO_PROCESSING_ERROR"
    PARAMETER_VALIDATION_ERROR = "PARAMETER_VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"


def create_error_response(
    code: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[str] = None,
    suggestion: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        code: Error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        suggestion: Suggested action to resolve the error
        
    Returns:
        Dict containing error information
    """
    error_response = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "suggestion": suggestion,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    }
    return error_response


class ModelLoadError(Exception):
    """Exception raised when model loading fails."""
    pass


class ModelInferenceError(Exception):
    """Exception raised when model inference fails."""
    pass


class ResourceLimitExceededError(Exception):
    """Exception raised when system resource limits are exceeded."""
    pass


class AudioProcessingError(Exception):
    """Exception raised when audio processing fails."""
    pass


class ValidationError(Exception):
    """Exception raised when parameter validation fails."""
    pass


def setup_error_handlers(app: FastAPI) -> None:
    """
    Configure error handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            error_response = create_error_response(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="The requested resource was not found",
                status_code=exc.status_code,
                details=str(exc.detail),
                suggestion="Check the URL and try again"
            )
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error_response = create_error_response(
                code=ErrorCode.UNAUTHORIZED,
                message="Authentication required",
                status_code=exc.status_code,
                details=str(exc.detail),
                suggestion="Provide valid authentication credentials"
            )
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            error_response = create_error_response(
                code=ErrorCode.FORBIDDEN,
                message="Access forbidden",
                status_code=exc.status_code,
                details=str(exc.detail),
                suggestion="You don't have permission to access this resource"
            )
        else:
            error_response = create_error_response(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message="An error occurred processing your request",
                status_code=exc.status_code,
                details=str(exc.detail),
                suggestion="Please try again later"
            )
        
        # Log the error
        logger.error(
            f"HTTP {exc.status_code} error: {exc.detail} - "
            f"URL: {request.method} {request.url}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors."""
        error_details = []
        for error in exc.errors():
            error_details.append({
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", "")
            })
            
        error_response = create_error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=error_details,
            suggestion="Check your request parameters and try again"
        )
        
        # Log the error
        logger.warning(
            f"Validation error: {error_details} - "
            f"URL: {request.method} {request.url}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response
        )
    
    @app.exception_handler(ModelLoadError)
    async def model_load_error_handler(request: Request, exc: ModelLoadError) -> JSONResponse:
        """Handle model loading errors."""
        error_response = create_error_response(
            code=ErrorCode.MODEL_LOAD_ERROR,
            message="Failed to load the model",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=str(exc),
            suggestion="Check system resources and model configuration"
        )
        
        # Log the error
        logger.error(f"Model load error: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )
    
    @app.exception_handler(ModelInferenceError)
    async def model_inference_error_handler(request: Request, exc: ModelInferenceError) -> JSONResponse:
        """Handle model inference errors."""
        error_response = create_error_response(
            code=ErrorCode.MODEL_INFERENCE_ERROR,
            message="Error during model inference",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=str(exc),
            suggestion="Try with different parameters or check system resources"
        )
        
        # Log the error
        logger.error(f"Model inference error: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )
    
    @app.exception_handler(ResourceLimitExceededError)
    async def resource_limit_error_handler(request: Request, exc: ResourceLimitExceededError) -> JSONResponse:
        """Handle resource limit errors."""
        error_response = create_error_response(
            code=ErrorCode.RESOURCE_LIMIT_EXCEEDED,
            message="System resource limits exceeded",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=str(exc),
            suggestion="Try again later or with smaller parameters"
        )
        
        # Log the error
        logger.error(f"Resource limit exceeded: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response
        )
    
    @app.exception_handler(AudioProcessingError)
    async def audio_processing_error_handler(request: Request, exc: AudioProcessingError) -> JSONResponse:
        """Handle audio processing errors."""
        error_response = create_error_response(
            code=ErrorCode.AUDIO_PROCESSING_ERROR,
            message="Error processing audio data",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=str(exc),
            suggestion="Try with different audio parameters"
        )
        
        # Log the error
        logger.error(f"Audio processing error: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle parameter validation errors."""
        error_response = create_error_response(
            code=ErrorCode.PARAMETER_VALIDATION_ERROR,
            message="Parameter validation failed",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=str(exc),
            suggestion="Check your request parameters and try again"
        )
        
        # Log the error
        logger.warning(f"Parameter validation error: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions."""
        error_response = create_error_response(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=str(exc),
            suggestion="Please try again later or contact support if the problem persists"
        )
        
        # Log the error
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )