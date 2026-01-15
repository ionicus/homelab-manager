import { Badge } from '@mantine/core';

function StatusBadge({ status, ...props }) {
  const getStatusColor = (status) => {
    const statusLower = status?.toLowerCase() || '';

    // Map status values to Mantine colors
    const statusMap = {
      active: 'green',
      inactive: 'red',
      maintenance: 'yellow',
      running: 'green',
      stopped: 'red',
      error: 'red',
      pending: 'blue',
      success: 'green',
      completed: 'green',
      failed: 'red',
      cancelled: 'orange',
      warning: 'yellow',
    };

    return statusMap[statusLower] || 'gray';
  };

  return (
    <Badge color={getStatusColor(status)} variant="filled" {...props}>
      {status}
    </Badge>
  );
}

export default StatusBadge;
