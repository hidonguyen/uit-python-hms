from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from ..models.guest import Guest, Gender

class GuestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Guest]:
        """Lấy danh sách khách hàng với phân trang và bộ lọc."""
        query = select(Guest)
        
        if filters:
            conditions = []
            if "name" in filters and filters["name"]:
                conditions.append(Guest.name.ilike(f"%{filters['name']}%"))
            if "phone" in filters and filters["phone"]:
                conditions.append(Guest.phone.ilike(f"%{filters['phone']}%"))
            if "email" in filters and filters["email"]:
                conditions.append(Guest.email.ilike(f"%{filters['email']}%"))
            if "gender" in filters and filters["gender"]:
                conditions.append(Guest.gender == filters["gender"])
            if "nationality" in filters and filters["nationality"]:
                conditions.append(Guest.nationality.ilike(f"%{filters['nationality']}%"))
            
            if conditions:
                query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get(self, guest_id: int) -> Optional[Guest]:
        """Lấy khách hàng theo ID."""
        result = await self.session.execute(
            select(Guest).where(Guest.id == guest_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, guest_data: Dict[str, Any]) -> Guest:
        """Tạo khách hàng mới."""
        guest = Guest(**guest_data)
        self.session.add(guest)
        await self.session.commit()
        await self.session.refresh(guest)
        return guest
    
    async def update(self, guest_id: int, guest_data: Dict[str, Any]) -> Optional[Guest]:
        """Cập nhật khách hàng."""
        guest = await self.get(guest_id)
        if not guest:
            return None
        
        for field, value in guest_data.items():
            if hasattr(guest, field) and value is not None:
                setattr(guest, field, value)
        
        await self.session.commit()
        await self.session.refresh(guest)
        return guest
    
    async def delete(self, guest_id: int) -> bool:
        """Xóa khách hàng (kiểm tra ràng buộc toàn vẹn)."""
        guest = await self.get(guest_id)
        if not guest:
            return False
        
        from ..models.booking import Booking
        bookings_count = await self.session.execute(
            select(func.count(Booking.id)).where(Booking.primary_guest_id == guest_id)
        )
        if bookings_count.scalar() > 0:
            raise ValueError("Không thể xóa khách hàng vì vẫn còn booking đang sử dụng")
        
        await self.session.delete(guest)
        await self.session.commit()
        return True
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Đếm tổng số khách hàng với bộ lọc."""
        query = select(func.count(Guest.id))
        
        if filters:
            conditions = []
            if "name" in filters and filters["name"]:
                conditions.append(Guest.name.ilike(f"%{filters['name']}%"))
            if "phone" in filters and filters["phone"]:
                conditions.append(Guest.phone.ilike(f"%{filters['phone']}%"))
            if "email" in filters and filters["email"]:
                conditions.append(Guest.email.ilike(f"%{filters['email']}%"))
            if "gender" in filters and filters["gender"]:
                conditions.append(Guest.gender == filters["gender"])
            if "nationality" in filters and filters["nationality"]:
                conditions.append(Guest.nationality.ilike(f"%{filters['nationality']}%"))
            
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0