# Deployment Guide

Comprehensive guide for deploying the Personal Finance Automation system to your homelab.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Quick Deployment](#quick-deployment)
- [Detailed Setup](#detailed-setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Docker Deployment](#docker-deployment)
- [n8n Workflow Setup](#n8n-workflow-setup)
- [Google Drive Integration](#google-drive-integration)
- [Nginx Reverse Proxy](#nginx-reverse-proxy)
- [HTTPS/TLS Configuration](#httpstls-configuration)
- [Backup Strategy](#backup-strategy)
- [Monitoring Setup](#monitoring-setup)
- [Production Hardening](#production-hardening)
- [Troubleshooting](#troubleshooting)
- [Upgrading](#upgrading)

## Prerequisites

### Hardware Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 2GB
- Storage: 20GB SSD
- Network: 100 Mbps

**Recommended:**
- CPU: 4 cores
- RAM: 4GB
- Storage: 50GB SSD
- Network: 1 Gbps

### Software Requirements

**Required:**
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- curl or wget

**Optional:**
- Nginx (for reverse proxy)
- Tailscale or WireGuard (for VPN access)
- Cloudflare account (for Tunnel)

### API Credentials

**Required:**
- **OpenAI API Key**: https://platform.openai.com/api-keys
- **Google Drive API Credentials**: https://console.cloud.google.com

**Optional:**
- Telegram Bot Token (for alerts)

### Network Requirements

- Ports available: 8080 (API), 5432 (PostgreSQL), 6379 (Redis), 5678 (n8n)
- Outbound HTTPS access for API calls
- Internal network for Docker services

## Deployment Options

### Option 1: Standard Docker Deployment (Recommended)

Best for most homelab setups.

```bash
make quickstart
```

**Pros:**
- Simple, one-command setup
- All services containerized
- Easy to maintain and upgrade
- Portable across systems

**Cons:**
- Requires Docker knowledge
- Some overhead compared to native

### Option 2: Local Development Mode

For development or testing without Docker.

```bash
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Pros:**
- Fast iteration
- Direct debugging
- No Docker overhead

**Cons:**
- Manual PostgreSQL setup required
- Not production-ready
- No service orchestration

### Option 3: Production with Nginx

Full production setup with reverse proxy.

```bash
make quickstart
# Then configure nginx (see section below)
```

**Pros:**
- HTTPS/TLS termination
- Rate limiting
- Static file serving
- Professional setup

**Cons:**
- More complex configuration
- Requires SSL certificates

## Quick Deployment

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/finance-automation.git
cd finance-automation/ops

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your values

# 3. Deploy everything
make quickstart

# 4. Verify deployment
make health

# 5. Access dashboard
open http://localhost:8080
```

### Verify Installation

```bash
# Check all services are running
docker compose ps

# Check API health
curl http://localhost:8080/health

# View logs
make logs

# Test database connection
docker compose exec postgres psql -U rody -d finance -c "SELECT 1;"
```

## Detailed Setup

### Step 1: Clone Repository

```bash
cd /path/to/your/homelab
git clone https://github.com/yourusername/finance-automation.git
cd finance-automation
```

### Step 2: Environment Configuration

```bash
cd ops
cp .env.example .env
```

**Edit .env with your settings:**

```bash
# Required - Database
POSTGRES_USER=rody
POSTGRES_PASSWORD=$(openssl rand -base64 32)  # Generate strong password
POSTGRES_DB=finance
DATABASE_URL=postgresql+psycopg2://rody:<YOUR_PASSWORD>@postgres:5432/finance

# Required - OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx  # From platform.openai.com
OPENAI_MODEL=gpt-4o-mini

# Required - Security
JWT_SECRET=$(openssl rand -base64 64)  # Generate random secret
ALLOWED_ORIGINS=http://localhost:8080

# Optional - Redis
REDIS_URL=redis://redis:6379/0

# Optional - Integrations
TELEGRAM_WEBHOOK_URL=https://api.telegram.org/botXXX/sendMessage

# Optional - Tuning
LOW_CONFIDENCE=0.80
REVIEW_AMOUNT_CENTS=5000
LOG_LEVEL=info
ENVIRONMENT=production
```

**Set proper permissions:**

```bash
chmod 600 .env
```

### Step 3: Build Docker Images

```bash
make build
```

This builds the FastAPI application image with all dependencies.

### Step 4: Start Services

```bash
make up
```

Services started:
- PostgreSQL 16 (port 5432)
- Redis 7 (port 6379)
- FastAPI API (port 8080)

### Step 5: Database Migrations

```bash
make migrate
```

This runs Alembic migrations to create all tables.

### Step 6: Seed Initial Data

```bash
make seed
```

Loads:
- Categorization rules (MCC mappings, regex patterns)
- Vendor aliases (canonical vendor names)

### Step 7: Verify Deployment

```bash
# Check service health
make health

# View logs
make logs

# Test API
curl http://localhost:8080/docs
```

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `rody` |
| `POSTGRES_PASSWORD` | Database password | `<strong-password>` |
| `POSTGRES_DB` | Database name | `finance` |
| `DATABASE_URL` | Full connection URL | `postgresql+psycopg2://...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-xxx` |
| `JWT_SECRET` | JWT signing secret | `<64-char-random>` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for categorization |
| `ALLOWED_ORIGINS` | `http://localhost:8080` | CORS origins |
| `LOW_CONFIDENCE` | `0.80` | Confidence threshold |
| `REVIEW_AMOUNT_CENTS` | `5000` | Amount threshold ($50) |
| `TELEGRAM_WEBHOOK_URL` | - | Telegram alerts |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `REDIS_PASSWORD` | - | Redis password |
| `LOG_LEVEL` | `info` | Logging level |
| `ENVIRONMENT` | `development` | Environment name |

### Generating Secrets

```bash
# PostgreSQL password
openssl rand -base64 32

# JWT secret (64 characters)
openssl rand -base64 64

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## Database Setup

### Automated Setup (Recommended)

```bash
# Complete database setup
make migrate  # Run migrations
make seed     # Load initial data
```

### Manual Setup

```bash
# 1. Access PostgreSQL container
docker compose exec postgres psql -U rody -d finance

# 2. Check tables
\dt

# 3. Check migration status
docker compose exec api alembic current

# 4. Manually run seed files
docker compose exec postgres psql -U rody -d finance < /app/seed/seed_rules.sql
docker compose exec postgres psql -U rody -d finance < /app/seed/seed_vendors.sql
```

### Database Schema

Tables created by migrations:

1. **transactions** - All financial transactions
2. **vendors** - Canonical vendor names and aliases
3. **rules** - Categorization rules
4. **reports** - Cached report data

Indexes:
- `transactions(txn_date)` - Date queries
- `transactions(canonical_vendor)` - Vendor grouping
- `transactions(category)` - Category filtering
- `transactions(hash_id)` - Deduplication (UNIQUE)

### Backup Configuration

```bash
# Manual backup
make backup

# Automated daily backups (add to crontab)
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * cd /path/to/finance-automation/ops && make backup

# Backup retention
# - Daily: 7 days
# - Weekly: 4 weeks
# - Monthly: 12 months
```

## Docker Deployment

### Service Overview

**docker-compose.yml includes:**

```yaml
services:
  postgres:    # PostgreSQL 16 Alpine
  redis:       # Redis 7 Alpine
  api:         # FastAPI application
  # n8n:       # (Optional) Workflow automation
```

### Volume Mounts

```yaml
volumes:
  postgres_data:  # PostgreSQL data persistence
  redis_data:     # Redis data persistence
```

### Network Configuration

```yaml
networks:
  finance-net:    # Internal bridge network
```

### Health Checks

All services include health checks:

- **PostgreSQL**: `pg_isready` every 10s
- **Redis**: `redis-cli ping` every 10s
- **API**: HTTP `/health` every 30s

### Resource Limits

Default resource limits:

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 1G
      reservations:
        memory: 512M
```

Adjust based on your hardware.

### Managing Services

```bash
# Start all services
make up

# Stop all services
make down

# Restart services
make restart

# View logs
make logs           # All services
make logs-api       # API only
make logs-db        # PostgreSQL only

# Check status
docker compose ps

# Check resource usage
docker stats
```

## n8n Workflow Setup

### Enable n8n Service

Uncomment in `docker-compose.yml`:

```yaml
n8n:
  image: n8nio/n8n:latest
  container_name: finance-n8n
  restart: unless-stopped
  ports:
    - "5678:5678"
  environment:
    - N8N_BASIC_AUTH_ACTIVE=true
    - N8N_BASIC_AUTH_USER=admin
    - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
  volumes:
    - ./n8n_data:/home/node/.n8n
  networks:
    - finance-net
```

```bash
# Add to .env
N8N_PASSWORD=$(openssl rand -base64 16)

# Restart to apply
make restart
```

### Import Workflows

1. Access n8n: http://localhost:5678
2. Login with credentials from .env
3. Click "Workflows" → "Import from File"
4. Import `n8n/workflows/drive_ingest.json`
5. Import `n8n/workflows/weekly_report.json`

### Configure Credentials

#### Google Drive API

1. Go to: https://console.cloud.google.com
2. Create new project: "Finance Automation"
3. Enable Google Drive API
4. Create OAuth 2.0 credentials
5. Add credentials to n8n

#### OpenAI API

1. In n8n, add "OpenAI" credential
2. Enter API key from OpenAI platform
3. Test connection

#### Webhook URL

Update webhook URLs in workflows to point to your API:

```
http://api:8080/api/ingest
```

### Activate Workflows

1. Open each workflow
2. Click "Activate" toggle
3. Test with sample file in Google Drive

## Google Drive Integration

### Create Google Cloud Project

```bash
# 1. Go to https://console.cloud.google.com
# 2. Create new project: "Finance Automation"
# 3. Enable Google Drive API
# 4. Create OAuth 2.0 Client ID credentials
# 5. Download credentials.json
```

### Configure OAuth Consent

1. Configure OAuth consent screen
2. Add scope: `https://www.googleapis.com/auth/drive.readonly`
3. Add test users (your email)

### Folder Structure

Create in Google Drive:

```
My Drive/
└── Finance/
    ├── Statements/          # Drop new statements here
    │   ├── 2025-10/
    │   │   ├── visa_statement.csv
    │   │   ├── amex_statement.pdf
    │   └── 2025-11/
    └── Receipts/            # Receipt images
        └── 2025-10/
```

### n8n Google Drive Trigger

Configure in workflow:

- **Folder**: `Finance/Statements`
- **Trigger**: "On file created"
- **File Types**: `.csv, .pdf, .ofx`
- **Polling Interval**: 1 minute

## Nginx Reverse Proxy

### Install Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# Or use Docker (recommended)
# Already configured in docker-compose.yml
```

### Configure nginx.conf

File: `ops/nginx.conf` (already created)

```nginx
upstream api_backend {
    server api:8080;
}

server {
    listen 80;
    server_name finance.local;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable Nginx in Docker Compose

Uncomment nginx service in `docker-compose.yml`.

### Test Configuration

```bash
# Test nginx config
docker compose exec nginx nginx -t

# Reload nginx
docker compose exec nginx nginx -s reload
```

## HTTPS/TLS Configuration

### Option 1: Let's Encrypt (Public Domain)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d finance.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Option 2: Self-Signed (Homelab)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout ops/ssl/key.pem \
  -out ops/ssl/cert.pem \
  -subj "/CN=finance.local"

# Update nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of config
}

# Mount in docker-compose.yml
volumes:
  - ./ssl:/etc/nginx/ssl:ro
```

### Option 3: Cloudflare Tunnel (Recommended for Remote Access)

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create finance

# Configure tunnel
nano ~/.cloudflared/config.yml

# Start tunnel
cloudflared tunnel run finance
```

**config.yml:**

```yaml
tunnel: <tunnel-id>
credentials-file: /home/user/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: finance.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

## Backup Strategy

### Automated Backups

**Add to crontab:**

```bash
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /path/to/finance-automation/ops && make backup

# Weekly backup on Sunday 3 AM
0 3 * * 0 cd /path/to/finance-automation/ops && make backup-weekly

# Monthly backup on 1st at 4 AM
0 4 1 * * cd /path/to/finance-automation/ops && make backup-monthly
```

### Backup Script

File: `ops/Makefile` (already includes backup target)

```makefile
backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	docker compose exec -T postgres pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) | \
		gzip > backups/finance_$(shell date +%Y%m%d_%H%M%S).sql.gz
```

### Backup Encryption

```bash
# Encrypted backup
make backup
gpg --encrypt --recipient your@email.com backups/finance_20251026.sql.gz

# Encrypted backup with age
brew install age
age -r <public-key> backups/finance_20251026.sql.gz > backups/finance_20251026.sql.gz.age
```

### Offsite Backups

**Option 1: rsync to remote server**

```bash
# Add to crontab after local backup
0 3 * * * rsync -avz /path/to/backups/ user@remote-server:/backups/finance/
```

**Option 2: S3/B2 Cloud Storage**

```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure rclone
rclone config

# Add to backup script
rclone copy backups/ remote:finance-backups/
```

### Restore Procedure

```bash
# List backups
ls -lh ops/backups/

# Restore from backup
make restore FILE=backups/finance_20251026_140530.sql.gz

# Or manually
gunzip -c backups/finance_20251026.sql.gz | \
  docker compose exec -T postgres psql -U rody -d finance
```

## Monitoring Setup

### Service Health Monitoring

```bash
# Built-in health checks
make health

# Continuous monitoring
watch -n 30 'make health'
```

### Log Aggregation

**Option 1: Local log files**

```bash
# Configure in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**Option 2: Centralized logging (Loki)**

```yaml
# Add to docker-compose.yml
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - ./loki-config.yaml:/etc/loki/local-config.yaml

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_AUTH_ANONYMOUS_ENABLED=true
```

### Application Metrics

**Add Prometheus metrics:**

```python
# api/app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

### Alerting

**Setup alerts for:**
- Service down
- Database connection failures
- High error rate (>1%)
- Disk space low (<10%)
- High memory usage (>80%)
- Failed backups

**Example: Simple email alerts**

```bash
# Add to monitoring script
#!/bin/bash
if ! make health > /dev/null 2>&1; then
    echo "Finance app health check failed!" | \
    mail -s "ALERT: Finance App Down" your@email.com
fi
```

## Production Hardening

### Security Checklist

- [x] Strong passwords for all services
- [x] JWT_SECRET is random 64+ characters
- [x] Services behind firewall/VPN
- [x] HTTPS/TLS enabled
- [x] CORS properly configured
- [x] Rate limiting enabled
- [x] Database user has minimal privileges
- [x] .env file permissions 600
- [x] Secrets not in Git
- [x] Security headers configured
- [x] Container vulnerability scanning
- [x] Regular security updates

### Performance Tuning

**PostgreSQL:**

```sql
-- Tune for your hardware
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';
```

**FastAPI:**

```python
# Use production ASGI server
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
```

### Firewall Rules

```bash
# Allow only Tailscale/VPN access
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow in on tailscale0
sudo ufw enable

# Or specific IP ranges
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

## Troubleshooting

### Services Won't Start

**Check logs:**

```bash
make logs
docker compose ps
```

**Common issues:**
- Port already in use → Change ports in docker-compose.yml
- Invalid .env → Check syntax and required variables
- Docker daemon not running → `sudo systemctl start docker`

### Database Connection Errors

```bash
# Test connection
docker compose exec postgres psql -U rody -d finance

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Verify PostgreSQL is running
docker compose ps postgres
```

### Migrations Failing

```bash
# Check current version
docker compose exec api alembic current

# Check migration history
docker compose exec api alembic history

# Manual migration
docker compose exec api alembic upgrade head

# Rollback
docker compose exec api alembic downgrade -1
```

### OpenAI API Errors

- Verify API key: https://platform.openai.com/api-keys
- Check quota: https://platform.openai.com/usage
- Test connection:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Increase resource limits in docker-compose.yml
# Or reduce concurrent connections
```

## Upgrading

### Application Updates

```bash
# 1. Backup first
make backup

# 2. Pull latest code
git pull origin main

# 3. Rebuild images
cd ops
make down
make build

# 4. Start with new images
make up

# 5. Run new migrations
make migrate

# 6. Verify
make health
```

### Database Migrations

```bash
# Automatic migration on upgrade
make migrate

# Or manually
docker compose exec api alembic upgrade head
```

### Rollback Procedure

```bash
# 1. Stop services
make down

# 2. Restore backup
make restore FILE=backups/finance_YYYYMMDD.sql.gz

# 3. Checkout previous version
git checkout <previous-commit>

# 4. Rebuild and start
make build
make up
```

---

**Deployment support:** For issues, check service logs with `make logs` and review the troubleshooting section.

**Next steps:** See [USAGE.md](USAGE.md) for user guide and [SECURITY.md](SECURITY.md) for security hardening.
