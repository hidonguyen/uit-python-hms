from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from ..models.service import Service, ServiceStatus

class ServiceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Service]:
        """Lấy danh sách dịch vụ với phân trang và bộ lọc."""
        query = select(Service)
        
        # Áp dụng bộ lọc nếu có
        if filters:
            conditions = []
            if "name" in filters and filters["name"]:
                conditions.append(Service.name.ilike(f"%{filters['name']}%"))
            if "unit" in filters and filters["unit"]:
                conditions.append(Service.unit.ilike(f"%{filters['unit']}%"))
            if "status" in filters and filters["status"]:
                conditions.append(Service.status == filters["status"])
            if "min_price" in filters and filters["min_price"] is not None:
                conditions.append(Service.price >= filters["min_price"])
            if "max_price" in filters and filters["max_price"] is not None:
                conditions.append(Service.price <= filters["max_price"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Phân trang
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get(self, service_id: int) -> Optional[Service]:
        """Lấy dịch vụ theo ID."""
        result = await self.session.execute(
            select(Service).where(Service.id == service_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Service]:
        """Lấy dịch vụ theo tên."""
        result = await self.session.execute(
            select(Service).where(Service.name == name)
        )
        return result.scalar_one_or_none()
    
    async def create(self, service_data: Dict[str, Any]) -> Service:
        """Tạo dịch vụ mới."""
        service = Service(**service_data)
        self.session.add(service)
        await self.session.commit()
        await self.session.refresh(service)
        return service
    
    async def update(self, service_id: int, service_data: Dict[str, Any]) -> Optional[Service]:
        """Cập nhật dịch vụ."""
        service = await self.get(service_id)
        if not service:
            return None
        
        # Cập nhật các trường
        for field, value in service_data.items():
            if hasattr(service, field) and value is not None:
                setattr(service, field, value)
        
        await self.session.commit()
        await self.session.refresh(service)
        return service
    
    async def delete(self, service_id: int) -> bool:
        """Xóa dịch vụ (kiểm tra ràng buộc toàn vẹn)."""
        service = await self.get(service_id)
        if not service:
            return False
        
        # Kiểm tra xem có booking detail nào đang sử dụng dịch vụ này không
        from ..models.booking_detail import BookingDetail
        booking_details_count = await self.session.execute(
            select(func.count(BookingDetail.id)).where(BookingDetail.service_id == service_id)
        )
        if booking_details_count.scalar() > 0:
            raise ValueError("Không thể xóa dịch vụ vì vẫn còn booking detail đang sử dụng")
        
        await self.session.delete(service)
        await self.session.commit()
        return True
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Đếm tổng số dịch vụ với bộ lọc."""
        query = select(func.count(Service.id))
        
        if filters:
            conditions = []
            if "name" in filters and filters["name"]:
                conditions.append(Service.name.ilike(f"%{filters['name']}%"))
            if "status" in filters and filters["status"]:
                conditions.append(Service.status == filters["status"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_active_services(self) -> List[Service]:
        """Lấy danh sách dịch vụ đang hoạt động."""
        result = await self.session.execute(
            select(Service).where(Service.status == ServiceStatus.ACTIVE)
        )
        return list(result.scalars().all())