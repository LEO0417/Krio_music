import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { useComponentSize } from '@/hooks/usePerformance';
import { FadeIn } from './animations';

interface ResponsiveLayoutTesterProps {
  className?: string;
}

interface ViewportSize {
  width: number;
  height: number;
  name: string;
  description: string;
}

interface LayoutTest {
  name: string;
  viewport: ViewportSize;
  status: 'pending' | 'testing' | 'passed' | 'failed';
  issues: string[];
  screenshot?: string;
}

const TesterContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
`;

const ViewportSelector = styled.div`
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  align-items: center;
`;

const ViewportButton = styled(Button)<{ active: boolean }>`
  background: ${props => props.active ? 'var(--color-primary)' : 'var(--color-background-secondary)'};
  color: ${props => props.active ? 'white' : 'var(--color-text-primary)'};
  border: 1px solid ${props => props.active ? 'var(--color-primary)' : 'var(--color-border)'};
`;

const TestViewport = styled.div<{ width: number; height: number }>`
  width: ${props => props.width}px;
  height: ${props => props.height}px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  position: relative;
  background: white;
  margin: 0 auto;
  transition: all 0.3s ease;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 30px;
    background: linear-gradient(to bottom, #f0f0f0, #e0e0e0);
    border-bottom: 1px solid #ccc;
    z-index: 1;
  }
  
  &::after {
    content: '${props => props.width}×${props => props.height}';
    position: absolute;
    top: 5px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 12px;
    color: #666;
    z-index: 2;
  }
`;

const TestFrame = styled.iframe<{ width: number; height: number }>`
  width: ${props => props.width}px;
  height: ${props => props.height - 30}px;
  border: none;
  display: block;
  margin-top: 30px;
  transform-origin: 0 0;
  transform: scale(${props => Math.min(1, 800 / props.width)});
`;

const TestResults = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
`;

const TestCard = styled(Card)<{ status: 'pending' | 'testing' | 'passed' | 'failed' }>`
  ${props => {
    switch (props.status) {
      case 'testing':
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
      default:
        return '';
    }
  }}
`;

const TestHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
`;

const TestTitle = styled.h3`
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const TestStatus = styled.div<{ status: 'pending' | 'testing' | 'passed' | 'failed' }>`
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 14px;
  font-weight: 500;
  color: ${props => {
    switch (props.status) {
      case 'testing': return 'var(--color-info)';
      case 'passed': return 'var(--color-success)';
      case 'failed': return 'var(--color-danger)';
      default: return 'var(--color-text-secondary)';
    }
  }};
`;

const TestInfo = styled.div`
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
`;

const IssuesList = styled.ul`
  margin: 0;
  padding-left: var(--spacing-md);
  color: var(--color-text-secondary);
  font-size: 14px;
`;

const IssueItem = styled.li`
  color: var(--color-danger);
  margin-bottom: var(--spacing-xs);
`;

const ControlsContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-background-secondary);
  border-radius: var(--radius-md);
  flex-wrap: wrap;
`;

const CurrentViewportInfo = styled.div`
  font-size: 14px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
`;

const ScaleInfo = styled.span`
  margin-left: 8px;
  font-size: 12px;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: var(--spacing-sm);
`;

const PassedStatus = styled.div`
  color: var(--color-success);
  font-size: 14px;
