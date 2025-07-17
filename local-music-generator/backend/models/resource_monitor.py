"""
资源监控器 (Resource Monitor)

这个模块提供了全面的系统资源监控功能，包括：
1. 实时监控CPU、内存、GPU使用情况
2. 模型推理性能跟踪
3. 资源使用警告和限制机制
4. 性能数据收集和分析

技术说明：
- 使用 psutil 监控系统资源
- 支持GPU监控（通过 torch）
- 异步监控以避免性能影响
- 提供资源使用历史和预测
"""
import os
import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque
import logging

import psutil
import torch

# Configure logging
logger = logging.getLogger("resource_monitor")

# Import notification system
from .notification_system import NotificationSystem, NotificationLevel, NotificationType

@dataclass
class ResourceSnapshot:
    """资源使用快照"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: int
    memory_total_mb: int
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    gpu_memory_used_mb: Optional[int] = None
    gpu_memory_total_mb: Optional[int] = None
    gpu_utilization: Optional[float] = None
    model_memory_mb: int = 0
    inference_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    avg_inference_time: float = 0.0
    total_inferences: int = 0
    successful_inferences: int = 0
    failed_inferences: int = 0
    peak_memory_usage_mb: int = 0
    avg_cpu_usage: float = 0.0
    avg_memory_usage: float = 0.0
    uptime_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

class ResourceThresholds:
    """资源阈值配置"""
    def __init__(self):
        self.cpu_warning = 80.0      # CPU使用率警告阈值
        self.cpu_critical = 95.0     # CPU使用率临界阈值
        self.memory_warning = 80.0   # 内存使用率警告阈值
        self.memory_critical = 90.0  # 内存使用率临界阈值
        self.disk_warning = 85.0     # 磁盘使用率警告阈值
        self.disk_critical = 95.0    # 磁盘使用率临界阈值
        self.gpu_memory_warning = 80.0  # GPU内存警告阈值
        self.gpu_memory_critical = 90.0 # GPU内存临界阈值

class ResourceMonitor:
    """
    资源监控器
    
    负责监控系统资源使用情况、模型性能，以及提供资源预警功能。
    """
    
    def __init__(self, history_size: int = 1000, monitor_interval: float = 1.0):
        """
        初始化资源监控器
        
        Args:
            history_size: 保持的历史记录数量
            monitor_interval: 监控间隔（秒）
        """
        self.history_size = history_size
        self.monitor_interval = monitor_interval
        self.thresholds = ResourceThresholds()
        
        # 资源使用历史
        self.resource_history: deque[ResourceSnapshot] = deque(maxlen=history_size)
        
        # 性能指标
        self.performance_metrics = PerformanceMetrics()
        self.start_time = datetime.now()
        
        # 推理计时
        self.inference_times: deque[float] = deque(maxlen=100)
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # 回调函数
        self.warning_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # 缓存上一次的资源信息
        self._last_snapshot: Optional[ResourceSnapshot] = None
        
        # 初始化通知系统
        self.notification_system = NotificationSystem()
        
        # 注册资源警告规则的回调
        self._setup_notification_callbacks()
        
        logger.info(f"Resource Monitor initialized with notification system - History size: {history_size}, Interval: {monitor_interval}s")
    
    def _setup_notification_callbacks(self):
        """设置通知系统的回调"""
        def resource_warning_callback(warning_type: str, details: Dict[str, Any]):
            """资源警告回调处理"""
            # 发送通知
            self.notification_system.send_notification(
                level=NotificationLevel.WARNING,
                notification_type=NotificationType.RESOURCE_WARNING,
                title=f"Resource Warning: {warning_type}",
                message=f"Resource usage exceeded threshold: {details}",
                data=details
            )
        
        self.add_warning_callback(resource_warning_callback)
    
    def add_warning_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        添加警告回调函数
        
        Args:
            callback: 警告回调函数，接收警告类型和详细信息
        """
        self.warning_callbacks.append(callback)
    
    def _trigger_warning(self, warning_type: str, details: Dict[str, Any]):
        """触发警告回调"""
        for callback in self.warning_callbacks:
            try:
                callback(warning_type, details)
            except Exception as e:
                logger.error(f"Error in warning callback: {e}")
    
    def _get_current_snapshot(self) -> ResourceSnapshot:
        """获取当前资源使用快照"""
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used // (1024 * 1024)
            memory_total_mb = memory.total // (1024 * 1024)
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used // (1024 ** 3)
            disk_total_gb = disk.total // (1024 ** 3)
            
            # GPU信息
            gpu_memory_used_mb = None
            gpu_memory_total_mb = None
            gpu_utilization = None
            
            if torch.cuda.is_available():
                try:
                    gpu_memory_used_mb = torch.cuda.memory_allocated() // (1024 * 1024)
                    gpu_props = torch.cuda.get_device_properties(0)
                    gpu_memory_total_mb = gpu_props.total_memory // (1024 * 1024)
                    # GPU利用率需要额外的库来获取，这里设为0
                    gpu_utilization = 0.0
                except Exception as e:
                    logger.debug(f"Error getting GPU info: {e}")
            
            snapshot = ResourceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                gpu_memory_used_mb=gpu_memory_used_mb,
                gpu_memory_total_mb=gpu_memory_total_mb,
                gpu_utilization=gpu_utilization,
                inference_count=self.performance_metrics.total_inferences
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error getting resource snapshot: {e}")
            # 返回默认快照
            return ResourceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0,
                memory_total_mb=0,
                disk_percent=0.0,
                disk_used_gb=0,
                disk_total_gb=0
            )
    
    def _check_thresholds(self, snapshot: ResourceSnapshot):
        """检查资源使用是否超过阈值"""
        warnings = []
        
        # 检查CPU使用率
        if snapshot.cpu_percent >= self.thresholds.cpu_critical:
            warnings.append({
                "type": "cpu_critical",
                "message": f"CPU usage critical: {snapshot.cpu_percent:.1f}%",
                "value": snapshot.cpu_percent,
                "threshold": self.thresholds.cpu_critical
            })
        elif snapshot.cpu_percent >= self.thresholds.cpu_warning:
            warnings.append({
                "type": "cpu_warning",
                "message": f"CPU usage high: {snapshot.cpu_percent:.1f}%",
                "value": snapshot.cpu_percent,
                "threshold": self.thresholds.cpu_warning
            })
        
        # 检查内存使用率
        if snapshot.memory_percent >= self.thresholds.memory_critical:
            warnings.append({
                "type": "memory_critical",
                "message": f"Memory usage critical: {snapshot.memory_percent:.1f}%",
                "value": snapshot.memory_percent,
                "threshold": self.thresholds.memory_critical
            })
        elif snapshot.memory_percent >= self.thresholds.memory_warning:
            warnings.append({
                "type": "memory_warning",
                "message": f"Memory usage high: {snapshot.memory_percent:.1f}%",
                "value": snapshot.memory_percent,
                "threshold": self.thresholds.memory_warning
            })
        
        # 检查磁盘使用率
        if snapshot.disk_percent >= self.thresholds.disk_critical:
            warnings.append({
                "type": "disk_critical",
                "message": f"Disk usage critical: {snapshot.disk_percent:.1f}%",
                "value": snapshot.disk_percent,
                "threshold": self.thresholds.disk_critical
            })
        elif snapshot.disk_percent >= self.thresholds.disk_warning:
            warnings.append({
                "type": "disk_warning",
                "message": f"Disk usage high: {snapshot.disk_percent:.1f}%",
                "value": snapshot.disk_percent,
                "threshold": self.thresholds.disk_warning
            })
        
        # 检查GPU内存使用率
        if (snapshot.gpu_memory_used_mb is not None and 
            snapshot.gpu_memory_total_mb is not None and 
            snapshot.gpu_memory_total_mb > 0):
            
            gpu_memory_percent = (snapshot.gpu_memory_used_mb / snapshot.gpu_memory_total_mb) * 100
            
            if gpu_memory_percent >= self.thresholds.gpu_memory_critical:
                warnings.append({
                    "type": "gpu_memory_critical",
                    "message": f"GPU memory usage critical: {gpu_memory_percent:.1f}%",
                    "value": gpu_memory_percent,
                    "threshold": self.thresholds.gpu_memory_critical
                })
            elif gpu_memory_percent >= self.thresholds.gpu_memory_warning:
                warnings.append({
                    "type": "gpu_memory_warning",
                    "message": f"GPU memory usage high: {gpu_memory_percent:.1f}%",
                    "value": gpu_memory_percent,
                    "threshold": self.thresholds.gpu_memory_warning
                })
        
        # 触发警告回调
        for warning in warnings:
            self._trigger_warning(warning["type"], warning)
    
    async def _monitor_loop(self):
        """监控循环"""
        logger.info("Resource monitoring started")
        
        while self.is_monitoring:
            try:
                # 获取资源快照
                snapshot = self._get_current_snapshot()
                
                # 添加到历史记录
                self.resource_history.append(snapshot)
                self._last_snapshot = snapshot
                
                # 检查阈值
                self._check_thresholds(snapshot)
                
                # 更新性能指标
                self._update_performance_metrics()
                
                # 等待下一次监控
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitor_interval)
        
        logger.info("Resource monitoring stopped")
    
    def _update_performance_metrics(self):
        """更新性能指标"""
        # 计算运行时间
        self.performance_metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # 计算平均推理时间
        if self.inference_times:
            self.performance_metrics.avg_inference_time = sum(self.inference_times) / len(self.inference_times)
        
        # 只有在有资源历史时才计算系统资源平均值
        if not self.resource_history:
            return
        
        # 计算平均值
        recent_snapshots = list(self.resource_history)[-60:]  # 最近60个快照
        
        if recent_snapshots:
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_memory = sum(s.memory_percent for s in recent_snapshots) / len(recent_snapshots)
            peak_memory = max(s.memory_used_mb for s in recent_snapshots)
            
            self.performance_metrics.avg_cpu_usage = avg_cpu
            self.performance_metrics.avg_memory_usage = avg_memory
            self.performance_metrics.peak_memory_usage_mb = max(
                self.performance_metrics.peak_memory_usage_mb, 
                peak_memory
            )
    
    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self.is_monitoring = True
        self.start_time = datetime.now()
        self.monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
    
    def record_inference_start(self) -> float:
        """记录推理开始时间"""
        return time.time()
    
    def record_inference_end(self, start_time: float, success: bool = True):
        """
        记录推理结束
        
        Args:
            start_time: 推理开始时间
            success: 推理是否成功
        """
        inference_time = time.time() - start_time
        self.inference_times.append(inference_time)
        
        self.performance_metrics.total_inferences += 1
        if success:
            self.performance_metrics.successful_inferences += 1
        else:
            self.performance_metrics.failed_inferences += 1
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前资源状态"""
        if self._last_snapshot is None:
            snapshot = self._get_current_snapshot()
            self._last_snapshot = snapshot
        else:
            snapshot = self._last_snapshot
        
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "cpu_percent": snapshot.cpu_percent,
            "memory_percent": snapshot.memory_percent,
            "memory_used_mb": snapshot.memory_used_mb,
            "memory_total_mb": snapshot.memory_total_mb,
            "disk_percent": snapshot.disk_percent,
            "disk_used_gb": snapshot.disk_used_gb,
            "disk_total_gb": snapshot.disk_total_gb,
            "gpu_memory_used_mb": snapshot.gpu_memory_used_mb,
            "gpu_memory_total_mb": snapshot.gpu_memory_total_mb,
            "gpu_utilization": snapshot.gpu_utilization,
            "is_monitoring": self.is_monitoring
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        self._update_performance_metrics()
        return self.performance_metrics.to_dict()
    
    def get_resource_history(self, minutes: int = 10) -> List[Dict[str, Any]]:
        """
        获取资源使用历史
        
        Args:
            minutes: 获取最近多少分钟的历史
            
        Returns:
            List[Dict]: 资源使用历史列表
        """
        if not self.resource_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_history = [
            snapshot.to_dict() 
            for snapshot in self.resource_history 
            if snapshot.timestamp >= cutoff_time
        ]
        
        return recent_history
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """获取资源使用摘要"""
        current_status = self.get_current_status()
        performance_metrics = self.get_performance_metrics()
        
        # 计算资源健康状态
        health_score = 100.0
        warnings = []
        
        if current_status["cpu_percent"] > self.thresholds.cpu_warning:
            health_score -= 20
            warnings.append("High CPU usage")
        
        if current_status["memory_percent"] > self.thresholds.memory_warning:
            health_score -= 25
            warnings.append("High memory usage")
        
        if current_status["disk_percent"] > self.thresholds.disk_warning:
            health_score -= 15
            warnings.append("High disk usage")
        
        health_status = "excellent"
        if health_score < 60:
            health_status = "poor"
        elif health_score < 80:
            health_status = "fair"
        elif health_score < 95:
            health_status = "good"
        
        return {
            "current_status": current_status,
            "performance_metrics": performance_metrics,
            "health": {
                "score": health_score,
                "status": health_status,
                "warnings": warnings
            },
            "thresholds": {
                "cpu_warning": self.thresholds.cpu_warning,
                "memory_warning": self.thresholds.memory_warning,
                "disk_warning": self.thresholds.disk_warning
            }
        }
    
    def set_thresholds(self, **kwargs):
        """
        设置资源阈值
        
        Args:
            **kwargs: 阈值参数
        """
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
                logger.info(f"Updated threshold {key} to {value}")
    
    def clear_history(self):
        """清除历史记录"""
        self.resource_history.clear()
        self.inference_times.clear()
        self.performance_metrics = PerformanceMetrics()
        self.start_time = datetime.now()
        logger.info("Resource history cleared")
    
    def get_resource_trend(self, resource_type: str, minutes: int = 30) -> Dict[str, Any]:
        """
        获取资源使用趋势分析
        
        Args:
            resource_type: 资源类型 ('cpu', 'memory', 'disk', 'gpu')
            minutes: 分析的时间窗口（分钟）
            
        Returns:
            Dict: 趋势分析结果
        """
        if not self.resource_history:
            return {
                "error": "No resource history available",
                "trend": "unknown",
                "change_rate": 0.0,
                "prediction": None
            }
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_data = [
            snapshot for snapshot in self.resource_history 
            if snapshot.timestamp >= cutoff_time
        ]
        
        if len(recent_data) < 2:
            return {
                "error": "Insufficient data for trend analysis",
                "trend": "unknown",
                "change_rate": 0.0,
                "prediction": None
            }
        
        # 提取指定资源的数据
        resource_values = []
        timestamps = []
        
        for snapshot in recent_data:
            timestamps.append(snapshot.timestamp)
            if resource_type == 'cpu':
                resource_values.append(snapshot.cpu_percent)
            elif resource_type == 'memory':
                resource_values.append(snapshot.memory_percent)
            elif resource_type == 'disk':
                resource_values.append(snapshot.disk_percent)
            elif resource_type == 'gpu' and snapshot.gpu_memory_used_mb:
                gpu_percent = (snapshot.gpu_memory_used_mb / snapshot.gpu_memory_total_mb * 100) if snapshot.gpu_memory_total_mb else 0
                resource_values.append(gpu_percent)
            else:
                return {"error": f"Unsupported resource type: {resource_type}"}
        
        if not resource_values:
            return {"error": f"No data available for resource type: {resource_type}"}
        
        # 计算趋势
        start_value = resource_values[0]
        end_value = resource_values[-1]
        change_rate = (end_value - start_value) / len(resource_values)  # 平均变化率
        
        # 确定趋势方向
        if abs(change_rate) < 0.1:
            trend = "stable"
        elif change_rate > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        # 简单的线性预测（未来10分钟）
        prediction_steps = 10 * 60 // self.monitor_interval  # 10分钟的步数
        predicted_value = end_value + (change_rate * prediction_steps)
        predicted_value = max(0, min(100, predicted_value))  # 限制在0-100%之间
        
        # 计算统计信息
        avg_value = sum(resource_values) / len(resource_values)
        max_value = max(resource_values)
        min_value = min(resource_values)
        
        return {
            "resource_type": resource_type,
            "time_window_minutes": minutes,
            "data_points": len(resource_values),
            "trend": trend,
            "change_rate": round(change_rate, 3),
            "current_value": round(end_value, 2),
            "prediction_10min": round(predicted_value, 2),
            "statistics": {
                "average": round(avg_value, 2),
                "maximum": round(max_value, 2),
                "minimum": round(min_value, 2),
                "volatility": round(max_value - min_value, 2)
            }
        }
    
    def get_all_trends(self, minutes: int = 30) -> Dict[str, Any]:
        """
        获取所有资源的趋势分析
        
        Args:
            minutes: 分析的时间窗口（分钟）
            
        Returns:
            Dict: 所有资源的趋势分析
        """
        trends = {}
        resource_types = ['cpu', 'memory', 'disk']
        
        # 检查是否有GPU数据
        if self.resource_history and any(s.gpu_memory_used_mb for s in self.resource_history):
            resource_types.append('gpu')
        
        for resource_type in resource_types:
            trends[resource_type] = self.get_resource_trend(resource_type, minutes)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "analysis_window_minutes": minutes,
            "trends": trends
        }
    
    def get_resource_alerts(self) -> List[Dict[str, Any]]:
        """
        获取当前资源警告列表
        
        Returns:
            List[Dict]: 警告列表
        """
        alerts = []
        current_status = self.get_current_status()
        
        # CPU警告
        if current_status["cpu_percent"] >= self.thresholds.cpu_critical:
            alerts.append({
                "type": "cpu_critical",
                "level": "critical",
                "message": f"CPU usage critical: {current_status['cpu_percent']:.1f}%",
                "threshold": self.thresholds.cpu_critical,
                "current_value": current_status["cpu_percent"]
            })
        elif current_status["cpu_percent"] >= self.thresholds.cpu_warning:
            alerts.append({
                "type": "cpu_warning",
                "level": "warning", 
                "message": f"CPU usage high: {current_status['cpu_percent']:.1f}%",
                "threshold": self.thresholds.cpu_warning,
                "current_value": current_status["cpu_percent"]
            })
        
        # 内存警告
        if current_status["memory_percent"] >= self.thresholds.memory_critical:
            alerts.append({
                "type": "memory_critical",
                "level": "critical",
                "message": f"Memory usage critical: {current_status['memory_percent']:.1f}%",
                "threshold": self.thresholds.memory_critical,
                "current_value": current_status["memory_percent"]
            })
        elif current_status["memory_percent"] >= self.thresholds.memory_warning:
            alerts.append({
                "type": "memory_warning",
                "level": "warning",
                "message": f"Memory usage high: {current_status['memory_percent']:.1f}%", 
                "threshold": self.thresholds.memory_warning,
                "current_value": current_status["memory_percent"]
            })
        
        # 磁盘警告
        if current_status["disk_percent"] >= self.thresholds.disk_critical:
            alerts.append({
                "type": "disk_critical",
                "level": "critical",
                "message": f"Disk usage critical: {current_status['disk_percent']:.1f}%",
                "threshold": self.thresholds.disk_critical,
                "current_value": current_status["disk_percent"]
            })
        elif current_status["disk_percent"] >= self.thresholds.disk_warning:
            alerts.append({
                "type": "disk_warning",
                "level": "warning",
                "message": f"Disk usage high: {current_status['disk_percent']:.1f}%",
                "threshold": self.thresholds.disk_warning,
                "current_value": current_status["disk_percent"]
            })
        
        # GPU警告（如果有GPU）
        if current_status.get("gpu_memory_used_mb") and current_status.get("gpu_memory_total_mb"):
            gpu_percent = (current_status["gpu_memory_used_mb"] / current_status["gpu_memory_total_mb"]) * 100
            
            if gpu_percent >= self.thresholds.gpu_memory_critical:
                alerts.append({
                    "type": "gpu_critical",
                    "level": "critical",
                    "message": f"GPU memory usage critical: {gpu_percent:.1f}%",
                    "threshold": self.thresholds.gpu_memory_critical,
                    "current_value": gpu_percent
                })
            elif gpu_percent >= self.thresholds.gpu_memory_warning:
                alerts.append({
                    "type": "gpu_warning", 
                    "level": "warning",
                    "message": f"GPU memory usage high: {gpu_percent:.1f}%",
                    "threshold": self.thresholds.gpu_memory_warning,
                    "current_value": gpu_percent
                })
        
        return alerts

# 全局资源监控器实例
resource_monitor = ResourceMonitor() 