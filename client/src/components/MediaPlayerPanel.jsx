import React, { useState, useEffect, useRef } from 'react';
import useWaveform from './useWaveform';
import './MediaPlayerPanel.css';

const getFileUrl = (node) => {
  if (!node) return null;
  if (node.source === 'backend' || !node.source) {
    return `http://127.0.0.1:8000/api/v1/media/serve?file_path=${encodeURIComponent(node.path)}`;
  }
  if (node.fileBlob) {
    return URL.createObjectURL(node.fileBlob);
  }
  return null;
};

const VideoPlayer = ({ fileUrl }) => {
  return (
    <div className="media-video-container">
      <video className="media-video" controls src={fileUrl || undefined} />
      <div className="scanline-overlay"></div>
    </div>
  );
};

const AudioPlayer = ({ fileUrl, metadata }) => {
  const canvasRef = useRef(null);
  const audioRef = useRef(null);
  
  // Use Web Audio API hook
  useWaveform(fileUrl, canvasRef, audioRef);

  return (
    <div className="media-audio-container">
      <div className="audio-album-placeholder">
        <div className="audio-album-gradient" />
        <span className="material-symbols-outlined" style={{ fontSize: '48px', color: 'rgba(255,255,255,0.4)' }}>music_note</span>
      </div>
      <div className="audio-info">
        <div className="audio-title">{metadata?.name || 'Unknown Track'}</div>
        <div className="audio-artist">Unknown Artist</div>
      </div>
      <canvas ref={canvasRef} className="audio-waveform" width="300" height="80" />
      <audio className="media-audio" controls src={fileUrl || undefined} ref={audioRef} />
    </div>
  );
};

