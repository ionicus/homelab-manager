import axios from 'axios';

// API URL configuration:
// 1. Use explicit VITE_API_URL if set (for development or non-standard deployments)
// 2. Default to /api (works with nginx proxy in production)
// 3. For development without proxy, set VITE_API_URL in .env.development.local
const API_URL = import.meta.env.VITE_API_URL || '/api';

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

// CSRF token stored in memory (not localStorage - cleared on page close)
let csrfToken = null;

export const setCsrfToken = (token) => {
  csrfToken = token;
};

export const getCsrfToken = () => csrfToken;

export const clearCsrfToken = () => {
  csrfToken = null;
};

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
  withCredentials: true, // Enable cookie-based auth
});

// Request interceptor to add CSRF token for state-changing requests
api.interceptors.request.use(
  (config) => {
    // Add CSRF token for non-GET requests (state-changing operations)
    if (csrfToken && config.method !== 'get') {
      config.headers['X-CSRF-TOKEN'] = csrfToken;
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
        clearCsrfToken();
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
export const getActionSchema = (executorType, actionName) =>
  api.get(`/automation/executors/${executorType}/actions/${actionName}/schema`);

// Automation - Jobs
export const getAutomationJobs = (deviceId = null, executorType = null) => {
  const params = new URLSearchParams();
  if (deviceId) params.append('device_id', deviceId);
  if (executorType) params.append('executor_type', executorType);
  const queryString = params.toString();
  return api.get(`/automation/jobs${queryString ? `?${queryString}` : ''}`);
};

// Trigger automation job
// Supports both single device (deviceId) and multi-device (deviceIds) modes
export const triggerAutomation = ({
  deviceId = null,
  deviceIds = null,
  actionName,
  executorType = 'ansible',
  actionConfig = null,
  extraVars = null,
  vaultSecretId = null,
}) =>
  api.post('/automation', {
    device_id: deviceId,
    device_ids: deviceIds,
    action_name: actionName,
    executor_type: executorType,
    action_config: actionConfig,
    extra_vars: extraVars,
    vault_secret_id: vaultSecretId,
  });

export const getJobStatus = (jobId) => api.get(`/automation/${jobId}`);
export const getJobLogs = (jobId) => api.get(`/automation/${jobId}/logs`);
export const cancelJob = (jobId) => api.post(`/automation/${jobId}/cancel`);
export const rerunJob = (jobId) => api.post(`/automation/${jobId}/rerun`);

// Vault Secrets
export const getVaultSecrets = () => api.get('/automation/vault/secrets');
export const createVaultSecret = (data) => api.post('/automation/vault/secrets', data);
export const updateVaultSecret = (secretId, data) =>
  api.put(`/automation/vault/secrets/${secretId}`, data);
export const deleteVaultSecret = (secretId) =>
  api.delete(`/automation/vault/secrets/${secretId}`);

// Get the URL for SSE log streaming (for EventSource)
export const getJobLogStreamUrl = (jobId, includeExisting = true) =>
  `${API_URL}/automation/${jobId}/logs/stream?include_existing=${includeExisting}`;

// Workflow Templates
export const getWorkflowTemplates = (page = 1, perPage = 20) =>
  api.get(`/workflows/templates?page=${page}&per_page=${perPage}`);
export const getWorkflowTemplate = (templateId) =>
  api.get(`/workflows/templates/${templateId}`);
export const createWorkflowTemplate = (data) => api.post('/workflows/templates', data);
export const updateWorkflowTemplate = (templateId, data) =>
  api.put(`/workflows/templates/${templateId}`, data);
export const deleteWorkflowTemplate = (templateId) =>
  api.delete(`/workflows/templates/${templateId}`);

// Workflow Instances
export const startWorkflow = ({
  templateId,
  deviceIds,
  rollbackOnFailure = false,
  extraVars = null,
  vaultSecretId = null,
}) =>
  api.post('/workflows', {
    template_id: templateId,
    device_ids: deviceIds,
    rollback_on_failure: rollbackOnFailure,
    extra_vars: extraVars,
    vault_secret_id: vaultSecretId,
  });
export const getWorkflowInstances = ({ templateId = null, status = null, page = 1, perPage = 20 } = {}) => {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('per_page', perPage);
  if (templateId) params.append('template_id', templateId);
  if (status) params.append('status', status);
  return api.get(`/workflows?${params.toString()}`);
};
export const getWorkflowInstance = (instanceId, includeJobs = false) =>
  api.get(`/workflows/${instanceId}?include_jobs=${includeJobs}`);
export const cancelWorkflow = (instanceId) =>
  api.post(`/workflows/${instanceId}/cancel`);

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
export const logout = () => api.post('/auth/logout');
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
