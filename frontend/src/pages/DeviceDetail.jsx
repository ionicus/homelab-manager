import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Group, Collapse } from '@mantine/core';
import { useQuery, useQueryClient } from '@tanstack/react-query';
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
  const queryClient = useQueryClient();
  const [showInterfaceForm, setShowInterfaceForm] = useState(false);
  const [editingInterface, setEditingInterface] = useState(null);
  const [showServiceForm, setShowServiceForm] = useState(false);
  const [automationExpanded, setAutomationExpanded] = useState(false);

  // Device query
  const {
    data: device,
    isLoading: deviceLoading,
    error: deviceError,
    refetch: refetchDevice,
  } = useQuery({
    queryKey: ['device', id],
    queryFn: async () => {
      const res = await getDevice(id);
      return res.data || res;
    },
  });

  // Services query
  const { data: services = [] } = useQuery({
    queryKey: ['device', id, 'services'],
    queryFn: async () => safeGetArray(await getDeviceServices(id)),
    enabled: !!device,
  });

  // Metrics query
  const { data: metrics = [] } = useQuery({
    queryKey: ['device', id, 'metrics'],
    queryFn: async () => safeGetArray(await getDeviceMetrics(id, 50)),
    enabled: !!device,
  });

  // Interfaces query
  const { data: interfaces = [] } = useQuery({
    queryKey: ['device', id, 'interfaces'],
    queryFn: async () => safeGetArray(await getDeviceInterfaces(id)),
    enabled: !!device,
  });

  // Automation jobs query
  const { data: automationJobs = [] } = useQuery({
    queryKey: ['device', id, 'jobs'],
    queryFn: async () => safeGetArray(await getAutomationJobs(id)),
    enabled: !!device,
  });

  const handleInterfaceUpdate = () => {
    setShowInterfaceForm(false);
    setEditingInterface(null);
    queryClient.invalidateQueries({ queryKey: ['device', id, 'interfaces'] });
  };

  const handleEditInterface = (iface) => {
    setEditingInterface(iface);
    setShowInterfaceForm(true);
  };

  const handleCancelInterfaceForm = () => {
    setShowInterfaceForm(false);
    setEditingInterface(null);
  };

  const handleServiceUpdate = () => {
    setShowServiceForm(false);
    queryClient.invalidateQueries({ queryKey: ['device', id, 'services'] });
  };

  const handlePlaybookExecute = () => {
    queryClient.invalidateQueries({ queryKey: ['device', id, 'jobs'] });
  };

  if (deviceLoading) return <LoadingSkeleton type="device-detail" />;
  if (deviceError) return <ErrorDisplay error={deviceError} onRetry={refetchDevice} />;
  if (!device) return <ErrorDisplay error="Device not found" onRetry={refetchDevice} />;

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
            onUpdate={() => queryClient.invalidateQueries({ queryKey: ['device', id, 'interfaces'] })}
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
            onUpdate={() => queryClient.invalidateQueries({ queryKey: ['device', id, 'services'] })}
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
