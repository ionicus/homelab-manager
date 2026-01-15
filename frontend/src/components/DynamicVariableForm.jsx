import { useState, useEffect } from 'react';
import {
  TextInput,
  NumberInput,
  Checkbox,
  Select,
  Textarea,
  Stack,
  Text,
  Paper,
  Group,
  Badge,
  ActionIcon,
  Button,
} from '@mantine/core';
import { IconPlus, IconTrash } from '@tabler/icons-react';

/**
 * DynamicVariableForm - Renders form fields based on JSON Schema
 *
 * Supports the following JSON Schema types:
 * - string (with optional enum for select)
 * - number/integer
 * - boolean (checkbox)
 * - array (of strings, with add/remove)
 *
 * @param {object} schema - JSON Schema for the variables
 * @param {object} values - Current variable values
 * @param {function} onChange - Callback when values change
 * @param {boolean} disabled - Whether form is disabled
 */
function DynamicVariableForm({ schema, values = {}, onChange, disabled = false }) {
  const [localValues, setLocalValues] = useState(values);

  // Sync with external values
  useEffect(() => {
    setLocalValues(values);
  }, [values]);

  // No schema = no form
  if (!schema || !schema.properties || Object.keys(schema.properties).length === 0) {
    return (
      <Text size="sm" c="dimmed" ta="center" py="md">
        This playbook has no configurable variables.
      </Text>
    );
  }

  const handleChange = (key, value) => {
    const newValues = { ...localValues, [key]: value };
    setLocalValues(newValues);
    if (onChange) {
      onChange(newValues);
    }
  };

  const handleArrayAdd = (key) => {
    const current = localValues[key] || [];
    handleChange(key, [...current, '']);
  };

  const handleArrayRemove = (key, index) => {
    const current = localValues[key] || [];
    const newArray = current.filter((_, i) => i !== index);
    handleChange(key, newArray);
  };

  const handleArrayItemChange = (key, index, value) => {
    const current = localValues[key] || [];
    const newArray = [...current];
    newArray[index] = value;
    handleChange(key, newArray);
  };

  const renderField = (key, propSchema) => {
    const value = localValues[key];
    const label = propSchema.title || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    const description = propSchema.description;
    const required = (schema.required || []).includes(key);

    // Handle enum (select dropdown)
    if (propSchema.enum) {
      return (
        <Select
          key={key}
          label={label}
          description={description}
          placeholder={`Select ${label.toLowerCase()}`}
          value={value ?? propSchema.default ?? ''}
          onChange={(v) => handleChange(key, v)}
          data={propSchema.enum.map((e) => ({ value: e, label: e }))}
          required={required}
          disabled={disabled}
          clearable
        />
      );
    }

    // Handle by type
    switch (propSchema.type) {
      case 'boolean':
        return (
          <Checkbox
            key={key}
            label={label}
            description={description}
            checked={value ?? propSchema.default ?? false}
            onChange={(e) => handleChange(key, e.target.checked)}
            disabled={disabled}
          />
        );

      case 'integer':
      case 'number':
        return (
          <NumberInput
            key={key}
            label={label}
            description={description}
            value={value ?? propSchema.default ?? ''}
            onChange={(v) => handleChange(key, v)}
            required={required}
            disabled={disabled}
            min={propSchema.minimum}
            max={propSchema.maximum}
            step={propSchema.type === 'integer' ? 1 : 0.1}
          />
        );

      case 'array':
        const arrayValue = value ?? propSchema.default ?? [];
        return (
          <Paper key={key} withBorder p="sm" radius="sm">
            <Group justify="space-between" mb="xs">
              <div>
                <Text size="sm" fw={500}>
                  {label}
                  {required && <span style={{ color: 'red' }}> *</span>}
                </Text>
                {description && (
                  <Text size="xs" c="dimmed">
                    {description}
                  </Text>
                )}
              </div>
              <Button
                size="xs"
                variant="light"
                leftSection={<IconPlus size={14} />}
                onClick={() => handleArrayAdd(key)}
                disabled={disabled}
              >
                Add
              </Button>
            </Group>
            <Stack gap="xs">
              {arrayValue.map((item, index) => (
                <Group key={index} gap="xs">
                  <TextInput
                    value={item}
                    onChange={(e) => handleArrayItemChange(key, index, e.target.value)}
                    disabled={disabled}
                    style={{ flex: 1 }}
                    placeholder={`${label} item ${index + 1}`}
                  />
                  <ActionIcon
                    color="red"
                    variant="light"
                    onClick={() => handleArrayRemove(key, index)}
                    disabled={disabled}
                  >
                    <IconTrash size={16} />
                  </ActionIcon>
                </Group>
              ))}
              {arrayValue.length === 0 && (
                <Text size="xs" c="dimmed" ta="center">
                  No items. Click &quot;Add&quot; to add one.
                </Text>
              )}
            </Stack>
          </Paper>
        );

      case 'string':
      default:
        // Check if it should be a textarea (multiline)
        if (propSchema.format === 'textarea' || (propSchema.maxLength && propSchema.maxLength > 200)) {
          return (
            <Textarea
              key={key}
              label={label}
              description={description}
              value={value ?? propSchema.default ?? ''}
              onChange={(e) => handleChange(key, e.target.value)}
              required={required}
              disabled={disabled}
              minRows={3}
              maxLength={propSchema.maxLength}
              placeholder={propSchema.examples?.[0] || `Enter ${label.toLowerCase()}`}
            />
          );
        }
        return (
          <TextInput
            key={key}
            label={label}
            description={description}
            value={value ?? propSchema.default ?? ''}
            onChange={(e) => handleChange(key, e.target.value)}
            required={required}
            disabled={disabled}
            maxLength={propSchema.maxLength}
            placeholder={propSchema.examples?.[0] || `Enter ${label.toLowerCase()}`}
          />
        );
    }
  };

  // Sort properties: required first, then alphabetically
  const sortedKeys = Object.keys(schema.properties).sort((a, b) => {
    const aRequired = (schema.required || []).includes(a);
    const bRequired = (schema.required || []).includes(b);
    if (aRequired && !bRequired) return -1;
    if (!aRequired && bRequired) return 1;
    return a.localeCompare(b);
  });

  return (
    <Stack gap="md">
      <Group gap="xs">
        <Text size="sm" fw={500}>
          Playbook Variables
        </Text>
        {schema.title && (
          <Badge size="sm" variant="light">
            {schema.title}
          </Badge>
        )}
      </Group>
      {schema.description && (
        <Text size="xs" c="dimmed">
          {schema.description}
        </Text>
      )}
      {sortedKeys.map((key) => renderField(key, schema.properties[key]))}
    </Stack>
  );
}

export default DynamicVariableForm;