const ImageViewer = ({ fileUrl, metadata }) => {
  const [scale, setScale] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });

  const handleWheel = (e) => {
    e.preventDefault();
    const newScale = Math.min(Math.max(0.1, scale - e.deltaY * 0.001), 5);
    setScale(newScale);
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartPos({ x: e.clientX - pos.x, y: e.clientY - pos.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPos({ x: e.clientX - startPos.x, y: e.clientY - startPos.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="media-image-container" onWheel={handleWheel}>
      <div className="media-image-canvas"
           onMouseDown={handleMouseDown}
           onMouseMove={handleMouseMove}
           onMouseUp={handleMouseUp}
           onMouseLeave={handleMouseUp}
           style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      >
        <img 
          src={fileUrl || undefined} 
          alt={metadata?.name} 
          style={{ 
            transform: `translate(${pos.x}px, ${pos.y}px) scale(${scale})`,
            transition: isDragging ? 'none' : 'transform 0.1s'
          }} 
          draggable={false}
        />
      </div>
      <div className="media-image-controls">
        <button onClick={() => setScale(s => Math.max(0.1, s - 0.2))}><span className="material-symbols-outlined">zoom_out</span></button>
        <button onClick={() => { setScale(1); setPos({x:0, y:0}); }}><span className="material-symbols-outlined">fit_screen</span></button>
        <button onClick={() => setScale(s => Math.min(5, s + 0.2))}><span className="material-symbols-outlined">zoom_in</span></button>
      </div>
      <div className="media-image-metadata">
        <span>{metadata?.name}</span>
        <span>{metadata?.extension?.toUpperCase().replace('.', '')}</span>
      </div>
    </div>
  );
};

const DocumentViewer = ({ fileUrl, metadata }) => {
  // Use robust logic to determine type
  const getFileType = (filePath, mimeType) => {
    const ext = filePath?.split('.').pop().toLowerCase().trim() || '';
    if (mimeType === 'application/pdf' || ext === 'pdf') return 'pdf';
    if (['txt','md','csv'].includes(ext)) return 'text';
    return 'unsupported';
  };
  
  const fileType = getFileType(metadata?.path || metadata?.name, metadata?.mimeType);
  const [textContent, setTextContent] = useState('');

  useEffect(() => {
    if (fileType === 'text' && fileUrl) {
      if (metadata.source === 'localFile' || metadata.source === 'localHandle') {
         if (metadata.fileBlob) {
            metadata.fileBlob.text().then(setTextContent).catch(console.error);
         }
      } else {
        fetch(fileUrl)
          .then(res => res.text())
          .then(setTextContent)
          .catch(console.error);
      }
    }
  }, [fileUrl, fileType, metadata]);

  if (fileType === 'pdf') {
    return (
      <iframe 
        className="media-document-pdf" 
        src={fileUrl || undefined} 
        style={{
          width: '100%',
          height: '100%',
          minHeight: '600px',
          border: 'none',
          background: '#0e0e12'
        }}
        title={metadata?.name} 
      />
    );
  }

  if (fileType === 'text') {
    return (
      <div className="media-document-text">
        <pre>{textContent}</pre>
      </div>
    );
  }

  return <div className="media-document-unknown">Unsupported document format</div>;
};

export default function MediaPlayerPanel({ file, onClose }) {
  const [isOpen, setIsOpen] = useState(false);
  const [url, setUrl] = useState(null);
  const panelRef = useRef(null);

  useEffect(() => {
    if (file) {
      setIsOpen(true);
      const newUrl = getFileUrl(file);
      setUrl(newUrl);
      
      return () => {
        if (newUrl && newUrl.startsWith('blob:')) {
          URL.revokeObjectURL(newUrl);
        }
      };
    } else {
      setIsOpen(false);
      setUrl(null);
    }
  }, [file]);

  const handleKeyDown = (e) => {
    // Only handle if active element is NOT an input or textarea
    const activeTag = document.activeElement?.tagName?.toLowerCase();
    if (activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select') {
      return; 
    }

    if (!isOpen) return;

    if (e.key === 'Escape') {
      if (onClose) onClose();
    } else if (e.key === ' ') {
      // Space for play/pause if there's a video/audio
      const mediaEl = panelRef.current?.querySelector('video, audio');
      if (mediaEl && document.activeElement !== mediaEl) {
        e.preventDefault();
        if (mediaEl.paused) mediaEl.play();
        else mediaEl.pause();
      }
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      const mediaEl = panelRef.current?.querySelector('video, audio');
      if (mediaEl && document.activeElement !== mediaEl) {
        e.preventDefault();
        mediaEl.currentTime += (e.key === 'ArrowRight' ? 5 : -5);
      }
    }
  };

  useEffect(() => {
    // We attach it to the window but carefully scope the action via activeElement check
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, onClose]);

  if (!isOpen && !file) {
    return null;
  }

  const renderContent = () => {
    if (!file) return <div className="media-empty">No file selected</div>;
    if (!url) {
       return <div className="media-empty">Accessing file...</div>;
    }
    
    const getFileType = (filePath, mimeType) => {
      const ext = filePath?.split('.').pop().toLowerCase().trim() || '';
      if (mimeType === 'application/pdf' || ext === 'pdf') return 'pdf';
      if (['mp4','mov','mkv','avi','webm'].includes(ext)) return 'video';
      if (['mp3','wav','flac','ogg','aac'].includes(ext)) return 'audio';
      if (['jpg','jpeg','png','gif','webp','svg'].includes(ext)) return 'image';
      if (['txt','md','docx','csv'].includes(ext)) return 'text';
      return 'unsupported';
    };

    const fileType = getFileType(file.path || file.name, file.mimeType);

    if (fileType === 'pdf') {
      return <DocumentViewer fileUrl={url} metadata={file} />;
    } else if (fileType === 'video') {
      return <VideoPlayer fileUrl={url} metadata={file} />;
    } else if (fileType === 'audio') {
      return <AudioPlayer fileUrl={url} metadata={file} />;
    } else if (fileType === 'image') {
      return <ImageViewer fileUrl={url} metadata={file} />;
    } else if (fileType === 'text') {
      return <DocumentViewer fileUrl={url} metadata={file} />;
    } else {
      return <div className="media-empty">Unsupported file format</div>;
    }
  };

  return (
    <div className={`media-player-panel ${isOpen ? 'open' : ''}`} ref={panelRef} tabIndex="-1">
      <div className="media-header">
        <span className="media-title">MEDIA INSPECTOR</span>
        <div className="media-filename" title={file?.name}>{file?.name || ''}</div>
      </div>
      
      <div className="media-content-area">
        {renderContent()}
      </div>
      
      <div className="media-bottom-bar">
        <div className="media-bottom-filename" title={file?.path}>{file?.name || 'None'}</div>
        <div className="media-bottom-actions">
           <button className="media-icon-btn" title="Fullscreen" onClick={() => document.querySelector('.media-content-area')?.requestFullscreen?.()}>
             <span className="material-symbols-outlined">fullscreen</span>
           </button>
           <button className="media-icon-btn" title="Download">
             <a href={url || '#'} download={file?.name || 'download'} style={{ color: 'inherit', display: 'flex' }}>
               <span className="material-symbols-outlined">download</span>
             </a>
           </button>
           <button className="media-icon-btn" title="Close" onClick={() => { setIsOpen(false); setTimeout(onClose, 250); }}>
             <span className="material-symbols-outlined">close</span>
           </button>
        </div>
      </div>
    </div>
  );
}
