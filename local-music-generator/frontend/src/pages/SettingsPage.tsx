import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useAppState } from '@/context/AppStateContext';
import { useTheme } from '@/context/ThemeContext';
import { useApi } from '@/hooks/useApiActions';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Slider } from '@/components/ui/Slider';

const PageContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: var(--spacing-lg);
`;

const PageTitle = styled.h1`
  margin: 0 0 var(--spacing-lg) 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
`;

const SettingsSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
`;

const SectionTitle = styled.h2`
  margin: 0 0 var(--spacing-md) 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const SettingItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--color-border);
  
  &:last-child {
    border-bottom: none;
  }
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-md);
  }
`;

const SettingLabel = styled.div`
  flex: 1;
  margin-right: var(--spacing-md);
  
  @media (max-width: 768px) {
    margin-right: 0;
  }
`;

const SettingTitle = styled.h3`
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const SettingDescription = styled.p`
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.4;
`;

const SettingControl = styled.div`
  flex-shrink: 0;
  min-width: 200px;
  
  @media (max-width: 768px) {
    min-width: 0;
  }
`;

const ThemeSelector = styled.div`
  display: flex;
  gap: var(--spacing-sm);
`;

const ThemeOption = styled.button<{ active: boolean }>`
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid ${props => props.active ? 'var(--color-primary)' : 'var(--color-border)'};
  background: ${props => props.active ? 'var(--color-primary)' : 'var(--color-background-secondary)'};
  color: ${props => props.active ? 'white' : 'var(--color-text-primary)'};
  border-radius: var(--radius-md);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--transition-normal);
  
  &:hover {
    border-color: var(--color-primary);
  }
`;

const SystemInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
`;

const InfoItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  font-size: 14px;
`;

const InfoLabel = styled.span`
  color: var(--color-text-secondary);
  font-weight: 500;
`;

const InfoValue = styled.span`
  color: var(--color-text-primary);
  font-family: var(--font-family-mono);
`;

const StatusIndicator = styled.div<{ status: 'good' | 'warning' | 'error' }>`
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
  
  background: ${props => {
    switch (props.status) {
      case 'good':
        return 'var(--color-success)';
      case 'warning':
        return 'var(--color-warning)';
      case 'error':
        return 'var(--color-danger)';
      default:
        return 'var(--color-text-tertiary)';
    }
  }};
  
  color: white;
`;

const StatusDot = styled.div`
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
`;

const ModelManagement = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
`;

const ModelActions = styled.div`
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
`;

