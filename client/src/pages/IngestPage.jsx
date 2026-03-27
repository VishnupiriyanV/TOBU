import { useState } from 'react';
import { ingestFile, ingestFolder, reindexFile, deleteFile, browseFile, browseFolder } from '../api';
import './IngestPage.css';

export default function IngestPage() {
  const [filePath, setFilePath] = useState('');
  const [sourceType, setSourceType] = useState('video');
  const [folderPath, setFolderPath] = useState('');
  const [recursive, setRecursive] = useState(true);
  const [reindexPath, setReindexPath] = useState('');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(null); // 'file' | 'folder' | 'reindex' | 'delete'

  const addLog = (type, message) => {
    const ts = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev, { type, message, ts }]);
  };

  const handleIngestFile = async () => {
    if (!filePath.trim()) return;
    setLoading('file');
    addLog('SYSTEM', `Ingesting file: ${filePath}`);
    try {
      const data = await ingestFile(filePath, sourceType);
      addLog('SUCCESS', `Job created → ID: ${data.job_id}, new: ${data.created}`);
    } catch (err) {
      addLog('ERROR', `Failed: ${err.response?.data?.error?.message || err.message}`);
    } finally {
      setLoading(null);
    }
  };

  const handleIngestFolder = async () => {
    if (!folderPath.trim()) return;
    setLoading('folder');
    addLog('SYSTEM', `Scanning folder: ${folderPath} (recursive: ${recursive})`);
    try {
      const data = await ingestFolder(folderPath, recursive);
      addLog('SUCCESS', `Queued: ${data.queued}, Skipped duplicates: ${data.skipped_duplicates}`);
    } catch (err) {
      addLog('ERROR', `Failed: ${err.response?.data?.error?.message || err.message}`);
    } finally {
      setLoading(null);
    }
  };

  const handleReindex = async () => {
    if (!reindexPath.trim()) return;
    setLoading('reindex');
    addLog('SYSTEM', `Reindexing: ${reindexPath}`);
    try {
      const data = await reindexFile(reindexPath);
      addLog('SUCCESS', `Reindex job created → ID: ${data.job_id}`);
    } catch (err) {
      addLog('ERROR', `Failed: ${err.response?.data?.error?.message || err.message}`);
    } finally {
      setLoading(null);
    }
  };

  const handleDelete = async () => {
    if (!reindexPath.trim()) return;
    setLoading('delete');
    addLog('SYSTEM', `Deleting records for: ${reindexPath}`);
    try {
      await deleteFile(reindexPath);
      addLog('SUCCESS', `Deleted all records for ${reindexPath}`);
    } catch (err) {
      addLog('ERROR', `Failed: ${err.response?.data?.error?.message || err.message}`);
    } finally {
      setLoading(null);
    }
  };

  const handleBrowseFileForIngest = async () => {
    try {
      const res = await browseFile();
      if (res.path) setFilePath(res.path);
    } catch (err) { console.error("Browse file failed", err); }
  };

  const handleBrowseFolderForIngest = async () => {
    try {
      const res = await browseFolder();
      if (res.path) setFolderPath(res.path);
    } catch (err) { console.error("Browse folder failed", err); }
  };

  const handleBrowseFileForReindex = async () => {
    try {
      const res = await browseFile();
      if (res.path) setReindexPath(res.path);
    } catch (err) { console.error("Browse file failed", err); }
  };


  return (
    <div className="ingest-page">
      {/* Controls Pane */}
      <div className="ingest-controls">
        <div className="ingest-controls-header font-mono">
          <span>Workspace Controls</span>
        </div>
        <div className="ingest-controls-body">
          {/* File Ingest */}
          <div className="ingest-section">
            <div className="ingest-upload-zone">
              <span className="material-symbols-outlined" style={{ fontSize: 28, color: 'rgba(201,191,255,0.3)' }}>upload_file</span>
              <h3 className="ingest-upload-title font-mono">FILE_INGEST</h3>
              <p className="ingest-upload-sub font-mono">Enter file path to ingest</p>
            </div>

            <div className="ingest-field">
              <label className="ingest-label font-mono">File Path</label>
              <input
                id="ingest-file-path"
                type="text"
                className="ingest-input font-mono"
                placeholder="Click to browse or enter path manually..."
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                onClick={handleBrowseFileForIngest}
                style={{ cursor: 'pointer' }}
              />
            </div>

            <div className="ingest-field">
              <label className="ingest-label font-mono">Source Type</label>
              <select
                id="ingest-source-type"
                className="ingest-select font-mono"
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
              >
                <option value="video">VIDEO</option>
                <option value="pdf">PDF</option>
                <option value="document">DOCUMENT</option>
              </select>
            </div>

            <button
              id="ingest-file-btn"
              className="ingest-btn"
              onClick={handleIngestFile}
              disabled={loading === 'file' || !filePath.trim()}
            >
              {loading === 'file' ? 'Processing...' : 'Ingest File'}
            </button>
          </div>

          {/* Folder Ingest */}
          <div className="ingest-section">
            <h4 className="ingest-section-title font-mono">FOLDER_SCAN</h4>
            <div className="ingest-field">
              <label className="ingest-label font-mono">Folder Path</label>
              <input
                id="ingest-folder-path"
                type="text"
                className="ingest-input font-mono"
                placeholder="Click to browse or enter path manually..."
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                onClick={handleBrowseFolderForIngest}
                style={{ cursor: 'pointer' }}
              />
            </div>
            <div className="ingest-field ingest-checkbox-row">
              <label className="ingest-label font-mono" style={{ flex: 1 }}>Recursive</label>
              <input
                type="checkbox"
                className="ingest-checkbox"
                checked={recursive}
                onChange={(e) => setRecursive(e.target.checked)}
              />
            </div>
            <button
              id="ingest-folder-btn"
              className="ingest-btn"
              onClick={handleIngestFolder}
              disabled={loading === 'folder' || !folderPath.trim()}
            >
              {loading === 'folder' ? 'Scanning...' : 'Scan Folder'}
            </button>
          </div>

          {/* Reindex / Delete */}
          <div className="ingest-section">
            <h4 className="ingest-section-title font-mono">REINDEX / DELETE</h4>
            <div className="ingest-field">
              <label className="ingest-label font-mono">File Path</label>
              <input
                id="ingest-reindex-path"
                type="text"
                className="ingest-input font-mono"
                placeholder="Click to browse or enter path manually..."
                value={reindexPath}
                onChange={(e) => setReindexPath(e.target.value)}
                onClick={handleBrowseFileForReindex}
                style={{ cursor: 'pointer' }}
              />
            </div>
            <div className="ingest-btn-row">
              <button
                className="ingest-btn"
                onClick={handleReindex}
                disabled={loading === 'reindex' || !reindexPath.trim()}
              >
                Reindex
              </button>
              <button
                className="ingest-btn ingest-btn--danger"
                onClick={handleDelete}
                disabled={loading === 'delete' || !reindexPath.trim()}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Terminal / Activity Log */}
      <div className="ingest-terminal">
        <div className="ingest-terminal-header">
          <div className="ingest-terminal-breadcrumb font-mono">
            <span>INGESTION</span>
            <span style={{ opacity: 0.3 }}>/</span>
            <span style={{ color: 'var(--primary)', fontWeight: 700 }}>ACTIVITY_LOG</span>
          </div>
          <div className="ingest-terminal-status">
            <span className="status-dot status-dot--running" style={{ width: 5, height: 5 }} />
            <span className="font-mono" style={{ color: 'var(--primary)', fontSize: 10, fontWeight: 700 }}>Ready</span>
          </div>
        </div>
        <div className="ingest-terminal-body">
          <div className="ingest-terminal-content font-mono" id="ingest-log-output">
            {logs.length === 0 && (
              <>
                <p><span className="log-ts">[{new Date().toLocaleTimeString('en-US', { hour12: false })}]</span> <span className="log-system">SYSTEM</span> Ingest terminal ready. Awaiting commands...</p>
                <p className="log-waiting">-- LISTENING FOR INGEST COMMANDS --</p>
              </>
            )}
            {logs.map((log, i) => (
              <p key={i}>
                <span className="log-ts">[{log.ts}]</span>{' '}
                <span className={`log-${log.type.toLowerCase()}`}>{log.type}</span>{' '}
                {log.message}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
