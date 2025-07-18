import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import styled from 'styled-components';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  disabled?: boolean;
  className?: string;
}

const TooltipContainer = styled.div`
  position: relative;
  display: inline-block;
`;

const TooltipContent = styled.div<{
  position: 'top' | 'bottom' | 'left' | 'right';
  visible: boolean;
  x: number;
  y: number;
}>`
  position: fixed;
  z-index: 1000;
  background: var(--color-background-primary);
  color: var(--color-text-primary);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.4;
  max-width: 200px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--color-border);
  opacity: ${props => props.visible ? 1 : 0};
  visibility: ${props => props.visible ? 'visible' : 'hidden'};
  transform: ${props => {
    const offset = 8;
    switch (props.position) {
      case 'top':
        return `translate(-50%, -100%) translateY(-${offset}px)`;
      case 'bottom':
        return `translate(-50%, 0%) translateY(${offset}px)`;
      case 'left':
        return `translate(-100%, -50%) translateX(-${offset}px)`;
      case 'right':
        return `translate(0%, -50%) translateX(${offset}px)`;
      default:
        return 'translate(-50%, -100%)';
    }
  }};
  left: ${props => props.x}px;
  top: ${props => props.y}px;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  pointer-events: none;
  word-wrap: break-word;
  
  &::before {
    content: '';
    position: absolute;
    width: 0;
    height: 0;
    border-style: solid;
    
    ${props => {
      const arrowSize = 4;
      switch (props.position) {
        case 'top':
          return `
            top: 100%;
            left: 50%;
            margin-left: -${arrowSize}px;
            border-width: ${arrowSize}px ${arrowSize}px 0 ${arrowSize}px;
            border-color: var(--color-background-primary) transparent transparent transparent;
          `;
        case 'bottom':
          return `
            bottom: 100%;
            left: 50%;
            margin-left: -${arrowSize}px;
            border-width: 0 ${arrowSize}px ${arrowSize}px ${arrowSize}px;
            border-color: transparent transparent var(--color-background-primary) transparent;
          `;
        case 'left':
          return `
            top: 50%;
            left: 100%;
            margin-top: -${arrowSize}px;
            border-width: ${arrowSize}px 0 ${arrowSize}px ${arrowSize}px;
            border-color: transparent transparent transparent var(--color-background-primary);
          `;
        case 'right':
          return `
            top: 50%;
            right: 100%;
            margin-top: -${arrowSize}px;
            border-width: ${arrowSize}px ${arrowSize}px ${arrowSize}px 0;
            border-color: transparent var(--color-background-primary) transparent transparent;
          `;
        default:
          return '';
      }
    }}
  }
`;

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 500,
  disabled = false,
  className,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const calculatePosition = () => {
    if (!containerRef.current) return { x: 0, y: 0 };

    const rect = containerRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    switch (position) {
      case 'top':
        return { x: centerX, y: rect.top };
      case 'bottom':
        return { x: centerX, y: rect.bottom };
      case 'left':
        return { x: rect.left, y: centerY };
      case 'right':
        return { x: rect.right, y: centerY };
      default:
        return { x: centerX, y: rect.top };
    }
  };

  const handleMouseEnter = () => {
    if (disabled) return;

    const pos = calculatePosition();
    setTooltipPosition(pos);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  const handleFocus = () => {
    if (disabled) return;
    handleMouseEnter();
  };

  const handleBlur = () => {
    handleMouseLeave();
  };

  return (
    <>
      <TooltipContainer
        ref={containerRef}
        className={className}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
      >
        {children}
      </TooltipContainer>
      
      {content && createPortal(
        <TooltipContent
          position={position}
          visible={isVisible}
          x={tooltipPosition.x}
          y={tooltipPosition.y}
        >
          {content}
        </TooltipContent>,
        document.body
      )}
    </>
  );
};