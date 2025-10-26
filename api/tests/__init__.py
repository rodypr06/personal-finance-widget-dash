"""
Tests package for Personal Finance Automation.

This package contains comprehensive test suites for:
- Transaction ingestion and processing
- Rules-based categorization
- OpenAI fallback categorization
- Reporting and analytics
- Anomaly detection
- Vendor normalization

Test Organization:
- conftest.py: Shared fixtures and test configuration
- test_ingest.py: Ingestion endpoint and hash generation tests (14 tests)
- test_rules.py: Rules engine and condition evaluation tests (19 tests)
- test_categorize.py: Categorization logic and OpenAI integration tests (15 tests)
- test_reports.py: Reporting and summary endpoint tests (12 tests)
- test_anomalies.py: Anomaly detection service tests (18 tests)

Total: 78+ comprehensive tests covering critical paths and edge cases.

Coverage Goals:
- Ingestion: >90% (critical path)
- Rules Engine: >95% (deterministic logic)
- Categorization: >85% (includes external API)
- Reports: >80% (aggregation logic)
- Anomalies: >85% (detection algorithms)

Running Tests:
    # Run all tests
    pytest

    # Run specific test file
    pytest tests/test_ingest.py

    # Run with coverage
    pytest --cov=app --cov-report=html

    # Run specific test class
    pytest tests/test_rules.py::TestRuleMatching

    # Run specific test
    pytest tests/test_categorize.py::TestCategorizeWithOpenAI::test_categorize_with_openai_success
"""

__version__ = "1.0.0"
