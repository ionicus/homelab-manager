import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDevices, deleteDevice } from '../services/api';

function DeviceList() {
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

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this device?')) {
      try {
        await deleteDevice(id);
        fetchDevices();
      } catch (err) {
        alert('Failed to delete device');
      }
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="device-list-page">
      <div className="page-header">
        <h1>Devices</h1>
        <Link to="/devices/new" className="btn btn-primary">Add Device</Link>
      </div>

      <div className="devices-table">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Status</th>
              <th>IP Address</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {devices.map(device => (
              <tr key={device.id}>
                <td><Link to={`/devices/${device.id}`}>{device.name}</Link></td>
                <td>{device.type}</td>
                <td>
                  <span className={`status-badge status-${device.status}`}>
                    {device.status}
                  </span>
                </td>
                <td>{device.ip_address || 'N/A'}</td>
                <td>
                  <Link to={`/devices/${device.id}`} className="btn btn-sm">View</Link>
                  <button 
                    onClick={() => handleDelete(device.id)} 
                    className="btn btn-sm btn-danger"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DeviceList;
