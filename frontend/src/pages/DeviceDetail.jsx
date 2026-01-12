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

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!device) return <div>Device not found</div>;

  return (
    <div className="device-detail">
      <div className="page-header">
        <h1>{device.name}</h1>
        <div>
          <Link to={`/devices/${device.id}/edit`} className="btn btn-primary">Edit</Link>
          <Link to="/devices" className="btn">Back to Devices</Link>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-card">
          <h2>Device Information</h2>
          <dl>
            <dt>Type:</dt>
            <dd>{device.type}</dd>
            <dt>Status:</dt>
            <dd>
              <span className={`status-badge status-${device.status}`}>
                {device.status}
              </span>
            </dd>
            <dt>IP Address:</dt>
            <dd>{device.ip_address || 'N/A'}</dd>
            <dt>MAC Address:</dt>
            <dd>{device.mac_address || 'N/A'}</dd>
            <dt>Created:</dt>
            <dd>{new Date(device.created_at).toLocaleString()}</dd>
          </dl>
        </div>

        <div className="detail-card">
          <h2>Services ({services.length})</h2>
          {services.length > 0 ? (
            <ul className="service-list">
              {services.map(service => (
                <li key={service.id}>
                  <strong>{service.name}</strong>
                  <span className={`status-badge status-${service.status}`}>
                    {service.status}
                  </span>
                  {service.port && <span>Port: {service.port}</span>}
                </li>
              ))}
            </ul>
          ) : (
            <p>No services configured</p>
          )}
        </div>

        <div className="detail-card full-width">
          <h2>Recent Metrics</h2>
          {metrics.length > 0 ? (
            <table>
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
                    <td>{metric.cpu_usage?.toFixed(1) || 'N/A'}</td>
                    <td>{metric.memory_usage?.toFixed(1) || 'N/A'}</td>
                    <td>{metric.disk_usage?.toFixed(1) || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No metrics available</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default DeviceDetail;
