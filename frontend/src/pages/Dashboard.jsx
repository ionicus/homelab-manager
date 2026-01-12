import { useState, useEffect } from 'react';
import { getDevices } from '../services/api';

function Dashboard() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await getDevices();
      setDevices(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch devices');
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">{error}</div>;

  const activeDevices = devices.filter(d => d.status === 'active').length;
  const totalDevices = devices.length;

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Devices</h3>
          <p className="stat-value">{totalDevices}</p>
        </div>
        <div className="stat-card">
          <h3>Active Devices</h3>
          <p className="stat-value">{activeDevices}</p>
        </div>
        <div className="stat-card">
          <h3>Inactive Devices</h3>
          <p className="stat-value">{totalDevices - activeDevices}</p>
        </div>
      </div>

      <div className="recent-devices">
        <h2>Recent Devices</h2>
        <div className="device-list">
          {devices.slice(0, 5).map(device => (
            <div key={device.id} className="device-item">
              <h4>{device.name}</h4>
              <p>Type: {device.type} | Status: {device.status}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
