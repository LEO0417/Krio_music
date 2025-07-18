"""
性能优化器 (Performance Optimizer)

这个模块提供了模型推理和系统性能优化功能，包括：
1. 模型推理优化（量化、缓存、批处理）
2. 内存管理优化
3. GPU优化（如果可用）
4. 动态性能调整
5. 负载均衡和资源分配
"""

import os
import gc
import time
import threading
import asyncio
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from contextlib import contextmanager
import weakref

import torch
import torch.nn as nn
from torch.cuda.amp import autocast, GradScaler
import psutil

from .resource_monitor import resource_monitor

logger = logging.getLogger("performance_optimizer")

class OptimizationLevel(Enum):
    """优化级别"""
    LOW = "low"           # 最小优化，最高质量
    MEDIUM = "medium"     # 平衡优化
    HIGH = "high"         # 最大优化，可能影响质量
    ADAPTIVE = "adaptive" # 自适应优化

class PerformanceMode(Enum):
    """性能模式"""
    QUALITY = "quality"       # 质量优先
    SPEED = "speed"          # 速度优先
    BALANCED = "balanced"    # 平衡模式
    MEMORY = "memory"        # 内存优先

@dataclass
class OptimizationConfig:
    """优化配置"""
    level: OptimizationLevel = OptimizationLevel.MEDIUM
    mode: PerformanceMode = PerformanceMode.BALANCED
    use_amp: bool = True              # 使用混合精度
    use_torch_compile: bool = False   # 使用torch.compile（需要PyTorch 2.0+）
    enable_memory_pool: bool = True   # 启用内存池
    max_memory_mb: int = 4096        # 最大内存使用（MB）
    batch_size: int = 1              # 批处理大小
    cache_size: int = 100            # 缓存大小
    gc_threshold: float = 0.8        # GC触发阈值
    enable_profiling: bool = False   # 启用性能分析

class MemoryPool:
    """内存池管理"""
    
    def __init__(self, max_size_mb: int = 2048):
        self.max_size_mb = max_size_mb
        self.allocated_tensors = []
        self.free_tensors = []
        self.lock = threading.Lock()
        self.current_size_mb = 0
        
    def allocate(self, shape: tuple, dtype: torch.dtype = torch.float32, device: str = "cpu") -> torch.Tensor:
        """分配tensor"""
        with self.lock:
            # 计算需要的内存大小
            element_size = torch.tensor([], dtype=dtype).element_size()
            tensor_size_mb = (torch.numel(torch.zeros(shape)) * element_size) / (1024 * 1024)
            
            # 检查是否超过最大内存限制
            if self.current_size_mb + tensor_size_mb > self.max_size_mb:
                self.cleanup()
            
            # 尝试从空闲列表中找到合适的tensor
            for i, (free_tensor, free_size) in enumerate(self.free_tensors):
                if (free_tensor.shape == shape and 
                    free_tensor.dtype == dtype and 
                    str(free_tensor.device) == device):
                    
                    tensor = self.free_tensors.pop(i)[0]
                    self.allocated_tensors.append((tensor, tensor_size_mb))
                    return tensor
            
            # 创建新的tensor
            tensor = torch.zeros(shape, dtype=dtype, device=device)
            self.allocated_tensors.append((tensor, tensor_size_mb))
            self.current_size_mb += tensor_size_mb
            
            return tensor
    
    def deallocate(self, tensor: torch.Tensor):
        """释放tensor"""
        with self.lock:
            for i, (allocated_tensor, size) in enumerate(self.allocated_tensors):
                if torch.equal(tensor, allocated_tensor):
                    self.allocated_tensors.pop(i)
                    self.free_tensors.append((tensor, size))
                    break
    
    def cleanup(self):
        """清理内存池"""
        with self.lock:
            # 清理空闲的tensor
            self.free_tensors.clear()
            
            # 手动垃圾回收
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

