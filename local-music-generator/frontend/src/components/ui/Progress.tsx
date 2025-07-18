import React from 'react';
import styled, { css, keyframes } from 'styled-components';

export interface ProgressProps {
  value: number;
  max?: number;
  size?: 'small' | 'medium' | 'large';
  variant?: 'linear' | 'circular' | 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  animated?: boolean;
  label?: string;
  showValue?: boolean;
  color?: string;
}

const progressAnimation = keyframes`
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
`;

const ProgressWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
`;

const ProgressHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Label = styled.label`
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const Value = styled.span`
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
`;

const ProgressSizes = {
  small: css`height: 4px;`,
  medium: css`height: 6px;`,
  large: css`height: 8px;`,
};

const LinearTrack = styled.div<{ size: 'small' | 'medium' | 'large' }>`
  position: relative;
  width: 100%;
  background: var(--color-background-secondary);
  border-radius: 999px;
  overflow: hidden;
  
  ${props => ProgressSizes[props.size]}
`;

const LinearFill = styled.div<{ 
  percentage: number; 
  animated?: boolean; 
  color?: string; 
}>`
  height: 100%;
  background: ${props => props.color || 'linear-gradient(90deg, #007aff 0%, #0056b3 100%)'};
  border-radius: 999px;
  width: ${props => props.percentage}%;
  transition: width 0.3s ease;
  
  ${props => props.animated && css`
    position: relative;
    overflow: hidden;
    
    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(255, 255, 255, 0.3) 50%,
        transparent 100%
      );
      animation: ${progressAnimation} 2s infinite;
    }
  `}
`;

const CircularSvg = styled.svg<{ size: number }>`
  width: ${props => props.size}px;
  height: ${props => props.size}px;
  transform: rotate(-90deg);
`;

const CircularTrack = styled.circle`
  fill: none;
  stroke: var(--color-background-secondary);
  stroke-width: 4;
`;

const CircularFill = styled.circle<{ 
  percentage: number; 
  circumference: number; 
  animated?: boolean;
  color?: string;
}>`
  fill: none;
  stroke: ${props => props.color || '#007aff'};
  stroke-width: 4;
  stroke-linecap: round;
  stroke-dasharray: ${props => props.circumference};
  stroke-dashoffset: ${props => props.circumference * (1 - props.percentage / 100)};
  transition: stroke-dashoffset 0.3s ease;
  
  ${props => props.animated && css`
    animation: ${progressAnimation} 2s infinite;
  `}
`;

const CircularWrapper = styled.div`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
`;

const CircularValue = styled.div`
  position: absolute;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  size = 'medium',
  variant = 'linear',
  animated = false,
  label,
  showValue = true,
  color,
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const displayValue = `${Math.round(percentage)}%`;

  // Determine color based on variant
  const getColor = () => {
    if (color) return color;
    
    switch (variant) {
      case 'primary': return '#007aff';
      case 'secondary': return '#8e8e93';
      case 'success': return '#28a745';
      case 'warning': return '#ffc107';
      case 'error': return '#dc3545';
      default: return '#007aff';
    }
  };

  const progressColor = getColor();
  const displayVariant = ['linear', 'circular'].includes(variant) ? variant : 'linear';

  if (displayVariant === 'circular') {
    const circularSize = size === 'small' ? 40 : size === 'medium' ? 60 : 80;
    const radius = (circularSize - 8) / 2;
    const circumference = 2 * Math.PI * radius;

    return (
      <ProgressWrapper>
        {(label || showValue) && (
          <ProgressHeader>
            {label && <Label>{label}</Label>}
            {showValue && <Value>{displayValue}</Value>}
          </ProgressHeader>
        )}
        
        <CircularWrapper>
          <CircularSvg size={circularSize}>
            <CircularTrack
              cx={circularSize / 2}
              cy={circularSize / 2}
              r={radius}
            />
            <CircularFill
              cx={circularSize / 2}
              cy={circularSize / 2}
              r={radius}
              percentage={percentage}
              circumference={circumference}
              animated={animated}
              color={progressColor}
            />
          </CircularSvg>
          <CircularValue>{displayValue}</CircularValue>
        </CircularWrapper>
      </ProgressWrapper>
    );
  }

  return (
    <ProgressWrapper>
      {(label || showValue) && (
        <ProgressHeader>
          {label && <Label>{label}</Label>}
          {showValue && <Value>{displayValue}</Value>}
        </ProgressHeader>
      )}
      
      <LinearTrack size={size}>
        <LinearFill
          percentage={percentage}
          animated={animated}
          color={progressColor}
        />
      </LinearTrack>
    </ProgressWrapper>
  );
};