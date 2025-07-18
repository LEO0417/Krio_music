import { useCallback } from 'react';
import { useAppState } from '@/context/AppStateContext';
import { apiClient } from '@/services/api';

export const useApi = () => {
  const { dispatch } = useAppState();

  const generateMusic = useCallback(async (params: {
    prompt: string;
    duration?: number;
    temperature?: number;
    top_k?: number;
    top_p?: number;
    guidance_scale?: number;
  }) => {
    try {
      const response = await apiClient.generateMusic(params);
      
      dispatch({
        type: 'SET_CURRENT_GENERATION',
        payload: {
          task_id: response.task_id,
          status: 'processing',
          progress: 0,
          prompt: params.prompt,
          created_at: new Date().toISOString(),
        },
      });
      
      return response;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const getGenerationStatus = useCallback(async (taskId: string) => {
    try {
      const response = await apiClient.getTaskStatus(taskId);
      
      dispatch({
        type: 'UPDATE_GENERATION_STATUS',
        payload: {
          task_id: taskId,
          status: response.status,
          progress: response.progress,
          message: response.message,
        },
      });
      
      return response;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const getGenerationResult = useCallback(async (taskId: string) => {
    try {
      const response = await apiClient.getTaskResult(taskId);
      
      if (response.status === 'completed') {
        dispatch({
          type: 'SET_GENERATION_RESULT',
          payload: {
            task_id: taskId,
            result: response.result,
          },
        });
      }
      
      return response;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const cancelGeneration = useCallback(async (taskId: string) => {
    try {
      const response = await apiClient.cancelGeneration(taskId);
      
      dispatch({
        type: 'UPDATE_GENERATION_STATUS',
        payload: {
          task_id: taskId,
          status: 'cancelled',
          progress: 0,
          message: 'Generation cancelled',
        },
      });
      
      return response;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const getGenerationHistory = useCallback(async () => {
    try {
      const response = await apiClient.getGenerationHistory();
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const validateParameters = useCallback(async (params: any) => {
    try {
      const response = await apiClient.validateParameters(params);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const getGenerationStats = useCallback(async () => {
    try {
      const response = await apiClient.getGenerationStats();
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const getAudioList = useCallback(async () => {
    try {
      const response = await apiClient.getAudioList();
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const getAudioMetadata = useCallback(async (audioId: string) => {
    try {
      const response = await apiClient.getAudioMetadata(audioId);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const updateAudioMetadata = useCallback(async (audioId: string, metadata: any) => {
    try {
      const response = await apiClient.updateAudioMetadata(audioId, metadata);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const deleteAudio = useCallback(async (audioId: string) => {
    try {
      const response = await apiClient.deleteAudio(audioId);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const downloadAudio = useCallback(async (audioId: string, format?: string) => {
    try {
      const response = await apiClient.downloadAudio(audioId, format);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const convertAudio = useCallback(async (audioId: string, format: string, quality?: string) => {
    try {
      const response = await apiClient.convertAudio(audioId, format, quality);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const analyzeAudio = useCallback(async (audioId: string) => {
    try {
      const response = await apiClient.analyzeAudio(audioId);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const getAudioStats = useCallback(async () => {
    try {
      const response = await apiClient.getAudioStats();
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const cleanupAudio = useCallback(async (olderThan?: string) => {
    try {
      const response = await apiClient.cleanupAudio(olderThan);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const loadModel = useCallback(async () => {
    try {
      dispatch({
        type: 'SET_MODEL_STATUS',
        payload: { status: 'loading' },
      });
      
      const response = await apiClient.loadModel();
      
      dispatch({
        type: 'SET_MODEL_STATUS',
        payload: { status: 'loaded' },
      });
      
      return response;
    } catch (error) {
      dispatch({
        type: 'SET_MODEL_STATUS',
        payload: { status: 'error' },
      });
      throw error;
    }
  }, [dispatch]);

  const unloadModel = useCallback(async () => {
    try {
      const response = await apiClient.unloadModel();
      
      dispatch({
        type: 'SET_MODEL_STATUS',
        payload: { status: 'not_loaded' },
      });
      
      return response;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const getModelStatus = useCallback(async () => {
    try {
      const response = await apiClient.getModelStatus();
      
      dispatch({
        type: 'SET_MODEL_STATUS',
        payload: {
          status: response.status,
          model_name: response.model_name,
          loaded_at: response.loaded_at,
        },
      });
      
      return response;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const clearCache = useCallback(async () => {
    try {
      const response = await apiClient.clearCache();
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const getSystemStatus = useCallback(async () => {
    try {
      const response = await apiClient.getSystemResources();
      
      dispatch({
        type: 'SET_SYSTEM_RESOURCES',
        payload: {
          cpu: response.cpu,
          memory: response.memory,
          gpu: response.gpu,
          disk_usage: response.disk_usage,
          cache_size: response.cache_size,
        },
      });
      
      return response;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  return {
    // Generation APIs
    generateMusic,
    getGenerationStatus,
    getGenerationResult,
    cancelGeneration,
    getGenerationHistory,
    validateParameters,
    getGenerationStats,
    
    // Audio APIs
    getAudioList,
    getAudioMetadata,
    updateAudioMetadata,
    deleteAudio,
    downloadAudio,
    convertAudio,
    analyzeAudio,
    getAudioStats,
    cleanupAudio,
    
    // Model APIs
    loadModel,
    unloadModel,
    getModelStatus,
    clearCache,
    
    // System APIs
    getSystemStatus,
  };
};