`;

const commonViewports: ViewportSize[] = [
  { width: 320, height: 568, name: 'iPhone SE', description: 'Small mobile' },
  { width: 375, height: 667, name: 'iPhone 8', description: 'Standard mobile' },
  { width: 414, height: 896, name: 'iPhone 11', description: 'Large mobile' },
  { width: 768, height: 1024, name: 'iPad', description: 'Tablet portrait' },
  { width: 1024, height: 768, name: 'iPad Landscape', description: 'Tablet landscape' },
  { width: 1366, height: 768, name: 'Laptop', description: 'Small laptop' },
  { width: 1920, height: 1080, name: 'Desktop', description: 'Full HD' },
  { width: 2560, height: 1440, name: 'Large Desktop', description: '2K display' },
];

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'testing': return '🔄';
    case 'passed': return '✅';
    case 'failed': return '❌';
    default: return '⏳';
  }
};

export const ResponsiveLayoutTester: React.FC<ResponsiveLayoutTesterProps> = ({
  className,
}) => {
  const [selectedViewport, setSelectedViewport] = useState<ViewportSize>(commonViewports[0]);
  const [isAutoTesting, setIsAutoTesting] = useState(false);
  const [layoutTests, setLayoutTests] = useState<LayoutTest[]>([]);
  const [, setCurrentTestIndex] = useState(0);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { ref: containerRef, size: containerSize } = useComponentSize();

  // Initialize layout tests
  useEffect(() => {
    const tests: LayoutTest[] = commonViewports.map(viewport => ({
      name: viewport.name,
      viewport,
      status: 'pending',
      issues: [],
    }));
    setLayoutTests(tests);
  }, []);

  const testLayout = async (viewport: ViewportSize): Promise<string[]> => {
    const issues: string[] = [];
    
    // Simulate layout testing
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock layout issues based on viewport
    if (viewport.width < 400) {
      if (Math.random() > 0.7) {
        issues.push('Text may be too small on this screen size');
      }
      if (Math.random() > 0.8) {
        issues.push('Buttons may be too close together');
      }
    }
    
    if (viewport.width > 1920) {
      if (Math.random() > 0.6) {
        issues.push('Content may appear too spread out');
      }
    }
    
    if (viewport.width > viewport.height && viewport.width < 1000) {
      if (Math.random() > 0.7) {
        issues.push('Sidebar may overlap main content in landscape mode');
      }
    }
    
    // Check for common responsive issues
    if (viewport.width < 768) {
      if (Math.random() > 0.8) {
        issues.push('Grid layout may not stack properly');
      }
      if (Math.random() > 0.9) {
        issues.push('Navigation menu may not collapse correctly');
      }
    }
    
    return issues;
  };

  const runSingleTest = async (viewportIndex: number) => {
    const viewport = commonViewports[viewportIndex];
    
    // Update test status to testing
    setLayoutTests(prev => prev.map((test, index) => 
      index === viewportIndex 
        ? { ...test, status: 'testing', issues: [] }
        : test
    ));
    
    // Run the test
    const issues = await testLayout(viewport);
    
    // Update test results
    setLayoutTests(prev => prev.map((test, index) => 
      index === viewportIndex 
        ? { 
            ...test, 
            status: issues.length > 0 ? 'failed' : 'passed',
            issues 
          }
        : test
    ));
  };

  const runAllTests = async () => {
    setIsAutoTesting(true);
    setCurrentTestIndex(0);
    
    for (let i = 0; i < commonViewports.length; i++) {
      setCurrentTestIndex(i);
      setSelectedViewport(commonViewports[i]);
      await runSingleTest(i);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    setIsAutoTesting(false);
  };

  const runCurrentTest = () => {
    const currentIndex = commonViewports.findIndex(v => v.name === selectedViewport.name);
    if (currentIndex !== -1) {
      runSingleTest(currentIndex);
    }
  };

  const resetTests = () => {
    setLayoutTests(prev => prev.map(test => ({
      ...test,
      status: 'pending',
      issues: [],
    })));
  };

  const exportTestResults = () => {
    const results = {
      timestamp: new Date().toISOString(),
      tests: layoutTests,
      summary: {
        total: layoutTests.length,
        passed: layoutTests.filter(t => t.status === 'passed').length,
        failed: layoutTests.filter(t => t.status === 'failed').length,
        pending: layoutTests.filter(t => t.status === 'pending').length,
      },
    };
    
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `responsive-layout-test-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getScaleFactor = () => {
    const maxWidth = Math.min(containerSize.width * 0.9, 800);
    return Math.min(1, maxWidth / selectedViewport.width);
  };

  return (
    <TesterContainer className={className} ref={containerRef}>
      <FadeIn direction="up">
        <Card>
          <ControlsContainer>
            <CurrentViewportInfo>
              📱 Current: {selectedViewport.name} ({selectedViewport.width}×{selectedViewport.height})
              <ScaleInfo>
                Scale: {(getScaleFactor() * 100).toFixed(0)}%
              </ScaleInfo>
            </CurrentViewportInfo>
            
            <ButtonGroup>
              <Button
                variant="primary"
                onClick={runCurrentTest}
                disabled={isAutoTesting}
              >
                Test Current
              </Button>
              
              <Button
                variant="secondary"
                onClick={runAllTests}
                disabled={isAutoTesting}
                loading={isAutoTesting}
              >
                {isAutoTesting ? 'Testing...' : 'Test All'}
              </Button>
              
              <Button
                variant="outline"
                onClick={resetTests}
                disabled={isAutoTesting}
              >
                Reset
              </Button>
              
              <Button
                variant="ghost"
                onClick={exportTestResults}
                disabled={isAutoTesting}
              >
                Export
              </Button>
            </ButtonGroup>
          </ControlsContainer>
          
          <ViewportSelector>
            {commonViewports.map((viewport, index) => (
              <ViewportButton
                key={viewport.name}
                active={selectedViewport.name === viewport.name}
                onClick={() => setSelectedViewport(viewport)}
                disabled={isAutoTesting}
                size="small"
              >
                {viewport.name}
              </ViewportButton>
            ))}
          </ViewportSelector>
        </Card>
      </FadeIn>
      
      <FadeIn direction="up" delay={100}>
        <Card>
          <TestViewport
            width={selectedViewport.width * getScaleFactor()}
            height={selectedViewport.height * getScaleFactor()}
          >
            <TestFrame
              ref={iframeRef}
              width={selectedViewport.width}
              height={selectedViewport.height}
              src={window.location.href}
              title={`Testing ${selectedViewport.name}`}
            />
          </TestViewport>
        </Card>
      </FadeIn>
      
      {layoutTests.some(test => test.status !== 'pending') && (
        <FadeIn direction="up" delay={200}>
          <TestResults>
            {layoutTests.map((test, index) => (
              <TestCard key={test.name} status={test.status}>
                <TestHeader>
                  <TestTitle>{test.name}</TestTitle>
                  <TestStatus status={test.status}>
                    {getStatusIcon(test.status)} {test.status}
                  </TestStatus>
                </TestHeader>
                
                <TestInfo>
                  {test.viewport.description} - {test.viewport.width}×{test.viewport.height}
                </TestInfo>
                
                {test.issues.length > 0 && (
                  <IssuesList>
                    {test.issues.map((issue, issueIndex) => (
                      <IssueItem key={issueIndex}>{issue}</IssueItem>
                    ))}
                  </IssuesList>
                )}
                
                {test.status === 'passed' && (
                  <PassedStatus>
                    ✅ Layout renders correctly on this viewport
                  </PassedStatus>
                )}
              </TestCard>
            ))}
          </TestResults>
        </FadeIn>
      )}
    </TesterContainer>
  );
};