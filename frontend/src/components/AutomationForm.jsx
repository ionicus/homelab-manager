import { useState, useEffect } from 'react';
import { Button, Group, CloseButton, Select, Stack, Text, Loader } from '@mantine/core';
import { getPlaybooks, triggerAutomation } from '../services/api';
import ErrorDisplay from './ErrorDisplay';

function AutomationForm({ deviceId, onSuccess, onCancel }) {
  const [playbooks, setPlaybooks] = useState([]);
  const [selectedPlaybook, setSelectedPlaybook] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fetchingPlaybooks, setFetchingPlaybooks] = useState(true);

  useEffect(() => {
    fetchPlaybooks();
  }, []);

  const fetchPlaybooks = async () => {
    try {
      setFetchingPlaybooks(true);
      const response = await getPlaybooks();
      const playbookList = response.data.data?.playbooks || [];
      setPlaybooks(playbookList);
      if (playbookList.length > 0) {
        setSelectedPlaybook(playbookList[0]);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch playbooks:', err);
      setError(err);
    } finally {
      setFetchingPlaybooks(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedPlaybook) {
      setError({ userMessage: 'Please select a playbook' });
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await triggerAutomation(deviceId, selectedPlaybook);
      if (onSuccess) {
        onSuccess(response.data.data);
      }
    } catch (err) {
      console.error('Failed to trigger automation:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const playbookDescriptions = {
    ping: 'Test basic connectivity and SSH access to the device.',
    system_info: 'Gather comprehensive system information (OS, CPU, memory, disk, network).',
    update: 'Update system packages (requires sudo privileges).',
    docker_install: 'Install Docker CE on Debian/Ubuntu systems (requires sudo privileges).',
    basic_setup: 'Basic system setup and configuration.',
  };

  return (
    <div className="form-modal" onClick={onCancel}>
      <div className="form-modal-content" onClick={(e) => e.stopPropagation()}>
        <Group justify="space-between" mb="md">
          <h2 style={{ margin: 0 }}>Run Ansible Playbook</h2>
          <CloseButton onClick={onCancel} size="lg" />
        </Group>

        <form onSubmit={handleSubmit}>
          <Stack spacing="md">
            {error && <ErrorDisplay error={error} onRetry={fetchingPlaybooks ? null : fetchPlaybooks} />}

            {fetchingPlaybooks ? (
              <Group spacing="sm">
                <Loader size="sm" />
                <Text color="dimmed">Loading available playbooks...</Text>
              </Group>
            ) : playbooks.length === 0 ? (
              <Text color="dimmed" ta="center" py="md">
                No playbooks available. Please add playbooks to ansible/playbooks/ directory.
              </Text>
            ) : (
              <Select
                label="Select Playbook"
                placeholder="Choose a playbook to run"
                value={selectedPlaybook}
                onChange={setSelectedPlaybook}
                data={playbooks.map(playbook => ({ value: playbook, label: playbook }))}
                required
                withAsterisk
                disabled={loading}
              />
            )}

            {selectedPlaybook && playbookDescriptions[selectedPlaybook] && (
              <Text size="sm" color="dimmed">
                {playbookDescriptions[selectedPlaybook]}
              </Text>
            )}

            <Group spacing="sm" justify="flex-end" mt="md">
              <Button type="button" onClick={onCancel} variant="default" disabled={loading}>
                Cancel
              </Button>
              <Button
                type="submit"
                loading={loading}
                disabled={fetchingPlaybooks || playbooks.length === 0}
              >
                Run Playbook
              </Button>
            </Group>
          </Stack>
        </form>
      </div>
    </div>
  );
}

export default AutomationForm;
