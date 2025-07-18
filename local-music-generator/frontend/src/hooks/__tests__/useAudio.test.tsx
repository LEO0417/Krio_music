import { renderHook, act } from '@testing-library/react';
import { useAudio } from '../useAudio';

// Mock HTMLAudioElement
global.HTMLAudioElement = jest.fn().mockImplementation(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  play: jest.fn().mockResolvedValue(undefined),
  pause: jest.fn(),
  currentTime: 0,
  duration: 100,
  volume: 0.7,
  src: '',
}));

describe('useAudio Hook', () => {
  let mockAudio: any;

  beforeEach(() => {
    mockAudio = {
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      play: jest.fn().mockResolvedValue(undefined),
      pause: jest.fn(),
      currentTime: 0,
      duration: 100,
      volume: 0.7,
      src: '',
    };
    
    (global.HTMLAudioElement as jest.Mock).mockImplementation(() => mockAudio);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useAudio());
    
    expect(result.current.isPlaying).toBe(false);
    expect(result.current.currentTime).toBe(0);
    expect(result.current.duration).toBe(0);
    expect(result.current.volume).toBe(0.7);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('loads audio correctly', () => {
    const { result } = renderHook(() => useAudio());
    
    act(() => {
      result.current.loadAudio('test.mp3');
    });
    
    expect(global.HTMLAudioElement).toHaveBeenCalled();
    expect(mockAudio.src).toBe('test.mp3');
  });

  it('plays audio', async () => {
    const { result } = renderHook(() => useAudio());
    
    act(() => {
      result.current.loadAudio('test.mp3');
    });
    
    await act(async () => {
      result.current.play();
    });
    
    expect(mockAudio.play).toHaveBeenCalled();
  });

  it('pauses audio', () => {
    const { result } = renderHook(() => useAudio());
    
    act(() => {
      result.current.loadAudio('test.mp3');
    });
    
    act(() => {
      result.current.pause();
    });
    
    expect(mockAudio.pause).toHaveBeenCalled();
  });

  it('stops audio', () => {
    const { result } = renderHook(() => useAudio());
    
    act(() => {
      result.current.loadAudio('test.mp3');
    });
    
    act(() => {
      result.current.stop();
    });
    
    expect(mockAudio.pause).toHaveBeenCalled();
    expect(mockAudio.currentTime).toBe(0);
  });

  it('seeks to specific time', () => {
    const { result } = renderHook(() => useAudio());
    
    act(() => {
      result.current.loadAudio('test.mp3');
    });
    
    act(() => {
      result.current.seek(50);
    });
    
    expect(mockAudio.currentTime).toBe(50);
  });

  it('sets volume', () => {
    const { result } = renderHook(() => useAudio());
    
    act(() => {
      result.current.loadAudio('test.mp3');
    });
    
    act(() => {
      result.current.setVolume(0.5);
    });
    
    expect(mockAudio.volume).toBe(0.5);
  });

  it('clamps volume between 0 and 1', () => {
    const { result } = renderHook(() => useAudio());
    
    act(() => {
      result.current.loadAudio('test.mp3');
    });
    
    act(() => {
      result.current.setVolume(1.5);
    });
    
    expect(result.current.volume).toBe(1);
    
    act(() => {
      result.current.setVolume(-0.5);
    });
    
    expect(result.current.volume).toBe(0);
  });
});