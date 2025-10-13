from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any

from app.models.user import User
from ..models.room_type import RoomType

class RoomTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RoomType]:
        """Lấy danh sách loại phòng với phân trang và bộ lọc."""
        query = select(RoomType)
        
        # Áp dụng bộ lọc nếu có
        if filters:
            conditions = []
            if "code" in filters and filters["code"]:
                conditions.append(RoomType.code.ilike(f"%{filters['code']}%"))
            if "name" in filters and filters["name"]:
                conditions.append(RoomType.name.ilike(f"%{filters['name']}%"))
            if "base_occupancy" in filters and filters["base_occupancy"] is not None:
                conditions.append(RoomType.base_occupancy == filters["base_occupancy"])
            if "max_occupancy" in filters and filters["max_occupancy"] is not None:
                conditions.append(RoomType.max_occupancy == filters["max_occupancy"])
            if "min_base_rate" in filters and filters["min_base_rate"] is not None:
                conditions.append(RoomType.base_rate >= filters["min_base_rate"])
            if "max_base_rate" in filters and filters["max_base_rate"] is not None:
                conditions.append(RoomType.base_rate <= filters["max_base_rate"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Phân trang
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Đếm tổng số loại phòng với bộ lọc."""
        query = select(func.count(RoomType.id))
        
        if filters:
            conditions = []
            if "code" in filters and filters["code"]:
                conditions.append(RoomType.code.ilike(f"%{filters['code']}%"))
            if "name" in filters and filters["name"]:
                conditions.append(RoomType.name.ilike(f"%{filters['name']}%"))
            
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get(self, room_type_id: int) -> Optional[RoomType]:
        """Lấy loại phòng theo ID."""
        result = await self.session.execute(
            select(RoomType).where(RoomType.id == room_type_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> Optional[RoomType]:
        """Lấy loại phòng theo mã code."""
        result = await self.session.execute(
            select(RoomType).where(RoomType.code == code)
        )
        return result.scalar_one_or_none()
    
    async def create(self, room_type_data: Dict[str, Any], current_user: User) -> RoomType:
        """Tạo loại phòng mới."""
        room_type = RoomType(**room_type_data)

        room_type.created_by = current_user.id
        room_type.created_at = datetime.now()

        self.session.add(room_type)
        await self.session.commit()
        await self.session.refresh(room_type)
        return room_type
    
    async def update(self, room_type_id: int, room_type_data: Dict[str, Any], current_user: User) -> Optional[RoomType]:
        """Cập nhật loại phòng."""
        room_type = await self.get(room_type_id)
        if not room_type:
            return None
        
        # Cập nhật các trường
        for field, value in room_type_data.items():
            if hasattr(room_type, field) and value is not None:
                setattr(room_type, field, value)

        room_type.updated_by = current_user.id
        room_type.updated_at = datetime.now()

        await self.session.commit()
        await self.session.refresh(room_type)
        return room_type
    
    async def delete(self, room_type_id: int) -> bool:
        """Xóa loại phòng (kiểm tra ràng buộc toàn vẹn)."""
        room_type = await self.get(room_type_id)
        if not room_type:
            return False
        
        # Kiểm tra xem có phòng nào đang sử dụng loại phòng này không
        from ..models.room import Room
        rooms_count = await self.session.execute(
            select(func.count(Room.id)).where(Room.room_type_id == room_type_id)
        )
        if rooms_count.scalar() > 0:
            raise ValueError("Không thể xóa thông tin loại phòng vì đã có phòng liên quan")
        
        # Kiểm tra xem có booking nào đang sử dụng loại phòng này không
        from ..models.booking import Booking
        bookings_count = await self.session.execute(
            select(func.count(Booking.id)).where(Booking.room_type_id == room_type_id)
        )
        if bookings_count.scalar() > 0:
            raise ValueError("Không thể xóa thông tin loại phòng vì đã có booking liên quan")
        
        await self.session.delete(room_type)
        await self.session.commit()
        return True