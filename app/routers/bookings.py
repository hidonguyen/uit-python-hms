# app/routers/bookings.py
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models.booking import Gender
from ..repositories.booking_repo import BookingRepository
from ..schemas.booking import BookingCreate, BookingUpdate, BookingOut, PagedBookingOut

router = APIRouter()


def get_repo(session: AsyncSession = Depends(get_session)) -> BookingRepository:
    return BookingRepository(session)


@router.get("", response_model=PagedBookingOut)
async def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    gender: Optional[Gender] = None,
    nationality: Optional[str] = None,
    repo: BookingRepository = Depends(get_repo),
):
    filters: Dict[str, Any] = {
        "name": name,
        "phone": phone,
        "email": email,
        "gender": gender,
        "nationality": nationality,
    }
    total = await repo.count(filters)
    items = await repo.list(skip=skip, limit=limit, filters=filters)
    return PagedBookingOut(total=total, skip=skip, limit=limit, items=items)


@router.get("/search/name", response_model=List[BookingOut])
async def search_by_name(name: str, repo: BookingRepository = Depends(get_repo)):
    return await repo.search_by_name(name)


@router.get("/search/phone", response_model=List[BookingOut])
async def search_by_phone(phone: str, repo: BookingRepository = Depends(get_repo)):
    return await repo.search_by_phone(phone)


@router.get("/nationality/{nationality}", response_model=List[BookingOut])
async def get_by_nationality(
    nationality: str, repo: BookingRepository = Depends(get_repo)
):
    return await repo.get_bookings_by_nationality(nationality)


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: int, repo: BookingRepository = Depends(get_repo)):
    booking = await repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return booking


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(payload: BookingCreate, repo: BookingRepository = Depends(get_repo)):
    if payload.phone:
        existed_phone = await repo.get_by_phone(payload.phone)
        if existed_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Phone already exists"
            )
    if payload.email:
        existed_email = await repo.get_by_email(payload.email)
        if existed_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )
    booking = await repo.create(payload.model_dump(exclude_unset=True))
    return booking


@router.put("/{booking_id}", response_model=BookingOut)
async def update_booking(
    booking_id: int, payload: BookingUpdate, repo: BookingRepository = Depends(get_repo)
):
    data = payload.model_dump(exclude_unset=True)
    if "phone" in data:
        existed = await repo.get_by_phone(data["phone"])
        if existed and existed.id != booking_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Phone already exists"
            )
    if "email" in data:
        existed = await repo.get_by_email(data["email"])
        if existed and existed.id != booking_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )
    updated = await repo.update(booking_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return updated


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(booking_id: int, repo: BookingRepository = Depends(get_repo)):
    try:
        ok = await repo.delete(booking_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return None
