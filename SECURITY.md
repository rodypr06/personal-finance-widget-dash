# Security Documentation

This document outlines security considerations, best practices, and threat mitigation strategies for the Personal Finance Automation system.

## Table of Contents

- [Security Overview](#security-overview)
- [Threat Model](#threat-model)
- [Security Architecture](#security-architecture)
- [Data Protection](#data-protection)
- [Authentication & Authorization](#authentication--authorization)
- [Network Security](#network-security)
- [Container Security](#container-security)
- [Database Security](#database-security)
- [API Security](#api-security)
- [Secrets Management](#secrets-management)
- [Security Best Practices](#security-best-practices)
- [Monitoring & Incident Response](#monitoring--incident-response)
- [Compliance Considerations](#compliance-considerations)
- [Security Checklist](#security-checklist)
- [Reporting Vulnerabilities](#reporting-vulnerabilities)

## Security Overview

### Guiding Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal permissions for all components
3. **Privacy by Design**: Never store or log sensitive financial data
4. **Secure by Default**: Safe defaults requiring explicit relaxation
5. **Transparency**: Clear audit trails and logging
6. **Zero Trust**: Verify everything, trust nothing

### Security Posture

- **Deployment**: Private homelab behind VPN/Tailscale
- **Access**: JWT-authenticated API, no public exposure
- **Data**: Encrypted at rest and in transit
- **Secrets**: Environment-based, never committed to code
- **Updates**: Regular dependency security audits

## Threat Model

### Assets

1. **Financial Transaction Data** (HIGH VALUE)
   - Transaction amounts, dates, descriptions
   - Merchant information
   - Account identifiers (obfuscated)

2. **System Credentials** (CRITICAL)
   - Database passwords
   - API keys (OpenAI, Google Drive)
   - JWT secrets

3. **Personal Information** (HIGH VALUE)
   - Spending patterns
   - Financial habits
   - Bank account associations

### Threat Actors

1. **External Attackers**
   - Severity: Medium (behind VPN/firewall)
   - Goal: Data exfiltration, system compromise
   - Mitigation: Network isolation, authentication, rate limiting

2. **Compromised Dependencies**
   - Severity: Medium
   - Goal: Supply chain attack, backdoor
   - Mitigation: Dependency scanning, pinned versions, minimal dependencies

3. **Insider Threats**
   - Severity: Low (single-user homelab)
   - Goal: Data access, system manipulation
   - Mitigation: Audit logging, access controls

4. **Physical Access**
   - Severity: Low (homelab physical security)
   - Goal: Direct system access
   - Mitigation: Encryption at rest, secure boot

### Attack Vectors

| Vector | Risk | Mitigation |
|--------|------|------------|
| Network Exposure | Medium | VPN/Tailscale, firewall, HTTPS |
| SQL Injection | Medium | Parameterized queries, ORM |
| XSS | Low | Template escaping, CSP headers |
| Authentication Bypass | Medium | JWT verification, CORS |
| Secrets Exposure | High | Environment vars, .gitignore |
| Dependency Vulnerabilities | Medium | Regular scans, minimal deps |
| Data Exfiltration | High | Network isolation, encryption |
| Denial of Service | Low | Rate limiting, resource limits |

## Security Architecture

### Network Layers

```
┌─────────────────────────────────────────────────────┐
│           Internet (Untrusted)                      │
└─────────────────────┬───────────────────────────────┘
                      │
                      │ Blocked by firewall
                      │
┌─────────────────────▼───────────────────────────────┐
│           VPN/Tailscale (Optional)                  │
└─────────────────────┬───────────────────────────────┘
                      │
                      │ Authenticated users only
                      │
┌─────────────────────▼───────────────────────────────┐
│           Nginx Reverse Proxy (Optional)            │
│  - HTTPS/TLS termination                            │
│  - Rate limiting                                    │
│  - Security headers                                 │
└─────────────────────┬───────────────────────────────┘
                      │
                      │ Internal network
                      │
┌─────────────────────▼───────────────────────────────┐
│           FastAPI Application                       │
│  - JWT authentication                               │
│  - CORS protection                                  │
│  - Input validation                                 │
└─────────┬──────────────────────┬────────────────────┘
          │                      │
          │ Internal network     │ Internal network
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │
│ (encrypted vol) │    │   (optional)    │
└─────────────────┘    └─────────────────┘
```

### Trust Boundaries

1. **External → VPN**: Firewall, network isolation
2. **VPN → Nginx**: TLS encryption, authentication
3. **Nginx → API**: Internal network, JWT verification
4. **API → Database**: Connection encryption, least privilege
5. **API → External Services**: API key authentication

## Data Protection

### Sensitive Data Handling

#### NEVER Store

- ❌ Full credit card numbers (PAN)
- ❌ CVV/CVC codes
- ❌ Card expiration dates
- ❌ Bank account routing numbers
- ❌ SSN or government IDs
- ❌ Full passwords (only hashed)

#### Safe to Store

- ✅ Last 4 digits of card (masked)
- ✅ Obfuscated account identifiers (`visa_primary`)
- ✅ Transaction amounts
- ✅ Merchant names (after normalization)
- ✅ Transaction dates
- ✅ Categories and tags

### PAN Redaction

Automatic redaction of patterns resembling credit card numbers:

```python
# In logging and storage
PAN_PATTERN = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
redacted = re.sub(PAN_PATTERN, '[REDACTED]', text)
```

### Encryption

**At Rest:**
- PostgreSQL volume encryption (LUKS or filesystem-level)
- Environment files with restricted permissions (600)
- Backups encrypted with GPG or age

**In Transit:**
- HTTPS/TLS 1.3 for all external connections
- PostgreSQL SSL mode for database connections
- Internal Docker network isolation

## Authentication & Authorization

### JWT Authentication

**Write Operations** (POST, PUT, DELETE) require JWT:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Read Operations** (GET) are optionally authenticated based on configuration.

### JWT Configuration

```bash
# Generate strong secret (64+ characters)
JWT_SECRET=$(openssl rand -base64 64)

# Token lifetime
JWT_EXPIRATION=3600  # 1 hour
```

### API Key Security

**OpenAI API Key:**
- Stored in environment variable only
- Never logged or exposed in responses
- API key rotation every 90 days
- Usage monitoring for anomalies

**Google Drive API:**
- OAuth 2.0 credentials
- Scoped to read-only access on Statements folder
- Credentials stored in n8n encrypted storage

## Network Security

### Firewall Rules

**Recommended iptables configuration:**

```bash
# Allow SSH (adjust port)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow Tailscale
iptables -A INPUT -i tailscale0 -j ACCEPT

# Block all external access to application
iptables -A INPUT -p tcp --dport 8080 -j DROP
iptables -A INPUT -p tcp --dport 5432 -j DROP
iptables -A INPUT -p tcp --dport 6379 -j DROP

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
```

### CORS Configuration

Restrict allowed origins:

```bash
# .env
ALLOWED_ORIGINS=http://localhost:8080,https://finance.yourdomain.com
```

Never use `*` wildcard in production.

### Rate Limiting

**Nginx configuration:**

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    limit_req_status 429;
}
```

**Application-level** (optional):

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/ingest")
@limiter.limit("10/minute")
async def ingest_transaction():
    ...
```

## Container Security

### Non-Root User

All containers run as non-root:

```dockerfile
# Create user
RUN adduser -D -u 1000 appuser

# Switch to user
USER appuser
```

### Read-Only Filesystems

Mount sensitive directories read-only:

```yaml
# docker-compose.yml
volumes:
  - ./seed:/app/seed:ro
  - /proc:/host/proc:ro
```

### Resource Limits

Prevent resource exhaustion:

```yaml
# docker-compose.yml
api:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 1G
      reservations:
        memory: 512M
```

### Security Scanning

Regular container vulnerability scans:

```bash
# Scan base image
docker scan python:3.11-slim

# Scan built image
docker scan finance-api:latest

# Trivy scan
trivy image finance-api:latest
```

## Database Security

### PostgreSQL Security

**Connection Security:**

```bash
# .env - Always use SSL in production
DATABASE_URL=postgresql+psycopg2://user:pass@postgres:5432/finance?sslmode=require
```

**User Permissions:**

```sql
-- Application user with minimal privileges
CREATE USER finance_app WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE finance TO finance_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO finance_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO finance_app;

-- Revoke dangerous privileges
REVOKE CREATE ON SCHEMA public FROM finance_app;
REVOKE DELETE ON transactions FROM finance_app;  -- Optional: prevent deletion
```

**Encryption:**

```bash
# Enable volume encryption (LUKS)
cryptsetup luksFormat /dev/sdX
cryptsetup open /dev/sdX postgres_encrypted
mkfs.ext4 /dev/mapper/postgres_encrypted
```

### Backup Security

```bash
# Encrypted backups with GPG
pg_dump finance | gzip | gpg --encrypt --recipient your@email.com > backup.sql.gz.gpg

# Restore
gpg --decrypt backup.sql.gz.gpg | gunzip | psql finance
```

**Backup retention:**
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

**Offsite storage:**
- Encrypted backups to S3/Backblaze B2
- Or encrypted rsync to remote server

## API Security

### Input Validation

**Pydantic schemas** enforce strict validation:

```python
class TxnIn(BaseModel):
    txn_date: date
    amount_cents: int = Field(gt=0, lt=1_000_000_00)  # Max $1M
    currency: str = Field(regex=r'^[A-Z]{3}$')
    direction: Literal['debit', 'credit']
    raw_descriptor: str = Field(max_length=255)
    # ... more fields
```

### SQL Injection Prevention

**SQLAlchemy ORM** with parameterized queries:

```python
# Safe - parameterized
stmt = select(Transaction).where(Transaction.id == txn_id)

# Never build queries with string concatenation
# UNSAFE: f"SELECT * FROM transactions WHERE id = {txn_id}"
```

### XSS Prevention

**Jinja2 auto-escaping** enabled by default:

```python
# config.py
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(
    directory="app/templates",
    autoescape=True  # Auto-escape all variables
)
```

**Content Security Policy:**

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
```

### HTTPS Enforcement

**Nginx configuration:**

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Modern TLS only
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

## Secrets Management

### Environment Variables

**Never commit secrets to Git:**

```bash
# .gitignore
.env
.env.*
!.env.example
*.pem
*.key
credentials.json
```

**Use .env for all secrets:**

```bash
# ops/.env (restricted to 600 permissions)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)
OPENAI_API_KEY=sk-proj-xxxxx
```

**Set proper permissions:**

```bash
chmod 600 ops/.env
```

### Secret Rotation

**Schedule:**
- JWT_SECRET: Every 6 months
- POSTGRES_PASSWORD: Every 12 months
- OPENAI_API_KEY: Every 90 days
- Backup encryption keys: Every 12 months

**Rotation procedure:**

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 64)

# 2. Update .env
sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$NEW_SECRET/" .env

# 3. Restart services
make restart

# 4. Invalidate old tokens (if applicable)
```

## Security Best Practices

### Deployment

1. **Use Tailscale or VPN** for private network access
2. **Enable firewall** to block external access
3. **Set up HTTPS/TLS** via nginx or Cloudflare Tunnel
4. **Configure strong passwords** for all services
5. **Enable audit logging** for all write operations
6. **Set up automated backups** with encryption
7. **Regular security updates** for all dependencies
8. **Monitor for anomalies** in access patterns

### Development

1. **Never commit secrets** to version control
2. **Use type hints** to catch security bugs early
3. **Validate all inputs** with Pydantic schemas
4. **Escape all outputs** in templates
5. **Use parameterized queries** exclusively
6. **Run security linters** (bandit, safety)
7. **Dependency scanning** with pip-audit or Snyk
8. **Code review** for security implications

### Operations

1. **Principle of least privilege** for all accounts
2. **Regular backups** with tested restore procedures
3. **Monitor logs** for suspicious activity
4. **Keep systems updated** with security patches
5. **Incident response plan** documented
6. **Regular security audits** of configuration
7. **Network segmentation** between services
8. **Encrypted communication** for all external APIs

## Monitoring & Incident Response

### Security Logging

**Log all security events:**

```python
import logging

security_logger = logging.getLogger("security")

@app.post("/api/ingest")
async def ingest(txn: TxnIn, user: User = Depends(get_current_user)):
    security_logger.info(
        "transaction_ingest",
        extra={
            "user_id": user.id,
            "source_account": txn.source_account,
            "amount_cents": txn.amount_cents,
            "ip": request.client.host
        }
    )
```

**Never log sensitive data:**

```python
# UNSAFE - logs PAN
logger.info(f"Processing card: {raw_descriptor}")

# SAFE - redacts PAN
logger.info(f"Processing card: {redact_pan(raw_descriptor)}")
```

### Anomaly Detection

Monitor for:
- Failed authentication attempts (>5 in 10 minutes)
- Unusual API access patterns
- Database connection failures
- Large data exports
- Configuration changes
- New vendor transactions >$100

### Incident Response Plan

**Detection → Containment → Eradication → Recovery → Lessons Learned**

1. **Detection**: Automated alerts or manual discovery
2. **Containment**:
   - Isolate affected systems
   - Block suspicious IPs
   - Revoke compromised credentials
3. **Eradication**:
   - Patch vulnerabilities
   - Remove backdoors
   - Reset all secrets
4. **Recovery**:
   - Restore from clean backups
   - Verify system integrity
   - Monitor for persistence
5. **Post-mortem**:
   - Document incident
   - Update procedures
   - Implement preventive controls

## Compliance Considerations

### PCI DSS (Payment Card Industry)

While this system doesn't process payments, consider these principles:

- ✅ Never store full PAN
- ✅ Encrypt data at rest and in transit
- ✅ Strong access controls
- ✅ Regular security testing
- ✅ Audit trails for all access

### GDPR (if applicable)

Personal data handling considerations:

- **Right to be forgotten**: Implement transaction deletion
- **Data minimization**: Only store necessary data
- **Encryption**: Protect personal data
- **Breach notification**: 72-hour reporting procedures
- **Data portability**: Export capability

## Security Checklist

### Initial Deployment

- [ ] Strong, unique passwords for all services
- [ ] JWT_SECRET is random 64+ characters
- [ ] OPENAI_API_KEY properly secured
- [ ] ALLOWED_ORIGINS configured (no wildcards)
- [ ] Firewall rules in place
- [ ] Services behind VPN/Tailscale
- [ ] HTTPS/TLS enabled
- [ ] .env file permissions set to 600
- [ ] .gitignore includes .env and secrets
- [ ] Database user has minimal privileges
- [ ] Automated backups configured
- [ ] Backup encryption tested
- [ ] Security headers configured in nginx
- [ ] Rate limiting enabled
- [ ] CORS properly restricted

### Ongoing

- [ ] Security updates applied monthly
- [ ] Dependency scanning weekly (pip-audit)
- [ ] Container image scanning before deploy
- [ ] Backup restore tested quarterly
- [ ] Access logs reviewed monthly
- [ ] Secrets rotated per schedule
- [ ] Audit trail reviewed for anomalies
- [ ] Incident response plan tested annually

### Pre-Production

- [ ] Penetration testing completed
- [ ] Security code review performed
- [ ] All FIXME/TODO security items resolved
- [ ] Documentation updated
- [ ] Disaster recovery plan documented
- [ ] Monitoring and alerting configured
- [ ] Emergency contacts established

## Reporting Vulnerabilities

### Contact

For security vulnerabilities, please report privately:

- **Email**: security@yourdomain.com
- **PGP Key**: [Your PGP key fingerprint]
- **Response Time**: 48 hours

### Please Provide

- Detailed description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested remediation (if any)
- Your contact information (optional)

### What to Expect

1. **Acknowledgment** within 48 hours
2. **Assessment** of severity and impact
3. **Remediation** plan with timeline
4. **Testing** of fix in isolated environment
5. **Deployment** of security patch
6. **Disclosure** coordination (if public disclosure planned)

### Responsible Disclosure

We appreciate responsible disclosure and will:

- Acknowledge your contribution
- Keep you informed of remediation progress
- Credit you in security advisories (if desired)
- Not pursue legal action for good-faith reports

---

**Security is a continuous process, not a one-time setup.**

Regularly review and update security measures as threats evolve.

**Last Updated**: October 26, 2025
