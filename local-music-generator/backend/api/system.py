"""
System-related API endpoints.

这个模块提供了与系统相关的API端点，包括：
1. 系统资源监控（CPU、内存、GPU、磁盘）
2. 系统信息查询
3. 进程管理和监控
4. 资源警告和阈值管理
5. 系统健康检查
"""
import os
import platform
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks, Path
from pydantic import BaseModel, Field
import logging

from api.errors import (
    ModelLoadError,
    ModelInferenceError,
    ResourceLimitExceededError,
    AudioProcessingError
)
from models.resource_monitor import resource_monitor

# Configure logging
logger = logging.getLogger("api.system")

router = APIRouter()

# Models
class SystemResources(BaseModel):
    """System resources information."""
    model_config = {"protected_namespaces": ()}
    
    cpu: Dict[str, Any] = Field(description="CPU信息和使用率")
    memory: Dict[str, Any] = Field(description="内存信息和使用率")
    disk: Dict[str, Any] = Field(description="磁盘信息和使用率")
    gpu: Optional[Dict[str, Any]] = Field(default=None, description="GPU信息（如果可用）")
    platform: Dict[str, Any] = Field(description="平台信息")

class SystemSettings(BaseModel):
    """System settings."""
    model: Dict[str, Any]
    audio: Dict[str, Any]
    ui: Dict[str, Any]
    system: Dict[str, Any]

class ResourceWarning(BaseModel):
    """资源警告信息"""
    resource: str = Field(description="资源类型")
    usage: float = Field(description="当前使用率")
    threshold: float = Field(description="警告阈值")
    message: str = Field(description="警告消息")
    severity: str = Field(description="严重程度：warning, critical")

class ResourceThresholdUpdate(BaseModel):
    """资源阈值更新请求"""
    cpu_warning: Optional[float] = Field(default=None, ge=0, le=100, description="CPU警告阈值")
    cpu_critical: Optional[float] = Field(default=None, ge=0, le=100, description="CPU临界阈值")
    memory_warning: Optional[float] = Field(default=None, ge=0, le=100, description="内存警告阈值")
    memory_critical: Optional[float] = Field(default=None, ge=0, le=100, description="内存临界阈值")
    disk_warning: Optional[float] = Field(default=None, ge=0, le=100, description="磁盘警告阈值")
    disk_critical: Optional[float] = Field(default=None, ge=0, le=100, description="磁盘临界阈值")

class SystemHealthResponse(BaseModel):
    """系统健康检查响应"""
    overall_status: str = Field(description="整体健康状态")
    health_score: float = Field(description="健康评分 (0-100)")
    resources: Dict[str, Any] = Field(description="资源状态")
    warnings: List[ResourceWarning] = Field(description="当前警告")
    recommendations: List[str] = Field(description="建议措施")
    timestamp: str = Field(description="检查时间")

# Helper functions
def get_system_resources() -> Dict[str, Any]:
    """
    Get current system resource usage.
    
    Returns:
        Dict[str, Any]: System resource information
    """
    try:
        # CPU information
        cpu_info = {
            "usage": psutil.cpu_percent(interval=0.1),
            "cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        memory_info = {
            "total": memory.total // (1024 * 1024),  # MB
            "used": memory.used // (1024 * 1024),    # MB
            "free": memory.available // (1024 * 1024),  # MB
            "percent": memory.percent,
            "swap_total": swap.total // (1024 * 1024),
            "swap_used": swap.used // (1024 * 1024),
            "swap_percent": swap.percent
        }
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total // (1024 * 1024),  # MB
            "used": disk.used // (1024 * 1024),    # MB
            "free": disk.free // (1024 * 1024),    # MB
            "percent": disk.percent
        }
        
        # GPU information using torch if available
        gpu_info = None
        try:
            import torch
            if torch.cuda.is_available():
                gpu_props = torch.cuda.get_device_properties(0)
                gpu_info = {
                    "name": gpu_props.name,
                    "total_memory": gpu_props.total_memory // (1024 * 1024),  # MB
                    "allocated_memory": torch.cuda.memory_allocated() // (1024 * 1024),
                    "reserved_memory": torch.cuda.memory_reserved() // (1024 * 1024),
                    "device_count": torch.cuda.device_count(),
                    "current_device": torch.cuda.current_device()
                }
            else:
                gpu_info = {"available": False, "message": "CUDA not available"}
        except ImportError:
            gpu_info = {"available": False, "message": "PyTorch not installed"}
        except Exception as e:
            gpu_info = {"available": False, "error": str(e)}
        
        return {
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "gpu": gpu_info,
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "processor": platform.processor(),
                "architecture": platform.machine(),
                "hostname": platform.node()
            }
        }
    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system resources: {str(e)}"
        )

