import axios, { AxiosInstance, AxiosError } from 'axios';

// Types
export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: any;
    suggestion?: string;
    timestamp: string;
  };
}

// API Client Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API] ${response.status} ${response.config.url}`);
        return response;
      },
      (error: AxiosError) => {
        console.error(`[API] Error ${error.response?.status} ${error.config?.url}:`, error.response?.data);
        return Promise.reject(error);
      }
    );
  }

  // Model Management APIs
  async getModelStatus() {
    const response = await this.client.get('/api/models/status');
    return response.data;
  }

  async loadModel(modelName?: string, force = false) {
    const response = await this.client.post('/api/models/load', {
      model_name: modelName,
      force,
    });
    return response.data;
  }

  async unloadModel() {
    const response = await this.client.post('/api/models/unload');
    return response.data;
  }

  async getModelInfo() {
    const response = await this.client.get('/api/models/info');
    return response.data;
  }

  async getSupportedModels() {
    const response = await this.client.get('/api/models/supported');
    return response.data;
  }

  async validateModel(modelName: string) {
    const response = await this.client.get(`/api/models/validate/${modelName}`);
    return response.data;
  }

  async getModelCache() {
    const response = await this.client.get('/api/models/cache');
    return response.data;
  }

  async clearModelCache(modelName?: string) {
    const response = await this.client.delete('/api/models/cache', {
      params: { model_name: modelName },
    });
    return response.data;
  }

  // Music Generation APIs
  async generateMusic(prompt: string, parameters?: Record<string, any>) {
    const response = await this.client.post('/api/generate/generate', {
      prompt,
      parameters,
    });
    return response.data;
  }

  async getTaskStatus(taskId: string) {
    const response = await this.client.get(`/api/generate/status/${taskId}`);
    return response.data;
  }

  async getTaskResult(taskId: string) {
    const response = await this.client.get(`/api/generate/result/${taskId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async cancelTask(taskId: string) {
    const response = await this.client.delete(`/api/generate/cancel/${taskId}`);
    return response.data;
  }

  async getActiveTasks() {
    const response = await this.client.get('/api/generate/tasks');
    return response.data;
  }

  async getTaskHistory(limit = 50) {
    const response = await this.client.get('/api/generate/history', {
      params: { limit },
    });
    return response.data;
  }

  async clearTaskHistory() {
    const response = await this.client.delete('/api/generate/history');
    return response.data;
  }

  async validateGenerationRequest(prompt: string, parameters?: string) {
    const response = await this.client.get('/api/generate/validate', {
      params: { prompt, parameters },
    });
    return response.data;
  }

  async getGenerationStats() {
    const response = await this.client.get('/api/generate/stats');
    return response.data;
  }

  // Audio Management APIs
  async getAudioList() {
    const response = await this.client.get('/api/audio/list');
    return response.data;
  }

  async getAudioMetadata(audioId: string) {
    const response = await this.client.get(`/api/audio/${audioId}`);
    return response.data;
  }

  async updateAudioMetadata(audioId: string, metadata: {
    title?: string;
    description?: string;
    artist?: string;
    album?: string;
    genre?: string;
  }) {
    const response = await this.client.put(`/api/audio/${audioId}`, metadata);
    return response.data;
  }

  async deleteAudio(audioId: string) {
    const response = await this.client.delete(`/api/audio/${audioId}`);
    return response.data;
  }

  async downloadAudio(audioId: string) {
    const response = await this.client.get(`/api/audio/${audioId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async convertAudioFormat(audioId: string, targetFormat: string, quality = 'high') {
    const response = await this.client.post(`/api/audio/${audioId}/convert`, {
      target_format: targetFormat,
      quality,
    });
    return response.data;
  }

  async analyzeAudio(audioId: string) {
    const response = await this.client.get(`/api/audio/${audioId}/analyze`);
    return response.data;
  }

  async getAudioStats() {
    const response = await this.client.get('/api/audio/stats/overview');
    return response.data;
  }

  async cleanupOldFiles(maxAgeDays = 30) {
    const response = await this.client.delete('/api/audio/cleanup', {
      params: { max_age_days: maxAgeDays },
    });
    return response.data;
  }

  // System APIs
  async getSystemResources() {
    const response = await this.client.get('/api/system/resources');
    return response.data;
  }

  async getSystemSettings() {
    const response = await this.client.get('/api/system/settings');
    return response.data;
  }

  async updateSystemSettings(settings: Record<string, any>) {
    const response = await this.client.put('/api/system/settings', settings);
    return response.data;
  }

  // Utility methods
  getAudioUrl(audioId: string) {
    return `${API_BASE_URL}/api/audio/${audioId}/download`;
  }

  async downloadFile(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  // Error handling utility
  handleApiError(error: AxiosError): string {
    if (error.response?.data) {
      const apiError = error.response.data as ApiError;
      return apiError.error?.message || 'An error occurred';
    }
    return error.message || 'Network error';
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;