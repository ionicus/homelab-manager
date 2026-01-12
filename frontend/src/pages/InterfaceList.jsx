import { useState } from 'react';
import {
  deleteDeviceInterface,
  setPrimaryInterface,
} from '../services/api';

function InterfaceList({ interfaces, deviceId, onUpdate }) {
  const [loading, setLoading] = useState({});

  const handleSetPrimary = async (interfaceId) => {
    setLoading({ ...loading, [interfaceId]: true });
    try {
      await setPrimaryInterface(deviceId, interfaceId);
      await onUpdate();
    } catch (err) {
      alert('Failed to set primary interface');
    } finally {
      setLoading({ ...loading, [interfaceId]: false });
    }
  };

  const handleDelete = async (interfaceId, interfaceName) => {
    if (!confirm(`Are you sure you want to delete interface ${interfaceName}?`)) {
      return;
    }

    setLoading({ ...loading, [interfaceId]: true });
    try {
      await deleteDeviceInterface(deviceId, interfaceId);
      await onUpdate();
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to delete interface');
    } finally {
      setLoading({ ...loading, [interfaceId]: false });
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'up':
        return '🟢';
      case 'down':
        return '🔴';
      case 'disabled':
        return '⚫';
      default:
        return '⚪';
    }
  };

  if (interfaces.length === 0) {
    return (
      <div className="empty-state">
        <p>No network interfaces configured for this device</p>
      </div>
    );
  }

  return (
    <div className="interface-grid">
      {interfaces.map((iface) => (
        <div
          key={iface.id}
          className={`interface-card ${iface.is_primary ? 'interface-primary' : ''}`}
        >
          <div className="interface-header">
            <div className="interface-title">
              <h3>{iface.interface_name}</h3>
              {iface.is_primary && (
                <span className="primary-badge">PRIMARY</span>
              )}
            </div>
            <div className="interface-status">
              <span className="status-icon">{getStatusIcon(iface.status)}</span>
              <span className="status-text">{iface.status}</span>
            </div>
          </div>

          <div className="interface-details">
            <div className="interface-detail">
              <span className="detail-label">MAC Address</span>
              <span className="detail-value mono">{iface.mac_address}</span>
            </div>

            {iface.ip_address && (
              <div className="interface-detail">
                <span className="detail-label">IP Address</span>
                <span className="detail-value mono">{iface.ip_address}</span>
              </div>
            )}

            {iface.subnet_mask && (
              <div className="interface-detail">
                <span className="detail-label">Subnet Mask</span>
                <span className="detail-value mono">{iface.subnet_mask}</span>
              </div>
            )}

            {iface.gateway && (
              <div className="interface-detail">
                <span className="detail-label">Gateway</span>
                <span className="detail-value mono">{iface.gateway}</span>
              </div>
            )}

            {iface.vlan_id && (
              <div className="interface-detail">
                <span className="detail-label">VLAN ID</span>
                <span className="detail-value">{iface.vlan_id}</span>
              </div>
            )}
          </div>

          <div className="interface-actions">
            {!iface.is_primary && (
              <button
                className="btn btn-sm btn-outline"
                onClick={() => handleSetPrimary(iface.id)}
                disabled={loading[iface.id]}
              >
                Set as Primary
              </button>
            )}
            <button
              className="btn btn-sm btn-danger"
              onClick={() => handleDelete(iface.id, iface.interface_name)}
              disabled={loading[iface.id]}
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default InterfaceList;
