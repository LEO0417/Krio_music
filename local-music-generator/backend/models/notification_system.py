"""
通知系统 (Notification System)

这个模块提供了全面的通知和警告管理功能，包括：
1. 资源警告通知
2. 系统状态变化通知
3. 模型状态通知
4. 通知历史和管理
5. 邮件/Webhook通知（可扩展）

技术说明：
- 支持多种通知类型和严重程度
- 实时通知和历史管理
- 可配置的通知规则和阈值
- 支持通知去重和频率限制
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import uuid

# Configure logging
logger = logging.getLogger("notification_system")

class NotificationLevel(Enum):
    """通知级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class NotificationType(Enum):
    """通知类型"""
    RESOURCE_WARNING = "resource_warning"
    RESOURCE_CRITICAL = "resource_critical"
    MODEL_STATUS = "model_status"
    SYSTEM_STATUS = "system_status"
    APPLICATION_ERROR = "application_error"
    PERFORMANCE = "performance"
    SECURITY = "security"

@dataclass
class Notification:
    """通知数据类"""
    id: str
    type: NotificationType
    level: NotificationLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        result['type'] = self.type.value
        result['level'] = self.level.value
        result['timestamp'] = self.timestamp.isoformat()
        result['acknowledged_at'] = self.acknowledged_at.isoformat() if self.acknowledged_at else None
        result['resolved_at'] = self.resolved_at.isoformat() if self.resolved_at else None
        return result

class NotificationRule:
    """通知规则"""
    def __init__(
        self,
        name: str,
        notification_type: NotificationType,
        level: NotificationLevel,
        condition_func: Callable[[Dict[str, Any]], bool],
        message_template: str,
        title_template: str,
        cooldown_minutes: int = 5,
        enabled: bool = True
    ):
        self.name = name
        self.notification_type = notification_type
        self.level = level
        self.condition_func = condition_func
        self.message_template = message_template
        self.title_template = title_template
        self.cooldown_minutes = cooldown_minutes
        self.enabled = enabled
        self.last_triggered: Optional[datetime] = None

    def should_trigger(self, data: Dict[str, Any]) -> bool:
        """检查是否应该触发通知"""
        if not self.enabled:
            return False
        
        # 检查冷却时间
        if self.last_triggered:
            time_since_last = datetime.now() - self.last_triggered
            if time_since_last < timedelta(minutes=self.cooldown_minutes):
                return False
        
        # 检查条件
        try:
            return self.condition_func(data)
        except Exception as e:
            logger.error(f"Error evaluating notification rule {self.name}: {e}")
            return False

    def create_notification(self, data: Dict[str, Any], source: str) -> Notification:
        """创建通知"""
        try:
            title = self.title_template.format(**data)
            message = self.message_template.format(**data)
        except KeyError as e:
            logger.warning(f"Missing template variable {e} in rule {self.name}")
            title = f"Notification: {self.name}"
            message = f"Data: {data}"
        
        self.last_triggered = datetime.now()
        
        return Notification(
            id=str(uuid.uuid4()),
            type=self.notification_type,
            level=self.level,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            data=data
        )

class NotificationChannel:
    """通知渠道基类"""
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
    
    async def send_notification(self, notification: Notification) -> bool:
        """发送通知"""
        raise NotImplementedError

class LogChannel(NotificationChannel):
    """日志通知渠道"""
    def __init__(self, name: str = "log", enabled: bool = True):
        super().__init__(name, enabled)
        self.logger = logging.getLogger(f"notifications.{name}")
    
    async def send_notification(self, notification: Notification) -> bool:
        """发送到日志"""
        if not self.enabled:
            return False
        
        try:
            log_level = {
                NotificationLevel.INFO: logging.INFO,
                NotificationLevel.WARNING: logging.WARNING,
                NotificationLevel.ERROR: logging.ERROR,
                NotificationLevel.CRITICAL: logging.CRITICAL
            }.get(notification.level, logging.INFO)
            
            self.logger.log(
                log_level,
                f"[{notification.type.value.upper()}] {notification.title}: {notification.message}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to log: {e}")
            return False

class WebhookChannel(NotificationChannel):
    """Webhook通知渠道"""
    def __init__(self, name: str, webhook_url: str, enabled: bool = True):
        super().__init__(name, enabled)
        self.webhook_url = webhook_url
    
    async def send_notification(self, notification: Notification) -> bool:
        """发送到Webhook"""
        if not self.enabled:
            return False
        
        try:
            import aiohttp
            
            payload = notification.to_dict()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.warning(f"Webhook returned status {response.status}")
                        return False
        except ImportError:
            logger.warning("aiohttp not available for webhook notifications")
            return False
        except Exception as e:
            logger.error(f"Failed to send notification to webhook: {e}")
            return False

