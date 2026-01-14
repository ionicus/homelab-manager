import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Paper,
  TextInput,
  PasswordInput,
  Button,
  Stack,
  Alert,
  Center,
  Box,
} from '@mantine/core';
import { useAuth } from '../contexts/AuthContext';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Get the page user was trying to access (for redirect after login)
  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const result = await login(username, password);
      if (result.success) {
        navigate(from, { replace: true });
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Center style={{ minHeight: '100vh' }}>
      <Box style={{ width: '100%', maxWidth: 400, padding: '0 1rem' }}>
        <Paper shadow="md" p="xl" withBorder>
          <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
            <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Homelab Manager</h1>
            <p style={{ margin: '0.5rem 0 0', color: 'var(--mantine-color-dimmed)' }}>
              Sign in to continue
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <Stack gap="md">
              {error && (
                <Alert color="red" variant="light">
                  {error}
                </Alert>
              )}

              <TextInput
                label="Username"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                autoComplete="username"
              />

              <PasswordInput
                label="Password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />

              <Button
                type="submit"
                fullWidth
                loading={loading}
                disabled={!username || !password}
              >
                Sign In
              </Button>
            </Stack>
          </form>
        </Paper>
      </Box>
    </Center>
  );
}

export default Login;
