import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Group } from '@mantine/core';
import { deleteService, updateServiceStatus } from '../services/api';
import ServiceForm from './ServiceForm';
import StatusBadge from './StatusBadge';

function ServiceList({ services, deviceId, onUpdate }) {
  const navigate = useNavigate();
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
          <div
            key={service.id}
            className="service-card clickable-card"
            onClick={() => navigate(`/services/${service.id}`)}
          >
            <div className="service-header">
              <h3>{service.name}</h3>
              <StatusBadge status={service.status} />
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

            <Group className="service-actions" gap="xs" onClick={(e) => e.stopPropagation()}>
              <Button
                size="sm"
                color={service.status === 'running' ? 'yellow' : 'green'}
                onClick={() => handleStatusToggle(service.id, service.status)}
                loading={updatingStatus[service.id]}
                title={service.status === 'running' ? 'Stop service' : 'Start service'}
              >
                {service.status === 'running' ? 'Stop' : 'Start'}
              </Button>
              <Button
                size="sm"
                variant="default"
                onClick={() => handleEdit(service.id)}
                title="Edit service"
              >
                Edit
              </Button>
              <Button
                size="sm"
                color="red"
                onClick={() => handleDelete(service.id, service.name)}
                title="Delete service"
              >
                Delete
              </Button>
            </Group>
          </div>
        ))}
      </div>
    </>
  );
}

export default ServiceList;
