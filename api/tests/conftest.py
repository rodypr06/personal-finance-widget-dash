"""
Test fixtures and configuration for pytest-asyncio.

This module provides shared fixtures for database setup, test client,
and sample data for comprehensive testing.
"""
import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import AsyncGenerator, Dict, Any
import hashlib

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Transaction, Vendor, Rule


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for the test session.

    This ensures all async fixtures and tests share the same event loop.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create in-memory SQLite database for testing.

    This fixture creates a fresh database for each test, ensuring test isolation.
    SQLite in-memory databases are fast and don't require cleanup.

    Yields:
        AsyncSession: Database session for the test
    """
    # Use in-memory SQLite with StaticPool for thread safety
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create session
    async with async_session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create FastAPI TestClient with test database.

    This fixture overrides the database dependency to use the test database
    and provides an async HTTP client for API testing.

    Args:
        test_db: Test database session

    Yields:
        AsyncClient: HTTP client for API testing
    """
    # Override database dependency
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_transaction_data() -> Dict[str, Any]:
    """
    Generate sample transaction data for testing.

    Returns:
        Dict with transaction fields
    """
    raw_descriptor = "STARBUCKS 1234"
    txn_date = date(2025, 10, 24)
    amount_cents = 784
    source_account = "amex_blue_cash"

    # Generate hash ID
    hash_string = f"{txn_date}|{amount_cents}|{raw_descriptor}|{source_account}"
    hash_id = hashlib.sha256(hash_string.encode()).hexdigest()

    return {
        "txn_date": txn_date,
        "amount_cents": amount_cents,
        "currency": "USD",
        "direction": "debit",
        "raw_descriptor": raw_descriptor,
        "source_account": source_account,
        "memo": None,
        "mcc": "5814",  # Coffee shops
        "hash_id": hash_id,
    }


@pytest_asyncio.fixture
async def sample_transaction(
    test_db: AsyncSession,
    sample_transaction_data: Dict[str, Any]
) -> Transaction:
    """
    Create and persist a sample transaction in the database.

    Args:
        test_db: Test database session
        sample_transaction_data: Transaction data

    Returns:
        Transaction: Persisted transaction object
    """
    txn = Transaction(**sample_transaction_data)
    test_db.add(txn)
    await test_db.commit()
    await test_db.refresh(txn)
    return txn


@pytest_asyncio.fixture
async def sample_vendor(test_db: AsyncSession) -> Vendor:
    """
    Create and persist a sample vendor in the database.

    Args:
        test_db: Test database session

    Returns:
        Vendor: Persisted vendor object
    """
    vendor = Vendor(
        canonical_vendor="Starbucks",
        default_category="Dining",
        default_subcat="Coffee",
        aliases=[
            "STARBUCKS",
            "SBUX",
            "STARBUCKS COFFEE",
            "TST* STARBUCKS",
        ],
    )
    test_db.add(vendor)
    await test_db.commit()
    await test_db.refresh(vendor)
    return vendor


@pytest_asyncio.fixture
async def sample_rule(test_db: AsyncSession) -> Rule:
    """
    Create and persist a sample categorization rule.

    Args:
        test_db: Test database session

    Returns:
        Rule: Persisted rule object
    """
    rule = Rule(
        priority=10,
        condition={"contains": "STARBUCKS"},
        action={"category": "Dining", "subcategory": "Coffee"},
        active=True,
    )
    test_db.add(rule)
    await test_db.commit()
    await test_db.refresh(rule)
    return rule


@pytest_asyncio.fixture
async def sample_vendors(test_db: AsyncSession) -> list[Vendor]:
    """
    Create multiple sample vendors for comprehensive testing.

    Args:
        test_db: Test database session

    Returns:
        List of persisted vendor objects
    """
    vendors = [
        Vendor(
            canonical_vendor="Hy-Vee",
            default_category="Groceries",
            default_subcat="Supermarket",
            aliases=["HY-VEE", "HYVEE", "HY VEE"],
        ),
        Vendor(
            canonical_vendor="Netflix",
            default_category="Subscriptions",
            default_subcat="Streaming",
            aliases=["NETFLIX.COM", "NETFLIX COM"],
        ),
        Vendor(
            canonical_vendor="Casey's",
            default_category="Fuel",
            default_subcat="Gas Station",
            aliases=["CASEYS", "CASEY'S", "CASEY'S STORE"],
        ),
        Vendor(
            canonical_vendor="Target",
            default_category="Shopping",
            default_subcat="Retail",
            aliases=["TARGET STORE", "TGT"],
        ),
    ]

    for vendor in vendors:
        test_db.add(vendor)

    await test_db.commit()

    # Refresh all vendors
    for vendor in vendors:
        await test_db.refresh(vendor)

    return vendors


@pytest_asyncio.fixture
async def sample_rules(test_db: AsyncSession) -> list[Rule]:
    """
    Create multiple sample rules for comprehensive testing.

    Args:
        test_db: Test database session

    Returns:
        List of persisted rule objects
    """
    rules = [
        # MCC-based rules
        Rule(
            priority=1,
            condition={"mcc_in": ["5411", "5422"]},
            action={"category": "Groceries", "subcategory": "Supermarket"},
            active=True,
        ),
        Rule(
            priority=2,
            condition={"mcc": "5814"},
            action={"category": "Dining", "subcategory": "Coffee"},
            active=True,
        ),
        # Descriptor-based rules
        Rule(
            priority=10,
            condition={"contains": "NETFLIX"},
            action={"category": "Subscriptions", "subcategory": "Streaming"},
            active=True,
        ),
        Rule(
            priority=11,
            condition={"regex": "^HY-?VEE.*"},
            action={"category": "Groceries", "subcategory": "Supermarket"},
            active=True,
        ),
        # Amount-based rule
        Rule(
            priority=20,
            condition={"amount_range": [100000, 999999999]},
            action={"category": "Shopping", "subcategory": "Large Purchase"},
            active=True,
        ),
        # Complex AND rule
        Rule(
            priority=30,
            condition={
                "and": [
                    {"contains": "DELTA"},
                    {"amount_range": [10000, 999999999]}
                ]
            },
            action={"category": "Travel-Air", "subcategory": "Flights"},
            active=True,
        ),
        # Inactive rule (should be skipped)
        Rule(
            priority=5,
            condition={"contains": "INACTIVE"},
            action={"category": "Test", "subcategory": "Inactive"},
            active=False,
        ),
    ]

    for rule in rules:
        test_db.add(rule)

    await test_db.commit()

    # Refresh all rules
    for rule in rules:
        await test_db.refresh(rule)

    return rules


# ============================================================================
# Helper Functions
# ============================================================================


def generate_hash_id(
    txn_date: date,
    amount_cents: int,
    descriptor: str,
    account: str
) -> str:
    """
    Generate transaction hash ID for deduplication.

    Args:
        txn_date: Transaction date
        amount_cents: Amount in cents
        descriptor: Raw descriptor
        account: Source account

    Returns:
        SHA256 hash string
    """
    hash_string = f"{txn_date}|{amount_cents}|{descriptor}|{account}"
    return hashlib.sha256(hash_string.encode()).hexdigest()


@pytest.fixture
def hash_generator():
    """Provide hash generation function to tests."""
    return generate_hash_id
