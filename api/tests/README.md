# Personal Finance Automation - Test Suite

Comprehensive test suite for the Personal Finance Automation system built with pytest-asyncio.

## Overview

This test suite provides **78+ comprehensive tests** covering all critical paths and edge cases across the application:

- **14 tests** for transaction ingestion and hash generation
- **19 tests** for rules engine and condition evaluation
- **15 tests** for categorization logic and OpenAI integration
- **12 tests** for reporting and summary endpoints
- **18 tests** for anomaly detection algorithms

## Test Organization

```
tests/
├── __init__.py              # Package documentation
├── conftest.py              # Shared fixtures and test configuration
├── test_ingest.py           # Ingestion endpoint tests
├── test_rules.py            # Rules engine tests
├── test_categorize.py       # Categorization tests
├── test_reports.py          # Reporting tests
├── test_anomalies.py        # Anomaly detection tests
└── README.md               # This file
```

## Test Coverage Goals

| Module | Target Coverage | Focus |
|--------|----------------|-------|
| Ingestion | >90% | Critical path for data entry |
| Rules Engine | >95% | Deterministic logic, high testability |
| Categorization | >85% | Includes external API, mocked |
| Reports | >80% | Aggregation and query logic |
| Anomalies | >85% | Detection algorithms |

## Running Tests

### All Tests
```bash
# Run all tests with default options
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

### Specific Test Files
```bash
# Run ingestion tests only
pytest tests/test_ingest.py

# Run rules tests only
pytest tests/test_rules.py

# Run categorization tests only
pytest tests/test_categorize.py

# Run reporting tests only
pytest tests/test_reports.py

# Run anomaly tests only
pytest tests/test_anomalies.py
```

### Specific Test Classes
```bash
# Run specific test class
pytest tests/test_rules.py::TestRuleMatching

# Run multiple classes
pytest tests/test_categorize.py::TestCategorizeWithRule tests/test_categorize.py::TestCategorizeWithOpenAI
```

### Specific Tests
```bash
# Run single test
pytest tests/test_ingest.py::TestIngestEndpoint::test_ingest_new_transaction

# Run tests matching pattern
pytest -k "duplicate"
```

### Advanced Options
```bash
# Run with detailed output and show local variables
pytest -vv --showlocals

# Run only failed tests from last run
pytest --lf

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Stop on first failure
pytest -x

# Show top 10 slowest tests
pytest --durations=10
```

## Test Fixtures

### Database Fixtures

#### `test_db`
In-memory SQLite database for fast, isolated tests.

```python
@pytest.mark.asyncio
async def test_example(test_db: AsyncSession):
    # Use test_db for database operations
    pass
```

#### `test_client`
FastAPI TestClient with test database dependency override.

```python
@pytest.mark.asyncio
async def test_api_endpoint(test_client: AsyncClient):
    response = await test_client.post("/ingest", json=payload)
    assert response.status_code == 200
```

### Sample Data Fixtures

#### `sample_transaction_data`
Dictionary with sample transaction data for testing.

#### `sample_transaction`
Persisted transaction object in test database.

#### `sample_vendor`
Persisted vendor object with aliases.

#### `sample_rule`
Persisted categorization rule.

#### `sample_vendors`
List of multiple vendors for comprehensive testing.

#### `sample_rules`
List of multiple rules with various conditions.

### Helper Functions

#### `hash_generator`
Function to generate consistent transaction hash IDs.

```python
def test_with_hash(hash_generator):
    hash_id = hash_generator(date(2025, 10, 24), 1000, "MERCHANT", "account")
    # Use hash_id...
