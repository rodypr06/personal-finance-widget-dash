"""
Transaction categorization service using rules and OpenAI.

This module provides intelligent categorization using OpenAI's API when
deterministic rules don't match. It includes retry logic, JSON parsing,
and confidence scoring.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

import openai
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction
from app.rules import apply_rules
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Fixed taxonomy for personal finance
TAXONOMY = [
    "Groceries",
    "Dining",
    "Transport",
    "Fuel",
    "Utilities",
    "Rent/Mortgage",
    "Internet",
    "Mobile",
    "Subscriptions",
    "Shopping",
    "Healthcare",
    "Pets",
    "Gifts/Charity",
    "Entertainment",
    "Travel-Air",
    "Travel-Hotel",
    "Travel-Other",
    "Income",
    "Transfers",
    "Savings"
]


async def categorize_transaction(
    transaction: Transaction,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Categorize a transaction using rules first, then OpenAI fallback.

    Args:
        transaction: Transaction to categorize
        db: Database session

    Returns:
        Dict with category, subcategory, confidence, vendor

    Process:
        1. Try deterministic rules (confidence = 1.0)
        2. If no rule matches, use OpenAI (confidence from model)
        3. Return categorization result
    """
    # Try rules first
    rule_result = await apply_rules(transaction, db)

    if rule_result:
        logger.info(f"Transaction {transaction.id} categorized by rule: {rule_result}")
        return {
            "category": rule_result.get("category"),
            "subcategory": rule_result.get("subcategory"),
            "confidence": Decimal("1.00"),
            "vendor": transaction.canonical_vendor
        }

    # Fallback to OpenAI
    logger.info(f"Transaction {transaction.id} using OpenAI categorization")
    ai_result = await categorize_with_openai(transaction)

    return ai_result


