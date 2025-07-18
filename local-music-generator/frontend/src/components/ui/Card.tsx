import React from 'react';
import styled, { css } from 'styled-components';

export interface CardProps {
  children: React.ReactNode;
  padding?: 'small' | 'medium' | 'large';
  shadow?: 'none' | 'small' | 'medium' | 'large';
  bordered?: boolean;
  hoverable?: boolean;
  className?: string;
}

const CardPadding = {
  small: css`padding: 12px;`,
  medium: css`padding: 20px;`,
  large: css`padding: 32px;`,
};

const CardShadow = {
  none: css`box-shadow: none;`,
  small: css`box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);`,
  medium: css`box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);`,
  large: css`box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);`,
};

const StyledCard = styled.div<CardProps>`
  background: var(--color-background-primary);
  border-radius: 16px;
  transition: all 0.2s ease;
  
  ${props => CardPadding[props.padding || 'medium']}
  ${props => CardShadow[props.shadow || 'medium']}
  
  ${props => props.bordered && css`
    border: 1px solid var(--color-border);
  `}
  
  ${props => props.hoverable && css`
    cursor: pointer;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
  `}
`;

export const Card: React.FC<CardProps> = ({
  children,
  padding = 'medium',
  shadow = 'medium',
  bordered = false,
  hoverable = false,
  className,
}) => {
  return (
    <StyledCard
      padding={padding}
      shadow={shadow}
      bordered={bordered}
      hoverable={hoverable}
      className={className}
    >
      {children}
    </StyledCard>
  );
};