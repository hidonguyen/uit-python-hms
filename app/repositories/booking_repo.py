from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from app.models.payment import Payment
from app.schemas.booking import BookingHistoryOut, TodayBookingOut
from ..models.booking import Booking, BookingStatus
from ..models.booking_detail import BookingDetail, BookingDetailType
from ..models.guest import Guest
from ..models.room import Room
from ..models.room_type import RoomType

class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list_today_bookings(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TodayBookingOut]:
        """Lấy danh sách booking hôm nay với phân trang."""
        today = date.today()

        rbd_subq = (
            select(
                BookingDetail.booking_id.label("booking_id"),
                func.coalesce(func.sum(BookingDetail.amount), 0).label("total_room_charges"),
            )
            .where(BookingDetail.type == BookingDetailType.ROOM)
            .group_by(BookingDetail.booking_id)
            .subquery()
        )

        sbd_subq = (
            select(
                BookingDetail.booking_id.label("booking_id"),
                func.coalesce(func.sum(BookingDetail.amount), 0).label("total_service_charges"),
            )
            .where(BookingDetail.type != BookingDetailType.ROOM)
            .group_by(BookingDetail.booking_id)
            .subquery()
        )

        query = (
            select(
                Booking.id,
                Booking.booking_no,
                Booking.charge_type,
                Booking.checkin,
                Booking.checkout,
                Booking.room_id,
                Room.name.label("room_name"),
                Booking.room_type_id,
                RoomType.name.label("room_type_name"),
                Booking.primary_guest_id,
                Guest.name.label("primary_guest_name"),
                Guest.phone.label("primary_guest_phone"),
                Booking.num_adults,
                Booking.num_children,
                func.coalesce(rbd_subq.c.total_room_charges, 0).label("total_room_charges"),
                func.coalesce(sbd_subq.c.total_service_charges, 0).label("total_service_charges"),
                Booking.status,
                Booking.payment_status,
                Booking.notes,
                Booking.created_at,
                Booking.created_by,
                Booking.updated_at,
                Booking.updated_by,
            )
            .select_from(Booking)
            .join(Room, Booking.room_id == Room.id)
            .join(RoomType, Booking.room_type_id == RoomType.id)
            .join(Guest, Booking.primary_guest_id == Guest.id)
            .outerjoin(rbd_subq, Booking.id == rbd_subq.c.booking_id)
            .outerjoin(sbd_subq, Booking.id == sbd_subq.c.booking_id)
            .where(
                and_(
                    func.date(Booking.checkin) <= today,
                    or_(Booking.checkout.is_(None), func.date(Booking.checkout) >= today),
                    Booking.status != BookingStatus.CHECKED_OUT
                )
            )
            .order_by(Booking.checkin.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        rows = result.all()

        bookings: List[TodayBookingOut] = []
        for row in rows:
            bookings.append(TodayBookingOut(
                id=row.id,
                booking_no=row.booking_no,
                charge_type=row.charge_type,
                checkin=row.checkin,
                checkout=row.checkout,
                room_id=row.room_id,
                room_name=row.room_name,
                room_type_id=row.room_type_id,
                room_type_name=row.room_type_name,
                primary_guest_id=row.primary_guest_id,
                primary_guest_name=row.primary_guest_name,
                primary_guest_phone=row.primary_guest_phone,
                num_adults=row.num_adults,
                num_children=row.num_children,
                total_room_charges=row.total_room_charges,
                total_service_charges=row.total_service_charges,
                notes=row.notes,
            ))

        return bookings
    
    async def count_today_bookings(self) -> int:
        """Đếm tổng số booking hôm nay với bộ lọc."""
        today = date.today()

        query = (
            select(func.count(Booking.id))
            .select_from(Booking)
            .join(Room, Booking.room_id == Room.id)
            .join(RoomType, Booking.room_type_id == RoomType.id)
            .join(Guest, Booking.primary_guest_id == Guest.id)
            .where(
                and_(
                    func.date(Booking.checkin) <= today,
                    or_(Booking.checkout.is_(None), func.date(Booking.checkout) >= today),
                    Booking.status != BookingStatus.CHECKED_OUT
                )
            )
        )

        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def list_booking_histories(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[BookingHistoryOut]:
        """Lấy danh sách booking với phân trang và bộ lọc."""

        bd_subq = (
            select(
                BookingDetail.booking_id.label("booking_id"),
                func.coalesce(func.sum(BookingDetail.amount), 0).label("total_amount"),
            )
            .group_by(BookingDetail.booking_id)
            .subquery()
        )

        pm_subq = (
            select(
                Payment.booking_id.label("booking_id"),
                func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
            )
            .group_by(Payment.booking_id)
            .subquery()
        )

        query = (
            select(
                Booking.id,
                Booking.booking_no,
                Booking.charge_type,
                Booking.checkin,
                Booking.checkout,
                Room.name.label("room_name"),
                RoomType.name.label("room_type_name"),
                Guest.name.label("primary_guest_name"),
                Guest.phone.label("primary_guest_phone"),
                Booking.num_adults,
                Booking.num_children,
                Booking.status,
                Booking.payment_status,
                func.coalesce(bd_subq.c.total_amount, 0).label("total_amount"),
                func.coalesce(pm_subq.c.paid_amount, 0).label("paid_amount"),
                (func.coalesce(bd_subq.c.total_amount, 0) - func.coalesce(pm_subq.c.paid_amount, 0)).label("balance"),
                Booking.notes
            )
            .select_from(Booking)
            .join(Room, Room.id == Booking.room_id)
            .join(RoomType, RoomType.id == Booking.room_type_id)
            .join(Guest, Guest.id == Booking.primary_guest_id)
            .outerjoin(bd_subq, bd_subq.c.booking_id == Booking.id)
            .outerjoin(pm_subq, pm_subq.c.booking_id == Booking.id)
        )
        
        if filters:
            conditions = []
            if "booking_no" in filters and filters["booking_no"]:
                conditions.append(Booking.booking_no.ilike(f"%{filters['booking_no']}%"))
            if "charge_type" in filters and filters["charge_type"]:
                conditions.append(Booking.charge_type == filters["charge_type"])
            if "checkin_from" in filters and filters["checkin_from"]:
                conditions.append(Booking.checkin >= filters["checkin_from"])
            if "checkin_to" in filters and filters["checkin_to"]:
                conditions.append(Booking.checkin <= filters["checkin_to"])
            if "checkout_from" in filters and filters["checkout_from"]:
                conditions.append(Booking.checkout >= filters["checkout_from"])
            if "checkout_to" in filters and filters["checkout_to"]:
                conditions.append(Booking.checkout <= filters["checkout_to"])
            if "room_id" in filters and filters["room_id"] is not None:
                conditions.append(Booking.room_id == filters["room_id"])
            if "room_name" in filters and filters["room_name"]:
                conditions.append(Room.name.ilike(f"%{filters['room_name']}%"))
            if "room_type_id" in filters and filters["room_type_id"] is not None:
                conditions.append(Booking.room_type_id == filters["room_type_id"])
            if "room_type_name" in filters and filters["room_type_name"]:
                conditions.append(RoomType.name.ilike(f"%{filters['room_type_name']}%"))
            if "primary_guest_id" in filters and filters["primary_guest_id"] is not None:
                conditions.append(Booking.primary_guest_id == filters["primary_guest_id"])
            if "primary_guest_name" in filters and filters["primary_guest_name"]:
                conditions.append(Guest.name.ilike(f"%{filters['primary_guest_name']}%"))
            if "status" in filters and filters["status"]:
                conditions.append(Booking.status == filters["status"])
            if "payment_status" in filters and filters["payment_status"]:
                conditions.append(Booking.payment_status == filters["payment_status"])
            if "notes" in filters and filters["notes"]:
                conditions.append(Booking.notes.ilike(f"%{filters['notes']}%"))
            
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        rows = result.all()

        bookings: List[BookingHistoryOut] = []
        for row in rows:
            bookings.append(BookingHistoryOut(
                id=row.id,
                booking_no=row.booking_no,
                charge_type=row.charge_type,
                checkin=row.checkin,
                checkout=row.checkout,
                room_id=row.room_id,
                room_name=row.room_name,
                room_type_id=row.room_type_id,
                room_type_name=row.room_type_name,
                primary_guest_id=row.primary_guest_id,
                primary_guest_name=row.primary_guest_name,
                primary_guest_phone=row.primary_guest_phone,
                num_adults=row.num_adults,
                num_children=row.num_children,
                status=row.status,
                payment_status=row.payment_status,
                total_amount=row.total_amount,
                paid_amount=row.paid_amount,
                balance=row.balance,
                notes=row.notes,
            ))

        return bookings
    
    async def count_booking_histories(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Đếm tổng số booking với bộ lọc."""

        bd_subq = (
            select(
                BookingDetail.booking_id.label("booking_id"),
                func.coalesce(func.sum(BookingDetail.amount), 0).label("total_amount"),
            )
            .group_by(BookingDetail.booking_id)
            .subquery()
        )

        pm_subq = (
            select(
                Payment.booking_id.label("booking_id"),
                func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
            )
            .group_by(Payment.booking_id)
            .subquery()
        )

        query = (
            select(
                Booking.id,
                Booking.booking_no,
                Booking.charge_type,
                Booking.checkin,
                Booking.checkout,
                Room.name.label("room_name"),
                RoomType.name.label("room_type_name"),
                Guest.name.label("primary_guest_name"),
                Guest.phone.label("primary_guest_phone"),
                Booking.num_adults,
                Booking.num_children,
                Booking.status,
                Booking.payment_status,
                func.coalesce(bd_subq.c.total_amount, 0).label("total_amount"),
                func.coalesce(pm_subq.c.paid_amount, 0).label("paid_amount"),
                (func.coalesce(bd_subq.c.total_amount, 0) - func.coalesce(pm_subq.c.paid_amount, 0)).label("balance"),
                Booking.notes
            )
            .select_from(Booking)
            .join(Room, Room.id == Booking.room_id)
            .join(RoomType, RoomType.id == Booking.room_type_id)
            .join(Guest, Guest.id == Booking.primary_guest_id)
            .outerjoin(bd_subq, bd_subq.c.booking_id == Booking.id)
            .outerjoin(pm_subq, pm_subq.c.booking_id == Booking.id)
        )
        
        if filters:
            conditions = []
            if "booking_no" in filters and filters["booking_no"]:
                conditions.append(Booking.booking_no.ilike(f"%{filters['booking_no']}%"))
            if "charge_type" in filters and filters["charge_type"]:
                conditions.append(Booking.charge_type == filters["charge_type"])
            if "checkin_from" in filters and filters["checkin_from"]:
                conditions.append(Booking.checkin >= filters["checkin_from"])
            if "checkin_to" in filters and filters["checkin_to"]:
                conditions.append(Booking.checkin <= filters["checkin_to"])
            if "checkout_from" in filters and filters["checkout_from"]:
                conditions.append(Booking.checkout >= filters["checkout_from"])
            if "checkout_to" in filters and filters["checkout_to"]:
                conditions.append(Booking.checkout <= filters["checkout_to"])
            if "room_id" in filters and filters["room_id"] is not None:
                conditions.append(Booking.room_id == filters["room_id"])
            if "room_name" in filters and filters["room_name"]:
                conditions.append(Room.name.ilike(f"%{filters['room_name']}%"))
            if "room_type_id" in filters and filters["room_type_id"] is not None:
                conditions.append(Booking.room_type_id == filters["room_type_id"])
            if "room_type_name" in filters and filters["room_type_name"]:
                conditions.append(RoomType.name.ilike(f"%{filters['room_type_name']}%"))
            if "primary_guest_id" in filters and filters["primary_guest_id"] is not None:
                conditions.append(Booking.primary_guest_id == filters["primary_guest_id"])
            if "primary_guest_name" in filters and filters["primary_guest_name"]:
                conditions.append(Guest.name.ilike(f"%{filters['primary_guest_name']}%"))
            if "status" in filters and filters["status"]:
                conditions.append(Booking.status == filters["status"])
            if "payment_status" in filters and filters["payment_status"]:
                conditions.append(Booking.payment_status == filters["payment_status"])
            if "notes" in filters and filters["notes"]:
                conditions.append(Booking.notes.ilike(f"%{filters['notes']}%"))
            
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def is_room_booked(self, room_id: int, checkin: datetime, checkout: Optional[datetime] = None) -> bool:
        """Kiểm tra phòng đã được đặt trong khoảng thời gian hay chưa."""
        base_conditions = [
            Booking.room_id == room_id,
            Booking.status != BookingStatus.CHECKED_OUT,
        ]

        if checkout is None:
            overlap = and_(
                Booking.checkin <= checkin,
                or_(Booking.checkout.is_(None), Booking.checkout > checkin),
            )
        else:
            overlap = and_(
                Booking.checkin < checkout,
                or_(Booking.checkout.is_(None), Booking.checkout > checkin),
            )

        query = select(func.count(Booking.id)).where(and_(*(base_conditions + [overlap])))
        result = await self.session.execute(query)
        return result.scalar() > 0


    async def get(self, booking_id: int) -> Optional[Booking]:
        """Lấy booking theo ID."""
        result = await self.session.execute(
            select(Booking)
            .options(
                selectinload(Booking.room),
                selectinload(Booking.room_type),
                selectinload(Booking.primary_guest),
                selectinload(Booking.booking_details),
                selectinload(Booking.payments)
            )
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_booking_no(self, booking_no: str) -> Optional[Booking]:
        """Lấy booking theo mã booking."""
        result = await self.session.execute(
            select(Booking).where(Booking.booking_no == booking_no)
        )
        return result.scalar_one_or_none()
    
    async def create(self, booking_data: Dict[str, Any]) -> Booking:
        """Tạo booking mới."""
        booking = Booking(**booking_data)

        booking.booking_no = await self.generate_booking_no()

        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
    async def update(self, booking_id: int, booking_data: Dict[str, Any]) -> Optional[Booking]:
        """Cập nhật booking."""
        booking = await self.get(booking_id)
        if not booking:
            return None
        
        for field, value in booking_data.items():
            if hasattr(booking, field) and value is not None:
                setattr(booking, field, value)
        
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
    async def delete(self, booking_id: int) -> bool:
        """Xóa booking (kiểm tra ràng buộc toàn vẹn)."""
        booking = await self.get(booking_id)
        if not booking:
            return False
        
        from ..models.payment import Payment
        payments_count = await self.session.execute(
            select(func.count(Payment.id)).where(Payment.booking_id == booking_id)
        )
        if payments_count.scalar() > 0:
            raise ValueError("Không thể xóa booking vì vẫn còn payment đang sử dụng")
        
        await self.session.delete(booking)
        await self.session.commit()
        return True
    
    async def checkout(self, booking_id: int, checkout_time: datetime) -> Optional[Booking]:
        """Check-out booking."""
        booking = await self.get(booking_id)
        if not booking:
            return None
        
        booking.checkout = checkout_time
        booking.status = BookingStatus.CHECKED_OUT
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
    async def generate_booking_no(self) -> str:
        """Tự động sinh mã booking theo định dạng BKGYYMMDDXXX."""
        today_str = datetime.now().strftime("%y%m%d")
        prefix = f"BKG{today_str}"
        
        result = await self.session.execute(
            select(func.max(Booking.booking_no)).where(Booking.booking_no.ilike(f"{prefix}%"))
        )
        max_booking_no = result.scalar()
        
        if max_booking_no:
            seq_num = int(max_booking_no[-3:]) + 1
        else:
            seq_num = 1
        
        return f"{prefix}{seq_num:03d}"