# Endpoints
@router.get("/resources", response_model=SystemResources)
async def get_resources():
    """
    Get current system resource usage.
    
    Returns:
        SystemResources: Current system resource information
    """
    try:
        resources = get_system_resources()
        return SystemResources(**resources)
    except Exception as e:
        logger.error(f"Error in get_resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system resources: {str(e)}"
        )

@router.get("/resources/history")
async def get_resource_history(
    minutes: int = Query(default=10, ge=1, le=1440, description="获取最近多少分钟的历史")
):
    """
    Get resource usage history from the resource monitor.
    
    Args:
        minutes: Number of minutes of history to retrieve
        
    Returns:
        Dict: Resource usage history
    """
    try:
        history = resource_monitor.get_resource_history(minutes=minutes)
        return {
            "history": history,
            "period_minutes": minutes,
            "total_records": len(history),
            "monitoring_active": resource_monitor.is_monitoring
        }
    except Exception as e:
        logger.error(f"Error getting resource history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource history: {str(e)}"
        )

@router.get("/resources/summary")
async def get_resource_summary():
    """
    Get comprehensive resource usage summary.
    
    Returns:
        Dict: Resource summary with health status and warnings
    """
    try:
        summary = resource_monitor.get_resource_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting resource summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource summary: {str(e)}"
        )

@router.get("/health", response_model=SystemHealthResponse)
async def system_health_check():
    """
    Perform comprehensive system health check.
    
    Returns:
        SystemHealthResponse: Detailed health status
    """
    try:
        # Get current resources
        resources = get_system_resources()
        
        # Get resource summary from monitor
        summary = resource_monitor.get_resource_summary()
        
        # Determine overall health status
        health_score = summary["health"]["score"]
        if health_score >= 90:
            overall_status = "excellent"
        elif health_score >= 75:
            overall_status = "good"
        elif health_score >= 50:
            overall_status = "fair"
        else:
            overall_status = "poor"
        
        # Generate warnings
        warnings = []
        current_status = summary["current_status"]
        
        # Check CPU
        if current_status["cpu_percent"] > resource_monitor.thresholds.cpu_critical:
            warnings.append(ResourceWarning(
                resource="CPU",
                usage=current_status["cpu_percent"],
                threshold=resource_monitor.thresholds.cpu_critical,
                message=f"CPU usage critically high: {current_status['cpu_percent']:.1f}%",
                severity="critical"
            ))
        elif current_status["cpu_percent"] > resource_monitor.thresholds.cpu_warning:
            warnings.append(ResourceWarning(
                resource="CPU",
                usage=current_status["cpu_percent"],
                threshold=resource_monitor.thresholds.cpu_warning,
                message=f"CPU usage high: {current_status['cpu_percent']:.1f}%",
                severity="warning"
            ))
        
        # Check Memory
        if current_status["memory_percent"] > resource_monitor.thresholds.memory_critical:
            warnings.append(ResourceWarning(
                resource="Memory",
                usage=current_status["memory_percent"],
                threshold=resource_monitor.thresholds.memory_critical,
                message=f"Memory usage critically high: {current_status['memory_percent']:.1f}%",
                severity="critical"
            ))
        elif current_status["memory_percent"] > resource_monitor.thresholds.memory_warning:
            warnings.append(ResourceWarning(
                resource="Memory",
                usage=current_status["memory_percent"],
                threshold=resource_monitor.thresholds.memory_warning,
                message=f"Memory usage high: {current_status['memory_percent']:.1f}%",
                severity="warning"
            ))
        
        # Check Disk
        if current_status["disk_percent"] > resource_monitor.thresholds.disk_critical:
            warnings.append(ResourceWarning(
                resource="Disk",
                usage=current_status["disk_percent"],
                threshold=resource_monitor.thresholds.disk_critical,
                message=f"Disk usage critically high: {current_status['disk_percent']:.1f}%",
                severity="critical"
            ))
        elif current_status["disk_percent"] > resource_monitor.thresholds.disk_warning:
            warnings.append(ResourceWarning(
                resource="Disk",
                usage=current_status["disk_percent"],
                threshold=resource_monitor.thresholds.disk_warning,
                message=f"Disk usage high: {current_status['disk_percent']:.1f}%",
                severity="warning"
            ))
        
        # Generate recommendations
        recommendations = []
        if any(w.severity == "critical" for w in warnings):
            recommendations.append("Immediate action required: Critical resource usage detected")
        if current_status["memory_percent"] > 80:
            recommendations.append("Consider closing unnecessary applications to free memory")
        if current_status["disk_percent"] > 85:
            recommendations.append("Clean up disk space by removing temporary files")
        if current_status["cpu_percent"] > 80:
            recommendations.append("High CPU usage detected, consider optimizing running processes")
        
        if not recommendations:
            recommendations.append("System is running optimally")
        
        return SystemHealthResponse(
            overall_status=overall_status,
            health_score=health_score,
            resources=current_status,
            warnings=warnings,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in system health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System health check failed: {str(e)}"
        )

