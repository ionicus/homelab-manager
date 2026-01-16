# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-01-16

### Added
- Configurable application settings (session timeout, login attempts, lockout duration)
- Admin-only endpoints for viewing and updating app settings (`GET/PUT /api/auth/settings`)
- Job rerun endpoint to re-execute failed/completed jobs (`POST /api/automation/{id}/rerun`)
- Device variables endpoints for per-device automation defaults
- Avatar upload/delete endpoints (`POST/DELETE /api/auth/me/avatar`)
- User preferences endpoint (`PUT /api/auth/me/preferences`)

### Changed
- Session timeout is now configurable via database settings

### Documentation
- Comprehensive API documentation updates

## [0.5.0] - 2026-01-15

### Added
- **Workflows**: Multi-step automation with dependencies and rollback support
- **Workflows**: Workflow templates for reusable automation sequences
- **Workflows**: Automatic rollback on failure (optional per-instance)
- **Workflows**: Step dependency management (steps wait for dependencies to complete)
- **Vault Secrets**: Encrypted storage for sensitive data (Ansible Vault passwords)
- **Vault Secrets**: Fernet symmetric encryption at rest
- **Multi-device**: Execute automation on multiple devices in parallel
- **Multi-device**: Dynamic inventory generation for multi-host playbooks
- **Variables**: Extra variables support for Ansible playbooks (`extra_vars`)
- **Variables**: JSON Schema support for playbook variable definitions
- **Variables**: Dynamic variable forms in frontend based on schemas
- **Execution**: Real-time log streaming via Server-Sent Events (SSE)
- **Execution**: Progress tracking with task count and percentage
- **Execution**: Job cancellation support (graceful termination)
- **Execution**: Error categorization (connectivity, permission, timeout, etc.)
- New `/api/workflows/*` endpoints for workflow management
- New `/api/automation/vault/secrets` endpoints for secret management
- Added `device_ids`, `extra_vars`, `vault_secret_id` to automation jobs
- SSE endpoint `/api/automation/{id}/logs/stream`
- Cancel endpoint `/api/automation/{id}/cancel`
- Frontend: Workflow builder UI for creating templates
- Frontend: Workflow execution and monitoring
- Frontend: Vault secret management
- Frontend: Multi-device selection for automation

## [0.4.1] - 2026-01-15

### Security
- JWT tokens now stored in HttpOnly cookies (XSS protection)
- CSRF protection for state-changing requests via `X-CSRF-TOKEN` header
- Rate limiting storage moved to Redis (persists across restarts)
- Avatar upload validates file signatures (magic bytes) in addition to MIME type
- Pillow decompression bomb protection (`MAX_IMAGE_PIXELS` limit)
- Secure temp files for Ansible inventory (restrictive permissions, random names)
- Sensitive data redaction in automation logs (passwords, API keys, private keys)
- Dedicated `AdminPasswordReset` schema (admin reset doesn't require current password)

### Changed
- Login response now returns `csrf_token` in response body
- `/auth/me` endpoint returns fresh `csrf_token` for session refresh after page reload

### Added
- `/auth/logout` endpoint to clear HttpOnly cookies
- Frontend: CSRF token stored in memory (not localStorage)
- Frontend: Session verification on page load retrieves fresh CSRF token

## [0.4.0] - 2026-01-14

### Added
- Celery background task queue for automation jobs
- Redis for task queue and result storage
- Standardized response envelope (`{"data": ...}` wrapper for all responses)
- Pagination support for list endpoints (devices, services, automation jobs)
- Pagination metadata includes `total`, `total_pages`, `has_next`, `has_prev`
- Automatic retry (3 attempts) for failed jobs
- 10-minute time limit per job

### Changed
- Jobs now execute in separate Celery worker process
- Worker survives web server restarts

### Added Files
- `celery_app.py`
- `tasks/automation.py`
- `worker.py`

## [0.3.0] - 2026-01-13

### Security
- Complete authentication system with JWT tokens
- User model with password hashing (Werkzeug)
- Role-based access control (admin/user roles)
- Rate limiting with Flask-Limiter
- CORS configuration (no more wildcard origins)
- Secrets required in production environment
- Fixed Ansible path traversal vulnerability
- Fixed Ansible inventory injection vulnerability
- Audit logging for security events

### Added
- CLI commands: `create-admin`, `list-users`, `reset-password`
- `/api/auth/*` endpoints for authentication
- User profile management
- Admin user management endpoints
- Frontend: Login page, protected routes, logout button
- Frontend: Profile and user management in Settings

## [0.2.0] - 2026-01-13

### Added
- Extensible automation framework with plugin architecture
- Executor registry for multiple automation backends
- `/api/automation/executors` endpoint to list available executors
- `/api/automation/executors/{type}/actions` endpoint to list executor actions
- `executor_type` filter to job listing endpoint

### Changed
- Database schema: renamed `playbook_name` to `action_name`
- Added `executor_type` and `action_config` fields

## [0.1.0] - 2026-01-12

### Added
- Initial API release
- Device management endpoints
- Multi-homed network interface support
- Service tracking endpoints
- Performance metrics collection
- Automation job triggering
- Comprehensive error handling with validation
- Transaction rollback on errors

[0.5.1]: https://github.com/ionicus/homelab-manager/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/ionicus/homelab-manager/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/ionicus/homelab-manager/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/ionicus/homelab-manager/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/ionicus/homelab-manager/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ionicus/homelab-manager/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ionicus/homelab-manager/releases/tag/v0.1.0
