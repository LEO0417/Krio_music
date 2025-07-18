import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { Progress } from './ui/Progress';
import { usePerformanceMonitor } from '@/hooks/usePerformance';
import { FadeIn } from './animations';

interface PerformanceData {
  cpu: number;
  memory: number;
  disk: number;
  gpu?: number;
  inferenceTime: number;
  cacheHitRate: number;
  timestamp: string;
}

interface PerformanceMonitorProps {
  className?: string;
  onOptimizationToggle?: (enabled: boolean) => void;
}

const MonitorContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const MetricCard = styled(Card)<{ alertLevel?: 'normal' | 'warning' | 'critical' }>`
  ${props => props.alertLevel === 'warning' && `
    border-left: 4px solid var(--color-warning);
    background: rgba(255, 193, 7, 0.05);
  `}
  
  ${props => props.alertLevel === 'critical' && `
    border-left: 4px solid var(--color-danger);
    background: rgba(220, 53, 69, 0.05);
  `}
`;

const MetricHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
`;

const MetricTitle = styled.h3`
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const MetricValue = styled.div`
  font-size: 24px;
  font-weight: 700;
  color: var(--color-primary);
`;

const MetricIcon = styled.div`
  font-size: 24px;
  color: var(--color-text-secondary);
`;

const ProgressContainer = styled.div`
  margin-top: var(--spacing-sm);
`;

const ProgressLabel = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
  font-size: 14px;
  color: var(--color-text-secondary);
`;

const ControlsContainer = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-background-secondary);
  border-radius: var(--radius-md);
`;

const StatusIndicator = styled.div<{ status: 'good' | 'warning' | 'critical' }>`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'good': return 'var(--color-success)';
      case 'warning': return 'var(--color-warning)';
      case 'critical': return 'var(--color-danger)';
      default: return 'var(--color-text-tertiary)';
    }
  }};
  flex-shrink: 0;
`;

const RecommendationsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
`;

const RecommendationItem = styled.div<{ priority: 'high' | 'medium' | 'low' }>`
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  border-left: 4px solid ${props => {
    switch (props.priority) {
      case 'high': return 'var(--color-danger)';
      case 'medium': return 'var(--color-warning)';
      case 'low': return 'var(--color-info)';
      default: return 'var(--color-border)';
    }
  }};
  background: var(--color-background-secondary);
  font-size: 14px;
  color: var(--color-text-secondary);
`;

const ChartsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  margin-top: var(--spacing-lg);
`;

const ChartCard = styled(Card)`
  min-height: 200px;
  display: flex;
  flex-direction: column;
`;

const ChartTitle = styled.h4`
  margin: 0 0 var(--spacing-md) 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const ChartPlaceholder = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  font-size: 14px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
`;

const RecommendationDetails = styled.div`
  margin-top: 4px;
  font-size: 12px;
  opacity: 0.8;
`;

