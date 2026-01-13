import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Group } from '@mantine/core';
import { getService, getDevice, updateServiceStatus, deleteService } from '../services/api';
import { formatTimestamp } from '../utils/formatting';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import StatusBadge from '../components/StatusBadge';
import ServiceForm from '../components/ServiceForm';

function ServiceDetail() {
  const { id } = useParams();
  const [service, setService] = useState(null);
  const [device, setDevice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);

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

  const handleServiceUpdate = () => {
    setShowEditForm(false);
    fetchServiceData();
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete service "${service.name}"?`)) {
      return;
    }

    try {
      await deleteService(service.id);
      window.location.href = '/services';
    } catch (err) {
      alert('Failed to delete service: ' + (err.userMessage || err.message));
    }
  };

  if (loading) return <LoadingSkeleton type="detail" />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchServiceData} />;
  if (!service) return <ErrorDisplay error="Service not found" onRetry={fetchServiceData} />;

  return (
    <div className="service-detail-page">
      <div className="page-header">
        <div className="header-content">
          <h1>{service.name}</h1>
          <StatusBadge status={service.status} />
        </div>
        <Group gap="sm">
          <Button
            onClick={handleStatusToggle}
            color={service.status === 'running' ? 'yellow' : 'green'}
            disabled={updatingStatus || service.status === 'error'}
          >
            {updatingStatus ? 'Updating...' : service.status === 'running' ? 'Stop Service' : 'Start Service'}
          </Button>
          <Button onClick={() => setShowEditForm(true)}>
            Edit
          </Button>
          <Button onClick={handleDelete} color="red">
            Delete
          </Button>
          <Button component={Link} to="/services" variant="default">
            Back to Services
          </Button>
        </Group>
      </div>

      {showEditForm && (
        <ServiceForm
          deviceId={service.device_id}
          serviceId={service.id}
          onSuccess={handleServiceUpdate}
          onCancel={() => setShowEditForm(false)}
        />
      )}

      <div className="detail-overview">
        <div className="overview-card">
          <div className="overview-icon">⚙️</div>
          <div className="overview-content">
            <span className="overview-label">Port</span>
            <span className="overview-value">{service.port || 'Not set'}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">🔌</div>
          <div className="overview-content">
            <span className="overview-label">Protocol</span>
            <span className="overview-value">{service.protocol || 'Not set'}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">🏥</div>
          <div className="overview-content">
            <span className="overview-label">Health Check</span>
            <span className="overview-value">{service.health_check_url ? 'Configured' : 'None'}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">📅</div>
          <div className="overview-content">
            <span className="overview-label">Created</span>
            <span className="overview-value">{new Date(service.created_at).toLocaleDateString()}</span>
          </div>
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
                <StatusBadge status={service.status} />
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
                <StatusBadge status={device.status} />
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
              <Button component={Link} to={`/devices/${device.id}`} size="sm">
                View Full Device Details
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ServiceDetail;
