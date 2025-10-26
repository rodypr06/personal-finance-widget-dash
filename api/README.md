# Finance Automation API

FastAPI-based backend for personal finance automation with PostgreSQL, OpenAI categorization, and n8n integration.

> **Note**: This is the API-specific documentation. For complete system documentation, see the [main README](../README.md).

## Quick Links

- **Main Documentation**: [../README.md](../README.md)
- **Deployment Guide**: [../DEPLOYMENT.md](../DEPLOYMENT.md)
- **User Guide**: [../USAGE.md](../USAGE.md)
- **Security**: [../SECURITY.md](../SECURITY.md)

## Features

- **Transaction Ingestion**: Receive and normalize financial transactions from various sources
- **Smart Categorization**: Rules-based + AI-powered transaction categorization
- **Vendor Normalization**: Canonical vendor names with alias support
- **Deduplication**: Hash-based transaction deduplication
- **Reporting**: Monthly/weekly summaries with category breakdowns
- **Alerts**: Anomaly detection and threshold-based notifications
- **Receipt Linking**: Link transactions to receipts in Google Drive

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **AI**: OpenAI GPT-4o-mini for categorization
- **Security**: JWT authentication with python-jose
- **Validation**: Pydantic v2

## Project Structure

```
api/
├── app/
│   ├── __init__.py
│   ├── config.py          # Environment configuration
│   ├── db.py              # Database setup and session management
│   ├── deps.py            # FastAPI dependencies
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic schemas
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic
│   ├── templates/         # Jinja2 templates
│   └── static/            # CSS, JS, images
├── alembic/
│   ├── env.py             # Migration environment
│   └── versions/          # Migration scripts
│       └── 001_initial_schema.py
├── tests/                 # Test suite
├── alembic.ini            # Alembic configuration
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata
└── .env.example           # Environment template
```

## Database Schema

### Tables

**transactions**
- Primary transaction storage with categorization and metadata
- Fields: id, txn_date, amount_cents, currency, direction, raw_descriptor, canonical_vendor, mcc, memo, source_account, hash_id (unique), receipt_url, category, subcategory, confidence, status, notes
- Indexes: txn_date, canonical_vendor, category, status

**vendors**
- Canonical vendor names with aliases
- Fields: canonical_vendor (PK), default_category, default_subcat, aliases[]

**rules**
- Deterministic categorization rules
- Fields: id, priority, condition (JSONB), action (JSONB), active, created_at
- Supports: contains, regex, mcc, amount_range, account matching

**reports**
- Cached report data for performance
- Fields: id, period, kind, payload (JSONB), created_at

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql+asyncpg://user:pass@localhost:5432/finance`)
- `OPENAI_API_KEY`: OpenAI API key for categorization
- `JWT_SECRET`: Secret key for JWT tokens
- `ALLOWED_ORIGINS`: CORS allowed origins

### 3. Run Migrations

```bash
# Apply database migrations
alembic upgrade head

# Check migration status
alembic current
```

### 4. Start Development Server

```bash
# Run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Or use make (if makefile exists)
make dev
```

## API Endpoints

### Transaction Management

- `POST /api/ingest` - Ingest new transaction
- `POST /api/categorize/{id}` - Categorize transaction
- `POST /api/finalize/{id}` - Finalize category
- `GET /api/transactions` - List transactions (with filters)
- `GET /api/transactions/{id}` - Get transaction details

### Reporting

- `GET /api/report/summary?month=YYYY-MM` - Monthly summary
- `GET /api/alerts` - Get alerts and anomalies

### Vendor Management

- `GET /api/vendors` - List vendors
- `POST /api/vendors` - Create/update vendor

### Rules

- `GET /api/rules` - List categorization rules
- `POST /api/rules` - Create new rule
- `PATCH /api/rules/{id}` - Update rule
- `DELETE /api/rules/{id}` - Delete rule

## API Usage Examples

### Ingest Transaction

```bash
curl -X POST http://localhost:8080/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "txn_date": "2025-10-24",
    "amount_cents": 784,
    "currency": "USD",
    "direction": "debit",
    "raw_descriptor": "STARBUCKS 1234",
    "source_account": "amex_blue_cash",
    "mcc": "5814",
    "hash_id": "a1b2c3d4e5f6..."
  }'
```

