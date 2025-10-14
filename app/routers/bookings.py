# app/routers/bookings.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import BookingStatus, ChargeType, PaymentStatus
from app.models.booking_detail import BookingDetailType
from app.models.user import User
from app.repositories.booking_detail_repo import BookingDetailRepository
from app.repositories.guest_repo import GuestRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.room_type_repo import RoomTypeRepository
from app.repositories.service_repo import ServiceRepository
from app.schemas.booking_detail import BookingDetailCreate, BookingDetailOut, BookingDetailTypeItem
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services.auth_service import require_manager, require_receptionist

from ..db import get_session
from ..repositories.booking_repo import BookingRepository
from ..schemas.booking import (
    BookingCreate,
    BookingOut,
    BookingStatusItem,
    BookingUpdate,
    ChargeTypeItem,
    PagedBookingHistoryOut,
    PagedTodayBookingOut,
    PaymentStatusItem,
)

router = APIRouter()


def get_room_repo(session: AsyncSession = Depends(get_session)) -> RoomRepository:
    return RoomRepository(session)
def get_room_type_repo(session: AsyncSession = Depends(get_session)) -> RoomTypeRepository:
    return RoomTypeRepository(session)
def get_guest_repo(session: AsyncSession = Depends(get_session)) -> GuestRepository:
    return GuestRepository(session)
def get_service_repo(session: AsyncSession = Depends(get_session)) -> ServiceRepository:
    return ServiceRepository(session)
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
    booking_repo: BookingRepository = Depends(get_booking_repo),
    _: User = Depends(require_receptionist),
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin phòng là bắt buộc"
        )
    
    room = await room_repo.get(payload.room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin phòng không hợp lệ"
        )
    
    if not payload.room_type_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin loại phòng là bắt buộc"
        )
    
    room_type = await room_type_repo.get(payload.room_type_id)
    if not room_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin loại phòng không hợp lệ"
        )
    
    if not payload.primary_guest_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin khách hàng chính là bắt buộc"
        )
    
    primary_guest = await guest_repo.get(payload.primary_guest_id)
    if not primary_guest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin khách hàng chính không hợp lệ"
        )

    if not payload.checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin ngày nhận phòng là bắt buộc"
        )

    if payload.checkin < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ngày nhận phòng không được ở quá khứ"
        )
    
    if payload.checkout and payload.checkin >= payload.checkout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ngày trả phòng phải sau ngày nhận phòng"
        )
    
    is_room_booked = await booking_repo.is_room_booked(
        room_id=payload.room_id,
        checkin=payload.checkin,
        checkout=payload.checkout
    )

    if is_room_booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Phòng đã được đặt"
        )
    
    if payload.num_adults is None or payload.num_adults < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Số lượng người lớn phải không âm"
        )
    
    if payload.num_children is None or payload.num_children < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Số lượng trẻ em phải không âm"
        )
    
    total_guests = payload.num_adults + payload.num_children
    if total_guests > room_type.max_occupancy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Tổng số khách ({total_guests}) vượt quá sức chứa tối đa của loại phòng ({room_type.max_occupancy})"
        )
        
    created = await booking_repo.create(payload.model_dump(exclude_unset=True), current_user)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể đặt phòng"
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )
    
    if booking.status not in [BookingStatus.RESERVED, BookingStatus.CHECKED_IN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ có thể cập nhật các đặt phòng có trạng thái 'Đã đặt' hoặc 'Đã nhận phòng'"
        )

    if not payload.room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin phòng là bắt buộc"
        )
    
    if payload.room_id != booking.room_id:    
        room = await room_repo.get(payload.room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin phòng không hợp lệ"
            )
    
    if not payload.room_type_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin loại phòng là bắt buộc"
        )
    
    room_type = await room_type_repo.get(payload.room_type_id)
    if not room_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin loại phòng không hợp lệ"
        )
    
    if not payload.primary_guest_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin khách chính là bắt buộc"
        )
    
    if payload.primary_guest_id != booking.primary_guest_id:
        primary_guest = await guest_repo.get(payload.primary_guest_id)
        if not primary_guest:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin khách chính không hợp lệ"
            )

    if not payload.checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Thông tin ngày nhận phòng là bắt buộc"
        )

    if booking.checkin != payload.checkin and payload.checkin < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ngày nhận phòng không được ở quá khứ"
        )
    
    if payload.checkout and payload.checkin >= payload.checkout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ngày trả phòng phải sau ngày nhận phòng"
        )
    
    if booking.room_id != payload.room_id or booking.checkin != payload.checkin or booking.checkout != payload.checkout:
        is_room_booked = await booking_repo.is_room_booked(
            room_id=payload.room_id,
            checkin=payload.checkin,
            checkout=payload.checkout
        )

        if is_room_booked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Phòng đã được đặt"
            )
    
    if payload.num_adults is None or payload.num_adults < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Số lượng người lớn phải không âm"
        )
    
    if payload.num_children is None or payload.num_children < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Số lượng trẻ em phải không âm"
        )
    
    total_guests = payload.num_adults + payload.num_children
    if total_guests > room_type.max_occupancy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Tổng số khách ({total_guests}) vượt quá sức chứa tối đa của loại phòng ({room_type.max_occupancy})"
        )

    updated = await booking_repo.update(booking_id, payload.model_dump(exclude_unset=True), current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )    
    return updated