const SettingsPage: React.FC = () => {
  const { state, dispatch } = useAppState();
  const { theme, setTheme, actualTheme } = useTheme();
  const { getSystemStatus, loadModel, unloadModel, clearCache } = useApi();
  
  const [isLoading, setIsLoading] = useState(false);
  const [systemInfo, setSystemInfo] = useState<any>(null);

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const info = await getSystemStatus();
      setSystemInfo(info);
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: 'Failed to load system information',
        },
      });
    }
  };

  const handleLoadModel = async () => {
    setIsLoading(true);
    try {
      await loadModel();
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'success',
          title: 'Success',
          message: 'Model loaded successfully',
        },
      });
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: error instanceof Error ? error.message : 'Failed to load model',
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnloadModel = async () => {
    setIsLoading(true);
    try {
      await unloadModel();
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'success',
          title: 'Success',
          message: 'Model unloaded successfully',
        },
      });
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: error instanceof Error ? error.message : 'Failed to unload model',
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearCache = async () => {
    setIsLoading(true);
    try {
      await clearCache();
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'success',
          title: 'Success',
          message: 'Cache cleared successfully',
        },
      });
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: error instanceof Error ? error.message : 'Failed to clear cache',
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getSystemHealthStatus = () => {
    if (!systemInfo) return 'good';
    
    const { cpu, memory, gpu } = systemInfo;
    if (cpu > 90 || memory > 90 || (gpu && gpu > 90)) {
      return 'error';
    }
    if (cpu > 70 || memory > 70 || (gpu && gpu > 70)) {
      return 'warning';
    }
    return 'good';
  };

  const getModelStatus = () => {
    switch (state.modelStatus?.status) {
      case 'loaded':
        return 'good';
      case 'loading':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'warning';
    }
  };

  return (
    <PageContainer>
      <PageTitle>Settings</PageTitle>
      
      <SettingsSection>
        <Card>
          <SectionTitle>Appearance</SectionTitle>
          
          <SettingItem>
            <SettingLabel>
              <SettingTitle>Theme</SettingTitle>
              <SettingDescription>
                Choose your preferred color theme
              </SettingDescription>
            </SettingLabel>
            
            <SettingControl>
              <ThemeSelector>
                <ThemeOption
                  active={theme === 'light'}
                  onClick={() => setTheme('light')}
                >
                  ☀️ Light
                </ThemeOption>
                <ThemeOption
                  active={theme === 'dark'}
                  onClick={() => setTheme('dark')}
                >
                  🌙 Dark
                </ThemeOption>
                <ThemeOption
                  active={theme === 'system'}
                  onClick={() => setTheme('system')}
                >
                  🖥️ System
                </ThemeOption>
              </ThemeSelector>
            </SettingControl>
          </SettingItem>
        </Card>
        
        <Card>
          <SectionTitle>Model Management</SectionTitle>
          
          <ModelManagement>
            <SettingItem>
              <SettingLabel>
                <SettingTitle>Model Status</SettingTitle>
                <SettingDescription>
                  Current status of the MusicGen model
                </SettingDescription>
              </SettingLabel>
              
              <SettingControl>
                <StatusIndicator status={getModelStatus()}>
                  <StatusDot />
                  {state.modelStatus?.status || 'Unknown'}
                </StatusIndicator>
              </SettingControl>
            </SettingItem>
            
            <ModelActions>
              <Button
                variant="primary"
                onClick={handleLoadModel}
                disabled={isLoading || state.modelStatus?.status === 'loaded'}
                loading={isLoading && state.modelStatus?.status === 'loading'}
              >
                Load Model
              </Button>
              
              <Button
                variant="secondary"
                onClick={handleUnloadModel}
                disabled={isLoading || state.modelStatus?.status !== 'loaded'}
                loading={isLoading}
              >
                Unload Model
              </Button>
              
              <Button
                variant="outline"
                onClick={handleClearCache}
                disabled={isLoading}
                loading={isLoading}
              >
                Clear Cache
              </Button>
            </ModelActions>
          </ModelManagement>
        </Card>
        
        <Card>
          <SectionTitle>System Information</SectionTitle>
          
          <SystemInfo>
            <SettingItem>
              <SettingLabel>
                <SettingTitle>System Status</SettingTitle>
                <SettingDescription>
                  Overall system health and resource usage
                </SettingDescription>
              </SettingLabel>
              
              <SettingControl>
                <StatusIndicator status={getSystemHealthStatus()}>
                  <StatusDot />
                  {getSystemHealthStatus() === 'good' ? 'Healthy' : 
                   getSystemHealthStatus() === 'warning' ? 'Warning' : 'Critical'}
                </StatusIndicator>
              </SettingControl>
            </SettingItem>
            
            {systemInfo && (
              <>
                <InfoItem>
                  <InfoLabel>CPU Usage</InfoLabel>
                  <InfoValue>{systemInfo.cpu?.toFixed(1)}%</InfoValue>
                </InfoItem>
                
                <InfoItem>
                  <InfoLabel>Memory Usage</InfoLabel>
                  <InfoValue>{systemInfo.memory?.toFixed(1)}%</InfoValue>
                </InfoItem>
                
                {systemInfo.gpu && (
                  <InfoItem>
                    <InfoLabel>GPU Usage</InfoLabel>
                    <InfoValue>{systemInfo.gpu.toFixed(1)}%</InfoValue>
                  </InfoItem>
                )}
                
                <InfoItem>
                  <InfoLabel>Disk Space</InfoLabel>
                  <InfoValue>{systemInfo.disk_usage || 'N/A'}</InfoValue>
                </InfoItem>
                
                <InfoItem>
                  <InfoLabel>Model Cache Size</InfoLabel>
                  <InfoValue>{systemInfo.cache_size || 'N/A'}</InfoValue>
                </InfoItem>
              </>
            )}
          </SystemInfo>
        </Card>
      </SettingsSection>
    </PageContainer>
  );
};

export default SettingsPage;