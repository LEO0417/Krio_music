import { useState, useRef, useCallback, useEffect } from 'react';

interface AudioState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isLoading: boolean;
  error: string | null;
}

interface AudioActions {
  play: () => void;
  pause: () => void;
  stop: () => void;
  seek: (time: number) => void;
  setVolume: (volume: number) => void;
  loadAudio: (src: string) => void;
}

export function useAudio(): AudioState & AudioActions {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<AudioState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 0.7,
    isLoading: false,
    error: null,
  });

  const updateState = useCallback((updates: Partial<AudioState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const loadAudio = useCallback((src: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }

    updateState({ isLoading: true, error: null });

    const audio = new Audio(src);
    audioRef.current = audio;

    audio.addEventListener('loadedmetadata', () => {
      updateState({
        isLoading: false,
        duration: audio.duration,
        currentTime: 0,
      });
    });

    audio.addEventListener('timeupdate', () => {
      updateState({ currentTime: audio.currentTime });
    });

    audio.addEventListener('ended', () => {
      updateState({ isPlaying: false, currentTime: 0 });
    });

    audio.addEventListener('error', (e) => {
      updateState({
        isLoading: false,
        error: 'Failed to load audio',
      });
    });

    audio.volume = state.volume;
  }, [state.volume, updateState]);

  const play = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.play()
        .then(() => updateState({ isPlaying: true }))
        .catch((error) => updateState({ error: 'Failed to play audio' }));
    }
  }, [updateState]);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      updateState({ isPlaying: false });
    }
  }, [updateState]);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      updateState({ isPlaying: false, currentTime: 0 });
    }
  }, [updateState]);

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      updateState({ currentTime: time });
    }
  }, [updateState]);

  const setVolume = useCallback((volume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    if (audioRef.current) {
      audioRef.current.volume = clampedVolume;
    }
    updateState({ volume: clampedVolume });
  }, [updateState]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return {
    ...state,
    play,
    pause,
    stop,
    seek,
    setVolume,
    loadAudio,
  };
}