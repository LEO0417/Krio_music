import React from 'react';
import styled from 'styled-components';

interface DragDropItemProps {
  children: React.ReactNode;
  isDragging: boolean;
  isDragOver: boolean;
  dragHandleProps?: React.HTMLAttributes<HTMLDivElement>;
  dropZoneProps?: React.HTMLAttributes<HTMLDivElement>;
  className?: string;
}

const DragDropContainer = styled.div<{
  isDragging: boolean;
  isDragOver: boolean;
}>`
  position: relative;
  transition: all 0.2s ease;
  
  ${props => props.isDragging && `
    opacity: 0.5;
    transform: scale(0.95);
    z-index: 1000;
  `}
  
  ${props => props.isDragOver && `
    transform: translateY(-2px);
    
    &::before {
      content: '';
      position: absolute;
      top: -2px;
      left: 0;
      right: 0;
      height: 2px;
      background: var(--color-primary);
      border-radius: 1px;
      z-index: 1;
    }
  `}
`;

const DragHandle = styled.div`
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-secondary);
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
  color: var(--color-text-secondary);
  font-size: 12px;
  z-index: 10;
  
  &:hover {
    background: var(--color-background-hover);
    color: var(--color-text-primary);
  }
  
  &:active {
    cursor: grabbing;
  }
  
  ${DragDropContainer}:hover & {
    opacity: 1;
  }
`;

const DragIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
    <circle cx="3" cy="3" r="1" />
    <circle cx="9" cy="3" r="1" />
    <circle cx="3" cy="6" r="1" />
    <circle cx="9" cy="6" r="1" />
    <circle cx="3" cy="9" r="1" />
    <circle cx="9" cy="9" r="1" />
  </svg>
);

export const DragDropItem: React.FC<DragDropItemProps> = ({
  children,
  isDragging,
  isDragOver,
  dragHandleProps,
  dropZoneProps,
  className,
}) => {
  return (
    <DragDropContainer
      className={className}
      isDragging={isDragging}
      isDragOver={isDragOver}
      {...dropZoneProps}
    >
      <DragHandle {...dragHandleProps}>
        <DragIcon />
      </DragHandle>
      {children}
    </DragDropContainer>
  );
};