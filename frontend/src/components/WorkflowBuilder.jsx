import { useState, useEffect } from 'react';
import {
  Button,
  Group,
  CloseButton,
  Select,
  Stack,
  Text,
  TextInput,
  Textarea,
  Paper,
  ActionIcon,
  Badge,
  Loader,
} from '@mantine/core';
import { IconPlus, IconTrash, IconGripVertical, IconArrowDown } from '@tabler/icons-react';
import { getExecutorActions } from '../services/api';
import ErrorDisplay from './ErrorDisplay';

function WorkflowBuilder({ template = null, onSave, onCancel }) {
  const isEditing = !!template;

  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [steps, setSteps] = useState(template?.steps || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Available actions for the dropdown
  const [availableActions, setAvailableActions] = useState([]);
  const [fetchingActions, setFetchingActions] = useState(true);

  useEffect(() => {
    fetchActions();
  }, []);

  const fetchActions = async () => {
    try {
      setFetchingActions(true);
      const response = await getExecutorActions('ansible');
      const actions = response.data.data.map((action) => ({
        value: action.name,
        label: action.display_name || action.name,
      }));
      setAvailableActions(actions);
    } catch (err) {
      console.error('Failed to fetch actions:', err);
      setError(err);
    } finally {
      setFetchingActions(false);
    }
  };

  const addStep = () => {
    const newOrder = steps.length > 0 ? Math.max(...steps.map((s) => s.order)) + 1 : 0;
    setSteps([
      ...steps,
      {
        order: newOrder,
        action_name: '',
        executor_type: 'ansible',
        depends_on: [],
        rollback_action: null,
        extra_vars: null,
      },
    ]);
  };

  const removeStep = (order) => {
    // Remove the step
    const newSteps = steps.filter((s) => s.order !== order);
    // Remove dependencies on the deleted step
    setSteps(
      newSteps.map((s) => ({
        ...s,
        depends_on: s.depends_on.filter((dep) => dep !== order),
      }))
    );
  };

  const updateStep = (order, field, value) => {
    setSteps(
      steps.map((s) => (s.order === order ? { ...s, [field]: value } : s))
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!name.trim()) {
      setError({ userMessage: 'Workflow name is required' });
      return;
    }

    if (steps.length === 0) {
      setError({ userMessage: 'At least one step is required' });
      return;
    }

    // Validate all steps have actions
    const emptySteps = steps.filter((s) => !s.action_name);
    if (emptySteps.length > 0) {
      setError({ userMessage: 'All steps must have an action selected' });
      return;
    }

    // Validate dependencies
    const orderSet = new Set(steps.map((s) => s.order));
    for (const step of steps) {
      for (const dep of step.depends_on) {
        if (!orderSet.has(dep)) {
          setError({ userMessage: `Step ${step.order} depends on non-existent step ${dep}` });
          return;
        }
        if (dep >= step.order) {
          setError({
            userMessage: `Step ${step.order} cannot depend on step ${dep} (must depend on earlier steps)`,
          });
          return;
        }
      }
    }

    setLoading(true);
    setError(null);

    try {
      await onSave({
        name: name.trim(),
        description: description.trim() || null,
        steps: steps.map((s) => ({
          order: s.order,
          action_name: s.action_name,
          executor_type: s.executor_type || 'ansible',
          depends_on: s.depends_on || [],
          rollback_action: s.rollback_action || null,
          extra_vars: s.extra_vars || null,
        })),
      });
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // Get available dependencies for a step (all steps with lower order)
  const getDependencyOptions = (currentOrder) => {
    return steps
      .filter((s) => s.order < currentOrder)
      .map((s) => ({
        value: String(s.order),
        label: `Step ${s.order}: ${s.action_name || '(unnamed)'}`,
      }));
  };

  return (
    <div className="form-modal" onClick={onCancel}>
      <div
        className="form-modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '700px' }}
      >
        <Group justify="space-between" mb="md">
          <h2 style={{ margin: 0 }}>
            {isEditing ? 'Edit Workflow Template' : 'Create Workflow Template'}
          </h2>
          <CloseButton onClick={onCancel} size="lg" />
        </Group>

        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            {error && <ErrorDisplay error={error} />}

            <TextInput
              label="Workflow Name"
              placeholder="Enter workflow name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={loading}
            />

            <Textarea
              label="Description"
              placeholder="Optional description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={loading}
              rows={2}
            />

            <Group justify="space-between" align="center">
              <Text fw={500}>Steps</Text>
              <Button
                size="xs"
                leftSection={<IconPlus size={14} />}
                onClick={addStep}
                disabled={loading || fetchingActions}
              >
                Add Step
              </Button>
            </Group>

            {fetchingActions ? (
              <Group gap="sm">
                <Loader size="sm" />
                <Text c="dimmed">Loading available actions...</Text>
              </Group>
            ) : steps.length === 0 ? (
              <Text c="dimmed" ta="center" py="md">
                No steps added yet. Click &quot;Add Step&quot; to begin.
              </Text>
            ) : (
              <Stack gap="sm">
                {steps
                  .sort((a, b) => a.order - b.order)
                  .map((step, index) => (
                    <Paper key={step.order} withBorder p="sm" radius="sm">
                      <Group justify="space-between" mb="xs">
                        <Group gap="xs">
                          <IconGripVertical size={16} style={{ color: 'var(--mantine-color-dimmed)' }} />
                          <Badge variant="light">Step {step.order}</Badge>
                        </Group>
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => removeStep(step.order)}
                          disabled={loading}
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Group>

                      <Stack gap="xs">
                        <Select
                          label="Action"
                          placeholder="Select an action"
                          data={availableActions}
                          value={step.action_name}
                          onChange={(value) => updateStep(step.order, 'action_name', value)}
                          required
                          disabled={loading}
                          searchable
                        />

                        {index > 0 && (
                          <Select
                            label="Depends On"
                            placeholder="No dependencies"
                            data={getDependencyOptions(step.order)}
                            value={step.depends_on.length > 0 ? String(step.depends_on[0]) : null}
                            onChange={(value) =>
                              updateStep(
                                step.order,
                                'depends_on',
                                value ? [parseInt(value)] : []
                              )
                            }
                            clearable
                            disabled={loading}
                          />
                        )}

                        <Select
                          label="Rollback Action"
                          placeholder="No rollback"
                          description="Action to run if workflow fails after this step"
                          data={availableActions}
                          value={step.rollback_action}
                          onChange={(value) => updateStep(step.order, 'rollback_action', value)}
                          clearable
                          disabled={loading}
                          searchable
                        />
                      </Stack>
                    </Paper>
                  ))}
              </Stack>
            )}

            {steps.length > 1 && (
              <Paper withBorder p="sm" radius="sm" bg="var(--mantine-color-dark-6)">
                <Text size="sm" fw={500} mb="xs">
                  Execution Order
                </Text>
                <Group gap="xs" wrap="wrap">
                  {steps
                    .sort((a, b) => a.order - b.order)
                    .map((step, index) => (
                      <Group key={step.order} gap={4}>
                        <Badge variant="light" color="blue">
                          {step.action_name || `Step ${step.order}`}
                        </Badge>
                        {index < steps.length - 1 && (
                          <IconArrowDown size={14} style={{ color: 'var(--mantine-color-dimmed)' }} />
                        )}
                      </Group>
                    ))}
                </Group>
              </Paper>
            )}

            <Group gap="sm" justify="flex-end" mt="md">
              <Button type="button" onClick={onCancel} variant="default" disabled={loading}>
                Cancel
              </Button>
              <Button type="submit" loading={loading} disabled={fetchingActions || steps.length === 0}>
                {isEditing ? 'Update Workflow' : 'Create Workflow'}
              </Button>
            </Group>
          </Stack>
        </form>
      </div>
    </div>
  );
}

export default WorkflowBuilder;
