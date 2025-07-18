import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { useAppState } from '@/context/AppStateContext';
import { useApi } from '@/hooks/useApiActions';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import AudioPlayer from '@/components/AudioPlayer';

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-lg);
`;

const PageTitle = styled.h1`
  margin: 0 0 var(--spacing-lg) 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
`;

const HistoryHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
  gap: var(--spacing-md);
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: stretch;
  }
`;

const SearchInput = styled(Input)`
  max-width: 400px;
  
  @media (max-width: 768px) {
    max-width: none;
  }
`;

const HistoryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--spacing-lg);
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const HistoryItem = styled(Card)`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-large);
  }
`;

const ItemHeader = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
`;

const ItemTitle = styled.h3`
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
  flex: 1;
`;

const ItemDate = styled.span`
  font-size: 12px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
`;

const ItemPrompt = styled.p`
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const ItemMetadata = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  font-size: 12px;
  color: var(--color-text-tertiary);
`;

const MetadataItem = styled.span`
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
`;

const ItemActions = styled.div`
  display: flex;
  gap: var(--spacing-sm);
  margin-top: auto;
  
  /* Prevent event propagation to parent */
  & > * {
    position: relative;
    z-index: 1;
  }
`;

const AudioPlayerContainer = styled.div`
  margin-top: var(--spacing-md);
`;

const EmptyState = styled.div`
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
`;

const EmptyIcon = styled.div`
  font-size: 48px;
  margin-bottom: var(--spacing-md);
`;

const EmptyTitle = styled.h3`
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const EmptyDescription = styled.p`
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
`;

const LoadingContainer = styled.div`
  text-align: center;
  padding: 2rem;
`;

const ModalContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
`;

const ModalSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
`;

const ModalLabel = styled.label`
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
`;

const ModalValue = styled.div`
  font-size: 16px;
  color: var(--color-text-primary);
`;

const HistoryPage: React.FC = () => {
  const { state, dispatch } = useAppState();
  const { getGenerationHistory, deleteAudio } = useApi();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setIsLoading(true);
      const history = await getGenerationHistory();
      dispatch({ type: 'SET_GENERATION_HISTORY', payload: history });
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          type: 'error',
          title: 'Error',
          message: 'Failed to load generation history',
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const filteredHistory = state.generationHistory.filter(item =>
    item.prompt.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.task_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleItemClick = (item: any) => {
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (audioId: string) => {
    try {
      await deleteAudio(audioId);
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          type: 'success',
          title: 'Deleted',
          message: 'Audio file deleted successfully',
        },
      });
      loadHistory(); // Refresh history
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          type: 'error',
          title: 'Delete Failed',
          message: error instanceof Error ? error.message : 'Failed to delete audio',
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

  if (isLoading) {
    return (
      <PageContainer>
        <PageTitle>History</PageTitle>
        <LoadingContainer>
          Loading history...
        </LoadingContainer>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageTitle>History</PageTitle>
      
      <HistoryHeader>
        <SearchInput
          value={searchTerm}
          onChange={(value) => setSearchTerm(value)}
          placeholder="Search by prompt or task ID..."
        />
        
        <Button
          variant="secondary"
          onClick={loadHistory}
        >
          Refresh
        </Button>
      </HistoryHeader>
      
      {filteredHistory.length === 0 ? (
        <EmptyState>
          <EmptyIcon>🎵</EmptyIcon>
          <EmptyTitle>
            {searchTerm ? 'No matching results' : 'No music generated yet'}
          </EmptyTitle>
          <EmptyDescription>
            {searchTerm
              ? 'Try adjusting your search terms.'
              : 'Start by generating your first piece of music!'
            }
          </EmptyDescription>
        </EmptyState>
      ) : (
        <HistoryGrid>
          {filteredHistory.map((item) => (
            <HistoryItem
              key={item.task_id}
              as="div"
              onClick={() => handleItemClick(item)}
            >
              <ItemHeader>
                <ItemTitle>
                  {item.prompt.substring(0, 50)}
                  {item.prompt.length > 50 ? '...' : ''}
                </ItemTitle>
                <ItemDate>{formatDate(item.created_at)}</ItemDate>
              </ItemHeader>
              
              <ItemPrompt>{item.prompt}</ItemPrompt>
              
              <ItemMetadata>
                <MetadataItem>
                  <span>⏱️</span>
                  {formatDuration(item.duration || 0)}
                </MetadataItem>
                <MetadataItem>
                  <span>🎵</span>
                  {item.status}
                </MetadataItem>
              </ItemMetadata>
              
              {item.audio_url && (
                <AudioPlayerContainer>
                  <AudioPlayer
                    src={item.audio_url}
                    title={item.prompt.substring(0, 50) + (item.prompt.length > 50 ? '...' : '')}
                    onError={(error) => {
                      dispatch({
                        type: 'ADD_NOTIFICATION',
                        payload: {
                          type: 'error',
                          title: 'Playback Error',
                          message: error,
                        },
                      });
                    }}
                  />
                </AudioPlayerContainer>
              )}
              
              <ItemActions onClick={(e) => e.stopPropagation()}>
                {item.audio_url && (
                  <Button
                    variant="secondary"
                    size="small"
                    onClick={() => {
                      window.open(item.audio_url, '_blank');
                    }}
                  >
                    Download
                  </Button>
                )}
                
                <Button
                  variant="danger"
                  size="small"
                  onClick={() => {
                    handleDelete(item.task_id);
                  }}
                >
                  Delete
                </Button>
              </ItemActions>
            </HistoryItem>
          ))}
        </HistoryGrid>
      )}
      
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Generation Details"
        size="medium"
      >
        {selectedItem && (
          <ModalContent>
            <ModalSection>
              <ModalLabel>Task ID</ModalLabel>
              <ModalValue>{selectedItem.task_id}</ModalValue>
            </ModalSection>
            
            <ModalSection>
              <ModalLabel>Prompt</ModalLabel>
              <ModalValue>{selectedItem.prompt}</ModalValue>
            </ModalSection>
            
            <ModalSection>
              <ModalLabel>Status</ModalLabel>
              <ModalValue>{selectedItem.status}</ModalValue>
            </ModalSection>
            
            <ModalSection>
              <ModalLabel>Created</ModalLabel>
              <ModalValue>{formatDate(selectedItem.created_at)}</ModalValue>
            </ModalSection>
            
            {selectedItem.duration && (
              <ModalSection>
                <ModalLabel>Duration</ModalLabel>
                <ModalValue>{formatDuration(selectedItem.duration)}</ModalValue>
              </ModalSection>
            )}
            
            {selectedItem.audio_url && (
              <ModalSection>
                <ModalLabel>Audio</ModalLabel>
                <AudioPlayer
                  src={selectedItem.audio_url}
                  title={selectedItem.prompt}
                  onError={(error) => {
                    dispatch({
                      type: 'ADD_NOTIFICATION',
                      payload: {
                        type: 'error',
                        title: 'Playback Error',
                        message: error,
                      },
                    });
                  }}
                />
              </ModalSection>
            )}
          </ModalContent>
        )}
      </Modal>
    </PageContainer>
  );
};

export default HistoryPage;