import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AppStateProvider, useAppState } from '../AppStateContext';

// Test component that uses the context
const TestComponent = () => {
  const { state, dispatch } = useAppState();
  
  return (
    <div>
      <span data-testid="current-page">{state.currentPage}</span>
      <span data-testid="sidebar-open">{state.sidebarOpen.toString()}</span>
      <button 
        onClick={() => dispatch({ type: 'SET_CURRENT_PAGE', payload: '/test' })}
        data-testid="set-page-button"
      >
        Set Page
      </button>
      <button 
        onClick={() => dispatch({ type: 'SET_SIDEBAR_OPEN', payload: true })}
        data-testid="open-sidebar-button"
      >
        Open Sidebar
      </button>
    </div>
  );
};

describe('AppStateContext', () => {
  it('provides initial state', () => {
    render(
      <AppStateProvider>
        <TestComponent />
      </AppStateProvider>
    );
    
    expect(screen.getByTestId('current-page')).toHaveTextContent('/');
    expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');
  });

  it('updates current page', () => {
    render(
      <AppStateProvider>
        <TestComponent />
      </AppStateProvider>
    );
    
    fireEvent.click(screen.getByTestId('set-page-button'));
    expect(screen.getByTestId('current-page')).toHaveTextContent('/test');
  });

  it('toggles sidebar state', () => {
    render(
      <AppStateProvider>
        <TestComponent />
      </AppStateProvider>
    );
    
    fireEvent.click(screen.getByTestId('open-sidebar-button'));
    expect(screen.getByTestId('sidebar-open')).toHaveTextContent('true');
  });

  it('throws error when used outside provider', () => {
    const originalError = console.error;
    console.error = jest.fn();
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAppState must be used within an AppStateProvider');
    
    console.error = originalError;
  });
});