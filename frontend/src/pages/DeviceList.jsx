import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDevices, deleteDevice } from '../services/api';
import { safeGetArray } from '../utils/validation';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';

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
        <Link to="/devices/new" className="btn btn-primary">Add Device</Link>
      </div>

      {devices.length === 0 ? (
        <div className="empty-state">
          <p>No devices found</p>
          <Link to="/devices/new" className="btn btn-primary">Add Your First Device</Link>
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
                  <span className={`status-badge status-${device.status}`}>
                    {device.status}
                  </span>
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
                <Link to={`/devices/${device.id}`} className="btn btn-sm">View Details</Link>
                <Link to={`/devices/${device.id}/edit`} className="btn btn-sm">Edit</Link>
                <button
                  onClick={() => handleDelete(device.id)}
                  className="btn btn-sm btn-danger"
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

export default DeviceList;
