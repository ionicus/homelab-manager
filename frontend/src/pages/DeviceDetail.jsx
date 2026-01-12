import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getDevice, getDeviceServices, getDeviceMetrics, getDeviceInterfaces } from '../services/api';
import { safeGetArray } from '../utils/validation';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import ServiceList from '../components/ServiceList';
import ServiceForm from '../components/ServiceForm';
import InterfaceList from './InterfaceList';
import InterfaceForm from './InterfaceForm';

function DeviceDetail() {
  const { id } = useParams();
  const [device, setDevice] = useState(null);
  const [services, setServices] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [interfaces, setInterfaces] = useState([]);
  const [showInterfaceForm, setShowInterfaceForm] = useState(false);
  const [showServiceForm, setShowServiceForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDeviceData();
  }, [id]);

  const fetchDeviceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [deviceRes, servicesRes, metricsRes, interfacesRes] = await Promise.all([
        getDevice(id),
        getDeviceServices(id),
        getDeviceMetrics(id, 10),
        getDeviceInterfaces(id),
      ]);

      setDevice(deviceRes.data || deviceRes);
      setServices(safeGetArray(servicesRes));
      setMetrics(safeGetArray(metricsRes));
      setInterfaces(safeGetArray(interfacesRes));
      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  const handleInterfaceUpdate = async () => {
    setShowInterfaceForm(false);
    await fetchDeviceData();
  };

  const handleServiceUpdate = async () => {
    setShowServiceForm(false);
    await fetchDeviceData();
  };

  if (loading) return <LoadingSkeleton type="device-detail" />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchDeviceData} />;
  if (!device) return <ErrorDisplay error="Device not found" onRetry={fetchDeviceData} />;

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
            <h2>Network Interfaces ({interfaces.length})</h2>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setShowInterfaceForm(true)}
            >
              Add Interface
            </button>
          </div>

          {showInterfaceForm && (
            <div className="interface-form-overlay">
              <InterfaceForm
                deviceId={id}
                onSuccess={handleInterfaceUpdate}
                onCancel={() => setShowInterfaceForm(false)}
              />
            </div>
          )}

          <InterfaceList
            interfaces={interfaces}
            deviceId={id}
            onUpdate={fetchDeviceData}
          />
        </div>

        <div className="detail-section">
          <div className="section-header">
            <h2>Services ({services.length})</h2>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setShowServiceForm(true)}
            >
              Add Service
            </button>
          </div>

          {showServiceForm && (
            <ServiceForm
              deviceId={id}
              onSuccess={handleServiceUpdate}
              onCancel={() => setShowServiceForm(false)}
            />
          )}

          <ServiceList
            services={services}
            deviceId={id}
            onUpdate={fetchDeviceData}
          />
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
