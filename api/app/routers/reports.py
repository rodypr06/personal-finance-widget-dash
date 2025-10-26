"""
Reporting router for financial summaries and analytics.
"""
import logging
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import insert

from app.deps import get_db
from app.models import Transaction, Report
from app.schemas import SummaryOut, CategoryTotal, VendorTotal, TimeseriesPoint

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/report/summary",
    response_model=SummaryOut,
    summary="Get financial summary report",
    description="""
    Get a comprehensive financial summary for a time period.

    - Aggregates by category
    - Top vendors by spending
    - Daily spending timeseries
    - Total income, expenses, and savings

    **Filters**:
    - `month`: YYYY-MM format (e.g., "2025-10")
    - `start_date`: Custom start date (YYYY-MM-DD)
    - `end_date`: Custom end date (YYYY-MM-DD)
    - `category`: Filter by category
    - `vendor`: Filter by vendor
    - `account`: Filter by account
    - `status`: Filter by status (default: finalized only)

    **Note**: Results are cached in the reports table for performance.

    **Authentication**: Not required (dashboard access)
    """,
    responses={
        200: {
            "description": "Summary report generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "period": "2025-10",
                        "totals_by_category": [
                            {"category": "Groceries", "amount_cents": 45000},
                            {"category": "Dining", "amount_cents": 12000}
                        ],
                        "top_vendors": [
                            {"vendor": "Hy-Vee", "amount_cents": 22000},
                            {"vendor": "Starbucks", "amount_cents": 5000}
                        ],
                        "timeseries": [
                            {"date": "2025-10-01", "sum_cents": 4300},
                            {"date": "2025-10-02", "sum_cents": 6700}
                        ],
                        "total_income_cents": 500000,
                        "total_expense_cents": 180000,
                        "net_savings_cents": 320000
                    }
                }
            }
        },
        400: {
            "description": "Invalid date parameters"
        }
    }
)
async def get_summary(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    category: Optional[str] = Query(None, description="Filter by category"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    account: Optional[str] = Query(None, description="Filter by account"),
    status: Optional[str] = Query("finalized", description="Filter by status"),
    db: AsyncSession = Depends(get_db)
) -> SummaryOut:
    """
    Get financial summary report.

    Process:
        1. Parse date range from month or start/end dates
        2. Check cache for existing report
        3. If not cached, query transactions
        4. Aggregate by category, vendor, and date
        5. Calculate totals
        6. Cache result
        7. Return summary
    """
    try:
        # Determine date range
        if month:
            # Parse month format YYYY-MM
            try:
                year, mon = month.split("-")
                start_date = date(int(year), int(mon), 1)
                # Last day of month
                if int(mon) == 12:
                    end_date = date(int(year) + 1, 1, 1)
                else:
                    end_date = date(int(year), int(mon) + 1, 1)
                period = month
            except (ValueError, IndexError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid month format. Use YYYY-MM"
                ) from e
        elif start_date and end_date:
            period = f"{start_date}_to_{end_date}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'month' or 'start_date' and 'end_date' required"
            )

        # Build base query
        conditions = [
            Transaction.txn_date >= start_date,
            Transaction.txn_date < end_date
        ]

        if category:
            conditions.append(Transaction.category == category)
        if vendor:
            conditions.append(Transaction.canonical_vendor == vendor)
        if account:
            conditions.append(Transaction.source_account == account)
        if status:
            conditions.append(Transaction.status == status)

        # Query: Totals by category
        category_result = await db.execute(
            select(
                Transaction.category,
                func.sum(Transaction.amount_cents).label("total")
            )
            .where(
                and_(
                    *conditions,
                    Transaction.direction == "debit",
                    Transaction.category.isnot(None)
                )
            )
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount_cents).desc())
        )

        totals_by_category = [
            CategoryTotal(category=row.category, amount_cents=int(row.total))
            for row in category_result.all()
        ]

        # Query: Top vendors
        vendor_result = await db.execute(
            select(
                Transaction.canonical_vendor,
                func.sum(Transaction.amount_cents).label("total")
            )
            .where(
                and_(
                    *conditions,
                    Transaction.direction == "debit",
                    Transaction.canonical_vendor.isnot(None)
                )
            )
            .group_by(Transaction.canonical_vendor)
            .order_by(func.sum(Transaction.amount_cents).desc())
            .limit(10)
        )

        top_vendors = [
            VendorTotal(vendor=row.canonical_vendor, amount_cents=int(row.total))
            for row in vendor_result.all()
        ]

        # Query: Timeseries
        timeseries_result = await db.execute(
            select(
                Transaction.txn_date,
                func.sum(Transaction.amount_cents).label("total")
            )
            .where(
                and_(
                    *conditions,
                    Transaction.direction == "debit"
                )
            )
            .group_by(Transaction.txn_date)
            .order_by(Transaction.txn_date)
        )

        timeseries = [
            TimeseriesPoint(date=row.txn_date, sum_cents=int(row.total))
            for row in timeseries_result.all()
        ]

        # Query: Total income
        income_result = await db.execute(
            select(func.sum(Transaction.amount_cents))
            .where(
                and_(
                    *conditions,
                    Transaction.direction == "credit"
                )
            )
        )
        total_income_cents = int(income_result.scalar() or 0)

        # Query: Total expenses
        expense_result = await db.execute(
            select(func.sum(Transaction.amount_cents))
            .where(
                and_(
                    *conditions,
                    Transaction.direction == "debit"
                )
            )
        )
        total_expense_cents = int(expense_result.scalar() or 0)

        # Calculate net savings
        net_savings_cents = total_income_cents - total_expense_cents

        summary = SummaryOut(
            period=period,
            totals_by_category=totals_by_category,
            top_vendors=top_vendors,
            timeseries=timeseries,
            total_income_cents=total_income_cents,
            total_expense_cents=total_expense_cents,
            net_savings_cents=net_savings_cents
        )

        # Cache result if using month parameter
        if month and not any([category, vendor, account]):
            try:
                stmt = insert(Report).values(
                    period=period,
                    kind="monthly",
                    payload=summary.model_dump(mode="json")
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["period", "kind"],
                    set_={"payload": stmt.excluded.payload}
                )
                await db.execute(stmt)
                await db.commit()
                logger.info(f"Cached report for period {period}")
            except Exception as e:
                logger.warning(f"Failed to cache report: {e}")
                # Continue even if caching fails

        logger.info(
            f"Generated summary report: period={period}, "
            f"categories={len(totals_by_category)}, "
            f"vendors={len(top_vendors)}"
        )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary report"
        ) from e
