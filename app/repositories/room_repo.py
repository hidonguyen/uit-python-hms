from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any

from app.models.booking import Booking, BookingStatus
from app.models.room_type import RoomType
from app.models.user import User
from app.schemas.room import AvailableRoomOut
from ..models.room import HousekeepingStatus, Room, RoomStatus

class RoomRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Room]:
        """Lấy danh sách phòng với phân trang và bộ lọc."""
        query = select(Room).options(selectinload(Room.room_type))
        
        # Áp dụng bộ lọc nếu có
        if filters:
            conditions = []
            if "name" in filters and filters["name"]:
                conditions.append(Room.name.ilike(f"%{filters['name']}%"))
            if "room_type_id" in filters and filters["room_type_id"] is not None:
                conditions.append(Room.room_type_id == filters["room_type_id"])
            if "status" in filters and filters["status"]:
                conditions.append(Room.status == filters["status"])
            if "housekeeping_status" in filters and filters["housekeeping_status"]:
                conditions.append(Room.housekeeping_status == filters["housekeeping_status"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Phân trang
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Đếm tổng số phòng với bộ lọc."""
        query = select(func.count(Room.id))
        
        if filters:
            conditions = []
            if "name" in filters and filters["name"]:
                conditions.append(Room.name.ilike(f"%{filters['name']}%"))
            if "room_type_id" in filters and filters["room_type_id"] is not None:
                conditions.append(Room.room_type_id == filters["room_type_id"])
            if "status" in filters and filters["status"]:
                conditions.append(Room.status == filters["status"])
            if "housekeeping_status" in filters and filters["housekeeping_status"]:
                conditions.append(Room.housekeeping_status == filters["housekeeping_status"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get(self, room_id: int) -> Optional[Room]:
        """Lấy phòng theo ID."""
        result = await self.session.execute(
            select(Room)
            .options(selectinload(Room.room_type))
            .where(Room.id == room_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Room]:
        """Lấy phòng theo tên."""
        result = await self.session.execute(
            select(Room).where(Room.name == name)
        )
        return result.scalar_one_or_none()
    
    async def create(self, room_data: Dict[str, Any], current_user: User) -> Room:
        """Tạo phòng mới."""
        room = Room(**room_data)
        
        room.created_by = current_user.id
        room.created_at = datetime.now()

        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return room
    
    async def update(self, room_id: int, room_data: Dict[str, Any], current_user: User) -> Optional[Room]:
        """Cập nhật phòng."""
        room = await self.get(room_id)
        if not room:
            return None
        
        # Cập nhật các trường
        for field, value in room_data.items():
            if hasattr(room, field) and value is not None:
                setattr(room, field, value)

        room.updated_by = current_user.id
        room.updated_at = datetime.now()

        await self.session.commit()
        await self.session.refresh(room)
        return room
    
    async def delete(self, room_id: int) -> bool:
        """Xóa phòng (kiểm tra ràng buộc toàn vẹn)."""
        room = await self.get(room_id)
        if not room:
            return False
        
        # Kiểm tra xem có booking nào đang sử dụng phòng này không
        from ..models.booking import Booking
        bookings_count = await self.session.execute(
            select(func.count(Booking.id)).where(Booking.room_id == room_id)
        )
        if bookings_count.scalar() > 0:
            raise ValueError("Không thể xóa thông tin phòng vì đã có booking liên quan")
        
        await self.session.delete(room)
        await self.session.commit()
        return True

    async def get_available_rooms(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        room_id: Optional[int] = None,
        room_type_id: Optional[int] = None, 
        occupancy: Optional[int] = None,
        min_base_rate: Optional[Decimal] = None,
        max_base_rate: Optional[Decimal] = None,
    ) -> List[AvailableRoomOut]:
        """Lấy danh sách phòng có sẵn."""

        if not from_date:
            from_date = datetime.today()
            from_date = from_date.replace(hour=14, minute=0, second=0, microsecond=0) # Giờ nhận phòng mặc định 14:00

        # Nếu from_date không có thông tin giờ, đặt giờ nhận phòng mặc định
        if from_date.hour == 0 and from_date.minute == 0 and from_date.second == 0 and from_date.microsecond == 0:
            from_date = from_date.replace(hour=14, minute=0, second=0, microsecond=0) # Giờ nhận phòng mặc định 14:00

        if not to_date:
            to_date = from_date + timedelta(days=1)
            to_date = to_date.replace(hour=12, minute=0, second=0, microsecond=0) # Giờ trả phòng mặc định 12:00
        
        # Nếu to_date không có thông tin giờ, đặt giờ trả phòng mặc định
        if to_date.hour == 0 and to_date.minute == 0 and to_date.second == 0 and to_date.microsecond == 0:
            to_date = to_date.replace(hour=12, minute=0, second=0, microsecond=0) # Giờ trả phòng mặc định 12:00

        # kiểm tra danh sách phòng có sẵn tại thời điểm cụ thể
        rooms = (
            select(Booking.room_id)
            .where(
                and_(
                    or_(Booking.status == BookingStatus.RESERVED, Booking.status == BookingStatus.CHECKED_IN),
                    or_(
                        and_(
                            Booking.checkout.is_(None),
                            Booking.checkin <= to_date,
                        ),
                        and_(
                            Booking.checkout.is_not(None),
                            Booking.checkin <= to_date,
                            Booking.checkout > from_date,
                        )
                    )
                )
            )
            .subquery()
        )

        # Lọc theo điều kiện của loại phòng
        rt_conditions = []
        if occupancy is not None:
            rt_conditions.append(RoomType.max_occupancy >= occupancy)
        if min_base_rate is not None:
            rt_conditions.append(RoomType.base_rate >= min_base_rate)
        if max_base_rate is not None:
            rt_conditions.append(RoomType.base_rate <= max_base_rate)

        query = (
            select(
                Room.id,
                Room.name,
                Room.room_type_id,
                RoomType.name.label("room_type"),
                RoomType.base_occupancy,
                RoomType.max_occupancy,
                RoomType.base_rate,
                RoomType.hour_rate,
                RoomType.extra_adult_fee,
                RoomType.extra_child_fee,
                Room.description,
                Room.status,
                Room.housekeeping_status,
                Room.created_at,
                Room.updated_at,
            )
            .select_from(Room)
            .join(RoomType, Room.room_type_id == RoomType.id)
            .where(
                and_(
                    Room.status == RoomStatus.AVAILABLE,
                    Room.housekeeping_status == HousekeepingStatus.CLEAN,
                    ~Room.id.in_(select(rooms.c.room_id)),
                    *rt_conditions
                )
            )
        )
        if room_id:
            query = query.where(and_(Room.id == room_id))
        if room_type_id:
            query = query.where(and_(Room.room_type_id == room_type_id))

        result = await self.session.execute(query)        
        rows = result.all()

        rooms: List[AvailableRoomOut] = []
        for row in rows:
            rooms.append(AvailableRoomOut(
                id=row.id,
                name=row.name,
                room_type_id=row.room_type_id,
                room_type=row.room_type,
                base_occupancy=row.base_occupancy,
                max_occupancy=row.max_occupancy,
                base_rate=row.base_rate,
                hour_rate=row.hour_rate,
                extra_adult_fee=row.extra_adult_fee,
                extra_child_fee=row.extra_child_fee,
                description=row.description,
                status=row.status,
                housekeeping_status=row.housekeeping_status,
                created_at=row.created_at,
                updated_at=row.updated_at,
            ))

        return rooms