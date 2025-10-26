# Personal Finance Automation System

![License](https://img.shields.io/badge/license-Private-red)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)

A modern, sleek homelab-hosted personal finance automation system with glassmorphic UI. Automatically ingests bank statements from Google Drive, categorizes transactions using AI, and provides beautiful insights into your spending patterns.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

This system automates the tedious process of tracking personal finances by:

1. **Monitoring** Google Drive for new bank statements (CSV, PDF, OFX)
2. **Parsing** transactions and normalizing vendor names
3. **Categorizing** using deterministic rules (70%) and AI fallback (30%)
4. **Storing** in PostgreSQL with deduplication
5. **Visualizing** in a beautiful glassmorphic dashboard
6. **Alerting** on anomalies, new vendors, and spending patterns

All running privately in your homelab with enterprise-grade security.

## Features

### Core Functionality

- **🔄 Automated Ingestion**: Drop statements in Google Drive, see them in your dashboard within 2 minutes
- **🤖 Smart Categorization**:
  - Deterministic rules handle 70%+ of transactions
  - OpenAI GPT-4o-mini handles edge cases with confidence scoring
  - Manual review queue for low-confidence or high-value items
- **🏪 Vendor Normalization**: "STARBUCKS 1234" → "Starbucks" with canonical names
- **🔗 Receipt Linking**: Automatic matching of receipts from Google Drive
- **📊 Rich Reports**: Monthly/weekly summaries with category trends and top vendors
- **🚨 Anomaly Detection**: Z-score analysis, spending spikes, duplicate alerts
- **💳 Multi-Account Support**: Track multiple credit cards and bank accounts

### Dashboard Features

- **Glassmorphic UI**: Modern liquid glass design with blue/purple gradient
- **Real-time Updates**: Live transaction feed as statements are processed
- **Category Breakdown**: Interactive donut charts and treemaps
- **Spending Trends**: Historical charts with configurable time ranges
- **Top Vendors**: See where your money actually goes
- **Search & Filter**: Find transactions by vendor, category, date, amount

### Technical Features

- **Deduplication**: SHA-256 hash-based duplicate prevention
- **Idempotent Ingestion**: Safe to re-upload statements
- **Transaction History**: Full audit trail with status tracking
- **Extensible Rules Engine**: JSON-based rules with priority ordering
- **RESTful API**: Well-documented endpoints for integrations
- **Containerized**: Docker Compose for easy deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Google Drive                              │
│                   (Statements/ folder)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ Watch for new files
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                          n8n Workflows                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ CSV Parser   │  │ PDF Extractor│  │ OFX Parser   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ POST /api/ingest
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Ingestion → Normalization → Categorization → Storage   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐         ┌──────────────┐                       │
│  │ Rules Engine│ ──70%──▶│ PostgreSQL   │                       │
│  └─────────────┘         └──────────────┘                       │
│         │                                                        │
│         │ 30% fallback                                           │
│         ▼                                                        │
│  ┌─────────────┐         ┌──────────────┐                       │
│  │ OpenAI GPT  │         │    Redis     │                       │
│  │  Categorizer│         │   (Cache)    │                       │
│  └─────────────┘         └──────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Serve UI & API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Glassmorphic Dashboard                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Overview │  │ Trends   │  │ Reports  │  │ Review   │        │
│  │  Cards   │  │  Charts  │  │ Monthly  │  │  Queue   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Upload**: Bank statement dropped in Google Drive `Statements/` folder
2. **Trigger**: n8n watches folder, detects new file
3. **Parse**: Extract transactions based on file type (CSV/PDF/OFX)
4. **Hash**: Generate SHA-256 hash for deduplication
5. **Ingest**: POST to `/api/ingest` endpoint
6. **Normalize**: Clean merchant name, apply canonical vendor
7. **Categorize**:
   - Try deterministic rules (MCC, regex, amount)
   - If no match, use OpenAI with taxonomy
8. **Review**: Low confidence (<0.80) or high value (>$50) → review queue
9. **Store**: Save to PostgreSQL with all metadata
10. **Display**: Real-time update in dashboard

### Categorization Flow

```
Transaction
    │
    ▼
┌─────────────────┐
│ Rule 1 (MCC)    │──── Match? ──▶ Category + Confidence: 1.0
└─────────────────┘       │
         │                │
         │ No match       │
         ▼                │
┌─────────────────┐       │
│ Rule 2 (Regex)  │──── Match? ──▶ Category + Confidence: 1.0
└─────────────────┘       │
         │                │
         │ No match       │
         ▼                │
┌─────────────────┐       │
│ OpenAI GPT      │──── Always returns ──▶ Category + Confidence: 0.0-1.0
└─────────────────┘
         │
         ▼
    Confidence < 0.80
    OR Amount > $50?
         │
         ├─── Yes ──▶ Review Queue
         │
         └─── No ──▶ Auto-finalize
```

## Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (20.10+)
- **Google Drive API** credentials
- **OpenAI API** key
- **Homelab** or server with 2GB+ RAM

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/finance-automation.git
cd finance-automation

# 2. Configure environment
cd ops
cp .env.example .env
nano .env  # Add your API keys and passwords

# 3. Start everything
make quickstart

# 4. Access dashboard
open http://localhost:8080
```

That's it! The system is now:
- Running on http://localhost:8080
- Watching your Google Drive
- Ready to categorize transactions

### First Transaction

```bash
# Test with a sample transaction
curl -X POST http://localhost:8080/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "txn_date": "2025-10-26",
    "amount_cents": 1250,
    "currency": "USD",
    "direction": "debit",
    "raw_descriptor": "STARBUCKS STORE 1234",
    "source_account": "visa_primary",
    "mcc": "5814",
    "hash_id": "test123"
  }'
