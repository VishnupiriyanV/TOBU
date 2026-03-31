import { useState, useCallback } from 'react';
import { searchHybrid, searchSemantic, searchKeyword } from '../api';
import UniversalInspector from '../components/UniversalInspector';
import './SearchPage.css';

const SEARCH_MODES = ['hybrid', 'semantic', 'keyword'];

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
  const [showAll, setShowAll] = useState(false);

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
      setShowAll(false); // Reset on new search
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

  const allItems = results?.items || [];

  // Decide threshold based on search mode
  // Hybrid/Keyword score higher is better (RRF). Semantic distance lower is better.
  const threshold = mode === 'semantic' ? 1.0 : 0.01;

  const highItems = allItems.filter(item =>
    mode === 'semantic' ? item.score < threshold : item.score >= threshold
  );
  const lowItems = allItems.filter(item =>
    mode === 'semantic' ? item.score >= threshold : item.score < threshold
  );

  const displayedItems = showAll ? allItems : highItems;
  const hasHidden = lowItems.length > 0 && !showAll;

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

          {displayedItems.map((item, idx) => {
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

          {hasHidden && (
            <div className="search-show-more-area">
              <div className="search-relevancy-divider">
                <span>Potential Matches Hidden</span>
              </div>
              <button
                className="search-show-more-btn"
                onClick={() => setShowAll(true)}
              >
                <span className="material-symbols-outlined">expand_more</span>
                Show {lowItems.length} more results with lower relevancy
              </button>
            </div>
          )}

          {!loading && results && allItems.length === 0 && (
            <div className="search-empty">
              <span className="material-symbols-outlined" style={{ fontSize: 48, opacity: 0.15 }}>sentiment_dissatisfied</span>
              <p>No results found for "{query}". Try a different term or keyword.</p>
            </div>
          )}
        </div>
      </div>

      {/* Right Pane: Media Inspector */}
      <div className="search-inspector" style={{ overflow: 'hidden' }}>
        {selected != null && displayedItems[selected] ? (
          <UniversalInspector item={displayedItems[selected]} onClose={() => setSelected(null)} />
        ) : (
          <div className="search-empty" style={{ padding: '40px 20px', height: '100%' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 40, opacity: 0.15 }}>preview</span>
            <p>Select a result to inspect</p>
          </div>
        )}
      </div>
    </div>
  );
}


