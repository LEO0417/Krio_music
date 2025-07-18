import React from 'react';
import styled, { keyframes } from 'styled-components';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
}

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
`;

const bounce = keyframes`
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-10px); }
  60% { transform: translateY(-5px); }
`;

const SpinnerContainer = styled.div<{ size: 'small' | 'medium' | 'large' }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 16px;
          height: 16px;
        `;
      case 'large':
        return `
          width: 48px;
          height: 48px;
        `;
      case 'medium':
      default:
        return `
          width: 24px;
          height: 24px;
        `;
    }
  }}
`;

const CircleSpinner = styled.div<{ color?: string }>`
  width: 100%;
  height: 100%;
  border: 2px solid ${props => props.color || 'var(--color-text-tertiary)'};
  border-top: 2px solid ${props => props.color || 'var(--color-primary)'};
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
`;

const DotsContainer = styled.div`
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
`;

const Dot = styled.div<{ color?: string; delay: number }>`
  width: 6px;
  height: 6px;
  background-color: ${props => props.color || 'var(--color-primary)'};
  border-radius: 50%;
  animation: ${bounce} 1.4s infinite ${props => props.delay}s;
`;

const PulseSpinnerElement = styled.div<{ color?: string }>`
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: ${props => props.color || 'var(--color-primary)'};
  animation: ${pulse} 1.5s infinite;
`;

const WaveContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
`;

const WaveBar = styled.div<{ color?: string; delay: number }>`
  width: 3px;
  height: 16px;
  background-color: ${props => props.color || 'var(--color-primary)'};
  border-radius: 1px;
  animation: ${keyframes`
    0%, 40%, 100% { transform: scaleY(0.4); }
    20% { transform: scaleY(1); }
  `} 1.2s infinite ${props => props.delay}s;
`;

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color,
  className,
}) => {
  return (
    <SpinnerContainer size={size} className={className}>
      <CircleSpinner color={color} />
    </SpinnerContainer>
  );
};

export const DotsSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color,
  className,
}) => {
  return (
    <SpinnerContainer size={size} className={className}>
      <DotsContainer>
        <Dot color={color} delay={0} />
        <Dot color={color} delay={0.2} />
        <Dot color={color} delay={0.4} />
      </DotsContainer>
    </SpinnerContainer>
  );
};

export const PulseSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color,
  className,
}) => {
  return (
    <SpinnerContainer size={size} className={className}>
      <PulseSpinnerElement color={color} />
    </SpinnerContainer>
  );
};

export const WaveSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color,
  className,
}) => {
  return (
    <SpinnerContainer size={size} className={className}>
      <WaveContainer>
        <WaveBar color={color} delay={0} />
        <WaveBar color={color} delay={0.1} />
        <WaveBar color={color} delay={0.2} />
        <WaveBar color={color} delay={0.3} />
        <WaveBar color={color} delay={0.4} />
      </WaveContainer>
    </SpinnerContainer>
  );
};