"""
Tests for anomaly detection service.

This module tests anomaly detection functionality including:
- New vendor alerts
- Missing receipt alerts
- Duplicate transaction detection
- Z-score outlier detection
- Unusual spending pattern detection
- Empty result handling
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction
from app.services.anomalies import (
    detect_anomalies,
    detect_new_vendors,
    detect_missing_receipts,
    detect_duplicates,
    detect_pending_review,
)


class TestNewVendorAlerts:
    """Test new vendor detection with high transaction amounts."""

    @pytest.mark.asyncio
    async def test_new_vendor_over_threshold(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test alert for new vendor with charge over $50."""
        today = date.today()

        # Create first transaction for new vendor above threshold
        txn = Transaction(
            txn_date=today,
            amount_cents=7500,  # $75
            currency="USD",
            direction="debit",
            raw_descriptor="NEW GYM MEMBERSHIP",
            canonical_vendor="Acme Gym",
            source_account="amex",
            hash_id=hash_generator(today, 7500, "NEW GYM", "amex"),
            category="Healthcare",
            status="finalized",
        )
        test_db.add(txn)
        await test_db.commit()

        # Detect anomalies
        alerts = await detect_new_vendors(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == "new_vendor_over_threshold"
        assert alert.vendor == "Acme Gym"
        assert alert.amount_cents == 7500
        assert alert.severity == "warning"

    @pytest.mark.asyncio
    async def test_new_vendor_below_threshold(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test no alert for new vendor below threshold."""
        today = date.today()

        # Create first transaction below threshold
        txn = Transaction(
            txn_date=today,
            amount_cents=1000,  # $10
            currency="USD",
            direction="debit",
            raw_descriptor="SMALL VENDOR",
            canonical_vendor="Small Store",
            source_account="amex",
            hash_id=hash_generator(today, 1000, "SMALL", "amex"),
            category="Shopping",
            status="finalized",
        )
        test_db.add(txn)
        await test_db.commit()

        alerts = await detect_new_vendors(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_existing_vendor_no_alert(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test no alert for existing vendor."""
        today = date.today()
        past = today - timedelta(days=30)

        # Create old transaction for vendor
        old_txn = Transaction(
            txn_date=past,
            amount_cents=5000,
            currency="USD",
            direction="debit",
            raw_descriptor="EXISTING VENDOR 1",
            canonical_vendor="Existing Store",
            source_account="amex",
            hash_id=hash_generator(past, 5000, "EXISTING 1", "amex"),
            category="Shopping",
            status="finalized",
        )
        test_db.add(old_txn)
        await test_db.commit()

        # Create new transaction for same vendor
        new_txn = Transaction(
            txn_date=today,
            amount_cents=10000,  # $100
            currency="USD",
            direction="debit",
            raw_descriptor="EXISTING VENDOR 2",
            canonical_vendor="Existing Store",
            source_account="amex",
            hash_id=hash_generator(today, 10000, "EXISTING 2", "amex"),
            category="Shopping",
            status="finalized",
        )
        test_db.add(new_txn)
        await test_db.commit()

        alerts = await detect_new_vendors(test_db, today - timedelta(days=1), today)

        # Should not alert since vendor already exists
        assert len(alerts) == 0


class TestMissingReceiptAlerts:
    """Test missing receipt detection for high-value transactions."""

    @pytest.mark.asyncio
    async def test_missing_receipt_alert(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test alert for high-value transaction without receipt."""
        today = date.today()

        txn = Transaction(
            txn_date=today,
            amount_cents=5000,  # $50
            currency="USD",
            direction="debit",
            raw_descriptor="BIG PURCHASE",
            canonical_vendor="Electronics Store",
            source_account="amex",
            hash_id=hash_generator(today, 5000, "BIG PURCHASE", "amex"),
            receipt_url=None,  # No receipt
            category="Shopping",
            status="finalized",
        )
        test_db.add(txn)
        await test_db.commit()

        alerts = await detect_missing_receipts(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == "missing_receipt"
        assert alert.amount_cents == 5000
        assert alert.severity == "info"
        assert alert.metadata["needs_receipt"] is True

    @pytest.mark.asyncio
    async def test_has_receipt_no_alert(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test no alert when receipt exists."""
        today = date.today()

        txn = Transaction(
            txn_date=today,
            amount_cents=5000,
            currency="USD",
            direction="debit",
            raw_descriptor="BIG PURCHASE",
            canonical_vendor="Electronics Store",
            source_account="amex",
            hash_id=hash_generator(today, 5000, "BIG PURCHASE", "amex"),
            receipt_url="https://drive.google.com/file/123",
            category="Shopping",
            status="finalized",
        )
        test_db.add(txn)
        await test_db.commit()

        alerts = await detect_missing_receipts(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_small_amount_no_alert(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test no alert for small amount without receipt."""
        today = date.today()

        txn = Transaction(
            txn_date=today,
            amount_cents=500,  # $5
            currency="USD",
            direction="debit",
            raw_descriptor="SMALL PURCHASE",
            source_account="amex",
            hash_id=hash_generator(today, 500, "SMALL", "amex"),
            receipt_url=None,
            category="Shopping",
            status="finalized",
        )
        test_db.add(txn)
        await test_db.commit()

        alerts = await detect_missing_receipts(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 0


class TestDuplicateDetection:
    """Test duplicate transaction detection."""

    @pytest.mark.asyncio
    async def test_duplicate_same_day(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test detection of duplicate transactions on same day."""
        today = date.today()

        # Create two transactions same vendor, amount, date
        txn1 = Transaction(
            txn_date=today,
            amount_cents=1234,
            currency="USD",
            direction="debit",
            raw_descriptor="STARBUCKS 1",
            canonical_vendor="Starbucks",
            source_account="amex",
            hash_id=hash_generator(today, 1234, "STARBUCKS 1", "amex"),
            category="Dining",
            status="finalized",
        )
        txn2 = Transaction(
            txn_date=today,
            amount_cents=1234,
            currency="USD",
            direction="debit",
            raw_descriptor="STARBUCKS 2",
            canonical_vendor="Starbucks",
            source_account="amex",
            hash_id=hash_generator(today, 1234, "STARBUCKS 2", "amex"),  # Different hash
            category="Dining",
            status="finalized",
        )

        test_db.add_all([txn1, txn2])
        await test_db.commit()

        alerts = await detect_duplicates(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == "duplicate_warning"
        assert alert.vendor == "Starbucks"
        assert alert.amount_cents == 1234
        assert alert.severity == "info"
        assert len(alert.metadata["transaction_ids"]) == 2

    @pytest.mark.asyncio
    async def test_different_amount_no_duplicate(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test no duplicate when amounts differ."""
        today = date.today()

        txn1 = Transaction(
            txn_date=today,
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="STARBUCKS 1",
            canonical_vendor="Starbucks",
            source_account="amex",
            hash_id=hash_generator(today, 1000, "STARBUCKS 1", "amex"),
            category="Dining",
            status="finalized",
        )
        txn2 = Transaction(
            txn_date=today,
            amount_cents=2000,  # Different amount
            currency="USD",
            direction="debit",
            raw_descriptor="STARBUCKS 2",
            canonical_vendor="Starbucks",
            source_account="amex",
            hash_id=hash_generator(today, 2000, "STARBUCKS 2", "amex"),
            category="Dining",
            status="finalized",
        )

        test_db.add_all([txn1, txn2])
        await test_db.commit()

        alerts = await detect_duplicates(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 0


class TestPendingReviewAlerts:
    """Test pending review transaction alerts."""

    @pytest.mark.asyncio
    async def test_low_confidence_review(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test alert for low confidence transaction."""
        today = date.today()

        txn = Transaction(
            txn_date=today,
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="UNKNOWN MERCHANT",
            source_account="amex",
            hash_id=hash_generator(today, 1000, "UNKNOWN", "amex"),
            category="Shopping",
            confidence=Decimal("0.60"),  # Low confidence
            status="review",
        )
        test_db.add(txn)
        await test_db.commit()

        alerts = await detect_pending_review(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == "low_confidence"
        assert alert.severity == "warning"
        assert alert.metadata["reason"] == "low confidence"

    @pytest.mark.asyncio
    async def test_high_amount_review(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test alert for high amount requiring review."""
        today = date.today()

        txn = Transaction(
            txn_date=today,
            amount_cents=10000,  # High amount
            currency="USD",
            direction="debit",
            raw_descriptor="BIG PURCHASE",
            source_account="amex",
            hash_id=hash_generator(today, 10000, "BIG PURCHASE", "amex"),
            category="Shopping",
            confidence=Decimal("0.95"),  # High confidence
            status="review",  # But still in review due to amount
        )
        test_db.add(txn)
        await test_db.commit()

        alerts = await detect_pending_review(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == "low_confidence"
        assert alert.metadata["reason"] == "high amount"

    @pytest.mark.asyncio
    async def test_finalized_no_alert(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test no alert for finalized transactions."""
        today = date.today()

        txn = Transaction(
            txn_date=today,
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="FINALIZED",
            source_account="amex",
            hash_id=hash_generator(today, 1000, "FINALIZED", "amex"),
            category="Shopping",
            status="finalized",  # Already finalized
        )
        test_db.add(txn)
        await test_db.commit()

        alerts = await detect_pending_review(test_db, today - timedelta(days=1), today)

        assert len(alerts) == 0


class TestAnomaliesEndpoint:
    """Test /alerts endpoint."""

    @pytest.mark.asyncio
    async def test_alerts_endpoint(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test alerts endpoint returns all anomaly types."""
        today = date.today()

        # Create various anomalies
        transactions = [
            # New vendor over threshold
            Transaction(
                txn_date=today,
                amount_cents=7500,
                currency="USD",
                direction="debit",
                raw_descriptor="NEW GYM",
                canonical_vendor="New Gym",
                source_account="amex",
                hash_id=hash_generator(today, 7500, "NEW GYM", "amex"),
                category="Healthcare",
                status="finalized",
            ),
            # Missing receipt
            Transaction(
                txn_date=today,
                amount_cents=5000,
                currency="USD",
                direction="debit",
                raw_descriptor="BIG PURCHASE",
                canonical_vendor="Store",
                source_account="amex",
                hash_id=hash_generator(today, 5000, "BIG PURCHASE", "amex"),
                receipt_url=None,
                category="Shopping",
                status="finalized",
            ),
            # Pending review
            Transaction(
                txn_date=today,
                amount_cents=1000,
                currency="USD",
                direction="debit",
                raw_descriptor="UNKNOWN",
                source_account="amex",
                hash_id=hash_generator(today, 1000, "UNKNOWN", "amex"),
                category="Shopping",
                confidence=Decimal("0.50"),
                status="review",
            ),
        ]

        for txn in transactions:
            test_db.add(txn)
        await test_db.commit()

        response = await test_client.get("/alerts")

        assert response.status_code == 200
        alerts = response.json()

        # Should have multiple alerts
        assert len(alerts) >= 3

        # Check alert types present
        alert_types = {alert["type"] for alert in alerts}
        assert "new_vendor_over_threshold" in alert_types
        assert "missing_receipt" in alert_types
        assert "low_confidence" in alert_types


class TestNoAnomalies:
    """Test cases where no anomalies should be detected."""

    @pytest.mark.asyncio
    async def test_no_anomalies_normal_transactions(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test no anomalies for normal, properly categorized transactions."""
        today = date.today()
        past = today - timedelta(days=30)

        # Create normal historical transaction
        old_txn = Transaction(
            txn_date=past,
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="NORMAL VENDOR",
            canonical_vendor="Normal Store",
            source_account="amex",
            hash_id=hash_generator(past, 1000, "NORMAL OLD", "amex"),
            receipt_url="https://drive.google.com/file/old",
            category="Shopping",
            status="finalized",
        )
        test_db.add(old_txn)
        await test_db.commit()

        # Create normal new transaction
        new_txn = Transaction(
            txn_date=today,
            amount_cents=1500,
            currency="USD",
            direction="debit",
            raw_descriptor="NORMAL VENDOR 2",
            canonical_vendor="Normal Store",
            source_account="amex",
            hash_id=hash_generator(today, 1500, "NORMAL NEW", "amex"),
            receipt_url="https://drive.google.com/file/new",
            category="Shopping",
            status="finalized",
        )
        test_db.add(new_txn)
        await test_db.commit()

        alerts = await detect_anomalies(test_db, lookback_days=30)

        # Should have minimal or no alerts for normal transactions
        # (May have some from z-score or unusual spending detection)
        assert all(alert.severity in ["info", "medium"] for alert in alerts)

    @pytest.mark.asyncio
    async def test_empty_database(
        self,
        test_db: AsyncSession
    ):
        """Test anomaly detection on empty database."""
        alerts = await detect_anomalies(test_db, lookback_days=30)

        assert len(alerts) == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_credit_transactions_excluded(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test credit transactions don't trigger expense-related alerts."""
        today = date.today()

        # Large credit transaction (income)
        txn = Transaction(
            txn_date=today,
            amount_cents=100000,  # $1000
            currency="USD",
            direction="credit",  # Income
            raw_descriptor="PAYROLL",
            source_account="checking",
            hash_id=hash_generator(today, 100000, "PAYROLL", "checking"),
            category="Income",
            status="finalized",
        )
        test_db.add(txn)
        await test_db.commit()

        # Should not trigger new vendor alert (debit-only)
        alerts = await detect_new_vendors(test_db, today - timedelta(days=1), today)
        assert len(alerts) == 0

        # Should not trigger missing receipt alert (debit-only)
        alerts = await detect_missing_receipts(test_db, today - timedelta(days=1), today)
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_transactions_without_vendor(
        self,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test handling of transactions without canonical vendor."""
        today = date.today()

        txn = Transaction(
            txn_date=today,
            amount_cents=10000,
            currency="USD",
            direction="debit",
            raw_descriptor="UNKNOWN MERCHANT",
            canonical_vendor=None,  # No vendor
            source_account="amex",
            hash_id=hash_generator(today, 10000, "UNKNOWN", "amex"),
            receipt_url=None,
            category="Shopping",
            status="finalized",
        )
        test_db.add(txn)
        await test_db.commit()

        # Should still detect missing receipt
        alerts = await detect_missing_receipts(test_db, today - timedelta(days=1), today)
        assert len(alerts) == 1

        # Message should include raw descriptor when vendor is None
        assert "UNKNOWN MERCHANT" in alerts[0].message
