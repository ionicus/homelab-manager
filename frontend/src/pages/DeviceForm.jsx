import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button, Group, TextInput, Select, Stack, Container, Title, Paper, Alert } from '@mantine/core';
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
    <Container size="md" py="xl">
      <Group justify="space-between" mb="xl">
        <Title order={1}>{isEditMode ? 'Edit Device' : 'Add New Device'}</Title>
        <Button component={Link} to="/devices" variant="default">Cancel</Button>
      </Group>

      <Paper shadow="sm" p="lg" withBorder>
        <form onSubmit={handleSubmit}>
          <Stack spacing="md">
            {error && (
              <Alert color="red" title="Error">
                {error}
              </Alert>
            )}

            <TextInput
              label="Device Name"
              placeholder="e.g., server-01"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              withAsterisk
            />

            <Select
              label="Type"
              placeholder="Select device type"
              name="type"
              value={formData.type}
              onChange={(value) => setFormData(prev => ({ ...prev, type: value }))}
              data={[
                { value: 'server', label: 'Server' },
                { value: 'vm', label: 'Virtual Machine' },
                { value: 'container', label: 'Container' },
                { value: 'network', label: 'Network Device' },
                { value: 'storage', label: 'Storage' },
              ]}
              required
              withAsterisk
            />

            <Select
              label="Status"
              placeholder="Select status"
              name="status"
              value={formData.status}
              onChange={(value) => setFormData(prev => ({ ...prev, status: value }))}
              data={[
                { value: 'active', label: 'Active' },
                { value: 'inactive', label: 'Inactive' },
                { value: 'maintenance', label: 'Maintenance' },
              ]}
              required
              withAsterisk
            />

            <TextInput
              label="IP Address"
              placeholder="e.g., 192.168.1.100"
              name="ip_address"
              value={formData.ip_address}
              onChange={handleChange}
            />

            <TextInput
              label="MAC Address"
              placeholder="e.g., 00:11:22:33:44:55"
              name="mac_address"
              value={formData.mac_address}
              onChange={handleChange}
            />

            <Group spacing="sm" justify="flex-end" mt="md">
              <Button component={Link} to="/devices" variant="default">
                Cancel
              </Button>
              <Button type="submit" loading={loading}>
                {isEditMode ? 'Update Device' : 'Create Device'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Paper>
    </Container>
  );
}

export default DeviceForm;
