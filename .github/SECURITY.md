# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Homelab Manager, please report it responsibly.

### How to Report

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email the maintainer directly or use GitHub's private vulnerability reporting feature
3. Include a detailed description of the vulnerability and steps to reproduce

### What to Expect

- Acknowledgment within 48 hours
- Regular updates on progress
- Credit in the fix announcement (if desired)

### Scope

This policy applies to:
- The Homelab Manager application (frontend and backend)
- Configuration and deployment scripts
- Documentation that could lead to security issues

### Out of Scope

- Vulnerabilities in third-party dependencies (report to upstream)
- Issues in user-deployed environments due to misconfiguration

## Supported Versions

| Version | Supported |
| ------- | --------- |
| main    | Yes       |

## Security Best Practices

When deploying Homelab Manager:
- Use HTTPS in production (required for secure cookies)
- Keep dependencies updated
- Store credentials in environment variables, never in code
- Restrict network access to trusted hosts
- Set strong, unique values for `SECRET_KEY` and `JWT_SECRET_KEY` (min 32 characters)
- Configure `CORS_ORIGINS` to list only your trusted frontend origins

## Security Features

### Authentication
- **HttpOnly Cookies**: JWT tokens are stored in HttpOnly cookies, preventing XSS attacks from stealing tokens
- **CSRF Protection**: State-changing requests require a CSRF token in the `X-CSRF-TOKEN` header
- **Secure Cookies**: In production (`FLASK_ENV=production`), cookies are only sent over HTTPS
- **SameSite=Lax**: Cookies are not sent with cross-site requests

### Input Validation
- **Pydantic Schemas**: All API inputs are validated with strict schemas
- **Path Traversal Prevention**: Ansible playbook names are validated against `^[a-zA-Z0-9_-]+$`
- **IP Address Validation**: Device IPs are validated using Python's `ipaddress` module
- **Inventory Sanitization**: Special characters are stripped from Ansible inventory values

### File Uploads
- **Magic Byte Validation**: Avatar uploads are validated by file signature, not just MIME type
- **Decompression Bomb Protection**: PIL `MAX_IMAGE_PIXELS` limit prevents memory exhaustion
- **Size Limits**: Maximum 5MB for avatar uploads

### Rate Limiting
- **Login Protection**: 5 attempts per minute to prevent brute force attacks
- **API Limits**: 200 requests/day, 50 requests/hour per IP
- **Redis Backend**: Rate limits persist across server restarts

### Sensitive Data
- **Log Redaction**: Passwords, API keys, and private keys are automatically redacted from automation logs
- **No Default Secrets**: Production deployments require explicitly set secrets
