import { useState, useEffect } from 'react';
import { createService, updateService, getService } from '../services/api';

function ServiceForm({ deviceId, serviceId = null, onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    port: '',
    protocol: '',
    status: 'stopped',
    health_check_url: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (serviceId) {
      fetchService();
    }
  }, [serviceId]);

  const fetchService = async () => {
    try {
      const response = await getService(serviceId);
      const service = response.data || response;
      setFormData({
        name: service.name || '',
        port: service.port || '',
        protocol: service.protocol || '',
        status: service.status || 'stopped',
        health_check_url: service.health_check_url || '',
      });
    } catch (err) {
      setError(err.userMessage || 'Failed to load service');
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
    setLoading(true);
    setError(null);

    try {
      const data = {
        device_id: deviceId,
        name: formData.name,
        port: formData.port ? parseInt(formData.port) : null,
        protocol: formData.protocol || null,
        status: formData.status,
        health_check_url: formData.health_check_url || null,
      };

      if (serviceId) {
        await updateService(serviceId, data);
      } else {
        await createService(data);
      }

      onSuccess();
    } catch (err) {
      setError(err.userMessage || 'Failed to save service');
      setLoading(false);
    }
  };

  return (
    <div className="form-modal">
      <div className="form-modal-content">
        <div className="form-header">
          <h2>{serviceId ? 'Edit Service' : 'Add New Service'}</h2>
          <button className="close-btn" onClick={onCancel}>✕</button>
        </div>

        <form onSubmit={handleSubmit} className="service-form">
          {error && (
            <div className="form-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="name">Service Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              maxLength={255}
              placeholder="e.g., nginx, postgresql, docker"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="port">Port</label>
              <input
                type="number"
                id="port"
                name="port"
                value={formData.port}
                onChange={handleChange}
                min="1"
                max="65535"
                placeholder="e.g., 80, 443, 5432"
              />
            </div>

            <div className="form-group">
              <label htmlFor="protocol">Protocol</label>
              <input
                type="text"
                id="protocol"
                name="protocol"
                value={formData.protocol}
                onChange={handleChange}
                maxLength={50}
                placeholder="e.g., http, https, tcp"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="status">Status</label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
            >
              <option value="stopped">Stopped</option>
              <option value="running">Running</option>
              <option value="error">Error</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="health_check_url">Health Check URL</label>
            <input
              type="url"
              id="health_check_url"
              name="health_check_url"
              value={formData.health_check_url}
              onChange={handleChange}
              maxLength={500}
              placeholder="e.g., http://localhost:80/health"
            />
          </div>

          <div className="form-actions">
            <button
              type="button"
              onClick={onCancel}
              className="btn"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Saving...' : (serviceId ? 'Update Service' : 'Create Service')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ServiceForm;
