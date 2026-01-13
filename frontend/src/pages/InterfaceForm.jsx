import { useState } from 'react';
import { Button, Stack, TextInput, NumberInput, Select, Checkbox, Alert, CloseButton, Group, SimpleGrid } from '@mantine/core';
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

  const handleTextChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCheckboxChange = (checked) => {
    setFormData((prev) => ({
      ...prev,
      is_primary: checked,
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
    <div className="form-modal-content">
      <Group justify="space-between" mb="md">
        <h2 style={{ margin: 0 }}>Add Network Interface</h2>
        <CloseButton onClick={onCancel} size="lg" />
      </Group>

      <form onSubmit={handleSubmit}>
        <Stack spacing="md">
          {error && (
            <Alert color="red" title="Error">
              {error}
            </Alert>
          )}

          <SimpleGrid cols={2} spacing="md" breakpoints={[{ maxWidth: 'sm', cols: 1 }]}>
            <TextInput
              label="Interface Name"
              placeholder="e.g., eth0, wlan0, ens33"
              name="interface_name"
              value={formData.interface_name}
              onChange={handleTextChange}
              required
              withAsterisk
            />

            <TextInput
              label="MAC Address"
              placeholder="XX:XX:XX:XX:XX:XX"
              name="mac_address"
              value={formData.mac_address}
              onChange={handleTextChange}
              required
              withAsterisk
              pattern="^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
              title="MAC address must be in format XX:XX:XX:XX:XX:XX"
            />
          </SimpleGrid>

          <SimpleGrid cols={2} spacing="md" breakpoints={[{ maxWidth: 'sm', cols: 1 }]}>
            <TextInput
              label="IP Address"
              placeholder="e.g., 192.168.1.100"
              name="ip_address"
              value={formData.ip_address}
              onChange={handleTextChange}
            />

            <TextInput
              label="Subnet Mask"
              placeholder="e.g., 255.255.255.0"
              name="subnet_mask"
              value={formData.subnet_mask}
              onChange={handleTextChange}
            />
          </SimpleGrid>

          <SimpleGrid cols={2} spacing="md" breakpoints={[{ maxWidth: 'sm', cols: 1 }]}>
            <TextInput
              label="Gateway"
              placeholder="e.g., 192.168.1.1"
              name="gateway"
              value={formData.gateway}
              onChange={handleTextChange}
            />

            <NumberInput
              label="VLAN ID"
              placeholder="1-4094"
              name="vlan_id"
              value={formData.vlan_id}
              onChange={(value) => setFormData(prev => ({ ...prev, vlan_id: value || '' }))}
              min={1}
              max={4094}
            />
          </SimpleGrid>

          <SimpleGrid cols={2} spacing="md" breakpoints={[{ maxWidth: 'sm', cols: 1 }]}>
            <Select
              label="Status"
              placeholder="Select status"
              name="status"
              value={formData.status}
              onChange={(value) => setFormData(prev => ({ ...prev, status: value }))}
              data={[
                { value: 'up', label: 'Up' },
                { value: 'down', label: 'Down' },
                { value: 'disabled', label: 'Disabled' },
              ]}
              required
              withAsterisk
            />

            <Checkbox
              label="Set as primary interface"
              checked={formData.is_primary}
              onChange={(event) => handleCheckboxChange(event.currentTarget.checked)}
              mt="xl"
            />
          </SimpleGrid>

          <Group spacing="sm" justify="flex-end" mt="md">
            <Button type="button" onClick={onCancel} variant="default">
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              Create Interface
            </Button>
          </Group>
        </Stack>
      </form>
    </div>
  );
}

export default InterfaceForm;
