import React from 'react';
import { ThemeProvider } from '@/context/ThemeContext';
import { AppStateProvider, useAppState } from '@/context/AppStateContext';
import Layout from '@/components/Layout';
import HomePage from '@/pages/HomePage';
import LibraryPage from '@/pages/LibraryPage';
import HistoryPage from '@/pages/HistoryPage';
import SettingsPage from '@/pages/SettingsPage';
import { PageTransition } from '@/components/animations';
import './styles/App.css';

const AppContent: React.FC = () => {
  const { state } = useAppState();
  
  const renderCurrentPage = () => {
    switch (state.currentPage) {
      case '/':
        return <HomePage />;
      case '/library':
        return <LibraryPage />;
      case '/history':
        return <HistoryPage />;
      case '/settings':
        return <SettingsPage />;
      default:
        return <HomePage />;
    }
  };

  return (
    <div className="app">
      <Layout>
        <PageTransition pageKey={state.currentPage} direction="fade">
          {renderCurrentPage()}
        </PageTransition>
      </Layout>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppStateProvider>
        <AppContent />
      </AppStateProvider>
    </ThemeProvider>
  );
};

export default App;