Response:
```json
{
  "id": 123,
  "status": "ingested"
}
```

### Categorize Transaction

```bash
curl -X POST http://localhost:8080/api/categorize/123
```

Response:
```json
{
  "id": 123,
  "category": "Dining",
  "subcategory": "Coffee",
  "confidence": 0.91,
  "status": "finalized"
}
```

### Get Monthly Summary

```bash
curl http://localhost:8080/api/report/summary?month=2025-10
```

Response:
```json
{
  "period": "2025-10",
  "totals_by_category": [
    {"category": "Groceries", "amount_cents": 45000},
    {"category": "Dining", "amount_cents": 12000}
  ],
  "top_vendors": [
    {"vendor": "Hy-Vee", "amount_cents": 22000}
  ],
  "timeseries": [
    {"date": "2025-10-01", "sum_cents": 4300}
  ],
  "total_income_cents": 500000,
  "total_expense_cents": 180000,
  "net_savings_cents": 320000
}
```

## Categorization

### Categorization Flow

1. **Deterministic Rules**: Apply rules from database (priority order)
   - MCC matching
   - Descriptor contains/regex
   - Amount range
   - Account-specific rules

2. **AI Fallback**: If no rule matches, use OpenAI
   - Taxonomy-based categorization
   - Confidence scoring
   - Vendor extraction

3. **Review Queue**: Low confidence or high-value transactions
   - Confidence < 0.80
   - Amount > $50.00

### Category Taxonomy

Standard categories:
- Groceries, Dining, Transport, Fuel, Utilities, Rent/Mortgage
- Internet, Mobile, Subscriptions, Shopping, Healthcare, Pets
- Gifts/Charity, Entertainment, Travel-Air, Travel-Hotel, Travel-Other
- Income, Transfers, Savings

## Development

### Code Quality

```bash
# Format code
black app/ tests/
ruff check --fix app/ tests/

# Type checking
mypy app/

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html
```

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Create empty migration
alembic revision -m "description"

# Apply migration
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

### Database Management

```bash
# Reset database (WARNING: destructive)
alembic downgrade base
alembic upgrade head

# Show migration history
alembic history

# Show current version
alembic current
```

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_ingest.py

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## Deployment

### Docker

```bash
# Build image
docker build -t finance-api .

# Run container
docker run -d \
  --name finance-api \
  -p 8080:8080 \
  --env-file .env \
  finance-api
```

### Production Considerations

- Use production-grade ASGI server (e.g., gunicorn with uvicorn workers)
- Enable HTTPS/TLS
- Set up connection pooling
- Configure proper logging
- Implement rate limiting
- Set up monitoring and alerts
- Regular database backups
- Rotate JWT secrets

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection URL |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |
| `JWT_SECRET` | Yes | - | JWT signing secret |
| `ALLOWED_ORIGINS` | No | `http://localhost:8080` | CORS allowed origins (comma-separated) |
| `LOW_CONFIDENCE` | No | `0.80` | Confidence threshold for review |
| `REVIEW_AMOUNT_CENTS` | No | `5000` | Amount threshold for review ($50) |
| `TELEGRAM_WEBHOOK_URL` | No | - | Telegram webhook for alerts |

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Check if database exists
psql -U postgres -c "\l"

# Create database if needed
createdb -U postgres finance
```

### Migration Issues

```bash
# Check current migration state
alembic current

# Show pending migrations
alembic history

# Force migration version (use with caution)
alembic stamp head
```

### OpenAI API Issues

- Verify API key is valid
- Check rate limits and quotas
- Ensure model name is correct
- Review OpenAI status page

## Additional Resources

- **Full System Documentation**: [../README.md](../README.md) - Complete project overview
- **Deployment Guide**: [../DEPLOYMENT.md](../DEPLOYMENT.md) - Production deployment
- **Usage Guide**: [../USAGE.md](../USAGE.md) - User manual
- **Security Documentation**: [../SECURITY.md](../SECURITY.md) - Security best practices

## License

Private homelab project - not licensed for public use.

## Support

For issues or questions:
1. Check service logs: `make logs` (from `../ops/` directory)
2. Review [Troubleshooting](../DEPLOYMENT.md#troubleshooting) section
3. Consult API documentation at http://localhost:8080/docs
