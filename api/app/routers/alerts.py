"""
Alerts and anomaly detection router.
"""
import logging
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas import AlertOut
from app.services.anomalies import detect_anomalies

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/alerts",
    response_model=List[AlertOut],
    summary="Get alerts and anomalies",
    description="""
    Get alerts for anomalies and issues requiring attention.

    **Alert Types**:
    - `new_vendor_over_threshold`: New vendor with large charge
    - `missing_receipt`: High-value transaction without receipt
    - `low_confidence`: Transaction pending manual review
    - `duplicate_warning`: Potential duplicate transaction

    **Filters**:
    - `start_date`: Start date for analysis (default: 30 days ago)
    - `end_date`: End date for analysis (default: today)
    - `severity`: Filter by severity (info, warning, critical)

    **Authentication**: Not required (dashboard access)
    """,
    responses={
        200: {
            "description": "Alerts retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "type": "new_vendor_over_threshold",
                            "vendor": "Acme Gym",
                            "amount_cents": 3999,
                            "date": "2025-10-20",
                            "message": "New vendor 'Acme Gym' with charge of $39.99",
                            "severity": "warning",
                            "metadata": {"first_transaction": True}
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Failed to generate alerts"
        }
    }
)
async def get_alerts(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: AsyncSession = Depends(get_db)
) -> List[AlertOut]:
    """
    Get alerts and anomalies.

    Process:
        1. Determine date range (default: last 30 days)
        2. Run anomaly detection service
        3. Filter by severity if specified
        4. Return alerts
    """
    try:
        # Default date range: last 30 days
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before end_date"
            )

        # Detect anomalies
        alerts = await detect_anomalies(db, start_date, end_date)

        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        logger.info(
            f"Generated {len(alerts)} alerts for period "
            f"{start_date} to {end_date}"
        )

        return alerts

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate alerts"
        ) from e
