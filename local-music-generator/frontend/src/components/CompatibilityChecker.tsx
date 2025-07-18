import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { Progress } from './ui/Progress';
import { FadeIn } from './animations';
import { 
  detectBrowser, 
  detectDeviceCapabilities, 
  checkAccessibilitySupport,
  PerformanceTest,
  generateCompatibilityReport
} from '@/utils/compatibility';

interface CompatibilityCheckProps {
  className?: string;
  onReportGenerated?: (report: any) => void;
}

interface TestResult {
  name: string;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'warning';
  message: string;
  details?: any;
  recommendation?: string;
}

const CheckerContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
`;

const TestGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const TestCard = styled(Card)<{ status: 'pending' | 'running' | 'passed' | 'failed' | 'warning' }>`
  ${props => {
    switch (props.status) {
      case 'running':
        return `
          border-left: 4px solid var(--color-info);
          background: rgba(0, 123, 255, 0.05);
        `;
      case 'passed':
        return `
          border-left: 4px solid var(--color-success);
          background: rgba(40, 167, 69, 0.05);
        `;
      case 'failed':
        return `
          border-left: 4px solid var(--color-danger);
          background: rgba(220, 53, 69, 0.05);
        `;
      case 'warning':
        return `
          border-left: 4px solid var(--color-warning);
          background: rgba(255, 193, 7, 0.05);
        `;
      default:
        return '';
    }
  }}
`;

const TestHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
`;

const TestTitle = styled.h3`
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const TestStatus = styled.div<{ status: 'pending' | 'running' | 'passed' | 'failed' | 'warning' }>`
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 14px;
  font-weight: 500;
  color: ${props => {
    switch (props.status) {
      case 'running': return 'var(--color-info)';
      case 'passed': return 'var(--color-success)';
      case 'failed': return 'var(--color-danger)';
      case 'warning': return 'var(--color-warning)';
      default: return 'var(--color-text-secondary)';
    }
  }};
`;

const TestMessage = styled.div`
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
`;

const TestDetails = styled.div`
  font-size: 12px;
  color: var(--color-text-tertiary);
  background: var(--color-background-secondary);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-sm);
`;

const TestRecommendation = styled.div`
  font-size: 12px;
  color: var(--color-text-secondary);
  font-style: italic;
  border-left: 2px solid var(--color-warning);
  padding-left: var(--spacing-sm);
`;

const OverallStatus = styled.div<{ status: 'excellent' | 'good' | 'fair' | 'poor' }>`
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  font-weight: 600;
  background: ${props => {
    switch (props.status) {
      case 'excellent': return 'rgba(40, 167, 69, 0.1)';
      case 'good': return 'rgba(40, 167, 69, 0.1)';
      case 'fair': return 'rgba(255, 193, 7, 0.1)';
      case 'poor': return 'rgba(220, 53, 69, 0.1)';
      default: return 'var(--color-background-secondary)';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'excellent': return 'var(--color-success)';
      case 'good': return 'var(--color-success)';
      case 'fair': return 'var(--color-warning)';
      case 'poor': return 'var(--color-danger)';
      default: return 'var(--color-text-primary)';
    }
  }};
`;

const ControlsContainer = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  justify-content: center;
  padding: var(--spacing-md);
  background: var(--color-background-secondary);
  border-radius: var(--radius-md);
`;

const ProgressContainer = styled.div`
  margin-top: var(--spacing-md);
`;

const SystemInfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
`;

const InfoItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs);
  background: var(--color-background-secondary);
  border-radius: var(--radius-sm);
  font-size: 14px;
`;

const InfoLabel = styled.span`
  color: var(--color-text-secondary);
`;

const InfoValue = styled.span`
  color: var(--color-text-primary);
  font-weight: 500;
`;

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'running': return '🔄';
    case 'passed': return '✅';
    case 'failed': return '❌';
    case 'warning': return '⚠️';
    default: return '⏳';
  }
};

