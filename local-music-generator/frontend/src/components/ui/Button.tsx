import React from 'react';
import styled, { css } from 'styled-components';
import { RippleEffect, LoadingSpinner } from '../animations';

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

const ButtonVariants = {
  primary: css`
    background: linear-gradient(135deg, #007aff 0%, #0056b3 100%);
    color: white;
    border: none;
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #0056b3 0%, #004494 100%);
      transform: translateY(-1px);
    }
    
    &:active:not(:disabled) {
      transform: translateY(0);
    }
  `,
  
  secondary: css`
    background: var(--color-background-secondary);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    
    &:hover:not(:disabled) {
      background: var(--color-background-hover);
      border-color: var(--color-border-hover);
    }
  `,
  
  outline: css`
    background: transparent;
    color: var(--color-primary);
    border: 1px solid var(--color-primary);
    
    &:hover:not(:disabled) {
      background: var(--color-primary);
      color: white;
    }
  `,
  
  ghost: css`
    background: transparent;
    color: var(--color-text-secondary);
    border: none;
    
    &:hover:not(:disabled) {
      background: var(--color-background-hover);
      color: var(--color-text-primary);
    }
  `,
  
  danger: css`
    background: linear-gradient(135deg, #ff3b30 0%, #d70015 100%);
    color: white;
    border: none;
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #d70015 0%, #b8000f 100%);
      transform: translateY(-1px);
    }
    
    &:active:not(:disabled) {
      transform: translateY(0);
    }
  `,
};

const ButtonSizes = {
  small: css`
    padding: 8px 16px;
    font-size: 14px;
    height: 36px;
  `,
  
  medium: css`
    padding: 12px 24px;
    font-size: 16px;
    height: 44px;
  `,
  
  large: css`
    padding: 16px 32px;
    font-size: 18px;
    height: 52px;
  `,
};

const StyledButton = styled.button<ButtonProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 12px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  
  ${props => ButtonVariants[props.variant || 'primary']}
  ${props => ButtonSizes[props.size || 'medium']}
  
  ${props => props.fullWidth && css`
    width: 100%;
  `}
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
  }
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.3);
  }
  
  /* Loading state */
  ${props => props.loading && css`
    pointer-events: none;
  `}
`;

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  fullWidth = false,
  children,
  onClick,
  type = 'button',
}) => {
  const getRippleColor = () => {
    switch (variant) {
      case 'primary':
        return 'rgba(255, 255, 255, 0.6)';
      case 'danger':
        return 'rgba(255, 255, 255, 0.6)';
      default:
        return 'rgba(0, 122, 255, 0.3)';
    }
  };

  return (
    <RippleEffect
      color={getRippleColor()}
      disabled={disabled || loading}
    >
      <StyledButton
        variant={variant}
        size={size}
        disabled={disabled || loading}
        loading={loading}
        fullWidth={fullWidth}
        onClick={onClick}
        type={type}
      >
        {loading && (
          <LoadingSpinner 
            size={size === 'small' ? 'small' : 'medium'}
            color={variant === 'primary' || variant === 'danger' ? 'white' : 'var(--color-primary)'}
          />
        )}
        {!loading && children}
      </StyledButton>
    </RippleEffect>
  );
};