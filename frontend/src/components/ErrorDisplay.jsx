function ErrorDisplay({ error, onRetry, showRetry = true }) {
  const getErrorDetails = () => {
    if (typeof error === 'string') {
      return { message: error, details: null };
    }

    if (error?.isNetworkError) {
      return {
        message: 'Unable to connect to the backend API',
        details: 'Please ensure the backend server is running and accessible.',
      };
    }

    if (error?.response?.data?.error) {
      return {
        message: error.response.data.error,
        details: error.response.data.details
          ? JSON.stringify(error.response.data.details, null, 2)
          : null,
      };
    }

    return {
      message: error?.message || 'An unexpected error occurred',
      details: null,
    };
  };

  const { message, details } = getErrorDetails();

  return (
    <div className="error-display">
      <div className="error-icon">⚠️</div>
      <h3 className="error-title">Error</h3>
      <p className="error-message">{message}</p>
      {details && (
        <pre className="error-details">{details}</pre>
      )}
      {showRetry && onRetry && (
        <button
          className="btn btn-primary"
          onClick={onRetry}
        >
          Try Again
        </button>
      )}
    </div>
  );
}

export default ErrorDisplay;
