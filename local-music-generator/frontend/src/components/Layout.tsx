import React from 'react';
import styled from 'styled-components';
import { useAppState } from '@/context/AppStateContext';
import { useTheme } from '@/context/ThemeContext';
import Sidebar from './Sidebar';
import Header from './Header';
import { NotificationProvider } from './ui/Notification';
import { KeyboardShortcuts } from './KeyboardShortcuts';

interface LayoutProps {
  children: React.ReactNode;
}

const LayoutContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background: var(--color-background-primary);
`;

const SidebarContainer = styled.div<{ isOpen: boolean }>`
  width: ${props => props.isOpen ? '280px' : '0'};
  transition: width 0.3s ease;
  overflow: hidden;
  background: var(--color-background-secondary);
  border-right: 1px solid var(--color-border);
  
  @media (max-width: 768px) {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    width: ${props => props.isOpen ? '280px' : '0'};
    box-shadow: ${props => props.isOpen ? '0 0 20px rgba(0, 0, 0, 0.3)' : 'none'};
  }
`;

const MainContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
`;

const ContentContainer = styled.main`
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  
  @media (max-width: 768px) {
    padding: var(--spacing-md);
  }
`;

const Overlay = styled.div<{ isVisible: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
  opacity: ${props => props.isVisible ? 1 : 0};
  visibility: ${props => props.isVisible ? 'visible' : 'hidden'};
  transition: all 0.3s ease;
  
  @media (min-width: 769px) {
    display: none;
  }
`;

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { state, dispatch } = useAppState();
  const { theme, setTheme, actualTheme } = useTheme();

  const toggleSidebar = () => {
    dispatch({ type: 'SET_SIDEBAR_OPEN', payload: !state.sidebarOpen });
  };

  const closeSidebar = () => {
    dispatch({ type: 'SET_SIDEBAR_OPEN', payload: false });
  };

  const toggleTheme = () => {
    setTheme(actualTheme === 'light' ? 'dark' : 'light');
  };

  return (
    <LayoutContainer>
      <SidebarContainer isOpen={state.sidebarOpen}>
        <Sidebar />
      </SidebarContainer>
      
      <MainContainer>
        <Header 
          onMenuClick={toggleSidebar}
          sidebarOpen={state.sidebarOpen}
        />
        
        <ContentContainer>
          {children}
        </ContentContainer>
      </MainContainer>
      
      <Overlay 
        isVisible={state.sidebarOpen} 
        onClick={closeSidebar}
      />
      
      <NotificationProvider />
      
      <KeyboardShortcuts 
        onToggleTheme={toggleTheme}
      />
    </LayoutContainer>
  );
};

export default Layout;