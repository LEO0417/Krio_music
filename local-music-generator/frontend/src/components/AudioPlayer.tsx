import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import styled from 'styled-components';
import { useAudio } from '@/hooks/useAudio';
import { useKeyboardShortcuts, createAudioPlayerShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useThrottledCallback } from '@/hooks/usePerformance';
import { Button } from './ui/Button';
import { Slider } from './ui/Slider';

interface AudioPlayerProps {
  src: string;
  title?: string;
  onError?: (error: string) => void;
  onLoadStart?: () => void;
  onLoadEnd?: () => void;
  className?: string;
}

const PlayerContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  background: var(--color-background-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
`;

const PlayerHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
`;

const PlayerTitle = styled.h3`
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const PlayerControls = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
`;

const PlayButton = styled(Button)`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  padding: 0;
`;

const TimeDisplay = styled.div`
  font-size: 14px;
  color: var(--color-text-secondary);
  font-family: var(--font-family-mono);
  min-width: 80px;
  text-align: center;
`;

const ProgressSection = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
`;

const ProgressContainer = styled.div`
  flex: 1;
  position: relative;
`;

const ProgressTrack = styled.div`
  width: 100%;
  height: 6px;
  background: var(--color-background-tertiary);
  border-radius: var(--radius-full);
  position: relative;
  cursor: pointer;
  transition: all var(--transition-normal);
  
  &:hover {
    transform: scaleY(1.2);
  }
`;

const ProgressBar = styled.div<{ progress: number }>`
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  width: ${props => props.progress}%;
  transition: width 0.1s ease;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    right: -2px;
    top: 50%;
    transform: translateY(-50%);
    width: 14px;
    height: 14px;
    background: var(--color-primary);
    border-radius: 50%;
    opacity: 0;
    transition: opacity var(--transition-normal);
    box-shadow: 0 0 0 2px var(--color-background-primary);
  }
  
  ${ProgressTrack}:hover &::after {
    opacity: 1;
  }
`;

const VolumeSection = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const VolumeIcon = styled.button`
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 18px;
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  transition: all var(--transition-normal);
  
  &:hover {
    color: var(--color-text-primary);
    background: var(--color-background-hover);
  }
`;

const VolumeSlider = styled.div`
  width: 80px;
`;

const WaveformContainer = styled.div`
  height: 60px;
  background: var(--color-background-tertiary);
  border-radius: var(--radius-md);
  position: relative;
  overflow: hidden;
  margin-top: var(--spacing-sm);
`;

const WaveformPlaceholder = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  font-size: 12px;
`;

const LoadingSpinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-text-tertiary);
  border-top: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const AudioPlayer: React.FC<AudioPlayerProps> = memo(({
  src,
  title,
  onError,
  onLoadStart,
  onLoadEnd,
  className,
}) => {
  const {
    isPlaying,
    currentTime,
    duration,
    volume,
    isLoading,
    error,
    play,
    pause,
    stop,
    seek,
    setVolume,
    loadAudio,
  } = useAudio();

  const [isMuted, setIsMuted] = useState(false);
  const [previousVolume, setPreviousVolume] = useState(0.7);
  const [isFocused, setIsFocused] = useState(false);
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (src) {
      if (onLoadStart) onLoadStart();
      loadAudio(src);
    }
  }, [src, loadAudio, onLoadStart]);

  useEffect(() => {
    if (!isLoading && onLoadEnd) {
      onLoadEnd();
    }
  }, [isLoading, onLoadEnd]);

  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  const handlePlayPause = () => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  };

  const handleProgressClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (progressRef.current && duration > 0) {
      const rect = progressRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const newTime = (clickX / rect.width) * duration;
      seek(newTime);
    }
  }, [duration, seek]);

  const handleVolumeToggle = useCallback(() => {
    if (isMuted) {
      setVolume(previousVolume);
      setIsMuted(false);
    } else {
      setPreviousVolume(volume);
      setVolume(0);
      setIsMuted(true);
    }
  }, [isMuted, previousVolume, volume, setVolume]);

  const handleVolumeChange = useThrottledCallback((newVolume: number) => {
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
    if (newVolume > 0) {
      setPreviousVolume(newVolume);
    }
  }, 50);

  const handleSeekForward = () => {
    if (duration > 0) {
      const newTime = Math.min(currentTime + 10, duration);
      seek(newTime);
    }
  };

  const handleSeekBackward = () => {
    if (duration > 0) {
      const newTime = Math.max(currentTime - 10, 0);
      seek(newTime);
    }
  };

  const handleVolumeUp = () => {
    const newVolume = Math.min(volume + 0.1, 1);
    setVolume(newVolume);
  };

  const handleVolumeDown = () => {
    const newVolume = Math.max(volume - 0.1, 0);
    setVolume(newVolume);
  };

  // Keyboard shortcuts
  useKeyboardShortcuts(
    isFocused ? createAudioPlayerShortcuts({
      play: handlePlayPause,
      pause: handlePlayPause,
      stop: stop,
      volumeUp: handleVolumeUp,
      volumeDown: handleVolumeDown,
      seekForward: handleSeekForward,
      seekBackward: handleSeekBackward,
      toggleMute: handleVolumeToggle,
    }) : []
  );

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getVolumeIcon = () => {
    if (isMuted || volume === 0) return '🔇';
    if (volume < 0.3) return '🔈';
    if (volume < 0.7) return '🔉';
    return '🔊';
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <PlayerContainer 
      className={className}
      tabIndex={0}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      style={{ 
        outline: isFocused ? '2px solid var(--color-primary)' : 'none',
        outlineOffset: '2px'
      }}
    >
      <PlayerHeader>
        <PlayerTitle>{title || 'Audio Player'}</PlayerTitle>
        <PlayerControls>
          <PlayButton
            variant="primary"
            onClick={handlePlayPause}
            disabled={isLoading || !!error}
          >
            {isLoading ? (
              <LoadingSpinner />
            ) : isPlaying ? (
              '⏸️'
            ) : (
              '▶️'
            )}
          </PlayButton>
          
          <Button
            variant="secondary"
            size="small"
            onClick={stop}
            disabled={isLoading || !!error}
          >
            ⏹️
          </Button>
        </PlayerControls>
      </PlayerHeader>

      <ProgressSection>
        <TimeDisplay>
          {formatTime(currentTime)}
        </TimeDisplay>
        
        <ProgressContainer>
          <ProgressTrack ref={progressRef} onClick={handleProgressClick}>
            <ProgressBar progress={progress} />
          </ProgressTrack>
        </ProgressContainer>
        
        <TimeDisplay>
          {formatTime(duration)}
        </TimeDisplay>
      </ProgressSection>

      <VolumeSection>
        <VolumeIcon onClick={handleVolumeToggle}>
          {getVolumeIcon()}
        </VolumeIcon>
        <VolumeSlider>
          <Slider
            value={volume}
            onChange={handleVolumeChange}
            min={0}
            max={1}
            step={0.1}
            disabled={isLoading}
          />
        </VolumeSlider>
      </VolumeSection>

      <WaveformContainer>
        <WaveformPlaceholder>
          {isLoading ? 'Loading waveform...' : 'Audio waveform visualization'}
        </WaveformPlaceholder>
      </WaveformContainer>

      {error && (
        <div style={{ 
          color: 'var(--color-danger)', 
          fontSize: '14px',
          textAlign: 'center',
          padding: 'var(--spacing-sm)'
        }}>
          {error}
        </div>
      )}
    </PlayerContainer>
  );
});

export default AudioPlayer;