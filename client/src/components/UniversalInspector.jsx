import React, { useEffect, useRef } from 'react';
import CustomPdfViewer from './CustomPdfViewer';
import { getMediaServeUrl, openMediaNative } from '../api';
import './UniversalInspector.css';

function fileIcon(sourceType, fileName) {
  if (sourceType === 'video' || /\.(mp4|mkv|avi|mov|webm)$/i.test(fileName || ''))
    return { icon: 'video_library', color: '#60a5fa' };
  if (sourceType === 'pdf' || /\.pdf$/i.test(fileName || ''))
    return { icon: 'picture_as_pdf', color: '#f87171' };
  if (/\.(md|txt|csv)$/i.test(fileName || ''))
    return { icon: 'description', color: '#fb923c' };
  if (/\.(jpg|jpeg|png|gif|webp)$/i.test(fileName || ''))
    return { icon: 'image', color: '#a78bfa' };
  if (/\.(mp3|wav|ogg|flac|aac)$/i.test(fileName || ''))
    return { icon: 'audio_file', color: '#34d399' };
  return { icon: 'insert_drive_file', color: '#9ca3af' };
}

function formatTime(seconds) {
  if (seconds == null) return '';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function UniversalInspector({ item, onClose }) {
  const fileName = item.file_name || item.file_path.split(/[/\\]/).pop();
  const fi = fileIcon(item.source_type, fileName);
  const mediaUrl = getMediaServeUrl(item.file_path);
  const mediaRef = useRef(null);

  useEffect(() => {
    if (item.start != null && mediaRef.current) {
      mediaRef.current.currentTime = item.start;
    }
  }, [item.start, item.file_path]);

  const handleLoadedMetadata = (e) => {
    if (item.start != null) {
      e.target.currentTime = item.start;
    }
  };

  if (fi.icon === 'picture_as_pdf') {
    return (
      <CustomPdfViewer
        fileUrl={mediaUrl}
        initialPage={item.start && !isNaN(Number(item.start)) ? Math.max(1, Math.floor(Number(item.start))) : 1}
        timestamp={item.start}
        onClose={onClose}
      />
    );
  }

  return (
    <div className="universal-inspector">
      <div className="universal-inspector-header">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0, fontSize: '14px', color: '#e0e0f0' }}>
          <span className="material-symbols-outlined" style={{ color: fi.color, fontSize: '20px' }}>{fi.icon}</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{fileName}</span>
        </h3>
        <button onClick={onClose} className="universal-close-btn" title="Close Inspector">
          <span className="material-symbols-outlined">close</span>
        </button>
      </div>

      <div className="universal-inspector-body">
        {fi.icon === 'video_library' && (
          <div className="inspector-media-container">
            <video 
              ref={mediaRef}
              src={mediaUrl}
              controls 
              className="inspector-video"
              onLoadedMetadata={handleLoadedMetadata}
            />
          </div>
        )}

        {fi.icon === 'audio_file' && (
          <div className="inspector-media-container" style={{ padding: '20px', background: '#0a0a0f', borderRadius: '8px', border: '1px solid #2a2a3a' }}>
            <audio 
              ref={mediaRef}
              src={mediaUrl}
              controls 
              className="inspector-audio"
              onLoadedMetadata={handleLoadedMetadata}
              style={{ width: '100%' }}
            />
          </div>
        )}

        {fi.icon === 'image' && (
          <div className="inspector-media-container">
            <img src={mediaUrl} alt={fileName} className="inspector-image" />
          </div>
        )}

        {fi.icon === 'description' && (
          <div className="inspector-fallback-box">
            <span className="material-symbols-outlined" style={{ fontSize: 40, color: fi.color }}>description</span>
            <p>Text Document</p>
            <button onClick={() => openMediaNative(item.file_path)} className="inspector-action-btn">
              Open Externally
            </button>
          </div>
        )}

        {fi.icon === 'insert_drive_file' && (
          <div className="inspector-fallback-box">
            <span className="material-symbols-outlined" style={{ fontSize: 40, opacity: 0.3 }}>extension_off</span>
            <p>Preview unavailable continuously in TOBU</p>
            <button onClick={() => openMediaNative(item.file_path)} className="inspector-action-btn">
              Open System App
            </button>
          </div>
        )}

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

        <div className="inspector-section">
          <h4 className="inspector-section-title" style={{ color: 'var(--outline)' }}>Metadata</h4>
          <div className="inspector-meta-grid">
            <div className="inspector-meta-cell">
              <span className="inspector-meta-key">File</span>
              <span className="inspector-meta-value" style={{wordBreak: 'break-all'}}>{fileName}</span>
            </div>
            <div className="inspector-meta-cell">
              <span className="inspector-meta-key">Score</span>
              <span className="inspector-meta-value">{item.score?.toFixed(4) || '—'}</span>
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
      </div>
    </div>
  );
}
