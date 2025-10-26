"""
Tests for rules engine and deterministic categorization.

This module tests the rules-based categorization logic including:
- MCC-based matching
- Descriptor pattern matching (contains, regex)
- Amount range filtering
- Account matching
- Complex conditions (AND/OR logic)
- Rule priority ordering
- Inactive rule handling
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, Rule
from app.rules import apply_rules, evaluate_condition


class TestRuleMatching:
    """Test individual rule matching conditions."""

    @pytest.mark.asyncio
    async def test_mcc_exact_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test exact MCC matching."""
        # Create rule matching transaction's MCC
        rule = Rule(
            priority=1,
            condition={"mcc": "5814"},
            action={"category": "Dining", "subcategory": "Coffee"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        # Apply rules
        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Dining"
        assert result["subcategory"] == "Coffee"

    @pytest.mark.asyncio
    async def test_mcc_in_list_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test MCC in list matching."""
        # Create rule with MCC list
        rule = Rule(
            priority=1,
            condition={"mcc_in": ["5411", "5814", "5422"]},
            action={"category": "Matched", "subcategory": "List"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Matched"

    @pytest.mark.asyncio
    async def test_descriptor_contains_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test descriptor contains matching (case-insensitive)."""
        rule = Rule(
            priority=1,
            condition={"contains": "starbucks"},  # Lowercase
            action={"category": "Dining", "subcategory": "Coffee"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Dining"

    @pytest.mark.asyncio
    async def test_descriptor_regex_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test descriptor regex matching."""
        rule = Rule(
            priority=1,
            condition={"regex": r"^STARBUCKS\s+\d+$"},
            action={"category": "Dining", "subcategory": "Coffee"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Dining"

    @pytest.mark.asyncio
    async def test_amount_range_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test amount range matching."""
        # Transaction amount is 784 cents
        rule = Rule(
            priority=1,
            condition={"amount_range": [500, 1000]},
            action={"category": "Small Purchase", "subcategory": "Under $10"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Small Purchase"

    @pytest.mark.asyncio
    async def test_account_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test account matching."""
        rule = Rule(
            priority=1,
            condition={"account": "amex_blue_cash"},
            action={"category": "Amex Transaction", "subcategory": "Blue Cash"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Amex Transaction"

    @pytest.mark.asyncio
    async def test_direction_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test direction matching."""
        rule = Rule(
            priority=1,
            condition={"direction": "debit"},
            action={"category": "Expense", "subcategory": "Debit"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Expense"


class TestComplexConditions:
    """Test complex logical conditions (AND/OR)."""

    @pytest.mark.asyncio
    async def test_and_condition_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test AND condition with all conditions matching."""
        rule = Rule(
            priority=1,
            condition={
                "and": [
                    {"contains": "STARBUCKS"},
                    {"mcc": "5814"},
                    {"amount_range": [0, 2000]}
                ]
            },
            action={"category": "Coffee", "subcategory": "Starbucks"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Coffee"

    @pytest.mark.asyncio
    async def test_and_condition_partial_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test AND condition with one condition not matching."""
        rule = Rule(
            priority=1,
            condition={
                "and": [
                    {"contains": "STARBUCKS"},
                    {"mcc": "9999"},  # Won't match
                ]
            },
            action={"category": "Should Not Match"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is None

    @pytest.mark.asyncio
    async def test_or_condition_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test OR condition with one condition matching."""
        rule = Rule(
            priority=1,
            condition={
                "or": [
                    {"contains": "WALMART"},  # Won't match
                    {"mcc": "5814"},  # Will match
                    {"amount_range": [10000, 99999]}  # Won't match
                ]
            },
            action={"category": "Matched", "subcategory": "Or"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Matched"

    @pytest.mark.asyncio
    async def test_or_condition_no_match(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test OR condition with no conditions matching."""
        rule = Rule(
            priority=1,
            condition={
                "or": [
                    {"contains": "WALMART"},
                    {"mcc": "9999"},
                    {"amount_range": [10000, 99999]}
                ]
            },
            action={"category": "Should Not Match"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is None

    @pytest.mark.asyncio
    async def test_nested_logic(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test nested AND/OR logic."""
        rule = Rule(
            priority=1,
            condition={
                "and": [
                    {
                        "or": [
                            {"contains": "STARBUCKS"},
                            {"contains": "DUNKIN"}
                        ]
                    },
                    {"mcc": "5814"}
                ]
            },
            action={"category": "Coffee", "subcategory": "Any"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Coffee"


class TestRulePriority:
    """Test rule priority ordering."""

    @pytest.mark.asyncio
    async def test_priority_ordering(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test rules are evaluated in priority order (lower = higher priority)."""
        # Create multiple matching rules with different priorities
        rule_low_priority = Rule(
            priority=100,
            condition={"contains": "STARBUCKS"},
            action={"category": "Low Priority", "subcategory": "100"},
            active=True,
        )
        rule_high_priority = Rule(
            priority=1,
            condition={"contains": "STARBUCKS"},
            action={"category": "High Priority", "subcategory": "1"},
            active=True,
        )
        rule_medium_priority = Rule(
            priority=50,
            condition={"contains": "STARBUCKS"},
            action={"category": "Medium Priority", "subcategory": "50"},
            active=True,
        )

        test_db.add_all([rule_low_priority, rule_high_priority, rule_medium_priority])
        await test_db.commit()

        # Apply rules - should match highest priority (lowest number)
        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "High Priority"
        assert result["subcategory"] == "1"

    @pytest.mark.asyncio
    async def test_inactive_rule_skipped(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test inactive rules are not evaluated."""
        # Create inactive rule
        inactive_rule = Rule(
            priority=1,
            condition={"contains": "STARBUCKS"},
            action={"category": "Inactive", "subcategory": "Should Not Match"},
            active=False,
        )
        # Create active rule with lower priority
        active_rule = Rule(
            priority=10,
            condition={"contains": "STARBUCKS"},
            action={"category": "Active", "subcategory": "Should Match"},
            active=True,
        )

        test_db.add_all([inactive_rule, active_rule])
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is not None
        assert result["category"] == "Active"


class TestNoRuleMatch:
    """Test cases where no rules match."""

    @pytest.mark.asyncio
    async def test_no_rules(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test when no rules exist in database."""
        result = await apply_rules(sample_transaction, test_db)

        assert result is None

    @pytest.mark.asyncio
    async def test_no_matching_rules(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test when rules exist but none match."""
        rule = Rule(
            priority=1,
            condition={"contains": "WALMART"},
            action={"category": "Groceries"},
            active=True,
        )
        test_db.add(rule)
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is None

    @pytest.mark.asyncio
    async def test_all_rules_inactive(
        self,
        test_db: AsyncSession,
        sample_transaction: Transaction
    ):
        """Test when all rules are inactive."""
        rule1 = Rule(
            priority=1,
            condition={"contains": "STARBUCKS"},
            action={"category": "Inactive 1"},
            active=False,
        )
        rule2 = Rule(
            priority=2,
            condition={"mcc": "5814"},
            action={"category": "Inactive 2"},
            active=False,
        )

        test_db.add_all([rule1, rule2])
        await test_db.commit()

        result = await apply_rules(sample_transaction, test_db)

        assert result is None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_evaluate_condition_missing_mcc(self):
        """Test MCC condition when transaction has no MCC."""
        txn = Transaction(
            txn_date=date(2025, 10, 24),
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="TEST",
            source_account="test",
            hash_id="test_hash",
            mcc=None,  # No MCC
        )

        condition = {"mcc": "5814"}

        result = evaluate_condition(txn, condition)

        assert result is False

    def test_evaluate_condition_invalid_regex(self):
        """Test invalid regex pattern raises error."""
        txn = Transaction(
            txn_date=date(2025, 10, 24),
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="TEST",
            source_account="test",
            hash_id="test_hash",
        )

        # Invalid regex pattern
        condition = {"regex": "[[[invalid"}

        with pytest.raises(ValueError, match="Invalid regex pattern"):
            evaluate_condition(txn, condition)

    def test_evaluate_condition_empty_condition(self):
        """Test empty condition returns False."""
        txn = Transaction(
            txn_date=date(2025, 10, 24),
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="TEST",
            source_account="test",
            hash_id="test_hash",
        )

        condition = {}

        result = evaluate_condition(txn, condition)

        assert result is False

    def test_evaluate_condition_unknown_type(self):
        """Test unknown condition type returns False."""
        txn = Transaction(
            txn_date=date(2025, 10, 24),
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="TEST",
            source_account="test",
            hash_id="test_hash",
        )

        condition = {"unknown_type": "value"}

        result = evaluate_condition(txn, condition)

        assert result is False

    def test_evaluate_condition_all_alias(self):
        """Test 'all' as alias for 'and'."""
        txn = Transaction(
            txn_date=date(2025, 10, 24),
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="STARBUCKS 1234",
            source_account="test",
            hash_id="test_hash",
            mcc="5814",
        )

        condition = {
            "all": [
                {"contains": "STARBUCKS"},
                {"mcc": "5814"}
            ]
        }

        result = evaluate_condition(txn, condition)

        assert result is True

    def test_evaluate_condition_any_alias(self):
        """Test 'any' as alias for 'or'."""
        txn = Transaction(
            txn_date=date(2025, 10, 24),
            amount_cents=1000,
            currency="USD",
            direction="debit",
            raw_descriptor="STARBUCKS 1234",
            source_account="test",
            hash_id="test_hash",
        )

        condition = {
            "any": [
                {"contains": "WALMART"},
                {"contains": "STARBUCKS"}
            ]
        }

        result = evaluate_condition(txn, condition)

        assert result is True