export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  className,
  onOptimizationToggle,
}) => {
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [optimizationEnabled, setOptimizationEnabled] = useState(true);
  
  const { trackOperation } = usePerformanceMonitor('PerformanceMonitor');
  
  // 模拟性能数据获取
  const fetchPerformanceData = useCallback(async () => {
    try {
      // 在实际应用中，这里会调用API获取真实数据
      const mockData: PerformanceData = {
        cpu: Math.random() * 100,
        memory: Math.random() * 100,
        disk: Math.random() * 100,
        gpu: Math.random() * 100,
        inferenceTime: Math.random() * 5000,
        cacheHitRate: Math.random() * 100,
        timestamp: new Date().toISOString(),
      };
      
      setPerformanceData(mockData);
      
      // 生成推荐
      const newRecommendations = [];
      if (mockData.cpu > 80) {
        newRecommendations.push({
          type: 'cpu',
          priority: 'high',
          message: 'CPU usage is high. Consider optimizing expensive operations.',
          suggestion: 'Enable performance optimization or reduce concurrent operations.',
        });
      }
      
      if (mockData.memory > 85) {
        newRecommendations.push({
          type: 'memory',
          priority: 'high',
          message: 'Memory usage is critical. Risk of performance degradation.',
          suggestion: 'Clear caches, reduce batch size, or restart the application.',
        });
      }
      
      if (mockData.inferenceTime > 3000) {
        newRecommendations.push({
          type: 'inference',
          priority: 'medium',
          message: 'Model inference time is slow.',
          suggestion: 'Enable model optimization or use a faster model variant.',
        });
      }
      
      setRecommendations(newRecommendations);
      
    } catch (error) {
      console.error('Error fetching performance data:', error);
    }
  }, []);
  
  // 定期更新性能数据
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isMonitoring) {
      fetchPerformanceData();
      interval = setInterval(fetchPerformanceData, 2000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isMonitoring, fetchPerformanceData]);
  
  const getAlertLevel = (value: number, type: 'cpu' | 'memory' | 'disk' | 'gpu') => {
    const thresholds = {
      cpu: { warning: 70, critical: 85 },
      memory: { warning: 75, critical: 90 },
      disk: { warning: 80, critical: 95 },
      gpu: { warning: 70, critical: 85 },
    };
    
    const threshold = thresholds[type];
    if (value >= threshold.critical) return 'critical';
    if (value >= threshold.warning) return 'warning';
    return 'normal';
  };
  
  const getStatusColor = (value: number, type: 'cpu' | 'memory' | 'disk' | 'gpu') => {
    const level = getAlertLevel(value, type);
    switch (level) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      default: return 'primary';
    }
  };
  
  const getOverallStatus = () => {
    if (!performanceData) return 'good';
    
    const metrics = [
      { value: performanceData.cpu, type: 'cpu' as const },
      { value: performanceData.memory, type: 'memory' as const },
      { value: performanceData.disk, type: 'disk' as const },
    ];
    
    const hasCritical = metrics.some(m => getAlertLevel(m.value, m.type) === 'critical');
    const hasWarning = metrics.some(m => getAlertLevel(m.value, m.type) === 'warning');
    
    if (hasCritical) return 'critical';
    if (hasWarning) return 'warning';
    return 'good';
  };
  
  const handleOptimizationToggle = () => {
    const newState = !optimizationEnabled;
    setOptimizationEnabled(newState);
    onOptimizationToggle?.(newState);
  };
  
  const handleClearCache = () => {
    trackOperation('clearCache', () => {
      // 清除缓存的逻辑
      console.log('Cache cleared');
    });
  };
  
  const handleGarbageCollection = () => {
    trackOperation('garbageCollection', () => {
      // 触发垃圾回收的逻辑
      console.log('Garbage collection triggered');
    });
  };
  
  return (
    <MonitorContainer className={className}>
      <FadeIn direction="up">
        <Card>
          <ControlsContainer>
            <StatusIndicator status={getOverallStatus()} />
            <span>System Status: {getOverallStatus().charAt(0).toUpperCase() + getOverallStatus().slice(1)}</span>
            
            <Button
              variant={isMonitoring ? 'primary' : 'secondary'}
              size="small"
              onClick={() => setIsMonitoring(!isMonitoring)}
            >
              {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
            </Button>
            
            <Button
              variant={optimizationEnabled ? 'primary' : 'outline'}
              size="small"
              onClick={handleOptimizationToggle}
            >
              {optimizationEnabled ? 'Optimization On' : 'Optimization Off'}
            </Button>
            
            <Button
              variant="secondary"
              size="small"
              onClick={handleClearCache}
            >
              Clear Cache
            </Button>
            
            <Button
              variant="secondary"
              size="small"
              onClick={handleGarbageCollection}
            >
              GC
            </Button>
          </ControlsContainer>
        </Card>
      </FadeIn>
      
      {performanceData && (
        <FadeIn direction="up" delay={100}>
          <MetricsGrid>
            <MetricCard alertLevel={getAlertLevel(performanceData.cpu, 'cpu')}>
              <MetricHeader>
                <MetricTitle>CPU Usage</MetricTitle>
                <MetricIcon>💻</MetricIcon>
              </MetricHeader>
              <MetricValue>{performanceData.cpu.toFixed(1)}%</MetricValue>
              <ProgressContainer>
                <Progress
                  value={performanceData.cpu}
                  max={100}
                  variant={getStatusColor(performanceData.cpu, 'cpu')}
                />
              </ProgressContainer>
            </MetricCard>
            
            <MetricCard alertLevel={getAlertLevel(performanceData.memory, 'memory')}>
              <MetricHeader>
                <MetricTitle>Memory Usage</MetricTitle>
                <MetricIcon>🧠</MetricIcon>
              </MetricHeader>
              <MetricValue>{performanceData.memory.toFixed(1)}%</MetricValue>
              <ProgressContainer>
                <Progress
                  value={performanceData.memory}
                  max={100}
                  variant={getStatusColor(performanceData.memory, 'memory')}
                />
              </ProgressContainer>
            </MetricCard>
            
            <MetricCard alertLevel={getAlertLevel(performanceData.disk, 'disk')}>
              <MetricHeader>
                <MetricTitle>Disk Usage</MetricTitle>
                <MetricIcon>💽</MetricIcon>
              </MetricHeader>
              <MetricValue>{performanceData.disk.toFixed(1)}%</MetricValue>
              <ProgressContainer>
                <Progress
                  value={performanceData.disk}
                  max={100}
                  variant={getStatusColor(performanceData.disk, 'disk')}
                />
              </ProgressContainer>
            </MetricCard>
            
            {performanceData.gpu && (
              <MetricCard alertLevel={getAlertLevel(performanceData.gpu, 'gpu')}>
                <MetricHeader>
                  <MetricTitle>GPU Usage</MetricTitle>
                  <MetricIcon>🎮</MetricIcon>
                </MetricHeader>
                <MetricValue>{performanceData.gpu.toFixed(1)}%</MetricValue>
                <ProgressContainer>
                  <Progress
                    value={performanceData.gpu}
                    max={100}
                    variant={getStatusColor(performanceData.gpu, 'gpu')}
                  />
                </ProgressContainer>
              </MetricCard>
            )}
            
            <MetricCard>
              <MetricHeader>
                <MetricTitle>Inference Time</MetricTitle>
                <MetricIcon>⏱️</MetricIcon>
              </MetricHeader>
              <MetricValue>{performanceData.inferenceTime.toFixed(0)}ms</MetricValue>
              <ProgressLabel>
                <span>Performance</span>
                <span>{performanceData.inferenceTime < 1000 ? 'Good' : 'Slow'}</span>
              </ProgressLabel>
            </MetricCard>
            
            <MetricCard>
              <MetricHeader>
                <MetricTitle>Cache Hit Rate</MetricTitle>
                <MetricIcon>🎯</MetricIcon>
              </MetricHeader>
              <MetricValue>{performanceData.cacheHitRate.toFixed(1)}%</MetricValue>
              <ProgressContainer>
                <Progress
                  value={performanceData.cacheHitRate}
                  max={100}
                  variant={performanceData.cacheHitRate > 70 ? 'success' : 'warning'}
                />
              </ProgressContainer>
            </MetricCard>
          </MetricsGrid>
        </FadeIn>
      )}
      
      {recommendations.length > 0 && (
        <FadeIn direction="up" delay={200}>
          <Card>
            <MetricTitle>Performance Recommendations</MetricTitle>
            <RecommendationsList>
              {recommendations.map((rec, index) => (
                <RecommendationItem key={index} priority={rec.priority}>
                  <strong>{rec.message}</strong>
                  <RecommendationDetails>
                    {rec.suggestion}
                  </RecommendationDetails>
                </RecommendationItem>
              ))}
            </RecommendationsList>
          </Card>
        </FadeIn>
      )}
      
      <ChartsContainer>
        <ChartCard>
          <ChartTitle>Resource Usage Over Time</ChartTitle>
          <ChartPlaceholder>
            📊 Performance charts would be displayed here
          </ChartPlaceholder>
        </ChartCard>
        
        <ChartCard>
          <ChartTitle>Inference Performance</ChartTitle>
          <ChartPlaceholder>
            📈 Inference time trends would be displayed here
          </ChartPlaceholder>
        </ChartCard>
      </ChartsContainer>
    </MonitorContainer>
  );
};