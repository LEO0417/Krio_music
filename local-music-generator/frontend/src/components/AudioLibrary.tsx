import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useAppState } from '@/context/AppStateContext';
import { useApi } from '@/hooks/useApiActions';
import { useDragAndDrop, reorderItems } from '@/hooks/useDragAndDrop';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Input } from './ui/Input';
import { Modal } from './ui/Modal';
import { DragDropItem } from './ui/DragDropItem';
import AudioPlayer from './AudioPlayer';

interface AudioItem {
  id: string;
  title: string;
  prompt: string;
  duration: number;
  created_at: string;
  audio_url: string;
  metadata?: {
    format: string;
    size: number;
    sample_rate: number;
  };
}

interface AudioLibraryProps {
  className?: string;
}

const LibraryContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
`;

const LibraryHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: stretch;
  }
`;

const LibraryTitle = styled.h2`
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
`;

const LibraryControls = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: stretch;
  }
`;

const SearchInput = styled(Input)`
  min-width: 300px;
  
  @media (max-width: 768px) {
    min-width: 0;
  }
`;

const FilterButtons = styled.div`
  display: flex;
  gap: var(--spacing-sm);
  
  @media (max-width: 768px) {
    flex-wrap: wrap;
  }
`;

const FilterButton = styled(Button)<{ active: boolean }>`
  background: ${props => props.active ? 'var(--color-primary)' : 'var(--color-background-secondary)'};
  color: ${props => props.active ? 'white' : 'var(--color-text-primary)'};
  border: 1px solid ${props => props.active ? 'var(--color-primary)' : 'var(--color-border)'};
`;

const AudioGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: var(--spacing-lg);
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const AudioCard = styled(Card)`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  transition: all var(--transition-normal);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-large);
  }
`;

const AudioCardHeader = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
`;

const AudioInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const AudioTitle = styled.h3`
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const AudioPrompt = styled.p`
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const AudioMetadata = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-sm);
  font-size: 12px;
  color: var(--color-text-tertiary);
`;

const MetadataItem = styled.span`
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
`;

const AudioActions = styled.div`
  display: flex;
  gap: var(--spacing-sm);
  flex-shrink: 0;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
`;

const EmptyIcon = styled.div`
  font-size: 64px;
  margin-bottom: var(--spacing-md);
`;

const EmptyTitle = styled.h3`
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const EmptyDescription = styled.p`
  margin: 0;
  font-size: 16px;
  line-height: 1.5;
`;

const EditModalContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
`;

const EditSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
`;

const EditLabel = styled.label`
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
`;

const LoadingState = styled.div`
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
`;

