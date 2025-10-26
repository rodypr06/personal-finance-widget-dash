"""
Anomaly detection service for identifying unusual transaction patterns.

This module provides various anomaly detection algorithms to identify:
- New vendors with high transaction amounts
- Duplicate transactions
- Statistical outliers (z-score analysis)
- Unusual spending patterns
"""
import logging
from datetime import date, timedelta
from typing import List, Dict

import numpy as np
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction
from app.schemas import AlertOut
from app.config import settings

logger = logging.getLogger(__name__)


async def detect_anomalies(
    db: AsyncSession, lookback_days: int = 30
) -> List[AlertOut]:
    """
    Detect anomalies in recent transactions.

    Analyzes transactions from the last N days to identify:
    1. New vendors with amounts > $50
    2. Duplicate transactions (same hash_id appearing multiple times)
    3. Z-score outliers per category (>2 standard deviations)
    4. Unusual spending patterns (category spending >3x average)
    5. Missing receipts on high-value transactions
    6. Low-confidence transactions pending review

    Args:
        db: Database session
        lookback_days: Number of days to analyze (default: 30)

    Returns:
        List of anomaly alert dictionaries

    Example:
        >>> anomalies = await detect_anomalies(db)
        >>> for alert in anomalies:
        ...     print(f"{alert.severity}: {alert.message}")
    """
    cutoff_date = date.today() - timedelta(days=lookback_days)
    end_date = date.today()

    logger.info(
        f"Detecting anomalies for transactions since {cutoff_date}",
        extra={"lookback_days": lookback_days, "cutoff_date": str(cutoff_date)},
    )

    try:
        alerts = []

        # Detect each anomaly type
        alerts.extend(await detect_new_vendors(db, cutoff_date, end_date))
        alerts.extend(await detect_duplicates(db, cutoff_date, end_date))
        alerts.extend(await _detect_zscore_outliers(db, cutoff_date))
        alerts.extend(await _detect_unusual_spending(db, cutoff_date))
        alerts.extend(await detect_missing_receipts(db, cutoff_date, end_date))
        alerts.extend(await detect_pending_review(db, cutoff_date, end_date))

        logger.info(
            f"Detected {len(alerts)} anomalies",
            extra={"count": len(alerts), "lookback_days": lookback_days},
        )

        return alerts

    except Exception as e:
        logger.error(
            f"Error detecting anomalies: {e}",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise


async def detect_new_vendors(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    threshold_cents: int = 5000
) -> List[AlertOut]:
    """
    Detect new vendors with charges above threshold.

    Args:
        db: Database session
        start_date: Start date
        end_date: End date
        threshold_cents: Alert if first transaction exceeds this amount

    Returns:
        List of new vendor alerts
    """
    alerts = []

    # Find vendors with first transaction in date range
    subq = (
        select(
            Transaction.canonical_vendor,
            func.min(Transaction.txn_date).label("first_date")
        )
        .where(Transaction.canonical_vendor.isnot(None))
        .group_by(Transaction.canonical_vendor)
        .subquery()
    )

    result = await db.execute(
        select(Transaction, subq.c.first_date)
        .join(
            subq,
            and_(
                Transaction.canonical_vendor == subq.c.canonical_vendor,
                Transaction.txn_date == subq.c.first_date
            )
        )
        .where(
            and_(
                subq.c.first_date >= start_date,
                subq.c.first_date <= end_date,
                Transaction.amount_cents >= threshold_cents,
                Transaction.direction == "debit"
            )
        )
    )

    for txn, first_date in result.all():
        alerts.append(AlertOut(
            type="new_vendor_over_threshold",
            vendor=txn.canonical_vendor,
            amount_cents=txn.amount_cents,
            date=txn.txn_date,
            message=f"New vendor '{txn.canonical_vendor}' with charge of ${txn.amount_cents / 100:.2f}",
            severity="warning",
            metadata={
                "first_transaction": True,
                "transaction_id": txn.id
            }
        ))

    return alerts


async def detect_missing_receipts(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    threshold_cents: int = 2500
) -> List[AlertOut]:
    """
    Detect high-value transactions without receipts.

    Args:
        db: Database session
        start_date: Start date
        end_date: End date
        threshold_cents: Alert if transaction exceeds this amount without receipt

    Returns:
        List of missing receipt alerts
    """
    alerts = []

    result = await db.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.txn_date >= start_date,
                Transaction.txn_date <= end_date,
                Transaction.receipt_url.is_(None),
                Transaction.amount_cents >= threshold_cents,
                Transaction.direction == "debit"
            )
        )
        .order_by(Transaction.amount_cents.desc())
        .limit(20)
    )

    for txn in result.scalars().all():
        alerts.append(AlertOut(
            type="missing_receipt",
            vendor=txn.canonical_vendor,
            category=txn.category,
            amount_cents=txn.amount_cents,
            date=txn.txn_date,
            message=f"Missing receipt for ${txn.amount_cents / 100:.2f} at {txn.canonical_vendor or txn.raw_descriptor}",
            severity="info",
            metadata={
                "transaction_id": txn.id,
                "needs_receipt": True
            }
        ))

    return alerts


