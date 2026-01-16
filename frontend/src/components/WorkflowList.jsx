import { useState, useEffect } from 'react';
import {
  Button,
  Group,
  Stack,
  Text,
  Paper,
  Badge,
  ActionIcon,
  Menu,
  Loader,
  Table,
  Tabs,
  Modal,
  MultiSelect,
  Switch,
  Select,
} from '@mantine/core';
import {
  IconPlus,
  IconDotsVertical,
  IconEdit,
  IconTrash,
  IconPlayerPlay,
  IconRefresh,
  IconX,
} from '@tabler/icons-react';
import {
  getWorkflowTemplates,
  createWorkflowTemplate,
  updateWorkflowTemplate,
  deleteWorkflowTemplate,
  getWorkflowInstances,
  startWorkflow,
  cancelWorkflow,
  getDevices,
  getVaultSecrets,
} from '../services/api';
import ErrorDisplay from './ErrorDisplay';
import WorkflowBuilder from './WorkflowBuilder';

const STATUS_COLORS = {
  pending: 'yellow',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'gray',
  rolling_back: 'orange',
  rolled_back: 'pink',
};

function WorkflowList() {
  const [templates, setTemplates] = useState([]);
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal states
  const [showBuilder, setShowBuilder] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [showRunModal, setShowRunModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // Run workflow form
  const [devices, setDevices] = useState([]);
  const [selectedDeviceIds, setSelectedDeviceIds] = useState([]);
  const [rollbackOnFailure, setRollbackOnFailure] = useState(false);
  const [vaultSecrets, setVaultSecrets] = useState([]);
  const [selectedVaultSecret, setSelectedVaultSecret] = useState(null);
  const [runLoading, setRunLoading] = useState(false);

  const [activeTab, setActiveTab] = useState('templates');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [templatesRes, instancesRes, devicesRes, secretsRes] = await Promise.all([
        getWorkflowTemplates(),
        getWorkflowInstances(),
        getDevices(),
        getVaultSecrets().catch(() => ({ data: { data: [] } })),
      ]);
      setTemplates(templatesRes.data.data || []);
      setInstances(instancesRes.data.data || []);
      setDevices(
        (devicesRes.data.data || []).map((d) => ({
          value: String(d.id),
          label: d.name,
        }))
      );
      setVaultSecrets(
        (secretsRes.data.data || []).map((s) => ({
          value: String(s.id),
          label: s.name,
        }))
      );
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async (data) => {
    await createWorkflowTemplate(data);
    await fetchData();
    setShowBuilder(false);
  };

  const handleUpdateTemplate = async (data) => {
    await updateWorkflowTemplate(editingTemplate.id, data);
    await fetchData();
    setEditingTemplate(null);
    setShowBuilder(false);
  };

  const handleDeleteTemplate = async (template) => {
    if (!window.confirm(`Delete workflow template "${template.name}"?`)) return;
    try {
      await deleteWorkflowTemplate(template.id);
      await fetchData();
    } catch (err) {
      setError(err);
    }
  };

  const openRunModal = (template) => {
    setSelectedTemplate(template);
    setSelectedDeviceIds([]);
    setRollbackOnFailure(false);
    setSelectedVaultSecret(null);
    setShowRunModal(true);
  };

  const handleRunWorkflow = async () => {
    if (selectedDeviceIds.length === 0) {
      setError({ userMessage: 'Please select at least one device' });
      return;
    }

    setRunLoading(true);
    try {
      await startWorkflow({
        templateId: selectedTemplate.id,
        deviceIds: selectedDeviceIds.map((id) => parseInt(id)),
        rollbackOnFailure,
        vaultSecretId: selectedVaultSecret ? parseInt(selectedVaultSecret) : null,
      });
      setShowRunModal(false);
      setActiveTab('instances');
      await fetchData();
    } catch (err) {
      setError(err);
    } finally {
      setRunLoading(false);
    }
  };

  const handleCancelWorkflow = async (instanceId) => {
    try {
      await cancelWorkflow(instanceId);
      await fetchData();
    } catch (err) {
      setError(err);
    }
  };

  if (loading) {
    return (
      <Group justify="center" py="xl">
        <Loader />
        <Text c="dimmed">Loading workflows...</Text>
      </Group>
    );
  }

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Text size="xl" fw={600}>
          Workflows
        </Text>
        <Group gap="sm">
          <ActionIcon variant="subtle" onClick={fetchData}>
            <IconRefresh size={18} />
          </ActionIcon>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => {
              setEditingTemplate(null);
              setShowBuilder(true);
            }}
          >
            New Template
          </Button>
        </Group>
      </Group>

      {error && <ErrorDisplay error={error} onRetry={fetchData} />}

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Tab value="templates">
            Templates ({templates.length})
          </Tabs.Tab>
          <Tabs.Tab value="instances">
            Instances ({instances.length})
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="templates" pt="md">
          {templates.length === 0 ? (
            <Paper withBorder p="xl" ta="center">
              <Text c="dimmed">
                No workflow templates yet. Create one to get started.
              </Text>
            </Paper>
          ) : (
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Name</Table.Th>
                  <Table.Th>Description</Table.Th>
                  <Table.Th>Steps</Table.Th>
                  <Table.Th>Created</Table.Th>
                  <Table.Th w={100}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {templates.map((template) => (
                  <Table.Tr key={template.id}>
                    <Table.Td>
                      <Text fw={500}>{template.name}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed" lineClamp={1}>
                        {template.description || '-'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge variant="light">{template.steps?.length || 0} steps</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {template.created_at
                          ? new Date(template.created_at).toLocaleDateString()
                          : '-'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon
                          variant="subtle"
                          color="green"
                          onClick={() => openRunModal(template)}
                          title="Run workflow"
                        >
                          <IconPlayerPlay size={16} />
                        </ActionIcon>
                        <Menu shadow="md" width={150}>
                          <Menu.Target>
                            <ActionIcon variant="subtle">
                              <IconDotsVertical size={16} />
                            </ActionIcon>
                          </Menu.Target>
                          <Menu.Dropdown>
                            <Menu.Item
                              leftSection={<IconEdit size={14} />}
                              onClick={() => {
                                setEditingTemplate(template);
                                setShowBuilder(true);
                              }}
                            >
                              Edit
                            </Menu.Item>
                            <Menu.Item
                              leftSection={<IconTrash size={14} />}
                              color="red"
                              onClick={() => handleDeleteTemplate(template)}
                            >
                              Delete
                            </Menu.Item>
                          </Menu.Dropdown>
                        </Menu>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="instances" pt="md">
          {instances.length === 0 ? (
            <Paper withBorder p="xl" ta="center">
              <Text c="dimmed">
                No workflow instances yet. Run a workflow template to create one.
              </Text>
            </Paper>
          ) : (
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>ID</Table.Th>
                  <Table.Th>Template</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Devices</Table.Th>
                  <Table.Th>Started</Table.Th>
                  <Table.Th>Completed</Table.Th>
                  <Table.Th w={80}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {instances.map((instance) => (
                  <Table.Tr key={instance.id}>
                    <Table.Td>
                      <Text fw={500}>#{instance.id}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{instance.template_name || '-'}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={STATUS_COLORS[instance.status] || 'gray'}>
                        {instance.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {instance.device_ids?.length || 0} device(s)
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {instance.started_at
                          ? new Date(instance.started_at).toLocaleString()
                          : '-'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {instance.completed_at
                          ? new Date(instance.completed_at).toLocaleString()
                          : '-'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      {['pending', 'running'].includes(instance.status) && (
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => handleCancelWorkflow(instance.id)}
                          title="Cancel workflow"
                        >
                          <IconX size={16} />
                        </ActionIcon>
                      )}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          )}
        </Tabs.Panel>
      </Tabs>

      {/* Workflow Builder Modal */}
      {showBuilder && (
        <WorkflowBuilder
          template={editingTemplate}
          onSave={editingTemplate ? handleUpdateTemplate : handleCreateTemplate}
          onCancel={() => {
            setShowBuilder(false);
            setEditingTemplate(null);
          }}
        />
      )}

      {/* Run Workflow Modal */}
      <Modal
        opened={showRunModal}
        onClose={() => setShowRunModal(false)}
        title={`Run Workflow: ${selectedTemplate?.name}`}
        size="md"
      >
        <Stack gap="md">
          <MultiSelect
            label="Target Devices"
            placeholder="Select devices to run workflow on"
            data={devices}
            value={selectedDeviceIds}
            onChange={setSelectedDeviceIds}
            required
            searchable
          />

          <Switch
            label="Rollback on Failure"
            description="Automatically run rollback actions if any step fails"
            checked={rollbackOnFailure}
            onChange={(e) => setRollbackOnFailure(e.currentTarget.checked)}
          />

          {vaultSecrets.length > 0 && (
            <Select
              label="Vault Secret"
              placeholder="No vault secret"
              description="Optional vault password for encrypted content"
              data={vaultSecrets}
              value={selectedVaultSecret}
              onChange={setSelectedVaultSecret}
              clearable
            />
          )}

          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setShowRunModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleRunWorkflow}
              loading={runLoading}
              disabled={selectedDeviceIds.length === 0}
            >
              Run Workflow
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

export default WorkflowList;
