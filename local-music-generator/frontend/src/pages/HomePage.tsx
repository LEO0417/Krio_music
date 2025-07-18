import React, { useState } from 'react';
import styled from 'styled-components';
import { useAppState } from '@/context/AppStateContext';
import { useApi } from '@/hooks/useApiActions';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Slider } from '@/components/ui/Slider';
import { Progress } from '@/components/ui/Progress';
import AudioPlayer from '@/components/AudioPlayer';
import { FadeIn, HoverEffect } from '@/components/animations';
import { Tooltip } from '@/components/ui/Tooltip';

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

const GenerationForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
`;

const FormSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
`;

const SectionTitle = styled.h3`
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const ParameterGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ParameterItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
`;

const ParameterLabel = styled.label`
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
`;

const GenerationStatus = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
`;

const StatusHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const StatusTitle = styled.h4`
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const StatusActions = styled.div`
  display: flex;
  gap: var(--spacing-sm);
`;

const AudioPreview = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
`;

const GeneratedAudioInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
`;

const AudioInfoItem = styled.div`
  font-size: 14px;
  color: var(--color-text-secondary);
  
  strong {
    color: var(--color-text-primary);
  }
`;

const HomePage: React.FC = () => {
  const { state, dispatch } = useAppState();
  const { generateMusic, cancelGeneration } = useApi();
  
  const [prompt, setPrompt] = useState('');
  const [parameters, setParameters] = useState({
    duration: 30,
    temperature: 0.7,
    top_k: 50,
    top_p: 0.9,
    guidance_scale: 7.5,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!prompt.trim()) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Error',
          message: 'Please enter a prompt for music generation',
        },
      });
      return;
    }

    try {
      const result = await generateMusic({
        prompt: prompt.trim(),
        ...parameters,
      });
      
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'success',
          title: 'Generation Started',
          message: `Started generating music with task ID: ${result.task_id}`,
        },
      });
    } catch (error) {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: Date.now().toString(),
          type: 'error',
          title: 'Generation Failed',
          message: error instanceof Error ? error.message : 'Unknown error occurred',
        },
      });
    }
  };

  const handleCancel = async () => {
    if (state.currentGeneration?.task_id) {
      try {
        await cancelGeneration(state.currentGeneration.task_id);
        dispatch({
          type: 'ADD_NOTIFICATION',
          payload: {
            id: Date.now().toString(),
            type: 'info',
            title: 'Generation Cancelled',
            message: 'Music generation has been cancelled',
          },
        });
      } catch (error) {
        dispatch({
          type: 'ADD_NOTIFICATION',
          payload: {
            id: Date.now().toString(),
            type: 'error',
            title: 'Cancel Failed',
            message: error instanceof Error ? error.message : 'Failed to cancel generation',
          },
        });
      }
    }
  };

  const isGenerating = state.currentGeneration?.status === 'processing';
  const canGenerate = state.modelStatus?.status === 'loaded' && !isGenerating;

  return (
    <PageContainer>
      <FadeIn direction="up" delay={0}>
        <PageTitle>Generate Music</PageTitle>
      </FadeIn>
      
      <FadeIn direction="up" delay={100}>
        <Card>
        <GenerationForm onSubmit={handleSubmit}>
          <FormSection>
            <SectionTitle>Music Description</SectionTitle>
            <Input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the music you want to generate (e.g., 'upbeat jazz piano with drums')"
              multiline
              rows={4}
              disabled={isGenerating}
            />
          </FormSection>
          
          <FormSection>
            <SectionTitle>Generation Parameters</SectionTitle>
            <ParameterGrid>
              <ParameterItem>
                <ParameterLabel>Duration (seconds)</ParameterLabel>
                <Tooltip content="Length of the generated music in seconds (10-120)">
                  <Slider
                    value={parameters.duration}
                    onChange={(value) => setParameters(prev => ({ ...prev, duration: value }))}
                    min={10}
                    max={120}
                    step={5}
                    disabled={isGenerating}
                  />
                </Tooltip>
              </ParameterItem>
              
              <ParameterItem>
                <ParameterLabel>Creativity (Temperature)</ParameterLabel>
                <Tooltip content="Controls randomness in generation. Lower values produce more predictable results">
                  <Slider
                    value={parameters.temperature}
                    onChange={(value) => setParameters(prev => ({ ...prev, temperature: value }))}
                    min={0.1}
                    max={1.0}
                    step={0.1}
                    disabled={isGenerating}
                  />
                </Tooltip>
              </ParameterItem>
              
              <ParameterItem>
                <ParameterLabel>Top K</ParameterLabel>
                <Slider
                  value={parameters.top_k}
                  onChange={(value) => setParameters(prev => ({ ...prev, top_k: value }))}
                  min={1}
                  max={100}
                  step={1}
                  disabled={isGenerating}
                />
              </ParameterItem>
              
              <ParameterItem>
                <ParameterLabel>Top P</ParameterLabel>
                <Slider
                  value={parameters.top_p}
                  onChange={(value) => setParameters(prev => ({ ...prev, top_p: value }))}
                  min={0.1}
                  max={1.0}
                  step={0.1}
                  disabled={isGenerating}
                />
              </ParameterItem>
              
              <ParameterItem>
                <ParameterLabel>Guidance Scale</ParameterLabel>
                <Slider
                  value={parameters.guidance_scale}
                  onChange={(value) => setParameters(prev => ({ ...prev, guidance_scale: value }))}
                  min={1.0}
                  max={15.0}
                  step={0.5}
                  disabled={isGenerating}
                />
              </ParameterItem>
            </ParameterGrid>
          </FormSection>
          
          <HoverEffect effect="lift">
            <Button
              type="submit"
              variant="primary"
              disabled={!canGenerate}
              loading={isGenerating}
            >
              {isGenerating ? 'Generating...' : 'Generate Music'}
            </Button>
          </HoverEffect>
        </GenerationForm>
        </Card>
      </FadeIn>
      
      {state.currentGeneration && (
        <FadeIn direction="up" delay={200}>
          <Card>
            <GenerationStatus>
            <StatusHeader>
              <StatusTitle>Generation Progress</StatusTitle>
              <StatusActions>
                {isGenerating && (
                  <Button
                    variant="danger"
                    size="small"
                    onClick={handleCancel}
                  >
                    Cancel
                  </Button>
                )}
              </StatusActions>
            </StatusHeader>
            
            <Progress
              value={state.currentGeneration.progress || 0}
              max={100}
              variant={state.currentGeneration.status === 'error' ? 'error' : 'primary'}
            />
            
            <div>
              <strong>Status:</strong> {state.currentGeneration.status}
              {state.currentGeneration.message && (
                <div style={{ marginTop: '8px', color: 'var(--color-text-secondary)' }}>
                  {state.currentGeneration.message}
                </div>
              )}
            </div>
          </GenerationStatus>
          </Card>
        </FadeIn>
      )}
      
      {state.currentGeneration?.status === 'completed' && state.currentGeneration.result && (
        <FadeIn direction="up" delay={300}>
          <Card>
            <AudioPreview>
            <SectionTitle>Generated Music</SectionTitle>
            
            <GeneratedAudioInfo>
              <AudioInfoItem>
                <strong>Prompt:</strong> {state.currentGeneration.result.prompt}
              </AudioInfoItem>
              
              {state.currentGeneration.result.metadata && (
                <AudioInfoItem>
                  <strong>Duration:</strong> {state.currentGeneration.result.metadata.duration}s
                </AudioInfoItem>
              )}
            </GeneratedAudioInfo>
            
            <AudioPlayer
              src={state.currentGeneration.result.audio_url}
              title={`Generated: ${state.currentGeneration.result.prompt.substring(0, 50)}...`}
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
            </AudioPreview>
          </Card>
        </FadeIn>
      )}
    </PageContainer>
  );
};

export default HomePage;