async def detect_pending_review(
    db: AsyncSession,
    start_date: date,
    end_date: date
) -> List[AlertOut]:
    """
    Detect transactions pending manual review.

    Args:
        db: Database session
        start_date: Start date
        end_date: End date

    Returns:
        List of review alerts
    """
    alerts = []

    result = await db.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.txn_date >= start_date,
                Transaction.txn_date <= end_date,
                Transaction.status == "review"
            )
        )
        .order_by(Transaction.txn_date.desc())
    )

    for txn in result.scalars().all():
        reason = "low confidence" if txn.confidence and txn.confidence < settings.LOW_CONFIDENCE else "high amount"

        alerts.append(AlertOut(
            type="low_confidence",
            vendor=txn.canonical_vendor,
            category=txn.category,
            amount_cents=txn.amount_cents,
            date=txn.txn_date,
            message=f"Transaction pending review ({reason}): ${txn.amount_cents / 100:.2f} at {txn.canonical_vendor or txn.raw_descriptor}",
            severity="warning",
            metadata={
                "transaction_id": txn.id,
                "confidence": float(txn.confidence) if txn.confidence else None,
                "reason": reason
            }
        ))

    return alerts


async def detect_duplicates(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    time_window_hours: int = 24
) -> List[AlertOut]:
    """
    Detect potential duplicate transactions.

    Args:
        db: Database session
        start_date: Start date
        end_date: End date
        time_window_hours: Time window for duplicate detection

    Returns:
        List of duplicate alerts

    Logic:
        - Same vendor
        - Same amount
        - Within time window
        - Different hash_id
    """
    alerts = []

    # Find all transactions in range
    result = await db.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.txn_date >= start_date,
                Transaction.txn_date <= end_date,
                Transaction.canonical_vendor.isnot(None)
            )
        )
        .order_by(Transaction.txn_date, Transaction.canonical_vendor)
    )

    transactions = result.scalars().all()

    # Simple duplicate detection
    seen = {}
    for txn in transactions:
        key = (txn.canonical_vendor, txn.amount_cents, txn.txn_date)

        if key in seen:
            other = seen[key]
            if other.hash_id != txn.hash_id:
                alerts.append(AlertOut(
                    type="duplicate_warning",
                    vendor=txn.canonical_vendor,
                    amount_cents=txn.amount_cents,
                    date=txn.txn_date,
                    message=f"Possible duplicate: ${txn.amount_cents / 100:.2f} at {txn.canonical_vendor} on {txn.txn_date}",
                    severity="info",
                    metadata={
                        "transaction_ids": [txn.id, other.id],
                        "same_day": True
                    }
                ))
        else:
            seen[key] = txn

    return alerts


