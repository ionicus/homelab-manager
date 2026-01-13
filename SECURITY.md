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
- Use HTTPS in production
- Keep dependencies updated
- Store credentials in environment variables, never in code
- Restrict network access to trusted hosts