```

## Test Categories

### 1. Ingestion Tests (`test_ingest.py`)

**Coverage**: Transaction ingestion, deduplication, vendor normalization

Tests:
- ✅ Successfully ingest new transaction
- ✅ Handle duplicate hash_id (upsert behavior)
- ✅ Validate missing required fields
- ✅ Validate invalid direction values
- ✅ Vendor normalization during ingestion
- ✅ Hash ID generation consistency
- ✅ Hash ID uniqueness for different inputs
- ✅ Edge cases (zero amount, large amounts, credit transactions)

### 2. Rules Engine Tests (`test_rules.py`)

**Coverage**: Deterministic categorization rules, condition evaluation

Tests:
- ✅ MCC exact matching
- ✅ MCC in list matching
- ✅ Descriptor contains matching (case-insensitive)
- ✅ Regex pattern matching
- ✅ Amount range filtering
- ✅ Account matching
- ✅ Direction matching
- ✅ Complex AND/OR conditions
- ✅ Nested logical operators
- ✅ Rule priority ordering
- ✅ Inactive rule skipping
- ✅ Error handling (invalid regex, unknown conditions)

### 3. Categorization Tests (`test_categorize.py`)

**Coverage**: OpenAI integration, confidence scoring, manual overrides

Tests:
- ✅ Rule-based categorization (confidence = 1.0)
- ✅ OpenAI fallback categorization
- ✅ Retry logic for malformed JSON
- ✅ Timeout handling
- ✅ Invalid category handling
- ✅ Rate limit retry with exponential backoff
- ✅ Confidence threshold logic (status = review)
- ✅ High amount threshold logic
- ✅ Manual category finalization
- ✅ Confidence score clamping [0, 1]

**Mocking**: OpenAI API calls are mocked using `unittest.mock.AsyncMock`

### 4. Reporting Tests (`test_reports.py`)

**Coverage**: Summary aggregation, date filtering, analytics

Tests:
- ✅ Monthly summary with category totals
- ✅ Income/expense/savings calculation
- ✅ Top vendors calculation (limit 10)
- ✅ Timeseries daily aggregation
- ✅ Date range filtering
- ✅ Category filtering
- ✅ Empty month handling
- ✅ Large dataset performance
- ✅ Multiple currency handling

### 5. Anomaly Detection Tests (`test_anomalies.py`)

**Coverage**: Alert generation, pattern detection, outlier identification

Tests:
- ✅ New vendor alerts (over threshold)
- ✅ Missing receipt alerts (high-value transactions)
- ✅ Duplicate transaction detection
- ✅ Pending review alerts (low confidence)
- ✅ Pending review alerts (high amount)
- ✅ Z-score outlier detection
- ✅ Unusual spending pattern detection
- ✅ Credit transaction exclusions
- ✅ No anomalies for normal transactions

## Mocking External Services

### OpenAI API

OpenAI API calls are mocked in categorization tests:

```python
from unittest.mock import AsyncMock, patch, MagicMock

mock_response = MagicMock()
mock_response.choices = [
    MagicMock(
        message=MagicMock(
            content=json.dumps({
                "category": "Dining",
                "subcategory": "Coffee",
                "confidence": 0.93,
                "vendor": "Starbucks"
            })
        )
    )
]

with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
    mock_create.return_value = mock_response
    # Test code...
```

### Google Drive

Google Drive integration is not directly tested in the API layer. Drive operations occur in n8n workflows.

## Coverage Reports

### Generate HTML Coverage Report

```bash
pytest --cov=app --cov-report=html
```

Open `htmlcov/index.html` in browser to view interactive coverage report.

### Generate Terminal Coverage Report

```bash
pytest --cov=app --cov-report=term-missing
```

### Coverage Configuration

Coverage settings are in `pytest.ini`:
- Source: `app` directory
- Omit: tests, cache, virtual environments
- Target: 80%+ overall coverage

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Best Practices

### Test Isolation
- Each test uses fresh in-memory database
- No shared state between tests
- Fixtures are function-scoped by default

### Async Testing
- Use `@pytest.mark.asyncio` decorator
- Use `async def` for test functions
- Use `await` for async operations

### Descriptive Test Names
```python
# Good
async def test_categorize_with_rule_confidence_is_one():
    ...

# Bad
async def test_categorize():
    ...
```

### Test Organization
```python
class TestFeatureGroup:
    """Group related tests in classes."""

    async def test_success_case(self):
        ...

    async def test_error_case(self):
        ...

    async def test_edge_case(self):
        ...
```

### Assert Messages
```python
# Good
assert result["category"] == "Dining", f"Expected 'Dining' but got {result['category']}"

# Acceptable
assert result["category"] == "Dining"
```

## Troubleshooting

### Import Errors
Ensure you're running from the `api/` directory:
```bash
cd /home/macboypr/personal-financial-tracker/api
pytest
```

### Async Errors
Ensure `pytest-asyncio` is installed and `asyncio_mode = auto` is set in `pytest.ini`.

### Database Errors
SQLite is used for tests (not PostgreSQL). Ensure `aiosqlite` is installed.

### OpenAI Mock Errors
Ensure mocks are patching the correct import path: `app.categorize.openai_client`

## Contributing

When adding new features, please:
1. Write tests first (TDD)
2. Aim for >80% coverage
3. Include success, error, and edge cases
4. Mock external services
5. Use descriptive test names
6. Group related tests in classes

## Test Maintenance

- Review and update tests when API contracts change
- Add regression tests for bug fixes
- Update mocks when external APIs change
- Keep test data realistic and representative
- Remove obsolete tests for deprecated features

---

**Total Test Count**: 78+ tests
**Target Coverage**: 80%+ overall
**Test Framework**: pytest + pytest-asyncio + pytest-cov
