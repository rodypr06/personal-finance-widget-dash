"""
Tests for transaction categorization logic.

This module tests the categorization system including:
- Rule-based categorization (confidence 1.0)
- OpenAI fallback categorization
- Retry logic for malformed JSON
- Timeout and error handling
- Confidence threshold logic
- Amount threshold for review status
- Manual category finalization
"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, Rule
from app.categorize import categorize_transaction, categorize_with_openai, TAXONOMY
from app.config import settings


class TestCategorizeWithRule:
    """Test categorization using deterministic rules."""

    @pytest.mark.asyncio
    async def test_categorize_with_matching_rule(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction,
        sample_rule: Rule
    ):
        """Test categorization when rule matches (confidence = 1.0)."""
        result = await categorize_transaction(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Dining"
        assert result["subcategory"] == "Coffee"
        assert result["confidence"] == Decimal("1.00")

    @pytest.mark.asyncio
    async def test_categorize_multiple_rules_priority(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test categorization respects rule priority."""
        # Create multiple matching rules
        rule1 = Rule(
            priority=1,
            condition={"contains": "STARBUCKS"},
            action={"category": "First", "subcategory": "Priority 1"},
            active=True,
        )
        rule2 = Rule(
            priority=10,
            condition={"contains": "STARBUCKS"},
            action={"category": "Second", "subcategory": "Priority 10"},
            active=True,
        )

        test_db.add_all([rule1, rule2])
        await test_db.commit()

        result = await categorize_transaction(sample_transaction, test_db)

        assert result["category"] == "First"
        assert result["subcategory"] == "Priority 1"
        assert result["confidence"] == Decimal("1.00")


class TestCategorizeWithOpenAI:
    """Test categorization using OpenAI fallback."""

    @pytest.mark.asyncio
    async def test_categorize_with_openai_success(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test successful OpenAI categorization."""
        # Mock OpenAI response
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

            result = await categorize_transaction(sample_transaction, test_db)

            assert result is not None
            assert result["category"] == "Dining"
            assert result["subcategory"] == "Coffee"
            assert result["confidence"] == Decimal("0.93")
            assert result["vendor"] == "Starbucks"

            # Verify OpenAI was called
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args.kwargs["model"] == settings.OPENAI_MODEL
            assert call_args.kwargs["temperature"] == 0.1

    @pytest.mark.asyncio
    async def test_openai_retry_on_malformed_json(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test retry logic when OpenAI returns malformed JSON."""
        # First call returns malformed JSON, second call succeeds
        mock_response_bad = MagicMock()
        mock_response_bad.choices = [
            MagicMock(message=MagicMock(content="Not valid JSON"))
        ]

        mock_response_good = MagicMock()
        mock_response_good.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "category": "Dining",
                        "subcategory": "Coffee",
                        "confidence": 0.85,
                        "vendor": "Starbucks"
                    })
                )
            )
        ]

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            # Return bad response first, then good response
            mock_create.side_effect = [mock_response_bad, mock_response_good]

            result = await categorize_transaction(sample_transaction, test_db)

            assert result is not None
            assert result["category"] == "Dining"
            assert mock_create.call_count == 2  # Retried once

    @pytest.mark.asyncio
    async def test_openai_max_retries_exceeded(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test default categorization when max retries exceeded."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Invalid JSON forever"))
        ]

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await categorize_transaction(sample_transaction, test_db)

            # Should return default after retries
            assert result is not None
            assert result["category"] == "Shopping"
            assert result["subcategory"] == "Uncategorized"
            assert result["confidence"] == Decimal("0.30")
            assert mock_create.call_count == 3  # max_retries + 1

    @pytest.mark.asyncio
    async def test_openai_timeout_handling(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test timeout handling for OpenAI API."""
        import asyncio

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            # Simulate timeout
            mock_create.side_effect = asyncio.TimeoutError()

            with pytest.raises(Exception, match="OpenAI API timeout"):
                await categorize_with_openai(sample_transaction, max_retries=1)

            assert mock_create.call_count == 2  # Original + 1 retry

    @pytest.mark.asyncio
    async def test_openai_invalid_category(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test handling of invalid category not in taxonomy."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "category": "InvalidCategory",  # Not in TAXONOMY
                        "subcategory": "Test",
                        "confidence": 0.90,
                        "vendor": "Test"
                    })
                )
            )
        ]

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await categorize_with_openai(sample_transaction)

            # Should fall back to "Shopping" and lower confidence
            assert result["category"] == "Shopping"
            assert result["confidence"] == Decimal("0.50")

    @pytest.mark.asyncio
    async def test_openai_rate_limit_retry(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test exponential backoff on rate limit errors."""
        from openai import RateLimitError

        mock_response_good = MagicMock()
        mock_response_good.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "category": "Dining",
                        "subcategory": "Coffee",
                        "confidence": 0.90,
                        "vendor": "Starbucks"
                    })
                )
            )
        ]

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            # First call rate limited, second succeeds
            mock_create.side_effect = [
                RateLimitError("Rate limit", response=MagicMock(), body=None),
                mock_response_good
            ]

            result = await categorize_with_openai(sample_transaction, max_retries=2)

            assert result["category"] == "Dining"
            assert mock_create.call_count == 2


