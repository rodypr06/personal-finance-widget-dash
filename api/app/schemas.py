"""
Pydantic schemas for request/response validation.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Transaction Schemas
# ============================================================================


class TxnIn(BaseModel):
    """
    Schema for incoming transaction data during ingestion.
    """

    txn_date: date = Field(..., description="Transaction date")
    amount_cents: int = Field(..., description="Amount in cents")
    currency: str = Field(default="USD", description="Currency code")
    direction: str = Field(..., description="Transaction direction: debit or credit")
    raw_descriptor: str = Field(..., description="Original merchant descriptor")
    source_account: str = Field(..., description="Source account identifier")
    memo: Optional[str] = Field(None, description="Transaction memo")
    mcc: Optional[str] = Field(None, description="Merchant Category Code")
    hash_id: str = Field(..., description="SHA256 hash for deduplication")

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate direction is either 'debit' or 'credit'."""
        if v not in ("debit", "credit"):
            raise ValueError("direction must be 'debit' or 'credit'")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "txn_date": "2025-10-24",
                "amount_cents": 784,
                "currency": "USD",
                "direction": "debit",
                "raw_descriptor": "STARBUCKS 1234",
                "source_account": "amex_blue_cash",
                "memo": None,
                "mcc": "5814",
                "hash_id": "a1b2c3d4e5f6...",
            }
        }
    }


class TxnOut(BaseModel):
    """
    Schema for transaction output.
    """

    id: int
    txn_date: date
    posted_at: datetime
    amount_cents: int
    currency: str
    direction: str
    raw_descriptor: str
    canonical_vendor: Optional[str] = None
    mcc: Optional[str] = None
    memo: Optional[str] = None
    source_account: str
    hash_id: str
    receipt_url: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    confidence: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 123,
                "txn_date": "2025-10-24",
                "posted_at": "2025-10-24T10:30:00Z",
                "amount_cents": 784,
                "currency": "USD",
                "direction": "debit",
                "raw_descriptor": "STARBUCKS 1234",
                "canonical_vendor": "Starbucks",
                "mcc": "5814",
                "memo": None,
                "source_account": "amex_blue_cash",
                "hash_id": "a1b2c3d4e5f6...",
                "receipt_url": None,
                "category": "Dining",
                "subcategory": "Coffee",
                "confidence": 0.91,
                "status": "finalized",
                "notes": None,
            }
        },
    }


class IngestResponse(BaseModel):
    """
    Response after ingesting a transaction.
    """

    id: int
    status: str

    model_config = {
        "json_schema_extra": {
            "example": {"id": 123, "status": "ingested"}
        }
    }


# ============================================================================
# Categorization Schemas
# ============================================================================


class CategorizeOut(BaseModel):
    """
    Schema for categorization response.
    """

    id: int
    category: Optional[str] = None
    subcategory: Optional[str] = None
    confidence: Optional[Decimal] = None
    status: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 123,
                "category": "Dining",
                "subcategory": "Coffee",
                "confidence": 0.91,
                "status": "finalized",
            }
        }
    }


class FinalizeRequest(BaseModel):
    """
    Schema for finalizing a transaction category.
    """

    category: str
    subcategory: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {"category": "Dining", "subcategory": "Coffee"}
        }
    }


class FinalizeResponse(BaseModel):
    """
    Response after finalizing a transaction.
    """

    ok: bool

    model_config = {"json_schema_extra": {"example": {"ok": True}}}


# ============================================================================
# Report Schemas
# ============================================================================


class CategoryTotal(BaseModel):
    """
    Total amount per category.
    """

    category: str
    amount_cents: int


class VendorTotal(BaseModel):
    """
    Total amount per vendor.
    """

    vendor: str
    amount_cents: int


class TimeseriesPoint(BaseModel):
    """
    Daily spending timeseries point.
    """

    date: date
    sum_cents: int


class SummaryOut(BaseModel):
    """
    Schema for monthly/period summary report.
    """

    period: str
    totals_by_category: List[CategoryTotal]
    top_vendors: List[VendorTotal]
    timeseries: List[TimeseriesPoint]
    total_income_cents: int = 0
    total_expense_cents: int = 0
    net_savings_cents: int = 0

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "2025-10",
                "totals_by_category": [
                    {"category": "Groceries", "amount_cents": 45000},
                    {"category": "Dining", "amount_cents": 12000},
                ],
                "top_vendors": [
                    {"vendor": "Hy-Vee", "amount_cents": 22000},
                    {"vendor": "Starbucks", "amount_cents": 5000},
                ],
                "timeseries": [
                    {"date": "2025-10-01", "sum_cents": 4300},
                    {"date": "2025-10-02", "sum_cents": 6700},
                ],
                "total_income_cents": 500000,
                "total_expense_cents": 180000,
                "net_savings_cents": 320000,
            }
        }
    }


# ============================================================================
# Alert Schemas
# ============================================================================


class AlertOut(BaseModel):
    """
    Schema for alert/anomaly detection output.
    """

    type: str = Field(..., description="Alert type identifier")
    vendor: Optional[str] = None
    category: Optional[str] = None
    amount_cents: Optional[int] = None
    date: Optional[date] = None
    message: str = Field(..., description="Human-readable alert message")
    severity: str = Field(default="info", description="Alert severity: info, warning, critical")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional alert metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "new_vendor_over_threshold",
                "vendor": "Acme Gym",
                "amount_cents": 3999,
                "date": "2025-10-20",
                "message": "New vendor 'Acme Gym' with charge of $39.99",
                "severity": "warning",
                "metadata": {"first_transaction": True},
            }
        }
    }


# ============================================================================
# Vendor Schemas
# ============================================================================


class VendorOut(BaseModel):
    """
    Schema for vendor output.
    """

    canonical_vendor: str
    default_category: Optional[str] = None
    default_subcat: Optional[str] = None
    aliases: List[str] = []

    model_config = {"from_attributes": True}


# ============================================================================
# Rule Schemas
# ============================================================================


class RuleOut(BaseModel):
    """
    Schema for rule output.
    """

    id: int
    priority: int
    condition: Dict[str, Any]
    action: Dict[str, Any]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
