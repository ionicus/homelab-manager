import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@mantine/core';
import { getDevices, deleteDevice } from '../services/api';
import { safeGetArray } from '../utils/validation';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import StatusBadge from '../components/StatusBadge';

function DeviceList() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getDevices();
      const devicesData = safeGetArray(response);
      setDevices(devicesData);
      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this device?')) {
      try {
        await deleteDevice(id);
        fetchDevices();
      } catch (err) {
        const message = err.userMessage || 'Failed to delete device';
        alert(message);
      }
    }
  };

  if (loading) return <LoadingSkeleton type="device-list" count={6} />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchDevices} />;

  const activeDevices = devices.filter(d => d.status === 'active').length;
  const maintenanceDevices = devices.filter(d => d.status === 'maintenance').length;
  const inactiveDevices = devices.filter(d => d.status === 'inactive').length;

  const getDeviceIcon = (type) => {
    const icons = {
      server: '🖥️',
      vm: '💻',
      container: '📦',
      network: '🌐',
      storage: '💾'
    };
    return icons[type] || '🖥️';
  };

  return (
    <div className="device-list-page">
      <div className="page-header">
        <h1>All Devices ({devices.length})</h1>
        <Button component={Link} to="/devices/new">Add Device</Button>
      </div>

      {devices.length > 0 && (
        <div className="stats-grid">
          <div className="stat-card stat-card-primary">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <h3>Total Devices</h3>
              <p className="stat-value">{devices.length}</p>
            </div>
          </div>
          <div className="stat-card stat-card-success">
            <div className="stat-icon">✓</div>
            <div className="stat-content">
              <h3>Active</h3>
              <p className="stat-value">{activeDevices}</p>
            </div>
          </div>
          <div className="stat-card stat-card-warning">
            <div className="stat-icon">⚠</div>
            <div className="stat-content">
              <h3>Maintenance</h3>
              <p className="stat-value">{maintenanceDevices}</p>
            </div>
          </div>
          <div className="stat-card stat-card-danger">
            <div className="stat-icon">⏸</div>
            <div className="stat-content">
              <h3>Inactive</h3>
              <p className="stat-value">{inactiveDevices}</p>
            </div>
          </div>
        </div>
      )}

      {devices.length === 0 ? (
        <div className="empty-state">
          <p>No devices found</p>
          <Button component={Link} to="/devices/new">Add Your First Device</Button>
        </div>
      ) : (
        <div className="devices-grid">
          {devices.map(device => (
            <div key={device.id} className="device-card">
              <Link to={`/devices/${device.id}`} className="device-card-link">
                <div className="device-card-header">
                  <div className="device-card-title">
                    <span className="device-card-icon">{getDeviceIcon(device.type)}</span>
                    <h3>{device.name}</h3>
                  </div>
                  <StatusBadge status={device.status} />
                </div>
                <div className="device-card-body">
                  <div className="device-card-info">
                    <span className="info-label">Type</span>
                    <span className="info-value">{device.type}</span>
                  </div>
                  <div className="device-card-info">
                    <span className="info-label">IP Address</span>
                    <span className="info-value">{device.ip_address || 'Not set'}</span>
                  </div>
                  {device.mac_address && (
                    <div className="device-card-info">
                      <span className="info-label">MAC Address</span>
                      <span className="info-value">{device.mac_address}</span>
                    </div>
                  )}
                </div>
              </Link>
              <div className="device-card-actions">
                <Button component={Link} to={`/devices/${device.id}`} size="sm" variant="default">View Details</Button>
                <Button component={Link} to={`/devices/${device.id}/edit`} size="sm" variant="default">Edit</Button>
                <Button
                  onClick={() => handleDelete(device.id)}
                  size="sm"
                  color="red"
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DeviceList;