const AudioLibrary: React.FC<AudioLibraryProps> = ({ className }) => {
  const { state, dispatch } = useAppState();
  const { getAudioList, updateAudioMetadata, deleteAudio, downloadAudio } = useApi();
  
  const [audioItems, setAudioItems] = useState<AudioItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<AudioItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'duration' | 'custom'>('date');
  const [selectedItem, setSelectedItem] = useState<AudioItem | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState({ title: '', prompt: '' });
  const [isLoading, setIsLoading] = useState(true);
  const [customOrder, setCustomOrder] = useState<string[]>([]);

  useEffect(() => {
    loadAudioItems();
  }, []);

  useEffect(() => {
    filterAndSortItems();
  }, [audioItems, searchTerm, sortBy, customOrder]);

  const loadAudioItems = async () => {
    try {
      setIsLoading(true);
      const items = await getAudioList();
      setAudioItems(items);
      // Initialize custom order with item IDs
      if (customOrder.length === 0) {
        setCustomOrder(items.map(item => item.id));
      }
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: 'Failed to load audio library',
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const filterAndSortItems = () => {
    let filtered = audioItems.filter(item =>
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.prompt.toLowerCase().includes(searchTerm.toLowerCase())
    );

    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return a.title.localeCompare(b.title);
        case 'duration':
          return b.duration - a.duration;
        case 'custom':
          return customOrder.indexOf(a.id) - customOrder.indexOf(b.id);
        case 'date':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

    setFilteredItems(filtered);
  };

  const handleReorder = (dragIndex: number, hoverIndex: number) => {
    if (sortBy !== 'custom') {
      setSortBy('custom');
    }
    
    const newOrder = reorderItems(customOrder, dragIndex, hoverIndex);
    setCustomOrder(newOrder);
  };

  const { dragState, getDragHandleProps, getDropZoneProps } = useDragAndDrop({
    onReorder: handleReorder,
  });

  const handleEdit = (item: AudioItem) => {
    setSelectedItem(item);
    setEditForm({
      title: item.title,
      prompt: item.prompt,
    });
    setIsEditModalOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedItem) return;

    try {
      await updateAudioMetadata(selectedItem.id, {
        title: editForm.title,
        prompt: editForm.prompt,
      });

      setAudioItems(prev => prev.map(item => 
        item.id === selectedItem.id 
          ? { ...item, title: editForm.title, prompt: editForm.prompt }
          : item
      ));

      setIsEditModalOpen(false);
      setSelectedItem(null);

      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'success',
          title: 'Success',
          message: 'Audio metadata updated successfully',
        },
      });
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: 'Failed to update audio metadata',
        },
      });
    }
  };

  const handleDelete = async (item: AudioItem) => {
    if (!window.confirm('Are you sure you want to delete this audio file?')) {
      return;
    }

    try {
      await deleteAudio(item.id);
      setAudioItems(prev => prev.filter(audio => audio.id !== item.id));

      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'success',
          title: 'Success',
          message: 'Audio file deleted successfully',
        },
      });
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: 'Failed to delete audio file',
        },
      });
    }
  };

  const handleDownload = async (item: AudioItem) => {
    try {
      await downloadAudio(item.id);
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: 'Failed to download audio file',
        },
      });
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <LoadingState>
        <div>Loading audio library...</div>
      </LoadingState>
    );
  }

  return (
    <LibraryContainer className={className}>
      <LibraryHeader>
        <LibraryTitle>Audio Library</LibraryTitle>
        
        <LibraryControls>
          <SearchInput
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search audio files..."
          />
          
          <FilterButtons>
            <FilterButton
              active={sortBy === 'date'}
              onClick={() => setSortBy('date')}
              size="small"
            >
              Date
            </FilterButton>
            <FilterButton
              active={sortBy === 'title'}
              onClick={() => setSortBy('title')}
              size="small"
            >
              Title
            </FilterButton>
            <FilterButton
              active={sortBy === 'duration'}
              onClick={() => setSortBy('duration')}
              size="small"
            >
              Duration
            </FilterButton>
            <FilterButton
              active={sortBy === 'custom'}
              onClick={() => setSortBy('custom')}
              size="small"
            >
              Custom
            </FilterButton>
          </FilterButtons>
          
          <Button
            variant="secondary"
            onClick={loadAudioItems}
            size="small"
          >
            Refresh
          </Button>
        </LibraryControls>
      </LibraryHeader>

      {filteredItems.length === 0 ? (
        <EmptyState>
          <EmptyIcon>🎵</EmptyIcon>
          <EmptyTitle>
            {searchTerm ? 'No matching results' : 'No audio files yet'}
          </EmptyTitle>
          <EmptyDescription>
            {searchTerm
              ? 'Try adjusting your search terms.'
              : 'Generate some music to populate your library!'
            }
          </EmptyDescription>
        </EmptyState>
      ) : (
        <AudioGrid>
          {filteredItems.map((item, index) => {
            const dragItem = {
              id: item.id,
              index,
              type: 'audio-item',
            };
            
            return (
              <DragDropItem
                key={item.id}
                isDragging={dragState.dragItem?.id === item.id}
                isDragOver={dragState.dragOverIndex === index}
                dragHandleProps={getDragHandleProps(dragItem)}
                dropZoneProps={getDropZoneProps(dragItem)}
              >
                <AudioCard>
                  <AudioCardHeader>
                    <AudioInfo>
                      <AudioTitle>{item.title}</AudioTitle>
                      <AudioPrompt>{item.prompt}</AudioPrompt>
                      
                      <AudioMetadata>
                        <MetadataItem>
                          <span>⏱️</span>
                          {formatDuration(item.duration)}
                        </MetadataItem>
                        <MetadataItem>
                          <span>📅</span>
                          {formatDate(item.created_at)}
                        </MetadataItem>
                        {item.metadata && (
                          <MetadataItem>
                            <span>📦</span>
                            {formatFileSize(item.metadata.size)}
                          </MetadataItem>
                        )}
                      </AudioMetadata>
                    </AudioInfo>
                    
                    <AudioActions>
                      <Button
                        variant="secondary"
                        size="small"
                        onClick={() => handleEdit(item)}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="small"
                        onClick={() => handleDownload(item)}
                      >
                        Download
                      </Button>
                      <Button
                        variant="danger"
                        size="small"
                        onClick={() => handleDelete(item)}
                      >
                        Delete
                      </Button>
                    </AudioActions>
                  </AudioCardHeader>
                  
                  <AudioPlayer
                    src={item.audio_url}
                    title={item.title}
                    onError={(error) => {
                      dispatch({
                        type: 'ADD_NOTIFICATION',
                        payload: {
                          id: Date.now().toString(),
                          type: 'error',
                          title: 'Playback Error',
                          message: error,
                        },
                      });
                    }}
                  />
                </AudioCard>
              </DragDropItem>
            );
          })}
        </AudioGrid>
      )}

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Audio Metadata"
        size="medium"
        footer={
          <div style={{ display: 'flex', gap: '12px' }}>
            <Button
              variant="secondary"
              onClick={() => setIsEditModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveEdit}
            >
              Save Changes
            </Button>
          </div>
        }
      >
        <EditModalContent>
          <EditSection>
            <EditLabel>Title</EditLabel>
            <Input
              value={editForm.title}
              onChange={(e) => setEditForm(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Enter audio title"
            />
          </EditSection>
          
          <EditSection>
            <EditLabel>Prompt</EditLabel>
            <Input
              value={editForm.prompt}
              onChange={(e) => setEditForm(prev => ({ ...prev, prompt: e.target.value }))}
              placeholder="Enter generation prompt"
              multiline
              rows={4}
            />
          </EditSection>
        </EditModalContent>
      </Modal>
    </LibraryContainer>
  );
};

export default AudioLibrary;