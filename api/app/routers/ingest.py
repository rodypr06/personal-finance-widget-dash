"""
Transaction ingestion router.
"""
import hashlib
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.deps import get_db
from app.models import Transaction
from app.schemas import TxnIn, IngestResponse
from app.services.vendor_normalize import normalize_vendor

logger = logging.getLogger(__name__)

router = APIRouter()


def compute_hash_id(
    txn_date: str,
    amount_cents: int,
    descriptor: str,
    account: str
) -> str:
    """
    Compute SHA256 hash for transaction deduplication.

    Args:
        txn_date: Transaction date (YYYY-MM-DD)
        amount_cents: Amount in cents
        descriptor: Raw descriptor
        account: Source account

    Returns:
        SHA256 hash hex string
    """
    data = f"{txn_date}|{amount_cents}|{descriptor}|{account}"
    return hashlib.sha256(data.encode()).hexdigest()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a transaction",
    description="""
    Ingest a new transaction into the system.

    - Computes hash_id for deduplication if not provided
    - Upserts transaction (updates if hash_id exists)
    - Normalizes vendor name
    - Returns transaction ID and status

    **Authentication**: Not required (called by n8n workflow)
    """,
    responses={
        201: {
            "description": "Transaction ingested successfully",
            "content": {
                "application/json": {
                    "example": {"id": 123, "status": "ingested"}
                }
            }
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid direction: must be 'debit' or 'credit'"}
                }
            }
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def ingest_transaction(
    txn_data: TxnIn,
    db: AsyncSession = Depends(get_db)
) -> IngestResponse:
    """
    Ingest a transaction.

    Process:
        1. Validate input data
        2. Compute hash_id if not provided
        3. Normalize vendor name
        4. Upsert transaction (update if exists)
        5. Return transaction ID and status
    """
    try:
        # Compute hash_id if not provided
        if not txn_data.hash_id:
            hash_id = compute_hash_id(
                str(txn_data.txn_date),
                txn_data.amount_cents,
                txn_data.raw_descriptor,
                txn_data.source_account
            )
        else:
            hash_id = txn_data.hash_id

        # Normalize vendor
        canonical_vendor = await normalize_vendor(
            txn_data.raw_descriptor,
            db
        )

        # Prepare transaction data
        txn_dict = {
            "txn_date": txn_data.txn_date,
            "amount_cents": txn_data.amount_cents,
            "currency": txn_data.currency,
            "direction": txn_data.direction,
            "raw_descriptor": txn_data.raw_descriptor,
            "canonical_vendor": canonical_vendor,
            "mcc": txn_data.mcc,
            "memo": txn_data.memo,
            "source_account": txn_data.source_account,
            "hash_id": hash_id,
            "status": "ingested"
        }

        # Upsert transaction
        stmt = insert(Transaction).values(**txn_dict)
        stmt = stmt.on_conflict_do_update(
            index_elements=["hash_id"],
            set_={
                "txn_date": stmt.excluded.txn_date,
                "amount_cents": stmt.excluded.amount_cents,
                "currency": stmt.excluded.currency,
                "direction": stmt.excluded.direction,
                "raw_descriptor": stmt.excluded.raw_descriptor,
                "canonical_vendor": stmt.excluded.canonical_vendor,
                "mcc": stmt.excluded.mcc,
                "memo": stmt.excluded.memo,
                "source_account": stmt.excluded.source_account,
            }
        ).returning(Transaction.id)

        result = await db.execute(stmt)
        await db.commit()

        txn_id = result.scalar_one()

        logger.info(
            f"Transaction ingested: id={txn_id}, vendor={canonical_vendor}, "
            f"amount={txn_data.amount_cents}, hash={hash_id[:8]}..."
        )

        return IngestResponse(id=txn_id, status="ingested")

    except ValueError as e:
        logger.error(f"Validation error during ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Error ingesting transaction: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest transaction"
        ) from e
