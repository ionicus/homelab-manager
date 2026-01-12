import axios from 'axios';

// Use environment variable or dynamically construct from current hostname
const API_URL = import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:5000/api`;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
export const getDeviceServices = (deviceId) => 
  api.get(`/devices/${deviceId}/services`);
export const updateServiceStatus = (serviceId, status) => 
  api.put(`/services/${serviceId}/status`, { status });

// Provisioning
export const triggerProvisioning = (deviceId, playbookName) => 
  api.post('/provision', { device_id: deviceId, playbook_name: playbookName });
export const getJobStatus = (jobId) => api.get(`/provision/${jobId}`);
export const getJobLogs = (jobId) => api.get(`/provision/${jobId}/logs`);

export default api;