@router.put("/{booking_id}/checkin", response_model=BookingOut)
async def checkin_booking(
    booking_id: int, 
    booking_repo: BookingRepository = Depends(get_booking_repo),
    current_user: User = Depends(require_receptionist)
):
    updated = await booking_repo.checkin(booking_id, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )    
    return updated


@router.get("/{booking_id}/details", response_model=List[BookingDetailOut])
async def get_booking_details(
    booking_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    booking_detail_repo: BookingDetailRepository = Depends(get_booking_detail_repo),
    _: User = Depends(require_receptionist),
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )
    
    return await booking_detail_repo.get_by_booking_id(booking_id)


@router.post("/{booking_id}/details", response_model=BookingDetailOut)
async def add_booking_detail(
    booking_id: int,
    payload: BookingDetailCreate,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    booking_detail_repo: BookingDetailRepository = Depends(get_booking_detail_repo),
    current_user: User = Depends(require_receptionist)
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )
    
    if booking.status not in [BookingStatus.RESERVED, BookingStatus.CHECKED_IN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ những đặt phòng có trạng thái 'Đã đặt' hoặc 'Đã nhận phòng' mới có thể thêm chi tiết"
        )

    payload.booking_id = booking_id

    return await booking_detail_repo.create(payload.model_dump(exclude_unset=True), current_user)


@router.delete("/{booking_id}/details/{detail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_booking_detail(
    booking_id: int,
    detail_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    booking_detail_repo: BookingDetailRepository = Depends(get_booking_detail_repo),
    _: User = Depends(require_receptionist),
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )
    
    if booking.status not in [BookingStatus.RESERVED, BookingStatus.CHECKED_IN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ những đặt phòng có trạng thái 'Đã đặt' hoặc 'Đã nhận phòng' mới có thể xóa chi tiết"
        )
    
    try:
        deleted = await booking_detail_repo.delete(detail_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin chi tiết đặt phòng"
        )
    return None


@router.get("/{booking_id}/payments", response_model=List[PaymentOut])
async def get_booking_payments(
    booking_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    payment_repo: PaymentRepository = Depends(get_payment_repo),
    _: User = Depends(require_receptionist),
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )

    return await payment_repo.get_by_booking_id(booking_id)


@router.post("/{booking_id}/payments", response_model=PaymentOut)
async def add_booking_payment(
    booking_id: int,
    payload: PaymentCreate,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    payment_repo: PaymentRepository = Depends(get_payment_repo),
    current_user: User = Depends(require_receptionist)
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )
    
    if booking.status not in [BookingStatus.RESERVED, BookingStatus.CHECKED_IN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ những đặt phòng có trạng thái 'Đã đặt' hoặc 'Đã nhận phòng' mới có thể thêm thanh toán"
        )

    return await payment_repo.create(payload.model_dump(exclude_unset=True), current_user)

