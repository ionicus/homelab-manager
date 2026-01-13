import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Group, Collapse } from '@mantine/core';
import {
  getDevice,
  getDeviceServices,
  getDeviceMetrics,
  getDeviceInterfaces,
  getAutomationJobs,
} from '../services/api';
import { safeGetArray } from '../utils/validation';
import ErrorDisplay from '../components/ErrorDisplay';
import LoadingSkeleton from '../components/LoadingSkeleton';
import StatusBadge from '../components/StatusBadge';
import ServiceList from '../components/ServiceList';
import ServiceForm from '../components/ServiceForm';
import MetricsChart from '../components/MetricsChart';
import NetworkChart from '../components/NetworkChart';
import InterfaceList from './InterfaceList';
import InterfaceForm from './InterfaceForm';
import PlaybookSelector from '../components/PlaybookSelector';
import AutomationJobsList from '../components/AutomationJobsList';

function DeviceDetail() {
  const { id } = useParams();
  const [device, setDevice] = useState(null);
  const [services, setServices] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [interfaces, setInterfaces] = useState([]);
  const [automationJobs, setAutomationJobs] = useState([]);
  const [showInterfaceForm, setShowInterfaceForm] = useState(false);
  const [editingInterface, setEditingInterface] = useState(null);
  const [showServiceForm, setShowServiceForm] = useState(false);
  const [automationExpanded, setAutomationExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDeviceData();
  }, [id]);

  const fetchDeviceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [deviceRes, servicesRes, metricsRes, interfacesRes, jobsRes] = await Promise.all([
        getDevice(id),
        getDeviceServices(id),
        getDeviceMetrics(id, 50),
        getDeviceInterfaces(id),
        getAutomationJobs(id),
      ]);

      setDevice(deviceRes.data || deviceRes);
      setServices(safeGetArray(servicesRes));
      setMetrics(safeGetArray(metricsRes));
      setInterfaces(safeGetArray(interfacesRes));
      setAutomationJobs(safeGetArray(jobsRes));
      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  const handleInterfaceUpdate = async () => {
    setShowInterfaceForm(false);
    setEditingInterface(null);
    await fetchDeviceData();
  };

  const handleEditInterface = (iface) => {
    setEditingInterface(iface);
    setShowInterfaceForm(true);
  };

  const handleCancelInterfaceForm = () => {
    setShowInterfaceForm(false);
    setEditingInterface(null);
  };

  const handleServiceUpdate = async () => {
    setShowServiceForm(false);
    await fetchDeviceData();
  };

  const handlePlaybookExecute = async () => {
    await fetchDeviceData();
  };

  if (loading) return <LoadingSkeleton type="device-detail" />;
  if (error) return <ErrorDisplay error={error} onRetry={fetchDeviceData} />;
  if (!device) return <ErrorDisplay error="Device not found" onRetry={fetchDeviceData} />;

  const hasMetadata = device.metadata && Object.keys(device.metadata).length > 0;

  return (
    <div className="device-detail">
      <div className="page-header">
        <div className="header-content">
          <h1>{device.name}</h1>
          <StatusBadge status={device.status} />
        </div>
        <Group spacing="sm">
          <Button component={Link} to={`/devices/${device.id}/edit`}>Edit</Button>
          <Button component={Link} to="/devices" variant="default">Back to Devices</Button>
        </Group>
      </div>

      <div className="detail-overview">
        <div className="overview-card">
          <div className="overview-icon">🖥️</div>
          <div className="overview-content">
            <span className="overview-label">Type</span>
            <span className="overview-value">{device.type}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">🌐</div>
          <div className="overview-content">
            <span className="overview-label">IP Address</span>
            <span className="overview-value">{device.ip_address || 'Not set'}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">📍</div>
          <div className="overview-content">
            <span className="overview-label">MAC Address</span>
            <span className="overview-value">{device.mac_address || 'Not set'}</span>
          </div>
        </div>
        <div className="overview-card">
          <div className="overview-icon">📅</div>
          <div className="overview-content">
            <span className="overview-label">Created</span>
            <span className="overview-value">{new Date(device.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <div className="detail-sections">
        {hasMetadata && (
          <div className="detail-section">
            <h2>Metadata</h2>
            <div className="metadata-grid">
              {Object.entries(device.metadata).map(([key, value]) => (
                <div key={key} className="metadata-item">
                  <span className="metadata-key">{key}</span>
                  <span className="metadata-value">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="detail-section">
          <div className="section-header">
            <h2>Network Interfaces ({interfaces.length})</h2>
            <Button
              size="sm"
              onClick={() => { setEditingInterface(null); setShowInterfaceForm(true); }}
            >
              Add Interface
            </Button>
          </div>

          {showInterfaceForm && (
            <div className="interface-form-overlay">
              <InterfaceForm
                deviceId={id}
                interfaceData={editingInterface}
                onSuccess={handleInterfaceUpdate}
                onCancel={handleCancelInterfaceForm}
              />
            </div>
          )}

          <InterfaceList
            interfaces={interfaces}
            deviceId={id}
            onUpdate={fetchDeviceData}
            onEdit={handleEditInterface}
          />
        </div>

        <div className="detail-section">
          <div className="section-header">
            <h2>Services ({services.length})</h2>
            <Button
              size="sm"
              onClick={() => setShowServiceForm(true)}
            >
              Add Service
            </Button>
          </div>

          {showServiceForm && (
            <ServiceForm
              deviceId={id}
              onSuccess={handleServiceUpdate}
              onCancel={() => setShowServiceForm(false)}
            />
          )}

          <ServiceList
            services={services}
            deviceId={id}
            onUpdate={fetchDeviceData}
          />
        </div>

        <div className="detail-section">
          <div
            className="section-header section-header-collapsible"
            onClick={() => setAutomationExpanded(!automationExpanded)}
          >
            <h2>
              <span className={`collapse-icon ${automationExpanded ? 'expanded' : ''}`}>▶</span>
              Automation ({automationJobs.length})
            </h2>
          </div>

          <Collapse in={automationExpanded}>
            <div className="automation-subsection">
              <h3>Run Playbook</h3>
              <PlaybookSelector deviceId={id} onExecute={handlePlaybookExecute} />
            </div>

            <div className="automation-subsection">
              <h3>Execution History</h3>
              <AutomationJobsList jobs={automationJobs} />
            </div>
          </Collapse>
        </div>

        <div className="detail-section">
          <h2>Performance Metrics</h2>
          {metrics.length > 0 ? (
            <div className="metrics-visualization">
              <MetricsChart metrics={metrics} title="System Usage Over Time" />
              <NetworkChart metrics={metrics} title="Network Traffic Over Time" />
            </div>
          ) : (
            <div className="empty-state">
              <p>No metrics available for this device</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DeviceDetail;
