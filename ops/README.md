# Operations & Deployment Guide

This directory contains all Docker, deployment, and operations configuration for the Personal Finance Automation system.

## Quick Start

```bash
# 1. Copy environment file and configure
cp .env.example .env
# Edit .env with your actual values

# 2. Complete setup (init, start, migrate, seed)
make quickstart

# 3. Access the application
open http://localhost:8080
```

## Files Overview

### Docker Configuration
- **docker-compose.yml** - Multi-service orchestration (PostgreSQL, Redis, API)
- **Dockerfile** - Multi-stage build for FastAPI application
- **.dockerignore** - Files excluded from Docker build context

### Operations
- **Makefile** - Automation commands for development and deployment
- **.env.example** - Template for environment variables
- **nginx.conf** - Optional reverse proxy configuration

## Makefile Commands

### Setup & Initialization
```bash
make init          # Create venv, install dependencies
make quickstart    # Complete setup: init + up + migrate + seed
```

### Docker Operations
```bash
make build         # Build Docker images
make up            # Start all services
make down          # Stop all services
make restart       # Restart all services
make health        # Check service health status
```

### Database Management
```bash
make migrate       # Run Alembic migrations
make seed          # Seed initial data (rules & vendors)
make backup        # Backup PostgreSQL database
make restore FILE=backups/finance_20250124.sql.gz  # Restore from backup
```

### Development
```bash
make logs          # Tail all service logs
make logs-api      # Tail API logs only
make logs-db       # Tail PostgreSQL logs only
make test          # Run pytest tests
make format        # Format code with ruff + black
make lint          # Lint code with ruff
```

### Maintenance
```bash
make clean         # Remove containers, volumes, cache (DESTRUCTIVE!)
make help          # Show all available commands
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

### Required Variables
```bash
# Database
POSTGRES_USER=rody
POSTGRES_PASSWORD=<your-secure-password>
POSTGRES_DB=finance
DATABASE_URL=postgresql+psycopg2://rody:<password>@postgres:5432/finance

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

# Security
JWT_SECRET=<generate-random-secret>
ALLOWED_ORIGINS=http://localhost:8080,https://finance.local
```

### Optional Variables
```bash
# Redis
REDIS_PASSWORD=<optional-password>
REDIS_URL=redis://redis:6379/0

# Integrations
TELEGRAM_WEBHOOK_URL=<optional>

# Application
LOG_LEVEL=info
ENVIRONMENT=production
```

## Service Architecture

### Services
1. **postgres:16-alpine** - PostgreSQL database with persistent storage
2. **redis:7-alpine** - Redis cache (optional, for session/caching)
3. **api** - FastAPI application with health checks
4. **n8n** - Workflow automation (optional, commented out by default)

### Networks
- **finance-net** - Bridge network for inter-service communication

### Volumes
- **postgres_data** - PostgreSQL data persistence
- **redis_data** - Redis data persistence

### Health Checks
All services include health checks for reliable startup sequencing:
- PostgreSQL: `pg_isready` check every 10s
- Redis: `redis-cli ping` every 10s
- API: HTTP check on `/health` endpoint every 30s

## Port Mappings

| Service    | Internal Port | External Port |
|------------|---------------|---------------|
| API        | 8080          | 8080          |
| PostgreSQL | 5432          | 5432          |
| Redis      | 6379          | 6379          |
| n8n        | 5678          | 5678 (optional) |

## Docker Image Details

### Multi-stage Build
The Dockerfile uses a two-stage build for optimal size and security:

**Stage 1: Builder**
- Base: `python:3.11-slim`
- Installs build dependencies (gcc, g++, libpq-dev)
- Creates virtual environment with all Python dependencies
- Result: ~500MB intermediate image (discarded)

**Stage 2: Production**
- Base: `python:3.11-slim`
- Runtime dependencies only (libpq5, curl)
- Non-root user (`appuser:1000`)
- Health check built-in
- Final size: ~200-250MB

### Security Features
- Non-root user execution
- Read-only system mounts
- Minimal attack surface
- No development dependencies
- Environment-based configuration

## Nginx Reverse Proxy (Optional)

If you want to add nginx as a reverse proxy:

### Add to docker-compose.yml
```yaml
nginx:
  image: nginx:alpine
  container_name: finance-nginx
  restart: unless-stopped
  ports:
    - "80:80"
    # - "443:443"  # Uncomment for HTTPS
  volumes:
    - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    # - ./ssl:/etc/nginx/ssl:ro  # SSL certificates
  networks:
    - finance-net
  depends_on:
    - api
```

### Features
- HTTP/HTTPS support
- WebSocket proxying
- Gzip compression
- Security headers
- Static file serving
- Rate limiting (configurable)

## Backup & Restore

### Automated Backups
```bash
# Manual backup
make backup

# Cron job example (daily at 2 AM)
0 2 * * * cd /path/to/ops && make backup
```

### Restore Process
```bash
# List available backups
ls -lh backups/

# Restore specific backup
make restore FILE=backups/finance_20250124_140530.sql.gz
```

## Production Deployment

### Pre-deployment Checklist
- [ ] Configure strong `JWT_SECRET`
- [ ] Set secure database password
- [ ] Configure `ALLOWED_ORIGINS` for your domain
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `LOG_LEVEL=warning` or `error`
- [ ] Configure Redis password
- [ ] Set up SSL certificates (if using nginx)
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Configure monitoring/alerts

### Recommended Settings
```bash
# Production .env additions
ENVIRONMENT=production
LOG_LEVEL=warning
JWT_SECRET=<64-character-random-string>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
ALLOWED_ORIGINS=https://your-domain.com
```

### Monitoring
```bash
# Check service status
make health

# Watch logs
make logs

# Check resource usage
docker stats
```

## Troubleshooting

### Services won't start
```bash
# Check logs
make logs

# Verify environment
cat .env | grep -v PASSWORD

# Check service health
docker compose ps
```

### Database connection errors
```bash
# Test database connection
docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Check database logs
make logs-db
```

### API health check failing
```bash
# Check API logs
make logs-api

# Manual health check
curl http://localhost:8080/health

# Restart API
docker compose restart api
```

### Port already in use
```bash
# Find process using port
lsof -i :8080

# Use different ports in docker-compose.yml
# Change: "8081:8080" for example
```

## Development Workflow

```bash
# 1. Start services
make up

# 2. Watch logs
make logs-api

# 3. Run migrations
make migrate

# 4. Seed data
make seed

# 5. Make code changes
# ... edit files in ../api/app/ ...

# 6. Test changes
make test

# 7. Format code
make format

# 8. Restart API to reload
docker compose restart api
```

## Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Docker Compose: https://docs.docker.com/compose/
- PostgreSQL: https://www.postgresql.org/docs/
- Alembic: https://alembic.sqlalchemy.org/

## Support

For issues or questions:
1. Check service logs: `make logs`
2. Verify health: `make health`
3. Review environment: `.env` configuration
4. Consult main project README: `../README.md`
