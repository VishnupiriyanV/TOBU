import { useState, useEffect } from 'react';
import './ExplorerPanel.css';

const FileIcon = ({ type, extension, expanded }) => {
  if (type === 'folder') return <span>{expanded ? '📂' : '📁'}</span>;
  
  switch (extension) {
    case '.mp3':
    case '.wav':
    case '.flac':
      return <span>🎵</span>;
    case '.mp4':
    case '.mov':
    case '.mkv':
      return <span>🎬</span>;
    case '.jpg':
    case '.png':
    case '.webp':
      return <span>🖼️</span>;
    case '.pdf':
    case '.txt':
    case '.docx':
      return <span>📄</span>;
    default:
      return <span className="material-symbols-outlined" style={{fontSize: '16px'}}>draft</span>;
  }
};

const TreeNode = ({ node, level, onSelectFile, activeFile }) => {
  const [expanded, setExpanded] = useState(true);
  const isFolder = node.type === 'folder';
  const isActive = activeFile === node.path && !isFolder;

  const handleClick = (e) => {
    e.stopPropagation();
    if (isFolder) {
      setExpanded(!expanded);
    } else {
      if (onSelectFile) onSelectFile(node);
    }
  };

  const handleContextMenu = (e) => {
    e.preventDefault();
    // In a real app we'd open a custom context menu here
    alert(`Context menu for: ${node.name}\n- Open\n- Rename\n- Delete\n- Copy Path`);
  };

  return (
    <div className="tree-node-container">
      <div 
        className={`tree-node ${isActive ? 'active' : ''}`} 
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
      >
        <div className="tree-node-icon">
          <FileIcon type={node.type} extension={node.extension} expanded={expanded} />
        </div>
        <span className="tree-node-label">{node.name}</span>
      </div>
      
      {isFolder && expanded && node.children && (
        <div className={`tree-children ${expanded ? 'expanded' : ''}`}>
          {node.children.map(child => (
            <TreeNode 
              key={child.id} 
              node={child} 
              level={level + 1} 
              onSelectFile={onSelectFile}
              activeFile={activeFile}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default function ExplorerPanel({ isOpen, onSelectMedia, activeMediaFile }) {
  const [treeData, setTreeData] = useState([]);
  const [activeFile, setActiveFile] = useState(null);
  
  // Keep local active file synced with parent
  useEffect(() => {
    setActiveFile(activeMediaFile?.path || null);
  }, [activeMediaFile]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTree = async () => {
    setLoading(true);
    try {
      // First try to fetch from backend
      const res = await fetch('http://127.0.0.1:8000/api/v1/system/file-tree');
      if (res.ok) {
        const json = await res.json();
        if (json.ok && json.data.tree) {
          setTreeData(json.data.tree);
          return;
        }
      }
    } catch (err) {
      console.warn("Could not fetch from backend, using sample tree.", err);
    } finally {
      setLoading(false);
    }
    
    // Fallback to sample tree
    setTreeData([
      {
        id: 'workspace', name: 'Workspace', type: 'folder', path: 'workspace',
        children: [
          {
            id: 'videos', name: 'Videos', type: 'folder', path: 'workspace/Videos',
            children: [
              { id: 'intro.mp4', name: 'intro.mp4', type: 'file', extension: '.mp4', path: 'workspace/Videos/intro.mp4' },
              { id: 'demo.mov', name: 'demo.mov', type: 'file', extension: '.mov', path: 'workspace/Videos/demo.mov' }
            ]
          },
          {
            id: 'music', name: 'Music', type: 'folder', path: 'workspace/Music',
            children: [
              { id: 'track01.mp3', name: 'track01.mp3', type: 'file', extension: '.mp3', path: 'workspace/Music/track01.mp3' },
              { id: 'ambient.flac', name: 'ambient.flac', type: 'file', extension: '.flac', path: 'workspace/Music/ambient.flac' }
            ]
          },
          {
            id: 'photos', name: 'Photos', type: 'folder', path: 'workspace/Photos',
            children: [
              { id: 'screenshot.png', name: 'screenshot.png', type: 'file', extension: '.png', path: 'workspace/Photos/screenshot.png' },
              { id: 'cover.webp', name: 'cover.webp', type: 'file', extension: '.webp', path: 'workspace/Photos/cover.webp' }
            ]
          },
          {
            id: 'documents', name: 'Documents', type: 'folder', path: 'workspace/Documents',
            children: [
              { id: 'readme.txt', name: 'readme.txt', type: 'file', extension: '.txt', path: 'workspace/Documents/readme.txt' },
              { id: 'report.pdf', name: 'report.pdf', type: 'file', extension: '.pdf', path: 'workspace/Documents/report.pdf' }
            ]
          }
        ]
      }
    ]);
  };

  useEffect(() => {
    fetchTree();
  }, []);

  const handleSelectFile = (node) => {
    setActiveFile(node.path);
    if (onSelectMedia) {
      onSelectMedia(node);
    }
  };

  return (
    <div className={`explorer-panel ${isOpen ? 'open' : ''}`}>
      <div className="explorer-header">
        <span className="explorer-title">EXPLORER</span>
        <div className="explorer-actions">
          <button className="explorer-icon-btn" title="New Folder">
            <span className="material-symbols-outlined">create_new_folder</span>
          </button>
          <button className="explorer-icon-btn" title="Refresh" onClick={fetchTree}>
            <span className="material-symbols-outlined">refresh</span>
          </button>
          <button className="explorer-icon-btn" title="Collapse All">
            <span className="material-symbols-outlined">unfold_less</span>
          </button>
        </div>
      </div>
      
      <div className="explorer-content">
        {loading ? (
          <div className="explorer-loading">Loading...</div>
        ) : (
          <div className="tree-root">
            {treeData.map(node => (
              <TreeNode 
                key={node.id} 
                node={node} 
                level={0} 
                onSelectFile={handleSelectFile}
                activeFile={activeFile}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
