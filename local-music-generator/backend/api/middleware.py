"""
Middleware for the API.

This module provides middleware components for the FastAPI application,
including request logging, resource monitoring, and error handling.

中间件（Middleware）是在请求处理过程中介入的组件，可以在请求到达路由处理函数之前
或响应返回客户端之前执行特定操作。本模块实现了以下中间件：

1. RequestLoggingMiddleware: 请求日志中间件，记录请求和响应的详细信息
2. ResourceMonitoringMiddleware: 资源监控中间件，监控系统资源使用情况
3. RequestValidationMiddleware: 请求验证中间件，验证请求数据的有效性
4. ErrorHandlingMiddleware: 错误处理中间件，捕获并处理未处理的异常

技术说明：
- BaseHTTPMiddleware: Starlette 提供的基础中间件类，用于创建自定义中间件
- ASGI: 异步服务器网关接口，是 Python 异步 Web 服务器的标准接口
- psutil: Python 系统工具库，用于获取系统资源使用情况
"""
import time
import json
import traceback
from typing import Callable, Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request information and timing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, log timing and response status.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next handler
        """
        start_time = time.time()
        
        # Get client IP, handling proxy forwarding
        client_host = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        client_ip = forwarded_for.split(",")[0] if forwarded_for else client_host
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} from {client_ip}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {process_time:.4f}s"
            )
            
            return response
        except Exception as e:
            # Log exception
            logger.error(
                f"Error processing {request.method} {request.url.path}: {str(e)}"
            )
            raise


class ResourceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring system resource usage during requests.
    Tracks CPU, memory, and disk usage during request processing.
    """
    
    def __init__(self, app: ASGIApp, threshold: float = 90.0):
        """
        Initialize the middleware with resource threshold.
        
        Args:
            app: The ASGI application
            threshold: Resource usage threshold percentage (default: 90%)
        """
        super().__init__(app)
        self.threshold = threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Monitor resource usage during request processing.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next handler
        """
        # Skip resource monitoring for static files and docs
        path = request.url.path
        if path.startswith("/static") or path.startswith("/audio") or path == "/docs" or path == "/redoc":
            return await call_next(request)
        
        # Get resource usage before processing
        cpu_before = psutil.cpu_percent(interval=0.1)
        memory_before = psutil.virtual_memory().percent
        
        # Process the request
        response = await call_next(request)
        
        # Get resource usage after processing
        cpu_after = psutil.cpu_percent(interval=0.1)
        memory_after = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        
        # Check if any resource is above threshold
        if cpu_after > self.threshold or memory_after > self.threshold or disk_usage > self.threshold:
            logger.warning(
                f"High resource usage detected - CPU: {cpu_after}%, "
                f"Memory: {memory_after}%, Disk: {disk_usage}%"
            )
            
            # Add resource usage headers
            response.headers["X-CPU-Usage"] = f"{cpu_after:.1f}%"
            response.headers["X-Memory-Usage"] = f"{memory_after:.1f}%"
            response.headers["X-Disk-Usage"] = f"{disk_usage:.1f}%"
            
            # If this is a JSON response, we could also include resource warning in the response
            if response.headers.get("content-type") == "application/json":
                try:
                    # This is a bit hacky but works for JSONResponse
                    # In a production system, you might want to use a more robust approach
                    if hasattr(response, "body"):
                        body = json.loads(response.body.decode())
                        if isinstance(body, dict):
                            body["resource_warning"] = {
                                "cpu": cpu_after,
                                "memory": memory_after,
                                "disk": disk_usage,
                                "threshold": self.threshold
                            }
                            response.body = json.dumps(body).encode()
                            response.headers["content-length"] = str(len(response.body))
                except Exception as e:
                    logger.error(f"Failed to modify response body: {str(e)}")
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating and sanitizing incoming requests.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Validate and sanitize incoming requests.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next handler
        """
        # Skip validation for static files and docs
        path = request.url.path
        if path.startswith("/static") or path.startswith("/audio") or path == "/docs" or path == "/redoc":
            return await call_next(request)
        
        # Check content type for POST, PUT, PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    # Try to parse the body as JSON to validate it early
                    # This is done by FastAPI automatically, but we can catch syntax errors here
                    body = await request.body()
                    if body:
                        json.loads(body)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in request body: {request.method} {request.url.path}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "code": "INVALID_JSON",
                                "message": "Invalid JSON in request body",
                                "details": "The request body contains invalid JSON syntax",
                                "suggestion": "Check your request body and ensure it is valid JSON",
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            }
                        }
                    )
        
        # Process the request
        response = await call_next(request)
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for catching and handling unhandled exceptions.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Catch and handle unhandled exceptions.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next handler
        """
        try:
            return await call_next(request)
        except Exception as exc:
            # Log the exception with traceback
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}",
                exc_info=True
            )
            
            # Create a standardized error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": str(exc),
                        "suggestion": "Please try again later or contact support if the problem persists",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                }
            )


def setup_middleware(app: FastAPI) -> None:
    """
    Configure middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add error handling middleware (should be first to catch all exceptions)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add request validation middleware
    app.add_middleware(RequestValidationMiddleware)
    
    # Add resource monitoring middleware
    app.add_middleware(ResourceMonitoringMiddleware, threshold=85.0)
    
    # Add request logging middleware (last to ensure all requests are logged)
    app.add_middleware(RequestLoggingMiddleware)