import { useState } from 'react';
import { getJobLogs } from '../services/api';

function ProvisioningJobsList({ jobs }) {
  const [expandedJob, setExpandedJob] = useState(null);
  const [logs, setLogs] = useState({});
  const [loadingLogs, setLoadingLogs] = useState({});

  const toggleJobExpansion = async (jobId) => {
    if (expandedJob === jobId) {
      setExpandedJob(null);
      return;
    }

    setExpandedJob(jobId);

    // Fetch logs if not already loaded
    if (!logs[jobId]) {
      try {
        setLoadingLogs({ ...loadingLogs, [jobId]: true });
        const response = await getJobLogs(jobId);
        setLogs({ ...logs, [jobId]: response.data.data?.log_output || '' });
      } catch (err) {
        console.error(`Failed to fetch logs for job ${jobId}:`, err);
        setLogs({ ...logs, [jobId]: 'Failed to load logs' });
      } finally {
        setLoadingLogs({ ...loadingLogs, [jobId]: false });
      }
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { className: 'status-badge status-pending', text: 'Pending', icon: '⏳' },
      running: { className: 'status-badge status-running', text: 'Running', icon: '▶' },
      completed: { className: 'status-badge status-completed', text: 'Completed', icon: '✓' },
      failed: { className: 'status-badge status-failed', text: 'Failed', icon: '✕' },
    };
    return badges[status] || badges.pending;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  if (!jobs || jobs.length === 0) {
    return (
      <div className="empty-state">
        <p>No provisioning jobs yet. Click "Run Playbook" to start.</p>
      </div>
    );
  }

  return (
    <div className="jobs-list">
      {jobs.map((job) => {
        const badge = getStatusBadge(job.status);
        const isExpanded = expandedJob === job.id;

        return (
          <div key={job.id} className={`job-card job-${job.status}`}>
            <div className="job-header" onClick={() => toggleJobExpansion(job.id)}>
              <div className="job-info">
                <h4>{job.playbook_name}</h4>
                <span className="job-timestamp">{formatTimestamp(job.created_at)}</span>
              </div>
              <div className="job-status">
                <span className={badge.className}>
                  {badge.icon} {badge.text}
                </span>
                <button className="expand-btn" type="button">
                  {isExpanded ? '▼' : '▶'}
                </button>
              </div>
            </div>

            {isExpanded && (
              <div className="job-details">
                <div className="job-metadata">
                  <div className="metadata-item">
                    <strong>Job ID:</strong> {job.id}
                  </div>
                  <div className="metadata-item">
                    <strong>Device ID:</strong> {job.device_id}
                  </div>
                  <div className="metadata-item">
                    <strong>Status:</strong> {job.status}
                  </div>
                  <div className="metadata-item">
                    <strong>Created:</strong> {formatTimestamp(job.created_at)}
                  </div>
                  {job.updated_at && (
                    <div className="metadata-item">
                      <strong>Updated:</strong> {formatTimestamp(job.updated_at)}
                    </div>
                  )}
                </div>

                <div className="job-logs">
                  <h5>Execution Logs</h5>
                  {loadingLogs[job.id] ? (
                    <div className="loading-state">Loading logs...</div>
                  ) : (
                    <pre className="log-output">
                      {logs[job.id] || job.log_output || 'No logs available yet.'}
                    </pre>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default ProvisioningJobsList;
