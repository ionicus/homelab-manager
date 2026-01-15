import { useState, useEffect } from 'react';
import { getExecutorActions, triggerAutomation } from '../services/api';
import ErrorDisplay from './ErrorDisplay';

function PlaybookSelector({ deviceId, onExecute }) {
  const [playbooks, setPlaybooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [executing, setExecuting] = useState(null);

  useEffect(() => {
    fetchPlaybooks();
  }, []);

  const fetchPlaybooks = async () => {
    try {
      setLoading(true);
      const response = await getExecutorActions('ansible');
      const playbookList = response.data.map(action => action.name);
      setPlaybooks(playbookList);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch playbooks:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (playbookName) => {
    if (!window.confirm(`Run ${playbookName} on this device?`)) {
      return;
    }

    try {
      setExecuting(playbookName);
      setError(null);
      const response = await triggerAutomation({ deviceId, actionName: playbookName });
      if (onExecute) {
        onExecute(response.data);
      }
    } catch (err) {
      console.error('Failed to execute playbook:', err);
      setError(err);
    } finally {
      setExecuting(null);
    }
  };

  const getPlaybookInfo = (name) => {
    const info = {
      ping: {
        category: 'Connectivity',
        icon: '🔌',
        description: 'Test SSH connectivity and verify device is reachable',
        requiresSudo: false,
      },
      system_info: {
        category: 'Discovery',
        icon: '📊',
        description: 'Gather system information (OS, CPU, memory, disk, network)',
        requiresSudo: false,
      },
      update: {
        category: 'Maintenance',
        icon: '🔄',
        description: 'Update system packages and apply security patches',
        requiresSudo: true,
      },
      docker_install: {
        category: 'Setup',
        icon: '🐳',
        description: 'Install Docker CE and configure container runtime',
        requiresSudo: true,
      },
      basic_setup: {
        category: 'Setup',
        icon: '⚙️',
        description: 'Basic system configuration and setup',
        requiresSudo: true,
      },
    };

    return info[name] || {
      category: 'Other',
      icon: '📦',
      description: 'Custom playbook',
      requiresSudo: false,
    };
  };

  const groupedPlaybooks = playbooks.reduce((acc, name) => {
    const info = getPlaybookInfo(name);
    if (!acc[info.category]) {
      acc[info.category] = [];
    }
    acc[info.category].push({ name, ...info });
    return acc;
  }, {});

  const categoryOrder = ['Connectivity', 'Discovery', 'Maintenance', 'Setup', 'Other'];
  const sortedCategories = categoryOrder.filter(cat => groupedPlaybooks[cat]);

  if (loading) {
    return <div className="loading-state">Loading playbooks...</div>;
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={fetchPlaybooks} />;
  }

  if (playbooks.length === 0) {
    return (
      <div className="empty-state">
        <p>No playbooks available. Add playbooks to ansible/playbooks/ directory.</p>
      </div>
    );
  }

  return (
    <div className="playbook-selector">
      {sortedCategories.map((category) => (
        <div key={category} className="playbook-category">
          <h4 className="category-title">{category}</h4>
          <div className="playbook-grid">
            {groupedPlaybooks[category].map((playbook) => (
              <button
                key={playbook.name}
                className={`playbook-card category-${playbook.category}`}
                onClick={() => handleExecute(playbook.name)}
                disabled={executing !== null}
              >
                <div className="playbook-icon">{playbook.icon}</div>
                <div className="playbook-content">
                  <div className="playbook-header">
                    <h5>{playbook.name}</h5>
                    {playbook.requiresSudo && (
                      <span className="sudo-badge" title="Requires sudo privileges">
                        sudo
                      </span>
                    )}
                  </div>
                  <p className="playbook-desc">{playbook.description}</p>
                  {executing === playbook.name && (
                    <div className="executing-indicator">
                      <span className="spinner"></span> Starting...
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default PlaybookSelector;
