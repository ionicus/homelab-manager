import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getServices, getDevices, deleteService, updateServiceStatus } from '../services/api';
import { safeGetArray } from '../utils/validation';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import ServiceForm from '../components/ServiceForm';

function Services() {
  const [services, setServices] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showServiceForm, setShowServiceForm] = useState(false);
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);
  const [filterDevice, setFilterDevice] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [updatingStatus, setUpdatingStatus] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [servicesRes, devicesRes] = await Promise.all([
        getServices(),
        getDevices(),
      ]);

      setServices(safeGetArray(servicesRes));
      setDevices(safeGetArray(devicesRes));
      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  const handleDelete = async (serviceId, serviceName) => {
    if (window.confirm(`Are you sure you want to delete service "${serviceName}"?`)) {
      try {
        await deleteService(serviceId);
        fetchData();
      } catch (err) {
        const message = err.userMessage || 'Failed to delete service';
        alert(message);
      }
    }
  };

  const handleStatusToggle = async (serviceId, currentStatus) => {
    const newStatus = currentStatus === 'running' ? 'stopped' : 'running';
    setUpdatingStatus(prev => ({ ...prev, [serviceId]: true }));

    try {
      await updateServiceStatus(serviceId, newStatus);
      fetchData();
    } catch (err) {
      const message = err.userMessage || 'Failed to update service status';
      alert(message);
    } finally {
      setUpdatingStatus(prev => ({ ...prev, [serviceId]: false }));
    }
  };

  const handleAddService = (deviceId) => {
    setSelectedDeviceId(deviceId);
    setShowServiceForm(true);
  };

  const handleServiceUpdate = () => {
    setShowServiceForm(false);
    setSelectedDeviceId(null);
    fetchData();
  };

  const getDeviceName = (deviceId) => {
    const device = devices.find(d => d.id === deviceId);
    return device ? device.name : `Device ${deviceId}`;
  };

  const filteredServices = services.filter(service => {
    if (filterDevice !== 'all' && service.device_id !== parseInt(filterDevice)) {
      return false;
    }
    if (filterStatus !== 'all' && service.status !== filterStatus) {
      return false;
    }
    return true;
  });

  const servicesByStatus = {
    running: services.filter(s => s.status === 'running').length,
    stopped: services.filter(s => s.status === 'stopped').length,
    error: services.filter(s => s.status === 'error').length,
  };

  if (loading) return <LoadingSkeleton type="device-list" count={6} />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchData} />;

  return (
    <div className="services-page">
      <div className="page-header">
        <h1>Services ({services.length})</h1>
      </div>

      <div className="stats-grid">
        <div className="stat-card stat-card-primary">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>Total Services</h3>
            <p className="stat-value">{services.length}</p>
          </div>
        </div>
        <div className="stat-card stat-card-success">
          <div className="stat-icon">✓</div>
          <div className="stat-content">
            <h3>Running</h3>
            <p className="stat-value">{servicesByStatus.running}</p>
          </div>
        </div>
        <div className="stat-card stat-card-warning">
          <div className="stat-icon">⚠</div>
          <div className="stat-content">
            <h3>Error</h3>
            <p className="stat-value">{servicesByStatus.error}</p>
          </div>
        </div>
        <div className="stat-card stat-card-danger">
          <div className="stat-icon">⏸</div>
          <div className="stat-content">
            <h3>Stopped</h3>
            <p className="stat-value">{servicesByStatus.stopped}</p>
          </div>
        </div>
      </div>

      <div className="filters-bar">
        <div className="filter-group">
          <label htmlFor="filterDevice">Device:</label>
          <select
            id="filterDevice"
            value={filterDevice}
            onChange={(e) => setFilterDevice(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Devices</option>
            {devices.map(device => (
              <option key={device.id} value={device.id}>
                {device.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filterStatus">Status:</label>
          <select
            id="filterStatus"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Statuses</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div className="filter-results">
          Showing {filteredServices.length} of {services.length} services
        </div>
      </div>

      {showServiceForm && selectedDeviceId && (
        <ServiceForm
          deviceId={selectedDeviceId}
          onSuccess={handleServiceUpdate}
          onCancel={() => {
            setShowServiceForm(false);
            setSelectedDeviceId(null);
          }}
        />
      )}

      {filteredServices.length === 0 ? (
        <div className="empty-state">
          <p>No services found{filterDevice !== 'all' || filterStatus !== 'all' ? ' with the selected filters' : ''}</p>
          {services.length === 0 && devices.length > 0 && (
            <p>Add services to your devices to get started</p>
          )}
        </div>
      ) : (
        <div className="service-grid">
          {filteredServices.map(service => (
            <div key={service.id} className="service-card">
              <div className="service-header">
                <div className="service-title-group">
                  <h3>{service.name}</h3>
                  <Link
                    to={`/devices/${service.device_id}`}
                    className="device-link"
                    title="View device"
                  >
                    {getDeviceName(service.device_id)}
                  </Link>
                </div>
                <span className={`status-badge status-${service.status}`}>
                  {service.status}
                </span>
              </div>

              <div className="service-details">
                {service.port && (
                  <div className="service-detail">
                    <span className="detail-label">Port:</span>
                    <span className="detail-value">{service.port}</span>
                  </div>
                )}
                {service.protocol && (
                  <div className="service-detail">
                    <span className="detail-label">Protocol:</span>
                    <span className="detail-value">{service.protocol}</span>
                  </div>
                )}
                {service.health_check_url && (
                  <div className="service-detail">
                    <span className="detail-label">Health Check:</span>
                    <span className="detail-value health-url">{service.health_check_url}</span>
                  </div>
                )}
              </div>

              <div className="service-actions">
                <button
                  className={`btn btn-sm ${
                    service.status === 'running' ? 'btn-warning' : 'btn-success'
                  }`}
                  onClick={() => handleStatusToggle(service.id, service.status)}
                  disabled={updatingStatus[service.id]}
                  title={service.status === 'running' ? 'Stop service' : 'Start service'}
                >
                  {updatingStatus[service.id] ? '...' : (
                    service.status === 'running' ? 'Stop' : 'Start'
                  )}
                </button>
                <Link
                  to={`/devices/${service.device_id}`}
                  className="btn btn-sm"
                  title="View device"
                >
                  View Device
                </Link>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => handleDelete(service.id, service.name)}
                  title="Delete service"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Services;