async def _detect_zscore_outliers(
    db: AsyncSession, cutoff_date: date, z_threshold: float = 2.0
) -> List[AlertOut]:
    """
    Detect statistical outliers using z-score analysis per category.

    Args:
        db: Database session
        cutoff_date: Only consider transactions after this date
        z_threshold: Z-score threshold for outlier detection (default: 2.0)

    Returns:
        List of anomaly alerts
    """
    alerts = []

    try:
        # Get all categories
        stmt = (
            select(Transaction.category)
            .where(
                and_(
                    Transaction.txn_date >= cutoff_date,
                    Transaction.category.isnot(None),
                )
            )
            .distinct()
        )
        result = await db.execute(stmt)
        categories = [row[0] for row in result]

        # Analyze each category
        for category in categories:
            # Get all amounts for this category
            stmt = (
                select(Transaction)
                .where(
                    and_(
                        Transaction.category == category,
                        Transaction.txn_date >= cutoff_date,
                    )
                )
                .order_by(Transaction.amount_cents.desc())
            )
            result = await db.execute(stmt)
            txns = result.scalars().all()

            if len(txns) < 5:  # Need minimum sample size
                continue

            amounts = np.array([t.amount_cents for t in txns])
            mean = np.mean(amounts)
            std = np.std(amounts)

            if std == 0:  # All amounts are the same
                continue

            # Find outliers
            for txn in txns:
                z_score = abs((txn.amount_cents - mean) / std)
                if z_score > z_threshold:
                    severity = "high" if z_score > 3.0 else "medium"
                    alerts.append(
                        AlertOut(
                            type="zscore_outlier",
                            vendor=txn.canonical_vendor,
                            category=category,
                            amount_cents=txn.amount_cents,
                            date=txn.txn_date,
                            message=f"Unusual ${txn.amount_cents / 100:.2f} transaction in {category} (z-score: {z_score:.2f})",
                            severity=severity,
                            metadata={
                                "z_score": round(z_score, 2),
                                "category_mean": round(float(mean), 2),
                                "category_std": round(float(std), 2),
                                "transaction_id": txn.id,
                            },
                        )
                    )

        logger.debug(
            f"Found {len(alerts)} z-score outlier anomalies",
            extra={"count": len(alerts)},
        )

    except Exception as e:
        logger.error(
            f"Error detecting z-score anomalies: {e}",
            extra={"error": str(e)},
            exc_info=True,
        )

    return alerts


async def _detect_unusual_spending(
    db: AsyncSession, cutoff_date: date, multiplier: float = 3.0
) -> List[AlertOut]:
    """
    Detect unusual spending patterns (category spending >3x average).

    Args:
        db: Database session
        cutoff_date: Only consider transactions after this date
        multiplier: Spending multiplier threshold (default: 3.0)

    Returns:
        List of anomaly alerts
    """
    alerts = []

    try:
        # Get spending by category for recent period
        recent_start = cutoff_date
        recent_end = date.today()
        period_days = (recent_end - recent_start).days

        # Get historical baseline (2x the lookback period)
        historical_start = recent_start - timedelta(days=period_days * 2)
        historical_end = recent_start

        # Calculate recent spending per category
        recent_stmt = (
            select(
                Transaction.category,
                func.sum(Transaction.amount_cents).label("total"),
            )
            .where(
                and_(
                    Transaction.txn_date >= recent_start,
                    Transaction.txn_date <= recent_end,
                    Transaction.category.isnot(None),
                    Transaction.direction == "debit",  # Only count expenses
                )
            )
            .group_by(Transaction.category)
        )
        recent_result = await db.execute(recent_stmt)
        recent_spending = {row[0]: row[1] for row in recent_result}

        # Calculate historical average per category
        historical_stmt = (
            select(
                Transaction.category,
                func.sum(Transaction.amount_cents).label("total"),
            )
            .where(
                and_(
                    Transaction.txn_date >= historical_start,
                    Transaction.txn_date < historical_end,
                    Transaction.category.isnot(None),
                    Transaction.direction == "debit",
                )
            )
            .group_by(Transaction.category)
        )
        historical_result = await db.execute(historical_stmt)
        historical_spending = {row[0]: row[1] for row in historical_result}

        # Compare recent vs historical
        for category, recent_amount in recent_spending.items():
            if category not in historical_spending:
                continue

            historical_amount = historical_spending[category]
            if historical_amount == 0:
                continue

            ratio = recent_amount / historical_amount

            if ratio > multiplier:
                severity = "high" if ratio > 5.0 else "medium"
                alerts.append(
                    AlertOut(
                        type="unusual_category_spending",
                        category=category,
                        amount_cents=recent_amount,
                        date=recent_end,
                        message=f"{category} spending is {ratio:.1f}x higher than average",
                        severity=severity,
                        metadata={
                            "recent_amount_cents": recent_amount,
                            "historical_amount_cents": historical_amount,
                            "ratio": round(ratio, 2),
                            "recent_period_days": period_days,
                            "historical_period_days": period_days * 2,
                        },
                    )
                )

        logger.debug(
            f"Found {len(alerts)} unusual spending anomalies",
            extra={"count": len(alerts)},
        )

    except Exception as e:
        logger.error(
            f"Error detecting unusual spending anomalies: {e}",
            extra={"error": str(e)},
            exc_info=True,
        )

    return alerts
