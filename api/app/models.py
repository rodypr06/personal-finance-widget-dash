"""
SQLAlchemy ORM models for the finance automation system.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMPTZ
from sqlalchemy.sql import func

from app.db import Base


class Transaction(Base):
    """
    Represents a financial transaction.

    Attributes:
        id: Unique transaction identifier
        txn_date: Date of the transaction
        posted_at: Timestamp when transaction was posted to our system
        amount_cents: Amount in cents (for precision)
        currency: Currency code (e.g., 'USD')
        direction: 'debit' or 'credit'
        raw_descriptor: Original merchant/transaction descriptor
        canonical_vendor: Normalized vendor name
        mcc: Merchant Category Code
        memo: Additional transaction notes from source
        source_account: Account identifier (e.g., 'amex_blue_cash')
        hash_id: Unique hash for deduplication (SHA256)
        receipt_url: URL to receipt in Google Drive
        category: Primary category (e.g., 'Groceries')
        subcategory: Secondary category (e.g., 'Supermarket')
        confidence: Categorization confidence score (0.00-1.00)
        status: Transaction status ('ingested', 'review', 'finalized')
        notes: User notes or system annotations
    """

    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    txn_date = Column(Date, nullable=False, index=True)
    posted_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    amount_cents = Column(BigInteger, nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    direction = Column(
        Text,
        CheckConstraint("direction IN ('debit', 'credit')"),
        nullable=False,
    )
    raw_descriptor = Column(Text, nullable=False)
    canonical_vendor = Column(Text, nullable=True, index=True)
    mcc = Column(Text, nullable=True)
    memo = Column(Text, nullable=True)
    source_account = Column(Text, nullable=False)
    hash_id = Column(Text, nullable=False, unique=True, index=True)
    receipt_url = Column(Text, nullable=True)
    category = Column(Text, nullable=True, index=True)
    subcategory = Column(Text, nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    status = Column(Text, nullable=False, default="ingested")
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_transactions_txn_date", "txn_date"),
        Index("ix_transactions_canonical_vendor", "canonical_vendor"),
        Index("ix_transactions_category", "category"),
        Index("ix_transactions_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, date={self.txn_date}, "
            f"vendor={self.canonical_vendor}, amount={self.amount_cents})>"
        )


class Vendor(Base):
    """
    Represents a canonical vendor with normalization rules.

    Attributes:
        canonical_vendor: Canonical vendor name (primary key)
        default_category: Default category for this vendor
        default_subcat: Default subcategory for this vendor
        aliases: List of known aliases/variations of vendor name
    """

    __tablename__ = "vendors"

    canonical_vendor = Column(Text, primary_key=True)
    default_category = Column(Text, nullable=True)
    default_subcat = Column(Text, nullable=True)
    aliases = Column(ARRAY(Text), nullable=True, default=list)

    def __repr__(self) -> str:
        return (
            f"<Vendor(name={self.canonical_vendor}, "
            f"category={self.default_category})>"
        )


class Rule(Base):
    """
    Represents a deterministic categorization rule.

    Attributes:
        id: Unique rule identifier
        priority: Rule priority (lower number = higher priority)
        condition: JSONB condition for matching transactions
            Examples:
            - {"contains": "NETFLIX"}: Match if descriptor contains "NETFLIX"
            - {"regex": "^STARBUCKS.*"}: Match if descriptor matches regex
            - {"mcc": "5411"}: Match if MCC equals "5411"
            - {"mcc_in": ["5411", "5422"]}: Match if MCC in list
            - {"amount_range": [1000, 50000]}: Match if amount_cents in range
            - {"account": "amex_blue_cash"}: Match specific account
        action: JSONB action to take when rule matches
            Example: {"category": "Subscriptions", "subcategory": "Streaming"}
        active: Whether rule is currently active
        created_at: Timestamp when rule was created
    """

    __tablename__ = "rules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    priority = Column(Integer, nullable=False, index=True)
    condition = Column(JSONB, nullable=False)
    action = Column(JSONB, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())

    __table_args__ = (Index("ix_rules_active_priority", "active", "priority"),)

    def __repr__(self) -> str:
        return f"<Rule(id={self.id}, priority={self.priority}, active={self.active})>"


class Report(Base):
    """
    Represents a cached report for performance optimization.

    Attributes:
        id: Unique report identifier
        period: Report period identifier (e.g., '2025-10', '2025-W42')
        kind: Report type ('weekly', 'monthly', 'yearly')
        payload: JSONB report data
        created_at: Timestamp when report was generated
    """

    __tablename__ = "reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    period = Column(Text, nullable=False, index=True)
    kind = Column(Text, nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())

    __table_args__ = (Index("ix_reports_period_kind", "period", "kind"),)

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, period={self.period}, kind={self.kind})>"