class TestCategorizeEndpoint:
    """Test /categorize/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_categorize_endpoint_with_rule(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        sample_transaction: Transaction,
        sample_rule: Rule
    ):
        """Test categorize endpoint when rule matches."""
        response = await test_client.post(f"/categorize/{sample_transaction.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_transaction.id
        assert data["category"] == "Dining"
        assert data["subcategory"] == "Coffee"
        assert float(data["confidence"]) == 1.0
        assert data["status"] == "finalized"  # High confidence auto-finalized

    @pytest.mark.asyncio
    async def test_categorize_endpoint_low_confidence(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test categorize endpoint sets status=review for low confidence."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "category": "Shopping",
                        "subcategory": "Unknown",
                        "confidence": 0.65,  # Below threshold
                        "vendor": "Unknown Vendor"
                    })
                )
            )
        ]

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            response = await test_client.post(f"/categorize/{sample_transaction.id}")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "review"  # Low confidence requires review
            assert float(data["confidence"]) == 0.65

    @pytest.mark.asyncio
    async def test_categorize_endpoint_high_amount(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        hash_generator
    ):
        """Test categorize endpoint sets status=review for high amounts."""
        # Create transaction with amount > $50
        txn_date = date(2025, 10, 24)
        raw_descriptor = "BIG PURCHASE"
        amount_cents = 15000  # $150
        source_account = "test_account"
        hash_id = hash_generator(txn_date, amount_cents, raw_descriptor, source_account)

        txn = Transaction(
            txn_date=txn_date,
            amount_cents=amount_cents,
            currency="USD",
            direction="debit",
            raw_descriptor=raw_descriptor,
            source_account=source_account,
            hash_id=hash_id,
        )
        test_db.add(txn)
        await test_db.commit()
        await test_db.refresh(txn)

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "category": "Shopping",
                        "subcategory": "Large Purchase",
                        "confidence": 0.95,  # High confidence
                        "vendor": "Big Store"
                    })
                )
            )
        ]

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            response = await test_client.post(f"/categorize/{txn.id}")

            assert response.status_code == 200
            data = response.json()

            # High amount requires review despite high confidence
            assert data["status"] == "review"

    @pytest.mark.asyncio
    async def test_categorize_nonexistent_transaction(
        self,
        test_client: AsyncClient
    ):
        """Test categorize endpoint with invalid transaction ID."""
        response = await test_client.post("/categorize/99999")

        assert response.status_code == 404


class TestFinalizeEndpoint:
    """Test /finalize/{id} endpoint for manual category override."""

    @pytest.mark.asyncio
    async def test_finalize_transaction(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test manual category finalization."""
        # First set to review status
        sample_transaction.status = "review"
        sample_transaction.category = "Shopping"
        sample_transaction.subcategory = "Unknown"
        sample_transaction.confidence = Decimal("0.60")
        await test_db.commit()

        # Finalize with correct category
        payload = {
            "category": "Dining",
            "subcategory": "Coffee"
        }

        response = await test_client.post(
            f"/finalize/{sample_transaction.id}",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

        # Verify database updated
        await test_db.refresh(sample_transaction)
        assert sample_transaction.category == "Dining"
        assert sample_transaction.subcategory == "Coffee"
        assert sample_transaction.status == "finalized"

    @pytest.mark.asyncio
    async def test_finalize_nonexistent_transaction(
        self,
        test_client: AsyncClient
    ):
        """Test finalize endpoint with invalid transaction ID."""
        payload = {
            "category": "Dining",
            "subcategory": "Coffee"
        }

        response = await test_client.post("/finalize/99999", json=payload)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_finalize_missing_category(
        self,
        test_client: AsyncClient,
        sample_transaction: Transaction
    ):
        """Test finalize endpoint with missing category."""
        payload = {
            "subcategory": "Coffee"
            # Missing category
        }

        response = await test_client.post(
            f"/finalize/{sample_transaction.id}",
            json=payload
        )

        assert response.status_code == 422  # Validation error


class TestConfidenceScoring:
    """Test confidence score handling and thresholds."""

    @pytest.mark.asyncio
    async def test_confidence_clamping(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test confidence scores are clamped to [0, 1] range."""
        # Mock response with out-of-range confidence
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "category": "Dining",
                        "subcategory": "Coffee",
                        "confidence": 1.5,  # > 1.0
                        "vendor": "Starbucks"
                    })
                )
            )
        ]

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await categorize_with_openai(sample_transaction)

            # Confidence should be clamped to 1.0
            assert result["confidence"] == Decimal("1.00")

    @pytest.mark.asyncio
    async def test_confidence_threshold_boundary(
        self,
        test_client: AsyncClient,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test confidence threshold boundary (0.80)."""
        # Test exactly at threshold
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "category": "Dining",
                        "subcategory": "Coffee",
                        "confidence": 0.80,  # Exactly at threshold
                        "vendor": "Starbucks"
                    })
                )
            )
        ]

        with patch("app.categorize.openai_client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            response = await test_client.post(f"/categorize/{sample_transaction.id}")

            data = response.json()
            # At threshold should finalize (>=)
            assert data["status"] == "finalized"
