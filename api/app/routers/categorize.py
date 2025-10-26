"""
Transaction categorization router.
"""
import logging
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.deps import get_db
from app.models import Transaction
from app.schemas import CategorizeOut, FinalizeRequest, FinalizeResponse
from app.categorize import categorize_transaction
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/categorize/{transaction_id}",
    response_model=CategorizeOut,
    summary="Categorize a transaction",
    description="""
    Categorize a transaction using rules and AI.

    - Applies deterministic rules first (confidence = 1.0)
    - Falls back to OpenAI if no rule matches
    - Sets status to 'review' if confidence < threshold or amount > review threshold
    - Sets status to 'finalized' otherwise
    - Returns categorization result

    **Authentication**: Not required (called by n8n workflow)
    """,
    responses={
        200: {
            "description": "Transaction categorized successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "category": "Dining",
                        "subcategory": "Coffee",
                        "confidence": 0.91,
                        "status": "finalized"
                    }
                }
            }
        },
        404: {
            "description": "Transaction not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Transaction not found"}
                }
            }
        },
        500: {
            "description": "Categorization failed"
        }
    }
)
async def categorize(
    transaction_id: int,
    db: AsyncSession = Depends(get_db)
) -> CategorizeOut:
    """
    Categorize a transaction.

    Process:
        1. Load transaction from database
        2. Apply rules engine (deterministic)
        3. Fallback to OpenAI if no rule matches
        4. Update transaction with category, subcategory, confidence
        5. Set status based on confidence and amount
        6. Return categorization result
    """
    try:
        # Load transaction
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        # Categorize transaction
        categorization = await categorize_transaction(transaction, db)

        # Update transaction
        transaction.category = categorization["category"]
        transaction.subcategory = categorization.get("subcategory")
        transaction.confidence = categorization["confidence"]

        # Update canonical vendor if provided by AI
        if categorization.get("vendor") and not transaction.canonical_vendor:
            transaction.canonical_vendor = categorization["vendor"]

        # Determine status
        needs_review = (
            categorization["confidence"] < Decimal(str(settings.LOW_CONFIDENCE))
            or transaction.amount_cents > settings.REVIEW_AMOUNT_CENTS
        )

        transaction.status = "review" if needs_review else "finalized"

        await db.commit()
        await db.refresh(transaction)

        logger.info(
            f"Transaction {transaction_id} categorized: "
            f"category={transaction.category}, "
            f"confidence={transaction.confidence}, "
            f"status={transaction.status}"
        )

        return CategorizeOut(
            id=transaction.id,
            category=transaction.category,
            subcategory=transaction.subcategory,
            confidence=transaction.confidence,
            status=transaction.status
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error categorizing transaction {transaction_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to categorize transaction"
        ) from e


@router.post(
    "/finalize/{transaction_id}",
    response_model=FinalizeResponse,
    summary="Finalize transaction category",
    description="""
    Finalize or override a transaction's category.

    - Updates category and subcategory
    - Sets status to 'finalized'
    - Used for manual review corrections

    **Authentication**: Not required (called by n8n workflow or dashboard)
    """,
    responses={
        200: {
            "description": "Transaction finalized successfully",
            "content": {
                "application/json": {
                    "example": {"ok": True}
                }
            }
        },
        404: {
            "description": "Transaction not found"
        },
        400: {
            "description": "Invalid request data"
        }
    }
)
async def finalize(
    transaction_id: int,
    finalize_data: FinalizeRequest,
    db: AsyncSession = Depends(get_db)
) -> FinalizeResponse:
    """
    Finalize a transaction's category.

    Process:
        1. Load transaction from database
        2. Update category and subcategory
        3. Set status to 'finalized'
        4. Save changes
    """
    try:
        # Load transaction
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        # Update category
        transaction.category = finalize_data.category
        transaction.subcategory = finalize_data.subcategory
        transaction.status = "finalized"
        transaction.confidence = Decimal("1.00")  # User override = full confidence

        await db.commit()

        logger.info(
            f"Transaction {transaction_id} finalized: "
            f"category={transaction.category}, "
            f"subcategory={transaction.subcategory}"
        )

        return FinalizeResponse(ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing transaction {transaction_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalize transaction"
        ) from e
