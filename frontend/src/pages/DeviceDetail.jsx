import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getDevice, getDeviceServices, getDeviceMetrics } from '../services/api';

function DeviceDetail() {
  const { id } = useParams();
  const [device, setDevice] = useState(null);
  const [services, setServices] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDeviceData();
  }, [id]);

  const fetchDeviceData = async () => {
    try {
      const [deviceRes, servicesRes, metricsRes] = await Promise.all([
        getDevice(id),
        getDeviceServices(id),
        getDeviceMetrics(id, 10),
      ]);
      
      setDevice(deviceRes.data);
      setServices(servicesRes.data);
      setMetrics(metricsRes.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch device details');
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!device) return <div className="not-found">Device not found</div>;

  const hasMetadata = device.metadata && Object.keys(device.metadata).length > 0;

  return (
    <div className="device-detail">
      <div className="page-header">
        <div className="header-content">
          <h1>{device.name}</h1>
          <span className={`status-badge status-${device.status}`}>
            {device.status}
          </span>
        </div>
        <div>
          <Link to={`/devices/${device.id}/edit`} className="btn btn-primary">Edit</Link>
          <Link to="/devices" className="btn">Back to Devices</Link>
        </div>
      </div>

      <div className="detail-overview">
        <div className="overview-card">
          <div className="overview-icon">🖥️</div>
          <div className="overview-content">
            <span className="overview-label">Type</span>
            <span className="overview-value">{device.type}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">🌐</div>
          <div className="overview-content">
            <span className="overview-label">IP Address</span>
            <span className="overview-value">{device.ip_address || 'Not set'}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">📍</div>
          <div className="overview-content">
            <span className="overview-label">MAC Address</span>
            <span className="overview-value">{device.mac_address || 'Not set'}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">📅</div>
          <div className="overview-content">
            <span className="overview-label">Created</span>
            <span className="overview-value">{new Date(device.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <div className="detail-sections">
        {hasMetadata && (
          <div className="detail-section">
            <h2>Metadata</h2>
            <div className="metadata-grid">
              {Object.entries(device.metadata).map(([key, value]) => (
                <div key={key} className="metadata-item">
                  <span className="metadata-key">{key}</span>
                  <span className="metadata-value">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="detail-section">
          <div className="section-header">
            <h2>Services ({services.length})</h2>
            <Link to={`/devices/${device.id}/services/new`} className="btn btn-sm btn-primary">Add Service</Link>
          </div>
          {services.length > 0 ? (
            <div className="service-grid">
              {services.map(service => (
                <div key={service.id} className="service-card">
                  <div className="service-header">
                    <h3>{service.name}</h3>
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
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>No services configured for this device</p>
              <Link to={`/devices/${device.id}/services/new`} className="btn btn-primary">Add First Service</Link>
            </div>
          )}
        </div>

        <div className="detail-section">
          <h2>Recent Metrics</h2>
          {metrics.length > 0 ? (
            <div className="metrics-table-wrapper">
              <table className="metrics-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>CPU %</th>
                    <th>Memory %</th>
                    <th>Disk %</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.slice(0, 5).map((metric, idx) => (
                    <tr key={idx}>
                      <td>{new Date(metric.timestamp).toLocaleString()}</td>
                      <td className="metric-value">{metric.cpu_usage?.toFixed(1) || 'N/A'}</td>
                      <td className="metric-value">{metric.memory_usage?.toFixed(1) || 'N/A'}</td>
                      <td className="metric-value">{metric.disk_usage?.toFixed(1) || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <p>No metrics available for this device</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DeviceDetail;
