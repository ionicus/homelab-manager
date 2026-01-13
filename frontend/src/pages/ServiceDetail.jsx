import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getService, getDevice, updateServiceStatus } from '../services/api';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';

function ServiceDetail() {
  const { id } = useParams();
  const [service, setService] = useState(null);
  const [device, setDevice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  useEffect(() => {
    fetchServiceData();
  }, [id]);

  const fetchServiceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const serviceRes = await getService(id);
      const serviceData = serviceRes.data;
      setService(serviceData);

      // Fetch device info
      if (serviceData.device_id) {
        const deviceRes = await getDevice(serviceData.device_id);
        setDevice(deviceRes.data || deviceRes);
      }

      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  const handleStatusToggle = async () => {
    if (!service) return;

    const newStatus = service.status === 'running' ? 'stopped' : 'running';
    const action = newStatus === 'running' ? 'start' : 'stop';

    if (!window.confirm(`Are you sure you want to ${action} ${service.name}?`)) {
      return;
    }

    try {
      setUpdatingStatus(true);
      await updateServiceStatus(service.id, newStatus);
      await fetchServiceData(); // Refresh data
    } catch (err) {
      console.error('Failed to update service status:', err);
      alert('Failed to update service status: ' + (err.userMessage || err.message));
    } finally {
      setUpdatingStatus(false);
    }
  };

  if (loading) return <LoadingSkeleton type="detail" />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchServiceData} />;
  if (!service) return <ErrorDisplay error="Service not found" onRetry={fetchServiceData} />;

  const getStatusBadge = (status) => {
    const badges = {
      running: { className: 'status-badge status-running', text: 'Running', icon: '▶' },
      stopped: { className: 'status-badge status-stopped', text: 'Stopped', icon: '⏸' },
      error: { className: 'status-badge status-error', text: 'Error', icon: '⚠' },
    };
    return badges[status] || badges.stopped;
  };

  const badge = getStatusBadge(service.status);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="service-detail">
      <div className="page-header">
        <div className="header-content">
          <h1>{service.name}</h1>
          <span className={badge.className}>
            {badge.icon} {badge.text}
          </span>
        </div>
        <div>
          <button
            onClick={handleStatusToggle}
            className={service.status === 'running' ? 'btn btn-warning' : 'btn btn-success'}
            disabled={updatingStatus || service.status === 'error'}
          >
            {updatingStatus ? 'Updating...' : service.status === 'running' ? 'Stop Service' : 'Start Service'}
          </button>
          <Link to="/services" className="btn">Back to Services</Link>
        </div>
      </div>

      <div className="detail-sections">
        <div className="detail-section">
          <h2>Service Information</h2>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Service ID</span>
              <span className="info-value">#{service.id}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Device</span>
              <span className="info-value">
                {device ? (
                  <Link to={`/devices/${device.id}`} className="device-link">
                    {device.name}
                  </Link>
                ) : (
                  `Device ${service.device_id}`
                )}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Service Name</span>
              <span className="info-value">{service.name}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Status</span>
              <span className="info-value">
                <span className={badge.className}>
                  {badge.icon} {badge.text}
                </span>
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Port</span>
              <span className="info-value">{service.port || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Protocol</span>
              <span className="info-value">{service.protocol || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Created At</span>
              <span className="info-value">{formatTimestamp(service.created_at)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Updated At</span>
              <span className="info-value">{formatTimestamp(service.updated_at)}</span>
            </div>
          </div>
        </div>

        {service.health_check_url && (
          <div className="detail-section">
            <h2>Health Check</h2>
            <div className="health-check-panel">
              <div className="health-check-info">
                <span className="info-label">Health Check URL</span>
                <a
                  href={service.health_check_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="health-check-link"
                >
                  {service.health_check_url}
                </a>
              </div>
              <p className="health-check-description">
                Click the link above to check the service health endpoint in a new tab.
              </p>
            </div>
          </div>
        )}

        {device && (
          <div className="detail-section">
            <h2>Device Details</h2>
            <div className="device-summary">
              <div className="device-summary-header">
                <h3>{device.name}</h3>
                <span className={`status-badge status-${device.status}`}>
                  {device.status}
                </span>
              </div>
              <div className="device-summary-info">
                <div className="device-info-item">
                  <span className="label">Type:</span>
                  <span className="value">{device.type}</span>
                </div>
                <div className="device-info-item">
                  <span className="label">IP Address:</span>
                  <span className="value">{device.ip_address || 'Not set'}</span>
                </div>
                <div className="device-info-item">
                  <span className="label">MAC Address:</span>
                  <span className="value">{device.mac_address || 'Not set'}</span>
                </div>
              </div>
              <Link to={`/devices/${device.id}`} className="btn btn-sm">
                View Full Device Details
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ServiceDetail;
