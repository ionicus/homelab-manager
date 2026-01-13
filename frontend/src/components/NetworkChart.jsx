import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function NetworkChart({ metrics, title = "Network Traffic" }) {
  if (!metrics || metrics.length === 0) {
    return (
      <div className="empty-state">
        <p>No network metrics data available</p>
      </div>
    );
  }

  // Format bytes to human-readable format
  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format data for the chart
  const chartData = metrics
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .map(metric => ({
      time: new Date(metric.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      rx: metric.network_rx_bytes || 0,
      tx: metric.network_tx_bytes || 0,
    }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="metrics-tooltip">
          <p className="tooltip-label">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {formatBytes(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="metrics-chart-container">
      <h3 className="chart-title">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="time"
            stroke="#ddd"
            style={{ fontSize: '0.875rem' }}
          />
          <YAxis
            stroke="#ddd"
            style={{ fontSize: '0.875rem' }}
            tickFormatter={formatBytes}
            label={{ value: 'Bytes', angle: -90, position: 'insideLeft', style: { fill: '#ddd' } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '0.875rem' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="rx"
            stroke="#4a9eff"
            strokeWidth={2}
            dot={{ r: 3 }}
            name="Received"
          />
          <Line
            type="monotone"
            dataKey="tx"
            stroke="#ff6b6b"
            strokeWidth={2}
            dot={{ r: 3 }}
            name="Transmitted"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default NetworkChart;
