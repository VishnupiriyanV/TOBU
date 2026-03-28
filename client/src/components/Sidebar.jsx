import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const navItems = [
  { to: '/',       icon: 'search',              label: 'Search' },
  { to: '/jobs',   icon: 'assignment_turned_in', label: 'Jobs' },
  { to: '/ingest', icon: 'input',               label: 'Ingest' },
  { to: '/system', icon: 'dashboard',           label: 'System' },
];

export default function Sidebar({ onToggleExplorer, isExplorerOpen }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-box">
          <span className="sidebar-logo-letter">T</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <button
          className={`sidebar-nav-item ${isExplorerOpen ? 'sidebar-nav-item--active' : ''}`}
          onClick={onToggleExplorer}
          title="Explorer"
        >
          <span className="material-symbols-outlined">folder</span>
        </button>
        {navItems.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `sidebar-nav-item ${isActive ? 'sidebar-nav-item--active' : ''}`
            }
            title={label}
          >
            <span
              className="material-symbols-outlined"
              style={undefined}
            >
              {icon}
            </span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <button className="sidebar-nav-item" title="Settings">
          <span className="material-symbols-outlined">settings</span>
        </button>
        <div className="sidebar-avatar">
          <span className="sidebar-avatar-letter">U</span>
        </div>
      </div>
    </aside>
  );
}
