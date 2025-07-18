import React from 'react';
import styled from 'styled-components';
import { useTheme } from '@/context/ThemeContext';
import { useAppState } from '@/context/AppStateContext';
import { Button } from './ui/Button';

interface HeaderProps {
  onMenuClick: () => void;
  sidebarOpen: boolean;
}

const HeaderContainer = styled.header`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-background-primary);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(20px);
  height: 64px;
  flex-shrink: 0;
  
  @media (max-width: 768px) {
    padding: var(--spacing-md);
  }
`;

const LeftSection = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
`;

const MenuButton = styled.button`
  background: none;
  border: none;
  color: var(--color-text-primary);
  font-size: 20px;
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-normal);
  
  &:hover {
    background: var(--color-background-hover);
  }
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
`;

const LogoIcon = styled.div`
  width: 32px;
  height: 32px;
  background: var(--gradient-primary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 18px;
`;

const LogoText = styled.h1`
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  
  @media (max-width: 480px) {
    display: none;
  }
`;

const RightSection = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
`;

const ModelStatus = styled.div<{ status: string }>`
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-background-secondary);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border);
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const StatusDot = styled.div<{ status: string }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'loaded':
        return 'var(--color-success)';
      case 'loading':
        return 'var(--color-warning)';
      case 'error':
        return 'var(--color-danger)';
      default:
        return 'var(--color-text-tertiary)';
    }
  }};
  
  ${props => props.status === 'loading' && `
    animation: pulse 1.5s infinite;
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `}
`;

const StatusText = styled.span`
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
`;

const ThemeToggle = styled.button`
  background: none;
  border: none;
  color: var(--color-text-primary);
  font-size: 20px;
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-normal);
  
  &:hover {
    background: var(--color-background-hover);
  }
`;

const Header: React.FC<HeaderProps> = ({ onMenuClick, sidebarOpen }) => {
  const { theme, setTheme, actualTheme } = useTheme();
  const { state } = useAppState();

  const toggleTheme = () => {
    setTheme(actualTheme === 'light' ? 'dark' : 'light');
  };

  const getModelStatusText = (status: string) => {
    switch (status) {
      case 'loaded':
        return 'Model Ready';
      case 'loading':
        return 'Loading...';
      case 'error':
        return 'Error';
      default:
        return 'Not Loaded';
    }
  };

  return (
    <HeaderContainer>
      <LeftSection>
        <MenuButton onClick={onMenuClick}>
          <span>{sidebarOpen ? '×' : '☰'}</span>
        </MenuButton>
        
        <Logo>
          <LogoIcon>♪</LogoIcon>
          <LogoText>Music Generator</LogoText>
        </Logo>
      </LeftSection>
      
      <RightSection>
        <ModelStatus status={state.modelStatus?.status || 'not_loaded'}>
          <StatusDot status={state.modelStatus?.status || 'not_loaded'} />
          <StatusText>
            {getModelStatusText(state.modelStatus?.status || 'not_loaded')}
          </StatusText>
        </ModelStatus>
        
        <ThemeToggle onClick={toggleTheme}>
          {actualTheme === 'light' ? '🌙' : '☀️'}
        </ThemeToggle>
      </RightSection>
    </HeaderContainer>
  );
};

export default Header;