import { useState, useEffect } from 'react';
import { getPlaybooks, triggerProvisioning } from '../services/api';
import ErrorDisplay from './ErrorDisplay';

function ProvisioningForm({ deviceId, onSuccess, onCancel }) {
  const [playbooks, setPlaybooks] = useState([]);
  const [selectedPlaybook, setSelectedPlaybook] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fetchingPlaybooks, setFetchingPlaybooks] = useState(true);

  useEffect(() => {
    fetchPlaybooks();
  }, []);

  const fetchPlaybooks = async () => {
    try {
      setFetchingPlaybooks(true);
      const response = await getPlaybooks();
      const playbookList = response.data.data?.playbooks || [];
      setPlaybooks(playbookList);
      if (playbookList.length > 0) {
        setSelectedPlaybook(playbookList[0]);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch playbooks:', err);
      setError(err);
    } finally {
      setFetchingPlaybooks(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedPlaybook) {
      setError({ userMessage: 'Please select a playbook' });
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await triggerProvisioning(deviceId, selectedPlaybook);
      if (onSuccess) {
        onSuccess(response.data.data);
      }
    } catch (err) {
      console.error('Failed to trigger provisioning:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-modal" onClick={onCancel}>
      <div className="form-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Run Ansible Playbook</h2>
          <button className="close-btn" onClick={onCancel}>&times;</button>
        </div>

        {error && <ErrorDisplay error={error} onRetry={fetchingPlaybooks ? null : fetchPlaybooks} />}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="playbook">Select Playbook *</label>
            {fetchingPlaybooks ? (
              <div className="loading-state">Loading available playbooks...</div>
            ) : playbooks.length === 0 ? (
              <div className="empty-state">
                <p>No playbooks available. Please add playbooks to ansible/playbooks/ directory.</p>
              </div>
            ) : (
              <select
                id="playbook"
                value={selectedPlaybook}
                onChange={(e) => setSelectedPlaybook(e.target.value)}
                required
                disabled={loading}
              >
                {playbooks.map((playbook) => (
                  <option key={playbook} value={playbook}>
                    {playbook}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="playbook-description">
            {selectedPlaybook === 'ping' && (
              <p>Test basic connectivity and SSH access to the device.</p>
            )}
            {selectedPlaybook === 'system_info' && (
              <p>Gather comprehensive system information (OS, CPU, memory, disk, network).</p>
            )}
            {selectedPlaybook === 'update' && (
              <p>Update system packages (requires sudo privileges).</p>
            )}
            {selectedPlaybook === 'docker_install' && (
              <p>Install Docker CE on Debian/Ubuntu systems (requires sudo privileges).</p>
            )}
            {selectedPlaybook === 'basic_setup' && (
              <p>Basic system setup and configuration.</p>
            )}
          </div>

          <div className="form-actions">
            <button type="button" onClick={onCancel} disabled={loading}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading || fetchingPlaybooks || playbooks.length === 0}
            >
              {loading ? 'Starting...' : 'Run Playbook'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ProvisioningForm;
