# app/routers/bookings.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..repositories.booking_repo import BookingRepository
from ..schemas.booking import PagedTodayBookingOut

router = APIRouter()


def get_repo(session: AsyncSession = Depends(get_session)) -> BookingRepository:
    return BookingRepository(session)


@router.get("today-bookings", response_model=PagedTodayBookingOut)
async def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    repo: BookingRepository = Depends(get_repo),
):
    total = await repo.count()
    items = await repo.list(skip=skip, limit=limit)
    return PagedTodayBookingOut(total=total, skip=skip, limit=limit, items=items)
