import React from 'react';
import QuantumOrchestra from './components/QuantumOrchestra';

function App() {
  try {
    return <QuantumOrchestra />;
  } catch (error) {
    console.error('Error loading QuantumOrchestra:', error);
    return (
      <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
        <h1 style={{ color: '#6366f1' }}>Orquestra QRE</h1>
        <p>Quantum Resource Estimation Platform</p>
        <div style={{ margin: '20px 0', color: 'red' }}>
          <h2>⚠️ Component Loading Error</h2>
          <p>There was an error loading the main application. Check the console for details.</p>
          <details>
            <summary>Error Details</summary>
            <pre>{error?.toString()}</pre>
          </details>
        </div>
      </div>
    );
  }
}

export default App;
