import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getDevice, createDevice, updateDevice } from '../services/api';

function DeviceForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = !!id;

  const [formData, setFormData] = useState({
    name: '',
    type: 'server',
    status: 'active',
    ip_address: '',
    mac_address: '',
    metadata: {}
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isEditMode) {
      fetchDevice();
    }
  }, [id]);

  const fetchDevice = async () => {
    try {
      setLoading(true);
      const response = await getDevice(id);
      const device = response.data;
      setFormData({
        name: device.name,
        type: device.type,
        status: device.status,
        ip_address: device.ip_address || '',
        mac_address: device.mac_address || '',
        metadata: device.metadata || {}
      });
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch device');
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isEditMode) {
        await updateDevice(id, formData);
      } else {
        await createDevice(formData);
      }
      navigate('/devices');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save device');
      setLoading(false);
    }
  };

  return (
    <div className="device-form-page">
      <div className="page-header">
        <h1>{isEditMode ? 'Edit Device' : 'Add New Device'}</h1>
        <Link to="/devices" className="btn">Cancel</Link>
      </div>

      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit} className="device-form">
        <div className="form-group">
          <label htmlFor="name">Device Name *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="e.g., server-01"
          />
        </div>

        <div className="form-group">
          <label htmlFor="type">Type *</label>
          <select
            id="type"
            name="type"
            value={formData.type}
            onChange={handleChange}
            required
          >
            <option value="server">Server</option>
            <option value="vm">Virtual Machine</option>
            <option value="container">Container</option>
            <option value="network">Network Device</option>
            <option value="storage">Storage</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="status">Status *</label>
          <select
            id="status"
            name="status"
            value={formData.status}
            onChange={handleChange}
            required
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="maintenance">Maintenance</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="ip_address">IP Address</label>
          <input
            type="text"
            id="ip_address"
            name="ip_address"
            value={formData.ip_address}
            onChange={handleChange}
            placeholder="e.g., 192.168.1.100"
          />
        </div>

        <div className="form-group">
          <label htmlFor="mac_address">MAC Address</label>
          <input
            type="text"
            id="mac_address"
            name="mac_address"
            value={formData.mac_address}
            onChange={handleChange}
            placeholder="e.g., 00:11:22:33:44:55"
          />
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : (isEditMode ? 'Update Device' : 'Create Device')}
          </button>
          <Link to="/devices" className="btn">Cancel</Link>
        </div>
      </form>
    </div>
  );
}

export default DeviceForm;