@router.delete("/{booking_id}/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_booking_payment(
    booking_id: int,
    payment_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    payment_repo: PaymentRepository = Depends(get_payment_repo),
    _: User = Depends(require_manager),
):
    booking = await booking_repo.get(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )
    
    if booking.status not in [BookingStatus.RESERVED, BookingStatus.CHECKED_IN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ những đặt phòng có trạng thái 'Đã đặt' hoặc 'Đã nhận phòng' mới có thể xóa thanh toán"
        )
    
    try:
        deleted = await payment_repo.delete(payment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin thanh toán"
        )
    return None


@router.put("/{booking_id}/checkout", response_model=BookingOut)
async def checkout_booking(
    booking_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    current_user: User = Depends(require_receptionist)
):
    updated = await booking_repo.checkout(booking_id, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )    
    return updated


@router.put("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    current_user: User = Depends(require_receptionist)
):
    updated = await booking_repo.update(booking_id, {"status": BookingStatus.CANCELLED}, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )    
    return updated


@router.put("/{booking_id}/no-show", response_model=BookingOut)
async def mark_booking_as_no_show(
    booking_id: int,
    booking_repo: BookingRepository = Depends(get_booking_repo),
    current_user: User = Depends(require_receptionist)
):
    updated = await booking_repo.update(booking_id, {"status": BookingStatus.NO_SHOW}, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )    
    return updated


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: int, 
    booking_repo: BookingRepository = Depends(get_booking_repo),
    _: User = Depends(require_manager),
):
    try:
        deleted = await booking_repo.delete(booking_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin đặt phòng"
        )
    return None

@router.get("/enum/booking-statuses", response_model=List[BookingStatusItem])
async def get_booking_statuses(_: User = Depends(require_receptionist)):
    return [
        BookingStatusItem(value=BookingStatus.RESERVED.value, text="Đã đặt"),
        BookingStatusItem(value=BookingStatus.CHECKED_IN.value, text="Đã nhận phòng"),
        BookingStatusItem(value=BookingStatus.CHECKED_OUT.value, text="Đã trả phòng"),
        BookingStatusItem(value=BookingStatus.CANCELLED.value, text="Đã hủy"),
        BookingStatusItem(value=BookingStatus.NO_SHOW.value, text="Không đến"),
    ]

@router.get("/enum/payment-statuses", response_model=List[PaymentStatusItem])
async def get_payment_statuses(_: User = Depends(require_receptionist)):
    return [
        PaymentStatusItem(value=PaymentStatus.PAID.value, text="Đã thanh toán"),
        PaymentStatusItem(value=PaymentStatus.PARTIAL.value, text="Thanh toán một phần"),
        PaymentStatusItem(value=PaymentStatus.UNPAID.value, text="Chưa thanh toán"),
    ]

@router.get("/enum/charge-types", response_model=List[ChargeTypeItem])
async def get_charge_types(_: User = Depends(require_receptionist)):
    return [
        ChargeTypeItem(value=ChargeType.HOUR.value, text="Theo giờ"),
        ChargeTypeItem(value=ChargeType.NIGHT.value, text="Qua đêm"),
    ]

@router.get("/enum/booking-detail-types", response_model=List[BookingDetailTypeItem])
async def get_booking_detail_types(_: User = Depends(require_receptionist)):
    return [
        BookingDetailTypeItem(value=BookingDetailType.ROOM.value, text="Phòng"),
        BookingDetailTypeItem(value=BookingDetailType.SERVICE.value, text="Dịch vụ"),
        BookingDetailTypeItem(value=BookingDetailType.FEE.value, text="Phí"),
        BookingDetailTypeItem(value=BookingDetailType.ADJUSTMENT.value, text="Điều chỉnh"),
    ]