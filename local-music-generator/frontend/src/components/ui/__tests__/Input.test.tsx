import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from 'styled-components';
import { Input } from '../Input';

const mockTheme = {};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={mockTheme}>
      {component}
    </ThemeProvider>
  );
};

describe('Input Component', () => {
  it('renders input field', () => {
    renderWithTheme(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('handles value changes', () => {
    const handleChange = jest.fn();
    renderWithTheme(<Input value="" onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test' } });
    expect(handleChange).toHaveBeenCalled();
  });

  it('handles disabled state', () => {
    renderWithTheme(<Input disabled placeholder="Disabled input" />);
    expect(screen.getByPlaceholderText('Disabled input')).toBeDisabled();
  });

  it('renders multiline input', () => {
    renderWithTheme(<Input multiline placeholder="Multiline input" />);
    expect(screen.getByPlaceholderText('Multiline input')).toBeInTheDocument();
  });

  it('handles error state', () => {
    renderWithTheme(<Input error="Error message" placeholder="Error input" />);
    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  it('renders with label', () => {
    renderWithTheme(<Input label="Test Label" placeholder="With label" />);
    expect(screen.getByText('Test Label')).toBeInTheDocument();
  });

  it('supports different types', () => {
    renderWithTheme(<Input type="email" placeholder="Email input" />);
    expect(screen.getByPlaceholderText('Email input')).toHaveAttribute('type', 'email');
  });

  it('supports full width', () => {
    renderWithTheme(<Input fullWidth placeholder="Full width input" />);
    expect(screen.getByPlaceholderText('Full width input')).toBeInTheDocument();
  });

  it('handles focus and blur events', () => {
    const handleFocus = jest.fn();
    const handleBlur = jest.fn();
    
    renderWithTheme(
      <Input 
        placeholder="Focus test" 
        onFocus={handleFocus} 
        onBlur={handleBlur} 
      />
    );
    
    const input = screen.getByPlaceholderText('Focus test');
    fireEvent.focus(input);
    expect(handleFocus).toHaveBeenCalled();
    
    fireEvent.blur(input);
    expect(handleBlur).toHaveBeenCalled();
  });
});