```

Check the dashboard - your transaction should appear categorized as "Dining > Coffee"!

## Tech Stack

### Backend
- **FastAPI** 0.115.0 - Modern Python web framework
- **PostgreSQL** 16 - Relational database with JSONB support
- **Redis** 7 - Caching and session storage
- **SQLAlchemy** 2.0 - Async ORM
- **Alembic** - Database migrations
- **Pydantic** v2 - Data validation

### AI & Automation
- **OpenAI** GPT-4o-mini - Transaction categorization
- **n8n** - Workflow automation and orchestration

### Frontend
- **Jinja2** Templates - Server-side rendering
- **Tailwind CSS** - Utility-first styling
- **Custom CSS** - Glassmorphic effects

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-service orchestration
- **Uvicorn** - ASGI server
- **Nginx** - Reverse proxy (optional)

### Testing & Quality
- **pytest** - Testing framework
- **black** - Code formatter
- **ruff** - Fast linter
- **mypy** - Type checking

## Project Structure

```
finance-automation/
├── api/                      # FastAPI application
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   │   ├── ingest.py     # Transaction ingestion
│   │   │   ├── categorize.py # Categorization logic
│   │   │   ├── reports.py    # Reporting endpoints
│   │   │   └── alerts.py     # Anomaly alerts
│   │   ├── services/         # Business logic
│   │   │   ├── vendor_normalize.py
│   │   │   ├── receipts.py
│   │   │   └── anomalies.py
│   │   ├── templates/        # Jinja2 HTML templates
│   │   ├── static/           # CSS, JS, images
│   │   ├── config.py         # Configuration
│   │   ├── db.py             # Database setup
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   └── main.py           # Application entry
│   ├── alembic/              # Database migrations
│   ├── tests/                # Test suite
│   └── requirements.txt      # Python dependencies
│
├── n8n/                      # Workflow automation
│   └── workflows/
│       ├── drive_ingest.json # Google Drive watcher
│       └── weekly_report.json
│
├── ops/                      # Deployment & operations
│   ├── docker-compose.yml    # Service orchestration
│   ├── Dockerfile            # API container build
│   ├── Makefile              # Automation commands
│   ├── .env.example          # Environment template
│   └── nginx.conf            # Reverse proxy config
│
├── seed/                     # Initial data
│   ├── seed_rules.sql        # Categorization rules
│   └── seed_vendors.sql      # Vendor aliases
│
├── README.md                 # This file
├── SECURITY.md               # Security documentation
├── DEPLOYMENT.md             # Deployment guide
└── USAGE.md                  # User guide
```

## Setup & Installation

### Detailed Setup

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment instructions.

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/finance-automation.git
cd finance-automation
```

