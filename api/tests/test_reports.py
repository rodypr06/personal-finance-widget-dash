"""
Tests for reporting and summary endpoints.

This module tests the reporting functionality including:
- Monthly summary aggregation
- Date range filtering
- Top vendors calculation
- Timeseries data generation
- Category totals and income/expense tracking
- Empty result handling
"""
from datetime import date, timedelta
from decimal import Decimal
import hashlib

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction


class TestMonthlySummary:
    """Test monthly summary report generation."""

    @pytest.mark.asyncio
    async def test_monthly_summary_basic(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test basic monthly summary with transactions."""
        # Create sample transactions for October 2025
        month = "2025-10"
        transactions = [
            # Groceries
            Transaction(
                txn_date=date(2025, 10, 1),
                amount_cents=4500,
                currency="USD",
                direction="debit",
                raw_descriptor="HY-VEE 1",
                canonical_vendor="Hy-Vee",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, 1), 4500, "HY-VEE 1", "amex"),
                category="Groceries",
                subcategory="Supermarket",
                status="finalized",
            ),
            Transaction(
                txn_date=date(2025, 10, 5),
                amount_cents=6700,
                currency="USD",
                direction="debit",
                raw_descriptor="HY-VEE 2",
                canonical_vendor="Hy-Vee",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, 5), 6700, "HY-VEE 2", "amex"),
                category="Groceries",
                subcategory="Supermarket",
                status="finalized",
            ),
            # Dining
            Transaction(
                txn_date=date(2025, 10, 3),
                amount_cents=1200,
                currency="USD",
                direction="debit",
                raw_descriptor="STARBUCKS",
                canonical_vendor="Starbucks",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, 3), 1200, "STARBUCKS", "amex"),
                category="Dining",
                subcategory="Coffee",
                status="finalized",
            ),
            # Income
            Transaction(
                txn_date=date(2025, 10, 15),
                amount_cents=500000,
                currency="USD",
                direction="credit",
                raw_descriptor="PAYROLL",
                source_account="checking",
                hash_id=hash_generator(date(2025, 10, 15), 500000, "PAYROLL", "checking"),
                category="Income",
                subcategory="Salary",
                status="finalized",
            ),
        ]

        for txn in transactions:
            test_db.add(txn)
        await test_db.commit()

        # Get summary
        response = await test_client.get(f"/report/summary?month={month}")

        assert response.status_code == 200
        data = response.json()

        assert data["period"] == month
        assert data["total_income_cents"] == 500000
        assert data["total_expense_cents"] == 12400  # 4500 + 6700 + 1200
        assert data["net_savings_cents"] == 487600

        # Check category totals
        category_totals = {item["category"]: item["amount_cents"] for item in data["totals_by_category"]}
        assert category_totals["Groceries"] == 11200
        assert category_totals["Dining"] == 1200

        # Check top vendors
        top_vendors = {item["vendor"]: item["amount_cents"] for item in data["top_vendors"]}
        assert "Hy-Vee" in top_vendors
        assert top_vendors["Hy-Vee"] == 11200

        # Check timeseries
        assert len(data["timeseries"]) > 0

    @pytest.mark.asyncio
    async def test_date_range_filter(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test custom date range filtering."""
        # Create transactions across multiple months
        transactions = [
            Transaction(
                txn_date=date(2025, 9, 15),
                amount_cents=1000,
                currency="USD",
                direction="debit",
                raw_descriptor="SEPT TRANSACTION",
                source_account="amex",
                hash_id=hash_generator(date(2025, 9, 15), 1000, "SEPT", "amex"),
                category="Shopping",
                status="finalized",
            ),
            Transaction(
                txn_date=date(2025, 10, 15),
                amount_cents=2000,
                currency="USD",
                direction="debit",
                raw_descriptor="OCT TRANSACTION",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, 15), 2000, "OCT", "amex"),
                category="Shopping",
                status="finalized",
            ),
            Transaction(
                txn_date=date(2025, 11, 15),
                amount_cents=3000,
                currency="USD",
                direction="debit",
                raw_descriptor="NOV TRANSACTION",
                source_account="amex",
                hash_id=hash_generator(date(2025, 11, 15), 3000, "NOV", "amex"),
                category="Shopping",
                status="finalized",
            ),
        ]

        for txn in transactions:
            test_db.add(txn)
        await test_db.commit()

        # Query October only
        response = await test_client.get("/report/summary?month=2025-10")

        assert response.status_code == 200
        data = response.json()

        # Should only include October transaction
        assert data["total_expense_cents"] == 2000

    @pytest.mark.asyncio
    async def test_top_vendors_limit(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test top vendors are limited to top 10."""
        # Create 15 different vendors
        for i in range(15):
            txn = Transaction(
                txn_date=date(2025, 10, i + 1),
                amount_cents=(15 - i) * 100,  # Descending amounts
                currency="USD",
                direction="debit",
                raw_descriptor=f"VENDOR {i}",
                canonical_vendor=f"Vendor{i}",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, i + 1), (15 - i) * 100, f"VENDOR {i}", "amex"),
                category="Shopping",
                status="finalized",
            )
            test_db.add(txn)
        await test_db.commit()

        response = await test_client.get("/report/summary?month=2025-10")

        assert response.status_code == 200
        data = response.json()

        # Should return at most 10 vendors
        assert len(data["top_vendors"]) <= 10

        # Verify they're in descending order
        amounts = [v["amount_cents"] for v in data["top_vendors"]]
        assert amounts == sorted(amounts, reverse=True)

    @pytest.mark.asyncio
    async def test_timeseries_daily_aggregation(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test daily spending timeseries aggregation."""
        # Create multiple transactions on same day
        txn_date = date(2025, 10, 15)
        transactions = [
            Transaction(
                txn_date=txn_date,
                amount_cents=1000,
                currency="USD",
                direction="debit",
                raw_descriptor="TXN 1",
                source_account="amex",
                hash_id=hash_generator(txn_date, 1000, "TXN 1", "amex"),
                category="Shopping",
                status="finalized",
            ),
            Transaction(
                txn_date=txn_date,
                amount_cents=2000,
                currency="USD",
                direction="debit",
                raw_descriptor="TXN 2",
                source_account="amex",
                hash_id=hash_generator(txn_date, 2000, "TXN 2", "amex"),
                category="Dining",
                status="finalized",
            ),
        ]

        for txn in transactions:
            test_db.add(txn)
        await test_db.commit()

        response = await test_client.get("/report/summary?month=2025-10")

        assert response.status_code == 200
        data = response.json()

        # Find the timeseries entry for this date
        timeseries_entry = next(
            (item for item in data["timeseries"] if item["date"] == str(txn_date)),
            None
        )

        assert timeseries_entry is not None
        assert timeseries_entry["sum_cents"] == 3000  # Aggregated


class TestEmptyResults:
    """Test handling of empty result sets."""

    @pytest.mark.asyncio
    async def test_empty_month(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test summary for month with no transactions."""
        response = await test_client.get("/report/summary?month=2099-12")

        assert response.status_code == 200
        data = response.json()

        assert data["period"] == "2099-12"
        assert data["total_income_cents"] == 0
        assert data["total_expense_cents"] == 0
        assert data["net_savings_cents"] == 0
        assert data["totals_by_category"] == []
        assert data["top_vendors"] == []
        assert data["timeseries"] == []

    @pytest.mark.asyncio
    async def test_only_uncategorized_transactions(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test summary with only uncategorized transactions."""
        txn = Transaction(
            txn_date=date(2025, 10, 15),
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="UNCATEGORIZED",
            source_account="amex",
            hash_id=hash_generator(date(2025, 10, 15), 1000, "UNCATEGORIZED", "amex"),
            category=None,  # No category
            status="ingested",
        )
        test_db.add(txn)
        await test_db.commit()

        response = await test_client.get("/report/summary?month=2025-10")

        assert response.status_code == 200
        data = response.json()

        # Should still show total expenses
        assert data["total_expense_cents"] == 1000
        # But no category totals
        assert data["totals_by_category"] == []


class TestCategoryFilter:
    """Test filtering by specific category."""

    @pytest.mark.asyncio
    async def test_filter_by_category(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test filtering summary by specific category."""
        transactions = [
            Transaction(
                txn_date=date(2025, 10, 1),
                amount_cents=1000,
                currency="USD",
                direction="debit",
                raw_descriptor="GROCERIES",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, 1), 1000, "GROCERIES", "amex"),
                category="Groceries",
                status="finalized",
            ),
            Transaction(
                txn_date=date(2025, 10, 2),
                amount_cents=2000,
                currency="USD",
                direction="debit",
                raw_descriptor="DINING",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, 2), 2000, "DINING", "amex"),
                category="Dining",
                status="finalized",
            ),
        ]

        for txn in transactions:
            test_db.add(txn)
        await test_db.commit()

        # Filter by Groceries only
        response = await test_client.get("/report/summary?month=2025-10&category=Groceries")

        assert response.status_code == 200
        data = response.json()

        # Should only include Groceries
        assert len(data["totals_by_category"]) == 1
        assert data["totals_by_category"][0]["category"] == "Groceries"
        assert data["total_expense_cents"] == 1000


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_invalid_month_format(
        self,
        test_client: AsyncClient
    ):
        """Test invalid month format."""
        response = await test_client.get("/report/summary?month=invalid")

        # Should return error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_future_month(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test querying future month."""
        future_date = date.today() + timedelta(days=365)
        future_month = future_date.strftime("%Y-%m")

        response = await test_client.get(f"/report/summary?month={future_month}")

        assert response.status_code == 200
        data = response.json()

        # Should return empty results
        assert data["total_expense_cents"] == 0

    @pytest.mark.asyncio
    async def test_transactions_multiple_currencies(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test handling of multiple currency transactions."""
        transactions = [
            Transaction(
                txn_date=date(2025, 10, 1),
                amount_cents=1000,
                currency="USD",
                direction="debit",
                raw_descriptor="USD TXN",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, 1), 1000, "USD TXN", "amex"),
                category="Shopping",
                status="finalized",
            ),
            Transaction(
                txn_date=date(2025, 10, 2),
                amount_cents=2000,
                currency="EUR",
                direction="debit",
                raw_descriptor="EUR TXN",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, 2), 2000, "EUR TXN", "amex"),
                category="Shopping",
                status="finalized",
            ),
        ]

        for txn in transactions:
            test_db.add(txn)
        await test_db.commit()

        response = await test_client.get("/report/summary?month=2025-10")

        assert response.status_code == 200
        data = response.json()

        # Note: Current implementation treats all currencies the same
        # This test documents the current behavior
        assert data["total_expense_cents"] == 3000

    @pytest.mark.asyncio
    async def test_very_large_dataset(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test performance with large number of transactions."""
        # Create 100 transactions
        for i in range(100):
            txn = Transaction(
                txn_date=date(2025, 10, (i % 28) + 1),
                amount_cents=i * 100,
                currency="USD",
                direction="debit",
                raw_descriptor=f"TXN {i}",
                source_account="amex",
                hash_id=hash_generator(date(2025, 10, (i % 28) + 1), i * 100, f"TXN {i}", "amex"),
                category="Shopping",
                status="finalized",
            )
            test_db.add(txn)
        await test_db.commit()

        response = await test_client.get("/report/summary?month=2025-10")

        assert response.status_code == 200
        data = response.json()

        # Verify aggregation worked correctly
        expected_total = sum(i * 100 for i in range(100))
        assert data["total_expense_cents"] == expected_total
