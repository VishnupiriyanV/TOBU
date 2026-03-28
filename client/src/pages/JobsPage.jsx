import { useState, useEffect, useCallback } from 'react';
import { getJobs, retryJob, cancelJob } from '../api';
import './JobsPage.css';

const STATUS_FILTERS = [null, 'running', 'queued', 'done', 'failed', 'cancelled'];
const STATUS_LABELS = ['All', 'Running', 'Queued', 'Done', 'Failed', 'Cancelled'];

function statusDot(status) {
  const map = {
    running:   'status-dot--running',
    queued:    'status-dot--queued',
    done:      'status-dot--done',
    failed:    'status-dot--failed',
    cancelled: 'status-dot--cancelled',
  };
  return map[status] || 'status-dot--queued';
}

function fileName(path) {
  return path?.split(/[/\\]/).pop() || path;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await getJobs(filter, 200);
      setJobs(data.items || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    setLoading(true);
    fetchJobs();
    const id = setInterval(fetchJobs, 5000);
    return () => clearInterval(id);
  }, [fetchJobs]);

  const handleRetry = async (id) => {
    try {
      await retryJob(id);
      fetchJobs();
    } catch { /* ignore */ }
  };

  const handleCancel = async (id) => {
    try {
      await cancelJob(id);
      fetchJobs();
    } catch { /* ignore */ }
  };

  // Compute metrics
  const total = jobs.length;
  const running = jobs.filter(j => j.status === 'running').length;
  const doneCount = jobs.filter(j => j.status === 'done').length;
  const failedCount = jobs.filter(j => j.status === 'failed').length;
  const successRate = total > 0 ? ((doneCount / total) * 100).toFixed(1) : '0.0';

  return (
    <div className="jobs-page">
      {/* Table Area */}
      <div className="jobs-main">
        {/* Breadcrumb / Actions */}
        <div className="jobs-action-bar">
          <div className="jobs-breadcrumb font-mono">
            <span>SYSTEM</span>
            <span style={{ opacity: 0.3 }}>/</span>
            <span style={{ color: 'var(--primary)', fontWeight: 700 }}>JOB_QUEUE</span>
          </div>
          <div className="jobs-actions">
            {STATUS_FILTERS.map((s, i) => (
              <button
                key={i}
                className={`jobs-filter-btn ${filter === s ? 'jobs-filter-btn--active' : ''}`}
                onClick={() => setFilter(s)}
              >
                {STATUS_LABELS[i]}
              </button>
            ))}
          </div>
        </div>

        {/* Metrics */}
        <div className="jobs-metrics">
          <div className="jobs-metric">
            <div className="jobs-metric-label font-mono">Total Jobs</div>
            <div className="jobs-metric-value font-mono">{total}</div>
          </div>
          <div className="jobs-metric">
            <div className="jobs-metric-label font-mono">Running</div>
            <div className="jobs-metric-value font-mono" style={{ color: 'var(--primary)' }}>{running}</div>
          </div>
          <div className="jobs-metric">
            <div className="jobs-metric-label font-mono">Success Rate</div>
            <div className="jobs-metric-value font-mono">{total > 0 ? `${successRate}%` : 'N/A'}</div>
          </div>
          <div className="jobs-metric">
            <div className="jobs-metric-label font-mono">Failed</div>
            <div className="jobs-metric-value font-mono" style={{ color: 'var(--error)' }}>{failedCount}</div>
          </div>
        </div>

        {/* Table */}
        <div className="jobs-table-wrap">
          {error && (
            <div className="search-error" style={{ margin: 16 }}>
              <span className="material-symbols-outlined">error</span>
              {error}
            </div>
          )}

          <table className="jobs-table" id="jobs-table">
            <thead>
              <tr>
                <th className="font-mono">ID</th>
                <th className="font-mono">Source</th>
                <th className="font-mono">Status</th>
                <th className="font-mono">Progress</th>
                <th className="font-mono">Stage</th>
                <th className="font-mono" style={{ textAlign: 'right' }}>Ops</th>
              </tr>
            </thead>
            <tbody>
              {loading && jobs.length === 0 && (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: 32, color: 'var(--outline)' }}>Loading jobs...</td></tr>
              )}
              {!loading && jobs.length === 0 && (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: 32, color: 'var(--outline)' }}>No jobs found</td></tr>
              )}
              {jobs.map((job) => {
                const isSelected = selectedJob?.id === job.id;
                return (
                  <tr
                    key={job.id}
                    className={`jobs-row ${isSelected ? 'jobs-row--active' : ''}`}
                    onClick={() => setSelectedJob(job)}
                  >
                    <td className="font-mono jobs-id">#{job.id}</td>
                    <td>
                      <div className="jobs-source">
                        <span className="material-symbols-outlined" style={{ fontSize: 16, color: 'var(--outline)' }}>description</span>
                        <span className="jobs-source-name">{fileName(job.file_path)}</span>
                      </div>
                    </td>
                    <td>
                      <div className="jobs-status">
                        <span className={`status-dot ${statusDot(job.status)}`} />
                        <span className="font-mono jobs-status-label">{job.status}</span>
                      </div>
                    </td>
                    <td style={{ width: 160 }}>
                      <div className="jobs-progress">
                        <div className="jobs-progress-info font-mono">
                          <span>{Math.round(job.progress * 100)}%</span>
                        </div>
                        <div className="jobs-progress-bar">
                          <div
                            className={`jobs-progress-fill ${job.status === 'failed' ? 'jobs-progress-fill--error' : ''}`}
                            style={{ width: `${job.progress * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`jobs-stage-badge font-mono ${job.status === 'failed' ? 'jobs-stage-badge--error' : ''}`}>
                        {job.stage}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div className="jobs-ops" onClick={(e) => e.stopPropagation()}>
                        {(job.status === 'failed' || job.status === 'cancelled') && (
                          <button className="jobs-op-btn" title="Retry" onClick={() => handleRetry(job.id)}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>refresh</span>
                          </button>
                        )}
                        {(job.status === 'running' || job.status === 'queued') && (
                          <button className="jobs-op-btn jobs-op-btn--cancel" title="Cancel" onClick={() => handleCancel(job.id)}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>close</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="jobs-table-footer font-mono">
          <span>Displaying {jobs.length} jobs</span>
        </div>
      </div>

      {/* Inspector */}
      <div className="jobs-inspector">
        <div className="jobs-inspector-header">
          <div className="jobs-inspector-title">
            <span className="material-symbols-outlined" style={{ fontSize: 16, color: 'var(--primary)' }}>analytics</span>
            <span>Job Inspector</span>
          </div>
        </div>
        <div className="jobs-inspector-body">
          {selectedJob ? (
            <JobInspector job={selectedJob} onRetry={handleRetry} onCancel={handleCancel} />
          ) : (
            <div className="search-empty" style={{ padding: '40px 20px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: 40, opacity: 0.15 }}>assignment</span>
              <p>Select a job to inspect</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function JobInspector({ job, onRetry, onCancel }) {
  return (
    <div className="job-detail">
      {/* Progress visual */}
      <div className="job-detail-progress-section">
        <div className="job-detail-status">
          <span className={`status-dot ${statusDot(job.status)}`} />
          <span className="font-mono" style={{ fontSize: 11, textTransform: 'uppercase' }}>{job.status}</span>
          <span className="font-mono" style={{ fontSize: 11, marginLeft: 'auto', color: 'var(--primary)' }}>
            {Math.round(job.progress * 100)}%
          </span>
        </div>
        <div className="jobs-progress-bar" style={{ height: 4 }}>
          <div
            className={`jobs-progress-fill ${job.status === 'failed' ? 'jobs-progress-fill--error' : ''}`}
            style={{ width: `${job.progress * 100}%` }}
          />
        </div>
      </div>

      {/* Actions */}
      <div className="job-detail-actions">
        {(job.status === 'failed' || job.status === 'cancelled') && (
          <button className="job-action-btn" onClick={() => onRetry(job.id)}>
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>refresh</span>
            Retry Job
          </button>
        )}
        {(job.status === 'running' || job.status === 'queued') && (
          <button className="job-action-btn job-action-btn--cancel" onClick={() => onCancel(job.id)}>
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>close</span>
            Cancel Job
          </button>
        )}
      </div>

      {/* Metadata */}
      <div className="inspector-section">
        <h4 className="inspector-section-title" style={{ color: 'var(--outline)' }}>Job Parameters</h4>
        <div className="inspector-meta-grid">
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">Job ID</span>
            <span className="inspector-meta-value">#{job.id}</span>
          </div>
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">Stage</span>
            <span className="inspector-meta-value">{job.stage}</span>
          </div>
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">Source Type</span>
            <span className="inspector-meta-value">{job.source_type || '—'}</span>
          </div>
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">Retries</span>
            <span className="inspector-meta-value">{job.retries} / {job.max_retries}</span>
          </div>
          <div className="inspector-meta-cell" style={{ gridColumn: '1 / -1' }}>
            <span className="inspector-meta-key">File Path</span>
            <span className="inspector-meta-value">{job.file_path}</span>
          </div>
          {job.error_message && (
            <div className="inspector-meta-cell" style={{ gridColumn: '1 / -1', borderLeft: '2px solid var(--error)' }}>
              <span className="inspector-meta-key" style={{ color: 'var(--error)' }}>Error</span>
              <span className="inspector-meta-value" style={{ color: 'var(--error)' }}>{job.error_message}</span>
            </div>
          )}
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">Created</span>
            <span className="inspector-meta-value">{job.created_at}</span>
          </div>
          <div className="inspector-meta-cell">
            <span className="inspector-meta-key">Updated</span>
            <span className="inspector-meta-value">{job.updated_at}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
