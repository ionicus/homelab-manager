import { useState, useEffect } from 'react';
import {
  Button,
  Group,
  CloseButton,
  Select,
  Stack,
  Text,
  Loader,
  Collapse,
  Paper,
} from '@mantine/core';
import { IconChevronDown, IconChevronUp } from '@tabler/icons-react';
import { getExecutorActions, getActionSchema, triggerAutomation } from '../services/api';
import ErrorDisplay from './ErrorDisplay';
import DynamicVariableForm from './DynamicVariableForm';

function AutomationForm({ deviceId, onSuccess, onCancel }) {
  const [playbooks, setPlaybooks] = useState([]);
  const [selectedPlaybook, setSelectedPlaybook] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fetchingPlaybooks, setFetchingPlaybooks] = useState(true);

  // Schema and variables state
  const [schema, setSchema] = useState(null);
  const [fetchingSchema, setFetchingSchema] = useState(false);
  const [extraVars, setExtraVars] = useState({});
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    fetchPlaybooks();
  }, []);

  // Fetch schema when playbook changes
  useEffect(() => {
    if (selectedPlaybook) {
      fetchSchema(selectedPlaybook);
    } else {
      setSchema(null);
      setExtraVars({});
    }
  }, [selectedPlaybook]);

  const fetchPlaybooks = async () => {
    try {
      setFetchingPlaybooks(true);
      const response = await getExecutorActions('ansible');
      const playbookList = response.data.data.map((action) => ({
        value: action.name,
        label: action.display_name || action.name,
        description: action.description,
      }));
      setPlaybooks(playbookList);
      if (playbookList.length > 0) {
        setSelectedPlaybook(playbookList[0].value);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch playbooks:', err);
      setError(err);
    } finally {
      setFetchingPlaybooks(false);
    }
  };

  const fetchSchema = async (playbookName) => {
    try {
      setFetchingSchema(true);
      const response = await getActionSchema('ansible', playbookName);
      const schemaData = response.data.data?.schema || null;
      setSchema(schemaData);

      // Initialize extra vars with defaults from schema
      if (schemaData?.properties) {
        const defaults = {};
        Object.entries(schemaData.properties).forEach(([key, prop]) => {
          if (prop.default !== undefined) {
            defaults[key] = prop.default;
          }
        });
        setExtraVars(defaults);
      } else {
        setExtraVars({});
      }
    } catch (err) {
      console.error('Failed to fetch schema:', err);
      // Schema is optional, don't show error
      setSchema(null);
      setExtraVars({});
    } finally {
      setFetchingSchema(false);
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

      // Only pass extra_vars if there are any non-default values
      const varsToSend = Object.keys(extraVars).length > 0 ? extraVars : null;

      const response = await triggerAutomation(
        deviceId,
        selectedPlaybook,
        'ansible',
        null,
        varsToSend
      );
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

  const selectedPlaybookData = playbooks.find((p) => p.value === selectedPlaybook);
  const hasSchema = schema?.properties && Object.keys(schema.properties).length > 0;

  return (
    <div className="form-modal" onClick={onCancel}>
      <div className="form-modal-content" onClick={(e) => e.stopPropagation()}>
        <Group justify="space-between" mb="md">
          <h2 style={{ margin: 0 }}>Run Ansible Playbook</h2>
          <CloseButton onClick={onCancel} size="lg" />
        </Group>

        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            {error && (
              <ErrorDisplay error={error} onRetry={fetchingPlaybooks ? null : fetchPlaybooks} />
            )}

            {fetchingPlaybooks ? (
              <Group gap="sm">
                <Loader size="sm" />
                <Text c="dimmed">Loading available playbooks...</Text>
              </Group>
            ) : playbooks.length === 0 ? (
              <Text c="dimmed" ta="center" py="md">
                No playbooks available. Please add playbooks to ansible/playbooks/ directory.
              </Text>
            ) : (
              <Select
                label="Select Playbook"
                placeholder="Choose a playbook to run"
                value={selectedPlaybook}
                onChange={setSelectedPlaybook}
                data={playbooks}
                required
                withAsterisk
                disabled={loading}
              />
            )}

            {selectedPlaybookData?.description && (
              <Text size="sm" c="dimmed">
                {selectedPlaybookData.description}
              </Text>
            )}

            {/* Schema loading indicator */}
            {fetchingSchema && (
              <Group gap="sm">
                <Loader size="xs" />
                <Text size="sm" c="dimmed">
                  Loading playbook variables...
                </Text>
              </Group>
            )}

            {/* Advanced options with schema-based form */}
            {!fetchingSchema && hasSchema && (
              <Paper withBorder p="sm" radius="sm">
                <Group
                  justify="space-between"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setShowAdvanced(!showAdvanced)}
                >
                  <Text size="sm" fw={500}>
                    Advanced Options
                  </Text>
                  {showAdvanced ? <IconChevronUp size={18} /> : <IconChevronDown size={18} />}
                </Group>
                <Collapse in={showAdvanced}>
                  <div style={{ marginTop: '1rem' }}>
                    <DynamicVariableForm
                      schema={schema}
                      values={extraVars}
                      onChange={setExtraVars}
                      disabled={loading}
                    />
                  </div>
                </Collapse>
              </Paper>
            )}

            <Group gap="sm" justify="flex-end" mt="md">
              <Button type="button" onClick={onCancel} variant="default" disabled={loading}>
                Cancel
              </Button>
              <Button
                type="submit"
                loading={loading}
                disabled={fetchingPlaybooks || playbooks.length === 0 || fetchingSchema}
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