class ModelCache:
    """模型结果缓存"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
        self.lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存结果"""
        with self.lock:
            if key in self.cache:
                # 更新访问顺序
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value: Any):
        """放入缓存"""
        with self.lock:
            if key in self.cache:
                # 更新现有项
                self.access_order.remove(key)
                self.access_order.append(key)
                self.cache[key] = value
            else:
                # 添加新项
                if len(self.cache) >= self.max_size:
                    # 删除最旧的项
                    oldest_key = self.access_order.pop(0)
                    del self.cache[oldest_key]
                
                self.cache[key] = value
                self.access_order.append(key)
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.memory_pool = MemoryPool(max_size_mb=self.config.max_memory_mb // 2)
        self.model_cache = ModelCache(max_size=self.config.cache_size)
        self.scaler = GradScaler() if self.config.use_amp else None
        
        # 性能统计
        self.inference_times = []
        self.memory_usage = []
        self.optimization_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'memory_optimizations': 0,
            'gc_collections': 0
        }
        
        # 自适应优化状态
        self.adaptive_state = {
            'last_memory_usage': 0,
            'last_inference_time': 0,
            'performance_trend': 'stable'
        }
        
        logger.info(f"Performance optimizer initialized with config: {self.config}")
    
    def optimize_model(self, model: nn.Module) -> nn.Module:
        """优化模型"""
        logger.info("Optimizing model...")
        
        # 设置模型为评估模式
        model.eval()
        
        # 禁用梯度计算
        for param in model.parameters():
            param.requires_grad = False
        
        # 使用torch.compile优化（如果支持）
        if self.config.use_torch_compile and hasattr(torch, 'compile'):
            try:
                logger.info("Applying torch.compile optimization...")
                model = torch.compile(model, mode='reduce-overhead')
            except Exception as e:
                logger.warning(f"torch.compile optimization failed: {e}")
        
        # 模型量化（如果配置为高优化级别）
        if self.config.level == OptimizationLevel.HIGH:
            try:
                logger.info("Applying model quantization...")
                model = torch.quantization.quantize_dynamic(
                    model, 
                    {torch.nn.Linear}, 
                    dtype=torch.qint8
                )
            except Exception as e:
                logger.warning(f"Model quantization failed: {e}")
        
        return model
    
    def optimize_inference_settings(self):
        """优化推理设置"""
        # 设置PyTorch优化
        torch.set_num_threads(min(4, psutil.cpu_count()))
        torch.set_grad_enabled(False)
        
        # CUDA优化
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
            
            # 设置内存管理
            torch.cuda.empty_cache()
            if hasattr(torch.cuda, 'memory_management'):
                torch.cuda.set_per_process_memory_fraction(0.8)
    
    @contextmanager
    def inference_context(self, model_name: str = "default"):
        """推理上下文管理器"""
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        try:
            # 预优化
            self._pre_inference_optimization()
            
            # 自适应优化
            if self.config.level == OptimizationLevel.ADAPTIVE:
                self._adaptive_optimization()
            
            yield
            
        finally:
            # 后优化
            self._post_inference_optimization()
            
            # 记录性能统计
            inference_time = time.time() - start_time
            final_memory = self._get_memory_usage()
            
            self.inference_times.append(inference_time)
            self.memory_usage.append(final_memory - initial_memory)
            
            # 保持统计数据在合理范围内
            if len(self.inference_times) > 100:
                self.inference_times = self.inference_times[-100:]
                self.memory_usage = self.memory_usage[-100:]
            
            logger.debug(f"Inference completed in {inference_time:.2f}s, "
                        f"memory delta: {final_memory - initial_memory:.2f}MB")
    
    def _pre_inference_optimization(self):
        """推理前优化"""
        # 检查内存使用情况
        current_memory = self._get_memory_usage()
        if current_memory > self.config.max_memory_mb * self.config.gc_threshold:
            logger.info("Memory usage high, triggering garbage collection...")
            self._trigger_gc()
            self.optimization_stats['gc_collections'] += 1
    
    def _post_inference_optimization(self):
        """推理后优化"""
        # 清理GPU缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # 更新自适应状态
        if self.config.level == OptimizationLevel.ADAPTIVE:
            self._update_adaptive_state()
    
    def _adaptive_optimization(self):
        """自适应优化"""
        current_memory = self._get_memory_usage()
        
        # 基于内存使用情况调整优化策略
        if current_memory > self.config.max_memory_mb * 0.8:
            # 高内存使用，切换到内存优先模式
            self.config.mode = PerformanceMode.MEMORY
            self._trigger_gc()
        elif current_memory < self.config.max_memory_mb * 0.4:
            # 低内存使用，可以优先质量
            self.config.mode = PerformanceMode.QUALITY
        else:
            # 平衡使用
            self.config.mode = PerformanceMode.BALANCED
    
    def _update_adaptive_state(self):
        """更新自适应状态"""
        if self.inference_times:
            current_time = self.inference_times[-1]
            if len(self.inference_times) > 1:
                prev_time = self.inference_times[-2]
                if current_time > prev_time * 1.1:
                    self.adaptive_state['performance_trend'] = 'degrading'
                elif current_time < prev_time * 0.9:
                    self.adaptive_state['performance_trend'] = 'improving'
                else:
                    self.adaptive_state['performance_trend'] = 'stable'
    
    def _get_memory_usage(self) -> float:
        """获取内存使用情况（MB）"""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 * 1024)
        else:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
    
    def _trigger_gc(self):
        """触发垃圾回收"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.memory_pool.cleanup()
    
    def cache_result(self, key: str, result: Any):
        """缓存结果"""
        self.model_cache.put(key, result)
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """获取缓存结果"""
        result = self.model_cache.get(key)
        if result is not None:
            self.optimization_stats['cache_hits'] += 1
        else:
            self.optimization_stats['cache_misses'] += 1
        return result
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = {
            'optimization_config': {
                'level': self.config.level.value,
                'mode': self.config.mode.value,
                'use_amp': self.config.use_amp,
                'use_torch_compile': self.config.use_torch_compile,
                'max_memory_mb': self.config.max_memory_mb,
                'cache_size': self.config.cache_size
            },
            'inference_stats': {
                'total_inferences': len(self.inference_times),
                'avg_inference_time': sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0,
                'min_inference_time': min(self.inference_times) if self.inference_times else 0,
                'max_inference_time': max(self.inference_times) if self.inference_times else 0,
                'avg_memory_usage': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
                'peak_memory_usage': max(self.memory_usage) if self.memory_usage else 0
            },
            'cache_stats': {
                'cache_hits': self.optimization_stats['cache_hits'],
                'cache_misses': self.optimization_stats['cache_misses'],
                'hit_rate': (self.optimization_stats['cache_hits'] / 
                           (self.optimization_stats['cache_hits'] + self.optimization_stats['cache_misses'])) 
                           if (self.optimization_stats['cache_hits'] + self.optimization_stats['cache_misses']) > 0 else 0
            },
            'memory_stats': {
                'current_memory_mb': self._get_memory_usage(),
                'memory_pool_size_mb': self.memory_pool.current_size_mb,
                'gc_collections': self.optimization_stats['gc_collections'],
                'memory_optimizations': self.optimization_stats['memory_optimizations']
            },
            'adaptive_state': self.adaptive_state.copy()
        }
        
        return stats
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        recommendations = []
        
        # 分析性能统计
        if self.inference_times:
            avg_time = sum(self.inference_times) / len(self.inference_times)
            if avg_time > 10.0:  # 如果平均推理时间超过10秒
                recommendations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'message': f'Average inference time is high ({avg_time:.2f}s). Consider increasing optimization level.',
                    'suggestion': 'Increase optimization level to HIGH or enable model quantization'
                })
        
        # 内存使用分析
        current_memory = self._get_memory_usage()
        if current_memory > self.config.max_memory_mb * 0.9:
            recommendations.append({
                'type': 'memory',
                'priority': 'high',
                'message': f'Memory usage is very high ({current_memory:.2f}MB). Risk of OOM.',
                'suggestion': 'Reduce batch size, enable memory optimization, or increase max memory limit'
            })
        
        # 缓存命中率分析
        total_requests = self.optimization_stats['cache_hits'] + self.optimization_stats['cache_misses']
        if total_requests > 0:
            hit_rate = self.optimization_stats['cache_hits'] / total_requests
            if hit_rate < 0.3:
                recommendations.append({
                    'type': 'cache',
                    'priority': 'medium',
                    'message': f'Cache hit rate is low ({hit_rate:.2%}). Consider increasing cache size.',
                    'suggestion': 'Increase cache size or review caching strategy'
                })
        
        # GPU使用分析
        if torch.cuda.is_available():
            if not self.config.use_amp:
                recommendations.append({
                    'type': 'gpu',
                    'priority': 'medium',
                    'message': 'Mixed precision training is disabled. This could improve performance.',
                    'suggestion': 'Enable mixed precision (AMP) for better GPU utilization'
                })
        
        return recommendations
    
    def apply_optimization_profile(self, profile_name: str):
        """应用优化配置文件"""
        profiles = {
            'speed': OptimizationConfig(
                level=OptimizationLevel.HIGH,
                mode=PerformanceMode.SPEED,
                use_amp=True,
                use_torch_compile=True,
                max_memory_mb=2048,
                cache_size=200
            ),
            'quality': OptimizationConfig(
                level=OptimizationLevel.LOW,
                mode=PerformanceMode.QUALITY,
                use_amp=False,
                use_torch_compile=False,
                max_memory_mb=8192,
                cache_size=50
            ),
            'balanced': OptimizationConfig(
                level=OptimizationLevel.MEDIUM,
                mode=PerformanceMode.BALANCED,
                use_amp=True,
                use_torch_compile=False,
                max_memory_mb=4096,
                cache_size=100
            ),
            'memory': OptimizationConfig(
                level=OptimizationLevel.HIGH,
                mode=PerformanceMode.MEMORY,
                use_amp=True,
                use_torch_compile=True,
                max_memory_mb=1024,
                cache_size=50,
                gc_threshold=0.7
            )
        }
        
        if profile_name in profiles:
            self.config = profiles[profile_name]
            logger.info(f"Applied optimization profile: {profile_name}")
        else:
            logger.warning(f"Unknown optimization profile: {profile_name}")
    
    def reset_stats(self):
        """重置统计数据"""
        self.inference_times.clear()
        self.memory_usage.clear()
        self.optimization_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'memory_optimizations': 0,
            'gc_collections': 0
        }
        self.model_cache.clear()
        logger.info("Performance statistics reset")

# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()

# 优化装饰器
def optimize_inference(cache_key: str = None, profile: str = None):
    """推理优化装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 应用配置文件
            if profile:
                performance_optimizer.apply_optimization_profile(profile)
            
            # 检查缓存
            if cache_key:
                cached_result = performance_optimizer.get_cached_result(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # 执行推理
            with performance_optimizer.inference_context():
                result = func(*args, **kwargs)
            
            # 缓存结果
            if cache_key:
                performance_optimizer.cache_result(cache_key, result)
            
            return result
        return wrapper
    return decorator