export const CompatibilityChecker: React.FC<CompatibilityCheckProps> = ({
  className,
  onReportGenerated,
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [overallStatus, setOverallStatus] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good');
  const [fullReport, setFullReport] = useState<any>(null);

  const initialTests: TestResult[] = [
    {
      name: 'Browser Compatibility',
      status: 'pending',
      message: 'Checking browser support and version...',
    },
    {
      name: 'Device Capabilities',
      status: 'pending',
      message: 'Analyzing device hardware and features...',
    },
    {
      name: 'Audio Support',
      status: 'pending',
      message: 'Testing audio format support...',
    },
    {
      name: 'Performance Baseline',
      status: 'pending',
      message: 'Running performance tests...',
    },
    {
      name: 'Accessibility Features',
      status: 'pending',
      message: 'Checking accessibility support...',
    },
    {
      name: 'Network Capabilities',
      status: 'pending',
      message: 'Testing network speed and reliability...',
    },
    {
      name: 'Storage Support',
      status: 'pending',
      message: 'Checking local storage capabilities...',
    },
    {
      name: 'CSS Features',
      status: 'pending',
      message: 'Testing CSS feature support...',
    },
  ];

  useEffect(() => {
    setTestResults(initialTests);
  }, []);

  const runCompatibilityTests = async () => {
    setIsRunning(true);
    setProgress(0);
    setTestResults(initialTests);

    try {
      const browserInfo = detectBrowser();
      const deviceInfo = detectDeviceCapabilities();
      const accessibilityInfo = checkAccessibilitySupport();
      const performanceTest = new PerformanceTest();

      // Test 1: Browser Compatibility
      await updateTestResult(0, 'running', 'Checking browser compatibility...');
      await delay(500);
      
      const browserResult = analyzeBrowserCompatibility(browserInfo);
      await updateTestResult(0, browserResult.status, browserResult.message, browserInfo, browserResult.recommendation);
      setProgress(12.5);

      // Test 2: Device Capabilities
      await updateTestResult(1, 'running', 'Analyzing device capabilities...');
      await delay(500);
      
      const deviceResult = analyzeDeviceCapabilities(deviceInfo);
      await updateTestResult(1, deviceResult.status, deviceResult.message, deviceInfo, deviceResult.recommendation);
      setProgress(25);

      // Test 3: Audio Support
      await updateTestResult(2, 'running', 'Testing audio format support...');
      await delay(500);
      
      const audioResult = testAudioSupport(browserInfo.features.audio);
      await updateTestResult(2, audioResult.status, audioResult.message, browserInfo.features.audio, audioResult.recommendation);
      setProgress(37.5);

      // Test 4: Performance Baseline
      await updateTestResult(3, 'running', 'Running performance tests...');
      await delay(500);
      
      const perfResults = await performanceTest.runAllTests();
      const perfResult = analyzePerformance(perfResults);
      await updateTestResult(3, perfResult.status, perfResult.message, perfResults, perfResult.recommendation);
      setProgress(50);

      // Test 5: Accessibility Features
      await updateTestResult(4, 'running', 'Checking accessibility support...');
      await delay(500);
      
      const a11yResult = analyzeAccessibility(accessibilityInfo);
      await updateTestResult(4, a11yResult.status, a11yResult.message, accessibilityInfo, a11yResult.recommendation);
      setProgress(62.5);

      // Test 6: Network Capabilities
      await updateTestResult(5, 'running', 'Testing network capabilities...');
      await delay(500);
      
      const networkResult = await testNetworkCapabilities();
      await updateTestResult(5, networkResult.status, networkResult.message, networkResult.details, networkResult.recommendation);
      setProgress(75);

      // Test 7: Storage Support
      await updateTestResult(6, 'running', 'Checking storage support...');
      await delay(500);
      
      const storageResult = testStorageSupport();
      await updateTestResult(6, storageResult.status, storageResult.message, storageResult.details, storageResult.recommendation);
      setProgress(87.5);

      // Test 8: CSS Features
      await updateTestResult(7, 'running', 'Testing CSS features...');
      await delay(500);
      
      const cssResult = testCSSFeatures(browserInfo.features.css);
      await updateTestResult(7, cssResult.status, cssResult.message, browserInfo.features.css, cssResult.recommendation);
      setProgress(100);

      // Generate full report
      const report = await generateCompatibilityReport();
      setFullReport(report);
      setSystemInfo({
        browser: browserInfo,
        device: deviceInfo,
        accessibility: accessibilityInfo,
        performance: perfResults,
      });

      // Calculate overall status
      const overallResult = calculateOverallStatus(testResults);
      setOverallStatus(overallResult);

      onReportGenerated?.(report);

    } catch (error) {
      console.error('Compatibility test failed:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const updateTestResult = async (
    index: number,
    status: TestResult['status'],
    message: string,
    details?: any,
    recommendation?: string
  ) => {
    setTestResults(prev => {
      const newResults = [...prev];
      newResults[index] = {
        ...newResults[index],
        status,
        message,
        details,
        recommendation,
      };
      return newResults;
    });
  };

  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const analyzeBrowserCompatibility = (browserInfo: any) => {
    if (!browserInfo.isSupported) {
      return {
        status: 'failed' as const,
        message: `Browser ${browserInfo.name} ${browserInfo.version} is not supported`,
        recommendation: 'Please upgrade to a supported browser version',
      };
    }

    if (browserInfo.name === 'Chrome' && parseInt(browserInfo.version) >= 90) {
      return {
        status: 'passed' as const,
        message: `Browser ${browserInfo.name} ${browserInfo.version} is fully supported`,
      };
    }

    return {
      status: 'warning' as const,
      message: `Browser ${browserInfo.name} ${browserInfo.version} has limited support`,
      recommendation: 'Consider updating to the latest version for best experience',
    };
  };

  const analyzeDeviceCapabilities = (deviceInfo: any) => {
    const score = calculateDeviceScore(deviceInfo);
    
    if (score >= 80) {
      return {
        status: 'passed' as const,
        message: 'Device has excellent capabilities for this application',
      };
    } else if (score >= 60) {
      return {
        status: 'warning' as const,
        message: 'Device has adequate capabilities with some limitations',
        recommendation: 'Some features may have reduced performance',
      };
    } else {
      return {
        status: 'failed' as const,
        message: 'Device capabilities are below minimum requirements',
        recommendation: 'Consider using a more powerful device',
      };
    }
  };

  const testAudioSupport = (audioSupport: any) => {
    const supportedFormats = Object.entries(audioSupport)
      .filter(([_, supported]) => supported)
      .map(([format, _]) => format);

    if (supportedFormats.includes('mp3') && supportedFormats.includes('wav')) {
      return {
        status: 'passed' as const,
        message: `Audio formats supported: ${supportedFormats.join(', ')}`,
      };
    } else if (supportedFormats.length > 0) {
      return {
        status: 'warning' as const,
        message: `Limited audio format support: ${supportedFormats.join(', ')}`,
        recommendation: 'Some audio features may not work properly',
      };
    } else {
      return {
        status: 'failed' as const,
        message: 'No supported audio formats detected',
        recommendation: 'Audio playback will not work',
      };
    }
  };

  const analyzePerformance = (perfResults: any) => {
    const renderTime = perfResults.renderPerformance || 0;
    const jsTime = perfResults.jsPerformance || 0;
    const memoryUsage = perfResults.memoryUsage || 0;

    if (renderTime < 100 && jsTime < 50 && memoryUsage < 0.8) {
      return {
        status: 'passed' as const,
        message: 'Performance is excellent for this application',
      };
    } else if (renderTime < 200 && jsTime < 100 && memoryUsage < 0.9) {
      return {
        status: 'warning' as const,
        message: 'Performance is adequate but may have some slowdowns',
        recommendation: 'Consider closing other applications for better performance',
      };
    } else {
      return {
        status: 'failed' as const,
        message: 'Performance is below acceptable levels',
        recommendation: 'Application may be very slow or unresponsive',
      };
    }
  };

  const analyzeAccessibility = (a11yInfo: any) => {
    const features = Object.values(a11yInfo.screenReader).filter(Boolean).length +
                    Object.values(a11yInfo.keyboard).filter(Boolean).length;

    if (features >= 3) {
      return {
        status: 'passed' as const,
        message: 'Good accessibility support detected',
      };
    } else if (features >= 2) {
      return {
        status: 'warning' as const,
        message: 'Basic accessibility support available',
        recommendation: 'Some accessibility features may be limited',
      };
    } else {
      return {
        status: 'failed' as const,
        message: 'Limited accessibility support',
        recommendation: 'Accessibility features may not work properly',
      };
    }
  };

  const testNetworkCapabilities = async () => {
    try {
      const start = Date.now();
      await fetch('/api/health');
      const latency = Date.now() - start;

      if (latency < 100) {
        return {
          status: 'passed' as const,
          message: 'Network connection is excellent',
          details: { latency },
        };
      } else if (latency < 500) {
        return {
          status: 'warning' as const,
          message: 'Network connection is adequate',
          details: { latency },
          recommendation: 'Some features may load slowly',
        };
      } else {
        return {
          status: 'failed' as const,
          message: 'Network connection is poor',
          details: { latency },
          recommendation: 'Application may be very slow',
        };
      }
    } catch (error) {
      return {
        status: 'failed' as const,
        message: 'Network test failed',
        details: { error: error.message },
        recommendation: 'Check your internet connection',
      };
    }
  };

  const testStorageSupport = () => {
    const hasLocalStorage = typeof Storage !== 'undefined';
    const hasIndexedDB = 'indexedDB' in window;
    const hasWebSQL = 'openDatabase' in window;

    const supportedStorage = [];
    if (hasLocalStorage) supportedStorage.push('localStorage');
    if (hasIndexedDB) supportedStorage.push('IndexedDB');
    if (hasWebSQL) supportedStorage.push('WebSQL');

    if (supportedStorage.length >= 2) {
      return {
        status: 'passed' as const,
        message: `Storage support: ${supportedStorage.join(', ')}`,
        details: { hasLocalStorage, hasIndexedDB, hasWebSQL },
      };
    } else if (supportedStorage.length === 1) {
      return {
        status: 'warning' as const,
        message: `Limited storage support: ${supportedStorage.join(', ')}`,
        details: { hasLocalStorage, hasIndexedDB, hasWebSQL },
        recommendation: 'Some data persistence features may not work',
      };
    } else {
      return {
        status: 'failed' as const,
        message: 'No storage support detected',
        details: { hasLocalStorage, hasIndexedDB, hasWebSQL },
        recommendation: 'Application cannot store data locally',
      };
    }
  };

  const testCSSFeatures = (cssFeatures: any) => {
    const supportedFeatures = Object.entries(cssFeatures)
      .filter(([_, supported]) => supported)
      .map(([feature, _]) => feature);

    if (supportedFeatures.length >= 4) {
      return {
        status: 'passed' as const,
        message: `CSS features supported: ${supportedFeatures.join(', ')}`,
      };
    } else if (supportedFeatures.length >= 2) {
      return {
        status: 'warning' as const,
        message: `Limited CSS support: ${supportedFeatures.join(', ')}`,
        recommendation: 'Some UI elements may not display correctly',
      };
    } else {
      return {
        status: 'failed' as const,
        message: 'Minimal CSS feature support',
        recommendation: 'User interface may be broken',
      };
    }
  };

  const calculateDeviceScore = (deviceInfo: any) => {
    let score = 0;
    
    // Screen resolution
    if (deviceInfo.screen.width >= 1920) score += 20;
    else if (deviceInfo.screen.width >= 1366) score += 15;
    else if (deviceInfo.screen.width >= 1024) score += 10;
    else score += 5;

    // CPU cores
    if (deviceInfo.hardware.cores >= 8) score += 20;
    else if (deviceInfo.hardware.cores >= 4) score += 15;
    else if (deviceInfo.hardware.cores >= 2) score += 10;
    else score += 5;

    // Memory
    if (deviceInfo.hardware.memory >= 8) score += 20;
    else if (deviceInfo.hardware.memory >= 4) score += 15;
    else if (deviceInfo.hardware.memory >= 2) score += 10;
    else score += 5;

    // Input methods
    if (deviceInfo.input.mouse && deviceInfo.input.keyboard) score += 20;
    else if (deviceInfo.input.touch) score += 15;
    else score += 10;

    // Connection
    if (deviceInfo.hardware.connection.type === '4g' || deviceInfo.hardware.connection.type === 'ethernet') score += 20;
    else if (deviceInfo.hardware.connection.type === 'wifi') score += 15;
    else score += 10;

    return score;
  };

  const calculateOverallStatus = (results: TestResult[]) => {
    const passed = results.filter(r => r.status === 'passed').length;
    const failed = results.filter(r => r.status === 'failed').length;
    const warnings = results.filter(r => r.status === 'warning').length;

    if (failed > 0) return 'poor';
    if (warnings > 2) return 'fair';
    if (passed >= 6) return 'excellent';
    return 'good';
  };

  const getOverallStatusMessage = () => {
    switch (overallStatus) {
      case 'excellent':
        return 'Your system is fully compatible and optimized for this application';
      case 'good':
        return 'Your system is compatible with good performance expected';
      case 'fair':
        return 'Your system is compatible but may have some limitations';
      case 'poor':
        return 'Your system may have compatibility issues affecting performance';
      default:
        return 'Compatibility status unknown';
    }
  };

  const exportReport = () => {
    if (fullReport) {
      const blob = new Blob([JSON.stringify(fullReport, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compatibility-report-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <CheckerContainer className={className}>
      <FadeIn direction="up">
        <Card>
          <ControlsContainer>
            <Button
              variant="primary"
              onClick={runCompatibilityTests}
              disabled={isRunning}
              loading={isRunning}
            >
              {isRunning ? 'Running Tests...' : 'Run Compatibility Tests'}
            </Button>
            
            {fullReport && (
              <Button
                variant="secondary"
                onClick={exportReport}
              >
                Export Report
              </Button>
            )}
          </ControlsContainer>
          
          {isRunning && (
            <ProgressContainer>
              <Progress value={progress} max={100} variant="primary" />
            </ProgressContainer>
          )}
          
          {testResults.some(t => t.status !== 'pending') && (
            <OverallStatus status={overallStatus}>
              {getStatusIcon(overallStatus)} {getOverallStatusMessage()}
            </OverallStatus>
          )}
        </Card>
      </FadeIn>
      
      {testResults.some(t => t.status !== 'pending') && (
        <FadeIn direction="up" delay={100}>
          <TestGrid>
            {testResults.map((test, index) => (
              <TestCard key={index} status={test.status}>
                <TestHeader>
                  <TestTitle>{test.name}</TestTitle>
                  <TestStatus status={test.status}>
                    {getStatusIcon(test.status)} {test.status}
                  </TestStatus>
                </TestHeader>
                
                <TestMessage>{test.message}</TestMessage>
                
                {test.details && (
                  <TestDetails>
                    <pre>{JSON.stringify(test.details, null, 2)}</pre>
                  </TestDetails>
                )}
                
                {test.recommendation && (
                  <TestRecommendation>
                    💡 {test.recommendation}
                  </TestRecommendation>
                )}
              </TestCard>
            ))}
          </TestGrid>
        </FadeIn>
      )}
      
      {systemInfo && (
        <FadeIn direction="up" delay={200}>
          <Card>
            <TestTitle>System Information</TestTitle>
            <SystemInfoGrid>
              <InfoItem>
                <InfoLabel>Browser:</InfoLabel>
                <InfoValue>{systemInfo.browser.name} {systemInfo.browser.version}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>OS:</InfoLabel>
                <InfoValue>{systemInfo.browser.os}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>Mobile:</InfoLabel>
                <InfoValue>{systemInfo.browser.isMobile ? 'Yes' : 'No'}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>Screen:</InfoLabel>
                <InfoValue>{systemInfo.device.screen.width}x{systemInfo.device.screen.height}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>CPU Cores:</InfoLabel>
                <InfoValue>{systemInfo.device.hardware.cores}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>Memory:</InfoLabel>
                <InfoValue>{systemInfo.device.hardware.memory}GB</InfoValue>
              </InfoItem>
            </SystemInfoGrid>
          </Card>
        </FadeIn>
      )}
    </CheckerContainer>
  );
};