async def categorize_with_openai(
    transaction: Transaction,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Categorize transaction using OpenAI API with retry logic.

    Args:
        transaction: Transaction to categorize
        max_retries: Maximum number of retry attempts on JSON parse errors

    Returns:
        Dict with category, subcategory, confidence, vendor

    Raises:
        Exception: On API errors or invalid responses after retries
    """
    system_prompt = """You classify personal finance transactions into a fixed taxonomy.
Prefer deterministic mapping from known vendors/MCCs; otherwise infer sensibly.
Return strict JSON with: category, subcategory, confidence (0-1), vendor.
Only return valid JSON, no additional text or formatting."""

    user_prompt = f"""Taxonomy = {json.dumps(TAXONOMY)}

Transaction:
date={transaction.txn_date}
amount={transaction.amount_cents / 100:.2f} {transaction.currency} ({transaction.direction})
descriptor="{transaction.raw_descriptor}"
memo="{transaction.memo or ''}"
mcc="{transaction.mcc or ''}"

Examples:
- "NETFLIX.COM" → {{"category":"Subscriptions","subcategory":"Streaming","confidence":0.97,"vendor":"Netflix"}}
- "CASEY'S STORE 1234" → {{"category":"Fuel","subcategory":"Gas Station","confidence":0.92,"vendor":"Casey's"}}
- "HY-VEE 1234" → {{"category":"Groceries","subcategory":"Supermarket","confidence":0.95,"vendor":"Hy-Vee"}}
- "STARBUCKS 5678" → {{"category":"Dining","subcategory":"Coffee","confidence":0.93,"vendor":"Starbucks"}}

Now classify this transaction. Return only valid JSON."""

    for attempt in range(max_retries + 1):
        try:
            logger.debug(
                f"Calling OpenAI API (attempt {attempt + 1}/{max_retries + 1})",
                extra={
                    "transaction_id": transaction.id,
                    "model": settings.OPENAI_MODEL,
                    "attempt": attempt + 1,
                },
            )

            # Call OpenAI with timeout
            response = await asyncio.wait_for(
                openai_client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent results
                    max_tokens=150,
                    response_format={"type": "json_object"}
                ),
                timeout=30.0  # 30 second timeout
            )

            result_text = response.choices[0].message.content
            logger.debug(
                f"OpenAI response: {result_text}",
                extra={"transaction_id": transaction.id, "response": result_text},
            )

            # Parse and validate response
            result = _parse_openai_response(result_text)

            # Validate required fields
            if not result.get("category"):
                raise ValueError("Missing required field 'category' in response")

            # Ensure confidence is Decimal and in valid range
            confidence = float(result.get("confidence", 0.5))
            result["confidence"] = Decimal(str(max(0.0, min(1.0, confidence))))

            # Validate category is in taxonomy
            if result["category"] not in TAXONOMY:
                logger.warning(
                    f"OpenAI returned invalid category: {result['category']}, using 'Shopping'",
                    extra={"invalid_category": result["category"]},
                )
                result["category"] = "Shopping"
                result["confidence"] = Decimal("0.50")

            logger.info(
                f"Transaction {transaction.id} categorized by OpenAI",
                extra={
                    "transaction_id": transaction.id,
                    "category": result["category"],
                    "confidence": result.get("confidence"),
                },
            )

            return result

        except asyncio.TimeoutError:
            logger.error(
                f"OpenAI API timeout on attempt {attempt + 1}",
                extra={"transaction_id": transaction.id, "attempt": attempt + 1},
            )
            if attempt == max_retries:
                raise Exception("OpenAI API timeout after retries")
            await asyncio.sleep(1)  # Brief pause before retry

        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON response on attempt {attempt + 1}: {e}",
                extra={
                    "transaction_id": transaction.id,
                    "attempt": attempt + 1,
                    "error": str(e),
                },
            )
            if attempt == max_retries:
                # Return default on final failure
                logger.error("Max retries reached, returning default categorization")
                return {
                    "category": "Shopping",
                    "subcategory": "Uncategorized",
                    "confidence": Decimal("0.30"),
                    "vendor": transaction.canonical_vendor or transaction.raw_descriptor
                }
            await asyncio.sleep(1)

        except openai.RateLimitError as e:
            logger.warning(
                f"Rate limit hit on attempt {attempt + 1}, retrying",
                extra={"transaction_id": transaction.id, "attempt": attempt + 1},
            )
            if attempt == max_retries:
                raise
            # Exponential backoff for rate limits
            await asyncio.sleep(2 ** attempt)

        except openai.APIError as e:
            logger.error(
                f"OpenAI API error on attempt {attempt + 1}: {e}",
                extra={
                    "transaction_id": transaction.id,
                    "attempt": attempt + 1,
                    "error": str(e),
                },
                exc_info=True,
            )
            if attempt == max_retries:
                return {
                    "category": "Shopping",
                    "subcategory": "Uncategorized",
                    "confidence": Decimal("0.30"),
                    "vendor": transaction.canonical_vendor or transaction.raw_descriptor
                }
            await asyncio.sleep(2 ** attempt)

    # Should never reach here, but safety fallback
    return {
        "category": "Shopping",
        "subcategory": "Uncategorized",
        "confidence": Decimal("0.30"),
        "vendor": transaction.canonical_vendor or transaction.raw_descriptor
    }


def _parse_openai_response(content: str) -> Dict:
    """
    Parse and validate OpenAI JSON response.

    Args:
        content: JSON string from OpenAI

    Returns:
        Parsed dictionary with category, subcategory, confidence, vendor

    Raises:
        json.JSONDecodeError: If content is not valid JSON
        ValueError: If required fields are missing
    """
    # Try to extract JSON if wrapped in markdown code blocks
    content = content.strip()
    if content.startswith("```"):
        # Remove markdown code fences
        lines = content.split("\n")
        content = "\n".join(
            line for line in lines if not line.startswith("```")
        )

    result = json.loads(content)

    # Validate confidence is in valid range
    if "confidence" in result:
        confidence = float(result["confidence"])
        if not 0.0 <= confidence <= 1.0:
            logger.warning(
                f"Confidence {confidence} out of range, clamping to [0, 1]"
            )
            result["confidence"] = max(0.0, min(1.0, confidence))

    return result
