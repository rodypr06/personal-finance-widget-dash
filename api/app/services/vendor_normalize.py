"""
Vendor normalization service for transaction merchant cleanup.

This module provides intelligent vendor name normalization by matching
raw transaction descriptors against known canonical vendor names and aliases.
"""
import logging
import re
from functools import lru_cache
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Vendor

logger = logging.getLogger(__name__)

# Common descriptor patterns to clean
CLEANUP_PATTERNS = [
    (r"TST\*", ""),  # Remove "TST*" prefix common in card processors
    (r"SQ\s*\*", ""),  # Remove "SQ *" prefix from Square transactions
    (r"PP\*", ""),  # Remove "PP*" prefix from PayPal
    (r"SP\s*\*", ""),  # Remove "SP*" prefix
    (r"\s*#\d+", ""),  # Remove store numbers like " #1234"
    (r"\s+STORE\s+\d+", ""),  # Remove "STORE 123" patterns
    (r"\s+\d{3,5}\s*$", ""),  # Remove trailing 3-5 digit numbers
    (r"\s{2,}", " "),  # Collapse multiple spaces
]


@lru_cache(maxsize=1024)
def _clean_descriptor(descriptor: str) -> str:
    """
    Clean a raw descriptor for better matching (cached).

    Removes common prefixes, store IDs, and normalizes whitespace.
    This is cached since the same descriptors appear frequently.

    Args:
        descriptor: Raw transaction descriptor

    Returns:
        Cleaned descriptor string
    """
    cleaned = descriptor.upper().strip()

    for pattern, replacement in CLEANUP_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


async def normalize_vendor(
    raw_descriptor: str, db: AsyncSession
) -> Optional[str]:
    """
    Normalize a raw transaction descriptor to a canonical vendor name.

    Matching strategy:
    1. Exact match on descriptor
    2. Case-insensitive match
    3. Cleaned descriptor match
    4. Alias match (exact and case-insensitive)
    5. Cleaned alias match
    6. Fuzzy pattern match on cleaned descriptor

    Args:
        raw_descriptor: Raw merchant descriptor from transaction
        db: Database session

    Returns:
        Canonical vendor name if match found, None otherwise

    Example:
        >>> await normalize_vendor("TST* STARBUCKS 1234", db)
        "Starbucks"
        >>> await normalize_vendor("NETFLIX.COM", db)
        "Netflix"
    """
    if not raw_descriptor:
        logger.debug("Empty descriptor provided")
        return None

    descriptor_upper = raw_descriptor.upper()
    cleaned = _clean_descriptor(raw_descriptor)

    logger.debug(
        f"Normalizing vendor: '{raw_descriptor}' → cleaned: '{cleaned}'",
        extra={
            "raw": raw_descriptor,
            "cleaned": cleaned,
        },
    )

    try:
        # Strategy 1: Exact match on canonical vendor name
        result = await db.execute(
            select(Vendor).where(Vendor.canonical_vendor == raw_descriptor)
        )
        vendor = result.scalar_one_or_none()
        if vendor:
            logger.info(
                f"Exact match: '{raw_descriptor}' → {vendor.canonical_vendor}",
                extra={"match_type": "exact", "vendor": vendor.canonical_vendor},
            )
            return vendor.canonical_vendor

        # Strategy 2: Case-insensitive match on canonical vendor
        result = await db.execute(
            select(Vendor).where(
                func.upper(Vendor.canonical_vendor) == descriptor_upper
            )
        )
        vendor = result.scalar_one_or_none()
        if vendor:
            logger.info(
                f"Case-insensitive match: '{raw_descriptor}' → {vendor.canonical_vendor}",
                extra={
                    "match_type": "case_insensitive",
                    "vendor": vendor.canonical_vendor,
                },
            )
            return vendor.canonical_vendor

        # Strategy 3: Cleaned descriptor match
        if cleaned != descriptor_upper:
            result = await db.execute(
                select(Vendor).where(
                    func.upper(Vendor.canonical_vendor) == cleaned
                )
            )
            vendor = result.scalar_one_or_none()
            if vendor:
                logger.info(
                    f"Cleaned match: '{raw_descriptor}' → {vendor.canonical_vendor}",
                    extra={
                        "match_type": "cleaned",
                        "vendor": vendor.canonical_vendor,
                    },
                )
                return vendor.canonical_vendor

        # Strategy 4 & 5: Alias matching (exact, case-insensitive, cleaned)
        # Search through all vendors and check if descriptor matches any alias
        result = await db.execute(select(Vendor))
        vendors = result.scalars().all()

        for vendor in vendors:
            if not vendor.aliases:
                continue

            for alias in vendor.aliases:
                # Exact alias match
                if alias == raw_descriptor:
                    logger.info(
                        f"Alias exact match: '{raw_descriptor}' → {vendor.canonical_vendor}",
                        extra={
                            "match_type": "alias_exact",
                            "vendor": vendor.canonical_vendor,
                            "alias": alias,
                        },
                    )
                    return vendor.canonical_vendor

                # Case-insensitive alias match
                if alias.upper() == descriptor_upper:
                    logger.info(
                        f"Alias case-insensitive match: '{raw_descriptor}' → {vendor.canonical_vendor}",
                        extra={
                            "match_type": "alias_case_insensitive",
                            "vendor": vendor.canonical_vendor,
                            "alias": alias,
                        },
                    )
                    return vendor.canonical_vendor

                # Cleaned alias match
                cleaned_alias = _clean_descriptor(alias)
                if cleaned_alias == cleaned:
                    logger.info(
                        f"Alias cleaned match: '{raw_descriptor}' → {vendor.canonical_vendor}",
                        extra={
                            "match_type": "alias_cleaned",
                            "vendor": vendor.canonical_vendor,
                            "alias": alias,
                        },
                    )
                    return vendor.canonical_vendor

        # Strategy 6: Fuzzy pattern matching on cleaned descriptor
        # Check if cleaned descriptor contains canonical vendor name
        for vendor in vendors:
            vendor_upper = vendor.canonical_vendor.upper()
            if vendor_upper in cleaned or cleaned in vendor_upper:
                logger.info(
                    f"Fuzzy match: '{raw_descriptor}' → {vendor.canonical_vendor}",
                    extra={
                        "match_type": "fuzzy",
                        "vendor": vendor.canonical_vendor,
                    },
                )
                return vendor.canonical_vendor

        logger.debug(
            f"No vendor match found for '{raw_descriptor}'",
            extra={"raw": raw_descriptor, "cleaned": cleaned},
        )
        return None

    except Exception as e:
        logger.error(
            f"Error normalizing vendor '{raw_descriptor}': {e}",
            extra={"raw": raw_descriptor, "error": str(e)},
            exc_info=True,
        )
        # Return None on error rather than raising
        return None


async def get_vendor_category(
    canonical_vendor: str, db: AsyncSession
) -> Optional[tuple[str, Optional[str]]]:
    """
    Get default category and subcategory for a canonical vendor.

    Args:
        canonical_vendor: Canonical vendor name
        db: Database session

    Returns:
        Tuple of (category, subcategory) if vendor found, None otherwise
    """
    try:
        result = await db.execute(
            select(Vendor).where(Vendor.canonical_vendor == canonical_vendor)
        )
        vendor = result.scalar_one_or_none()

        if vendor and vendor.default_category:
            return (vendor.default_category, vendor.default_subcat)

        return None

    except Exception as e:
        logger.error(
            f"Error getting vendor category for '{canonical_vendor}': {e}",
            extra={"vendor": canonical_vendor, "error": str(e)},
            exc_info=True,
        )
        return None
