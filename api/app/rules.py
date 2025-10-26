"""
Deterministic rule engine for transaction categorization.

This module provides the rules-based categorization system that evaluates
transactions against a set of deterministic rules stored in the database.
Rules are evaluated in priority order until a match is found.
"""
import logging
import re
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Transaction, Rule

logger = logging.getLogger(__name__)


async def apply_rules(
    transaction: Transaction,
    db: AsyncSession
) -> Optional[Dict[str, Any]]:
    """
    Apply deterministic rules to categorize a transaction.

    Evaluates rules in priority order (lowest priority number first) until
    a matching rule is found. Supports multiple condition types:
    - mcc: Exact MCC match
    - mcc_in: MCC in list of values
    - regex: Regex match on raw_descriptor (case-insensitive)
    - contains: Substring match on raw_descriptor (case-insensitive)
    - direction: Match transaction direction (debit/credit)
    - amount_range: Amount falls within [min, max] range in cents
    - account: Match source_account
    - and/or: Logical operators for complex conditions

    Args:
        transaction: Transaction to categorize
        db: Database session

    Returns:
        Action dict with category/subcategory if rule matches, None otherwise
        Example: {"category": "Groceries", "subcategory": "Supermarket"}

    Raises:
        Exception: Database errors or malformed rule conditions
    """
    try:
        # Load active rules ordered by priority
        result = await db.execute(
            select(Rule)
            .where(Rule.active == True)
            .order_by(Rule.priority.asc())
        )
        rules = result.scalars().all()

        logger.debug(
            f"Evaluating {len(rules)} active rules for transaction {transaction.id}",
            extra={
                "transaction_id": transaction.id,
                "descriptor": transaction.raw_descriptor,
                "mcc": transaction.mcc,
                "amount_cents": transaction.amount_cents,
            },
        )

        # Evaluate each rule until match found
        for rule in rules:
            try:
                if evaluate_condition(transaction, rule.condition):
                    logger.info(
                        f"Rule {rule.id} (priority {rule.priority}) matched transaction {transaction.id}",
                        extra={
                            "rule_id": rule.id,
                            "transaction_id": transaction.id,
                            "condition": rule.condition,
                            "action": rule.action,
                        },
                    )
                    return rule.action
            except Exception as e:
                logger.error(
                    f"Error evaluating rule {rule.id}: {e}",
                    extra={
                        "rule_id": rule.id,
                        "transaction_id": transaction.id,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                continue

        logger.debug(
            f"No matching rule found for transaction {transaction.id}",
            extra={"transaction_id": transaction.id},
        )
        return None

    except Exception as e:
        logger.error(
            f"Error applying rules to transaction {transaction.id}: {e}",
            extra={"transaction_id": transaction.id, "error": str(e)},
            exc_info=True,
        )
        raise


def evaluate_condition(
    transaction: Transaction,
    condition: Dict[str, Any]
) -> bool:
    """
    Evaluate a rule condition against a transaction.

    Args:
        transaction: Transaction to check
        condition: Condition dict

    Returns:
        True if condition matches, False otherwise

    Raises:
        ValueError: If condition format is invalid

    Supported conditions:
        - {"contains": "NETFLIX"}: Descriptor contains substring (case-insensitive)
        - {"regex": "^STARBUCKS.*"}: Descriptor matches regex (case-insensitive)
        - {"mcc": "5411"}: MCC equals value
        - {"mcc_in": ["5411", "5422"]}: MCC in list
        - {"amount_range": [1000, 50000]}: Amount in cents in range [min, max]
        - {"account": "amex_blue_cash"}: Account matches
        - {"direction": "debit"}: Direction matches
        - {"and": [cond1, cond2]}: All conditions must match
        - {"or": [cond1, cond2]}: Any condition must match
        - {"all": [cond1, cond2]}: Alias for "and"
        - {"any": [cond1, cond2]}: Alias for "or"
    """
    # Handle logical operators
    if "and" in condition or "all" in condition:
        conditions_list = condition.get("and") or condition.get("all")
        return all(evaluate_condition(transaction, c) for c in conditions_list)

    if "or" in condition or "any" in condition:
        conditions_list = condition.get("or") or condition.get("any")
        return any(evaluate_condition(transaction, c) for c in conditions_list)

    # Contains check (case-insensitive)
    if "contains" in condition:
        search_term = condition["contains"].lower()
        return search_term in transaction.raw_descriptor.lower()

    # Regex check (case-insensitive)
    if "regex" in condition:
        pattern = condition["regex"]
        try:
            return bool(re.search(pattern, transaction.raw_descriptor, re.IGNORECASE))
        except re.error as e:
            logger.error(
                f"Invalid regex pattern: {pattern}",
                extra={"pattern": pattern, "error": str(e)},
            )
            raise ValueError(f"Invalid regex pattern: {pattern}") from e

    # MCC exact match
    if "mcc" in condition:
        if not transaction.mcc:
            return False
        return transaction.mcc == condition["mcc"]

    # MCC in list
    if "mcc_in" in condition:
        if not transaction.mcc:
            return False
        return transaction.mcc in condition["mcc_in"]

    # Amount range [min, max] in cents
    if "amount_range" in condition:
        min_amt, max_amt = condition["amount_range"]
        return min_amt <= transaction.amount_cents <= max_amt

    # Account match
    if "account" in condition:
        return transaction.source_account == condition["account"]

    # Direction match
    if "direction" in condition:
        return transaction.direction == condition["direction"]

    # Unknown condition type
    logger.warning(
        f"Unknown condition type: {list(condition.keys())}",
        extra={"condition": condition},
    )
    return False