class NotificationSystem:
    """
    通知系统
    
    负责管理通知的创建、发送、存储和查询。
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.notifications: deque[Notification] = deque(maxlen=max_history)
        self.rules: List[NotificationRule] = []
        self.channels: List[NotificationChannel] = []
        self.subscribers: Dict[NotificationType, List[Callable]] = defaultdict(list)
        
        # 统计信息
        self.stats = {
            "total_sent": 0,
            "by_type": defaultdict(int),
            "by_level": defaultdict(int),
            "failed_sends": 0
        }
        
        # 默认添加日志渠道
        self.add_channel(LogChannel())
        
        # 初始化默认规则
        self._setup_default_rules()
        
        logger.info("Notification system initialized")
    
    def _setup_default_rules(self):
        """设置默认通知规则"""
        # CPU使用率警告
        self.add_rule(NotificationRule(
            name="cpu_warning",
            notification_type=NotificationType.RESOURCE_WARNING,
            level=NotificationLevel.WARNING,
            condition_func=lambda data: data.get("cpu_percent", 0) > 80,
            title_template="CPU Usage Warning",
            message_template="CPU usage is high: {cpu_percent:.1f}%",
            cooldown_minutes=5
        ))
        
        # CPU使用率临界
        self.add_rule(NotificationRule(
            name="cpu_critical",
            notification_type=NotificationType.RESOURCE_CRITICAL,
            level=NotificationLevel.CRITICAL,
            condition_func=lambda data: data.get("cpu_percent", 0) > 95,
            title_template="CPU Usage Critical",
            message_template="CPU usage is critically high: {cpu_percent:.1f}%",
            cooldown_minutes=2
        ))
        
        # 内存使用率警告
        self.add_rule(NotificationRule(
            name="memory_warning",
            notification_type=NotificationType.RESOURCE_WARNING,
            level=NotificationLevel.WARNING,
            condition_func=lambda data: data.get("memory_percent", 0) > 80,
            title_template="Memory Usage Warning",
            message_template="Memory usage is high: {memory_percent:.1f}%",
            cooldown_minutes=5
        ))
        
        # 内存使用率临界
        self.add_rule(NotificationRule(
            name="memory_critical",
            notification_type=NotificationType.RESOURCE_CRITICAL,
            level=NotificationLevel.CRITICAL,
            condition_func=lambda data: data.get("memory_percent", 0) > 90,
            title_template="Memory Usage Critical",
            message_template="Memory usage is critically high: {memory_percent:.1f}%",
            cooldown_minutes=2
        ))
        
        # 磁盘使用率警告
        self.add_rule(NotificationRule(
            name="disk_warning",
            notification_type=NotificationType.RESOURCE_WARNING,
            level=NotificationLevel.WARNING,
            condition_func=lambda data: data.get("disk_percent", 0) > 85,
            title_template="Disk Usage Warning",
            message_template="Disk usage is high: {disk_percent:.1f}%",
            cooldown_minutes=10
        ))
        
        # 模型加载失败
        self.add_rule(NotificationRule(
            name="model_load_error",
            notification_type=NotificationType.MODEL_STATUS,
            level=NotificationLevel.ERROR,
            condition_func=lambda data: data.get("event") == "model_load_failed",
            title_template="Model Load Failed",
            message_template="Failed to load model {model_name}: {error_message}",
            cooldown_minutes=1
        ))
        
        # 模型加载成功
        self.add_rule(NotificationRule(
            name="model_load_success",
            notification_type=NotificationType.MODEL_STATUS,
            level=NotificationLevel.INFO,
            condition_func=lambda data: data.get("event") == "model_loaded",
            title_template="Model Loaded Successfully",
            message_template="Model {model_name} loaded on {device}",
            cooldown_minutes=1
        ))
    
    def add_rule(self, rule: NotificationRule):
        """添加通知规则"""
        self.rules.append(rule)
        logger.info(f"Added notification rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除通知规则"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.info(f"Removed notification rule: {rule_name}")
                return True
        return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """启用通知规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.info(f"Enabled notification rule: {rule_name}")
                return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """禁用通知规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.info(f"Disabled notification rule: {rule_name}")
                return True
        return False
    
    def add_channel(self, channel: NotificationChannel):
        """添加通知渠道"""
        self.channels.append(channel)
        logger.info(f"Added notification channel: {channel.name}")
    
    def remove_channel(self, channel_name: str) -> bool:
        """移除通知渠道"""
        for i, channel in enumerate(self.channels):
            if channel.name == channel_name:
                del self.channels[i]
                logger.info(f"Removed notification channel: {channel_name}")
                return True
        return False
    
    def subscribe(self, notification_type: NotificationType, callback: Callable[[Notification], None]):
        """订阅特定类型的通知"""
        self.subscribers[notification_type].append(callback)
    
    async def check_and_notify(self, data: Dict[str, Any], source: str = "system"):
        """检查数据并触发相应的通知"""
        for rule in self.rules:
            if rule.should_trigger(data):
                notification = rule.create_notification(data, source)
                await self.send_notification(notification)
    
    async def send_notification(self, notification: Notification):
        """发送通知"""
        try:
            # 添加到历史记录
            self.notifications.append(notification)
            
            # 更新统计
            self.stats["total_sent"] += 1
            self.stats["by_type"][notification.type.value] += 1
            self.stats["by_level"][notification.level.value] += 1
            
            # 发送到所有渠道
            send_tasks = []
            for channel in self.channels:
                if channel.enabled:
                    send_tasks.append(channel.send_notification(notification))
            
            if send_tasks:
                results = await asyncio.gather(*send_tasks, return_exceptions=True)
                failed_count = sum(1 for result in results if isinstance(result, Exception) or not result)
                self.stats["failed_sends"] += failed_count
            
            # 通知订阅者
            for callback in self.subscribers[notification.type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(notification)
                    else:
                        callback(notification)
                except Exception as e:
                    logger.error(f"Error in notification callback: {e}")
            
            logger.debug(f"Sent notification: {notification.title}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            self.stats["failed_sends"] += 1
    
    async def create_notification(
        self,
        type: NotificationType,
        level: NotificationLevel,
        title: str,
        message: str,
        source: str = "manual",
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """手动创建并发送通知"""
        notification = Notification(
            id=str(uuid.uuid4()),
            type=type,
            level=level,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            data=data or {}
        )
        
        await self.send_notification(notification)
        return notification
    
    def get_notifications(
        self,
        limit: Optional[int] = None,
        notification_type: Optional[NotificationType] = None,
        level: Optional[NotificationLevel] = None,
        since: Optional[datetime] = None,
        acknowledged: Optional[bool] = None
    ) -> List[Notification]:
        """获取通知列表"""
        notifications = list(self.notifications)
        
        # 按时间排序（最新的在前）
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        
        # 过滤条件
        if notification_type:
            notifications = [n for n in notifications if n.type == notification_type]
        
        if level:
            notifications = [n for n in notifications if n.level == level]
        
        if since:
            notifications = [n for n in notifications if n.timestamp >= since]
        
        if acknowledged is not None:
            notifications = [n for n in notifications if n.acknowledged == acknowledged]
        
        # 限制数量
        if limit:
            notifications = notifications[:limit]
        
        return notifications
    
    def acknowledge_notification(self, notification_id: str, user: str = "system") -> bool:
        """确认通知"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.acknowledged = True
                notification.acknowledged_at = datetime.now()
                notification.acknowledged_by = user
                logger.info(f"Notification {notification_id} acknowledged by {user}")
                return True
        return False
    
    def resolve_notification(self, notification_id: str) -> bool:
        """解决通知"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.resolved = True
                notification.resolved_at = datetime.now()
                logger.info(f"Notification {notification_id} resolved")
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取通知统计信息"""
        unacknowledged_count = sum(1 for n in self.notifications if not n.acknowledged)
        unresolved_count = sum(1 for n in self.notifications if not n.resolved)
        
        return {
            "total_notifications": len(self.notifications),
            "unacknowledged_count": unacknowledged_count,
            "unresolved_count": unresolved_count,
            "stats": dict(self.stats),
            "rules_count": len(self.rules),
            "active_rules_count": sum(1 for r in self.rules if r.enabled),
            "channels_count": len(self.channels),
            "active_channels_count": sum(1 for c in self.channels if c.enabled)
        }
    
    def get_rule_status(self) -> List[Dict[str, Any]]:
        """获取规则状态"""
        return [
            {
                "name": rule.name,
                "type": rule.notification_type.value,
                "level": rule.level.value,
                "enabled": rule.enabled,
                "cooldown_minutes": rule.cooldown_minutes,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
            }
            for rule in self.rules
        ]
    
    def clear_notifications(self, before: Optional[datetime] = None):
        """清除通知"""
        if before:
            # 清除指定时间之前的通知
            self.notifications = deque(
                (n for n in self.notifications if n.timestamp >= before),
                maxlen=self.max_history
            )
        else:
            # 清除所有通知
            self.notifications.clear()
        
        logger.info(f"Cleared notifications{' before ' + before.isoformat() if before else ''}")

# 全局通知系统实例
notification_system = NotificationSystem() 