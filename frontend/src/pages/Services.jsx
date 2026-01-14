import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Group, Select } from '@mantine/core';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getServices, getDevices, deleteService, updateServiceStatus } from '../services/api';
import { safeGetArray } from '../utils/validation';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import StatusBadge from '../components/StatusBadge';
import ServiceForm from '../components/ServiceForm';

function Services() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showServiceForm, setShowServiceForm] = useState(false);
  const [showDeviceSelector, setShowDeviceSelector] = useState(false);
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);
  const [filterDevice, setFilterDevice] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Services query
  const {
    data: services = [],
    isLoading: servicesLoading,
    error: servicesError,
    refetch: refetchServices,
  } = useQuery({
    queryKey: ['services'],
    queryFn: async () => safeGetArray(await getServices()),
  });

  // Devices query (for the device selector and names)
  const { data: devices = [] } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => safeGetArray(await getDevices()),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
    onError: (err) => {
      alert(err.userMessage || 'Failed to delete service');
    },
  });

  // Status update mutation
  const statusMutation = useMutation({
    mutationFn: ({ id, status }) => updateServiceStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
    onError: (err) => {
      alert(err.userMessage || 'Failed to update service status');
    },
  });

  const handleDelete = (serviceId, serviceName) => {
    if (window.confirm(`Are you sure you want to delete service "${serviceName}"?`)) {
      deleteMutation.mutate(serviceId);
    }
  };

  const handleStatusToggle = (serviceId, currentStatus) => {
    const newStatus = currentStatus === 'running' ? 'stopped' : 'running';
    statusMutation.mutate({ id: serviceId, status: newStatus });
  };

  const handleAddServiceClick = () => {
    setShowDeviceSelector(true);
  };

  const handleDeviceSelect = (deviceId) => {
    if (deviceId) {
      setSelectedDeviceId(parseInt(deviceId));
      setShowDeviceSelector(false);
      setShowServiceForm(true);
    }
  };

  const handleCancelDeviceSelector = () => {
    setShowDeviceSelector(false);
  };

  const handleServiceUpdate = () => {
    setShowServiceForm(false);
    setSelectedDeviceId(null);
    queryClient.invalidateQueries({ queryKey: ['services'] });
  };

  const getDeviceName = (deviceId) => {
    const device = devices.find(d => d.id === deviceId);
    return device ? device.name : `Device ${deviceId}`;
  };

  const filteredServices = services.filter(service => {
    if (filterDevice !== 'all' && service.device_id !== parseInt(filterDevice)) {
      return false;
    }
    if (filterStatus !== 'all' && service.status !== filterStatus) {
      return false;
    }
    return true;
  });

  const servicesByStatus = {
    running: services.filter(s => s.status === 'running').length,
    stopped: services.filter(s => s.status === 'stopped').length,
    error: services.filter(s => s.status === 'error').length,
  };

  if (servicesLoading) return <LoadingSkeleton type="device-list" count={6} />;
  if (servicesError) return <ErrorDisplay error={servicesError} onRetry={refetchServices} />;

  return (
    <div className="services-page">
      <div className="page-header">
        <h1>Services ({services.length})</h1>
        <Button onClick={handleAddServiceClick} disabled={devices.length === 0}>
          Add Service
        </Button>
      </div>

      {showDeviceSelector && (
        <div className="form-modal" onClick={handleCancelDeviceSelector}>
          <div className="form-modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Select Device</h2>
            <p>Choose a device to add the service to:</p>
            <Select
              placeholder="Select a device"
              data={devices.map(d => ({ value: String(d.id), label: d.name }))}
              onChange={handleDeviceSelect}
              searchable
            />
            <Group mt="md" justify="flex-end">
              <Button variant="default" onClick={handleCancelDeviceSelector}>
                Cancel
              </Button>
            </Group>
          </div>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card stat-card-primary">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>Total Services</h3>
            <p className="stat-value">{services.length}</p>
          </div>
        </div>
        <div className="stat-card stat-card-success">
          <div className="stat-icon">✓</div>
          <div className="stat-content">
            <h3>Running</h3>
            <p className="stat-value">{servicesByStatus.running}</p>
          </div>
        </div>
        <div className="stat-card stat-card-warning">
          <div className="stat-icon">⚠</div>
          <div className="stat-content">
            <h3>Error</h3>
            <p className="stat-value">{servicesByStatus.error}</p>
          </div>
        </div>
        <div className="stat-card stat-card-danger">
          <div className="stat-icon">⏸</div>
          <div className="stat-content">
            <h3>Stopped</h3>
            <p className="stat-value">{servicesByStatus.stopped}</p>
          </div>
        </div>
      </div>

      <div className="filters-bar">
        <div className="filter-group">
          <label htmlFor="filterDevice">Device:</label>
          <select
            id="filterDevice"
            value={filterDevice}
            onChange={(e) => setFilterDevice(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Devices</option>
            {devices.map(device => (
              <option key={device.id} value={device.id}>
                {device.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filterStatus">Status:</label>
          <select
            id="filterStatus"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Statuses</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div className="filter-results">
          Showing {filteredServices.length} of {services.length} services
        </div>
      </div>

      {showServiceForm && selectedDeviceId && (
        <ServiceForm
          deviceId={selectedDeviceId}
          onSuccess={handleServiceUpdate}
          onCancel={() => {
            setShowServiceForm(false);
            setSelectedDeviceId(null);
          }}
        />
      )}

      {filteredServices.length === 0 ? (
        <div className="empty-state">
          <p>No services found{filterDevice !== 'all' || filterStatus !== 'all' ? ' with the selected filters' : ''}</p>
          {services.length === 0 && devices.length > 0 && (
            <p>Add services to your devices to get started</p>
          )}
        </div>
      ) : (
        <div className="service-grid">
          {filteredServices.map(service => (
            <div
              key={service.id}
              className="service-card clickable-card"
              onClick={() => navigate(`/services/${service.id}`)}
            >
              <div className="service-header">
                <div className="service-title-group">
                  <h3>{service.name}</h3>
                  <Link
                    to={`/devices/${service.device_id}`}
                    className="device-link"
                    title="View device"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {getDeviceName(service.device_id)}
                  </Link>
                </div>
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
                  size="xs"
                  color={service.status === 'running' ? 'yellow' : 'green'}
                  onClick={() => handleStatusToggle(service.id, service.status)}
                  disabled={statusMutation.isPending}
                  title={service.status === 'running' ? 'Stop service' : 'Start service'}
                >
                  {service.status === 'running' ? 'Stop' : 'Start'}
                </Button>
                <Button
                  size="xs"
                  color="red"
                  onClick={() => handleDelete(service.id, service.name)}
                  disabled={deleteMutation.isPending}
                  title="Delete service"
                >
                  Delete
                </Button>
              </Group>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Services;
