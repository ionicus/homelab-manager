import { useState, useEffect } from 'react';
import { Button, Group, CloseButton, TextInput, NumberInput, Select, Stack, Alert } from '@mantine/core';
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

  const handleTextChange = (e) => {
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
        <Group justify="space-between" mb="md">
          <h2 style={{ margin: 0 }}>{serviceId ? 'Edit Service' : 'Add New Service'}</h2>
          <CloseButton onClick={onCancel} size="lg" />
        </Group>

        <form onSubmit={handleSubmit}>
          <Stack spacing="md">
            {error && (
              <Alert color="red" title="Error">
                {error}
              </Alert>
            )}

            <TextInput
              label="Service Name"
              placeholder="e.g., nginx, postgresql, docker"
              name="name"
              value={formData.name}
              onChange={handleTextChange}
              required
              withAsterisk
              maxLength={255}
            />

            <Group grow>
              <NumberInput
                label="Port"
                placeholder="e.g., 80, 443, 5432"
                name="port"
                value={formData.port}
                onChange={(value) => setFormData(prev => ({ ...prev, port: value || '' }))}
                min={1}
                max={65535}
              />

              <TextInput
                label="Protocol"
                placeholder="e.g., http, https, tcp"
                name="protocol"
                value={formData.protocol}
                onChange={handleTextChange}
                maxLength={50}
              />
            </Group>

            <Select
              label="Status"
              placeholder="Select status"
              name="status"
              value={formData.status}
              onChange={(value) => setFormData(prev => ({ ...prev, status: value }))}
              data={[
                { value: 'stopped', label: 'Stopped' },
                { value: 'running', label: 'Running' },
                { value: 'error', label: 'Error' },
              ]}
            />

            <TextInput
              label="Health Check URL"
              placeholder="e.g., http://localhost:80/health"
              name="health_check_url"
              value={formData.health_check_url}
              onChange={handleTextChange}
              maxLength={500}
              type="url"
            />

            <Group spacing="sm" justify="flex-end" mt="md">
              <Button
                type="button"
                onClick={onCancel}
                variant="default"
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                loading={loading}
              >
                {serviceId ? 'Update Service' : 'Create Service'}
              </Button>
            </Group>
          </Stack>
        </form>
      </div>
    </div>
  );
}

export default ServiceForm;
