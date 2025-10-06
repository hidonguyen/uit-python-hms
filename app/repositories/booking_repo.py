from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from ..models.booking import Booking, BookingStatus, PaymentStatus, ChargeType

class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Booking]:
        """Lấy danh sách booking với phân trang và bộ lọc."""
        query = select(Booking).options(
            selectinload(Booking.room),
            selectinload(Booking.room_type),
            selectinload(Booking.primary_guest)
        )
        
        # Áp dụng bộ lọc nếu có
        if filters:
            conditions = []
            if "booking_no" in filters and filters["booking_no"]:
                conditions.append(Booking.booking_no.ilike(f"%{filters['booking_no']}%"))
            if "room_id" in filters and filters["room_id"] is not None:
                conditions.append(Booking.room_id == filters["room_id"])
            if "room_type_id" in filters and filters["room_type_id"] is not None:
                conditions.append(Booking.room_type_id == filters["room_type_id"])
            if "primary_guest_id" in filters and filters["primary_guest_id"] is not None:
                conditions.append(Booking.primary_guest_id == filters["primary_guest_id"])
            if "status" in filters and filters["status"]:
                conditions.append(Booking.status == filters["status"])
            if "payment_status" in filters and filters["payment_status"]:
                conditions.append(Booking.payment_status == filters["payment_status"])
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
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Sắp xếp theo thời gian tạo mới nhất
        query = query.order_by(Booking.created_at.desc())
        
        # Phân trang
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
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
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
    async def update(self, booking_id: int, booking_data: Dict[str, Any]) -> Optional[Booking]:
        """Cập nhật booking."""
        booking = await self.get(booking_id)
        if not booking:
            return None
        
        # Cập nhật các trường
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
        
        # Kiểm tra xem có payment nào đang sử dụng booking này không
        from ..models.payment import Payment
        payments_count = await self.session.execute(
            select(func.count(Payment.id)).where(Payment.booking_id == booking_id)
        )
        if payments_count.scalar() > 0:
            raise ValueError("Không thể xóa booking vì vẫn còn payment đang sử dụng")
        
        await self.session.delete(booking)
        await self.session.commit()
        return True
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Đếm tổng số booking với bộ lọc."""
        query = select(func.count(Booking.id))
        
        if filters:
            conditions = []
            if "booking_no" in filters and filters["booking_no"]:
                conditions.append(Booking.booking_no.ilike(f"%{filters['booking_no']}%"))
            if "room_id" in filters and filters["room_id"] is not None:
                conditions.append(Booking.room_id == filters["room_id"])
            if "status" in filters and filters["status"]:
                conditions.append(Booking.status == filters["status"])
            if "payment_status" in filters and filters["payment_status"]:
                conditions.append(Booking.payment_status == filters["payment_status"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_bookings_by_status(self, status: BookingStatus) -> List[Booking]:
        """Lấy danh sách booking theo trạng thái."""
        result = await self.session.execute(
            select(Booking).where(Booking.status == status)
        )
        return list(result.scalars().all())
    
    async def get_bookings_by_payment_status(self, payment_status: PaymentStatus) -> List[Booking]:
        """Lấy danh sách booking theo trạng thái thanh toán."""
        result = await self.session.execute(
            select(Booking).where(Booking.payment_status == payment_status)
        )
        return list(result.scalars().all())
    
    async def get_bookings_by_room(self, room_id: int) -> List[Booking]:
        """Lấy danh sách booking theo phòng."""
        result = await self.session.execute(
            select(Booking).where(Booking.room_id == room_id)
        )
        return list(result.scalars().all())
    
    async def get_bookings_by_guest(self, guest_id: int) -> List[Booking]:
        """Lấy danh sách booking theo khách hàng."""
        result = await self.session.execute(
            select(Booking).where(Booking.primary_guest_id == guest_id)
        )
        return list(result.scalars().all())
    
    async def get_active_bookings(self) -> List[Booking]:
        """Lấy danh sách booking đang hoạt động (CheckedIn)."""
        result = await self.session.execute(
            select(Booking).where(Booking.status == BookingStatus.CHECKED_IN)
        )
        return list(result.scalars().all())
    
    async def update_status(self, booking_id: int, status: BookingStatus) -> Optional[Booking]:
        """Cập nhật trạng thái booking."""
        booking = await self.get(booking_id)
        if not booking:
            return None
        
        booking.status = status
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
    async def update_payment_status(self, booking_id: int, payment_status: PaymentStatus) -> Optional[Booking]:
        """Cập nhật trạng thái thanh toán booking."""
        booking = await self.get(booking_id)
        if not booking:
            return None
        
        booking.payment_status = payment_status
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
    async def checkin(self, booking_id: int, checkin_time: datetime) -> Optional[Booking]:
        """Check-in booking."""
        booking = await self.get(booking_id)
        if not booking:
            return None
        
        booking.checkin = checkin_time
        booking.status = BookingStatus.CHECKED_IN
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
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