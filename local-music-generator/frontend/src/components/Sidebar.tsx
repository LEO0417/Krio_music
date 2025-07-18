import React from 'react';
import styled from 'styled-components';
import { useAppState } from '@/context/AppStateContext';

interface SidebarProps {}

const SidebarContainer = styled.nav`
  width: 100%;
  height: 100vh;
  background: var(--color-background-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg) 0;
`;

const SidebarHeader = styled.div`
  padding: 0 var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
`;

const SidebarTitle = styled.h3`
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const SidebarNav = styled.ul`
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
`;

const NavItem = styled.li`
  margin-bottom: var(--spacing-xs);
`;

const NavLink = styled.button<{ active?: boolean }>`
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: ${props => props.active ? 'var(--color-background-hover)' : 'transparent'};
  border: none;
  border-left: 3px solid ${props => props.active ? 'var(--color-primary)' : 'transparent'};
  color: ${props => props.active ? 'var(--color-primary)' : 'var(--color-text-secondary)'};
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
  text-align: left;
  
  &:hover {
    background: var(--color-background-hover);
    color: var(--color-text-primary);
  }
`;

const NavIcon = styled.span`
  font-size: 18px;
  flex-shrink: 0;
`;

const NavText = styled.span`
  flex: 1;
`;

const SidebarFooter = styled.div`
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  margin-top: auto;
`;

const SystemStatus = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
`;

const StatusItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-secondary);
`;

const StatusLabel = styled.span`
  font-weight: 500;
`;

const StatusValue = styled.span<{ status?: 'good' | 'warning' | 'error' }>`
  color: ${props => {
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
  font-weight: 500;
`;

const navigationItems = [
  { id: 'home', label: 'Generate Music', icon: '🎵', path: '/' },
  { id: 'library', label: 'Music Library', icon: '🎼', path: '/library' },
  { id: 'history', label: 'History', icon: '📜', path: '/history' },
  { id: 'settings', label: 'Settings', icon: '⚙️', path: '/settings' },
];

const Sidebar: React.FC<SidebarProps> = () => {
  const { state, dispatch } = useAppState();
  
  const handleNavClick = (path: string) => {
    dispatch({ type: 'SET_CURRENT_PAGE', payload: path });
    // Close sidebar on mobile after navigation
    if (window.innerWidth <= 768) {
      dispatch({ type: 'SET_SIDEBAR_OPEN', payload: false });
    }
  };

  const getSystemStatus = () => {
    if (state.systemResources) {
      const { cpu, memory, gpu } = state.systemResources;
      if (cpu > 90 || memory > 90 || (gpu && gpu > 90)) {
        return 'error';
      }
      if (cpu > 70 || memory > 70 || (gpu && gpu > 70)) {
        return 'warning';
      }
      return 'good';
    }
    return undefined;
  };

  const formatPercentage = (value: number | undefined) => {
    return value ? `${value.toFixed(1)}%` : '--';
  };

  return (
    <SidebarContainer>
      <SidebarHeader>
        <SidebarTitle>Navigation</SidebarTitle>
      </SidebarHeader>
      
      <SidebarNav>
        {navigationItems.map(item => (
          <NavItem key={item.id}>
            <NavLink
              active={state.currentPage === item.path}
              onClick={() => handleNavClick(item.path)}
            >
              <NavIcon>{item.icon}</NavIcon>
              <NavText>{item.label}</NavText>
            </NavLink>
          </NavItem>
        ))}
      </SidebarNav>
      
      <SidebarFooter>
        <SystemStatus>
          <StatusItem>
            <StatusLabel>System Status</StatusLabel>
            <StatusValue status={getSystemStatus()}>
              {getSystemStatus() === 'good' ? 'Good' : 
               getSystemStatus() === 'warning' ? 'Warning' : 
               getSystemStatus() === 'error' ? 'High Load' : 'Unknown'}
            </StatusValue>
          </StatusItem>
          
          <StatusItem>
            <StatusLabel>CPU</StatusLabel>
            <StatusValue>
              {formatPercentage(state.systemResources?.cpu)}
            </StatusValue>
          </StatusItem>
          
          <StatusItem>
            <StatusLabel>Memory</StatusLabel>
            <StatusValue>
              {formatPercentage(state.systemResources?.memory)}
            </StatusValue>
          </StatusItem>
          
          {state.systemResources?.gpu && (
            <StatusItem>
              <StatusLabel>GPU</StatusLabel>
              <StatusValue>
                {formatPercentage(state.systemResources.gpu)}
              </StatusValue>
            </StatusItem>
          )}
        </SystemStatus>
      </SidebarFooter>
    </SidebarContainer>
  );
};

export default Sidebar;