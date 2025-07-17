"""
模型管理器测试

这个模块包含了对模型管理器功能的全面测试，包括：
1. 模型加载和卸载测试
2. 资源监控测试
3. API端点测试
4. 错误处理测试
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import torch

from models.model_manager import ModelManager, ModelStatus, ModelInfo
from models.resource_monitor import ResourceMonitor, ResourceSnapshot
from api.errors import ModelLoadError, ResourceLimitExceededError

class TestModelManager:
    """模型管理器测试类"""
    
    @pytest.fixture
    def model_manager(self):
        """创建测试用的模型管理器实例"""
        manager = ModelManager()
        # 禁用自动加载以避免在测试中加载真实模型
        manager.auto_load = False
        return manager
    
    def test_model_manager_initialization(self, model_manager):
        """测试模型管理器初始化"""
        assert model_manager.model is None
        assert model_manager.processor is None
        assert model_manager.model_info.status == ModelStatus.NOT_LOADED
        assert isinstance(model_manager.model_info, ModelInfo)
    
    def test_model_info_to_dict(self):
        """测试模型信息转换为字典"""
        model_info = ModelInfo()
        model_info.name = "test-model"
        model_info.status = ModelStatus.LOADED
        model_info.device = "cpu"
        
        info_dict = model_info.to_dict()
        assert info_dict["name"] == "test-model"
        assert info_dict["status"] == "loaded"
        assert info_dict["device"] == "cpu"
    
    @patch('models.model_manager.psutil.virtual_memory')
    @patch('models.model_manager.psutil.disk_usage')
    def test_check_system_resources_sufficient(self, mock_disk, mock_memory, model_manager):
        """测试系统资源充足的情况"""
        # 模拟足够的内存和磁盘空间
        mock_memory.return_value.percent = 50.0  # 50% 内存使用
        mock_disk.return_value.free = 10 * (1024**3)  # 10GB 可用空间
        
        assert model_manager._check_system_resources() == True
    
    @patch('models.model_manager.psutil.virtual_memory')
    def test_check_system_resources_insufficient_memory(self, mock_memory, model_manager):
        """测试内存不足的情况"""
        # 模拟内存不足
        mock_memory.return_value.percent = 95.0  # 95% 内存使用
        
        assert model_manager._check_system_resources() == False
    
    @patch('models.model_manager.psutil.disk_usage')
    def test_check_system_resources_insufficient_disk(self, mock_disk, model_manager):
        """测试磁盘空间不足的情况"""
        # 模拟磁盘空间不足
        mock_disk.return_value.free = 1 * (1024**3)  # 只有1GB可用空间
        
        assert model_manager._check_system_resources() == False
    
    @patch('models.model_manager.torch.cuda.is_available')
    @patch('models.model_manager.torch.cuda.get_device_properties')
    def test_get_model_device_gpu_available(self, mock_props, mock_cuda, model_manager):
        """测试GPU可用时的设备选择"""
        model_manager.use_gpu = True
        mock_cuda.return_value = True
        
        # 模拟足够的GPU内存
        mock_device = Mock()
        mock_device.total_memory = 8 * (1024**3)  # 8GB GPU内存
        mock_props.return_value = mock_device
        
        device = model_manager._get_model_device()
        assert device == "cuda"
    
    @patch('models.model_manager.torch.cuda.is_available')
    def test_get_model_device_gpu_unavailable(self, mock_cuda, model_manager):
        """测试GPU不可用时的设备选择"""
        mock_cuda.return_value = False
        
        device = model_manager._get_model_device()
        assert device == "cpu"
    
    @pytest.mark.asyncio
    async def test_load_model_already_loaded(self, model_manager):
        """测试模型已加载时的行为"""
        # 设置模型为已加载状态
        model_manager.model_info.status = ModelStatus.LOADED
        model_manager.model = Mock()
        model_manager.processor = Mock()
        
        result = await model_manager.load_model()
        assert result == True
    
    @pytest.mark.asyncio
    async def test_load_model_already_loading(self, model_manager):
        """测试模型正在加载时的行为"""
        # 设置模型为正在加载状态
        model_manager.model_info.status = ModelStatus.LOADING
        
        result = await model_manager.load_model()
        assert result == False
    
    @pytest.mark.asyncio
    @patch('models.model_manager.ModelManager._check_system_resources')
    async def test_load_model_insufficient_resources(self, mock_resources, model_manager):
        """测试资源不足时的模型加载"""
        mock_resources.return_value = False
        
        with pytest.raises(ResourceLimitExceededError):
            await model_manager.load_model()
    
    @pytest.mark.asyncio
    @patch('models.model_manager.ModelManager._load_model_sync')
    @patch('models.model_manager.ModelManager._check_system_resources')
    @patch('models.model_manager.ModelManager._get_model_device')
    @patch('models.model_manager.asyncio.to_thread')
    async def test_load_model_success(self, mock_thread, mock_device, mock_resources, mock_sync, model_manager):
        """测试成功加载模型"""
        mock_resources.return_value = True
        mock_device.return_value = "cpu"
        mock_thread.return_value = None
        
        # 模拟成功加载
        model_manager.model = Mock()
        model_manager.processor = Mock()
        
        result = await model_manager.load_model("test-model")
        assert result == True
        assert model_manager.model_info.status == ModelStatus.LOADED
        assert model_manager.model_info.name == "test-model"
    
    @pytest.mark.asyncio
    async def test_unload_model_not_loaded(self, model_manager):
        """测试卸载未加载的模型"""
        model_manager.model_info.status = ModelStatus.NOT_LOADED
        
        result = await model_manager.unload_model()
        assert result == True
    
    @pytest.mark.asyncio
    @patch('models.model_manager.ModelManager._cleanup_model')
    async def test_unload_model_success(self, mock_cleanup, model_manager):
        """测试成功卸载模型"""
        # 设置模型为已加载状态
        model_manager.model_info.status = ModelStatus.LOADED
        model_manager.model = Mock()
        model_manager.processor = Mock()
        
        mock_cleanup.return_value = None
        
        result = await model_manager.unload_model()
        assert result == True
        assert model_manager.model_info.status == ModelStatus.NOT_LOADED
    
    def test_is_ready_true(self, model_manager):
        """测试模型准备就绪的检查"""
        model_manager.model_info.status = ModelStatus.LOADED
        model_manager.model = Mock()
        model_manager.processor = Mock()
        
        assert model_manager.is_ready() == True
    
    def test_is_ready_false(self, model_manager):
        """测试模型未准备就绪的检查"""
        model_manager.model_info.status = ModelStatus.NOT_LOADED
        model_manager.model = None
        model_manager.processor = None
        
        assert model_manager.is_ready() == False
    
    def test_get_model_status(self, model_manager):
        """测试获取模型状态"""
        model_manager.model_info.name = "test-model"
        model_manager.model_info.status = ModelStatus.LOADED
        model_manager.model_info.device = "cpu"
        
        status = model_manager.get_model_status()
        assert status["name"] == "test-model"
        assert status["status"] == "loaded"
        assert status["device"] == "cpu"
    
    @pytest.mark.asyncio
    @patch('models.model_manager.psutil.virtual_memory')
    async def test_health_check(self, mock_memory, model_manager):
        """测试健康检查"""
        mock_memory.return_value.percent = 50.0
        
        model_manager.model_info.status = ModelStatus.LOADED
        model_manager.model_info.device = "cpu"
        model_manager.model_info.memory_usage = 100
        
        health = await model_manager.health_check()
        assert "model_loaded" in health
        assert "model_status" in health
        assert "device" in health
        assert "timestamp" in health
    
    def test_record_inference(self, model_manager):
        """测试记录推理调用"""
        initial_count = model_manager.model_info.inference_count
        
        model_manager.record_inference()
        
        assert model_manager.model_info.inference_count == initial_count + 1
        assert model_manager.model_info.last_inference_time is not None

class TestResourceMonitor:
    """资源监控器测试类"""
    
    @pytest.fixture
    def resource_monitor(self):
        """创建测试用的资源监控器实例"""
        return ResourceMonitor(history_size=10, monitor_interval=0.1)
    
    def test_resource_monitor_initialization(self, resource_monitor):
        """测试资源监控器初始化"""
        assert resource_monitor.history_size == 10
        assert resource_monitor.monitor_interval == 0.1
        assert resource_monitor.is_monitoring == False
        assert len(resource_monitor.resource_history) == 0
    
    def test_resource_snapshot_to_dict(self):
        """测试资源快照转换为字典"""
        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=1000,
            memory_total_mb=2000,
            disk_percent=70.0,
            disk_used_gb=50,
            disk_total_gb=100
        )
        
        snapshot_dict = snapshot.to_dict()
        assert snapshot_dict["cpu_percent"] == 50.0
        assert snapshot_dict["memory_percent"] == 60.0
        assert snapshot_dict["disk_percent"] == 70.0
    
    @patch('models.resource_monitor.psutil.cpu_percent')
    @patch('models.resource_monitor.psutil.virtual_memory')
    @patch('models.resource_monitor.psutil.disk_usage')
    def test_get_current_snapshot(self, mock_disk, mock_memory, mock_cpu, resource_monitor):
        """测试获取当前资源快照"""
        # 模拟系统资源使用情况
        mock_cpu.return_value = 25.0
        
        mock_mem = Mock()
        mock_mem.percent = 40.0
        mock_mem.used = 1000 * (1024 * 1024)  # 1000MB
        mock_mem.total = 2000 * (1024 * 1024)  # 2000MB
        mock_memory.return_value = mock_mem
        
        mock_disk_info = Mock()
        mock_disk_info.percent = 30.0
        mock_disk_info.used = 50 * (1024**3)  # 50GB
        mock_disk_info.total = 100 * (1024**3)  # 100GB
        mock_disk.return_value = mock_disk_info
        
        snapshot = resource_monitor._get_current_snapshot()
        
        assert snapshot.cpu_percent == 25.0
        assert snapshot.memory_percent == 40.0
        assert snapshot.memory_used_mb == 1000
        assert snapshot.disk_percent == 30.0
    
    def test_add_warning_callback(self, resource_monitor):
        """测试添加警告回调"""
        callback = Mock()
        resource_monitor.add_warning_callback(callback)
        
        assert callback in resource_monitor.warning_callbacks
    
    def test_check_thresholds_cpu_warning(self, resource_monitor):
        """测试CPU使用率警告"""
        callback = Mock()
        resource_monitor.add_warning_callback(callback)
        
        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=85.0,  # 超过警告阈值
            memory_percent=50.0,
            memory_used_mb=1000,
            memory_total_mb=2000,
            disk_percent=50.0,
            disk_used_gb=50,
            disk_total_gb=100
        )
        
        resource_monitor._check_thresholds(snapshot)
        
        # 验证警告回调被调用
        callback.assert_called()
        args = callback.call_args[0]
        assert args[0] == "cpu_warning"
    
    def test_record_inference_timing(self, resource_monitor):
        """测试推理计时记录"""
        start_time = resource_monitor.record_inference_start()
        assert isinstance(start_time, float)
        
        # 模拟一些处理时间
        import time
        time.sleep(0.001)
        
        initial_count = resource_monitor.performance_metrics.total_inferences
        resource_monitor.record_inference_end(start_time, success=True)
        
        assert resource_monitor.performance_metrics.total_inferences == initial_count + 1
        assert resource_monitor.performance_metrics.successful_inferences == 1
        assert len(resource_monitor.inference_times) == 1
    
    def test_get_performance_metrics(self, resource_monitor):
        """测试获取性能指标"""
        # 记录一些推理
        for i in range(3):
            start_time = resource_monitor.record_inference_start()
            # 模拟一些处理时间
            import time
            time.sleep(0.001)
            resource_monitor.record_inference_end(start_time, success=True)
        
        metrics = resource_monitor.get_performance_metrics()
        
        assert metrics["total_inferences"] == 3
        assert metrics["successful_inferences"] == 3
        assert metrics["failed_inferences"] == 0
        # 检查推理时间是否被正确记录
        assert len(resource_monitor.inference_times) == 3
        # 如果有推理时间记录，平均时间应该大于0
        if resource_monitor.inference_times:
            assert metrics["avg_inference_time"] > 0
    
    def test_clear_history(self, resource_monitor):
        """测试清除历史记录"""
        # 添加一些历史记录
        for i in range(5):
            start_time = resource_monitor.record_inference_start()
            resource_monitor.record_inference_end(start_time)
        
        assert resource_monitor.performance_metrics.total_inferences == 5
        
        resource_monitor.clear_history()
        
        assert resource_monitor.performance_metrics.total_inferences == 0
        assert len(resource_monitor.inference_times) == 0
        assert len(resource_monitor.resource_history) == 0
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, resource_monitor):
        """测试监控生命周期"""
        assert resource_monitor.is_monitoring == False
        
        # 启动监控
        await resource_monitor.start_monitoring()
        assert resource_monitor.is_monitoring == True
        assert resource_monitor.monitor_task is not None
        
        # 等待一小段时间让监控运行
        await asyncio.sleep(0.2)
        
        # 停止监控
        await resource_monitor.stop_monitoring()
        assert resource_monitor.is_monitoring == False
        assert resource_monitor.monitor_task is None

class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.mark.asyncio
    async def test_model_api_endpoints_available(self):
        """测试模型API端点是否可用"""
        from api.models import router
        
        # 检查路由是否包含期望的端点
        routes = [route.path for route in router.routes]
        
        expected_routes = [
            "/status",
            "/load", 
            "/unload",
            "/health",
            "/resources",
            "/info",
            "/reload",
            "/logs"
        ]
        
        for expected_route in expected_routes:
            assert expected_route in routes

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 