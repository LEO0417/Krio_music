import { useState, useCallback } from 'react';
import { AxiosError } from 'axios';
import { apiClient } from '@/services/api';
import { useNotification } from '@/context/NotificationContext';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiActions<T> {
  execute: (...args: any[]) => Promise<T>;
  reset: () => void;
}

export function useApi<T>(
  apiCall: (...args: any[]) => Promise<T>,
  showNotifications = true
): UseApiState<T> & UseApiActions<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const { showNotification } = useNotification();

  const execute = useCallback(
    async (...args: any[]): Promise<T> => {
      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const result = await apiCall(...args);
        setState(prev => ({ ...prev, data: result, loading: false }));
        return result;
      } catch (error) {
        const errorMessage = apiClient.handleApiError(error as AxiosError);
        setState(prev => ({ ...prev, error: errorMessage, loading: false }));
        
        if (showNotifications) {
          showNotification({
            type: 'error',
            title: 'API Error',
            message: errorMessage,
          });
        }
        
        throw error;
      }
    },
    [apiCall, showNotification, showNotifications]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

// Specialized hooks for common operations
export function useModelStatus() {
  return useApi(apiClient.getModelStatus.bind(apiClient));
}

export function useLoadModel() {
  return useApi(apiClient.loadModel.bind(apiClient));
}

export function useGenerateMusic() {
  return useApi(apiClient.generateMusic.bind(apiClient));
}

export function useTaskStatus() {
  return useApi(apiClient.getTaskStatus.bind(apiClient), false);
}

export function useAudioList() {
  return useApi(apiClient.getAudioList.bind(apiClient));
}

export function useSystemResources() {
  return useApi(apiClient.getSystemResources.bind(apiClient));
}