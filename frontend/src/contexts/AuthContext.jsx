import { createContext, useContext, useState, useCallback } from 'react';
import api, { uploadAvatar as uploadAvatarApi, deleteAvatar as deleteAvatarApi } from '../services/api';

const AuthContext = createContext(null);

const TOKEN_STORAGE_KEY = 'homelab-token';
const USER_STORAGE_KEY = 'homelab-user';

export function AuthProvider({ children }) {
  // Initialize state from localStorage
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem(USER_STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });
  const [error, setError] = useState(null);

  const isAuthenticated = !!token && !!user;
  const isAdmin = user?.is_admin || false;

  // Set axios header if we have a token
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  const login = useCallback(async (username, password) => {
    setError(null);
    try {
      const response = await api.post('/auth/login', { username, password });

      const { access_token, user: userData } = response.data;
      if (!access_token || !userData) {
        throw new Error('Invalid response from server');
      }

      // Save to localStorage
      localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));

      // Set axios header
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      // Update state
      setToken(access_token);
      setUser(userData);

      return { success: true };
    } catch (err) {
      const message = err.response?.data?.error || err.message || 'Login failed';
      setError(message);
      return { success: false, error: message };
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    delete api.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
    setError(null);
  }, []);

  const updateProfile = useCallback(async (data) => {
    try {
      const response = await api.put('/auth/me', data);
      const updatedUser = response.data;
      setUser(updatedUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updatedUser));
      return { success: true, user: updatedUser };
    } catch (err) {
      return { success: false, error: err.response?.data?.error || 'Failed to update profile' };
    }
  }, []);

  const changePassword = useCallback(async (currentPassword, newPassword) => {
    try {
      await api.put('/auth/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      return { success: true };
    } catch (err) {
      return { success: false, error: err.response?.data?.error || 'Failed to change password' };
    }
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.data));
    } catch {
      // Silently fail - user can retry manually
    }
  }, [token]);

  const uploadAvatar = useCallback(async (file) => {
    try {
      const response = await uploadAvatarApi(file);
      const updatedUser = response.data.user;
      setUser(updatedUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updatedUser));
      return { success: true, avatarUrl: response.data.avatar_url };
    } catch (err) {
      return { success: false, error: err.response?.data?.error || 'Failed to upload avatar' };
    }
  }, []);

  const deleteAvatar = useCallback(async () => {
    try {
      const response = await deleteAvatarApi();
      const updatedUser = response.data.user;
      setUser(updatedUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updatedUser));
      return { success: true };
    } catch (err) {
      return { success: false, error: err.response?.data?.error || 'Failed to delete avatar' };
    }
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading: false,
      error,
      isAuthenticated,
      isAdmin,
      login,
      logout,
      updateProfile,
      changePassword,
      refreshUser,
      uploadAvatar,
      deleteAvatar,
    }}>
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
