import React, { useState, useRef } from 'react';
import styled, { keyframes } from 'styled-components';

interface RippleEffectProps {
  children: React.ReactNode;
  className?: string;
  color?: string;
  duration?: number;
  disabled?: boolean;
}

interface HoverEffectProps {
  children: React.ReactNode;
  effect?: 'lift' | 'glow' | 'scale' | 'rotate' | 'bounce';
  className?: string;
  disabled?: boolean;
}

const rippleAnimation = keyframes`
  0% {
    transform: scale(0);
    opacity: 0.6;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
`;


const glowEffect = keyframes`
  0% {
    box-shadow: 0 0 0 0 rgba(0, 122, 255, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(0, 122, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 122, 255, 0);
  }
`;



const bounceEffect = keyframes`
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
`;

const RippleContainer = styled.div`
  position: relative;
  overflow: hidden;
  cursor: pointer;
`;

const RippleCircle = styled.div<{ x: number; y: number; color: string; duration: number }>`
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: ${props => props.color};
  left: ${props => props.x - 10}px;
  top: ${props => props.y - 10}px;
  animation: ${rippleAnimation} ${props => props.duration}ms linear;
  pointer-events: none;
`;

const HoverContainer = styled.div<{
  effect: 'lift' | 'glow' | 'scale' | 'rotate' | 'bounce';
  disabled: boolean;
}>`
  transition: all 0.3s ease;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  
  ${props => !props.disabled && `
    &:hover {
      ${props.effect === 'lift' && `
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
      `}
      
      ${props.effect === 'glow' && `
        animation: ${glowEffect} 1.5s infinite;
      `}
      
      ${props.effect === 'scale' && `
        transform: scale(1.05);
      `}
      
      ${props.effect === 'rotate' && `
        transform: rotate(5deg);
      `}
      
      ${props.effect === 'bounce' && `
        animation: ${bounceEffect} 0.6s;
      `}
    }
  `}
`;

export const RippleEffect: React.FC<RippleEffectProps> = ({
  children,
  className,
  color = 'rgba(255, 255, 255, 0.6)',
  duration = 600,
  disabled = false,
}) => {
  const [ripples, setRipples] = useState<Array<{
    id: number;
    x: number;
    y: number;
  }>>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleClick = (event: React.MouseEvent) => {
    if (disabled) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const newRipple = {
      id: Date.now(),
      x,
      y,
    };

    setRipples(prev => [...prev, newRipple]);

    setTimeout(() => {
      setRipples(prev => prev.filter(ripple => ripple.id !== newRipple.id));
    }, duration);
  };

  return (
    <RippleContainer
      ref={containerRef}
      className={className}
      onClick={handleClick}
    >
      {children}
      {ripples.map(ripple => (
        <RippleCircle
          key={ripple.id}
          x={ripple.x}
          y={ripple.y}
          color={color}
          duration={duration}
        />
      ))}
    </RippleContainer>
  );
};

export const HoverEffect: React.FC<HoverEffectProps> = ({
  children,
  effect = 'lift',
  className,
  disabled = false,
}) => {
  return (
    <HoverContainer
      effect={effect}
      disabled={disabled}
      className={className}
    >
      {children}
    </HoverContainer>
  );
};

// Loading dots animation
const LoadingDots = styled.div`
  display: inline-flex;
  gap: 4px;
  align-items: center;
`;

const Dot = styled.div<{ delay: number }>`
  width: 8px;
  height: 8px;
  background-color: var(--color-primary);
  border-radius: 50%;
  animation: ${keyframes`
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  `} 1.4s infinite ${props => props.delay}s;
`;

export const LoadingDotsAnimation: React.FC = () => {
  return (
    <LoadingDots>
      <Dot delay={0} />
      <Dot delay={0.2} />
      <Dot delay={0.4} />
    </LoadingDots>
  );
};

// Pulse effect for notifications
const pulseNotification = keyframes`
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
`;

export const PulseNotification = styled.div`
  animation: ${pulseNotification} 2s infinite;
`;

// Shake effect for errors
const shakeAnimation = keyframes`
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
`;

export const ShakeEffect = styled.div<{ trigger: boolean }>`
  ${props => props.trigger && `
    animation: ${shakeAnimation} 0.5s;
  `}
`;

// Typing animation
const typingAnimation = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
`;

export const TypingIndicator = styled.div`
  &::after {
    content: '|';
    animation: ${typingAnimation} 1s infinite;
  }
`;

// Progress bar fill animation
const progressFill = keyframes`
  0% { width: 0%; }
  100% { width: 100%; }
`;

export const AnimatedProgressBar = styled.div<{ duration: number }>`
  width: 100%;
  height: 4px;
  background-color: var(--color-background-secondary);
  border-radius: 2px;
  overflow: hidden;
  
  &::after {
    content: '';
    display: block;
    height: 100%;
    background: var(--gradient-primary);
    animation: ${progressFill} ${props => props.duration}ms ease-out;
  }
`;