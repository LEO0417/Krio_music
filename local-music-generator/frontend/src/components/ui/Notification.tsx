import React, { useEffect } from 'react';
import styled, { css } from 'styled-components';
import { useAppState } from '@/context/AppStateContext';

interface NotificationItemProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  onClose: (id: string) => void;
}

const NotificationVariants = {
  success: css`
    background: linear-gradient(135deg, #34c759 0%, #28a745 100%);
    color: white;
  `,
  error: css`
    background: linear-gradient(135deg, #ff3b30 0%, #dc3545 100%);
    color: white;
  `,
  warning: css`
    background: linear-gradient(135deg, #ff9500 0%, #fd7e14 100%);
    color: white;
  `,
  info: css`
    background: linear-gradient(135deg, #007aff 0%, #0056b3 100%);
    color: white;
  `,
};

const NotificationItem = styled.div<{ type: 'success' | 'error' | 'warning' | 'info' }>`
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
  max-width: 400px;
  animation: slideIn 0.3s ease;
  
  ${props => NotificationVariants[props.type]}
  
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
`;

const NotificationIcon = styled.div`
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
`;

const NotificationContent = styled.div`
  flex: 1;
  min-width: 0;
`;

const NotificationTitle = styled.h4`
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
`;

const NotificationMessage = styled.p`
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
  line-height: 1.4;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: inherit;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
  flex-shrink: 0;
  
  &:hover {
    opacity: 1;
  }
`;

const NotificationContainer = styled.div`
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1100;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
  
  > * {
    pointer-events: all;
  }
`;

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'success':
      return '✓';
    case 'error':
      return '✗';
    case 'warning':
      return '⚠';
    case 'info':
      return 'ℹ';
    default:
      return 'ℹ';
  }
};

const NotificationItemComponent: React.FC<NotificationItemProps> = ({
  id,
  type,
  title,
  message,
  duration = 5000,
  onClose,
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose(id);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  return (
    <NotificationItem type={type}>
      <NotificationIcon>{getNotificationIcon(type)}</NotificationIcon>
      <NotificationContent>
        <NotificationTitle>{title}</NotificationTitle>
        <NotificationMessage>{message}</NotificationMessage>
      </NotificationContent>
      <CloseButton onClick={() => onClose(id)}>×</CloseButton>
    </NotificationItem>
  );
};

export const NotificationProvider: React.FC = () => {
  const { state, dispatch } = useAppState();

  const handleClose = (id: string) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
  };

  return (
    <NotificationContainer>
      {state.notifications.map(notification => (
        <NotificationItemComponent
          key={notification.id}
          id={notification.id}
          type={notification.type}
          title={notification.title}
          message={notification.message}
          duration={notification.duration}
          onClose={handleClose}
        />
      ))}
    </NotificationContainer>
  );
};