#### 2. Configure Environment

```bash
cd ops
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Database
POSTGRES_USER=rody
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=finance
DATABASE_URL=postgresql+psycopg2://rody:your_password@postgres:5432/finance

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# Security
JWT_SECRET=generate_random_64_character_string_here
ALLOWED_ORIGINS=http://localhost:8080,https://finance.yourdomain.com
```

#### 3. Start Services

```bash
# Complete setup (recommended)
make quickstart

# Or step-by-step
make init          # Install dependencies
make up            # Start Docker containers
make migrate       # Run database migrations
make seed          # Load initial data
```

#### 4. Verify Installation

```bash
# Check service health
make health

# View logs
make logs

# Test API
curl http://localhost:8080/health
```

#### 5. Configure n8n (Optional)

See [n8n Integration](#n8n-integration) section below.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_USER` | Yes | - | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | - | PostgreSQL password |
| `POSTGRES_DB` | Yes | `finance` | Database name |
| `DATABASE_URL` | Yes | - | Full PostgreSQL connection URL |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for categorization |
| `JWT_SECRET` | Yes | - | Secret for JWT tokens |
| `ALLOWED_ORIGINS` | No | `http://localhost:8080` | CORS origins (comma-separated) |
| `LOW_CONFIDENCE` | No | `0.80` | Confidence threshold for review |
| `REVIEW_AMOUNT_CENTS` | No | `5000` | Amount threshold ($50) |
| `TELEGRAM_WEBHOOK_URL` | No | - | Telegram webhook for alerts |
| `REDIS_URL` | No | `redis://redis:6379/0` | Redis connection URL |
| `LOG_LEVEL` | No | `info` | Logging level |
| `ENVIRONMENT` | No | `development` | Environment name |

### Category Taxonomy

The system uses a fixed taxonomy for consistent categorization:

**Core Categories:**
- Groceries, Dining, Transport, Fuel
- Utilities, Rent/Mortgage, Internet, Mobile
- Subscriptions, Shopping, Healthcare, Pets
- Gifts/Charity, Entertainment
- Travel-Air, Travel-Hotel, Travel-Other
- Income, Transfers, Savings

Each category can have custom subcategories defined in the rules.

## Usage

See [USAGE.md](USAGE.md) for detailed user guide.

### Adding Transactions

#### Method 1: Google Drive (Recommended)

1. Drop your bank statement (CSV, PDF, OFX) in Google Drive folder: `Statements/`
2. n8n workflow automatically detects and processes
3. View in dashboard within 2 minutes

#### Method 2: Manual Upload

1. Navigate to dashboard
2. Click "Upload Statement"
3. Select file and source account
4. Submit

#### Method 3: API

```bash
curl -X POST http://localhost:8080/api/ingest \
  -H "Content-Type: application/json" \
  -d @transaction.json
```

### Reviewing Transactions

Low-confidence or high-value transactions appear in the Review Queue:

1. Navigate to "Review" tab
2. See transaction details and AI suggestion
3. Accept, modify, or reject category
4. Click "Finalize"

### Viewing Reports

- **Dashboard**: Overview cards, category donut, top vendors
- **Monthly Report**: `/api/report/summary?month=2025-10`
- **Alerts**: `/api/alerts` for anomalies

## API Documentation

### Interactive Docs

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

### Key Endpoints

#### Transaction Ingestion

```http
POST /api/ingest
Content-Type: application/json

{
  "txn_date": "2025-10-26",
  "amount_cents": 1250,
  "currency": "USD",
  "direction": "debit",
  "raw_descriptor": "AMAZON.COM MKTP US",
  "source_account": "visa_primary",
  "mcc": "5942",
  "memo": null,
  "hash_id": "a1b2c3d4e5f6..."
}
```

#### Categorization

```http
POST /api/categorize/{transaction_id}
```

Response:
```json
{
  "id": 123,
  "category": "Shopping",
  "subcategory": "Online",
  "confidence": 0.95,
  "status": "finalized"
}
```

#### Monthly Summary

```http
GET /api/report/summary?month=2025-10
```

See [api/README.md](api/README.md) for complete API documentation.

## Development

### Local Development (without Docker)

```bash
# 1. Create virtual environment
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up database
# Create PostgreSQL database manually
createdb finance

# 4. Configure environment
cp .env.example .env
# Edit DATABASE_URL to point to your local PostgreSQL

# 5. Run migrations
alembic upgrade head

# 6. Seed data
psql finance < ../seed/seed_rules.sql
psql finance < ../seed/seed_vendors.sql

# 7. Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Running Tests

```bash
cd api

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_ingest.py -v
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
cd api
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guide.

### Production Checklist

- [ ] Strong passwords for all services
- [ ] `JWT_SECRET` is random 64+ characters
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_LEVEL=warning`
- [ ] HTTPS/TLS configured (via nginx or Cloudflare)
- [ ] Firewall rules configured
- [ ] Automated backups set up
- [ ] Monitoring and alerts configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured

### Backup & Restore

```bash
# Backup database
make backup

# Restore from backup
make restore FILE=backups/finance_20250126.sql.gz

# Automated daily backups (cron)
0 2 * * * cd /path/to/ops && make backup
```

### Updating

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
cd ops
make down
make build
make up

# Apply new migrations
make migrate
```

## Security

See [SECURITY.md](SECURITY.md) for comprehensive security documentation.

### Key Security Features

- **No PAN Storage**: Full card numbers never stored or logged
- **JWT Authentication**: Secure API access
- **Environment Secrets**: All sensitive data in `.env`
- **CORS Protection**: Configurable allowed origins
- **Non-root Containers**: Docker runs as `appuser:1000`
- **Network Isolation**: Internal Docker network
- **Read-only Mounts**: System files mounted read-only

### Recommended Deployment

- Behind **Tailscale** or VPN for private access
- Optional **Cloudflare Tunnel** for external access
- **Nginx** reverse proxy with rate limiting
- **PostgreSQL** with encryption at rest
- Regular **security audits** of dependencies

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check logs
make logs

# Verify environment
cat .env | grep -v PASSWORD

# Check Docker
docker compose ps
docker compose logs
```

#### Database Connection Error

```bash
# Test connection
docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Check database logs
make logs-db

# Verify DATABASE_URL in .env
```

#### OpenAI API Errors

- Verify API key is valid: https://platform.openai.com/api-keys
- Check usage quota: https://platform.openai.com/usage
- Ensure model name is correct (`gpt-4o-mini`)
- Review OpenAI status: https://status.openai.com

#### Transactions Not Categorizing

```bash
# Check rules
psql finance -c "SELECT * FROM rules WHERE active = true ORDER BY priority;"

# Test categorization
curl -X POST http://localhost:8080/api/categorize/{id}

# Check OpenAI logs
make logs-api | grep -i openai
```

#### Dashboard Not Loading

```bash
# Check API health
curl http://localhost:8080/health

# Restart API
docker compose restart api

# Check browser console for errors
```

### Getting Help

1. Check logs: `make logs`
2. Review environment configuration
3. Consult documentation
4. Check GitHub issues

## n8n Integration

### Setting Up Workflows

1. **Start n8n** (optional service in docker-compose.yml)
2. **Import workflows** from `n8n/workflows/`
3. **Configure credentials**:
   - Google Drive API
   - OpenAI API
   - Webhook URL for this API
4. **Activate workflows**

### Workflow Overview

**drive_ingest.json**:
- Watches Google Drive `Statements/` folder
- Parses CSV/PDF/OFX files
- POSTs to `/api/ingest`
- Links receipts by matching date/amount

**weekly_report.json**:
- Runs every Monday 9 AM
- Generates weekly summary
- Sends to Telegram (optional)

## Contributing

This is a private homelab project. If you'd like to contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Add tests for new features
- Run `make format` before committing

## License

**Private Use Only** - This is a personal homelab project not licensed for public use.

The codebase includes dependencies with various open-source licenses. See individual package licenses for details.

## Acknowledgments

- **FastAPI** - Modern Python web framework
- **OpenAI** - GPT models for categorization
- **n8n** - Workflow automation
- **PostgreSQL** - Reliable database
- **Tailwind CSS** - Utility-first CSS framework

---

**Made with ☕ for personal finance automation**

**Disclaimer**: This software handles sensitive financial data. Use at your own risk. Always keep backups and follow security best practices.
