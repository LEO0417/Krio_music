import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from 'styled-components';
import { FadeIn } from '../FadeIn';

const mockTheme = {};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={mockTheme}>
      {component}
    </ThemeProvider>
  );
};

describe('FadeIn Animation Component', () => {
  it('renders children correctly', () => {
    renderWithTheme(
      <FadeIn>
        <div>Test content</div>
      </FadeIn>
    );
    
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('renders with different directions', () => {
    const { rerender } = renderWithTheme(
      <FadeIn direction="up">
        <div>Fade up</div>
      </FadeIn>
    );
    
    expect(screen.getByText('Fade up')).toBeInTheDocument();
    
    rerender(
      <ThemeProvider theme={mockTheme}>
        <FadeIn direction="down">
          <div>Fade down</div>
        </FadeIn>
      </ThemeProvider>
    );
    
    expect(screen.getByText('Fade down')).toBeInTheDocument();
  });

  it('renders with custom delay and duration', () => {
    renderWithTheme(
      <FadeIn delay={200} duration={800}>
        <div>Custom timing</div>
      </FadeIn>
    );
    
    expect(screen.getByText('Custom timing')).toBeInTheDocument();
  });

  it('renders with all direction options', () => {
    const directions = ['up', 'down', 'left', 'right', 'none'] as const;
    
    directions.forEach(direction => {
      const { rerender } = renderWithTheme(
        <FadeIn direction={direction}>
          <div>{direction} content</div>
        </FadeIn>
      );
      
      expect(screen.getByText(`${direction} content`)).toBeInTheDocument();
    });
  });

  it('handles custom distance', () => {
    renderWithTheme(
      <FadeIn direction="up" distance={50}>
        <div>Custom distance</div>
      </FadeIn>
    );
    
    expect(screen.getByText('Custom distance')).toBeInTheDocument();
  });

  it('applies animation styles correctly', () => {
    renderWithTheme(
      <FadeIn direction="up" delay={100} duration={300}>
        <div>Styled content</div>
      </FadeIn>
    );
    
    const container = screen.getByText('Styled content').parentElement;
    expect(container).toHaveStyle('animation-delay: 100ms');
    expect(container).toHaveStyle('animation-duration: 300ms');
  });
});