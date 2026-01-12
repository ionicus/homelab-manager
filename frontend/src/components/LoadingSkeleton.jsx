function LoadingSkeleton({ type = 'default', count = 1 }) {
  if (type === 'dashboard') {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <div className="skeleton skeleton-title"></div>
          <div className="skeleton skeleton-button"></div>
        </div>

        <div className="stats-grid">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="stat-card">
              <div className="skeleton skeleton-icon"></div>
              <div className="stat-content">
                <div className="skeleton skeleton-text"></div>
                <div className="skeleton skeleton-number"></div>
              </div>
            </div>
          ))}
        </div>

        <div className="dashboard-grid">
          <div className="dashboard-section">
            <div className="skeleton skeleton-subtitle"></div>
            <div className="type-grid">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton skeleton-card"></div>
              ))}
            </div>
          </div>
          <div className="dashboard-section">
            <div className="skeleton skeleton-subtitle"></div>
            {[...Array(3)].map((_, i) => (
              <div key={i} className="skeleton skeleton-list-item"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (type === 'device-list') {
    return (
      <div className="device-list-page">
        <div className="page-header">
          <div className="skeleton skeleton-title"></div>
          <div className="skeleton skeleton-button"></div>
        </div>
        <div className="devices-grid">
          {[...Array(count)].map((_, i) => (
            <div key={i} className="device-card">
              <div className="skeleton skeleton-card-header"></div>
              <div className="skeleton skeleton-card-body"></div>
              <div className="skeleton skeleton-card-footer"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (type === 'device-detail') {
    return (
      <div className="device-detail">
        <div className="page-header">
          <div className="skeleton skeleton-title"></div>
          <div className="skeleton skeleton-button"></div>
        </div>
        <div className="detail-overview">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="overview-card">
              <div className="skeleton skeleton-icon"></div>
              <div className="skeleton skeleton-text"></div>
            </div>
          ))}
        </div>
        <div className="detail-sections">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="detail-section">
              <div className="skeleton skeleton-subtitle"></div>
              <div className="skeleton skeleton-content"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Default skeleton
  return (
    <div className="loading-skeleton">
      {[...Array(count)].map((_, i) => (
        <div key={i} className="skeleton skeleton-line"></div>
      ))}
    </div>
  );
}

export default LoadingSkeleton;
