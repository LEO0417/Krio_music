import React from 'react';
import { Routes, Route } from 'react-router-dom';
import './styles/App.css';

// Import pages here when created
// import HomePage from './pages/HomePage';

const App: React.FC = () => {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<div>Local Music Generator</div>} />
        {/* Add more routes as needed */}
      </Routes>
    </div>
  );
};

export default App;