import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import ExplorerPanel from './ExplorerPanel';
import MediaPlayerPanel from './MediaPlayerPanel';
import Header from './Header';
import Footer from './Footer';
import './Layout.css';

export default function Layout() {
  const [isExplorerOpen, setIsExplorerOpen] = useState(true);
  const [activeMediaFile, setActiveMediaFile] = useState(null);
  return (
    <div className="app-shell">
      <Sidebar 
        onToggleExplorer={() => setIsExplorerOpen(!isExplorerOpen)}
        isExplorerOpen={isExplorerOpen}
      />
      <ExplorerPanel 
        isOpen={isExplorerOpen} 
        onSelectMedia={setActiveMediaFile} 
        activeMediaFile={activeMediaFile} 
      />
      <div className="app-main">
        <Header />
        <main className="app-content">
          <Outlet />
        </main>
        <Footer />
      </div>
      <MediaPlayerPanel 
        file={activeMediaFile} 
        onClose={() => setActiveMediaFile(null)} 
      />
    </div>
  );
}
