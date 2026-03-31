import { HashRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import SearchPage from './pages/SearchPage';
import JobsPage from './pages/JobsPage';
import IngestPage from './pages/IngestPage';
import SystemPage from './pages/SystemPage';
import Onboarding from './components/Onboarding';
import React, { useState, useEffect } from 'react';
import './App.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', color: 'white' }}>
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>Try Again</button>
        </div>
      );
    }
    return this.props.children;
  }
}


function App() {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkOnboarding();
  }, []);

  const checkOnboarding = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/system/onboarding-status');
      const data = await res.json();
      if (data.ok) {
        setShowOnboarding(!data.data.completed);
      }
    } catch (err) {
      console.error('Failed to check onboarding status', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="app-loader">Loading TOBU...</div>;

  return (
    <HashRouter>
      {showOnboarding && <Onboarding onComplete={() => setShowOnboarding(false)} />}
      <ErrorBoundary>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<SearchPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/ingest" element={<IngestPage />} />
            <Route path="/system" element={<SystemPage />} />
          </Route>
        </Routes>
      </ErrorBoundary>
    </HashRouter>
  );
}

export default App;
