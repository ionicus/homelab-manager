import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Group } from '@mantine/core';
import { getJobStatus, getJobLogs, getDevice, triggerProvisioning } from '../services/api';
import { formatTimestamp } from '../utils/formatting';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import StatusBadge from '../components/StatusBadge';

function JobDetail() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [device, setDevice] = useState(null);
  const [logs, setLogs] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rerunning, setRerunning] = useState(false);

  useEffect(() => {
    fetchJobData();
    // Auto-refresh if job is running
    const interval = setInterval(() => {
      if (job?.status === 'running') {
        fetchJobData();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [id, job?.status]);

  const fetchJobData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [jobRes, logsRes] = await Promise.all([
        getJobStatus(id),
        getJobLogs(id),
      ]);

      const jobData = jobRes.data;
      setJob(jobData);
      setLogs(logsRes.data.log_output || '');

      // Fetch device info
      if (jobData.device_id) {
        const deviceRes = await getDevice(jobData.device_id);
        setDevice(deviceRes.data || deviceRes);
      }

      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    if (!job || !window.confirm(`Re-run ${job.playbook_name} on ${device?.name || 'this device'}?`)) {
      return;
    }

    try {
      setRerunning(true);
      await triggerProvisioning(job.device_id, job.playbook_name);
      // Optionally redirect to new job or show success message
      alert('New job created successfully! Refresh the page to see it.');
    } catch (err) {
      console.error('Failed to re-run job:', err);
      alert('Failed to re-run job: ' + (err.userMessage || err.message));
    } finally {
      setRerunning(false);
    }
  };

  if (loading) return <LoadingSkeleton type="detail" />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchJobData} />;
  if (!job) return <ErrorDisplay error="Job not found" onRetry={fetchJobData} />;

  return (
    <div className="job-detail">
      <div className="page-header">
        <div className="header-content">
          <h1>Automation Job #{job.id}</h1>
          <StatusBadge status={job.status} />
        </div>
        <Group gap="sm">
          <Button
            onClick={handleRerun}
            disabled={rerunning || job.status === 'running'}
          >
            {rerunning ? 'Creating...' : 'Re-run Playbook'}
          </Button>
          <Button
            variant="outline"
            component={Link}
            to="/automation"
          >
            Back to Automation
          </Button>
        </Group>
      </div>

      <div className="detail-sections">
        <div className="detail-section">
          <h2>Job Information</h2>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Job ID</span>
              <span className="info-value">#{job.id}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Device</span>
              <span className="info-value">
                {device ? (
                  <Link to={`/devices/${device.id}`} className="device-link">
                    {device.name}
                  </Link>
                ) : (
                  `Device ${job.device_id}`
                )}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Playbook</span>
              <span className="info-value playbook-name">{job.playbook_name}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Status</span>
              <span className="info-value">
                <StatusBadge status={job.status} />
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Started At</span>
              <span className="info-value">{formatTimestamp(job.started_at)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Completed At</span>
              <span className="info-value">{formatTimestamp(job.completed_at)}</span>
            </div>
          </div>
        </div>

        <div className="detail-section">
          <h2>Execution Logs</h2>
          {job.status === 'running' && (
            <div className="log-info">
              <span className="spinner"></span> Job is currently running... (auto-refreshing every 3 seconds)
            </div>
          )}
          <div className="log-output-container">
            {logs ? (
              <pre className="log-output">{logs}</pre>
            ) : (
              <div className="empty-state">
                <p>No logs available yet.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default JobDetail;
