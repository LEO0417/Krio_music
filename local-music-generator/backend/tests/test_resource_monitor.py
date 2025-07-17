"""
测试资源监控器功能

测试内容包括：
1. 资源监控器基本功能
2. 趋势分析功能
3. 警告系统集成
4. 通知系统集成
5. API端点测试
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from models.resource_monitor import (
    ResourceMonitor, 
    ResourceSnapshot, 
    ResourceThresholds,
    PerformanceMetrics
)
from models.notification_system import NotificationSystem, NotificationLevel, NotificationType
from api.system import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router, prefix="/system")
client = TestClient(app)

class TestResourceMonitor:
    """测试ResourceMonitor类"""
    
    def setup_method(self):
        """测试前设置"""
        self.monitor = ResourceMonitor(history_size=100, monitor_interval=0.1)
    
    def teardown_method(self):
        """测试后清理"""
        if self.monitor.is_monitoring:
            asyncio.run(self.monitor.stop_monitoring())
    
    def test_initialization(self):
        """测试初始化"""
        assert not self.monitor.is_monitoring
        assert self.monitor.history_size == 100
        assert self.monitor.monitor_interval == 0.1
        assert isinstance(self.monitor.thresholds, ResourceThresholds)
        assert isinstance(self.monitor.notification_system, NotificationSystem)
        assert len(self.monitor.resource_history) == 0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('torch.cuda.is_available')
    def test_get_current_snapshot(self, mock_cuda, mock_disk, mock_memory, mock_cpu):
        """测试获取当前资源快照"""
        # Mock系统资源
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, used=8*1024**3, total=16*1024**3)
        mock_disk.return_value = Mock(percent=70.0, used=100*1024**3, total=500*1024**3)
        mock_cuda.return_value = False
        
        snapshot = self.monitor._get_current_snapshot()
        
        assert isinstance(snapshot, ResourceSnapshot)
        assert snapshot.cpu_percent == 50.0
        assert snapshot.memory_percent == 60.0
        assert snapshot.disk_percent == 70.0
        assert snapshot.gpu_memory_used_mb is None
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory') 
    @patch('psutil.disk_usage')
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.memory_allocated')
    @patch('torch.cuda.get_device_properties')
    def test_get_current_snapshot_with_gpu(self, mock_props, mock_allocated, mock_cuda, mock_disk, mock_memory, mock_cpu):
        """测试获取带GPU的资源快照"""
        # Mock系统资源
        mock_cpu.return_value = 40.0
        mock_memory.return_value = Mock(percent=50.0, used=4*1024**3, total=8*1024**3)
        mock_disk.return_value = Mock(percent=30.0, used=50*1024**3, total=200*1024**3)
        
        # Mock GPU
        mock_cuda.return_value = True
        mock_allocated.return_value = 2*1024**3  # 2GB used
        mock_props.return_value = Mock(total_memory=8*1024**3)  # 8GB total
        
        snapshot = self.monitor._get_current_snapshot()
        
        assert snapshot.gpu_memory_used_mb == 2048  # 2GB in MB
        assert snapshot.gpu_memory_total_mb == 8192  # 8GB in MB
    
    def test_check_thresholds_no_warnings(self):
        """测试阈值检查 - 无警告"""
        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=30.0,
            memory_percent=40.0,
            memory_used_mb=4000,
            memory_total_mb=8000,
            disk_percent=50.0,
            disk_used_gb=100,
            disk_total_gb=200
        )
        
        # 应该没有警告被触发
        self.monitor._check_thresholds(snapshot)
        # 这里我们只是确保没有异常被抛出
    
    def test_check_thresholds_with_warnings(self):
        """测试阈值检查 - 有警告"""
        warning_triggered = []
        
        def mock_callback(warning_type, details):
            warning_triggered.append((warning_type, details))
        
        self.monitor.add_warning_callback(mock_callback)
        
        # 创建超过警告阈值的快照
        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=85.0,  # 超过80%警告阈值
            memory_percent=85.0,  # 超过80%警告阈值
            memory_used_mb=6800,
            memory_total_mb=8000,
            disk_percent=85.0,  # 超过80%警告阈值
            disk_used_gb=170,
            disk_total_gb=200
        )
        
        self.monitor._check_thresholds(snapshot)
        
        # 应该触发3个警告
        assert len(warning_triggered) == 3
        warning_types = [w[0] for w in warning_triggered]
        assert "cpu_warning" in warning_types
        assert "memory_warning" in warning_types
        assert "disk_warning" in warning_types
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        assert not self.monitor.is_monitoring
        
        # 启动监控
        await self.monitor.start_monitoring()
        assert self.monitor.is_monitoring
        
        # 等待一点时间让监控收集数据
        await asyncio.sleep(0.2)
        
        # 停止监控
        await self.monitor.stop_monitoring()
        assert not self.monitor.is_monitoring
    
    def test_record_inference_time(self):
        """测试记录推理时间"""
        assert len(self.monitor.inference_times) == 0
        
        # 模拟推理时间记录
        import time
        
        # 记录三次推理，每次等待少量时间来模拟推理过程
        start1 = time.time() - 1.5  # 模拟1.5秒前开始
        self.monitor.record_inference_end(start1)
        
        start2 = time.time() - 2.0  # 模拟2.0秒前开始
        self.monitor.record_inference_end(start2)
        
        start3 = time.time() - 1.8  # 模拟1.8秒前开始
        self.monitor.record_inference_end(start3)
        
        assert len(self.monitor.inference_times) == 3
        # 检查记录的推理时间大致正确（允许一些误差）
        times = list(self.monitor.inference_times)
        assert 1.4 <= times[0] <= 1.6  # 大约1.5秒
        assert 1.9 <= times[1] <= 2.1  # 大约2.0秒
        assert 1.7 <= times[2] <= 1.9  # 大约1.8秒
    
    def test_get_current_status(self):
        """测试获取当前状态"""
        with patch.object(self.monitor, '_get_current_snapshot') as mock_snapshot:
            mock_snapshot.return_value = ResourceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=45.0,
                memory_percent=55.0,
                memory_used_mb=4400,
                memory_total_mb=8000,
                disk_percent=65.0,
                disk_used_gb=130,
                disk_total_gb=200
            )
            
            status = self.monitor.get_current_status()
            
            assert status["cpu_percent"] == 45.0
            assert status["memory_percent"] == 55.0
            assert status["disk_percent"] == 65.0
            assert status["is_monitoring"] == False
    
    def test_get_resource_history(self):
        """测试获取资源历史"""
        # 添加一些历史数据
        now = datetime.now()
        for i in range(5):
            snapshot = ResourceSnapshot(
                timestamp=now - timedelta(minutes=i),
                cpu_percent=50.0 + i,
                memory_percent=60.0 + i,
                memory_used_mb=4000 + i*100,
                memory_total_mb=8000,
                disk_percent=70.0 + i,
                disk_used_gb=100 + i*10,
                disk_total_gb=200
            )
            self.monitor.resource_history.append(snapshot)
        
        # 获取最近3分钟的历史
        history = self.monitor.get_resource_history(minutes=3)
        
        # 应该有4个记录（0, 1, 2, 3分钟前的），但由于时间精度问题，可能是3个
        assert len(history) >= 3
    
    def test_get_resource_summary(self):
        """测试获取资源摘要"""
        with patch.object(self.monitor, 'get_current_status') as mock_status:
            mock_status.return_value = {
                "cpu_percent": 70.0,
                "memory_percent": 60.0,
                "disk_percent": 50.0
            }
            
            summary = self.monitor.get_resource_summary()
            
            assert "current_status" in summary
            assert "performance_metrics" in summary
            assert "health" in summary
            assert "thresholds" in summary
            
            health = summary["health"]
            assert "score" in health
            assert "status" in health
            assert "warnings" in health

class TestResourceTrends:
    """测试资源趋势分析"""
    
    def setup_method(self):
        """测试前设置"""
        self.monitor = ResourceMonitor(history_size=100, monitor_interval=0.1)
        
        # 创建模拟的历史数据
        now = datetime.now()
        for i in range(20):
            snapshot = ResourceSnapshot(
                timestamp=now - timedelta(minutes=i),
                cpu_percent=50.0 + i,  # 递增趋势
                memory_percent=60.0 - i*0.5,  # 递减趋势
                memory_used_mb=4000 + i*50,
                memory_total_mb=8000,
                disk_percent=40.0,  # 稳定
                disk_used_gb=100,
                disk_total_gb=200
            )
            self.monitor.resource_history.append(snapshot)
    
    def test_get_resource_trend_cpu_increasing(self):
        """测试CPU使用趋势 - 递增"""
        trend = self.monitor.get_resource_trend("cpu", minutes=30)
        
        assert trend["resource_type"] == "cpu"
        assert trend["trend"] == "increasing"
        assert trend["change_rate"] > 0
        assert "prediction_10min" in trend
        assert "statistics" in trend
    
    def test_get_resource_trend_memory_decreasing(self):
        """测试内存使用趋势 - 递减"""
        trend = self.monitor.get_resource_trend("memory", minutes=30)
        
        assert trend["resource_type"] == "memory"
        assert trend["trend"] == "decreasing"
        assert trend["change_rate"] < 0
    
    def test_get_resource_trend_disk_stable(self):
        """测试磁盘使用趋势 - 稳定"""
        trend = self.monitor.get_resource_trend("disk", minutes=30)
        
        assert trend["resource_type"] == "disk"
        assert trend["trend"] == "stable"
        assert abs(trend["change_rate"]) < 0.1
    
    def test_get_all_trends(self):
        """测试获取所有趋势"""
        trends = self.monitor.get_all_trends(minutes=30)
        
        assert "timestamp" in trends
        assert "analysis_window_minutes" in trends
        assert "trends" in trends
        
        trend_data = trends["trends"]
        assert "cpu" in trend_data
        assert "memory" in trend_data
        assert "disk" in trend_data
    
    def test_get_resource_trend_no_history(self):
        """测试无历史数据时的趋势分析"""
        empty_monitor = ResourceMonitor()
        trend = empty_monitor.get_resource_trend("cpu", minutes=30)
        
        assert "error" in trend
        assert trend["trend"] == "unknown"
    
    def test_get_resource_trend_insufficient_data(self):
        """测试数据不足时的趋势分析"""
        limited_monitor = ResourceMonitor()
        
        # 只添加一个数据点
        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=4000,
            memory_total_mb=8000,
            disk_percent=40.0,
            disk_used_gb=100,
            disk_total_gb=200
        )
        limited_monitor.resource_history.append(snapshot)
        
        trend = limited_monitor.get_resource_trend("cpu", minutes=30)
        
        assert "error" in trend
        assert trend["trend"] == "unknown"

class TestResourceAlerts:
    """测试资源警告"""
    
    def setup_method(self):
        """测试前设置"""
        self.monitor = ResourceMonitor()
    
    def test_get_resource_alerts_no_warnings(self):
        """测试无警告时的资源警告"""
        with patch.object(self.monitor, 'get_current_status') as mock_status:
            mock_status.return_value = {
                "cpu_percent": 30.0,
                "memory_percent": 40.0,
                "disk_percent": 50.0,
                "gpu_memory_used_mb": None,
                "gpu_memory_total_mb": None
            }
            
            alerts = self.monitor.get_resource_alerts()
            assert len(alerts) == 0
    
    def test_get_resource_alerts_with_warnings(self):
        """测试有警告时的资源警告"""
        with patch.object(self.monitor, 'get_current_status') as mock_status:
            mock_status.return_value = {
                "cpu_percent": 85.0,  # 超过警告阈值
                "memory_percent": 85.0,  # 超过警告阈值
                "disk_percent": 60.0,  # 正常
                "gpu_memory_used_mb": None,
                "gpu_memory_total_mb": None
            }
            
            alerts = self.monitor.get_resource_alerts()
            
            assert len(alerts) == 2
            alert_types = [alert["type"] for alert in alerts]
            assert "cpu_warning" in alert_types
            assert "memory_warning" in alert_types
    
    def test_get_resource_alerts_critical(self):
        """测试严重警告"""
        with patch.object(self.monitor, 'get_current_status') as mock_status:
            mock_status.return_value = {
                "cpu_percent": 95.0,  # 超过严重阈值
                "memory_percent": 95.0,  # 超过严重阈值
                "disk_percent": 95.0,  # 超过严重阈值
                "gpu_memory_used_mb": 7000,  # 7GB
                "gpu_memory_total_mb": 8000   # 8GB total = 87.5%
            }
            
            alerts = self.monitor.get_resource_alerts()
            
            assert len(alerts) >= 3
            critical_alerts = [alert for alert in alerts if alert["level"] == "critical"]
            assert len(critical_alerts) >= 3

class TestSystemAPI:
    """测试系统API端点"""
    
    def test_get_resource_trends_api(self):
        """测试资源趋势API端点"""
        with patch('api.system.resource_monitor') as mock_monitor:
            mock_monitor.get_all_trends.return_value = {
                "timestamp": datetime.now().isoformat(),
                "analysis_window_minutes": 30,
                "trends": {
                    "cpu": {"trend": "stable", "change_rate": 0.05},
                    "memory": {"trend": "increasing", "change_rate": 0.5}
                }
            }
            
            response = client.get("/system/resources/trends?minutes=30")
            assert response.status_code == 200
            
            data = response.json()
            assert "trends" in data
            assert "timestamp" in data
    
    def test_get_resource_trend_specific_api(self):
        """测试特定资源趋势API端点"""
        with patch('api.system.resource_monitor') as mock_monitor:
            mock_monitor.get_resource_trend.return_value = {
                "resource_type": "cpu",
                "trend": "stable",
                "change_rate": 0.05,
                "prediction_10min": 52.0
            }
            
            response = client.get("/system/resources/trend/cpu?minutes=30")
            assert response.status_code == 200
            
            data = response.json()
            assert data["resource_type"] == "cpu"
            assert "trend" in data
    
    def test_get_resource_trend_invalid_type(self):
        """测试无效资源类型"""
        response = client.get("/system/resources/trend/invalid?minutes=30")
        assert response.status_code == 400
    
    def test_get_resource_alerts_api(self):
        """测试资源警告API端点"""
        with patch('api.system.resource_monitor') as mock_monitor:
            mock_monitor.get_resource_alerts.return_value = [
                {
                    "type": "cpu_warning",
                    "level": "warning",
                    "message": "CPU usage high: 85.0%",
                    "current_value": 85.0
                }
            ]
            
            response = client.get("/system/resources/alerts")
            assert response.status_code == 200
            
            data = response.json()
            assert "alerts" in data
            assert "count" in data
            assert data["count"] == 1

class TestNotificationIntegration:
    """测试通知系统集成"""
    
    def setup_method(self):
        """测试前设置"""
        self.monitor = ResourceMonitor()
    
    def test_notification_system_initialization(self):
        """测试通知系统初始化"""
        assert hasattr(self.monitor, 'notification_system')
        assert isinstance(self.monitor.notification_system, NotificationSystem)
    
    def test_warning_callback_triggers_notification(self):
        """测试警告回调触发通知"""
        # 模拟警告触发
        warning_type = "cpu_warning"
        details = {"cpu_percent": 85.0, "threshold": 80.0}
        
        with patch.object(self.monitor.notification_system, 'send_notification') as mock_send:
            self.monitor._trigger_warning(warning_type, details)
            
            # 验证通知被发送
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]['level'] == NotificationLevel.WARNING
            assert call_args[1]['notification_type'] == NotificationType.RESOURCE_WARNING

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 