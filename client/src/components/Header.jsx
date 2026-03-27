import './Header.css';

export default function Header() {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <span className="topbar-brand">TOBU</span>
      </div>
      <div className="topbar-right">

        <button className="topbar-icon-btn" title="Notifications">
          <span className="material-symbols-outlined">notifications</span>
        </button>
        <button className="topbar-icon-btn" title="Help">
          <span className="material-symbols-outlined">help_outline</span>
        </button>
      </div>
    </header>
  );
}
