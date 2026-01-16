# Homelab Manager API Documentation

Version: 0.5.1
Base URL: `http://localhost:5000/api`

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [CLI Commands](#cli-commands)
- [Authentication](#authentication)
- [Response Format](#response-format)
- [Pagination](#pagination)
- [Error Handling](#error-handling)
- [Devices](#devices)
- [Network Interfaces](#network-interfaces)
- [Services](#services)
- [Metrics](#metrics)
- [Automation](#automation)
- [Device Variables](#device-variables)
- [Vault Secrets](#vault-secrets)
- [Workflows](#workflows)

---

## Overview

The Homelab Manager API provides comprehensive management of homelab infrastructure including devices, network interfaces, services, and performance metrics.

### Features

- **Centralized Device Management**: Track servers, VMs, containers, and network equipment
- **Multi-Homed Network Support**: Manage multiple network interfaces per device with MAC, IP, VLAN configuration
- **Service Monitoring**: Track running services with health checks and status
- **Performance Metrics**: Collect and query CPU, memory, disk, and network usage
- **Ansible Integration**: Trigger automation jobs for device configuration

### Interactive Documentation

Swagger UI is available at `http://localhost:5000/apidocs/` for interactive API exploration and testing.

### Request/Response Format

- All requests and responses use **JSON**
- Request body must include `Content-Type: application/json` header
- Timestamps are in ISO 8601 format
- All successful responses use a consistent envelope format (see [Response Format](#response-format))

---

## Getting Started

### Prerequisites

1. PostgreSQL database
2. Python 3.14+
3. Node.js 18+ (for frontend)

### Initial Setup

1. Clone the repository and install dependencies:
   ```bash
   cd backend
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

2. Configure environment variables in `backend/.env`

3. Initialize the database:
   ```bash
   alembic upgrade head
   ```

4. Create the initial admin user:
   ```bash
   flask create-admin
   ```

5. Start the backend:
   ```bash
   flask run
   ```

---

## CLI Commands

The backend provides CLI commands for administration tasks. Run from the `backend` directory with the virtual environment activated.

### Create Admin User

Create an initial administrator account:

```bash
# Interactive mode (prompts for all values)
flask create-admin

# With command-line options
flask create-admin --username admin --email admin@example.com
```

**Options:**
- `--username` - Admin username (prompted if not provided)
- `--email` - Admin email address (prompted if not provided)
- `--password` - Admin password (prompted securely if not provided)

**Example session:**
```
$ flask create-admin
Username: admin
Email: admin@homelab.local
Password: ********
Repeat for confirmation: ********
Admin user 'admin' created successfully!
  Username: admin
  Email: admin@homelab.local
  Admin: Yes
```

### List Users

Display all users in the system:

```bash
flask list-users
```

**Example output:**
```
ID    Username             Email                          Admin   Active
---------------------------------------------------------------------------
1     admin                admin@homelab.local            Yes     Yes
2     operator             operator@homelab.local         No      Yes

Total: 2 user(s)
```

### Reset Password

Reset a user's password from the command line:

```bash
# Interactive mode
flask reset-password --username admin

# The password is always prompted securely
```

---

## Authentication

All API endpoints (except `/health` and `/api/auth/login`) require JWT authentication.

### Security Features

- **HttpOnly Cookies**: JWT tokens are stored in HttpOnly cookies (not accessible to JavaScript) to prevent XSS attacks
- **CSRF Protection**: State-changing requests (POST, PUT, DELETE) require a CSRF token in the `X-CSRF-TOKEN` header
- **Secure Cookies**: In production, cookies are sent only over HTTPS
- **SameSite=Lax**: Cookies are not sent with cross-site requests to prevent CSRF

### Login

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "username": "admin",
  "password": "your-password"
}
```

**Response** `200 OK`:
```json
{
  "data": {
    "csrf_token": "abc123-csrf-token-xyz",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "display_name": "Admin User",
      "is_admin": true
    }
  }
}
```

The response also sets an HttpOnly cookie (`access_token`) containing the JWT.

**Errors:**
- `401` - Invalid credentials
- `429` - Too many login attempts (rate limited to 5/minute)

### Using Authentication

Authentication is handled automatically via cookies. For state-changing requests, include the CSRF token:

```http
X-CSRF-TOKEN: abc123-csrf-token-xyz
```

**Important:** The CSRF token is required for all POST, PUT, and DELETE requests.

### Logout

```http
POST /api/auth/logout
```

Clears the HttpOnly cookie and invalidates the session.

**Response** `200 OK`:
```json
{
  "data": {
    "message": "Logged out successfully"
  }
}
```

### Get Current User

```http
GET /api/auth/me
```

Returns the currently authenticated user's profile.

### Update Profile

```http
PUT /api/auth/me
```

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "display_name": "New Display Name",
  "bio": "A short bio",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

### Change Password

```http
PUT /api/auth/me/password
```

**Request Body:**
```json
{
  "current_password": "old-password",
  "new_password": "new-password"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### User Management (Admin Only)

#### List Users

```http
GET /api/auth/users
```

#### Create User

```http
POST /api/auth/users
```

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePass123",
  "display_name": "New User",
  "is_admin": false
}
```

#### Update User

```http
PUT /api/auth/users/{user_id}
```

#### Delete User

```http
DELETE /api/auth/users/{user_id}
```

#### Reset User Password

```http
POST /api/auth/users/{user_id}/reset-password
```

**Request Body:**
```json
{
  "new_password": "NewSecurePass123"
}
```

### Application Settings (Admin Only)

Manage system-wide configuration settings.

#### List Settings

```http
GET /api/auth/settings
```

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": 1,
      "key": "session_timeout_minutes",
      "value": "60",
      "description": "Session timeout in minutes (default: 60)",
      "updated_at": "2026-01-16T10:00:00"
    },
    {
      "id": 2,
      "key": "max_login_attempts",
      "value": "5",
      "description": "Maximum failed login attempts before lockout"
    },
    {
      "id": 3,
      "key": "lockout_duration_minutes",
      "value": "15",
      "description": "Account lockout duration in minutes"
    }
  ]
}
```

#### Update Setting

```http
PUT /api/auth/settings/{key}
```

**Request Body:**
```json
{
  "value": "120"
}
```

**Response** `200 OK`:
```json
{
  "data": {
    "key": "session_timeout_minutes",
    "value": "120",
    "updated_at": "2026-01-16T10:30:00"
  }
}
```

**Errors:**
- `400` - Invalid value
- `403` - Admin access required
- `404` - Setting not found

### Avatar Management

#### Upload Avatar

```http
POST /api/auth/me/avatar
Content-Type: multipart/form-data
```

**Request Body:**
- `avatar` (file, required) - Image file (JPEG, PNG, GIF, or WebP, max 5MB)

**Response** `200 OK`:
```json
{
  "data": {
    "avatar_url": "/uploads/avatars/abc123.jpg",
    "user": { ... }
  }
}
```

**Errors:**
- `400` - No file provided, invalid file type, or file too large

#### Delete Avatar

```http
DELETE /api/auth/me/avatar
```

**Response** `200 OK`:
```json
{
  "data": {
    "message": "Avatar deleted",
    "user": { ... }
  }
}
```

### Update Preferences

```http
PUT /api/auth/me/preferences
```

**Request Body:**
```json
{
  "theme": "dark",
  "notifications_enabled": true
}
```

Stores arbitrary JSON preferences for the user.

---

## Response Format

All API responses use a consistent JSON envelope format.

### Success Response

Single resource responses:
```json
{
  "data": {
    "id": 1,
    "name": "server-01",
    ...
  }
}
```

List responses (without pagination):
```json
{
  "data": [
    { "id": 1, "name": "server-01", ... },
    { "id": 2, "name": "server-02", ... }
  ]
}
```

Message-only responses:
```json
{
  "message": "Device deleted successfully"
}
```

### Paginated Response

List endpoints that support pagination return:
```json
{
  "data": [
    { "id": 1, ... },
    { "id": 2, ... }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Pagination

List endpoints support pagination via query parameters.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `per_page` | integer | 20 | Items per page (max: 100) |

### Example

```http
GET /api/devices?page=2&per_page=10
```

### Paginated Endpoints

The following endpoints support pagination:
- `GET /api/devices` - List devices
- `GET /api/services` - List services
- `GET /api/automation/jobs` - List automation jobs

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
| `401` | Unauthorized - Missing or invalid authentication token |
| `403` | Forbidden - Insufficient permissions for this action |
| `404` | Not Found - Resource does not exist |
| `409` | Conflict - Resource already exists or constraint violation |
| `429` | Too Many Requests - Rate limit exceeded |
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
GET /api/devices?page=1&per_page=20
```

**Query Parameters**:
- `page` (integer, optional, default: 1) - Page number
- `per_page` (integer, optional, default: 20, max: 100) - Items per page

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": 1,
      "name": "server-01",
      "type": "server",
      "status": "active",
      ...
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
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
  "data": {
    "id": 1,
    "name": "server-01",
    "type": "server",
    ...
  }
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
  "data": {
    "id": 1,
    "name": "server-01",
    ...
  }
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
  "data": {
    "id": 1,
    "name": "server-01-updated",
    ...
  }
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
{
  "data": [
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
}
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
{
  "data": [
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
}
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

Execute automation actions on devices using pluggable executor backends.

The automation system supports multiple executor types (Ansible, SSH, etc.) through a plugin architecture. Each executor provides its own set of actions that can be triggered on devices.

### Executor Types

- `ansible` - Execute Ansible playbooks for configuration management

### Automation Job Object

```json
{
  "id": 1,
  "device_id": 1,
  "device_ids": [1, 2, 3],
  "executor_type": "ansible",
  "action_name": "ping",
  "action_config": null,
  "extra_vars": {"key": "value"},
  "status": "running",
  "progress": 45,
  "task_count": 10,
  "tasks_completed": 4,
  "error_category": null,
  "cancel_requested": false,
  "celery_task_id": "abc123",
  "vault_secret_id": 1,
  "started_at": "2026-01-12T10:00:00",
  "completed_at": null,
  "log_output": null
}
```

### Job Status

- `pending` - Job is queued
- `running` - Job is currently executing
- `completed` - Job finished successfully
- `failed` - Job failed
- `cancelled` - Job was cancelled by user

### Error Categories

When a job fails, the `error_category` field indicates the type of failure:

- `connectivity` - Network/connection issues
- `permission` - Permission denied errors
- `timeout` - Execution timeout
- `authentication` - Auth failures
- `not_found` - Resource not found
- `execution` - General execution errors

### List Available Executors

```http
GET /api/automation/executors
```

Returns a list of registered executor types.

**Response** `200 OK`:
```json
[
  {
    "type": "ansible",
    "display_name": "Ansible",
    "description": "Execute Ansible playbooks for configuration management"
  }
]
```

### List Executor Actions

```http
GET /api/automation/executors/{executor_type}/actions
```

Returns available actions for a specific executor type.

**Parameters**:
- `executor_type` (path, string, required) - Executor type identifier

**Response** `200 OK`:
```json
[
  {
    "name": "ping",
    "display_name": "Ping",
    "description": "Simple connectivity test",
    "config_schema": {}
  },
  {
    "name": "system_info",
    "display_name": "System Info",
    "description": "Gather system information",
    "config_schema": {}
  }
]
```

**Errors**:
- `404` - Executor type not found

### List Automation Jobs

```http
GET /api/automation/jobs?device_id=1&executor_type=ansible
```

**Query Parameters** (all optional):
- `device_id` (integer) - Filter jobs by device ID
- `executor_type` (string) - Filter jobs by executor type

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "device_id": 1,
    "executor_type": "ansible",
    "action_name": "ping",
    "status": "completed",
    "started_at": "2026-01-12T10:00:00"
  }
]
```

### Trigger Automation Job

```http
POST /api/automation
```

Supports both single-device and multi-device execution modes.

**Request Body**:
```json
{
  "device_id": 1,
  "device_ids": [1, 2, 3],
  "executor_type": "ansible",
  "action_name": "docker_install",
  "action_config": null,
  "extra_vars": {
    "docker_version": "24.0",
    "install_compose": true
  },
  "vault_secret_id": 1
}
```

**Required Fields**:
- `action_name` (string) - Action to execute
- One of `device_id` or `device_ids` must be provided

**Optional Fields**:
- `device_id` (integer) - Single target device ID
- `device_ids` (array of integers) - Multiple target device IDs for parallel execution
- `executor_type` (string) - Executor type (default: "ansible")
- `action_config` (object) - Action-specific configuration
- `extra_vars` (object) - Variables to pass to the action (e.g., Ansible extra-vars)
- `vault_secret_id` (integer) - ID of vault secret for encrypted content

**Response** `201 Created`:
```json
{
  "data": {
    "id": 1,
    "device_id": 1,
    "device_ids": [1, 2, 3],
    "executor_type": "ansible",
    "action_name": "docker_install",
    "status": "pending",
    "progress": 0
  }
}
```

**Errors**:
- `400` - Validation error (invalid executor type, action, or device has no IP)
- `404` - Device or vault secret not found

### Get Action Schema

```http
GET /api/automation/executors/{executor_type}/actions/{action_name}/schema
```

Returns the JSON Schema for an action's variables.

**Response** `200 OK`:
```json
{
  "data": {
    "action_name": "docker_install",
    "schema": {
      "type": "object",
      "properties": {
        "docker_version": {
          "type": "string",
          "default": "latest"
        },
        "install_compose": {
          "type": "boolean",
          "default": true
        }
      }
    }
  }
}
```

### Get Job Status

```http
GET /api/automation/{job_id}
```

**Parameters**:
- `job_id` (path, integer, required) - Job ID

**Response** `200 OK`:
```json
{
  "id": 1,
  "device_id": 1,
  "executor_type": "ansible",
  "action_name": "ping",
  "status": "completed",
  "log_output": "STDOUT:\n..."
}
```

**Errors**:
- `404` - Job not found

### Get Job Logs

```http
GET /api/automation/{job_id}/logs
```

**Parameters**:
- `job_id` (path, integer, required) - Job ID

**Response** `200 OK`:
```json
{
  "data": {
    "job_id": 1,
    "log_output": "STDOUT:\nAnsible playbook execution logs...\n\nSTDERR:\n"
  }
}
```

**Errors**:
- `404` - Job not found

### Stream Job Logs (SSE)

```http
GET /api/automation/{job_id}/logs/stream?include_existing=true
```

Real-time log streaming via Server-Sent Events (SSE).

**Parameters**:
- `job_id` (path, integer, required) - Job ID
- `include_existing` (query, boolean, default: true) - Include existing logs before streaming

**Event Types**:
- `status` - Initial job status and progress
- `data` - Log line
- `complete` - Job finished
- `error` - Streaming error

**Example Usage** (JavaScript):
```javascript
const eventSource = new EventSource(`/api/automation/${jobId}/logs/stream`);
eventSource.onmessage = (event) => console.log(event.data);
eventSource.addEventListener('complete', () => eventSource.close());
```

### Cancel Job

```http
POST /api/automation/{job_id}/cancel
```

Request cancellation of a running or pending job.

**Parameters**:
- `job_id` (path, integer, required) - Job ID

**Response** `200 OK`:
```json
{
  "data": {
    "job_id": 1,
    "message": "Cancellation requested. Job will stop at next checkpoint.",
    "status": "cancellation_requested"
  }
}
```

**Errors**:
- `400` - Job cannot be cancelled (not running or pending)
- `404` - Job not found

**Note**: Pending jobs are cancelled immediately. Running jobs are cancelled at the next checkpoint (typically between Ansible tasks).

### Rerun Job

```http
POST /api/automation/{job_id}/rerun
```

Create a new job with the same parameters as the original.

**Parameters**:
- `job_id` (path, integer, required) - Original job ID

**Response** `201 Created`:
```json
{
  "data": {
    "id": 2,
    "original_job_id": 1,
    "device_id": 1,
    "action_name": "docker_install",
    "status": "pending"
  }
}
```

**Errors**:
- `404` - Original job not found

---

## Device Variables

Store default variables per device for automation actions.

### Get Device Variables

```http
GET /api/devices/{device_id}/variables
```

Returns all variables stored for a device.

**Response** `200 OK`:
```json
{
  "data": {
    "device_id": 1,
    "variables": [
      {
        "id": 1,
        "playbook_name": null,
        "variables": {"ansible_user": "admin"}
      },
      {
        "id": 2,
        "playbook_name": "docker_install",
        "variables": {"docker_version": "24.0"}
      }
    ]
  }
}
```

### Set Device Default Variables

```http
PUT /api/devices/{device_id}/variables
```

Set default variables that apply to all playbooks for this device.

**Request Body:**
```json
{
  "variables": {
    "ansible_user": "admin",
    "ansible_become": true
  }
}
```

### Get Playbook-Specific Variables

```http
GET /api/devices/{device_id}/variables/{playbook_name}
```

### Set Playbook-Specific Variables

```http
PUT /api/devices/{device_id}/variables/{playbook_name}
```

**Request Body:**
```json
{
  "variables": {
    "docker_version": "24.0",
    "install_compose": true
  }
}
```

### Delete Playbook Variables

```http
DELETE /api/devices/{device_id}/variables/{playbook_name}
```

---

## Vault Secrets

Securely store encrypted secrets (e.g., Ansible Vault passwords) for use in automation jobs.

### Vault Secret Object

```json
{
  "id": 1,
  "name": "production_vault",
  "description": "Vault password for production playbooks",
  "created_at": "2026-01-15T10:00:00",
  "updated_at": "2026-01-15T10:00:00"
}
```

**Note**: The encrypted content is never returned in API responses.

### List Vault Secrets

```http
GET /api/automation/vault/secrets
```

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": 1,
      "name": "production_vault",
      "description": "Vault password for production playbooks",
      "created_at": "2026-01-15T10:00:00"
    }
  ]
}
```

### Create Vault Secret

```http
POST /api/automation/vault/secrets
```

**Request Body**:
```json
{
  "name": "production_vault",
  "description": "Vault password for production playbooks",
  "content": "my-secret-vault-password"
}
```

**Required Fields**:
- `name` (string, 1-100 chars) - Unique identifier (alphanumeric, underscore, hyphen)
- `content` (string) - The secret content to encrypt

**Optional Fields**:
- `description` (string) - Human-readable description

**Response** `201 Created`:
```json
{
  "data": {
    "id": 1,
    "name": "production_vault",
    "description": "Vault password for production playbooks"
  }
}
```

**Errors**:
- `400` - Invalid name format or missing required fields
- `409` - Secret with this name already exists

### Get Vault Secret

```http
GET /api/automation/vault/secrets/{secret_id}
```

Returns secret metadata (never the encrypted content).

### Update Vault Secret

```http
PUT /api/automation/vault/secrets/{secret_id}
```

**Request Body**:
```json
{
  "description": "Updated description",
  "content": "new-secret-content"
}
```

Both fields are optional. Only provided fields are updated.

### Delete Vault Secret

```http
DELETE /api/automation/vault/secrets/{secret_id}
```

**Response** `200 OK`:
```json
{
  "data": {
    "message": "Secret 'production_vault' deleted"
  }
}
```

---

## Workflows

Workflows allow you to define and execute multi-step automation sequences with dependencies and rollback support.

### Workflow Template Object

```json
{
  "id": 1,
  "name": "Full Server Setup",
  "description": "Complete server provisioning workflow",
  "steps": [
    {
      "order": 0,
      "action_name": "ping",
      "executor_type": "ansible",
      "depends_on": [],
      "rollback_action": null,
      "extra_vars": {}
    },
    {
      "order": 1,
      "action_name": "docker_install",
      "executor_type": "ansible",
      "depends_on": [0],
      "rollback_action": "docker_uninstall",
      "extra_vars": {"docker_version": "24.0"}
    }
  ],
  "created_at": "2026-01-15T10:00:00",
  "updated_at": "2026-01-15T10:00:00"
}
```

### Workflow Instance Object

```json
{
  "id": 1,
  "template_id": 1,
  "template_name": "Full Server Setup",
  "status": "running",
  "device_ids": [1, 2],
  "rollback_on_failure": true,
  "extra_vars": {"environment": "production"},
  "started_at": "2026-01-15T10:00:00",
  "completed_at": null,
  "error_message": null,
  "jobs": [...]
}
```

### Workflow Status

- `pending` - Workflow is queued
- `running` - Workflow is executing
- `completed` - All steps completed successfully
- `failed` - A step failed (no rollback or rollback disabled)
- `cancelled` - Workflow was cancelled
- `rolling_back` - Running rollback actions
- `rolled_back` - Rollback completed successfully

### List Workflow Templates

```http
GET /api/workflows/templates?page=1&per_page=20
```

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Full Server Setup",
      "steps": [...],
      ...
    }
  ],
  "pagination": {...}
}
```

### Create Workflow Template

```http
POST /api/workflows/templates
```

**Request Body**:
```json
{
  "name": "Full Server Setup",
  "description": "Complete server provisioning workflow",
  "steps": [
    {
      "order": 0,
      "action_name": "ping",
      "executor_type": "ansible",
      "depends_on": [],
      "rollback_action": null
    },
    {
      "order": 1,
      "action_name": "docker_install",
      "executor_type": "ansible",
      "depends_on": [0],
      "rollback_action": "docker_uninstall"
    }
  ]
}
```

**Required Fields**:
- `name` (string, 1-100 chars) - Unique template name
- `steps` (array) - At least one step required

**Step Fields**:
- `order` (integer, required) - Unique step order (0-indexed)
- `action_name` (string, required) - Action to execute
- `executor_type` (string, default: "ansible") - Executor type
- `depends_on` (array of integers) - Step orders this step depends on
- `rollback_action` (string) - Action to run on rollback
- `extra_vars` (object) - Step-specific variables

**Response** `201 Created`

**Errors**:
- `400` - Validation error (duplicate orders, invalid dependencies)
- `409` - Template with this name already exists

### Get Workflow Template

```http
GET /api/workflows/templates/{template_id}
```

### Update Workflow Template

```http
PUT /api/workflows/templates/{template_id}
```

### Delete Workflow Template

```http
DELETE /api/workflows/templates/{template_id}
```

**Errors**:
- `400` - Cannot delete template with running instances
- `404` - Template not found

### Start Workflow

```http
POST /api/workflows
```

**Request Body**:
```json
{
  "template_id": 1,
  "device_ids": [1, 2, 3],
  "rollback_on_failure": true,
  "extra_vars": {"environment": "production"},
  "vault_secret_id": 1
}
```

**Required Fields**:
- `template_id` (integer) - ID of the workflow template
- `device_ids` (array of integers) - Target device IDs

**Optional Fields**:
- `rollback_on_failure` (boolean, default: false) - Run rollback actions if any step fails
- `extra_vars` (object) - Variables passed to all steps
- `vault_secret_id` (integer) - Vault secret for encrypted content

**Response** `201 Created`:
```json
{
  "data": {
    "id": 1,
    "template_id": 1,
    "status": "running",
    "device_ids": [1, 2, 3],
    "jobs": [
      {"id": 1, "step_order": 0, "status": "running", ...},
      {"id": 2, "step_order": 1, "status": "pending", ...}
    ]
  }
}
```

### List Workflow Instances

```http
GET /api/workflows?template_id=1&status=running&page=1&per_page=20
```

**Query Parameters**:
- `template_id` (integer) - Filter by template
- `status` (string) - Filter by status
- `page`, `per_page` - Pagination

### Get Workflow Instance

```http
GET /api/workflows/{instance_id}?include_jobs=true
```

**Query Parameters**:
- `include_jobs` (boolean, default: false) - Include job details

### Cancel Workflow

```http
POST /api/workflows/{instance_id}/cancel
```

Cancels a running workflow. Pending jobs are marked as cancelled, running jobs receive a cancellation request.

**Response** `200 OK`:
```json
{
  "data": {
    "id": 1,
    "status": "cancelled",
    "jobs": [...]
  }
}
```

**Errors**:
- `400` - Workflow cannot be cancelled (already completed/failed)
- `404` - Instance not found

---

## Rate Limiting

Rate limiting is enforced to protect the API from abuse.

### Default Limits

- **Global**: 200 requests per day, 50 requests per hour per IP
- **Login**: 5 attempts per minute (to prevent brute force attacks)

### Rate Limit Response

When you exceed the rate limit, you'll receive:

```http
HTTP/1.1 429 Too Many Requests
```

```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

---

## Changelog

For the complete version history, see [CHANGELOG.md](../CHANGELOG.md) in the project root.

---

## Support

For issues, questions, or contributions, please visit the GitHub repository.
