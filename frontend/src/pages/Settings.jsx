import { useState } from 'react';
import { Title, Paper, Stack, SegmentedControl, Text, Card, Group, Button, ColorSwatch, useMantineTheme, NavLink, Grid } from '@mantine/core';
import { IconPalette, IconBrush, IconSettings } from '@tabler/icons-react';
import { useTheme } from '../contexts/ThemeContext';

function Settings() {
  const [activeSection, setActiveSection] = useState('theme');
  const { currentTheme, switchTheme, availableThemes, pageAccents, updatePageAccent, resetAccents } = useTheme();
  const theme = useMantineTheme();

  const sections = [
    { id: 'theme', label: 'Theme', icon: IconPalette, description: 'Color scheme' },
    { id: 'accents', label: 'Page Accents', icon: IconBrush, description: 'Section colors' },
    { id: 'general', label: 'General', icon: IconSettings, description: 'App preferences', disabled: true },
  ];

  // Theme Section
  const themeOptions = availableThemes.map((themeName) => ({
    value: themeName,
    label: themeName.charAt(0).toUpperCase() + themeName.slice(1),
  }));

  const themeDescriptions = {
    dark: 'Classic dark theme with balanced contrast',
    light: 'Clean light theme for bright environments',
    midnight: 'Deep blue-black theme for minimal eye strain',
  };

  const themeColors = {
    dark: theme.colors.dark?.[6] || '#25262B',
    light: '#FFFFFF',
    midnight: '#141D2E',
  };

  // Accent Colors Section
  const availableColors = [
    { name: 'Blue', value: 'blue' },
    { name: 'Red', value: 'red' },
    { name: 'Green', value: 'green' },
    { name: 'Teal', value: 'teal' },
    { name: 'Cyan', value: 'cyan' },
    { name: 'Purple', value: 'purple' },
    { name: 'Violet', value: 'violet' },
    { name: 'Indigo', value: 'indigo' },
    { name: 'Pink', value: 'pink' },
    { name: 'Orange', value: 'orange' },
    { name: 'Yellow', value: 'yellow' },
    { name: 'Lime', value: 'lime' },
    { name: 'Grape', value: 'grape' },
  ];

  const accentSections = [
    { key: 'dashboard', label: 'Dashboard', icon: '📊' },
    { key: 'devices', label: 'Devices', icon: '🖥️' },
    { key: 'services', label: 'Services', icon: '⚙️' },
    { key: 'automation', label: 'Automation', icon: '🤖' },
  ];

  const renderThemeSection = () => (
    <Stack spacing="xl">
      <div>
        <Title order={2} mb="xs">Theme</Title>
        <Text size="sm" color="dimmed">
          Choose your preferred color scheme
        </Text>
      </div>

      <Paper shadow="sm" p="lg" withBorder>
        <Stack spacing="md">
          <Text size="sm" weight={500}>Color Scheme</Text>

          <SegmentedControl
            value={currentTheme}
            onChange={switchTheme}
            data={themeOptions}
            size="md"
            fullWidth
          />

          <div>
            <Text size="sm" weight={500} mb="sm">
              Preview
            </Text>
            <Group spacing="md">
              {availableThemes.map((themeName) => (
                <Card
                  key={themeName}
                  shadow="sm"
                  p="lg"
                  withBorder
                  style={{
                    flex: 1,
                    backgroundColor: themeColors[themeName],
                    borderColor: currentTheme === themeName
                      ? theme.colors[theme.primaryColor][6]
                      : undefined,
                    borderWidth: currentTheme === themeName ? 2 : 1,
                  }}
                >
                  <Stack spacing="xs">
                    <Text
                      size="sm"
                      weight={600}
                      style={{
                        color: themeName === 'light' ? '#000' : '#fff',
                      }}
                    >
                      {themeName.charAt(0).toUpperCase() + themeName.slice(1)}
                    </Text>
                    <Text
                      size="xs"
                      style={{
                        color: themeName === 'light' ? '#666' : '#aaa',
                      }}
                    >
                      {themeDescriptions[themeName]}
                    </Text>
                  </Stack>
                </Card>
              ))}
            </Group>
          </div>

          <Text size="xs" color="dimmed">
            Stored in browser localStorage (key: homelab-theme)
          </Text>
        </Stack>
      </Paper>
    </Stack>
  );

  const renderAccentsSection = () => (
    <Stack spacing="xl">
      <Group justify="space-between" align="center">
        <div>
          <Title order={2} mb="xs">Page Accent Colors</Title>
          <Text size="sm" color="dimmed">
            Customize the accent color for each section
          </Text>
        </div>
        <Button size="xs" variant="subtle" onClick={resetAccents}>
          Reset to Defaults
        </Button>
      </Group>

      <Stack spacing="lg">
        {accentSections.map((section) => (
          <Paper key={section.key} shadow="sm" p="lg" withBorder>
            <Stack spacing="md">
              <Group justify="space-between" align="center">
                <Group spacing="sm">
                  <Text size="xl">{section.icon}</Text>
                  <div>
                    <Text size="md" weight={600}>{section.label}</Text>
                    <Text size="xs" color="dimmed" tt="capitalize">
                      Current: {pageAccents[section.key]}
                    </Text>
                  </div>
                </Group>
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    background: theme.colors[pageAccents[section.key]][6],
                    borderRadius: '8px',
                    border: '2px solid',
                    borderColor: theme.colorScheme === 'dark' ? theme.colors.dark[4] : theme.colors.gray[3],
                  }}
                />
              </Group>

              <div>
                <Text size="xs" weight={500} mb="xs" color="dimmed">
                  Choose color:
                </Text>
                <Group spacing="xs">
                  {availableColors.map((color) => (
                    <ColorSwatch
                      key={color.value}
                      color={theme.colors[color.value][6]}
                      size={32}
                      style={{
                        cursor: 'pointer',
                        border: pageAccents[section.key] === color.value
                          ? `3px solid ${theme.colors[color.value][9]}`
                          : '2px solid transparent',
                      }}
                      onClick={() => updatePageAccent(section.key, color.value)}
                      title={color.name}
                    />
                  ))}
                </Group>
              </div>
            </Stack>
          </Paper>
        ))}
      </Stack>

      <Text size="xs" color="dimmed">
        Stored in browser localStorage (key: homelab-accents)
      </Text>
    </Stack>
  );

  const renderGeneralSection = () => (
    <Stack spacing="xl">
      <div>
        <Title order={2} mb="xs">General Settings</Title>
        <Text size="sm" color="dimmed">
          Application preferences (Coming soon)
        </Text>
      </div>

      <Paper shadow="sm" p="lg" withBorder>
        <Text color="dimmed" ta="center" py="xl">
          Additional settings will be available here in future updates
        </Text>
      </Paper>
    </Stack>
  );

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
      </div>

      <Grid gutter="lg">
        <Grid.Col span={3}>
          <Paper shadow="sm" p="md" withBorder>
            <Stack spacing="xs">
              {sections.map((section) => {
                const Icon = section.icon;
                return (
                  <NavLink
                    key={section.id}
                    label={section.label}
                    description={section.description}
                    icon={<Icon size={20} />}
                    active={activeSection === section.id}
                    onClick={() => !section.disabled && setActiveSection(section.id)}
                    disabled={section.disabled}
                    style={{
                      borderRadius: theme.radius.sm,
                    }}
                  />
                );
              })}
            </Stack>
          </Paper>

          <Paper shadow="sm" p="md" withBorder mt="md">
            <Stack spacing="xs">
              <Text size="xs" weight={600} color="dimmed">Storage Location</Text>
              <Text size="xs" color="dimmed">
                All settings are stored locally in your browser using localStorage API.
                They persist across sessions but are specific to this browser.
              </Text>
            </Stack>
          </Paper>
        </Grid.Col>

        <Grid.Col span={9}>
          {activeSection === 'theme' && renderThemeSection()}
          {activeSection === 'accents' && renderAccentsSection()}
          {activeSection === 'general' && renderGeneralSection()}
        </Grid.Col>
      </Grid>
    </div>
  );
}

export default Settings;
