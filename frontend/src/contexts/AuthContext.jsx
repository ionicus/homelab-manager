import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import api, {
  setCsrfToken,
  clearCsrfToken,
  getCsrfToken,
  uploadAvatar as uploadAvatarApi,
  deleteAvatar as deleteAvatarApi,
  logout as logoutApi
} from '../services/api';

const AuthContext = createContext(null);

const USER_STORAGE_KEY = 'homelab-user';

export function AuthProvider({ children }) {
  // User info can be stored in localStorage (not sensitive)
  // But auth state depends on HttpOnly cookie (checked via /auth/me)
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
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated by verifying with backend
  // This validates the HttpOnly cookie
  const isAuthenticated = !!user && !!getCsrfToken();
  const isAdmin = user?.is_admin || false;

  // On mount, verify authentication status with backend
  useEffect(() => {
    const verifyAuth = async () => {
      // If we have cached user info, try to verify the session
      if (user) {
        try {
          const response = await api.get('/auth/me');
          const data = response.data?.data || response.data;
          const { csrf_token, user: userData } = data;

          // Store refreshed CSRF token (needed after page reload)
          if (csrf_token) {
            setCsrfToken(csrf_token);
          }

          setUser(userData || data);
          localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData || data));
        } catch {
          // Session invalid - clear local state
          setUser(null);
          clearCsrfToken();
          localStorage.removeItem(USER_STORAGE_KEY);
        }
      }
      setLoading(false);
    };
    verifyAuth();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (username, password) => {
    setError(null);
    try {
      const response = await api.post('/auth/login', { username, password });

      // Response now contains csrf_token and user in data envelope
      const data = response.data?.data || response.data;
      const { csrf_token, user: userData } = data;

      if (!csrf_token || !userData) {
        throw new Error('Invalid response from server');
      }

      // Store CSRF token in memory (api.js)
      setCsrfToken(csrf_token);

      // Save user info to localStorage (not sensitive)
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));

      // Update state
      setUser(userData);

      return { success: true };
    } catch (err) {
      const message = err.response?.data?.error || err.message || 'Login failed';
      setError(message);
      return { success: false, error: message };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      // Call backend to clear the HttpOnly cookie
      await logoutApi();
    } catch {
      // Continue with local logout even if API fails
    }
    clearCsrfToken();
    localStorage.removeItem(USER_STORAGE_KEY);
    setUser(null);
    setError(null);
  }, []);

  const updateProfile = useCallback(async (data) => {
    try {
      const response = await api.put('/auth/me', data);
      const updatedUser = response.data?.data || response.data;
      setUser(updatedUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updatedUser));
      return { success: true, user: updatedUser };
    } catch (err) {
      const error = new Error(err.response?.data?.error || 'Failed to update profile');
      error.userMessage = error.message;
      throw error;
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
      const error = new Error(err.response?.data?.error || 'Failed to change password');
      error.userMessage = error.message;
      throw error;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const response = await api.get('/auth/me');
      const userData = response.data?.data || response.data;
      setUser(userData);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));
    } catch {
      // Silently fail - user can retry manually
    }
  }, []);

  const uploadAvatar = useCallback(async (file) => {
    try {
      const response = await uploadAvatarApi(file);
      const updatedUser = response.data?.data?.user || response.data.user;
      setUser(updatedUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updatedUser));
      return { success: true, avatarUrl: response.data?.data?.avatar_url || response.data.avatar_url };
    } catch (err) {
      return { success: false, error: err.response?.data?.error || 'Failed to upload avatar' };
    }
  }, []);

  const deleteAvatar = useCallback(async () => {
    try {
      const response = await deleteAvatarApi();
      const updatedUser = response.data?.data?.user || response.data.user;
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
      loading,
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
