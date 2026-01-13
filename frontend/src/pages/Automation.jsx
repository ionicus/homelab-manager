import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAutomationJobs, getDevices } from '../services/api';
import { safeGetArray } from '../utils/validation';
import { formatShortTimestamp } from '../utils/formatting';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import StatusBadge from '../components/StatusBadge';

function Automation() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterDevice, setFilterDevice] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [jobsRes, devicesRes] = await Promise.all([
        getAutomationJobs(),
        getDevices(),
      ]);

      setJobs(safeGetArray(jobsRes));
      setDevices(safeGetArray(devicesRes));
      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  if (loading) return <LoadingSkeleton type="list" />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchData} />;

  // Apply filters
  const filteredJobs = jobs.filter((job) => {
    if (filterDevice && job.device_id !== parseInt(filterDevice)) {
      return false;
    }
    if (filterStatus && job.status !== filterStatus) {
      return false;
    }
    return true;
  });

  // Calculate statistics
  const totalJobs = jobs.length;
  const runningJobs = jobs.filter((j) => j.status === 'running').length;
  const completedJobs = jobs.filter((j) => j.status === 'completed').length;
  const failedJobs = jobs.filter((j) => j.status === 'failed').length;

  const getDeviceName = (deviceId) => {
    const device = devices.find((d) => d.id === deviceId);
    return device?.name || `Device ${deviceId}`;
  };

  return (
    <div className="automation-page">
      <div className="page-header">
        <h1>Automation</h1>
      </div>

      <div className="stats-grid">
        <div className="stat-card stat-card-primary">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <div className="stat-value">{totalJobs}</div>
            <div className="stat-label">Total Jobs</div>
          </div>
        </div>

        <div className="stat-card stat-card-info">
          <div className="stat-icon">▶</div>
          <div className="stat-content">
            <div className="stat-value">{runningJobs}</div>
            <div className="stat-label">Running</div>
          </div>
        </div>

        <div className="stat-card stat-card-success">
          <div className="stat-icon">✓</div>
          <div className="stat-content">
            <div className="stat-value">{completedJobs}</div>
            <div className="stat-label">Completed</div>
          </div>
        </div>

        <div className="stat-card stat-card-danger">
          <div className="stat-icon">✕</div>
          <div className="stat-content">
            <div className="stat-value">{failedJobs}</div>
            <div className="stat-label">Failed</div>
          </div>
        </div>
      </div>

      <div className="filters-bar">
        <div className="filter-group">
          <label htmlFor="filter-device">Device:</label>
          <select
            id="filter-device"
            className="filter-select"
            value={filterDevice}
            onChange={(e) => setFilterDevice(e.target.value)}
          >
            <option value="">All Devices</option>
            {devices.map((device) => (
              <option key={device.id} value={device.id}>
                {device.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-status">Status:</label>
          <select
            id="filter-status"
            className="filter-select"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      <div className="automation-jobs-list">
        <h2>Job History ({filteredJobs.length})</h2>

        {filteredJobs.length === 0 ? (
          <div className="empty-state">
            <p>No automation jobs found.</p>
          </div>
        ) : (
          <div className="jobs-table-container">
            <table className="jobs-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Device</th>
                  <th>Playbook</th>
                  <th>Status</th>
                  <th>Started</th>
                  <th>Completed</th>
                </tr>
              </thead>
              <tbody>
                {filteredJobs.map((job) => (
                  <tr
                    key={job.id}
                    className={`job-row job-${job.status} clickable-row`}
                    onClick={() => navigate(`/automation/jobs/${job.id}`)}
                  >
                    <td className="job-id">#{job.id}</td>
                    <td>
                      <Link
                        to={`/devices/${job.device_id}`}
                        className="device-link"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {getDeviceName(job.device_id)}
                      </Link>
                    </td>
                    <td className="playbook-name">{job.playbook_name}</td>
                    <td>
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="timestamp">{formatShortTimestamp(job.started_at)}</td>
                    <td className="timestamp">{formatShortTimestamp(job.completed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Automation;
