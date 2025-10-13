from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.report import (
    SummaryOut,
    RoomTypeRevenueOut,
    RoomTypeRevenueItem,
    ServiceRevenueOut,
    ServiceRevenueItem,
    CustomerDistributionOut,
    DailyBookingsOut,
    DailyBookingPoint,
)
from app.repositories.report_repo import (
    get_summary,
    get_roomtype_revenue,
    get_service_revenue,
    get_customer_distribution,
    get_bookings_per_day,
)

router = APIRouter()

MAX_RANGE_DAYS = 370


def parse_flexible_date(value: str) -> date:
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Invalid date format for '{value}'. Use YYYY-MM-DD or DD-MM-YYYY.",
    )


def _validate_range(start_date: date, end_date: date):
    if start_date is None or end_date is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date và end_date là bắt buộc (DD-MM-YYYY).",
        )
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date không được lớn hơn end_date.",
        )
    if (end_date - start_date).days > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Khoảng ngày quá lớn (> {MAX_RANGE_DAYS} ngày).",
        )


@router.get("/summary", response_model=SummaryOut)
async def summary(
    start_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    end_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    session: AsyncSession = Depends(get_session),
):
    s = parse_flexible_date(start_date)
    e = parse_flexible_date(end_date)
    _validate_range(s, e)

    raw = await get_summary(session, s, e)
    room = Decimal(str(raw.get("room_amount", 0.0)))
    svc = Decimal(str(raw.get("svc_amount", 0.0)))
    guests = int(raw.get("guest_count", 0))
    total = room + svc

    return SummaryOut(
        total_revenue=total,
        room_revenue=room,
        service_revenue=svc,
        total_guests=guests,
        currency="VND",
    )


@router.get("/revenue-by-room-type", response_model=RoomTypeRevenueOut)
async def revenue_by_room_type(
    start_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    end_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    session: AsyncSession = Depends(get_session),
):
    s = parse_flexible_date(start_date)
    e = parse_flexible_date(end_date)
    _validate_range(s, e)

    rows = await get_roomtype_revenue(session, s, e)
    total = (
        sum(Decimal(str(r.get("revenue", 0))) for r in rows) if rows else Decimal("0")
    )
    items: List[RoomTypeRevenueItem] = []
    for r in rows:
        rev = Decimal(str(r.get("revenue", 0)))
        pct = float((rev / total * 100) if total else 0)
        items.append(
            RoomTypeRevenueItem(
                name=r.get("room_type") or r.get("name") or "",
                revenue=rev,
                percent=round(pct, 2),
            )
        )
    return RoomTypeRevenueOut(total=total, items=items)


@router.get("/service-revenue", response_model=ServiceRevenueOut)
async def service_revenue(
    start_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    end_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    session: AsyncSession = Depends(get_session),
):
    s = parse_flexible_date(start_date)
    e = parse_flexible_date(end_date)
    _validate_range(s, e)

    rows = await get_service_revenue(session, s, e)
    total = (
        sum(Decimal(str(r.get("revenue", 0))) for r in rows) if rows else Decimal("0")
    )
    items: List[ServiceRevenueItem] = []
    for r in rows:
        rev = Decimal(str(r.get("revenue", 0)))
        pct = float((rev / total * 100) if total else 0)
        items.append(
            ServiceRevenueItem(
                name=r.get("service_name") or r.get("name") or "",
                revenue=rev,
                percent=round(pct, 2),
            )
        )
    return ServiceRevenueOut(total=total, items=items)


@router.get("/customer-distribution", response_model=CustomerDistributionOut)
async def customer_distribution(
    start_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    end_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    session: AsyncSession = Depends(get_session),
):
    s = parse_flexible_date(start_date)
    e = parse_flexible_date(end_date)
    _validate_range(s, e)

    raw = await get_customer_distribution(session, s, e)
    return CustomerDistributionOut(
        new_customers=int(raw.get("new_customers", 0)),
        returning_customers=int(raw.get("returning_customers", 0)),
        percent_new=float(raw.get("percent_new", 0.0)),
        percent_returning=float(raw.get("percent_returning", 0.0)),
    )


@router.get("/bookings-per-day", response_model=DailyBookingsOut)
async def bookings_per_day(
    start_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    end_date: Annotated[str, Query(..., description="DD-MM-YYYY")],
    session: AsyncSession = Depends(get_session),
):
    s = parse_flexible_date(start_date)
    e = parse_flexible_date(end_date)
    _validate_range(s, e)

    rows = await get_bookings_per_day(session, s, e)
    points: List[DailyBookingPoint] = []
    total = 0
    for r in rows:
        d_str = r.get("date")
        cnt = int(r.get("booking_count", 0))
        total += cnt
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        points.append(DailyBookingPoint(date=d, bookings=cnt))

    return DailyBookingsOut(total=total, points=points)
