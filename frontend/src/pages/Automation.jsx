import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, MultiSelect, Group, Text } from '@mantine/core';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getAutomationJobs, getDevices } from '../services/api';
import { safeGetArray } from '../utils/validation';
import { formatShortTimestamp } from '../utils/formatting';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import StatusBadge from '../components/StatusBadge';
import AutomationForm from '../components/AutomationForm';

function Automation() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filterDevice, setFilterDevice] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [showDeviceSelector, setShowDeviceSelector] = useState(false);
  const [showAutomationForm, setShowAutomationForm] = useState(false);
  const [selectedDeviceIds, setSelectedDeviceIds] = useState([]);

  // Jobs query
  const {
    data: jobs = [],
    isLoading: jobsLoading,
    error: jobsError,
    refetch: refetchJobs,
  } = useQuery({
    queryKey: ['automation-jobs'],
    queryFn: async () => safeGetArray(await getAutomationJobs()),
  });

  // Devices query
  const { data: devices = [] } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => safeGetArray(await getDevices()),
  });

  const handleNewJobClick = () => {
    setShowDeviceSelector(true);
  };

  const handleDeviceSelect = () => {
    if (selectedDeviceIds.length > 0) {
      setShowDeviceSelector(false);
      setShowAutomationForm(true);
    }
  };

  const handleCancelDeviceSelector = () => {
    setShowDeviceSelector(false);
    setSelectedDeviceIds([]);
  };

  const handleAutomationSuccess = () => {
    setShowAutomationForm(false);
    setSelectedDeviceIds([]);
    queryClient.invalidateQueries({ queryKey: ['automation-jobs'] });
  };

  const handleAutomationCancel = () => {
    setShowAutomationForm(false);
    setSelectedDeviceIds([]);
  };

  if (jobsLoading) return <LoadingSkeleton type="list" />;
  if (jobsError) return <ErrorDisplay error={jobsError} onRetry={refetchJobs} />;

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

  // Filter to only devices with IP addresses (required for automation)
  const devicesWithIp = devices.filter(d => d.ip_address);

  return (
    <div className="automation-page">
      <div className="page-header">
        <h1>Automation</h1>
        <Button onClick={handleNewJobClick} disabled={devicesWithIp.length === 0}>
          New Job
        </Button>
      </div>

      {showDeviceSelector && (
        <div className="form-modal" onClick={handleCancelDeviceSelector}>
          <div className="form-modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Select Devices</h2>
            <Text size="sm" c="dimmed" mb="md">
              Choose one or more devices to run automation on:
            </Text>
            <MultiSelect
              placeholder="Select devices"
              data={devicesWithIp.map(d => ({ value: String(d.id), label: `${d.name} (${d.ip_address})` }))}
              value={selectedDeviceIds.map(String)}
              onChange={(values) => setSelectedDeviceIds(values.map(v => parseInt(v)))}
              searchable
              clearable
            />
            <Group mt="md" justify="flex-end">
              <Button variant="default" onClick={handleCancelDeviceSelector}>
                Cancel
              </Button>
              <Button onClick={handleDeviceSelect} disabled={selectedDeviceIds.length === 0}>
                Continue
              </Button>
            </Group>
          </div>
        </div>
      )}

      {showAutomationForm && selectedDeviceIds.length > 0 && (
        <AutomationForm
          deviceIds={selectedDeviceIds}
          devices={devicesWithIp}
          onSuccess={handleAutomationSuccess}
          onCancel={handleAutomationCancel}
        />
      )}

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
                    <td className="playbook-name">{job.action_name}</td>
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
