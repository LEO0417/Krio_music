import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useAppState } from '@/context/AppStateContext';
import { Modal } from './ui/Modal';
import { Button } from './ui/Button';

interface KeyboardShortcutsProps {
  onGenerateMusic?: () => void;
  onToggleTheme?: () => void;
  onNavigateToLibrary?: () => void;
  onNavigateToHistory?: () => void;
  onNavigateToSettings?: () => void;
  onNavigateToHome?: () => void;
}

const ShortcutsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
`;

const ShortcutGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
`;

const GroupTitle = styled.h3`
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing-sm);
`;

const ShortcutItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
`;

const ShortcutDescription = styled.span`
  color: var(--color-text-secondary);
  font-size: 14px;
`;

const ShortcutKeys = styled.div`
  display: flex;
  gap: var(--spacing-xs);
  align-items: center;
`;

const KeyBadge = styled.span`
  background: var(--color-background-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 2px 8px;
  font-size: 12px;
  font-family: var(--font-family-mono);
  color: var(--color-text-primary);
  min-width: 24px;
  text-align: center;
`;

const PlusSign = styled.span`
  color: var(--color-text-tertiary);
  font-size: 12px;
`;

const HelpButton = styled(Button)`
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 100;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  
  @media (max-width: 768px) {
    bottom: 16px;
    right: 16px;
    width: 44px;
    height: 44px;
  }
`;

export const KeyboardShortcuts: React.FC<KeyboardShortcutsProps> = ({
  onGenerateMusic,
  onToggleTheme,
  onNavigateToLibrary,
  onNavigateToHistory,
  onNavigateToSettings,
  onNavigateToHome,
}) => {
  const { dispatch } = useAppState();
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  const shortcuts = [
    // Navigation shortcuts
    { key: '1', ctrlKey: true, action: onNavigateToHome || (() => dispatch({ type: 'SET_CURRENT_PAGE', payload: '/' })) },
    { key: '2', ctrlKey: true, action: onNavigateToLibrary || (() => dispatch({ type: 'SET_CURRENT_PAGE', payload: '/library' })) },
    { key: '3', ctrlKey: true, action: onNavigateToHistory || (() => dispatch({ type: 'SET_CURRENT_PAGE', payload: '/history' })) },
    { key: '4', ctrlKey: true, action: onNavigateToSettings || (() => dispatch({ type: 'SET_CURRENT_PAGE', payload: '/settings' })) },
    
    // App shortcuts
    { key: 'g', ctrlKey: true, action: onGenerateMusic || (() => {}) },
    { key: 't', ctrlKey: true, action: onToggleTheme || (() => {}) },
    { key: '/', action: () => setIsHelpOpen(true) },
    { key: 'Escape', action: () => setIsHelpOpen(false) },
  ];

  useKeyboardShortcuts(shortcuts);

  const shortcutGroups = [
    {
      title: 'Navigation',
      shortcuts: [
        { description: 'Go to Home', keys: ['Ctrl', '1'] },
        { description: 'Go to Library', keys: ['Ctrl', '2'] },
        { description: 'Go to History', keys: ['Ctrl', '3'] },
        { description: 'Go to Settings', keys: ['Ctrl', '4'] },
      ],
    },
    {
      title: 'Actions',
      shortcuts: [
        { description: 'Generate Music', keys: ['Ctrl', 'G'] },
        { description: 'Toggle Theme', keys: ['Ctrl', 'T'] },
        { description: 'Show Help', keys: ['/'] },
      ],
    },
    {
      title: 'Audio Player',
      shortcuts: [
        { description: 'Play/Pause', keys: ['Space'] },
        { description: 'Play/Pause', keys: ['K'] },
        { description: 'Stop', keys: ['S'] },
        { description: 'Volume Up', keys: ['↑'] },
        { description: 'Volume Down', keys: ['↓'] },
        { description: 'Seek Forward', keys: ['→'] },
        { description: 'Seek Backward', keys: ['←'] },
        { description: 'Mute/Unmute', keys: ['M'] },
      ],
    },
  ];

  return (
    <>
      <HelpButton
        variant="primary"
        onClick={() => setIsHelpOpen(true)}
        title="Keyboard Shortcuts (/)"
      >
        ?
      </HelpButton>

      <Modal
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
        title="Keyboard Shortcuts"
        size="medium"
      >
        <ShortcutsContainer>
          {shortcutGroups.map((group, index) => (
            <ShortcutGroup key={index}>
              <GroupTitle>{group.title}</GroupTitle>
              
              {group.shortcuts.map((shortcut, shortcutIndex) => (
                <ShortcutItem key={shortcutIndex}>
                  <ShortcutDescription>
                    {shortcut.description}
                  </ShortcutDescription>
                  
                  <ShortcutKeys>
                    {shortcut.keys.map((key, keyIndex) => (
                      <React.Fragment key={keyIndex}>
                        {keyIndex > 0 && <PlusSign>+</PlusSign>}
                        <KeyBadge>{key}</KeyBadge>
                      </React.Fragment>
                    ))}
                  </ShortcutKeys>
                </ShortcutItem>
              ))}
            </ShortcutGroup>
          ))}
        </ShortcutsContainer>
      </Modal>
    </>
  );
};