import { Link } from 'react-router-dom';
import { Button } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { getDevices } from '../services/api';
import { safeGetArray } from '../utils/validation';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import StatusBadge from '../components/StatusBadge';

function Dashboard() {
  const {
    data: devices = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => safeGetArray(await getDevices()),
  });

  if (isLoading) return <LoadingSkeleton type="dashboard" />;
  if (error) return <ErrorDisplay error={error} onRetry={refetch} />;

  const activeDevices = devices.filter(d => d.status === 'active').length;
  const maintenanceDevices = devices.filter(d => d.status === 'maintenance').length;
  const inactiveDevices = devices.filter(d => d.status === 'inactive').length;
  const totalDevices = devices.length;

  const devicesByType = devices.reduce((acc, device) => {
    acc[device.type] = (acc[device.type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <Button component={Link} to="/devices/new">Add Device</Button>
      </div>

      <div className="stats-grid">
        <div className="stat-card stat-card-primary">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>Total Devices</h3>
            <p className="stat-value">{totalDevices}</p>
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

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Device Types</h2>
          </div>
          <div className="type-grid">
            {Object.entries(devicesByType).map(([type, count]) => (
              <div key={type} className="type-card">
                <span className="type-name">{type}</span>
                <span className="type-count">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recent Devices</h2>
            <Link to="/devices" className="view-all-link">View All →</Link>
          </div>
          <div className="device-list">
            {devices.slice(0, 5).map(device => (
              <Link key={device.id} to={`/devices/${device.id}`} className="device-item">
                <div className="device-info">
                  <h4>{device.name}</h4>
                  <p className="device-meta">
                    <span className="device-type">{device.type}</span>
                    {device.ip_address && <span className="device-ip">{device.ip_address}</span>}
                  </p>
                </div>
                <StatusBadge status={device.status} />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
