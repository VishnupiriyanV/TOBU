import { useState, useEffect } from 'react';
import { getHealth } from '../api';
import './Footer.css';

export default function Footer() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const check = () => getHealth().then(setHealth).catch(() => setHealth(null));
    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, []);

  const isOk = health?.database === 'ok';

  return (
    <footer className="statusbar">
      <div className="statusbar-left">
        <div className="statusbar-health">
          <span className={`statusbar-dot ${isOk ? 'statusbar-dot--ok' : 'statusbar-dot--err'}`} />
          <span className="statusbar-label">
            {isOk ? 'System: Optimal' : health ? 'System: Degraded' : 'Connecting...'}
          </span>
        </div>
      </div>
      <div className="statusbar-right">
        <span className="statusbar-meta">TOBU v1.0.0</span>
      </div>
    </footer>
  );
}
