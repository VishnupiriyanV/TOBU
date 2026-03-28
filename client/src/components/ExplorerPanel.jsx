import React, { useState, useEffect, useRef } from 'react';
import { storeHandle, getHandle, deleteHandle, getAllHandles, verifyPermission } from './workspaceDB';
import './ExplorerPanel.css';

const FileIcon = ({ type, extension, expanded }) => {
  if (type === 'folder') return <span>{expanded ? '📂' : '📁'}</span>;
  
  switch (extension) {
    case '.mp3': case '.wav': case '.flac': case '.ogg': case '.aac':
      return <span>🎵</span>;
    case '.mp4': case '.mov': case '.mkv': case '.avi': case '.webm':
      return <span>🎬</span>;
    case '.jpg': case '.jpeg': case '.png': case '.gif': case '.webp': case '.svg':
      return <span>🖼️</span>;
    case '.pdf': case '.txt': case '.md': case '.docx': case '.csv':
      return <span>📄</span>;
    default:
      return <span>📎</span>;
  }
};

const TreeNode = ({ node, level, onSelectFile, activeFile, onRemove, onRename }) => {
  const [expanded, setExpanded] = useState(true);
  const isFolder = node.type === 'folder';
  const isActive = activeFile === node.path && !isFolder;
  const [showContext, setShowContext] = useState(false);
  const [contextPos, setContextPos] = useState({x: 0, y: 0});
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(node.name);

  const handleClick = (e) => {
    e.stopPropagation();
    setShowContext(false);
    if (isFolder) {
      setExpanded(!expanded);
    } else {
      if (onSelectFile) onSelectFile(node);
    }
  };

  const handleContextMenu = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setContextPos({ x: e.clientX, y: e.clientY });
    setShowContext(true);
  };

  useEffect(() => {
    const hideMenu = () => setShowContext(false);
    window.addEventListener('click', hideMenu);
    return () => window.removeEventListener('click', hideMenu);
  }, []);

  const submitRename = () => {
    setIsEditing(false);
    if (editName.trim() && editName !== node.name && onRename) {
      onRename(node.path, editName.trim());
    } else {
      setEditName(node.name);
    }
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
          <FileIcon type={node.type} extension={node.extension || (node.name.includes('.') ? node.name.substring(node.name.lastIndexOf('.')).toLowerCase() : '')} expanded={expanded} />
        </div>
        {isEditing ? (
          <input
            autoFocus
            className="tree-node-edit"
            value={editName}
            onChange={e => setEditName(e.target.value)}
            onBlur={submitRename}
            onKeyDown={e => { if(e.key === 'Enter') submitRename(); if(e.key === 'Escape') { setIsEditing(false); setEditName(node.name); } }}
            onClick={e => e.stopPropagation()}
          />
        ) : (
          <span className="tree-node-label">{node.name}</span>
        )}
      </div>
      
      {showContext && (
        <div className="context-menu" style={{ top: contextPos.y, left: contextPos.x }} onClick={e => e.stopPropagation()}>
          <button onClick={() => { setShowContext(false); setIsEditing(true); }}>Rename</button>
          <button onClick={() => { setShowContext(false); if(onRemove) onRemove(node.path); }}>Remove from Workspace</button>
        </div>
      )}

      {isFolder && expanded && node.children && (
        <div className={`tree-children ${expanded ? 'expanded' : ''}`}>
          {node.children.map(child => (
            <TreeNode 
              key={child.path || child.name} 
              node={child} 
              level={level + 1} 
              onSelectFile={onSelectFile}
              activeFile={activeFile}
              onRemove={onRemove}
              onRename={onRename}
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
  const [loading, setLoading] = useState(true);
  const [needsAuth, setNeedsAuth] = useState(false);
  const fileInputRef = useRef(null);
  const memoryFilesRef = useRef({}); // Store File objects from <input type="file">

  useEffect(() => {
    setActiveFile(activeMediaFile?.path || null);
  }, [activeMediaFile]);

  const mergeTrees = (backendTree, localTree) => {
    if (!backendTree && !localTree) return [];
    if (!backendTree) return localTree ? [localTree] : [];
    if (!localTree) return [backendTree];
    
    // Simple top level merge for array of nodes vs single root node
    const bArray = Array.isArray(backendTree) ? backendTree : [backendTree];
    const lArray = Array.isArray(localTree) ? localTree : [];
    
    const combined = [...bArray];
    const bPaths = new Set(combined.map(n => n.path));
    
    for (const lNode of lArray) {
      if (!bPaths.has(lNode.path)) {
        combined.push(lNode);
      }
    }
    return combined;
  };

  const fetchAndMergeTree = async () => {
    setLoading(true);
    let bTree = null;
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/system/file-tree');
      if (res.ok) {
        const json = await res.json();
        if (json.ok && json.data) {
          bTree = json.data;
        }
      }
    } catch (e) {
      console.warn("Backend tree fetch failed.");
    }
    
    let lTree = [];
    try {
      const saved = localStorage.getItem('tobu_workspace_tree');
      if (saved) lTree = JSON.parse(saved);
    } catch (e) {}

    const finalTree = mergeTrees(bTree, lTree);
    setTreeData(finalTree);
    setLoading(false);
    checkPermissions();
  };

  useEffect(() => {
    fetchAndMergeTree();
    // eslint-disable-next-line
  }, []);

  const saveLocalTree = (treeArr) => {
    // We only save nodes that are NOT from the backend
    // Since our backend node path is usually absolute and starts at watch,
    // we could just save everything that isn't the 'watch' root.
    // For simplicity, we filter out nodes that we know are backend default (e.g. name="watch" if it came from backend)
    // Assuming user injected folders have different paths.
    // Or we just save everything and the merge handles it.
    // The prompt says "store the injected file/folder tree... on reload merge".
    const localNodes = treeArr.filter(n => n.source !== 'backend');
    localStorage.setItem('tobu_workspace_tree', JSON.stringify(localNodes));
    setTreeData(treeArr);
  };

  const checkPermissions = async () => {
    try {
      const handles = await getAllHandles();
      let needed = false;
      for (const h of handles) {
        if ((await h.handle.queryPermission({mode: 'read'})) !== 'granted') {
          needed = true;
          break;
        }
      }
      setNeedsAuth(needed);
    } catch (e) {
      console.error(e);
    }
  };

  const requestAllPermissions = async () => {
    try {
      const handles = await getAllHandles();
      for (const h of handles) {
        await verifyPermission(h.handle, false);
      }
      setNeedsAuth(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleOpenFolder = async () => {
    try {
      const directoryHandle = await window.showDirectoryPicker();
      
      const processDirectory = async (dirHandle, pathPrefix) => {
        let items = [];
        for await (const entry of dirHandle.values()) {
          const entryPath = pathPrefix + '/' + entry.name;
          if (entry.kind === 'file') {
            const file = await entry.getFile();
            const ext = entry.name.includes('.') ? entry.name.substring(entry.name.lastIndexOf('.')).toLowerCase() : '';
            items.push({
              name: entry.name,
              path: entryPath,
              type: 'file',
              mimeType: file.type || 'application/octet-stream',
              size: file.size,
              lastModified: new Date(file.lastModified).toISOString(),
              extension: ext,
              source: 'localHandle'
            });
            await storeHandle(entryPath, entry);
          } else if (entry.kind === 'directory') {
            items.push({
              name: entry.name,
              path: entryPath,
              type: 'folder',
              source: 'localHandle',
              children: await processDirectory(entry, entryPath)
            });
            await storeHandle(entryPath, entry);
          }
        }
        return items.sort((a,b) => (b.type === 'folder') - (a.type === 'folder') || a.name.localeCompare(b.name));
      };
      
      const folderPath = 'local://' + directoryHandle.name;
      await storeHandle(folderPath, directoryHandle);
      
      const newFolderNode = {
        name: directoryHandle.name,
        path: folderPath,
        type: 'folder',
        source: 'localHandle',
        children: await processDirectory(directoryHandle, folderPath)
      };
      
      const newTree = [...treeData.filter(n => n.path !== folderPath), newFolderNode];
      saveLocalTree(newTree);

    } catch (e) {
      if (e.name !== 'AbortError') console.error(e);
    }
  };

  const handleFileInputChange = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    
    // Add them to a "Virtual Uploads" folder or root
    const newChildren = files.map(file => {
      const path = 'memory://' + file.name + '-' + Date.now();
      memoryFilesRef.current[path] = file;
      const ext = file.name.includes('.') ? file.name.substring(file.name.lastIndexOf('.')).toLowerCase() : '';
      return {
        name: file.name,
        path: path,
        type: 'file',
        mimeType: file.type || 'application/octet-stream',
        size: file.size,
        lastModified: new Date(file.lastModified).toISOString(),
        extension: ext,
        source: 'localFile'
      };
    });
    
    let newTree = [...treeData];
    let uploadsNode = newTree.find(n => n.id === 'virtual_uploads');
    if (!uploadsNode) {
      uploadsNode = { id: 'virtual_uploads', name: 'Virtual Uploads', type: 'folder', path: 'virtual_uploads', source: 'localFile', children: [] };
      newTree.push(uploadsNode);
    }
    uploadsNode.children = [...uploadsNode.children, ...newChildren];
    
    saveLocalTree(newTree);
    e.target.value = ''; // reset
  };

  const handleSelectFile = async (node) => {
    setActiveFile(node.path);
    if (!onSelectMedia) return;

    let enhancedNode = { ...node };
    
    if (node.source === 'localHandle') {
      const handle = await getHandle(node.path);
      if (handle && handle.kind === 'file') {
        const permitted = await verifyPermission(handle);
        if (permitted) {
          enhancedNode.fileBlob = await handle.getFile();
        }
      }
    } else if (node.source === 'localFile') {
       enhancedNode.fileBlob = memoryFilesRef.current[node.path];
    } else {
       // Backend file
       enhancedNode.source = 'backend';
    }

    onSelectMedia(enhancedNode);
  };

  const deepRemove = (nodes, pathToRemove) => {
    return nodes.filter(n => n.path !== pathToRemove).map(n => {
      if (n.children) {
        return { ...n, children: deepRemove(n.children, pathToRemove) };
      }
      return n;
    });
  };

  const handleRemove = (path) => {
    deleteHandle(path);
    const newTree = deepRemove(treeData, path);
    saveLocalTree(newTree);
    if (activeFile === path && onSelectMedia) {
      onSelectMedia(null);
    }
  };

  const deepRename = (nodes, targetPath, newName) => {
    return nodes.map(n => {
      if (n.path === targetPath) return { ...n, name: newName };
      if (n.children) return { ...n, children: deepRename(n.children, targetPath, newName) };
      return n;
    });
  };

  const handleRename = (path, newName) => {
     saveLocalTree(deepRename(treeData, path, newName));
  };
  
  // Drag and drop support
  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const items = Array.from(e.dataTransfer.items);
    if (items.length === 0) return;
    
    let newTree = [...treeData];
    let uploadsNode = newTree.find(n => n.id === 'virtual_uploads');
    
    for (const item of items) {
      if (item.kind === 'file') {
        let entry = null;
        if (item.getAsFileSystemHandle) {
          entry = await item.getAsFileSystemHandle();
        } else if (item.webkitGetAsEntry) {
           // Fallback for older browsers
           const file = item.getAsFile();
           // similar memory logic ...
           if (file) {
              if (!uploadsNode) {
                uploadsNode = { id: 'virtual_uploads', name: 'Virtual Uploads', type: 'folder', path: 'virtual_uploads', source: 'localFile', children: [] };
                newTree.push(uploadsNode);
              }
              const path = 'memory://' + file.name + '-' + Date.now();
              memoryFilesRef.current[path] = file;
              uploadsNode.children.push({
                name: file.name, path, type: 'file', source: 'localFile', extension: file.name.includes('.') ? file.name.substring(file.name.lastIndexOf('.')).toLowerCase() : ''
              });
           }
           continue;
        }
        
        if (entry) {
          // If we got handles from drop
          if (entry.kind === 'directory') {
            const processDirectory = async (dirHandle, pathPrefix) => {
              let res = [];
              for await (const child of dirHandle.values()) {
                const childPath = pathPrefix + '/' + child.name;
                if (child.kind === 'file') {
                  const f = await child.getFile();
                  res.push({
                    name: child.name, path: childPath, type: 'file', source: 'localHandle',
                    size: f.size, mimeType: f.type, lastModified: new Date(f.lastModified).toISOString(),
                    extension: child.name.includes('.') ? child.name.substring(child.name.lastIndexOf('.')).toLowerCase() : ''
                  });
                  await storeHandle(childPath, child);
                } else {
                  res.push({
                    name: child.name, path: childPath, type: 'folder', source: 'localHandle',
                    children: await processDirectory(child, childPath)
                  });
                  await storeHandle(childPath, child);
                }
              }
              return res;
            };
            const p = 'local://' + entry.name;
            await storeHandle(p, entry);
            newTree.push({
              name: entry.name, path: p, type: 'folder', source: 'localHandle',
              children: await processDirectory(entry, p)
            });
          } else {
             // Single file drop as handle
             if (!uploadsNode) {
                uploadsNode = { id: 'virtual_uploads', name: 'Virtual Uploads', type: 'folder', path: 'virtual_uploads', source: 'localFile', children: [] };
                newTree.push(uploadsNode);
             }
             const file = await entry.getFile();
             const p = 'local://' + entry.name;
             await storeHandle(p, entry);
             uploadsNode.children.push({
               name: entry.name, path: p, type: 'file', source: 'localHandle',
               size: file.size, mimeType: file.type, lastModified: new Date(file.lastModified).toISOString(),
               extension: entry.name.includes('.') ? entry.name.substring(entry.name.lastIndexOf('.')).toLowerCase() : ''
             });
          }
        }
      }
    }
    
    saveLocalTree(newTree);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <div className={`explorer-panel ${isOpen ? 'open' : ''}`} onDrop={handleDrop} onDragOver={handleDragOver}>
      <div className="explorer-header">
        <span className="explorer-title">EXPLORER</span>
        <div className="explorer-actions">
          <button className="explorer-icon-btn" title="Open Folder" onClick={handleOpenFolder}>
            <span className="material-symbols-outlined">snippet_folder</span>
          </button>
          <button className="explorer-icon-btn" title="Add Files" onClick={() => fileInputRef.current?.click()}>
            <span className="material-symbols-outlined">note_add</span>
          </button>
          <input type="file" multiple ref={fileInputRef} style={{display:'none'}} onChange={handleFileInputChange} />
        </div>
      </div>

      {needsAuth && (
        <div className="explorer-auth-banner">
          <span>Re-authorize workspace access</span>
          <button onClick={requestAllPermissions}>Allow</button>
        </div>
      )}
      
      <div className="explorer-content">
        {loading ? (
          <div className="explorer-loading">Loading...</div>
        ) : treeData.length === 0 ? (
           <div className="explorer-empty">
             <span className="material-symbols-outlined" style={{fontSize: '48px', color: '#555566', marginBottom: '16px'}}>drive_folder_upload</span>
             <div>Drop files or folders here to get started</div>
           </div>
        ) : (
          <div className="tree-root">
            {treeData.map(node => (
              <TreeNode 
                key={node.path || node.name} 
                node={node} 
                level={0} 
                onSelectFile={handleSelectFile}
                activeFile={activeFile}
                onRemove={handleRemove}
                onRename={handleRename}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
