"""
Main entry point for the Local Music Generator API.

这个模块是应用程序的主入口点，负责：
1. 配置和初始化 FastAPI 应用程序
2. 设置中间件（middleware）和错误处理
3. 注册 API 路由（routes）
4. 配置静态文件服务
5. 定义应用程序启动和关闭事件
6. 启动 Web 服务器

技术说明：
- FastAPI: 一个现代、高性能的 Python Web 框架，用于构建 API
- CORS: 跨源资源共享，一种安全机制，允许不同源的网页请求访问该 API
- Middleware: 中间件，处理请求和响应的组件，在路由处理之前和之后执行
- OpenAPI: API 文档标准，用于描述 RESTful API
"""
import logging
import uvicorn
import time
import platform
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from pathlib import Path

from config.settings import (
    API_V1_PREFIX, 
    CORS_ORIGINS, 
    DEBUG, 
    AUDIO_DIR,
    DATA_DIR,
    get_settings
)
from api.errors import setup_error_handlers
from api.middleware import setup_middleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")

# Create FastAPI app
app = FastAPI(
    title="Local Music Generator API",
    description="API for generating music using Facebook's MusicGen model locally",
    version="0.1.0",
    debug=DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup error handlers
setup_error_handlers(app)

# Add CORS middleware with more specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "Accept", 
        "Origin", 
        "X-Requested-With",
        "X-API-Key"
    ],
    expose_headers=[
        "X-Process-Time", 
        "X-CPU-Usage", 
        "X-Memory-Usage", 
        "X-Disk-Usage"
    ],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Setup custom middleware
setup_middleware(app)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Local Music Generator API is running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

# Settings endpoint
@app.get("/settings")
async def settings():
    """
    Get application settings.
    """
    return get_settings()

# Include API routers
from api.base import router as base_router
from api.system import router as system_router
from api.models import router as models_router

# Register routers
app.include_router(base_router, prefix=API_V1_PREFIX)
app.include_router(system_router, prefix=f"{API_V1_PREFIX}/system", tags=["System"])
app.include_router(models_router, prefix=f"{API_V1_PREFIX}/models", tags=["Models"])

# Mount static files for audio output
audio_path = Path(AUDIO_DIR)
if audio_path.exists():
    app.mount("/audio", StaticFiles(directory=str(audio_path)), name="audio")
    logger.info(f"Mounted audio directory at {audio_path}")
else:
    logger.warning(f"Audio directory {audio_path} does not exist")

# Customize OpenAPI documentation
def custom_openapi():
    """
    Customize OpenAPI documentation.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Local Music Generator API",
        version="0.1.0",
        description="API for generating music using Facebook's MusicGen model locally",
        routes=app.routes,
    )
    
    # Add custom documentation
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # Add security schemes if needed
    # openapi_schema["components"]["securitySchemes"] = {
    #     "ApiKeyAuth": {
    #         "type": "apiKey",
    #         "in": "header",
    #         "name": "X-API-Key"
    #     }
    # }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Import model manager and resource monitor
from models.model_manager import model_manager
from models.resource_monitor import resource_monitor

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    """
    logger.info("Starting Local Music Generator API")
    
    # Create necessary directories
    for directory in [AUDIO_DIR, DATA_DIR]:
        if not Path(directory).exists():
            logger.info(f"Creating directory: {directory}")
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Log system information
    logger.info(f"Running on platform: {platform.system()} {platform.release()}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Debug mode: {'enabled' if DEBUG else 'disabled'}")
    
    # Start resource monitoring
    try:
        await resource_monitor.start_monitoring()
        logger.info("Resource monitoring started")
    except Exception as e:
        logger.error(f"Failed to start resource monitoring: {e}")
    
    # Auto-load model if configured
    try:
        if model_manager.auto_load:
            logger.info("Auto-loading model on startup")
            await model_manager.load_model()
    except Exception as e:
        logger.warning(f"Failed to auto-load model: {e}")
    
    logger.info("Application startup completed")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    """
    logger.info("Shutting down Local Music Generator API")
    
    # Stop resource monitoring
    try:
        await resource_monitor.stop_monitoring()
        logger.info("Resource monitoring stopped")
    except Exception as e:
        logger.error(f"Error stopping resource monitoring: {e}")
    
    # Unload model and cleanup resources
    try:
        await model_manager.unload_model()
        logger.info("Model unloaded")
    except Exception as e:
        logger.error(f"Error unloading model: {e}")
    
    logger.info("Application shutdown completed")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)