import { Alert, Stack, Button, Code } from '@mantine/core';

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
    <Stack spacing="md" p="md">
      <Alert
        color="red"
        title="Error"
        icon={<span style={{ fontSize: '1.5rem' }}>⚠️</span>}
      >
        {message}
      </Alert>
      {details && (
        <Code block>{details}</Code>
      )}
      {showRetry && onRetry && (
        <Button onClick={onRetry}>
          Try Again
        </Button>
      )}
    </Stack>
  );
}

export default ErrorDisplay;
