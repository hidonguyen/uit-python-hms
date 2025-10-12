# app/routers/bookings.py
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from httpx import get
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import BookingStatus, ChargeType, PaymentStatus
from app.models.user import User
from app.repositories.booking_detail_repo import BookingDetailRepository
from app.repositories.guest_repo import GuestRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.room_type_repo import RoomTypeRepository
from app.schemas.booking_detail import BookingDetailCreate, BookingDetailOut
from app.services.auth_service import get_current_user, require_manager, require_receptionist

from ..db import get_session
from ..repositories.booking_repo import BookingRepository
from ..schemas.booking import BookingCreate, BookingOut, BookingStatusUpdate, BookingUpdate, PagedBookingHistoryOut, PagedTodayBookingOut

router = APIRouter()


def get_room_repo(session: AsyncSession = Depends(get_session)) -> RoomRepository:
    return RoomRepository(session)
def get_room_type_repo(session: AsyncSession = Depends(get_session)) -> RoomTypeRepository:
    return RoomTypeRepository(session)
def get_guest_repo(session: AsyncSession = Depends(get_session)) -> GuestRepository:
    return GuestRepository(session)
def get_booking_repo(session: AsyncSession = Depends(get_session)) -> BookingRepository:
    return BookingRepository(session)
def get_booking_detail_repo(session: AsyncSession = Depends(get_session)) -> BookingDetailRepository:
    return BookingDetailRepository(session)
def get_payment_repo(session: AsyncSession = Depends(get_session)) -> PaymentRepository:
    return PaymentRepository(session)


@router.get("/today", response_model=PagedTodayBookingOut)
async def list_today_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    _: User = Depends(require_receptionist),
):
    total = await booking_repo.count_today_bookings()
    items = await booking_repo.list_today_bookings(skip=skip, limit=limit)
    return PagedTodayBookingOut(total=total, skip=skip, limit=limit, items=items)


@router.get("/histories", response_model=PagedBookingHistoryOut)
async def list_booking_histories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    booking_no: Optional[str] = None,
    charge_type: Optional[ChargeType] = None,
    checkin_from: Optional[datetime] = None,
    checkin_to: Optional[datetime] = None,
    checkout_from: Optional[datetime] = None,
    checkout_to: Optional[datetime] = None,
    room_id: Optional[int] = None,
    room_name: Optional[str] = None,
    room_type_id: Optional[int] = None,
    room_type_name: Optional[str] = None,
    primary_guest_id: Optional[int] = None,
    primary_guest_name: Optional[str] = None,
    status: Optional[BookingStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    notes: Optional[str] = None,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    _: User = Depends(require_manager),
):
    filters: Dict[str, Any] = {
        "booking_no": booking_no,
        "charge_type": charge_type,
        "checkin_from": checkin_from,
        "checkin_to": checkin_to,
        "checkout_from": checkout_from,
        "checkout_to": checkout_to,
        "room_id": room_id,
        "room_name": room_name,
        "room_type_id": room_type_id,
        "room_type_name": room_type_name,
        "primary_guest_id": primary_guest_id,
        "primary_guest_name": primary_guest_name,
        "status": status,
        "payment_status": payment_status,
        "notes": notes,
    }

    total = await booking_repo.count_booking_histories(filters)
    items = await booking_repo.list_booking_histories(skip=skip, limit=limit, filters=filters)
    return PagedBookingHistoryOut(total=total, skip=skip, limit=limit, items=items)


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo)
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return booking


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    room_type_repo: RoomTypeRepository = Depends(get_room_type_repo),
    room_repo: RoomRepository = Depends(get_room_repo),
    guest_repo: GuestRepository = Depends(get_guest_repo),
    current_user: User = Depends(require_receptionist),
):
    if not payload.room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Room ID is required"
        )
    
    room = await room_repo.get(payload.room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room"
        )
    
    if not payload.room_type_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Room Type ID is required"
        )
    
    room_type = await room_type_repo.get(payload.room_type_id)
    if not room_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room type"
        )
    
    if not payload.primary_guest_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Primary Guest ID is required"
        )
    
    primary_guest = await guest_repo.get(payload.primary_guest_id)
    if not primary_guest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid primary guest"
        )

    if not payload.checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Check-in date is required"
        )

    if payload.checkin < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Check-in cannot be in the past"
        )
    
    if payload.checkout and payload.checkin >= payload.checkout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Check-out must be after check-in"
        )
    
    is_room_booked = await booking_repo.is_room_booked(
        room_id=payload.room_id,
        checkin=payload.checkin,
        checkout=payload.checkout
    )

    if is_room_booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Room is already booked"
        )
    
    if payload.num_adults is None or payload.num_adults < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Number of adults must be non-negative"
        )
    
    if payload.num_children is None or payload.num_children < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Number of children must be non-negative"
        )
    
    total_guests = payload.num_adults + payload.num_children
    if total_guests > room_type.max_occupancy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Total guests ({total_guests}) exceed room type max occupancy ({room_type.max_occupancy})"
        )
        
    created = await booking_repo.create(payload.model_dump(exclude_unset=True), current_user)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create booking"
        )
    return created


