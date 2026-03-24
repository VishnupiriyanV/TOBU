import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import SearchPage from './pages/SearchPage';
import JobsPage from './pages/JobsPage';
import IngestPage from './pages/IngestPage';
import SystemPage from './pages/SystemPage';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<SearchPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/ingest" element={<IngestPage />} />
          <Route path="/system" element={<SystemPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
