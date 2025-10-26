"""
Tests for transaction ingestion endpoints and logic.

This module tests the /ingest endpoint functionality including:
- Successful ingestion of new transactions
- Duplicate handling (upsert by hash_id)
- Input validation and error cases
- Vendor normalization integration
- Hash ID generation and validation
"""
from datetime import date
from decimal import Decimal
import hashlib

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, Vendor
from app.schemas import TxnIn, IngestResponse


class TestIngestEndpoint:
    """Test /ingest POST endpoint."""

    @pytest.mark.asyncio
    async def test_ingest_new_transaction(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test successfully ingesting a new transaction."""
        # Prepare request data
        txn_date = date(2025, 10, 24)
        raw_descriptor = "TARGET 1234"
        amount_cents = 4567
        source_account = "visa_rewards"

        hash_string = f"{txn_date}|{amount_cents}|{raw_descriptor}|{source_account}"
        hash_id = hashlib.sha256(hash_string.encode()).hexdigest()

        payload = {
            "txn_date": str(txn_date),
            "amount_cents": amount_cents,
            "currency": "USD",
            "direction": "debit",
            "raw_descriptor": raw_descriptor,
            "source_account": source_account,
            "memo": "Test memo",
            "mcc": "5411",
            "hash_id": hash_id,
        }

        # Make request
        response = await test_client.post("/ingest", json=payload)

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "ingested"

        # Verify database
        result = await test_db.execute(
            select(Transaction).where(Transaction.hash_id == hash_id)
        )
        txn = result.scalar_one()

        assert txn.txn_date == txn_date
        assert txn.amount_cents == amount_cents
        assert txn.raw_descriptor == raw_descriptor
        assert txn.source_account == source_account
        assert txn.memo == "Test memo"
        assert txn.mcc == "5411"
        assert txn.status == "ingested"

    @pytest.mark.asyncio
    async def test_ingest_duplicate_transaction(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test upserting a duplicate transaction by hash_id."""
        # Prepare duplicate with updated memo
        payload = {
            "txn_date": str(sample_transaction.txn_date),
            "amount_cents": sample_transaction.amount_cents,
            "currency": sample_transaction.currency,
            "direction": sample_transaction.direction,
            "raw_descriptor": sample_transaction.raw_descriptor,
            "source_account": sample_transaction.source_account,
            "memo": "UPDATED MEMO",
            "mcc": sample_transaction.mcc,
            "hash_id": sample_transaction.hash_id,
        }

        # Get original ID
        original_id = sample_transaction.id

        # Make request
        response = await test_client.post("/ingest", json=payload)

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == original_id  # Same ID due to upsert
        assert data["status"] == "ingested"

        # Verify database updated
        result = await test_db.execute(
            select(Transaction).where(Transaction.hash_id == sample_transaction.hash_id)
        )
        txn = result.scalar_one()

        assert txn.id == original_id
        assert txn.memo == "UPDATED MEMO"

    @pytest.mark.asyncio
    async def test_ingest_missing_required_fields(
        self,
        test_client: AsyncClient
    ):
        """Test validation error for missing required fields."""
        # Missing txn_date, amount_cents, direction
        payload = {
            "raw_descriptor": "TEST",
            "source_account": "test_account",
            "hash_id": "abc123",
        }

        response = await test_client.post("/ingest", json=payload)

        # Should return 422 Validation Error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ingest_invalid_direction(
        self,
        test_client: AsyncClient
    ):
        """Test validation error for invalid direction value."""
        txn_date = date(2025, 10, 24)
        hash_id = hashlib.sha256(b"test").hexdigest()

        payload = {
            "txn_date": str(txn_date),
            "amount_cents": 1000,
            "currency": "USD",
            "direction": "invalid",  # Invalid value
            "raw_descriptor": "TEST",
            "source_account": "test_account",
            "hash_id": hash_id,
        }

        response = await test_client.post("/ingest", json=payload)

        # Should return 422 Validation Error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ingest_vendor_normalization(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        sample_vendor: Vendor
    ):
        """Test vendor normalization during ingestion."""
        # Use a descriptor that should match the vendor alias
        txn_date = date(2025, 10, 24)
        raw_descriptor = "TST* STARBUCKS 5678"
        amount_cents = 892
        source_account = "amex_blue_cash"

        hash_string = f"{txn_date}|{amount_cents}|{raw_descriptor}|{source_account}"
        hash_id = hashlib.sha256(hash_string.encode()).hexdigest()

        payload = {
            "txn_date": str(txn_date),
            "amount_cents": amount_cents,
            "currency": "USD",
            "direction": "debit",
            "raw_descriptor": raw_descriptor,
            "source_account": source_account,
            "mcc": "5814",
            "hash_id": hash_id,
        }

        response = await test_client.post("/ingest", json=payload)

        assert response.status_code == 200

        # Verify vendor was normalized
        result = await test_db.execute(
            select(Transaction).where(Transaction.hash_id == hash_id)
        )
        txn = result.scalar_one()

        assert txn.canonical_vendor == "Starbucks"


