import { useEffect } from 'react';

interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  action: () => void;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const matchingShortcut = shortcuts.find(shortcut => {
        return (
          shortcut.key.toLowerCase() === event.key.toLowerCase() &&
          (shortcut.ctrlKey || false) === event.ctrlKey &&
          (shortcut.altKey || false) === event.altKey &&
          (shortcut.shiftKey || false) === event.shiftKey
        );
      });

      if (matchingShortcut) {
        event.preventDefault();
        matchingShortcut.action();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
};

// Common shortcuts for audio players
export const createAudioPlayerShortcuts = (audioControls: {
  play: () => void;
  pause: () => void;
  stop: () => void;
  volumeUp: () => void;
  volumeDown: () => void;
  seekForward: () => void;
  seekBackward: () => void;
  toggleMute: () => void;
}) => {
  return [
    { key: ' ', action: audioControls.play }, // Spacebar for play/pause
    { key: 'k', action: audioControls.play }, // K for play/pause (YouTube style)
    { key: 's', action: audioControls.stop }, // S for stop
    { key: 'ArrowUp', action: audioControls.volumeUp }, // Up arrow for volume up
    { key: 'ArrowDown', action: audioControls.volumeDown }, // Down arrow for volume down
    { key: 'ArrowRight', action: audioControls.seekForward }, // Right arrow for seek forward
    { key: 'ArrowLeft', action: audioControls.seekBackward }, // Left arrow for seek backward
    { key: 'm', action: audioControls.toggleMute }, // M for mute/unmute
  ];
};