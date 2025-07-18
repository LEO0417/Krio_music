import React from 'react';

const App: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Local Music Generator</h1>
      <p>Testing... If you can see this, React is working!</p>
      <div style={{ marginTop: '20px' }}>
        <button onClick={() => alert('Button clicked!')}>
          Test Button
        </button>
      </div>
    </div>
  );
};

export default App;