class TestHashGeneration:
    """Test hash ID generation logic."""

    def test_hash_generation_consistency(self, hash_generator):
        """Test hash ID is consistent for same inputs."""
        txn_date = date(2025, 10, 24)
        amount_cents = 1234
        descriptor = "TEST MERCHANT"
        account = "test_account"

        hash1 = hash_generator(txn_date, amount_cents, descriptor, account)
        hash2 = hash_generator(txn_date, amount_cents, descriptor, account)

        assert hash1 == hash2

    def test_hash_generation_uniqueness(self, hash_generator):
        """Test hash ID is different for different inputs."""
        txn_date = date(2025, 10, 24)
        amount_cents = 1234
        descriptor = "TEST MERCHANT"
        account = "test_account"

        hash1 = hash_generator(txn_date, amount_cents, descriptor, account)

        # Different date
        hash2 = hash_generator(date(2025, 10, 25), amount_cents, descriptor, account)
        assert hash1 != hash2

        # Different amount
        hash3 = hash_generator(txn_date, 5678, descriptor, account)
        assert hash1 != hash3

        # Different descriptor
        hash4 = hash_generator(txn_date, amount_cents, "DIFFERENT", account)
        assert hash1 != hash4

        # Different account
        hash5 = hash_generator(txn_date, amount_cents, descriptor, "other_account")
        assert hash1 != hash5

    def test_hash_format(self, hash_generator):
        """Test hash ID format is valid SHA256."""
        txn_date = date(2025, 10, 24)
        amount_cents = 1234
        descriptor = "TEST"
        account = "test"

        hash_id = hash_generator(txn_date, amount_cents, descriptor, account)

        # SHA256 produces 64 character hex string
        assert len(hash_id) == 64
        assert all(c in "0123456789abcdef" for c in hash_id)


class TestVendorNormalizationIntegration:
    """Test vendor normalization integration during ingestion."""

    @pytest.mark.asyncio
    async def test_normalize_vendor_with_alias(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        sample_vendors: list[Vendor]
    ):
        """Test vendor normalization with known aliases."""
        txn_date = date(2025, 10, 24)
        raw_descriptor = "HYVEE STORE 1234"
        amount_cents = 5678
        source_account = "visa_rewards"

        hash_string = f"{txn_date}|{amount_cents}|{raw_descriptor}|{source_account}"
        hash_id = hashlib.sha256(hash_string.encode()).hexdigest()

        payload = {
            "txn_date": str(txn_date),
            "amount_cents": amount_cents,
            "currency": "USD",
            "direction": "debit",
            "raw_descriptor": raw_descriptor,
            "source_account": source_account,
            "mcc": "5411",
            "hash_id": hash_id,
        }

        response = await test_client.post("/ingest", json=payload)
        assert response.status_code == 200

        # Verify vendor normalization
        result = await test_db.execute(
            select(Transaction).where(Transaction.hash_id == hash_id)
        )
        txn = result.scalar_one()

        assert txn.canonical_vendor == "Hy-Vee"

    @pytest.mark.asyncio
    async def test_normalize_vendor_no_match(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test vendor normalization when no match found."""
        txn_date = date(2025, 10, 24)
        raw_descriptor = "UNKNOWN MERCHANT 999"
        amount_cents = 1234
        source_account = "visa_rewards"

        hash_string = f"{txn_date}|{amount_cents}|{raw_descriptor}|{source_account}"
        hash_id = hashlib.sha256(hash_string.encode()).hexdigest()

        payload = {
            "txn_date": str(txn_date),
            "amount_cents": amount_cents,
            "currency": "USD",
            "direction": "debit",
            "raw_descriptor": raw_descriptor,
            "source_account": source_account,
            "hash_id": hash_id,
        }

        response = await test_client.post("/ingest", json=payload)
        assert response.status_code == 200

        # Verify no vendor normalization
        result = await test_db.execute(
            select(Transaction).where(Transaction.hash_id == hash_id)
        )
        txn = result.scalar_one()

        assert txn.canonical_vendor is None


class TestIngestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_ingest_zero_amount(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test ingesting transaction with zero amount."""
        txn_date = date(2025, 10, 24)
        raw_descriptor = "TEST"
        amount_cents = 0
        source_account = "test_account"

        hash_string = f"{txn_date}|{amount_cents}|{raw_descriptor}|{source_account}"
        hash_id = hashlib.sha256(hash_string.encode()).hexdigest()

        payload = {
            "txn_date": str(txn_date),
            "amount_cents": amount_cents,
            "currency": "USD",
            "direction": "debit",
            "raw_descriptor": raw_descriptor,
            "source_account": source_account,
            "hash_id": hash_id,
        }

        response = await test_client.post("/ingest", json=payload)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ingest_large_amount(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test ingesting transaction with very large amount."""
        txn_date = date(2025, 10, 24)
        raw_descriptor = "BIG PURCHASE"
        amount_cents = 999999999  # $9,999,999.99
        source_account = "test_account"

        hash_string = f"{txn_date}|{amount_cents}|{raw_descriptor}|{source_account}"
        hash_id = hashlib.sha256(hash_string.encode()).hexdigest()

        payload = {
            "txn_date": str(txn_date),
            "amount_cents": amount_cents,
            "currency": "USD",
            "direction": "credit",
            "raw_descriptor": raw_descriptor,
            "source_account": source_account,
            "hash_id": hash_id,
        }

        response = await test_client.post("/ingest", json=payload)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ingest_credit_transaction(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test ingesting credit (income) transaction."""
        txn_date = date(2025, 10, 24)
        raw_descriptor = "PAYROLL DEPOSIT"
        amount_cents = 500000
        source_account = "checking"

        hash_string = f"{txn_date}|{amount_cents}|{raw_descriptor}|{source_account}"
        hash_id = hashlib.sha256(hash_string.encode()).hexdigest()

        payload = {
            "txn_date": str(txn_date),
            "amount_cents": amount_cents,
            "currency": "USD",
            "direction": "credit",
            "raw_descriptor": raw_descriptor,
            "source_account": source_account,
            "hash_id": hash_id,
        }

        response = await test_client.post("/ingest", json=payload)
        assert response.status_code == 200

        result = await test_db.execute(
            select(Transaction).where(Transaction.hash_id == hash_id)
        )
        txn = result.scalar_one()

        assert txn.direction == "credit"