@router.get("/info")
async def get_system_info():
    """
    Get general system information.
    
    Returns:
        Dict[str, Any]: System information
    """
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "boot_time": boot_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0],
            "pid": os.getpid(),
            "working_directory": os.getcwd()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system information: {str(e)}"
        )

@router.get("/processes")
async def get_processes(
    limit: int = Query(default=10, ge=1, le=100, description="返回的进程数量"),
    sort_by: str = Query(default="memory", description="排序字段：memory, cpu, name")
):
    """
    Get information about running processes.
    
    Args:
        limit: Number of processes to return
        sort_by: Field to sort by (memory, cpu, name)
        
    Returns:
        Dict[str, Any]: Process information
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent', 'status', 'create_time']):
            try:
                proc_info = proc.info
                processes.append({
                    "pid": proc_info['pid'],
                    "name": proc_info['name'],
                    "username": proc_info['username'],
                    "memory_percent": proc_info['memory_percent'],
                    "cpu_percent": proc_info['cpu_percent'],
                    "status": proc_info['status'],
                    "create_time": datetime.fromtimestamp(proc_info['create_time']).isoformat()
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort processes
        if sort_by == "memory":
            processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        elif sort_by == "cpu":
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        elif sort_by == "name":
            processes.sort(key=lambda x: x['name'])
        
        return {
            "total": len(processes),
            "processes": processes[:limit],
            "sort_by": sort_by,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get process information: {str(e)}"
        )

@router.get("/monitor/status")
async def get_monitor_status():
    """
    Get resource monitor status.
    
    Returns:
        Dict: Monitor status and configuration
    """
    try:
        return {
            "monitoring_active": resource_monitor.is_monitoring,
            "monitor_interval": resource_monitor.monitor_interval,
            "history_size": resource_monitor.history_size,
            "current_history_count": len(resource_monitor.resource_history),
            "thresholds": {
                "cpu_warning": resource_monitor.thresholds.cpu_warning,
                "cpu_critical": resource_monitor.thresholds.cpu_critical,
                "memory_warning": resource_monitor.thresholds.memory_warning,
                "memory_critical": resource_monitor.thresholds.memory_critical,
                "disk_warning": resource_monitor.thresholds.disk_warning,
                "disk_critical": resource_monitor.thresholds.disk_critical
            },
            "performance_metrics": resource_monitor.get_performance_metrics()
        }
    except Exception as e:
        logger.error(f"Error getting monitor status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitor status: {str(e)}"
        )

@router.post("/monitor/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """
    Start resource monitoring.
    
    Returns:
        Dict: Operation result
    """
    try:
        if resource_monitor.is_monitoring:
            return {"message": "Monitoring is already active", "status": "already_running"}
        
        await resource_monitor.start_monitoring()
        return {"message": "Resource monitoring started", "status": "started"}
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )

@router.post("/monitor/stop")
async def stop_monitoring():
    """
    Stop resource monitoring.
    
    Returns:
        Dict: Operation result
    """
    try:
        if not resource_monitor.is_monitoring:
            return {"message": "Monitoring is not active", "status": "not_running"}
        
        await resource_monitor.stop_monitoring()
        return {"message": "Resource monitoring stopped", "status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}"
        )

@router.put("/monitor/thresholds")
async def update_thresholds(thresholds: ResourceThresholdUpdate):
    """
    Update resource monitoring thresholds.
    
    Args:
        thresholds: New threshold values
        
    Returns:
        Dict: Updated thresholds
    """
    try:
        # Update only provided thresholds
        threshold_dict = thresholds.model_dump(exclude_none=True)
        resource_monitor.set_thresholds(**threshold_dict)
        
        return {
            "message": "Thresholds updated successfully",
            "updated_thresholds": threshold_dict,
            "current_thresholds": {
                "cpu_warning": resource_monitor.thresholds.cpu_warning,
                "cpu_critical": resource_monitor.thresholds.cpu_critical,
                "memory_warning": resource_monitor.thresholds.memory_warning,
                "memory_critical": resource_monitor.thresholds.memory_critical,
                "disk_warning": resource_monitor.thresholds.disk_warning,
                "disk_critical": resource_monitor.thresholds.disk_critical
            }
        }
    except Exception as e:
        logger.error(f"Error updating thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update thresholds: {str(e)}"
        )

@router.delete("/monitor/history")
async def clear_monitor_history():
    """
    Clear resource monitoring history.
    
    Returns:
        Dict: Operation result
    """
    try:
        resource_monitor.clear_history()
        return {"message": "Resource monitoring history cleared", "status": "cleared"}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}"
        )

@router.get("/warnings")
async def get_current_warnings():
    """
    Get current resource warnings.
    
    Returns:
        Dict: Current warnings and their details
    """
    try:
        current_status = resource_monitor.get_current_status()
        warnings = []
        
        # Check all thresholds
        if current_status["cpu_percent"] > resource_monitor.thresholds.cpu_warning:
            severity = "critical" if current_status["cpu_percent"] > resource_monitor.thresholds.cpu_critical else "warning"
            warnings.append({
                "resource": "CPU",
                "usage": current_status["cpu_percent"],
                "threshold": resource_monitor.thresholds.cpu_critical if severity == "critical" else resource_monitor.thresholds.cpu_warning,
                "message": f"CPU usage {'critically ' if severity == 'critical' else ''}high: {current_status['cpu_percent']:.1f}%",
                "severity": severity,
                "timestamp": current_status["timestamp"]
            })
        
        if current_status["memory_percent"] > resource_monitor.thresholds.memory_warning:
            severity = "critical" if current_status["memory_percent"] > resource_monitor.thresholds.memory_critical else "warning"
            warnings.append({
                "resource": "Memory",
                "usage": current_status["memory_percent"],
                "threshold": resource_monitor.thresholds.memory_critical if severity == "critical" else resource_monitor.thresholds.memory_warning,
                "message": f"Memory usage {'critically ' if severity == 'critical' else ''}high: {current_status['memory_percent']:.1f}%",
                "severity": severity,
                "timestamp": current_status["timestamp"]
            })
        
        if current_status["disk_percent"] > resource_monitor.thresholds.disk_warning:
            severity = "critical" if current_status["disk_percent"] > resource_monitor.thresholds.disk_critical else "warning"
            warnings.append({
                "resource": "Disk",
                "usage": current_status["disk_percent"],
                "threshold": resource_monitor.thresholds.disk_critical if severity == "critical" else resource_monitor.thresholds.disk_warning,
                "message": f"Disk usage {'critically ' if severity == 'critical' else ''}high: {current_status['disk_percent']:.1f}%",
                "severity": severity,
                "timestamp": current_status["timestamp"]
            })
        
        return {
            "has_warnings": len(warnings) > 0,
            "warning_count": len(warnings),
            "critical_count": sum(1 for w in warnings if w["severity"] == "critical"),
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting warnings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get warnings: {str(e)}"
        )

# Deprecated endpoints (kept for compatibility)
@router.get("/check-warning")
async def check_resource_warning(
    threshold: int = Query(80, description="Resource usage threshold percentage")
):
    """
    Check if system resources are above warning threshold.
    
    Args:
        threshold: Resource usage threshold percentage
        
    Returns:
        Dict: Resource warning status
        
    Note: This endpoint is deprecated, use /warnings instead
    """
    logger.warning("Deprecated endpoint /check-warning called, use /warnings instead")
    
    resources = get_system_resources()
    
    warnings = []
    
    # Check CPU usage
    if resources["cpu"]["usage"] > threshold:
        warnings.append({
            "resource": "CPU",
            "usage": resources["cpu"]["usage"],
            "threshold": threshold,
            "message": f"CPU usage is above {threshold}%"
        })
    
    # Check memory usage
    if resources["memory"]["percent"] > threshold:
        warnings.append({
            "resource": "Memory",
            "usage": resources["memory"]["percent"],
            "threshold": threshold,
            "message": f"Memory usage is above {threshold}%"
        })
    
    # Check disk usage
    if resources["disk"]["percent"] > threshold:
        warnings.append({
            "resource": "Disk",
            "usage": resources["disk"]["percent"],
            "threshold": threshold,
            "message": f"Disk usage is above {threshold}%"
        })
    
    # If any resource is critically high, raise an error
    if any(w["usage"] > 95 for w in warnings):
        raise ResourceLimitExceededError("Critical resource usage detected")
    
    return {
        "has_warnings": len(warnings) > 0,
        "warnings": warnings,
        "threshold": threshold
    }

# Test error handling endpoints
@router.get("/test-error/{error_type}")
async def test_error(
    error_type: str,
    message: str = Query("Test error message", description="Custom error message")
):
    """
    Test endpoint to trigger different types of errors.
    
    Args:
        error_type: Type of error to trigger (http, validation, model_load, model_inference, resource, audio, general)
        message: Custom error message
        
    Returns:
        Dict: Response if no error is triggered
    """
    if error_type == "http":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    elif error_type == "model_load":
        raise ModelLoadError(message)
    elif error_type == "model_inference":
        raise ModelInferenceError(message)
    elif error_type == "resource":
        raise ResourceLimitExceededError(message)
    elif error_type == "audio":
        raise AudioProcessingError(message)
    elif error_type == "general":
        raise Exception(message)
    else:
        return {
            "message": "No error triggered",
            "error_type": error_type,
            "custom_message": message
        }

@router.get("/resources/trends", response_model=Dict[str, Any])
async def get_resource_trends(minutes: int = Query(30, ge=5, le=1440, description="分析时间窗口（分钟）")):
    """获取资源使用趋势分析"""
    try:
        trends = resource_monitor.get_all_trends(minutes)
        return trends
    except Exception as e:
        logger.error(f"Error getting resource trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resources/trend/{resource_type}", response_model=Dict[str, Any])
async def get_resource_trend(
    resource_type: str = Path(..., description="资源类型 (cpu, memory, disk, gpu)"),
    minutes: int = Query(30, ge=5, le=1440, description="分析时间窗口（分钟）")
):
    """获取特定资源的使用趋势"""
    try:
        if resource_type not in ['cpu', 'memory', 'disk', 'gpu']:
            raise HTTPException(status_code=400, detail="Invalid resource type")
        
        trend = resource_monitor.get_resource_trend(resource_type, minutes)
        return trend
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"Error getting {resource_type} trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resources/alerts", response_model=Dict[str, Any])
async def get_resource_alerts():
    """获取当前资源警告"""
    try:
        alerts = resource_monitor.get_resource_alerts()
        return {
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting resource alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))