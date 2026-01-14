import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

const TOKEN_STORAGE_KEY = 'homelab-token';
const USER_STORAGE_KEY = 'homelab-user';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    // Try to load user from localStorage on initial mount
    const savedUser = localStorage.getItem(USER_STORAGE_KEY);
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch {
        return null;
      }
    }
    return null;
  });

  const [token, setToken] = useState(() => {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is authenticated
  const isAuthenticated = !!token && !!user;

  // Check if user is admin
  const isAdmin = user?.is_admin || false;

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        // Set the token in the default headers
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

        // Verify token by fetching current user
        const response = await api.get('/auth/me');
        setUser(response.data);
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.data));
        setError(null);
      } catch (err) {
        // Token is invalid or expired
        console.error('Token verification failed:', err);
        logout();
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, [token]);

  // Login function
  const login = useCallback(async (username, password) => {
    setError(null);
    try {
      const response = await api.post('/auth/login', { username, password });
      const { access_token, user: userData } = response.data;

      // Save token and user
      localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));

      // Set token in axios defaults
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      setToken(access_token);
      setUser(userData);

      return { success: true };
    } catch (err) {
      const message = err.response?.data?.error || err.userMessage || 'Login failed';
      setError(message);
      return { success: false, error: message };
    }
  }, []);

  // Logout function
  const logout = useCallback(() => {
    // Clear storage
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);

    // Clear axios headers
    delete api.defaults.headers.common['Authorization'];

    // Clear state
    setToken(null);
    setUser(null);
    setError(null);
  }, []);

  // Update user profile
  const updateProfile = useCallback(async (data) => {
    try {
      const response = await api.put('/auth/me', data);
      const updatedUser = response.data;
      setUser(updatedUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updatedUser));
      return { success: true, user: updatedUser };
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to update profile';
      return { success: false, error: message };
    }
  }, []);

  // Change password
  const changePassword = useCallback(async (currentPassword, newPassword) => {
    try {
      await api.put('/auth/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to change password';
      return { success: false, error: message };
    }
  }, []);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    if (!token) return;

    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.data));
    } catch (err) {
      console.error('Failed to refresh user:', err);
    }
  }, [token]);

  const value = {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    updateProfile,
    changePassword,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
