# Homelab Manager API Documentation

Version: 0.1.0
Base URL: `http://localhost:5000/api`

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Devices](#devices)
- [Network Interfaces](#network-interfaces)
- [Services](#services)
- [Metrics](#metrics)
- [Automation](#automation)

---

## Overview

The Homelab Manager API provides comprehensive management of homelab infrastructure including devices, network interfaces, services, and performance metrics.

### Features

- **Centralized Device Management**: Track servers, VMs, containers, and network equipment
- **Multi-Homed Network Support**: Manage multiple network interfaces per device with MAC, IP, VLAN configuration
- **Service Monitoring**: Track running services with health checks and status
- **Performance Metrics**: Collect and query CPU, memory, disk, and network usage
- **Ansible Integration**: Trigger automation jobs for device configuration

### Request/Response Format

- All requests and responses use **JSON**
- Request body must include `Content-Type: application/json` header
- Timestamps are in ISO 8601 format

---

## Authentication

**Current Status**: Authentication is not yet implemented. All endpoints are publicly accessible.

**Planned**: JWT-based authentication using `flask-jwt-extended`.

---

## Error Handling

All errors return a consistent JSON format with appropriate HTTP status codes.

### Error Response Format

```json
{
  "error": "Error message describing what went wrong"
}
```

### Validation Error Format

When request validation fails, detailed field-level errors are returned:

```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "field_name",
      "message": "Validation error description"
    }
  ]
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success - Request completed successfully |
| `201` | Created - Resource created successfully |
| `400` | Bad Request - Invalid request data or validation error |
| `404` | Not Found - Resource does not exist |
| `409` | Conflict - Resource already exists or constraint violation |
| `500` | Internal Server Error - Unexpected server error |

---

## Devices

Devices represent physical or virtual systems in your homelab (servers, VMs, containers, network equipment).

### Device Object

```json
{
  "id": 1,
  "name": "server-01",
  "type": "server",
  "status": "active",
  "ip_address": "192.168.1.10",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "metadata": {
    "location": "rack-1",
    "notes": "Primary web server"
  },
  "created_at": "2026-01-12T10:00:00",
  "updated_at": "2026-01-12T10:00:00"
}
```

### Device Types

- `server` - Physical or virtual server
- `vm` - Virtual machine
- `container` - Container instance
- `network` - Network equipment (router, switch, etc.)
- `storage` - Storage device (NAS, SAN, etc.)

### Device Status

- `active` - Device is operational
- `inactive` - Device is powered off or unavailable
- `maintenance` - Device is undergoing maintenance

### List All Devices

```http
GET /api/devices
```

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "name": "server-01",
    "type": "server",
    "status": "active",
    ...
  }
]
```

### Get Device

```http
GET /api/devices/{device_id}
```

**Parameters**:
- `device_id` (path, integer, required) - Device ID

**Response** `200 OK`:
```json
{
  "id": 1,
  "name": "server-01",
  "type": "server",
  ...
}
```

**Errors**:
- `404` - Device not found

### Create Device

```http
POST /api/devices
```

**Request Body**:
```json
{
  "name": "server-01",
  "type": "server",
  "status": "active",
  "ip_address": "192.168.1.10",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "metadata": {
    "location": "rack-1"
  }
}
```

**Required Fields**:
- `name` (string, 1-100 chars) - Unique device name
- `type` (string) - Device type (server, vm, container, network, storage)

**Optional Fields**:
- `status` (string) - Device status (default: "inactive")
- `ip_address` (string) - Primary IP address (IPv4 or IPv6)
- `mac_address` (string) - Primary MAC address (XX:XX:XX:XX:XX:XX format)
- `metadata` (object) - Additional key-value data

**Response** `201 Created`:
```json
{
  "id": 1,
  "name": "server-01",
  ...
}
```

**Errors**:
- `400` - Validation error (missing required fields or invalid format)
- `409` - Device with this name already exists

### Update Device

```http
PUT /api/devices/{device_id}
```

**Parameters**:
- `device_id` (path, integer, required) - Device ID

**Request Body** (all fields optional):
```json
{
  "name": "server-01-updated",
  "status": "maintenance",
  "metadata": {
    "location": "rack-2"
  }
}
```

**Response** `200 OK`:
```json
{
  "id": 1,
  "name": "server-01-updated",
  ...
}
```

**Errors**:
- `404` - Device not found
- `400` - Validation error

### Delete Device

```http
DELETE /api/devices/{device_id}
```

**Parameters**:
- `device_id` (path, integer, required) - Device ID

**Response** `200 OK`:
```json
{
  "message": "Device deleted successfully"
}
```

**Errors**:
- `404` - Device not found

**Note**: Deleting a device will cascade delete all associated network interfaces, services, and metrics.

### Get Device Services

```http
GET /api/devices/{device_id}/services
```

Returns all services running on the specified device.

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "device_id": 1,
    "name": "nginx",
    "port": 80,
    "protocol": "http",
    "status": "running",
    ...
  }
]
```

**Errors**:
- `404` - Device not found

### Get Device Metrics

```http
GET /api/devices/{device_id}/metrics?limit=100
```

Returns recent performance metrics for the specified device.

**Query Parameters**:
- `limit` (integer, optional, default: 100) - Maximum number of metrics to return

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "device_id": 1,
    "timestamp": "2026-01-12T10:00:00",
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 82.1,
    ...
  }
]
```

**Errors**:
- `404` - Device not found

---

## Network Interfaces

Network interfaces represent physical or virtual NICs attached to devices. Devices can have multiple interfaces for multi-homed configurations.

### Network Interface Object

```json
{
  "id": 1,
  "device_id": 1,
  "interface_name": "eth0",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.1.10",
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "vlan_id": 100,
  "is_primary": true,
  "status": "up"
}
```

### Interface Status

- `up` - Interface is active and operational
- `down` - Interface is down or disconnected
- `disabled` - Interface is administratively disabled

### List Device Interfaces

```http
GET /api/devices/{device_id}/interfaces
```

Returns all network interfaces for a device, ordered by primary status then name.

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "device_id": 1,
    "interface_name": "eth0",
    "is_primary": true,
    ...
  }
]
```

**Errors**:
- `404` - Device not found

### Get Device Interface

```http
GET /api/devices/{device_id}/interfaces/{interface_id}
```

**Response** `200 OK`:
```json
{
  "id": 1,
  "device_id": 1,
  ...
}
```

**Errors**:
- `404` - Interface not found

### Create Interface

```http
POST /api/devices/{device_id}/interfaces
```

**Request Body**:
```json
{
  "interface_name": "eth0",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.1.10",
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "vlan_id": 100,
  "status": "up",
  "is_primary": false
}
```

**Required Fields**:
- `interface_name` (string, 1-50 chars) - Interface name (e.g., eth0, wlan0)
- `mac_address` (string) - MAC address in XX:XX:XX:XX:XX:XX format

**Optional Fields**:
- `ip_address` (string) - IPv4 or IPv6 address
- `subnet_mask` (string) - Subnet mask
- `gateway` (string) - Gateway IP address
- `vlan_id` (integer, 1-4094) - VLAN ID for 802.1Q tagging
- `status` (string) - Interface status (default: "up")
- `is_primary` (boolean) - Whether this is the primary interface (default: false)

**Response** `201 Created`:
```json
{
  "id": 1,
  "device_id": 1,
  ...
}
```

**Errors**:
- `404` - Device not found
- `400` - Validation error (invalid MAC, IP, or VLAN ID)
- `409` - Interface with this MAC address already exists for this device

**Notes**:
- The first interface added to a device is automatically set as primary
- Only one interface per device can be primary
- MAC addresses are automatically converted to uppercase

### Update Interface

```http
PUT /api/devices/{device_id}/interfaces/{interface_id}
```

**Request Body** (all fields optional):
```json
{
  "ip_address": "192.168.1.20",
  "status": "down",
  "is_primary": true
}
```

**Response** `200 OK`:
```json
{
  "id": 1,
  ...
}
```

**Errors**:
- `404` - Interface not found
- `400` - Validation error
- `409` - MAC address conflict

### Delete Interface

```http
DELETE /api/devices/{device_id}/interfaces/{interface_id}
```

**Response** `200 OK`:
```json
{
  "message": "Interface deleted successfully"
}
```

**Errors**:
- `404` - Interface not found
- `400` - Cannot delete the only interface (devices must have at least one interface)

**Note**: If you delete the primary interface, another interface will automatically be promoted to primary.

### Set Primary Interface

```http
PUT /api/devices/{device_id}/interfaces/{interface_id}/set-primary
```

Designates the specified interface as the primary interface for the device.

**Response** `200 OK`:
```json
{
  "id": 1,
  "is_primary": true,
  ...
}
```

**Errors**:
- `404` - Interface not found

### Global Interface Queries

#### List All Interfaces

```http
GET /api/interfaces?device_id=1&status=up&is_primary=true
```

**Query Parameters** (all optional):
- `device_id` (integer) - Filter by device ID
- `status` (string) - Filter by status (up, down, disabled)
- `is_primary` (boolean) - Filter by primary status

#### Find by MAC Address

```http
GET /api/interfaces/by-mac/{mac_address}
```

**Example**: `/api/interfaces/by-mac/AA:BB:CC:DD:EE:FF`

#### Find by IP Address

```http
GET /api/interfaces/by-ip/{ip_address}
```

**Example**: `/api/interfaces/by-ip/192.168.1.10`

---

## Services

Services represent applications or daemons running on devices.

### Service Object

```json
{
  "id": 1,
  "device_id": 1,
  "name": "nginx",
  "port": 80,
  "protocol": "http",
  "status": "running",
  "health_check_url": "http://localhost:80/health"
}
```

### Service Status

- `running` - Service is active and running
- `stopped` - Service is stopped
- `error` - Service is in an error state

### List All Services

```http
GET /api/services
```

### Get Service

```http
GET /api/services/{service_id}
```

### Create Service

```http
POST /api/services
```

**Request Body**:
```json
{
  "device_id": 1,
  "name": "nginx",
  "port": 80,
  "protocol": "http",
  "status": "running",
  "health_check_url": "http://localhost:80/health"
}
```

**Required Fields**:
- `device_id` (integer) - ID of the device running this service
- `name` (string, 1-255 chars) - Service name

**Optional Fields**:
- `port` (integer, 1-65535) - Port number
- `protocol` (string, max 50 chars) - Protocol (http, https, tcp, etc.)
- `status` (string) - Service status (default: "stopped")
- `health_check_url` (string, max 500 chars) - Health check endpoint

**Response** `201 Created`

**Errors**:
- `404` - Device not found
- `400` - Validation error

### Update Service

```http
PUT /api/services/{service_id}
```

### Delete Service

```http
DELETE /api/services/{service_id}
```

### Update Service Status

```http
PUT /api/services/{service_id}/status
```

**Request Body**:
```json
{
  "status": "running"
}
```

---

## Metrics

Metrics represent system performance data collected from devices.

### Metric Object

```json
{
  "id": 1,
  "device_id": 1,
  "timestamp": "2026-01-12T10:00:00",
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 82.1,
  "network_rx_bytes": 1048576,
  "network_tx_bytes": 524288
}
```

### Submit Metrics

```http
POST /api/metrics
```

**Request Body**:
```json
{
  "device_id": 1,
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 82.1,
  "network_rx_bytes": 1048576,
  "network_tx_bytes": 524288
}
```

**Required Fields**:
- `device_id` (integer) - ID of the device

**Optional Fields** (all floats/integers):
- `cpu_usage` (float, 0-100) - CPU usage percentage
- `memory_usage` (float, 0-100) - Memory usage percentage
- `disk_usage` (float, 0-100) - Disk usage percentage
- `network_rx_bytes` (integer, ≥0) - Network received bytes
- `network_tx_bytes` (integer, ≥0) - Network transmitted bytes

**Response** `201 Created`

**Errors**:
- `404` - Device not found
- `400` - Validation error (percentages out of range or negative values)

---

## Automation

Trigger Ansible playbook executions for automated device configuration.

### Automation Job Object

```json
{
  "id": 1,
  "device_id": 1,
  "playbook_name": "configure_web_server",
  "status": "pending",
  "created_at": "2026-01-12T10:00:00"
}
```

### Job Status

- `pending` - Job is queued
- `running` - Job is currently executing
- `completed` - Job finished successfully
- `failed` - Job failed

### List Available Playbooks

```http
GET /api/automation/playbooks
```

Returns a list of available Ansible playbooks.

**Response** `200 OK`:
```json
[
  {
    "name": "ping",
    "description": "Simple connectivity test"
  },
  {
    "name": "system_info",
    "description": "Gather system information"
  }
]
```

### List Automation Jobs

```http
GET /api/automation/jobs?device_id=1
```

**Query Parameters** (all optional):
- `device_id` (integer) - Filter jobs by device ID

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "device_id": 1,
    "playbook_name": "ping",
    "status": "completed",
    "created_at": "2026-01-12T10:00:00"
  }
]
```

### Trigger Automation Job

```http
POST /api/automation
```

**Request Body**:
```json
{
  "device_id": 1,
  "playbook_name": "configure_web_server"
}
```

**Response** `201 Created`

### Get Job Status

```http
GET /api/automation/{job_id}
```

### Get Job Logs

```http
GET /api/automation/{job_id}/logs
```

**Response**:
```json
{
  "job_id": 1,
  "log_output": "Ansible playbook execution logs..."
}
```

---

## Rate Limiting

**Current Status**: Not implemented. No rate limiting is currently enforced.

**Planned**: Rate limiting will be added in future versions.

---

## Changelog

### Version 0.1.0 (2026-01-12)

- Initial API release
- Device management endpoints
- Multi-homed network interface support
- Service tracking endpoints
- Performance metrics collection
- Provisioning job triggering
- Comprehensive error handling with validation
- Transaction rollback on errors

---

## Support

For issues, questions, or contributions, please visit the GitHub repository.
