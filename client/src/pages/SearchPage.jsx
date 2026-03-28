import { useState, useCallback } from 'react';
import { searchHybrid, searchSemantic, searchKeyword, getMediaServeUrl } from '../api';
import CustomPdfViewer from '../components/CustomPdfViewer';
import './SearchPage.css';

const SEARCH_MODES = ['hybrid', 'semantic', 'keyword'];

function formatTime(seconds) {
  if (seconds == null) return '';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function fileIcon(sourceType, fileName) {
  if (sourceType === 'video' || /\.(mp4|mkv|avi|mov|webm)$/i.test(fileName || ''))
    return { icon: 'video_library', color: '#60a5fa' };
  if (sourceType === 'pdf' || /\.pdf$/i.test(fileName || ''))
    return { icon: 'picture_as_pdf', color: '#f87171' };
  if (/\.(md|txt)$/i.test(fileName || ''))
    return { icon: 'description', color: '#fb923c' };
  return { icon: 'insert_drive_file', color: '#9ca3af' };
}

export default function SearchPage() {
  const [mode, setMode] = useState('hybrid');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  const doSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setSelected(null);
    try {
      let data;
      if (mode === 'hybrid') {
        data = await searchHybrid({ query, limit: 20 });
      } else if (mode === 'semantic') {
        data = await searchSemantic(query, 20);
      } else {
        data = await searchKeyword(query);
      }
      setResults(data);
    } catch (err) {
      const rawMsg = err.response?.data?.error?.message || err.response?.data?.detail || err.message || 'Search failed';
      const status = err.response?.status;
      // Friendlier messages for common errors
      if (status === 500 && (rawMsg.includes('unexpected') || rawMsg.includes('Internal'))) {
        setError('No indexed data found. Ingest some files first via the Ingest panel.');
      } else {
        setError(rawMsg);
      }
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, [query, mode]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') doSearch();
  };

  const items = results?.items || [];

  return (
    <div className="search-page">
      {/* Center: Search Results */}
      <div className="search-center">
        {/* Tabs */}
        <div className="search-tabs-bar">
          <nav className="search-tabs">
            {SEARCH_MODES.map((m) => (
              <button
                key={m}
                className={`search-tab ${mode === m ? 'search-tab--active' : ''}`}
                onClick={() => setMode(m)}
              >
                {m}
              </button>
            ))}
          </nav>
          <div className="search-tabs-meta font-mono">
            {results && <span>{results.count ?? items.length} Results Found</span>}
          </div>
        </div>

        {/* Search Input */}
        <div className="search-input-area">
          <div className="search-input-box">
            <span className="material-symbols-outlined search-input-icon">search</span>
            <input
              id="search-query-input"
              type="text"
              className="search-input"
              placeholder="Enter your search query..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>
          <button
            id="search-execute-btn"
            className="search-execute-btn"
            onClick={doSearch}
            disabled={loading || !query.trim()}
          >
            {loading ? 'Searching...' : 'Execute'}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="search-error">
            <span className="material-symbols-outlined">error</span>
            {error}
          </div>
        )}

        {/* Results */}
        <div className="search-results">
          {!results && !loading && !error && (
            <div className="search-empty">
              <span className="material-symbols-outlined" style={{ fontSize: 48, opacity: 0.15 }}>search</span>
              <p>Enter a query and press Execute to search your indexed files.</p>
            </div>
          )}

          {items.map((item, idx) => {
            const fi = fileIcon(item.source_type, item.file_name || item.file_path);
            const isSelected = selected === idx;
            return (
              <div
                key={idx}
                className={`search-result-card ${isSelected ? 'search-result-card--active' : ''}`}
                onClick={() => setSelected(idx)}
              >
                <div className="search-result-header">
                  <div className="search-result-title">
                    <span className="material-symbols-outlined" style={{ color: fi.color }}>{fi.icon}</span>
                    <h3>{item.file_name || item.file_path.split(/[/\\]/).pop()}</h3>
                  </div>
                  <span className="search-result-score font-mono">
                    Match Score: {item.score?.toFixed(2)}
                  </span>
                </div>
                {item.text && (
                  <p className="search-result-text">{item.text}</p>
                )}
                <div className="search-result-chips">
                  {item.matched_by?.length > 0 && (
                    <span className="search-chip font-mono">
                      {item.matched_by.join(' + ')}
                    </span>
                  )}
                  {item.source_type && (
                    <span className="search-chip font-mono">{item.source_type}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Pane: Media Inspector */}
      <div className="search-inspector">
        {selected != null && items[selected] && fileIcon(items[selected].source_type, items[selected].file_name || items[selected].file_path).icon === 'picture_as_pdf' ? (
          <CustomPdfViewer
            fileUrl={getMediaServeUrl(items[selected].file_path)}
            initialPage={items[selected].start != null ? Math.max(1, Math.floor(items[selected].start)) : 1}
            timestamp={items[selected].start}
            onClose={() => setSelected(null)}
          />
        ) : (
          <>
            <div className="search-inspector-body">
              {selected != null && items[selected] ? (
                <InspectorContent item={items[selected]} />
              ) : (
                <div className="search-empty" style={{ padding: '40px 20px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 40, opacity: 0.15 }}>preview</span>
                  <p>Select a result to inspect</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function InspectorContent({ item }) {
  const fi = fileIcon(item.source_type, item.file_name || item.file_path);
  const fileName = item.file_name || item.file_path.split(/[/\\]/).pop();
  const isVideo = fi.icon === 'video_library';

  return (
    <>
      {/* Video preview placeholder */}
      {isVideo && (
        <div className="inspector-video-hero">
          <div className="inspector-video-overlay">
            <div className="inspector-play-btn">
              <span className="material-symbols-outlined" style={{ fontSize: 32, fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
            </div>
          </div>
          {item.start != null && (
            <div className="inspector-video-controls">
              <div className="inspector-progress-bar">
                <div className="inspector-progress-fill" style={{ width: '33%' }} />
              </div>
              <div className="inspector-time-labels font-mono">
                <span>{formatTime(item.start)}</span>
                <span>{item.end != null ? formatTime(item.end) : '--:--'}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Segment / Transcript */}
      <div className="inspector-section">
        <h4 className="inspector-section-title">Content Detail</h4>
        <div className="inspector-segment">
          <div className="inspector-segment-header">
            <span className="font-mono" style={{color: 'var(--primary)', fontWeight: 700, fontSize: 10}}>
              {item.start != null ? `${formatTime(item.start)} - ${formatTime(item.end)}` : 'Full Document'}
            </span>
            <span className="inspector-segment-badge">{item.source_type || 'file'}</span>
          </div>
          {item.text && <p className="inspector-segment-text">{item.text}</p>}
        </div>
      </div>

      {/* Metadata */}
      <div className="inspector-section">
        <h4 className="inspector-section-title" style={{ color: 'var(--outline)' }}>Metadata</h4>
        <div className="inspector-meta-grid">
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">File</span>
            <span className="inspector-meta-value">{fileName}</span>
          </div>
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">Score</span>
            <span className="inspector-meta-value">{item.score?.toFixed(4)}</span>
          </div>
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">Matched By</span>
            <span className="inspector-meta-value">{item.matched_by?.join(', ') || '—'}</span>
          </div>
          {item.added_at && (
            <div className="inspector-meta-cell">
              <span className="inspector-meta-key">Added</span>
              <span className="inspector-meta-value">{item.added_at}</span>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
