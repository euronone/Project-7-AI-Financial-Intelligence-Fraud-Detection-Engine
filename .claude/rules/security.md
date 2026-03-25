# Auto-sync metadata (source: CLAUDE.md, updated 2026-03-24T06:21:20Z)

**Source:** CLAUDE.md

he chunk size as much as # Security Rules - FinShield AI

Apply these rules to all sensitive changes.

## Input Handling
- Treat all external input as untrusted.
- Validate and sanitize with Pydantic v2.
- Validate file uploads: MIME types, size, content.
- Apply input length limits.
- Sanitize HTML/markdown content.
- Implement fraud detection input validation.
- Use parameterized queries.

## Authentication
- Use JWT tokens 15-min expiration.
- Implement RBAC: admin, analyst, viewer.
- Apply least-privilege access.
- Validate permissions with tenant isolation.
- Never trust client-side role checks.
- Support SSO integration.
- Enforce MFA for admin accounts.

## Data Protection
- Encrypt sensitive data at rest AES-256.
- Encrypt data in transit TLS 1.3.
- Encrypt stored credentials AES-256.
- Never log PII, credentials.
- Implement ISO 27001 controls.
- Support SOC 2 Type II.
- Follow PCI-DSS standards.
- Implement GDPR compliance.
- Support data residency.
- Maintain audit trails.

## Multi-tenancy
- Implement RLS for tenant isolation.
- Validate tenant context.
- Use tenant-specific encryption keys.
- Prevent cross-tenant data access.
- Implement tenant-specific rate limiting.
- Support custom schema isolation.

## ML Security
- Secure model artifacts encryption.
- Implement model versioning.
- Protect against adversarial attacks.
- Use secure model serving.
- Monitor for model poisoning.
- Implement model explainability.
- Validate ML inputs.

## API Security
- Rate limit all endpoints.
- Use HTTPS everywhere.
- Implement CORS correctly.
- Validate request schemas.
- Add security headers.
- Implement API key rotation.
- Use request/response encryption.
- Apply circuit breakers.

## Infrastructure
- Avoid unsafe shell execution.
- Keep credentials in secrets manager.
- Encrypt data at rest and transit.
- Apply rate limiting.
- Use circuit breakers.
- Implement DDoS protection.
- Use VPN for internal communication.
- Secure WebSocket connections.

## Incident Response
- Flag changes impacting auth, payments, PII.
- Log security events with severity levels.
- Never expose stack traces.
- Implement real-time monitoring.
- Set up automated alerts.
- Maintain incident response playbooks.
- Implement breach notification.
- Regular security training.
- Penetration testing.
- Monitor fraud system bypass.
