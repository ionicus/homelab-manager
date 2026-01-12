import { useState } from 'react';
import { deleteService, updateServiceStatus } from '../services/api';
import ServiceForm from './ServiceForm';

function ServiceList({ services, deviceId, onUpdate }) {
  const [editingServiceId, setEditingServiceId] = useState(null);
  const [updatingStatus, setUpdatingStatus] = useState({});

  const handleDelete = async (serviceId, serviceName) => {
    if (window.confirm(`Are you sure you want to delete service "${serviceName}"?`)) {
      try {
        await deleteService(serviceId);
        onUpdate();
      } catch (err) {
        const message = err.userMessage || 'Failed to delete service';
        alert(message);
      }
    }
  };

  const handleStatusToggle = async (serviceId, currentStatus) => {
    const newStatus = currentStatus === 'running' ? 'stopped' : 'running';
    setUpdatingStatus(prev => ({ ...prev, [serviceId]: true }));

    try {
      await updateServiceStatus(serviceId, newStatus);
      onUpdate();
    } catch (err) {
      const message = err.userMessage || 'Failed to update service status';
      alert(message);
    } finally {
      setUpdatingStatus(prev => ({ ...prev, [serviceId]: false }));
    }
  };

  const handleEdit = (serviceId) => {
    setEditingServiceId(serviceId);
  };

  const handleEditSuccess = () => {
    setEditingServiceId(null);
    onUpdate();
  };

  if (services.length === 0) {
    return (
      <div className="empty-state">
        <p>No services configured for this device</p>
      </div>
    );
  }

  return (
    <>
      {editingServiceId && (
        <ServiceForm
          deviceId={deviceId}
          serviceId={editingServiceId}
          onSuccess={handleEditSuccess}
          onCancel={() => setEditingServiceId(null)}
        />
      )}

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

            <div className="service-actions">
              <button
                className={`btn btn-sm ${
                  service.status === 'running' ? 'btn-warning' : 'btn-success'
                }`}
                onClick={() => handleStatusToggle(service.id, service.status)}
                disabled={updatingStatus[service.id]}
                title={service.status === 'running' ? 'Stop service' : 'Start service'}
              >
                {updatingStatus[service.id] ? '...' : (
                  service.status === 'running' ? 'Stop' : 'Start'
                )}
              </button>
              <button
                className="btn btn-sm"
                onClick={() => handleEdit(service.id)}
                title="Edit service"
              >
                Edit
              </button>
              <button
                className="btn btn-sm btn-danger"
                onClick={() => handleDelete(service.id, service.name)}
                title="Delete service"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

export default ServiceList;