@router.put("/{booking_id}", response_model=BookingOut)
async def update_booking(
    booking_id: int, 
    payload: BookingUpdate,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    room_type_repo: RoomTypeRepository = Depends(get_room_type_repo),
    room_repo: RoomRepository = Depends(get_room_repo),
    guest_repo: GuestRepository = Depends(get_guest_repo),
    current_user: User = Depends(require_receptionist)
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    if not payload.room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Room ID is required"
        )
    
    if payload.room_id != booking.room_id:    
        room = await room_repo.get(payload.room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room"
            )
    
    if not payload.room_type_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Room Type ID is required"
        )
    
    if payload.room_type_id != booking.room_type_id:
        room_type = await room_type_repo.get(payload.room_type_id)
        if not room_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room type"
            )
    
    if not payload.primary_guest_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Primary Guest ID is required"
        )
    
    if payload.primary_guest_id != booking.primary_guest_id:
        primary_guest = await guest_repo.get(payload.primary_guest_id)
        if not primary_guest:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid primary guest"
            )

    if not payload.checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Check-in date is required"
        )

    if payload.checkin < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Check-in cannot be in the past"
        )
    
    if payload.checkout and payload.checkin >= payload.checkout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Check-out must be after check-in"
        )
    
    is_room_booked = await booking_repo.is_room_booked(
        room_id=payload.room_id,
        checkin=payload.checkin,
        checkout=payload.checkout
    )

    if is_room_booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Room is already booked"
        )
    
    if payload.num_adults is None or payload.num_adults < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Number of adults must be non-negative"
        )
    
    if payload.num_children is None or payload.num_children < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Number of children must be non-negative"
        )
    
    total_guests = payload.num_adults + payload.num_children
    if total_guests > room_type.max_occupancy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Total guests ({total_guests}) exceed room type max occupancy ({room_type.max_occupancy})"
        )

    updated = await booking_repo.update(booking_id, payload.model_dump(exclude_unset=True), current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )    
    return updated


@router.patch("/{booking_id}/status", response_model=BookingOut)
async def update_booking_status(
    booking_id: int, 
    payload: BookingStatusUpdate, 
    booking_repo: BookingRepository = Depends(get_booking_repo)
):
    updated = await booking_repo.update(booking_id, {"status": payload.status})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return updated


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: int, 
    booking_repo: BookingRepository = Depends(get_booking_repo)
):
    try:
        deleted = await booking_repo.delete(booking_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return None


@router.get("/{booking_id}/details", response_model=List[BookingDetailOut])
async def get_booking_details(
    booking_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    booking_detail_repo: BookingDetailRepository = Depends(get_booking_detail_repo)
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    
    return await booking_detail_repo.get_by_booking_id(booking_id)


@router.post("/{booking_id}/details", response_model=BookingDetailOut)
async def create_booking_detail(
    booking_id: int,
    payload: BookingDetailCreate,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    booking_detail_repo: BookingDetailRepository = Depends(get_booking_detail_repo),
    current_user: User = Depends(require_receptionist)
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    return await booking_detail_repo.create(booking_id, payload.model_dump(), current_user)

@router.delete("/{booking_id}/details/{detail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking_detail(
    booking_id: int,
    detail_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    booking_detail_repo: BookingDetailRepository = Depends(get_booking_detail_repo)
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    
    try:
        deleted = await booking_detail_repo.delete(booking_id, detail_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking detail not found"
        )
    return None
