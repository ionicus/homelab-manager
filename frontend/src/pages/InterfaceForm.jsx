import { useState } from 'react';
import { createDeviceInterface } from '../services/api';

function InterfaceForm({ deviceId, onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    interface_name: '',
    mac_address: '',
    ip_address: '',
    subnet_mask: '',
    gateway: '',
    vlan_id: '',
    status: 'up',
    is_primary: false,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Clean up empty values
      const cleanData = {
        interface_name: formData.interface_name,
        mac_address: formData.mac_address,
        status: formData.status,
        is_primary: formData.is_primary,
      };

      // Only include optional fields if they have values
      if (formData.ip_address) cleanData.ip_address = formData.ip_address;
      if (formData.subnet_mask) cleanData.subnet_mask = formData.subnet_mask;
      if (formData.gateway) cleanData.gateway = formData.gateway;
      if (formData.vlan_id) cleanData.vlan_id = parseInt(formData.vlan_id, 10);

      await createDeviceInterface(deviceId, cleanData);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create interface');
      setLoading(false);
    }
  };

  return (
    <div className="interface-form-container">
      <div className="interface-form-header">
        <h3>Add Network Interface</h3>
        <button className="btn-close" onClick={onCancel}>
          ✕
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit} className="interface-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="interface_name">Interface Name *</label>
            <input
              type="text"
              id="interface_name"
              name="interface_name"
              value={formData.interface_name}
              onChange={handleChange}
              required
              placeholder="e.g., eth0, wlan0, ens33"
            />
          </div>

          <div className="form-group">
            <label htmlFor="mac_address">MAC Address *</label>
            <input
              type="text"
              id="mac_address"
              name="mac_address"
              value={formData.mac_address}
              onChange={handleChange}
              required
              placeholder="XX:XX:XX:XX:XX:XX"
              pattern="^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
              title="MAC address must be in format XX:XX:XX:XX:XX:XX"
            />
          </div>
        </div>

        <div className="form-row">
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
            <label htmlFor="subnet_mask">Subnet Mask</label>
            <input
              type="text"
              id="subnet_mask"
              name="subnet_mask"
              value={formData.subnet_mask}
              onChange={handleChange}
              placeholder="e.g., 255.255.255.0"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="gateway">Gateway</label>
            <input
              type="text"
              id="gateway"
              name="gateway"
              value={formData.gateway}
              onChange={handleChange}
              placeholder="e.g., 192.168.1.1"
            />
          </div>

          <div className="form-group">
            <label htmlFor="vlan_id">VLAN ID</label>
            <input
              type="number"
              id="vlan_id"
              name="vlan_id"
              value={formData.vlan_id}
              onChange={handleChange}
              placeholder="1-4094"
              min="1"
              max="4094"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="status">Status *</label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
              required
            >
              <option value="up">Up</option>
              <option value="down">Down</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="is_primary"
                checked={formData.is_primary}
                onChange={handleChange}
              />
              <span>Set as primary interface</span>
            </label>
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Interface'}
          </button>
          <button type="button" className="btn" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default InterfaceForm;
