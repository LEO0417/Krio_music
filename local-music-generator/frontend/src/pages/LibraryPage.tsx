import React from 'react';
import styled from 'styled-components';
import AudioLibrary from '@/components/AudioLibrary';

const PageContainer = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-lg);
`;

const LibraryPage: React.FC = () => {
  return (
    <PageContainer>
      <AudioLibrary />
    </PageContainer>
  );
};

export default LibraryPage;