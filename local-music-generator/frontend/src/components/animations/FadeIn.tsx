import React from 'react';
import styled, { keyframes } from 'styled-components';

interface FadeInProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  direction?: 'up' | 'down' | 'left' | 'right' | 'none';
  distance?: number;
}

const fadeIn = keyframes`
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
`;

const slideUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const slideDown = keyframes`
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const slideLeft = keyframes`
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

const slideRight = keyframes`
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

const AnimatedContainer = styled.div<{
  delay: number;
  duration: number;
  direction: 'up' | 'down' | 'left' | 'right' | 'none';
  distance: number;
}>`
  animation: ${props => {
    switch (props.direction) {
      case 'up':
        return slideUp;
      case 'down':
        return slideDown;
      case 'left':
        return slideLeft;
      case 'right':
        return slideRight;
      case 'none':
      default:
        return fadeIn;
    }
  }} ${props => props.duration}ms ease-out ${props => props.delay}ms both;
`;

export const FadeIn: React.FC<FadeInProps> = ({
  children,
  delay = 0,
  duration = 500,
  direction = 'none',
  distance = 20,
}) => {
  return (
    <AnimatedContainer
      delay={delay}
      duration={duration}
      direction={direction}
      distance={distance}
    >
      {children}
    </AnimatedContainer>
  );
};