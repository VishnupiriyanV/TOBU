import React, { useState, useEffect, useRef } from 'react';
import './MediaPlayerPanel.css';

const getFileUrl = (path) => {
  return `http://127.0.0.1:8000/api/v1/media/serve?file_path=${encodeURIComponent(path)}`;
};

const VideoPlayer = ({ fileUrl }) => {
  return (
    <div className="media-video-container">
      <video className="media-video" controls src={fileUrl} />
      <div className="scanline-overlay"></div>
    </div>
  );
};

const AudioPlayer = ({ fileUrl, metadata }) => {
  const canvasRef = useRef(null);
  const audioRef = useRef(null);

  useEffect(() => {
    // Simple mock waveform animation for the canvas
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationId;
    
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#7b6ef6';
      
      const barWidth = Math.max(2, canvas.width / 50);
      const gap = 2;
      const numBars = Math.floor(canvas.width / (barWidth + gap));
      
      for (let i = 0; i < numBars; i++) {
        const height = Math.random() * canvas.height * 0.8;
        ctx.fillRect(i * (barWidth + gap), canvas.height - height, barWidth, height);
      }
      
      animationId = requestAnimationFrame(() => {
        setTimeout(draw, 100); // Throttle random heights for visual stability
      });
    };
    
    draw();
    return () => cancelAnimationFrame(animationId);
  }, [fileUrl]);

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
      <audio className="media-audio" controls src={fileUrl} ref={audioRef} />
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
          src={fileUrl} 
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
  const ext = metadata?.extension?.toLowerCase();
  const [textContent, setTextContent] = useState('');

  useEffect(() => {
    if (ext === '.txt' || ext === '.md') {
      fetch(fileUrl)
        .then(res => res.text())
        .then(setTextContent)
        .catch(console.error);
    }
  }, [fileUrl, ext]);

  if (ext === '.pdf') {
    return <iframe className="media-document-pdf" src={fileUrl} title={metadata?.name} />;
  }

  if (ext === '.txt' || ext === '.md') {
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

  useEffect(() => {
    if (file) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  }, [file]);

  const handleKeyDown = (e) => {
    if (!isOpen) return;
    if (e.key === 'Escape') {
      if (onClose) onClose();
    }
  };

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen && !file) {
    return null; // Don't render if permanently closed
  }

  const renderContent = () => {
    if (!file) return <div className="media-empty">No file selected</div>;
    
    const ext = file.extension?.toLowerCase();
    const url = getFileUrl(file.path);

    if (['.mp4', '.mov', '.mkv', '.webm', '.avi'].includes(ext)) {
      return <VideoPlayer fileUrl={url} metadata={file} />;
    } else if (['.mp3', '.wav', '.flac', '.ogg'].includes(ext)) {
      return <AudioPlayer fileUrl={url} metadata={file} />;
    } else if (['.jpg', '.jpeg', '.png', '.webp', '.gif'].includes(ext)) {
      return <ImageViewer fileUrl={url} metadata={file} />;
    } else if (['.pdf', '.txt', '.md', '.docx'].includes(ext)) {
      return <DocumentViewer fileUrl={url} metadata={file} />;
    } else {
      return <div className="media-empty">Unsupported file format: {ext}</div>;
    }
  };

  return (
    <div className={`media-player-panel ${isOpen ? 'open' : ''}`}>
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
             <a href={file ? getFileUrl(file.path) : '#'} download style={{ color: 'inherit', display: 'flex' }}>
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
