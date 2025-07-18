import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from 'styled-components';
import { Tooltip } from '../Tooltip';

const mockTheme = {};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={mockTheme}>
      {component}
    </ThemeProvider>
  );
};

describe('Tooltip Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders children correctly', () => {
    renderWithTheme(
      <Tooltip content="Test tooltip">
        <button>Hover me</button>
      </Tooltip>
    );
    
    expect(screen.getByRole('button')).toHaveTextContent('Hover me');
  });

  it('shows tooltip on hover after delay', async () => {
    renderWithTheme(
      <Tooltip content="Test tooltip" delay={500}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const button = screen.getByRole('button');
    fireEvent.mouseEnter(button);
    
    // Tooltip should not be visible immediately
    expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();
    
    // Fast forward time
    jest.advanceTimersByTime(500);
    
    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });
  });

  it('hides tooltip on mouse leave', async () => {
    renderWithTheme(
      <Tooltip content="Test tooltip" delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const button = screen.getByRole('button');
    fireEvent.mouseEnter(button);
    
    jest.advanceTimersByTime(100);
    
    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });
    
    fireEvent.mouseLeave(button);
    
    await waitFor(() => {
      expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();
    });
  });

  it('shows tooltip on focus', async () => {
    renderWithTheme(
      <Tooltip content="Test tooltip" delay={100}>
        <button>Focus me</button>
      </Tooltip>
    );
    
    const button = screen.getByRole('button');
    fireEvent.focus(button);
    
    jest.advanceTimersByTime(100);
    
    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });
  });

  it('hides tooltip on blur', async () => {
    renderWithTheme(
      <Tooltip content="Test tooltip" delay={100}>
        <button>Focus me</button>
      </Tooltip>
    );
    
    const button = screen.getByRole('button');
    fireEvent.focus(button);
    
    jest.advanceTimersByTime(100);
    
    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });
    
    fireEvent.blur(button);
    
    await waitFor(() => {
      expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();
    });
  });

  it('does not show tooltip when disabled', () => {
    renderWithTheme(
      <Tooltip content="Test tooltip" disabled delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const button = screen.getByRole('button');
    fireEvent.mouseEnter(button);
    
    jest.advanceTimersByTime(100);
    
    expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();
  });

  it('clears timeout on unmount', () => {
    const { unmount } = renderWithTheme(
      <Tooltip content="Test tooltip" delay={500}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const button = screen.getByRole('button');
    fireEvent.mouseEnter(button);
    
    // Unmount before timeout
    unmount();
    
    jest.advanceTimersByTime(500);
    
    // Should not throw or cause issues
    expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();
  });

  it('handles different positions', () => {
    const positions = ['top', 'bottom', 'left', 'right'] as const;
    
    positions.forEach(position => {
      const { unmount } = renderWithTheme(
        <Tooltip content="Test tooltip" position={position} delay={100}>
          <button>Hover me</button>
        </Tooltip>
      );
      
      const button = screen.getByRole('button');
      fireEvent.mouseEnter(button);
      
      jest.advanceTimersByTime(100);
      
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
      
      unmount();
    });
  });

  it('cancels previous timeout when hovering again', async () => {
    renderWithTheme(
      <Tooltip content="Test tooltip" delay={500}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const button = screen.getByRole('button');
    
    // First hover
    fireEvent.mouseEnter(button);
    jest.advanceTimersByTime(200);
    
    // Second hover before first timeout
    fireEvent.mouseLeave(button);
    fireEvent.mouseEnter(button);
    
    // Should not show tooltip from first hover
    jest.advanceTimersByTime(300);
    expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();
    
    // Should show tooltip from second hover
    jest.advanceTimersByTime(200);
    
    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    const { container } = renderWithTheme(
      <Tooltip content="Test tooltip" className="custom-tooltip">
        <button>Hover me</button>
      </Tooltip>
    );
    
    expect(container.querySelector('.custom-tooltip')).toBeInTheDocument();
  });

  it('handles long tooltip content', async () => {
    const longContent = 'This is a very long tooltip content that should wrap and display correctly';
    
    renderWithTheme(
      <Tooltip content={longContent} delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );
    
    const button = screen.getByRole('button');
    fireEvent.mouseEnter(button);
    
    jest.advanceTimersByTime(100);
    
    await waitFor(() => {
      expect(screen.getByText(longContent)).toBeInTheDocument();
    });
  });
});