import React, { createContext, useContext, useReducer, ReactNode } from 'react';

// Types
export interface GenerationTask {
  id: string;
  task_id: string;
  prompt: string;
  parameters: Record<string, any>;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  result_path?: string;
  audio_url?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  estimated_time: number;
  duration?: number;
}

export interface AudioMetadata {
  id: string;
  title: string;
  description: string;
  artist: string;
  album: string;
  genre: string;
  duration: number;
  sample_rate: number;
  channels: number;
  format: string;
  file_size: number;
  file_path: string;
  created_at: string;
  prompt: string;
  parameters: Record<string, any>;
  checksum: string;
}

export interface ModelStatus {
  name: string;
  status: string;
  loaded_at?: string;
  error_message?: string;
  device: string;
  memory_usage_mb: number;
  inference_count: number;
  last_inference_time?: string;
  model_size_mb: number;
}

export interface SystemResources {
  cpu: { usage: number; cores: number };
  memory: { total: number; used: number; free: number };
  gpu?: { name: string; memory_total: number; memory_used: number; utilization: number };
  disk: { total: number; used: number; free: number };
}

interface AppState {
  // Model state
  modelStatus: ModelStatus | null;
  modelLoading: boolean;
  
  // Generation state
  currentTask: GenerationTask | null;
  activeTasks: GenerationTask[];
  taskHistory: GenerationTask[];
  generationHistory: GenerationTask[];
  generationLoading: boolean;
  
  // Audio state
  audioList: AudioMetadata[];
  currentAudio: AudioMetadata | null;
  audioLoading: boolean;
  
  // System state
  systemResources: SystemResources | null;
  
  // UI state
  sidebarOpen: boolean;
  notifications: Notification[];
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  duration?: number;
}

// Actions
type AppAction =
  | { type: 'SET_MODEL_STATUS'; payload: ModelStatus | null }
  | { type: 'SET_MODEL_LOADING'; payload: boolean }
  | { type: 'SET_CURRENT_TASK'; payload: GenerationTask | null }
  | { type: 'SET_ACTIVE_TASKS'; payload: GenerationTask[] }
  | { type: 'SET_TASK_HISTORY'; payload: GenerationTask[] }
  | { type: 'SET_GENERATION_HISTORY'; payload: GenerationTask[] }
  | { type: 'SET_GENERATION_LOADING'; payload: boolean }
  | { type: 'SET_AUDIO_LIST'; payload: AudioMetadata[] }
  | { type: 'SET_CURRENT_AUDIO'; payload: AudioMetadata | null }
  | { type: 'SET_AUDIO_LOADING'; payload: boolean }
  | { type: 'SET_SYSTEM_RESOURCES'; payload: SystemResources | null }
  | { type: 'SET_SIDEBAR_OPEN'; payload: boolean }
  | { type: 'ADD_NOTIFICATION'; payload: Omit<Notification, 'id' | 'timestamp'> }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'UPDATE_TASK'; payload: GenerationTask }
  | { type: 'ADD_AUDIO'; payload: AudioMetadata }
  | { type: 'UPDATE_AUDIO'; payload: AudioMetadata }
  | { type: 'REMOVE_AUDIO'; payload: string };

// Initial state
const initialState: AppState = {
  modelStatus: null,
  modelLoading: false,
  currentTask: null,
  activeTasks: [],
  taskHistory: [],
  generationHistory: [],
  generationLoading: false,
  audioList: [],
  currentAudio: null,
  audioLoading: false,
  systemResources: null,
  sidebarOpen: false,
  notifications: [],
};

// Reducer
const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_MODEL_STATUS':
      return { ...state, modelStatus: action.payload };
    case 'SET_MODEL_LOADING':
      return { ...state, modelLoading: action.payload };
    case 'SET_CURRENT_TASK':
      return { ...state, currentTask: action.payload };
    case 'SET_ACTIVE_TASKS':
      return { ...state, activeTasks: action.payload };
    case 'SET_TASK_HISTORY':
      return { ...state, taskHistory: action.payload };
    case 'SET_GENERATION_HISTORY':
      return { ...state, generationHistory: action.payload };
    case 'SET_GENERATION_LOADING':
      return { ...state, generationLoading: action.payload };
    case 'SET_AUDIO_LIST':
      return { ...state, audioList: action.payload };
    case 'SET_CURRENT_AUDIO':
      return { ...state, currentAudio: action.payload };
    case 'SET_AUDIO_LOADING':
      return { ...state, audioLoading: action.payload };
    case 'SET_SYSTEM_RESOURCES':
      return { ...state, systemResources: action.payload };
    case 'SET_SIDEBAR_OPEN':
      return { ...state, sidebarOpen: action.payload };
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [
          ...state.notifications,
          {
            ...action.payload,
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
          },
        ],
      };
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };
    case 'UPDATE_TASK':
      return {
        ...state,
        activeTasks: state.activeTasks.map(task =>
          task.id === action.payload.id ? action.payload : task
        ),
        currentTask: state.currentTask?.id === action.payload.id ? action.payload : state.currentTask,
      };
    case 'ADD_AUDIO':
      return {
        ...state,
        audioList: [action.payload, ...state.audioList],
      };
    case 'UPDATE_AUDIO':
      return {
        ...state,
        audioList: state.audioList.map(audio =>
          audio.id === action.payload.id ? action.payload : audio
        ),
        currentAudio: state.currentAudio?.id === action.payload.id ? action.payload : state.currentAudio,
      };
    case 'REMOVE_AUDIO':
      return {
        ...state,
        audioList: state.audioList.filter(audio => audio.id !== action.payload),
        currentAudio: state.currentAudio?.id === action.payload ? null : state.currentAudio,
      };
    default:
      return state;
  }
};

// Context
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppStateContext = createContext<AppContextType | undefined>(undefined);

export const useAppState = () => {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within an AppStateProvider');
  }
  return context;
};

interface AppStateProviderProps {
  children: ReactNode;
}

export const AppStateProvider: React.FC<AppStateProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppStateContext.Provider value={{ state, dispatch }}>
      {children}
    </AppStateContext.Provider>
  );
};