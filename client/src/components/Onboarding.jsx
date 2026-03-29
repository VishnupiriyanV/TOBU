import React, { useState, useEffect } from 'react';
import './Onboarding.css';

const Onboarding = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [modelStatus, setModelStatus] = useState({ semantic: false, visual: false, summarizer: false });
  const [isDownloading, setIsDownloading] = useState(false);
  const [watchFolder, setWatchFolder] = useState('');

  useEffect(() => {
    fetchModelStatus();
    const interval = setInterval(fetchModelStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchModelStatus = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/system/models/status');
      const data = await res.json();
      if (data.ok) {
        setModelStatus(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch model status', err);
    }
  };

  const handleDownloadModels = async () => {
    setIsDownloading(true);
    try {
      await fetch('http://127.0.0.1:8000/api/v1/system/models/download', { method: 'POST' });
    } catch (err) {
      console.error('Failed to start download', err);
    }
  };

  const handleBrowseFolder = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/system/browse-folder');
      const data = await res.json();
      if (data.ok && data.data.path) {
        setWatchFolder(data.data.path);
      }
    } catch (err) {
      console.error('Failed to browse folder', err);
    }
  };

  const handleFinish = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/v1/system/onboarding-completed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: true }),
      });
      onComplete();
    } catch (err) {
      console.error('Failed to complete onboarding', err);
    }
  };

  const allModelsReady = modelStatus.semantic && modelStatus.visual && modelStatus.summarizer;

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-card">
        <div className="onboarding-header">
          <div className="logo">TOBU</div>
          <div className="step-indicator">Step {step} of 4</div>
        </div>

        {step === 1 && (
          <div className="onboarding-step fade-in">
            <h1>Welcome to TOBU</h1>
            <p>The ultimate multimodal knowledge vault. Let's get you set up in a few seconds.</p>
            <div className="benefit-list">
              <div className="benefit-item">
                <span className="icon">🔍</span>
                <div>
                  <h3>Semantic Search</h3>
                  <p>Find what you need by meaning, not just keywords.</p>
                </div>
              </div>
              <div className="benefit-item">
                <span className="icon">🧠</span>
                <div>
                  <h3>Local AI</h3>
                  <p>Your data stays on your machine. Private and secure.</p>
                </div>
              </div>
            </div>
            <button className="primary-btn" onClick={() => setStep(2)}>Get Started</button>
          </div>
        )}

        {step === 2 && (
          <div className="onboarding-step fade-in">
            <h1>AI Model Setup</h1>
            <p>TOBU uses lightweight local models for indexing and search. We need to ensure they are downloaded.</p>
            
            <div className="model-list">
              <div className={`model-item ${modelStatus.semantic ? 'ready' : 'missing'}`}>
                <span>Semantic Model (Text)</span>
                <span className="status">{modelStatus.semantic ? 'Ready' : 'Missing'}</span>
              </div>
              <div className={`model-item ${modelStatus.visual ? 'ready' : 'missing'}`}>
                <span>Visual Model (CLIP)</span>
                <span className="status">{modelStatus.visual ? 'Ready' : 'Missing'}</span>
              </div>
              <div className={`model-item ${modelStatus.summarizer ? 'ready' : 'missing'}`}>
                <span>Summarization Model</span>
                <span className="status">{modelStatus.summarizer ? 'Ready' : 'Missing'}</span>
              </div>
            </div>

            {!allModelsReady && !isDownloading && (
              <button className="primary-btn" onClick={handleDownloadModels}>Download Models</button>
            )}
            {isDownloading && !allModelsReady && (
              <div className="downloading-state">
                <div className="loader"></div>
                <p>Downloading models in background... This may take a minute.</p>
              </div>
            )}
            {allModelsReady && (
              <div className="success-message">
                <p>✅ All models are ready!</p>
                <button className="primary-btn" onClick={() => setStep(3)}>Continue</button>
              </div>
            )}
          </div>
        )}

        {step === 3 && (
          <div className="onboarding-step fade-in">
            <h1>Where's your vault?</h1>
            <p>Select a folder where you store your media, notes, and documents. TOBU will watch this folder for changes.</p>
            
            <div className="folder-selector">
              <input type="text" readOnly value={watchFolder} placeholder="Select a folder..." />
              <button className="secondary-btn" onClick={handleBrowseFolder}>Browse</button>
            </div>

            <button 
              className="primary-btn" 
              disabled={!watchFolder} 
              onClick={() => setStep(4)}
            >
              Continue
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="onboarding-step fade-in">
            <h1>Ready to Roll!</h1>
            <p>You're all set. TOBU will now begin indexing your files. This happens entirely in the background.</p>
            <div className="final-check">
              <p>📍 Location: <code>{watchFolder}</code></p>
              <p>🤖 Models: <code>Optimized (Local)</code></p>
            </div>
            <button className="primary-btn finish-btn" onClick={handleFinish}>Enter TOBU</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Onboarding;
