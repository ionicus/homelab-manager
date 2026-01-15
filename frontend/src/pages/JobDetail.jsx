import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Group, Progress, Badge, Text, Paper, Tooltip } from '@mantine/core';
import { IconPlayerStop, IconRefresh, IconArrowLeft } from '@tabler/icons-react';
import {
  getJobStatus,
  getJobLogs,
  getDevice,
  triggerAutomation,
  cancelJob,
  getJobLogStreamUrl,
} from '../services/api';
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
  const [cancelling, setCancelling] = useState(false);
  const [streamingActive, setStreamingActive] = useState(false);

  const eventSourceRef = useRef(null);
  const logContainerRef = useRef(null);

  // Auto-scroll logs to bottom
  const scrollToBottom = useCallback(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, []);

  // Start SSE streaming for real-time logs
  const startStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = getJobLogStreamUrl(id, true);
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;
    setStreamingActive(true);

    eventSource.onmessage = (event) => {
      // Append new log line
      setLogs((prev) => prev + (prev ? '\n' : '') + event.data);
      scrollToBottom();
    };

    eventSource.addEventListener('status', (event) => {
      const data = JSON.parse(event.data);
      setJob((prev) => prev ? { ...prev, status: data.status, progress: data.progress } : prev);
    });

    eventSource.addEventListener('complete', () => {
      eventSource.close();
      setStreamingActive(false);
      // Refresh job data to get final status
      fetchJobData(false);
    });

    eventSource.addEventListener('error', (event) => {
      if (event.data) {
        console.warn('SSE error:', event.data);
      }
      // Fall back to polling if streaming fails
      eventSource.close();
      setStreamingActive(false);
    });

    eventSource.onerror = () => {
      eventSource.close();
      setStreamingActive(false);
    };
  }, [id, scrollToBottom]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Fetch job data
  const fetchJobData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setError(null);
    try {
      const [jobRes, logsRes] = await Promise.all([getJobStatus(id), getJobLogs(id)]);

      const jobData = jobRes.data;
      setJob(jobData);
      setLogs(logsRes.data.log_output || '');

      // Fetch device info
      if (jobData.device_id) {
        const deviceRes = await getDevice(jobData.device_id);
        setDevice(deviceRes.data || deviceRes);
      }

      // Start streaming if job is running
      if (jobData.status === 'running' && !streamingActive) {
        startStreaming();
      }

      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobData();
  }, [id]);

  // Auto-refresh for running/pending jobs (fallback when SSE not available)
  useEffect(() => {
    if (!job || streamingActive) return;

    if (job.status === 'running' || job.status === 'pending') {
      const interval = setInterval(() => fetchJobData(false), 5000);
      return () => clearInterval(interval);
    }
  }, [job?.status, streamingActive]);

  const handleRerun = async () => {
    if (!job || !window.confirm(`Re-run ${job.action_name || job.playbook_name} on ${device?.name || 'this device'}?`)) {
      return;
    }

    try {
      setRerunning(true);
      await triggerAutomation({
        deviceId: job.device_ids ? null : job.device_id,
        deviceIds: job.device_ids || null,
        actionName: job.action_name || job.playbook_name,
        executorType: job.executor_type || 'ansible',
      });
      alert('New job created successfully! Refresh the page to see it.');
    } catch (err) {
      console.error('Failed to re-run job:', err);
      alert('Failed to re-run job: ' + (err.userMessage || err.message));
    } finally {
      setRerunning(false);
    }
  };

  const handleCancel = async () => {
    if (!job) return;

    const confirmMsg =
      job.status === 'pending'
        ? 'Cancel this pending job?'
        : 'Request cancellation of this running job? It will stop at the next checkpoint.';

    if (!window.confirm(confirmMsg)) return;

    try {
      setCancelling(true);
      const response = await cancelJob(job.id);
      const data = response.data;

      // Update local state
      if (data.status === 'cancelled') {
        setJob((prev) => ({ ...prev, status: 'cancelled' }));
      } else {
        setJob((prev) => ({ ...prev, cancel_requested: true }));
      }

      alert(data.message);
    } catch (err) {
      console.error('Failed to cancel job:', err);
      alert('Failed to cancel job: ' + (err.userMessage || err.message));
    } finally {
      setCancelling(false);
    }
  };

  if (loading) return <LoadingSkeleton type="detail" />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchJobData} />;
  if (!job) return <ErrorDisplay error="Job not found" onRetry={fetchJobData} />;

  const isRunning = job.status === 'running';
  const isPending = job.status === 'pending';
  const canCancel = (isRunning || isPending) && !job.cancel_requested;
  const progress = job.progress || 0;

  return (
    <div className="job-detail">
      <div className="page-header">
        <div className="header-content">
          <h1>Automation Job #{job.id}</h1>
          <Group gap="xs">
            <StatusBadge status={job.status} />
            {job.cancel_requested && job.status === 'running' && (
              <Badge color="orange" variant="light">
                Cancellation Requested
              </Badge>
            )}
            {streamingActive && (
              <Badge color="blue" variant="dot">
                Live
              </Badge>
            )}
          </Group>
        </div>
        <Group gap="sm">
          {canCancel && (
            <Button
              color="red"
              variant="light"
              onClick={handleCancel}
              disabled={cancelling}
              leftSection={<IconPlayerStop size={16} />}
            >
              {cancelling ? 'Cancelling...' : 'Cancel Job'}
            </Button>
          )}
          <Button
            onClick={handleRerun}
            disabled={rerunning || isRunning || isPending}
            leftSection={<IconRefresh size={16} />}
          >
            {rerunning ? 'Creating...' : 'Re-run'}
          </Button>
          <Button variant="outline" component={Link} to="/automation" leftSection={<IconArrowLeft size={16} />}>
            Back
          </Button>
        </Group>
      </div>

      {/* Progress Section */}
      {(isRunning || isPending) && (
        <Paper withBorder p="md" mb="md" radius="md">
          <Group justify="space-between" mb="xs">
            <Text size="sm" fw={500}>
              Execution Progress
            </Text>
            <Text size="sm" c="dimmed">
              {job.tasks_completed || 0} / {job.task_count || '?'} tasks
            </Text>
          </Group>
          <Progress
            value={progress}
            size="lg"
            radius="md"
            color={isPending ? 'gray' : 'blue'}
            animated={isRunning}
            striped={isRunning}
          />
          <Text size="xs" c="dimmed" mt="xs" ta="center">
            {isPending ? 'Waiting to start...' : `${progress}% complete`}
          </Text>
        </Paper>
      )}

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
              <span className="info-label">Executor</span>
              <span className="info-value">{job.executor_type || 'ansible'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Action</span>
              <span className="info-value playbook-name">{job.action_name || job.playbook_name}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Status</span>
              <span className="info-value">
                <StatusBadge status={job.status} />
              </span>
            </div>
            {job.error_category && (
              <div className="info-item">
                <span className="info-label">Error Type</span>
                <span className="info-value">
                  <Badge color="red" variant="light">
                    {job.error_category}
                  </Badge>
                </span>
              </div>
            )}
            <div className="info-item">
              <span className="info-label">Started At</span>
              <span className="info-value">{formatTimestamp(job.started_at)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Completed At</span>
              <span className="info-value">{formatTimestamp(job.completed_at || job.cancelled_at)}</span>
            </div>
          </div>
        </div>

        <div className="detail-section">
          <Group justify="space-between" mb="sm">
            <h2 style={{ margin: 0 }}>Execution Logs</h2>
            {isRunning && (
              <Tooltip label={streamingActive ? 'Receiving real-time updates' : 'Polling every 5 seconds'}>
                <Badge color={streamingActive ? 'green' : 'yellow'} variant="light">
                  {streamingActive ? 'Streaming' : 'Polling'}
                </Badge>
              </Tooltip>
            )}
          </Group>
          <div className="log-output-container" ref={logContainerRef} style={{ maxHeight: '500px', overflowY: 'auto' }}>
            {logs ? (
              <pre className="log-output">{logs}</pre>
            ) : (
              <div className="empty-state">
                <p>{isPending ? 'Logs will appear when the job starts...' : 'No logs available yet.'}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default JobDetail;
