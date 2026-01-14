import axios from 'axios';

// Use environment variable or dynamically construct from current hostname
const API_URL = import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:5000/api`;

// Base URL for the backend server (without /api)
const BACKEND_URL = API_URL.replace(/\/api$/, '');

// Helper to get full URL for uploaded files
export const getUploadUrl = (path) => {
  if (!path) return null;
  // If it's already a full URL, return as-is
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  // Otherwise, prepend the backend URL
  return `${BACKEND_URL}${path}`;
};

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('homelab-token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Network error (backend down, CORS issues, etc.)
    if (!error.response) {
      error.isNetworkError = true;
      error.userMessage = 'Cannot connect to backend server. Please check that the server is running.';
      return Promise.reject(error);
    }

    const status = error.response.status;
    const data = error.response.data;

    // Handle 401 Unauthorized - redirect to login (unless already there)
    if (status === 401) {
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('homelab-token');
        localStorage.removeItem('homelab-user');
        window.location.href = '/login';
      }
      error.userMessage = 'Session expired. Please log in again.';
      return Promise.reject(error);
    }

    // Handle other common status codes
    if (status === 403) {
      error.userMessage = data?.error || 'You do not have permission to perform this action';
    } else if (status === 404) {
      error.userMessage = data?.error || 'Resource not found';
    } else if (status === 400) {
      error.userMessage = data?.error || 'Invalid request';
    } else if (status === 409) {
      error.userMessage = data?.error || 'Resource already exists';
    } else if (status === 429) {
      error.userMessage = 'Too many requests. Please try again later.';
    } else if (status === 500) {
      error.userMessage = 'Server error occurred';
    } else {
      error.userMessage = data?.error || 'An error occurred';
    }

    return Promise.reject(error);
  }
);

// Devices
export const getDevices = () => api.get('/devices');
export const getDevice = (id) => api.get(`/devices/${id}`);
export const createDevice = (data) => api.post('/devices', data);
export const updateDevice = (id, data) => api.put(`/devices/${id}`, data);
export const deleteDevice = (id) => api.delete(`/devices/${id}`);

// Metrics
export const getDeviceMetrics = (deviceId, limit = 100) =>
  api.get(`/devices/${deviceId}/metrics?limit=${limit}`);
export const submitMetrics = (data) => api.post('/metrics', data);

// Services
export const getServices = () => api.get('/services');
export const getService = (id) => api.get(`/services/${id}`);
export const getDeviceServices = (deviceId) =>
  api.get(`/devices/${deviceId}/services`);
export const createService = (data) => api.post('/services', data);
export const updateService = (id, data) => api.put(`/services/${id}`, data);
export const deleteService = (id) => api.delete(`/services/${id}`);
export const updateServiceStatus = (serviceId, status) =>
  api.put(`/services/${serviceId}/status`, { status });

// Automation - Executors (extensible automation)
export const getExecutors = () => api.get('/automation/executors');
export const getExecutorActions = (executorType) =>
  api.get(`/automation/executors/${executorType}/actions`);

// Automation - Jobs
export const getAutomationJobs = (deviceId = null, executorType = null) => {
  const params = new URLSearchParams();
  if (deviceId) params.append('device_id', deviceId);
  if (executorType) params.append('executor_type', executorType);
  const queryString = params.toString();
  return api.get(`/automation/jobs${queryString ? `?${queryString}` : ''}`);
};

// Trigger automation job
export const triggerAutomation = (
  deviceId,
  actionName,
  executorType = 'ansible',
  actionConfig = null
) =>
  api.post('/automation', {
    device_id: deviceId,
    action_name: actionName,
    executor_type: executorType,
    action_config: actionConfig,
  });

export const getJobStatus = (jobId) => api.get(`/automation/${jobId}`);
export const getJobLogs = (jobId) => api.get(`/automation/${jobId}/logs`);

// Network Interfaces
export const getDeviceInterfaces = (deviceId) =>
  api.get(`/devices/${deviceId}/interfaces`);
export const createDeviceInterface = (deviceId, data) =>
  api.post(`/devices/${deviceId}/interfaces`, data);
export const updateDeviceInterface = (deviceId, interfaceId, data) =>
  api.put(`/devices/${deviceId}/interfaces/${interfaceId}`, data);
export const deleteDeviceInterface = (deviceId, interfaceId) =>
  api.delete(`/devices/${deviceId}/interfaces/${interfaceId}`);
export const setPrimaryInterface = (deviceId, interfaceId) =>
  api.put(`/devices/${deviceId}/interfaces/${interfaceId}/set-primary`);

// Authentication
export const login = (username, password) =>
  api.post('/auth/login', { username, password });
export const getCurrentUser = () => api.get('/auth/me');
export const updateCurrentUser = (data) => api.put('/auth/me', data);
export const changePassword = (currentPassword, newPassword) =>
  api.put('/auth/me/password', {
    current_password: currentPassword,
    new_password: newPassword,
  });
export const uploadAvatar = (file) => {
  const formData = new FormData();
  formData.append('avatar', file);
  return api.post('/auth/me/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const deleteAvatar = () => api.delete('/auth/me/avatar');
export const updatePreferences = (data) => api.put('/auth/me/preferences', data);

// User Management (admin only)
export const getUsers = () => api.get('/auth/users');
export const getUser = (userId) => api.get(`/auth/users/${userId}`);
export const createUser = (data) => api.post('/auth/users', data);
export const updateUser = (userId, data) => api.put(`/auth/users/${userId}`, data);
export const deleteUser = (userId) => api.delete(`/auth/users/${userId}`);
export const resetUserPassword = (userId, newPassword) =>
  api.post(`/auth/users/${userId}/reset-password`, { new_password: newPassword });

export default api;
