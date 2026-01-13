import axios from 'axios';

// Use environment variable or dynamically construct from current hostname
const API_URL = import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:5000/api`;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Response interceptor for consistent error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Network error (backend down, CORS issues, etc.)
    if (!error.response) {
      error.isNetworkError = true;
      error.userMessage = 'Cannot connect to backend server. Please check that the server is running.';
      console.error('Network error:', error.message);
      return Promise.reject(error);
    }

    // Server returned an error response
    const status = error.response.status;
    const data = error.response.data;

    // Add user-friendly messages based on status code
    if (status === 404) {
      error.userMessage = data?.error || 'Resource not found';
    } else if (status === 400) {
      error.userMessage = data?.error || 'Invalid request';
    } else if (status === 409) {
      error.userMessage = data?.error || 'Resource already exists';
    } else if (status === 500) {
      error.userMessage = 'Server error occurred';
    } else {
      error.userMessage = data?.error || 'An error occurred';
    }

    console.error(`API Error (${status}):`, data?.error || error.message);
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

// Trigger automation with executor type support (backwards compatible)
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

// Legacy: trigger with playbook_name for backwards compatibility
export const triggerPlaybook = (deviceId, playbookName) =>
  api.post('/automation', { device_id: deviceId, playbook_name: playbookName });

export const getJobStatus = (jobId) => api.get(`/automation/${jobId}`);
export const getJobLogs = (jobId) => api.get(`/automation/${jobId}/logs`);

// Deprecated: Use getExecutorActions('ansible') instead
export const getPlaybooks = () => api.get('/automation/playbooks');

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

export default api;
