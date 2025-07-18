import React, { useEffect, useState } from 'react';
import styled, { keyframes } from 'styled-components';

interface PageTransitionProps {
  children: React.ReactNode;
  pageKey: string;
  direction?: 'fade' | 'slide' | 'scale';
  duration?: number;
}

const fadeIn = keyframes`
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
`;

const fadeOut = keyframes`
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
`;

const slideInFromRight = keyframes`
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

const slideOutToLeft = keyframes`
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(-100%);
  }
`;

const scaleIn = keyframes`
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`;

const scaleOut = keyframes`
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.8);
  }
`;

const TransitionContainer = styled.div<{
  direction: 'fade' | 'slide' | 'scale';
  duration: number;
  isEntering: boolean;
  isExiting: boolean;
}>`
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  
  ${props => {
    if (props.isExiting) {
      switch (props.direction) {
        case 'slide':
          return `animation: ${slideOutToLeft} ${props.duration}ms ease-in-out forwards;`;
        case 'scale':
          return `animation: ${scaleOut} ${props.duration}ms ease-in-out forwards;`;
        case 'fade':
        default:
          return `animation: ${fadeOut} ${props.duration}ms ease-in-out forwards;`;
      }
    } else if (props.isEntering) {
      switch (props.direction) {
        case 'slide':
          return `animation: ${slideInFromRight} ${props.duration}ms ease-in-out forwards;`;
        case 'scale':
          return `animation: ${scaleIn} ${props.duration}ms ease-in-out forwards;`;
        case 'fade':
        default:
          return `animation: ${fadeIn} ${props.duration}ms ease-in-out forwards;`;
      }
    }
    return '';
  }}
`;

export const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  pageKey,
  direction = 'fade',
  duration = 300,
}) => {
  const [currentPageKey, setCurrentPageKey] = useState(pageKey);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isEntering, setIsEntering] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (pageKey !== currentPageKey) {
      setIsTransitioning(true);
      setIsExiting(true);
      setIsEntering(false);

      const exitTimer = setTimeout(() => {
        setCurrentPageKey(pageKey);
        setIsExiting(false);
        setIsEntering(true);
      }, duration);

      const enterTimer = setTimeout(() => {
        setIsEntering(false);
        setIsTransitioning(false);
      }, duration * 2);

      return () => {
        clearTimeout(exitTimer);
        clearTimeout(enterTimer);
      };
    }
  }, [pageKey, currentPageKey, duration]);

  return (
    <TransitionContainer
      direction={direction}
      duration={duration}
      isEntering={isEntering}
      isExiting={isExiting}
    >
      {children}
    </TransitionContainer>
  );
};