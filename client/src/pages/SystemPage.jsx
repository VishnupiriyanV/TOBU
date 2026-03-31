import { useState, useEffect } from 'react';
import { getSystemStatus, getIntegrity, createBackup } from '../api';
import './SystemPage.css';

export default function SystemPage() {
  const [status, setStatus] = useState(null);
  const [integrity, setIntegrity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [integrityLoading, setIntegrityLoading] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);
  const [backupResult, setBackupResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await getSystemStatus();
        setStatus(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
    const id = setInterval(fetchStatus, 10000);
    return () => clearInterval(id);
  }, []);

  const runIntegrity = async () => {
    setIntegrityLoading(true);
    try { setIntegrity(await getIntegrity()); }
    catch (err) { setIntegrity({ error: err.message }); }
    finally { setIntegrityLoading(false); }
  };

  const runBackup = async () => {
    setBackupLoading(true);
    try { setBackupResult(await createBackup()); }
    catch (err) { setBackupResult({ error: err.message }); }
    finally { setBackupLoading(false); }
  };

  const healthOk = status?.health?.database === 'ok';
  const dbStats = status?.db_stats || {};

  return (
    <div className="system-page">
      <div className="system-main">
        <div className="system-content">
          <div className="system-header">
            <div>
              <nav className="system-breadcrumb font-mono">
                <span>INFRA</span><span style={{opacity:0.3}}>/</span>
                <span style={{color:'var(--primary)'}}>SYSTEM_STATUS</span>
              </nav>
              <h1 className="system-title">Core Infrastructure Status</h1>
            </div>
            <div className="system-header-actions">
              <button className="system-action-btn" onClick={runIntegrity} disabled={integrityLoading}>
                {integrityLoading ? 'Checking...' : 'Integrity Check'}
              </button>
              <button className="system-action-btn system-action-btn--secondary" onClick={runBackup} disabled={backupLoading}>
                {backupLoading ? 'Creating...' : 'Create Backup'}
              </button>
            </div>
          </div>

          {error && <div className="sys-error"><span className="material-symbols-outlined">error</span>{error}</div>}

          <div className="system-metrics-grid">
            <MetricCard label="DATABASE" icon="database" value={healthOk ? 'OK' : loading ? '...' : 'Error'} bar={healthOk ? 100 : 0} />
            <MetricCard label="TOTAL FILES" icon="folder" value={dbStats.total_files ?? '—'} />
            <MetricCard label="TOTAL SEGMENTS" icon="view_timeline" value={dbStats.total_segments ?? '—'} />
          </div>

          {Object.keys(dbStats).length > 0 && (
            <StatsSection title="Database Statistics" data={dbStats} />
          )}
          {integrity && <StatsSection title="Integrity Check" data={integrity} />}
          {backupResult && <StatsSection title="Backup Result" data={backupResult} />}
        </div>
      </div>

      <aside className="system-inspector">
        <div className="system-inspector-header">
          <h3 style={{color:'var(--primary)',fontSize:11,fontWeight:700,textTransform:'uppercase',letterSpacing:'0.1em'}}>Inspector</h3>
        </div>
        <div className="system-inspector-body">
          <section className="sys-insp-section">
            <h4 className="sys-insp-title font-mono">System Health</h4>
            <div className="system-health-grid">
              {[1,2,3,4,5,6].map(i => (
                <div key={i} className={`system-health-node ${i===4?'system-health-node--idle':healthOk?'system-health-node--ok':'system-health-node--err'}`} />
              ))}
            </div>
          </section>
          <section className="sys-insp-section">
            <h4 className="sys-insp-title font-mono">Metadata</h4>
            <div className="sys-meta-list">
              <div className="sys-meta-row"><span className="sys-meta-k font-mono">STATUS</span><span className="sys-meta-v font-mono">{healthOk?'NOMINAL':loading?'...':'DEGRADED'}</span></div>
              <div className="sys-meta-row"><span className="sys-meta-k font-mono">DATABASE</span><span className="sys-meta-v font-mono" style={{color:healthOk?'var(--primary)':'var(--error)'}}>{status?.health?.database||'—'}</span></div>
              <div className="sys-meta-row"><span className="sys-meta-k font-mono">VERSION</span><span className="sys-meta-v font-mono">1.0.0</span></div>
            </div>
          </section>
        </div>
      </aside>
    </div>
  );
}

function MetricCard({label,icon,value,bar}) {
  return (
    <div className="sys-metric-card">
      <div className="sys-metric-top"><span className="sys-metric-label font-mono">{label}</span><span className="material-symbols-outlined" style={{color:'var(--primary)',fontSize:16}}>{icon}</span></div>
      <div className="sys-metric-val font-mono">{value}</div>
      {bar != null && <div className="sys-bar-wrap"><div className="sys-bar-fill" style={{width:`${bar}%`}}/></div>}
    </div>
  );
}

function StatsSection({title,data}) {
  if (data.error) return (
    <div className="sys-section"><h3 className="sys-section-title">{title}</h3><div className="sys-error"><span className="material-symbols-outlined">error</span>{data.error}</div></div>
  );
  return (
    <div className="sys-section">
      <h3 className="sys-section-title">{title}</h3>
      <div className="sys-stats-grid">
        {Object.entries(data).map(([k,v])=>(
          <div key={k} className="sys-stat-cell"><span className="sys-stat-k font-mono">{k.replace(/_/g,' ')}</span><span className="sys-stat-v font-mono">{typeof v==='object'?JSON.stringify(v):String(v)}</span></div>
        ))}
      </div>
    </div>
  );
}
