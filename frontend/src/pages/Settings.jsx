import { useState, useEffect, useRef } from 'react';
import {
  Title, Paper, Stack, SegmentedControl, Text, Card, Group, Button,
  ColorSwatch, useMantineTheme, NavLink, Grid, TextInput, PasswordInput,
  Switch, Table, ActionIcon, Modal, Alert, Badge, Loader, Avatar, FileButton
} from '@mantine/core';
import { IconPalette, IconBrush, IconSettings, IconUsers, IconUser, IconTrash, IconEdit, IconPlus, IconUpload } from '@tabler/icons-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { getUsers, createUser, updateUser, deleteUser, resetUserPassword, getUploadUrl, getSettings, updateSetting } from '../services/api';

function Settings() {
  const [activeSection, setActiveSection] = useState('profile');
  const { currentTheme, switchTheme, availableThemes, pageAccents, updatePageAccent, resetAccents } = useTheme();
  const { user, updateProfile, changePassword, uploadAvatar, deleteAvatar } = useAuth();
  const theme = useMantineTheme();
  const resetFileRef = useRef(null);

  // Profile state
  const [profileForm, setProfileForm] = useState({
    display_name: '',
    email: '',
    bio: '',
    avatar_url: '',
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [profileSuccess, setProfileSuccess] = useState(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarError, setAvatarError] = useState(null);

  // Password change state
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState(null);
  const [passwordSuccess, setPasswordSuccess] = useState(null);

  // Users management state (admin only)
  const queryClient = useQueryClient();
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    display_name: '',
    password: '',
    is_admin: false,
  });
  const [userFormError, setUserFormError] = useState(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');

  // Application settings state (admin only)
  const [appSettingsForm, setAppSettingsForm] = useState({});
  const [appSettingsLoading, setAppSettingsLoading] = useState(false);
  const [appSettingsError, setAppSettingsError] = useState(null);
  const [appSettingsSuccess, setAppSettingsSuccess] = useState(null);

  // Initialize profile form with current user data
  useEffect(() => {
    if (user) {
      setProfileForm({
        display_name: user.display_name || '',
        email: user.email || '',
        bio: user.bio || '',
        avatar_url: user.avatar_url || '',
      });
    }
  }, [user]);

  // Fetch users with TanStack Query (only when admin views users section)
  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersQueryError,
  } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await getUsers();
      // API returns { data: [...] } envelope
      return response.data.data || response.data.users || response.data;
    },
    enabled: activeSection === 'users' && user?.is_admin,
  });

  const users = usersData || [];
  const usersError = usersQueryError?.userMessage || (usersQueryError ? 'Failed to load users' : null);

  // Fetch application settings (admin only)
  const {
    data: appSettingsData,
    isLoading: appSettingsQueryLoading,
    error: appSettingsQueryError,
  } = useQuery({
    queryKey: ['appSettings'],
    queryFn: async () => {
      const response = await getSettings();
      // API returns { data: [...] } envelope
      return response.data.data || response.data.settings || response.data;
    },
    enabled: activeSection === 'appsettings' && user?.is_admin,
  });

  // Initialize form when settings are loaded
  useEffect(() => {
    if (appSettingsData && Array.isArray(appSettingsData)) {
      const formData = {};
      appSettingsData.forEach((setting) => {
        formData[setting.key] = setting.value;
      });
      setAppSettingsForm(formData);
    }
  }, [appSettingsData]);

  // Mutations for user CRUD operations
  const createUserMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setUserModalOpen(false);
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }) => updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setUserModalOpen(false);
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setDeleteConfirmOpen(false);
      setUserToDelete(null);
    },
  });

  const resetPasswordMutation = useMutation({
    mutationFn: ({ id, password }) => resetUserPassword(id, password),
    onSuccess: () => {
      setResetPasswordOpen(false);
      setResetPasswordUser(null);
      setNewPassword('');
    },
  });

  // Profile handlers
  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileError(null);
    setProfileSuccess(null);
    try {
      await updateProfile(profileForm);
      setProfileSuccess('Profile updated successfully');
    } catch (err) {
      setProfileError(err.userMessage || 'Failed to update profile');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleAvatarUpload = async (file) => {
    if (!file) return;
    setAvatarUploading(true);
    setAvatarError(null);
    const result = await uploadAvatar(file);
    setAvatarUploading(false);
    if (result.success) {
      setProfileForm(prev => ({ ...prev, avatar_url: result.avatarUrl }));
      resetFileRef.current?.();
    } else {
      setAvatarError(result.error);
    }
  };

  const handleAvatarDelete = async () => {
    setAvatarUploading(true);
    setAvatarError(null);
    const result = await deleteAvatar();
    setAvatarUploading(false);
    if (result.success) {
      setProfileForm(prev => ({ ...prev, avatar_url: '' }));
    } else {
      setAvatarError(result.error);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('Passwords do not match');
      return;
    }
    setPasswordLoading(true);
    setPasswordError(null);
    setPasswordSuccess(null);
    try {
      await changePassword(passwordForm.current_password, passwordForm.new_password);
      setPasswordSuccess('Password changed successfully');
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setPasswordError(err.userMessage || 'Failed to change password');
    } finally {
      setPasswordLoading(false);
    }
  };

  // User management handlers (admin)
  const openCreateUserModal = () => {
    setEditingUser(null);
    setUserForm({ username: '', email: '', display_name: '', password: '', is_admin: false });
    setUserFormError(null);
    setUserModalOpen(true);
  };

  const openEditUserModal = (userToEdit) => {
    setEditingUser(userToEdit);
    setUserForm({
      username: userToEdit.username,
      email: userToEdit.email,
      display_name: userToEdit.display_name || '',
      password: '',
      is_admin: userToEdit.is_admin,
    });
    setUserFormError(null);
    setUserModalOpen(true);
  };

  const handleUserFormSubmit = (e) => {
    e.preventDefault();
    setUserFormError(null);
    if (editingUser) {
      const updateData = {
        email: userForm.email,
        display_name: userForm.display_name,
        is_admin: userForm.is_admin,
      };
      updateUserMutation.mutate(
        { id: editingUser.id, data: updateData },
        { onError: (err) => setUserFormError(err.userMessage || 'Failed to save user') }
      );
    } else {
      createUserMutation.mutate(userForm, {
        onError: (err) => setUserFormError(err.userMessage || 'Failed to save user'),
      });
    }
  };

  const handleDeleteUser = () => {
    if (!userToDelete) return;
    deleteUserMutation.mutate(userToDelete.id);
  };

  const handleResetPassword = () => {
    if (!resetPasswordUser || !newPassword) return;
    resetPasswordMutation.mutate({ id: resetPasswordUser.id, password: newPassword });
  };

  const userFormLoading = createUserMutation.isPending || updateUserMutation.isPending;

  // Application settings handlers
  const handleAppSettingUpdate = async (key, value) => {
    setAppSettingsLoading(true);
    setAppSettingsError(null);
    setAppSettingsSuccess(null);
    try {
      await updateSetting(key, value);
      setAppSettingsForm((prev) => ({ ...prev, [key]: value }));
      queryClient.invalidateQueries({ queryKey: ['appSettings'] });
      setAppSettingsSuccess(`Setting "${key}" updated successfully`);
    } catch (err) {
      setAppSettingsError(err.userMessage || 'Failed to update setting');
    } finally {
      setAppSettingsLoading(false);
    }
  };

  const baseSections = [
    { id: 'profile', label: 'Profile', icon: IconUser, description: 'Your account' },
    { id: 'theme', label: 'Theme', icon: IconPalette, description: 'Color scheme' },
    { id: 'accents', label: 'Page Accents', icon: IconBrush, description: 'Section colors' },
  ];

  const adminSections = [
    { id: 'users', label: 'Users', icon: IconUsers, description: 'Manage users' },
    { id: 'appsettings', label: 'Application', icon: IconSettings, description: 'App settings' },
  ];

  const sections = user?.is_admin
    ? [...baseSections.slice(0, 1), ...adminSections, ...baseSections.slice(1)]
    : baseSections;

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

  const settingDescriptions = {
    session_timeout_minutes: 'How long until users are automatically logged out due to inactivity',
    max_login_attempts: 'Number of failed login attempts before account is temporarily locked',
    lockout_duration_minutes: 'How long an account stays locked after too many failed attempts',
  };

  const renderAppSettingsSection = () => (
    <Stack spacing="xl">
      <div>
        <Title order={2} mb="xs">Application Settings</Title>
        <Text size="sm" c="dimmed">
          Configure system-wide application settings
        </Text>
      </div>

      {appSettingsError && <Alert color="red" mb="md">{appSettingsError}</Alert>}
      {appSettingsSuccess && <Alert color="green" mb="md">{appSettingsSuccess}</Alert>}

      <Paper shadow="sm" p="lg" withBorder>
        {appSettingsQueryLoading ? (
          <Group justify="center" py="xl">
            <Loader />
          </Group>
        ) : appSettingsQueryError ? (
          <Alert color="red">
            {appSettingsQueryError.userMessage || 'Failed to load settings'}
          </Alert>
        ) : (
          <Stack spacing="lg">
            <Title order={4}>Session & Security</Title>

            <TextInput
              label="Session Timeout (minutes)"
              description={settingDescriptions.session_timeout_minutes}
              value={appSettingsForm.session_timeout_minutes || '60'}
              onChange={(e) => setAppSettingsForm((prev) => ({
                ...prev,
                session_timeout_minutes: e.target.value,
              }))}
              type="number"
              min={1}
              max={1440}
              rightSection={
                <Button
                  size="xs"
                  variant="light"
                  onClick={() => handleAppSettingUpdate('session_timeout_minutes', appSettingsForm.session_timeout_minutes)}
                  loading={appSettingsLoading}
                >
                  Save
                </Button>
              }
              rightSectionWidth={70}
            />

            <TextInput
              label="Max Login Attempts"
              description={settingDescriptions.max_login_attempts}
              value={appSettingsForm.max_login_attempts || '5'}
              onChange={(e) => setAppSettingsForm((prev) => ({
                ...prev,
                max_login_attempts: e.target.value,
              }))}
              type="number"
              min={1}
              max={20}
              rightSection={
                <Button
                  size="xs"
                  variant="light"
                  onClick={() => handleAppSettingUpdate('max_login_attempts', appSettingsForm.max_login_attempts)}
                  loading={appSettingsLoading}
                >
                  Save
                </Button>
              }
              rightSectionWidth={70}
            />

            <TextInput
              label="Lockout Duration (minutes)"
              description={settingDescriptions.lockout_duration_minutes}
              value={appSettingsForm.lockout_duration_minutes || '15'}
              onChange={(e) => setAppSettingsForm((prev) => ({
                ...prev,
                lockout_duration_minutes: e.target.value,
              }))}
              type="number"
              min={1}
              max={1440}
              rightSection={
                <Button
                  size="xs"
                  variant="light"
                  onClick={() => handleAppSettingUpdate('lockout_duration_minutes', appSettingsForm.lockout_duration_minutes)}
                  loading={appSettingsLoading}
                >
                  Save
                </Button>
              }
              rightSectionWidth={70}
            />
          </Stack>
        )}
      </Paper>

      <Text size="xs" c="dimmed">
        Changes take effect immediately. Session timeout applies to new logins.
      </Text>
    </Stack>
  );

  const renderProfileSection = () => (
    <Stack spacing="xl">
      <div>
        <Title order={2} mb="xs">Profile</Title>
        <Text size="sm" color="dimmed">
          Manage your account information
        </Text>
      </div>

      {/* Profile Info */}
      <Paper shadow="sm" p="lg" withBorder>
        <form onSubmit={handleProfileSubmit}>
          <Stack spacing="md">
            <Group align="flex-start">
              <Stack spacing="xs" align="center">
                <Avatar
                  src={getUploadUrl(profileForm.avatar_url || user?.avatar_url)}
                  size={80}
                  radius="md"
                  color="blue"
                >
                  {user?.username?.charAt(0).toUpperCase()}
                </Avatar>
                <Group spacing="xs">
                  <FileButton
                    resetRef={resetFileRef}
                    onChange={handleAvatarUpload}
                    accept="image/png,image/jpeg,image/gif,image/webp"
                  >
                    {(props) => (
                      <Button
                        {...props}
                        size="xs"
                        variant="light"
                        loading={avatarUploading}
                        leftSection={<IconUpload size={14} />}
                      >
                        Upload
                      </Button>
                    )}
                  </FileButton>
                  {(profileForm.avatar_url || user?.avatar_url) && (
                    <Button
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={handleAvatarDelete}
                      loading={avatarUploading}
                    >
                      Remove
                    </Button>
                  )}
                </Group>
              </Stack>
              <div style={{ flex: 1 }}>
                <Text size="sm" fw={500} mb={4}>Username</Text>
                <Text size="sm" c="dimmed">{user?.username}</Text>
                <Text size="xs" c="dimmed" mt={4}>Username cannot be changed</Text>
              </div>
            </Group>

            {avatarError && <Alert color="red" mb="xs">{avatarError}</Alert>}

            <TextInput
              label="Display Name"
              placeholder="How you want to be called"
              value={profileForm.display_name}
              onChange={(e) => setProfileForm({ ...profileForm, display_name: e.target.value })}
            />

            <TextInput
              label="Email"
              type="email"
              placeholder="your@email.com"
              value={profileForm.email}
              onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
              required
            />

            <TextInput
              label="Avatar URL"
              placeholder="https://example.com/avatar.jpg (or upload above)"
              description="You can enter a URL or upload an image file above"
              value={profileForm.avatar_url}
              onChange={(e) => setProfileForm({ ...profileForm, avatar_url: e.target.value })}
            />

            <TextInput
              label="Bio"
              placeholder="A short bio about yourself"
              value={profileForm.bio}
              onChange={(e) => setProfileForm({ ...profileForm, bio: e.target.value })}
            />

            {profileError && <Alert color="red">{profileError}</Alert>}
            {profileSuccess && <Alert color="green">{profileSuccess}</Alert>}

            <Group justify="flex-end">
              <Button type="submit" loading={profileLoading}>
                Save Profile
              </Button>
            </Group>
          </Stack>
        </form>
      </Paper>

      {/* Change Password */}
      <Paper shadow="sm" p="lg" withBorder>
        <Title order={4} mb="md">Change Password</Title>
        <form onSubmit={handlePasswordSubmit}>
          <Stack spacing="md">
            <PasswordInput
              label="Current Password"
              placeholder="Enter current password"
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
              required
            />

            <PasswordInput
              label="New Password"
              placeholder="Enter new password"
              description="At least 8 characters with uppercase, lowercase, and a number"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
              required
            />

            <PasswordInput
              label="Confirm New Password"
              placeholder="Confirm new password"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
              required
            />

            {passwordError && <Alert color="red">{passwordError}</Alert>}
            {passwordSuccess && <Alert color="green">{passwordSuccess}</Alert>}

            <Group justify="flex-end">
              <Button type="submit" loading={passwordLoading}>
                Change Password
              </Button>
            </Group>
          </Stack>
        </form>
      </Paper>
    </Stack>
  );

  const renderUsersSection = () => (
    <Stack spacing="xl">
      <Group justify="space-between" align="center">
        <div>
          <Title order={2} mb="xs">User Management</Title>
          <Text size="sm" color="dimmed">
            Manage system users and permissions
          </Text>
        </div>
        <Button leftSection={<IconPlus size={16} />} onClick={openCreateUserModal}>
          Add User
        </Button>
      </Group>

      {usersError && <Alert color="red" mb="md">{usersError}</Alert>}

      <Paper shadow="sm" p="lg" withBorder>
        {usersLoading ? (
          <Group justify="center" py="xl">
            <Loader />
          </Group>
        ) : (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>User</Table.Th>
                <Table.Th>Email</Table.Th>
                <Table.Th>Role</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {users.map((u) => (
                <Table.Tr key={u.id}>
                  <Table.Td>
                    <Group spacing="sm">
                      <Avatar src={getUploadUrl(u.avatar_url)} size={32} radius="xl" color="blue">
                        {u.username?.charAt(0).toUpperCase()}
                      </Avatar>
                      <div>
                        <Text size="sm" weight={500}>{u.display_name || u.username}</Text>
                        <Text size="xs" color="dimmed">@{u.username}</Text>
                      </div>
                    </Group>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{u.email}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge color={u.is_admin ? 'red' : 'blue'} variant="light">
                      {u.is_admin ? 'Admin' : 'User'}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Badge color={u.is_active ? 'green' : 'gray'} variant="light">
                      {u.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group spacing="xs">
                      <ActionIcon
                        variant="subtle"
                        color="blue"
                        onClick={() => openEditUserModal(u)}
                        title="Edit user"
                      >
                        <IconEdit size={16} />
                      </ActionIcon>
                      <ActionIcon
                        variant="subtle"
                        color="orange"
                        onClick={() => {
                          setResetPasswordUser(u);
                          setResetPasswordOpen(true);
                        }}
                        title="Reset password"
                      >
                        <IconUser size={16} />
                      </ActionIcon>
                      {u.id !== user?.id && (
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => {
                            setUserToDelete(u);
                            setDeleteConfirmOpen(true);
                          }}
                          title="Delete user"
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      )}
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Paper>

      {/* Create/Edit User Modal */}
      <Modal
        opened={userModalOpen}
        onClose={() => setUserModalOpen(false)}
        title={editingUser ? 'Edit User' : 'Create User'}
      >
        <form onSubmit={handleUserFormSubmit}>
          <Stack spacing="md">
            {!editingUser && (
              <TextInput
                label="Username"
                placeholder="username"
                value={userForm.username}
                onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                required
              />
            )}

            <TextInput
              label="Email"
              type="email"
              placeholder="user@example.com"
              value={userForm.email}
              onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
              required
            />

            <TextInput
              label="Display Name"
              placeholder="Display Name"
              value={userForm.display_name}
              onChange={(e) => setUserForm({ ...userForm, display_name: e.target.value })}
            />

            {!editingUser && (
              <PasswordInput
                label="Password"
                placeholder="Initial password"
                description="At least 8 characters with uppercase, lowercase, and a number"
                value={userForm.password}
                onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                required
              />
            )}

            <Switch
              label="Administrator"
              description="Admins can manage users and system settings"
              checked={userForm.is_admin}
              onChange={(e) => setUserForm({ ...userForm, is_admin: e.currentTarget.checked })}
            />

            {userFormError && <Alert color="red">{userFormError}</Alert>}

            <Group justify="flex-end">
              <Button variant="subtle" onClick={() => setUserModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={userFormLoading}>
                {editingUser ? 'Save Changes' : 'Create User'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        title="Confirm Delete"
        size="sm"
      >
        <Stack spacing="md">
          <Text>
            Are you sure you want to delete user <strong>{userToDelete?.username}</strong>?
            This action cannot be undone.
          </Text>
          <Group justify="flex-end">
            <Button variant="subtle" onClick={() => setDeleteConfirmOpen(false)}>
              Cancel
            </Button>
            <Button color="red" onClick={handleDeleteUser}>
              Delete User
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Reset Password Modal */}
      <Modal
        opened={resetPasswordOpen}
        onClose={() => setResetPasswordOpen(false)}
        title="Reset Password"
        size="sm"
      >
        <Stack spacing="md">
          <Text>
            Set a new password for <strong>{resetPasswordUser?.username}</strong>
          </Text>
          <PasswordInput
            label="New Password"
            placeholder="Enter new password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={() => setResetPasswordOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleResetPassword}>
              Reset Password
            </Button>
          </Group>
        </Stack>
      </Modal>
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
          {activeSection === 'profile' && renderProfileSection()}
          {activeSection === 'users' && user?.is_admin && renderUsersSection()}
          {activeSection === 'appsettings' && user?.is_admin && renderAppSettingsSection()}
          {activeSection === 'theme' && renderThemeSection()}
          {activeSection === 'accents' && renderAccentsSection()}
        </Grid.Col>
      </Grid>
    </div>
  );
}

export default Settings;
